# ai/pattern_extractor.py
"""
استخراج الگو از Word پروپوزال‌های Import‌شده
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict

from docx import Document

from ai.proposal_section_detector import ProposalSectionDetector

logger = logging.getLogger(__name__)


class PatternExtractor:
    """استخراج الگو از Word Import‌شده"""
    
    def __init__(self, db_manager, app):
        self.db = db_manager
        self.app = app
        self.detector = ProposalSectionDetector()
        self._ensure_tables()
    
    def _ensure_tables(self):
        """ایجاد جداول الگو"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # project_patterns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    source_file TEXT,
                    total_sections INTEGER,
                    total_devices INTEGER,
                    total_io INTEGER,
                    section_types TEXT,
                    created_at TEXT,
                    usage_count INTEGER DEFAULT 0
                )
            ''')
            
            # component_patterns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS component_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_pattern_id INTEGER,
                    section_type TEXT NOT NULL,
                    device_count INTEGER,
                    components_json TEXT,
                    io_json TEXT,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT
                )
            ''')
            
            # io_patterns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS io_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section_type TEXT NOT NULL,
                    device_count INTEGER,
                    avg_di REAL,
                    avg_do REAL,
                    avg_ai REAL,
                    avg_ao REAL,
                    avg_total REAL,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT
                )
            ''')
            
            conn.commit()
            logger.info("✅ Pattern tables ensured")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    def extract_from_docx(self, docx_path: str) -> Optional[Dict[str, Any]]:
        """استخراج الگو از Word"""
        try:
            if not os.path.exists(docx_path):
                return None
            
            doc = Document(docx_path)
            
            # استخراج جداول
            tables = []
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    table_data.append(row_data)
                tables.append(table_data)
            
            logger.info(f"📊 Found {len(tables)} tables in {os.path.basename(docx_path)}")
            
            patterns = self._process_tables(tables)
            
            if not patterns:
                return None
            
            patterns['project_name'] = Path(docx_path).stem
            patterns['source_file'] = os.path.basename(docx_path)
            
            return patterns
        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)
            return None
    
    def _process_tables(self, tables: List) -> Optional[Dict[str, Any]]:
        """پردازش جداول"""
        result = {
            'total_sections': 0,
            'total_devices': 0,
            'total_io': {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0, 'total': 0},
            'sections': [],
        }
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            header = ' '.join(table[0]).lower()
            has_io = all(x in header for x in ['di', 'do', 'ai', 'ao'])
            
            if not has_io:
                continue
            
            section_devices = []
            section_io = {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0}
            
            for row in table[1:]:
                if len(row) < 8:
                    continue
                try:
                    device_name = row[1].strip() if len(row) > 1 else ''
                    di = self._safe_int(row[3])
                    do = self._safe_int(row[4])
                    ai = self._safe_int(row[5])
                    ao = self._safe_int(row[6])
                    
                    if device_name and (di + do + ai + ao) > 0:
                        section_devices.append({
                            'name': device_name,
                            'di': di, 'do': do, 'ai': ai, 'ao': ao,
                        })
                        section_io['DI'] += di
                        section_io['DO'] += do
                        section_io['AI'] += ai
                        section_io['AO'] += ao
                except:
                    continue
            
            if section_devices:
                section_type = self._detect_section_from_devices(section_devices)
                components = self._extract_components(section_devices)
                
                result['sections'].append({
                    'section_type': section_type,
                    'device_count': len(section_devices),
                    'components': components,
                    'io': section_io,
                    'device_examples': [d['name'] for d in section_devices[:10]],
                })
                
                result['total_devices'] += len(section_devices)
                result['total_io']['DI'] += section_io['DI']
                result['total_io']['DO'] += section_io['DO']
                result['total_io']['AI'] += section_io['AI']
                result['total_io']['AO'] += section_io['AO']
        
        result['total_sections'] = len(result['sections'])
        result['total_io']['total'] = sum(
            result['total_io'][k] for k in ['DI', 'DO', 'AI', 'AO']
        )
        
        return result if result['sections'] else None
    
    def _extract_components(self, devices: List[Dict]) -> Dict[str, int]:
        """استخراج کامپوننت‌ها"""
        components = defaultdict(int)
        
        for device in devices:
            name = (device['name'] or '').upper()
            
            if 'PUMP' in name or name.startswith('P-') or name.startswith('PU-'):
                components['PU'] += 1
                components['FA'] += 1
                components['FE'] += 1
                components['SLE'] += 1
                components['CMD'] += 1
            elif 'FAN' in name or name.startswith('F-') or 'S-FAN' in name:
                components['PU'] += 1
                components['FA'] += 1
                components['FE'] += 1
                components['CMD'] += 1
            elif 'CHILLER' in name or name.startswith('CH-') or 'CH.' in name:
                components['CHILLER'] += 1
            elif 'HWB' in name or 'BOILER' in name or 'BLR' in name:
                components['BOILER'] += 1
            elif 'VSD' in name or 'VFD' in name:
                components['VSD'] += 1
            
            if 'DTS' in name: components['DTS'] += 1
            if 'ITS' in name: components['ITS'] += 1
            if 'RTS' in name: components['RTS'] += 1
            if 'RTHS' in name: components['RTHS'] += 1
            if 'DTHS' in name: components['DTHS'] += 1
            if name.startswith('PT') or 'TRANS' in name: components['PT'] += 1
            if 'DPT' in name: components['DPT'] += 1
            if 'FS' in name or 'FLOW' in name: components['FS'] += 1
            if 'PS' in name or 'PRESS' in name: components['PS'] += 1
            if 'LS' in name or 'LEVEL' in name: components['LS'] += 1
            if 'FRZ' in name or 'FREEZE' in name or 'FR-' in name: components['FR'] += 1
            if 'VA-' in name or 'VALVE' in name: components['VA'] += 1
            if 'SV-' in name or 'SOLENOID' in name: components['SV'] += 1
            if 'MOV' in name: components['MOV'] += 1
            if 'DAM-' in name or 'DAMPER' in name: components['DAM_T1'] += 1
        
        return dict(components)
    
    def _detect_section_from_devices(self, devices: List[Dict]) -> str:
        """تشخیص نوع سکشن"""
        names = ' '.join(d['name'] for d in devices).upper()
        
        if 'AHU' in names: return 'ahu'
        elif 'CHILLER' in names or 'CH-' in names: return 'chiller'
        elif 'BOILER' in names or 'HWB' in names: return 'boiler'
        elif 'DHW' in names: return 'dhw'
        elif 'PUMP' in names or names.count('P-') > 3: return 'pump'
        elif 'BOOSTER' in names: return 'booster_pump'
        elif 'EX.TNK' in names or 'EXPANSION' in names: return 'expansion_tank'
        elif 'FANCOIL' in names or 'FCU' in names: return 'fancoil'
        elif 'PANEL' in names or 'MCC' in names: return 'panel'
        else: return 'unknown'
    
    def save_pattern(self, pattern_data: Dict[str, Any], source: str = 'imported') -> bool:
        """ذخیره الگو در دیتابیس"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            section_types_json = ','.join(
                s['section_type'] for s in pattern_data['sections']
            )
            
            cursor.execute('''
                INSERT INTO project_patterns
                (project_name, source_file, total_sections, total_devices,
                 total_io, section_types, created_at, usage_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            ''', (
                pattern_data['project_name'],
                pattern_data.get('source_file', ''),
                pattern_data['total_sections'],
                pattern_data['total_devices'],
                pattern_data['total_io']['total'],
                section_types_json,
                now,
            ))
            
            project_pattern_id = cursor.lastrowid
            
            for section in pattern_data['sections']:
                cursor.execute('''
                    INSERT INTO component_patterns
                    (project_pattern_id, section_type, device_count,
                     components_json, io_json, usage_count, created_at)
                    VALUES (?, ?, ?, ?, ?, 0, ?)
                ''', (
                    project_pattern_id,
                    section['section_type'],
                    section['device_count'],
                    json.dumps(section['components'], ensure_ascii=False),
                    json.dumps(section['io'], ensure_ascii=False),
                    now,
                ))
            
            conn.commit()
            logger.info(f"✅ Pattern saved: {pattern_data['project_name']}")
            return True
        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _safe_int(value) -> int:
        """تبدیل امن به int"""
        if not value:
            return 0
        try:
            cleaned = re.sub(r'[^\d-]', '', str(value))
            return int(cleaned) if cleaned else 0
        except:
            return 0


__all__ = ['PatternExtractor']