# ai/pattern_matcher.py
"""
تطبیق الگو با پروژه‌های جدید
"""

import json
import logging
from typing import Dict, List, Optional, Any
from collections import defaultdict

from ai.proposal_section_detector import ProposalSectionDetector

logger = logging.getLogger(__name__)


class PatternMatcher:
    """تطبیق الگو با پروژه جدید"""
    
    def __init__(self, db_manager, app):
        self.db = db_manager
        self.app = app
        self.detector = ProposalSectionDetector()
    
    def predict_components(self, project, revision_name: str = None) -> Dict[str, Any]:
        """پیش‌بینی کامپوننت‌ها"""
        try:
            if revision_name:
                revision = project.get_revision_by_name(revision_name)
            else:
                revision = project.get_current_revision()
            
            if not revision:
                return {}
            
            sections_by_type = self.detector.group_sections_by_type(revision.sections)
            
            predictions = defaultdict(int)
            based_on = []
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            for section_type, sections in sections_by_type.items():
                if section_type == '_unknown':
                    continue
                
                device_count = sum(len(s.devices) for s in sections)
                
                cursor.execute('''
                    SELECT components_json, device_count, usage_count
                    FROM component_patterns
                    WHERE section_type = ?
                    ORDER BY usage_count DESC
                    LIMIT 5
                ''', (section_type,))
                
                patterns = cursor.fetchall()
                if not patterns:
                    continue
                
                component_totals = defaultdict(float)
                total_weight = 0
                
                for pattern_json, pattern_devices, usage_count in patterns:
                    try:
                        components = json.loads(pattern_json or '{}')
                    except:
                        continue
                    
                    weight = max(1, usage_count)
                    total_weight += weight
                    
                    ratio = device_count / pattern_devices if pattern_devices > 0 else 1.0
                    
                    for comp, count in components.items():
                        component_totals[comp] += count * weight * ratio
                
                if total_weight > 0:
                    for comp, total in component_totals.items():
                        avg = total / total_weight
                        predictions[comp] += int(round(avg))
                
                if section_type not in based_on:
                    based_on.append(section_type)
            
            anomalies = self._detect_anomalies(revision, predictions)
            
            return {
                'predictions': dict(predictions),
                'anomalies': anomalies,
                'based_on': based_on,
            }
        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)
            return {}
    
    def _detect_anomalies(self, revision, predictions: Dict[str, int]) -> List[Dict[str, Any]]:
        """تشخیص خطا"""
        anomalies = []
        
        current = defaultdict(int)
        for device in revision.get_all_devices():
            for field in device.NUMERIC_FIELDS:
                if field in ['DI', 'DO', 'AI', 'AO']:
                    continue
                qty = getattr(device, field, 0)
                if qty > 0:
                    current[field] += qty
        
        rules = [
            {
                'condition': lambda c: c.get('PU', 0) > 0 and c.get('FS', 0) == 0,
                'message': '⚠️ PU دارد اما FS ندارد!',
                'suggestion': 'برای هر پمپ، یک FS لازم است.',
            },
            {
                'condition': lambda c: c.get('VSD', 0) > c.get('PU', 0),
                'message': '⚠️ تعداد VSD بیشتر از PU است.',
                'suggestion': 'هر VSD باید به یک PU متصل باشد.',
            },
        ]
        
        for rule in rules:
            try:
                if rule['condition'](current):
                    anomalies.append({
                        'message': rule['message'],
                        'suggestion': rule['suggestion'],
                    })
            except:
                continue
        
        return anomalies
    
    def get_patterns_summary(self) -> Dict[str, Any]:
        """خلاصه الگوها"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM project_patterns")
            total_projects = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM component_patterns")
            total_components = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT section_type, COUNT(*), AVG(device_count)
                FROM component_patterns
                GROUP BY section_type
                ORDER BY COUNT(*) DESC
            ''')
            
            sections_stats = []
            for row in cursor.fetchall():
                sections_stats.append({
                    'section_type': row[0],
                    'count': row[1],
                    'avg_devices': round(row[2] or 0, 1),
                })
            
            return {
                'total_projects': total_projects,
                'total_component_patterns': total_components,
                'sections_stats': sections_stats,
            }
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return {}


__all__ = ['PatternMatcher']