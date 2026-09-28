# ai/learning_engine.py
"""
Learning Engine - یادگیری از همه پروژه‌ها و همه Revision ها

نسخه 3.1 — اصلاح‌شده
- ✅ _extract_patterns برای analyze_project
- ✅ _suggest_io_optimization برای optimization
- ✅ _detect_equipment_type_from_tag برای SmartTag
- ✅ _get_project_templates
- ✅ label در get_statistics
- ✅ پشتیبانی کامل از app.projects
"""

import json
import sqlite3
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class LearningEngine:
    """
    موتور یادگیری هوشمند - یادگیری از همه پروژه‌ها و Revision ها
    """
    
    def __init__(self, db_manager, app=None):
        self.db = db_manager
        self.app = app
        self._init_learning_tables()
        
        logger.info("LearningEngine initialized (v3.1 - fixed)")
    
    # ================================================================
    # INIT
    # ================================================================
    
    def _init_learning_tables(self):
        """ایجاد جداول یادگیری"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # ============================================================
            # 1. بررسی جدول قدیمی learning_patterns
            # ============================================================
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='learning_patterns'"
            )
            
            if cursor.fetchone():
                cursor.execute("PRAGMA table_info(learning_patterns)")
                existing_cols = [col[1] for col in cursor.fetchall()]
                
                if 'project_name' not in existing_cols:
                    logger.warning("🔄 Old learning_patterns table found. Migrating...")
                    cursor.execute("DROP TABLE learning_patterns")
                    logger.info("✅ Dropped old learning_patterns table")
            
            # ============================================================
            # 2. learning_patterns
            # ============================================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    revision_name TEXT DEFAULT 'Rev-0',
                    pattern_type TEXT NOT NULL,
                    equipment_type TEXT,
                    component_key TEXT,
                    component_count INTEGER,
                    io_pattern TEXT,
                    usage_count INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            # ============================================================
            # 3. بررسی ستون‌های گم‌شده
            # ============================================================
            cursor.execute("PRAGMA table_info(learning_patterns)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'revision_name' not in columns:
                cursor.execute(
                    "ALTER TABLE learning_patterns ADD COLUMN revision_name TEXT DEFAULT 'Rev-0'"
                )
                logger.info("✅ Added revision_name to learning_patterns")
            
            # ============================================================
            # 4. learning_project_analysis
            # ============================================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_project_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL,
                    revision_name TEXT DEFAULT 'Rev-0',
                    total_devices INTEGER,
                    total_sections INTEGER,
                    total_io INTEGER,
                    avg_io_per_device REAL,
                    component_usage TEXT,
                    io_distribution TEXT,
                    analyzed_at TEXT,
                    UNIQUE(project_name, revision_name)
                )
            ''')
            
            cursor.execute("PRAGMA table_info(learning_project_analysis)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'revision_name' not in columns:
                cursor.execute(
                    "ALTER TABLE learning_project_analysis "
                    "ADD COLUMN revision_name TEXT DEFAULT 'Rev-0'"
                )
                logger.info("✅ Added revision_name to learning_project_analysis")
            
            if 'total_sections' not in columns:
                cursor.execute(
                    "ALTER TABLE learning_project_analysis "
                    "ADD COLUMN total_sections INTEGER DEFAULT 0"
                )
                logger.info("✅ Added total_sections to learning_project_analysis")
            
            # ============================================================
            # 5. learning_equipment_patterns
            # ============================================================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_equipment_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_type TEXT NOT NULL,
                    pattern_signature TEXT NOT NULL,
                    components TEXT,
                    io_pattern TEXT,
                    usage_count INTEGER DEFAULT 1,
                    sample_projects TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    UNIQUE(equipment_type, pattern_signature)
                )
            ''')
            
            conn.commit()
            logger.info("✅ Learning tables initialized")
            
        except sqlite3.Error as e:
            logger.error(f"Error initializing learning tables: {e}")
            raise
    
    # ================================================================
    # LEARN FROM PROJECT
    # ================================================================
    
    def learn_from_project(self, project, revision_name: str = None):
        """یادگیری از یک پروژه (همه Revision ها یا یکی)"""
        try:
            # ============================================================
            # حالت 1: همه Revision ها
            # ============================================================
            if revision_name is None:
                if not project.revisions:
                    logger.warning(f"Project '{project.name}' has no revisions")
                    return
                
                logger.info(
                    f"📚 Learning from ALL {len(project.revisions)} revisions "
                    f"of '{project.name}'"
                )
                
                total_stats = {
                    'revisions_learned': 0,
                    'total_devices': 0,
                    'total_io': 0,
                }
                
                for revision in project.revisions:
                    try:
                        self._learn_from_single_revision(project.name, revision)
                        total_stats['revisions_learned'] += 1
                        total_stats['total_devices'] += len(revision.get_all_devices())
                        total_stats['total_io'] += revision.get_total_io()
                        logger.info(
                            f"  ✅ Learned '{revision.name}': "
                            f"{len(revision.sections)} sections, "
                            f"{len(revision.get_all_devices())} devices"
                        )
                    except Exception as e:
                        logger.error(f"  ❌ Failed to learn '{revision.name}': {e}")
                
                logger.info(
                    f"🎉 Learning complete for '{project.name}': "
                    f"{total_stats['revisions_learned']} revisions, "
                    f"{total_stats['total_devices']} devices, "
                    f"{total_stats['total_io']} I/O"
                )
            
            # ============================================================
            # حالت 2: یک Revision خاص
            # ============================================================
            else:
                revision = project.get_revision_by_name(revision_name)
                if not revision:
                    logger.warning(
                        f"Revision '{revision_name}' not found in '{project.name}'"
                    )
                    return
                
                logger.info(f"📚 Learning from '{project.name}' → '{revision.name}'")
                self._learn_from_single_revision(project.name, revision)
                logger.info(f"✅ Learning complete for '{project.name}' / '{revision.name}'")
        
        except Exception as e:
            logger.error(f"Error learning from project: {e}", exc_info=True)
    
    def _learn_from_single_revision(self, project_name: str, revision):
        """یادگیری از یک Revision خاص"""
        self._learn_component_patterns(project_name, revision)
        self._learn_equipment_patterns(project_name, revision)
        self._save_revision_analysis(project_name, revision)
    
    def learn_from_all_projects(self, projects: Dict) -> Dict[str, Any]:
        """یادگیری از همه پروژه‌ها و همه Revision ها"""
        stats = {
            'total_projects': len(projects),
            'total_revisions': 0,
            'total_devices': 0,
            'total_io': 0,
            'successful': 0,
            'failed': 0,
            'errors': [],
        }
        
        logger.info(f"🚀 Learning from ALL {len(projects)} projects...")
        
        for proj_name, project in projects.items():
            try:
                revisions_count = len(project.revisions)
                stats['total_revisions'] += revisions_count
                
                for revision in project.revisions:
                    try:
                        self._learn_from_single_revision(proj_name, revision)
                        stats['total_devices'] += len(revision.get_all_devices())
                        stats['total_io'] += revision.get_total_io()
                        stats['successful'] += 1
                    except Exception as e:
                        stats['failed'] += 1
                        stats['errors'].append(f"{proj_name}/{revision.name}: {e}")
                
                logger.info(f"  ✅ '{proj_name}': {revisions_count} revisions learned")
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"{proj_name}: {e}")
                logger.error(f"  ❌ Failed '{proj_name}': {e}")
        
        logger.info(
            f"🎉 Learning complete: "
            f"{stats['successful']} revisions, "
            f"{stats['total_devices']} devices, "
            f"{stats['total_io']} I/O"
        )
        return stats
    
    # ================================================================
    # COMPONENT PATTERNS
    # ================================================================
    
    def _learn_component_patterns(self, project_name: str, revision):
        """یادگیری الگوهای کامپوننت‌ها"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # پاک کردن الگوهای قبلی
            cursor.execute('''
                DELETE FROM learning_patterns
                WHERE project_name = ? AND revision_name = ?
                AND pattern_type = 'component'
            ''', (project_name, revision.name))
            
            # جمع‌آوری
            component_usage = {}
            for device in revision.get_all_devices():
                for field in device.NUMERIC_FIELDS:
                    if field in ['DI', 'DO', 'AI', 'AO']:
                        continue
                    qty = getattr(device, field, 0)
                    if qty > 0:
                        component_usage[field] = component_usage.get(field, 0) + qty
            
            # ذخیره
            now = datetime.now().isoformat()
            for comp_key, count in component_usage.items():
                cursor.execute('''
                    INSERT INTO learning_patterns
                    (project_name, revision_name, pattern_type, component_key,
                     component_count, usage_count, created_at, updated_at)
                    VALUES (?, ?, 'component', ?, ?, 1, ?, ?)
                ''', (project_name, revision.name, comp_key, count, now, now))
            
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error learning component patterns: {e}")
    
    # ================================================================
    # EQUIPMENT PATTERNS
    # ================================================================
    
    def _learn_equipment_patterns(self, project_name: str, revision):
        """
        یادگیری الگوهای تجهیزات
        
        ✅ اصلاح: اول تلاش برای استخراج نوع از SmartTag
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            io_calc = self._get_io_calculation()
            
            for device in revision.get_all_devices():
                # ============================================================
                # ✅ شناسایی نوع تجهیز (اولویت: استخراج از SmartTag)
                # ============================================================
                smart_tag = (getattr(device, 'SmartTag', '') or '').strip()
                
                equipment_type = None
                
                # 1. تلاش برای استخراج از SmartTag
                if smart_tag:
                    equipment_type = self._detect_equipment_type_from_tag(smart_tag)
                
                # 2. اگر نشد، از Name/Description
                if not equipment_type:
                    equipment_type = self._detect_equipment_type(device)
                
                # 3. اگر باز هم نشد، از SmartTag خام (به عنوان آخرین راه)
                if not equipment_type and smart_tag:
                    equipment_type = smart_tag.upper()
                
                if not equipment_type:
                    continue
                
                # ============================================================
                # استخراج کامپوننت‌های فعال
                # ============================================================
                active_components = []
                io_totals = {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0}
                
                for field in device.NUMERIC_FIELDS:
                    if field in ['DI', 'DO', 'AI', 'AO']:
                        continue
                    
                    qty = getattr(device, field, 0)
                    if qty > 0:
                        active_components.append(f"{field}:{qty}")
                        
                        if field in io_calc:
                            io_config = io_calc[field]
                            io_totals['DI'] += qty * io_config.get('DI', 0)
                            io_totals['DO'] += qty * io_config.get('DO', 0)
                            io_totals['AI'] += qty * io_config.get('AI', 0)
                            io_totals['AO'] += qty * io_config.get('AO', 0)
                
                if not active_components:
                    continue
                
                # ============================================================
                # ساخت signature
                # ============================================================
                pattern_signature = "|".join(sorted(active_components))
                io_signature = (
                    f"DI:{io_totals['DI']},DO:{io_totals['DO']},"
                    f"AI:{io_totals['AI']},AO:{io_totals['AO']}"
                )
                
                # ============================================================
                # بروزرسانی یا درج
                # ============================================================
                cursor.execute('''
                    SELECT id, usage_count, sample_projects
                    FROM learning_equipment_patterns
                    WHERE equipment_type = ? AND pattern_signature = ?
                ''', (equipment_type, pattern_signature))
                
                row = cursor.fetchone()
                
                if row:
                    usage_count = row[1] + 1
                    try:
                        sample_projects = json.loads(row[2] or '[]')
                    except Exception:
                        sample_projects = []
                    
                    project_key = f"{project_name}/{revision.name}"
                    if project_key not in sample_projects:
                        sample_projects.append(project_key)
                        sample_projects = sample_projects[-10:]
                    
                    cursor.execute('''
                        UPDATE learning_equipment_patterns
                        SET usage_count = ?, sample_projects = ?, updated_at = ?
                        WHERE id = ?
                    ''', (usage_count, json.dumps(sample_projects), now, row[0]))
                else:
                    cursor.execute('''
                        INSERT INTO learning_equipment_patterns
                        (equipment_type, pattern_signature, components, io_pattern,
                        usage_count, sample_projects, created_at, updated_at)
                        VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (
                        equipment_type,
                        pattern_signature,
                        json.dumps(active_components),
                        io_signature,
                        json.dumps([f"{project_name}/{revision.name}"]),
                        now,
                        now
                    ))
            
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error learning equipment patterns: {e}")
    
    def _detect_equipment_type_from_tag(self, tag: str) -> Optional[str]:
        """
        ✅ جدید: استخراج نوع تجهیز از SmartTag
        
        مثال‌ها:
            'AHU-01'    → 'AHU'
            'P-05a'     → 'PUMP'
            'CH-02'     → 'CHILLER'
            'FCU-12'    → 'FCU'
            'BLR-01'    → 'BOILER'
        """
        if not tag:
            return None
        
        tag_upper = tag.upper().strip()
        
        # ===== الگوهای prefix =====
        tag_patterns = {
            'AHU':      ['AHU', 'AIR HANDLING'],
            'PUMP':     ['P-', 'PU-', 'PMP-', 'PUMP-', 'CWP-', 'CHWP-', 'HWP-'],
            'FAN':      ['F-', 'FAN-', 'SF-', 'EF-', 'RF-', 'SUPPLY FAN', 'EXHAUST FAN'],
            'CHILLER':  ['CH-', 'CHL-', 'CHILLER-', 'CHLR-'],
            'BOILER':   ['BLR-', 'BL-', 'B-', 'BOILER-', 'HWB-'],
            'FCU':      ['FCU-', 'FC-', 'FANCOIL-'],
            'VAV':      ['VAV-'],
            'CT':       ['CT-', 'TOWER-', 'COOLING TOWER'],
            'DHW':      ['DHW-'],
            'BOOSTER':  ['BP-', 'BOOST-', 'BOOSTER-', 'JOCKEY-'],
            'EXPANSION':['ET-', 'EX-', 'EXP-', 'EXPANSION-'],
            'VSD':      ['VSD-', 'VFD-', 'INV-'],
            'VALVE':    ['VA-', 'VLV-', 'VALVE-'],
            'DAMPER':   ['DAM-', 'DMP-', 'DAMPER-'],
            'PANEL':    ['MCC-', 'PANEL-', 'PNL-'],
            'HEAT_EXCHANGER': ['HX-', 'HEX-', 'PHE-', 'HXCH-'],
            'PRIMARY_LOOP':   ['PL-', 'PRI-', 'PRIMARY-'],
            'SECONDARY_LOOP': ['SL-', 'SEC-', 'SECONDARY-'],
        }
        
        for eq_type, prefixes in tag_patterns.items():
            for prefix in prefixes:
                if tag_upper.startswith(prefix):
                    logger.debug(f"✅ Extracted '{eq_type}' from tag '{tag}'")
                    return eq_type
        
        # ===== اگر هیچ prefix پیدا نشد، فقط حروف اول را بگیر =====
        match = re.match(r'^([A-Z]{2,4})', tag_upper)
        if match:
            return match.group(1)
        
        return None
    
    def _detect_equipment_type(self, device) -> Optional[str]:
        """شناسایی نوع تجهیز از نام یا توضیحات"""
        name = (getattr(device, 'Name', '') or '').upper()
        desc = (getattr(device, 'Description', '') or '').upper()
        combined = f"{name} {desc}"
        
        patterns = {
            'PUMP': ['PUMP', 'پمپ', 'P-', 'PU-', 'CIRCULATOR', 'CWP', 'HWP'],
            'FAN': ['FAN', 'فن', 'BLOWER', 'SUPPLY', 'RETURN', 'EXHAUST'],
            'AHU': ['AHU', 'AIR HANDLING'],
            'CHILLER': ['CHILLER', 'چیلر'],
            'BOILER': ['BOILER', 'دیگ', 'بویلر', 'HWB'],
            'FCU': ['FCU', 'FANCOIL', 'FAN COIL', 'فن کویل'],
            'VAV': ['VAV', 'VARIABLE AIR'],
            'COOLING_TOWER': ['COOLING TOWER', 'برج خنک', 'CT-'],
            'VALVE': ['VALVE', 'شیر'],
            'DAMPER': ['DAMPER', 'دمپر'],
            'SENSOR': ['SENSOR', 'سنسور'],
            'MOTOR': ['MOTOR', 'موتور'],
            'PRIMARY_LOOP': ['PRIMARY LOOP', 'مدار اولیه'],
            'SECONDARY_LOOP': ['SECONDARY LOOP', 'مدار ثانویه'],
            'EXPANSION_TANK': ['EXPANSION TANK', 'منبع انبساط'],
            'DHW': ['DHW', 'DOMESTIC HOT WATER', 'آبگرم مصرفی'],
            'BOOSTER_PUMP': ['BOOSTER PUMP', 'بوسترپمپ', 'FIRE PUMP'],
        }
        
        for eq_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in combined:
                    return eq_type
        
        return None
    
    def _get_io_calculation(self):
        """دریافت IO_CALCULATION"""
        try:
            from core.constants import IO_CALCULATION
            return IO_CALCULATION
        except Exception:
            return {}
    
    def _save_revision_analysis(self, project_name: str, revision):
        """ذخیره تحلیل Revision"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            devices = revision.get_all_devices()
            total_devices = len(devices)
            total_sections = len(revision.sections)
            total_io = revision.get_total_io()
            avg_io = total_io / total_devices if total_devices > 0 else 0
            
            # ===== Component usage =====
            component_usage = {}
            for device in devices:
                for field in device.NUMERIC_FIELDS:
                    if field in ['DI', 'DO', 'AI', 'AO']:
                        continue
                    qty = getattr(device, field, 0)
                    if qty > 0:
                        component_usage[field] = component_usage.get(field, 0) + qty
            
            # ===== IO distribution =====
            io_dist = {
                'DI': sum(d.DI for d in devices),
                'DO': sum(d.DO for d in devices),
                'AI': sum(d.AI for d in devices),
                'AO': sum(d.AO for d in devices),
            }
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT OR REPLACE INTO learning_project_analysis
                (project_name, revision_name, total_devices, total_sections,
                 total_io, avg_io_per_device, component_usage, io_distribution, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                project_name,
                revision.name,
                total_devices,
                total_sections,
                total_io,
                avg_io,
                json.dumps(component_usage),
                json.dumps(io_dist),
                now
            ))
            
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error saving revision analysis: {e}")
    
    # ================================================================
    # ANALYZE PROJECT
    # ================================================================
    
    def analyze_project(self, project, revision_name: str = None) -> Dict[str, Any]:
        """
        تحلیل پروژه
        
        ✅ اصلاح: شامل 'patterns' می‌شود
        """
        try:
            if revision_name is None:
                revision = project.get_current_revision()
            else:
                revision = project.get_revision_by_name(revision_name)
            
            if not revision:
                return {'error': 'No revision found'}
            
            devices = revision.get_all_devices()
            component_usage = revision.get_component_usage()
            total_io = revision.get_total_io()
            
            # ✅ استخراج patterns
            patterns = self._extract_patterns(revision)
            
            return {
                'project_name': project.name,
                'revision_name': revision.name,
                'total_devices': len(devices),
                'total_sections': len(revision.sections),
                'total_io': total_io,
                'avg_io_per_device': total_io / len(devices) if devices else 0,
                'component_usage': component_usage,
                'io_distribution': {
                    'DI': sum(d.DI for d in devices),
                    'DO': sum(d.DO for d in devices),
                    'AI': sum(d.AI for d in devices),
                    'AO': sum(d.AO for d in devices),
                },
                'patterns': patterns,   # ✅ جدید
            }
        except Exception as e:
            logger.error(f"Error analyzing project: {e}")
            return {'error': str(e)}
    
    def _extract_patterns(self, revision) -> Dict[str, Any]:
        """
        ✅ جدید: استخراج الگوهای تکراری از یک revision
        """
        patterns = {
            'common_combinations': [],
            'repeated_devices': [],
        }
        
        try:
            # ===== الگوهای ترکیب کامپوننت =====
            combos = Counter()
            for device in revision.get_all_devices():
                active = []
                for field in device.NUMERIC_FIELDS:
                    if field in ['DI', 'DO', 'AI', 'AO']:
                        continue
                    if getattr(device, field, 0) > 0:
                        active.append(field)
                
                if active:
                    key = tuple(sorted(active))
                    combos[key] += 1
            
            # ۳ الگوی برتر (حداقل ۲ بار تکرار)
            for combo, count in combos.most_common(5):
                if count >= 2:
                    patterns['common_combinations'].append({
                        'components': list(combo),
                        'count': count,
                    })
            
            # ===== دستگاه‌های تکراری (بر اساس SmartTag) =====
            tag_counter = Counter()
            for device in revision.get_all_devices():
                tag = (getattr(device, 'SmartTag', '') or '').strip().upper()
                if tag:
                    tag_counter[tag] += 1
            
            for tag, count in tag_counter.most_common(5):
                if count >= 2:
                    patterns['repeated_devices'].append({
                        'tag': tag,
                        'count': count,
                    })
        
        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
        
        return patterns
    
    # ================================================================
    # COMPARE REVISIONS
    # ================================================================
    
    def compare_revisions(self, project, revision_a: str, revision_b: str) -> Dict[str, Any]:
        """مقایسه دو Revision از یک پروژه"""
        try:
            rev_a = project.get_revision_by_name(revision_a)
            rev_b = project.get_revision_by_name(revision_b)
            
            if not rev_a or not rev_b:
                return {'error': 'One or both revisions not found'}
            
            stats_a = rev_a.get_statistics()
            stats_b = rev_b.get_statistics()
            
            comp_a = rev_a.get_component_usage()
            comp_b = rev_b.get_component_usage()
            
            all_components = set(comp_a.keys()) | set(comp_b.keys())
            
            component_diff = {}
            for comp in all_components:
                count_a = comp_a.get(comp, 0)
                count_b = comp_b.get(comp, 0)
                diff = count_b - count_a
                
                if diff != 0 or count_a > 0 or count_b > 0:
                    component_diff[comp] = {
                        'count_a': count_a,
                        'count_b': count_b,
                        'diff': diff,
                        'status': self._get_diff_status(diff),
                    }
            
            devices_a = {d.Name: d for d in rev_a.get_all_devices() if d.Name}
            devices_b = {d.Name: d for d in rev_b.get_all_devices() if d.Name}
            
            added_devices = set(devices_b.keys()) - set(devices_a.keys())
            removed_devices = set(devices_a.keys()) - set(devices_b.keys())
            common_devices = set(devices_a.keys()) & set(devices_b.keys())
            
            modified_devices = []
            for dev_name in common_devices:
                dev_a = devices_a[dev_name]
                dev_b = devices_b[dev_name]
                
                io_a = {
                    'DI': dev_a.DI, 'DO': dev_a.DO,
                    'AI': dev_a.AI, 'AO': dev_a.AO,
                    'total': dev_a.get_total_io()
                }
                io_b = {
                    'DI': dev_b.DI, 'DO': dev_b.DO,
                    'AI': dev_b.AI, 'AO': dev_b.AO,
                    'total': dev_b.get_total_io()
                }
                
                if io_a != io_b:
                    modified_devices.append({
                        'name': dev_name,
                        'io_a': io_a,
                        'io_b': io_b,
                        'diff_total': io_b['total'] - io_a['total'],
                    })
            
            sections_a = {s.name for s in rev_a.sections}
            sections_b = {s.name for s in rev_b.sections}
            
            added_sections = sections_b - sections_a
            removed_sections = sections_a - sections_b
            
            io_diff = {
                'DI': stats_b['total_di'] - stats_a['total_di'],
                'DO': stats_b['total_do'] - stats_a['total_do'],
                'AI': stats_b['total_ai'] - stats_a['total_ai'],
                'AO': stats_b['total_ao'] - stats_a['total_ao'],
                'total': stats_b['total_io'] - stats_a['total_io'],
            }
            
            return {
                'revision_a': revision_a,
                'revision_b': revision_b,
                'stats_a': stats_a,
                'stats_b': stats_b,
                'io_diff': io_diff,
                'component_diff': component_diff,
                'devices_added': list(added_devices),
                'devices_removed': list(removed_devices),
                'devices_modified': modified_devices,
                'sections_added': list(added_sections),
                'sections_removed': list(removed_sections),
                'summary': {
                    'total_added_devices': len(added_devices),
                    'total_removed_devices': len(removed_devices),
                    'total_modified_devices': len(modified_devices),
                    'total_added_sections': len(added_sections),
                    'total_removed_sections': len(removed_sections),
                    'io_change': io_diff['total'],
                }
            }
        except Exception as e:
            logger.error(f"Error comparing revisions: {e}", exc_info=True)
            return {'error': str(e)}
    
    def _get_diff_status(self, diff: int) -> str:
        """وضعیت تفاوت"""
        if diff > 0:
            return 'added'
        elif diff < 0:
            return 'removed'
        else:
            return 'same'
    
    # ================================================================
    # PREDICT
    # ================================================================
    
    def predict_component_needs(self, devices: List) -> List[Dict]:
        """پیش‌بینی نیازهای کامپوننت"""
        try:
            predictions = []
            
            equipment_counts = {}
            for device in devices:
                # ✅ اصلاح: از tag استفاده کن
                smart_tag = (getattr(device, 'SmartTag', '') or '').strip()
                eq_type = None
                
                if smart_tag:
                    eq_type = self._detect_equipment_type_from_tag(smart_tag)
                
                if not eq_type:
                    eq_type = self._detect_equipment_type(device)
                
                if eq_type:
                    equipment_counts[eq_type] = equipment_counts.get(eq_type, 0) + 1
            
            for eq_type, count in equipment_counts.items():
                patterns = self._get_patterns_for_equipment(eq_type)
                
                if patterns:
                    best = patterns[0]
                    
                    # ✅ اضافه کردن label
                    label = self._get_equipment_label(eq_type)
                    
                    predictions.append({
                        'equipment_type': eq_type,
                        'label': label,
                        'count': count,
                        'suggested_components': best.get('components', []),
                        'reason': f"Based on {best.get('usage_count', 0)} similar devices",
                        'priority': 'high' if best.get('usage_count', 0) > 3 else 'medium',
                    })
            
            return predictions
        except Exception as e:
            logger.error(f"Error predicting components: {e}")
            return []
    
    def _get_equipment_label(self, eq_type: str) -> str:
        """✅ جدید: برچسب فارسی برای نوع تجهیز"""
        labels = {
            'PUMP': 'پمپ',
            'FAN': 'فن',
            'AHU': 'هواساز',
            'CHILLER': 'چیلر',
            'BOILER': 'بویلر',
            'FCU': 'فن‌کویل',
            'VAV': 'VAV',
            'COOLING_TOWER': 'برج خنک‌کننده',
            'VALVE': 'شیر',
            'DAMPER': 'دمپر',
            'SENSOR': 'سنسور',
            'MOTOR': 'موتور',
            'DHW': 'آبگرم مصرفی',
            'BOOSTER_PUMP': 'بوسترپمپ',
            'EXPANSION_TANK': 'منبع انبساط',
            'PRIMARY_LOOP': 'مدار اولیه',
            'SECONDARY_LOOP': 'مدار ثانویه',
            'VSD': 'درایو دور متغیر',
            'PANEL': 'تابلو برق',
            'HEAT_EXCHANGER': 'مبدل حرارتی',
        }
        return labels.get(eq_type, eq_type)
    
    def _get_patterns_for_equipment(self, equipment_type: str) -> List[Dict]:
        """دریافت الگوهای یک نوع تجهیز"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT equipment_type, components, io_pattern, usage_count, sample_projects
                FROM learning_equipment_patterns
                WHERE equipment_type = ?
                ORDER BY usage_count DESC
                LIMIT 10
            ''', (equipment_type,))
            
            patterns = []
            for row in cursor.fetchall():
                try:
                    components = json.loads(row[1] or '[]')
                except Exception:
                    components = []
                
                try:
                    sample_projects = json.loads(row[4] or '[]')
                except Exception:
                    sample_projects = []
                
                patterns.append({
                    'equipment_type': row[0],
                    'components': components,
                    'io_pattern': row[2],
                    'usage_count': row[3],
                    'sample_projects': sample_projects,
                })
            
            return patterns
        except sqlite3.Error as e:
            logger.error(f"Error getting patterns: {e}")
            return []
    
    # ================================================================
    # STATISTICS
    # ================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        آمار کلی یادگیری
        
        ✅ اصلاح: شامل label در most_common_components
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # تعداد پروژه‌ها
            cursor.execute("SELECT COUNT(DISTINCT project_name) FROM learning_project_analysis")
            total_projects = cursor.fetchone()[0]
            
            # تعداد Revision ها
            cursor.execute("SELECT COUNT(*) FROM learning_project_analysis")
            total_revisions = cursor.fetchone()[0]
            
            # تعداد الگوهای کامپوننت
            cursor.execute(
                "SELECT COUNT(*) FROM learning_patterns WHERE pattern_type = 'component'"
            )
            total_components = cursor.fetchone()[0]
            
            # تعداد الگوهای تجهیزات
            cursor.execute("SELECT COUNT(*) FROM learning_equipment_patterns")
            total_equipment_patterns = cursor.fetchone()[0]
            
            # پرکاربردترین کامپوننت‌ها
            cursor.execute('''
                SELECT component_key, SUM(component_count) as total
                FROM learning_patterns
                WHERE pattern_type = 'component'
                GROUP BY component_key
                ORDER BY total DESC
                LIMIT 10
            ''')
            
            most_common = []
            for row in cursor.fetchall():
                key = row[0]
                count = row[1]
                label = self._get_component_label(key)
                most_common.append({
                    'component': key,
                    'label': label,      # ✅ جدید
                    'count': count,
                })
            
            # پرکاربردترین تجهیزات
            cursor.execute('''
                SELECT equipment_type, SUM(usage_count) as total
                FROM learning_equipment_patterns
                GROUP BY equipment_type
                ORDER BY total DESC
                LIMIT 10
            ''')
            
            top_equipment = []
            for row in cursor.fetchall():
                top_equipment.append({
                    'type': row[0],
                    'label': self._get_equipment_label(row[0]),   # ✅ جدید
                    'count': row[1],
                })
            
            # لیست پروژه‌های تحلیل شده
            cursor.execute('''
                SELECT project_name, revision_name, total_devices, total_io
                FROM learning_project_analysis
                ORDER BY project_name, revision_name
            ''')
            
            analyzed_list = []
            for row in cursor.fetchall():
                analyzed_list.append({
                    'project': row[0],
                    'revision': row[1],
                    'devices': row[2],
                    'io': row[3],
                })
            
            return {
                'total_projects_analyzed': total_projects,
                'total_revisions_analyzed': total_revisions,   # ✅ اضافه شد
                'total_components_learned': total_components,
                'total_io_patterns': total_equipment_patterns,
                'total_equipment_types': len(top_equipment),
                'most_common_components': most_common,
                'top_equipment_types': top_equipment,
                'analyzed_list': analyzed_list,
            }
        except sqlite3.Error as e:
            logger.error(f"Error getting statistics: {e}")
            return self._empty_stats()
    
    def _get_component_label(self, key: str, lang: str = 'fa') -> str:
        """✅ جدید: برچسب کامپوننت"""
        try:
            from core.constants import COMPONENT_LABELS
            return COMPONENT_LABELS.get(key, {}).get(lang, key)
        except Exception:
            return key
    
    def _empty_stats(self) -> Dict[str, Any]:
        """آمار خالی"""
        return {
            'total_projects_analyzed': 0,
            'total_revisions_analyzed': 0,
            'total_components_learned': 0,
            'total_io_patterns': 0,
            'total_equipment_types': 0,
            'most_common_components': [],
            'top_equipment_types': [],
            'analyzed_list': [],
        }
    
    # ================================================================
    # OPTIMIZATION (✅ جدید)
    # ================================================================
    
    def _suggest_io_optimization(self, current_io: Dict[str, int]) -> List[Dict]:
        """
        ✅ جدید: پیشنهاد بهینه‌سازی I/O
        
        Args:
            current_io: {'DI': int, 'DO': int, 'AI': int, 'AO': int}
        
        Returns:
            لیست پیشنهادات
        """
        suggestions = []
        total = sum(current_io.values())
        
        # ===== پیشنهاد ۱: I/O زیاد =====
        if total > 500:
            suggestions.append({
                'message': f'مجموع I/O شما ({total}) زیاد است.',
                'suggestion': 'استفاده از کنترلرهای توزیع‌شده (Distributed) را در نظر بگیرید.',
            })
        
        # ===== پیشنهاد ۲: I/O کم =====
        if total < 50:
            suggestions.append({
                'message': f'مجموع I/O کوچک است ({total}).',
                'suggestion': 'می‌توان از کنترلرهای کوچک‌تر مثل MCX-08m2 استفاده کرد.',
            })
        
        # ===== پیشنهاد ۳: نسبت AI به DI =====
        di = current_io.get('DI', 0)
        ai = current_io.get('AI', 0)
        if di > 0:
            ai_ratio = ai / di
            if ai_ratio < 0.2:
                suggestions.append({
                    'message': f'نسبت AI به DI پایین است ({ai_ratio:.2f}).',
                    'suggestion': 'شاید برخی نقاط آنالوگ را می‌توان با دیجیتال جایگزین کرد.',
                })
            elif ai_ratio > 2.0:
                suggestions.append({
                    'message': f'نسبت AI به DI بالا است ({ai_ratio:.2f}).',
                    'suggestion': 'مطمئن شوید همه سنسورهای آنالوگ ضروری هستند.',
                })
        
        # ===== پیشنهاد ۴: AO بیشتر از AI =====
        ao = current_io.get('AO', 0)
        if ao > ai:
            suggestions.append({
                'message': f'تعداد AO ({ao}) بیشتر از AI ({ai}) است.',
                'suggestion': 'مطمئن شوید که همه AO ها واقعاً ضروری هستند.',
            })
        
        # ===== پیشنهاد ۵: DO بیشتر از DI =====
        do = current_io.get('DO', 0)
        if do > di * 1.5 and di > 0:
            suggestions.append({
                'message': f'نسبت DO به DI بالا است ({do}/{di}).',
                'suggestion': 'بررسی کنید آیا برخی فرمان‌ها را می‌توان از طریق شبکه ارسال کرد.',
            })
        
        if not suggestions:
            suggestions.append({
                'message': 'توزیع I/O شما متعادل است.',
                'suggestion': 'طراحی فعلی به نظر می‌رسد بهینه باشد.',
            })
        
        return suggestions
    
    # ================================================================
    # SIMILAR PROJECTS
    # ================================================================
    
    def _find_similar_projects(self, project) -> List[Dict]:
        """پیدا کردن پروژه‌های مشابه"""
        try:
            current_rev = project.get_current_revision()
            if not current_rev:
                return []
            
            current_components = current_rev.get_component_usage()
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT project_name, revision_name, component_usage, io_distribution, total_io, total_devices
                FROM learning_project_analysis
                WHERE project_name != ?
            ''', (project.name,))
            
            similar = []
            
            for row in cursor.fetchall():
                proj_name, rev_name, comp_usage_json, io_json, total_io, total_devices = row
                
                try:
                    comp_usage = json.loads(comp_usage_json or '{}')
                    sim_score = self._calculate_similarity(current_components, comp_usage)
                    
                    if sim_score > 20:
                        similar.append({
                            'project_name': proj_name,
                            'revision_name': rev_name,
                            'similarity': round(sim_score, 1),
                            'component_similarity': sim_score,
                            'io_similarity': sim_score,
                            'io_total': total_io,
                            'devices_count': total_devices or 0,
                            'common_components': list(
                                set(current_components.keys()) & set(comp_usage.keys())
                            ),
                            'unique_components': list(
                                set(comp_usage.keys()) - set(current_components.keys())
                            ),
                        })
                except Exception:
                    continue
            
            similar.sort(key=lambda x: x['similarity'], reverse=True)
            return similar[:10]
        except Exception as e:
            logger.error(f"Error finding similar projects: {e}")
            return []
    
    def _calculate_similarity(self, comp_a: Dict, comp_b: Dict) -> float:
        """محاسبه شباهت"""
        if not comp_a or not comp_b:
            return 0.0
        
        keys_a = set(comp_a.keys())
        keys_b = set(comp_b.keys())
        
        intersection = len(keys_a & keys_b)
        union = len(keys_a | keys_b)
        
        if union == 0:
            return 0.0
        
        return (intersection / union) * 100
    
    # ================================================================
    # TEMPLATES (✅ جدید)
    # ================================================================
    
    def _get_project_templates(self) -> List[Dict]:
        """
        ✅ جدید: دریافت قالب‌های پروژه از پروژه‌های قبلی
        
        Returns:
            لیست قالب‌ها
        """
        templates = []
        
        try:
            # ===== چک app =====
            if not self.app or not hasattr(self.app, 'projects'):
                return []
            
            # ===== از هر پروژه یک قالب =====
            for proj_name, project in self.app.projects.items():
                current_rev = project.get_current_revision()
                if not current_rev:
                    continue
                
                devices = current_rev.get_all_devices()
                if not devices:
                    continue
                
                # ===== انواع سکشن =====
                section_types = set()
                for section in current_rev.sections:
                    try:
                        from ai.proposal_section_detector import ProposalSectionDetector
                        detector = ProposalSectionDetector()
                        stype = detector.detect(
                            getattr(section, 'name', ''),
                            getattr(section, 'description', '')
                        )
                        if stype:
                            section_types.add(stype)
                    except Exception:
                        pass
                
                # ===== کامپوننت‌های اصلی =====
                comp_usage = current_rev.get_component_usage()
                top_components = sorted(
                    comp_usage.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                
                templates.append({
                    'name': proj_name,
                    'description': (
                        f"{len(current_rev.sections)} سکشن، "
                        f"{len(devices)} دستگاه، "
                        f"{current_rev.get_total_io()} I/O"
                    ),
                    'sections': ', '.join(sorted(section_types)) if section_types else '—',
                    'top_components': [
                        self._get_component_label(k) for k, _ in top_components
                    ],
                    'device_count': len(devices),
                    'io_count': current_rev.get_total_io(),
                })
            
            # ===== مرتب‌سازی: بزرگ‌ترین اول =====
            templates.sort(key=lambda x: x['io_count'], reverse=True)
            return templates[:10]
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return []
    
    # ================================================================
    # BEST PRACTICES
    # ================================================================
    
    def _get_best_practices(self, project=None) -> List[str]:
        """بهترین روش‌ها"""
        return [
            "Use unique device names (P5a, P5b or P5, P6, P7)",
            "Match FS count with PU count for each pump",
            "Match VSD count with PU count if using VFD",
            "Group similar devices in dedicated sections",
            "Use consistent component naming across projects",
            "Keep spare I/O (SPR) for future expansion",
            "Document Modbus devices separately",
            "Use AI sensors for critical measurements",
            "Verify cable sizes match component requirements",
            "Review validation errors before export",
        ]
    
    # ================================================================
    # LIVE SUGGESTIONS
    # ================================================================
    
    def get_live_suggestions(self, name: str, description: str,
                            info: str, section_name: str = "") -> Dict[str, Any]:
        """پیشنهادات زنده"""
        try:
            combined = f"{name} {description} {info}".upper()
            
            equipment_type = None
            keywords_map = {
                'PUMP': ['PUMP', 'پمپ', 'P-', 'PU-'],
                'FAN': ['FAN', 'فن', 'BLOWER'],
                'AHU': ['AHU'],
                'CHILLER': ['CHILLER', 'چیلر'],
                'BOILER': ['BOILER', 'دیگ'],
                'FCU': ['FCU', 'FANCOIL'],
                'VAV': ['VAV'],
                'COOLING_TOWER': ['COOLING TOWER', 'برج'],
                'VALVE': ['VALVE', 'شیر'],
                'DAMPER': ['DAMPER', 'دمپر'],
                'SENSOR': ['SENSOR', 'سنسور'],
                'MOTOR': ['MOTOR', 'موتور'],
            }
            
            for eq_type, keywords in keywords_map.items():
                for kw in keywords:
                    if kw in combined:
                        equipment_type = eq_type
                        break
                if equipment_type:
                    break
            
            if not equipment_type:
                return {'equipment_type': None, 'suggestions': []}
            
            patterns = self._get_patterns_for_equipment(equipment_type)
            
            if not patterns:
                return {
                    'equipment_type': equipment_type,
                    'suggestions': self._get_default_suggestions(equipment_type),
                }
            
            best = patterns[0]
            suggestions = []
            
            for comp_str in best.get('components', []):
                if ':' in comp_str:
                    key, qty = comp_str.split(':')
                    try:
                        qty = int(qty)
                    except Exception:
                        qty = 1
                    
                    suggestions.append({
                        'component': key,
                        'qty': qty,
                        'label': self._get_component_label(key),
                        'io': self._get_component_io(key),
                    })
            
            return {
                'equipment_type': equipment_type,
                'suggestions': suggestions,
                'based_on_count': best.get('usage_count', 1),
            }
        except Exception as e:
            logger.error(f"Error getting live suggestions: {e}")
            return {'equipment_type': None, 'suggestions': []}
    
    def _get_default_suggestions(self, equipment_type: str) -> List[Dict]:
        """پیشنهادات پیش‌فرض"""
        defaults = {
            'PUMP': [
                {'component': 'PU', 'qty': 1},
                {'component': 'FA', 'qty': 1},
                {'component': 'FE', 'qty': 1},
                {'component': 'SLE', 'qty': 1},
                {'component': 'CMD', 'qty': 1},
            ],
            'FAN': [
                {'component': 'PU', 'qty': 1},
                {'component': 'FA', 'qty': 1},
                {'component': 'FE', 'qty': 1},
                {'component': 'CMD', 'qty': 1},
            ],
            'AHU': [
                {'component': 'DTS', 'qty': 1},
                {'component': 'DTHS', 'qty': 1},
                {'component': 'FS', 'qty': 1},
            ],
        }
        
        components = defaults.get(equipment_type, [])
        
        for comp in components:
            comp['label'] = self._get_component_label(comp['component'])
            comp['io'] = self._get_component_io(comp['component'])
        
        return components
    
    def _get_component_io(self, key: str) -> Dict[str, int]:
        """I/O کامپوننت"""
        try:
            from core.constants import IO_CALCULATION
            return IO_CALCULATION.get(key, {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0})
        except Exception:
            return {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0}
    
    # ================================================================
    # QUERY PARSER
    # ================================================================
    
    def _parse_query(self, query: str) -> Dict[str, Any]:
        """پارس کردن query کاربر"""
        result = {
            'keyword': '',
            'filters': {},
        }
        
        if not query:
            return result
        
        parts = [p.strip() for p in query.split(',') if p.strip()]
        if not parts:
            return result
        
        result['keyword'] = parts[0].lower()
        
        import re
        for part in parts[1:]:
            part = part.strip()
            if not part:
                continue
            
            # الگوی 1: "2 ITS"
            match = re.match(r'^(\d+)\s*([A-Za-z_]+)$', part)
            if match:
                result['filters'][match.group(2).upper()] = int(match.group(1))
                continue
            
            # الگوی 2: "ITS=2" یا "ITS:2"
            match = re.match(r'^([A-Za-z_]+)\s*[=:]\s*(\d+)$', part)
            if match:
                result['filters'][match.group(1).upper()] = int(match.group(2))
                continue
            
            # الگوی 3: "ITS 2"
            match = re.match(r'^([A-Za-z_]+)\s+(\d+)$', part)
            if match:
                result['filters'][match.group(1).upper()] = int(match.group(2))
                continue
        
        return result
    
    # ================================================================
    # SMART MODEL SEARCH
    # ================================================================
    
    def get_similar_models(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """پیدا کردن مدل‌های مشابه بر اساس query"""
        try:
            parsed = self._parse_query(query)
            keyword = parsed['keyword']
            filters = parsed['filters']
            
            if not keyword or len(keyword) < 2:
                return []
            
            logger.info(f"🔍 Searching models: keyword='{keyword}', filters={filters}")
            
            # ===== چک app =====
            if not self.app or not hasattr(self.app, 'projects'):
                logger.warning("⚠️ app.projects not available")
                return []
            
            models = {}
            
            for proj_name, project in self.app.projects.items():
                for revision in project.revisions:
                    for device in revision.get_all_devices():
                        search_text = " ".join([
                            (getattr(device, 'Name', '') or ""),
                            (getattr(device, 'Description', '') or ""),
                            (getattr(device, 'INFO', '') or ""),
                            (getattr(device, 'SmartTag', '') or ""),
                        ]).lower()
                        
                        if keyword not in search_text:
                            continue
                        
                        components = {}
                        for field in device.NUMERIC_FIELDS:
                            if field in ['DI', 'DO', 'AI', 'AO']:
                                continue
                            qty = getattr(device, field, 0)
                            if qty > 0:
                                components[field] = qty
                        
                        if not components:
                            continue
                        
                        # فیلترها
                        match_filters = True
                        for comp_key, required_qty in filters.items():
                            actual_qty = components.get(comp_key, 0)
                            if actual_qty != required_qty:
                                match_filters = False
                                break
                        
                        if not match_filters:
                            continue
                        
                        pattern_key = json.dumps(components, sort_keys=True)
                        
                        model_name = (
                            getattr(device, 'SmartTag', '') or
                            getattr(device, 'Name', '') or
                            getattr(device, 'Description', '') or
                            "Unnamed Model"
                        ).strip()
                        
                        if pattern_key not in models:
                            models[pattern_key] = {
                                'name': model_name,
                                'description': getattr(device, 'Description', '') or '',
                                'info': getattr(device, 'INFO', '') or '',
                                'smart_tag': getattr(device, 'SmartTag', '') or '',
                                'components': components,
                                'usage_count': 0,
                                'last_used': '',
                                'sample_devices': [],
                            }
                        models[pattern_key]['usage_count'] += 1
                        
                        device_info = f"{proj_name}/{revision.name}/{getattr(device, 'Name', 'Unnamed')}"
                        if device_info not in models[pattern_key]['sample_devices']:
                            models[pattern_key]['sample_devices'].append(device_info)
                            models[pattern_key]['sample_devices'] = (
                                models[pattern_key]['sample_devices'][-5:]
                            )
            
            result = list(models.values())
            result.sort(key=lambda x: x['usage_count'], reverse=True)
            return result[:limit]
        except Exception as e:
            logger.error(f"Error searching models: {e}", exc_info=True)
            return []


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['LearningEngine']