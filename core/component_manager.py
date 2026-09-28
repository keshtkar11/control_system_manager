"""مدیریت کامپوننت‌ها (پیش‌فرض و سفارشی)"""

import sqlite3
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from core.constants import (
    COMPONENT_LABELS, 
    COMPONENT_LABELS_FA, 
    COMPONENT_LABELS_EN,
    IO_CALCULATION, 
    CABLE_SIZE,
    COLORS
)

logger = logging.getLogger(__name__)

class ComponentManager:
    """
    مدیریت کامپوننت‌های پیش‌فرض و سفارشی
    """

    def __init__(self, db_manager):
        """
        Args:
            db_manager: نمونه DatabaseManager برای دسترسی به دیتابیس
        """
        self.db = db_manager
        self._custom_components: Dict[str, Dict] = {}
        self._all_components: Dict[str, Dict] = {}
        self._load_custom_components()
        self._merge_components()

    # ================================================================
    # ✅ فقط یک نسخه از این متد باید وجود داشته باشد
    # ================================================================
    def _load_custom_components(self):
        """بارگذاری کامپوننت‌های سفارشی از دیتابیس و همگام‌سازی با COMPONENT_LABELS"""
        from core.constants import COMPONENT_LABELS, IO_CALCULATION, CABLE_SIZE
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # بررسی وجود جدول
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='custom_components'
            """)
            
            if not cursor.fetchone():
                self._create_custom_components_table(cursor)
                # ✅ اضافه کردن کامپوننت‌های پیش‌فرض بعد از ایجاد جدول
                self._insert_default_components(cursor)
                conn.commit()
                # بعد از commit، دوباره بارگذاری کن
                self._load_custom_components()
                return
            
            # ================================================================
            # ✅ همگام‌سازی: اضافه کردن کامپوننت‌های جدید از COMPONENT_LABELS
            # ================================================================
            cursor.execute("SELECT key FROM custom_components")
            existing_keys = {row[0] for row in cursor.fetchall()}
            
            added_count = 0
            for key, labels in COMPONENT_LABELS.items():
                if key not in existing_keys:
                    io = IO_CALCULATION.get(key, {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0})
                    cable = CABLE_SIZE.get(key, '2x1mm²')
                    now = datetime.now().isoformat()
                    
                    cursor.execute('''
                        INSERT INTO custom_components 
                        (key, label_fa, label_en, di, do, ai, ao, cable_size, is_active, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        key,
                        labels.get('fa', key),
                        labels.get('en', key),
                        io.get('DI', 0),
                        io.get('DO', 0),
                        io.get('AI', 0),
                        io.get('AO', 0),
                        cable,
                        1,
                        now,
                        now
                    ))
                    added_count += 1
                    logger.info(f"Synced new default component: {key}")
            
            if added_count > 0:
                conn.commit()
                logger.info(f"Added {added_count} new components to database")
            
            # ================================================================
            # ✅ بارگذاری کامپوننت‌های سفارشی
            # ================================================================
            cursor.execute('''
                SELECT key, label_fa, label_en, di, do, ai, ao, 
                    cable_size, is_active, created_at, updated_at
                FROM custom_components
                WHERE is_active = 1
            ''')
            
            # ✅ پاک کردن کش قبلی
            self._custom_components.clear()
            
            for row in cursor.fetchall():
                key, label_fa, label_en, di, do, ai, ao, cable_size, is_active, created_at, updated_at = row
                self._custom_components[key] = {
                    'fa': label_fa,
                    'en': label_en,
                    'io': {'DI': di, 'DO': do, 'AI': ai, 'AO': ao},
                    'cable_size': cable_size or '2x1mm²',
                    'is_active': bool(is_active),
                    'created_at': created_at,
                    'updated_at': updated_at
                }
            
            cursor.close()
            self._merge_components()
            logger.info(f"Loaded {len(self._custom_components)} custom components")
            
        except Exception as e:
            logger.error(f"Error loading custom components: {e}")

    def _insert_default_components(self, cursor):
        """اضافه کردن تمام کامپوننت‌های پیش‌فرض به دیتابیس (برای اولین بار)"""
        from core.constants import COMPONENT_LABELS, IO_CALCULATION, CABLE_SIZE
        
        now = datetime.now().isoformat()
        
        for key, labels in COMPONENT_LABELS.items():
            io = IO_CALCULATION.get(key, {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0})
            cable = CABLE_SIZE.get(key, '2x1mm²')
            
            cursor.execute('''
                INSERT INTO custom_components 
                (key, label_fa, label_en, di, do, ai, ao, cable_size, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                key,
                labels.get('fa', key),
                labels.get('en', key),
                io.get('DI', 0),
                io.get('DO', 0),
                io.get('AI', 0),
                io.get('AO', 0),
                cable,
                1,
                now,
                now
            ))
            logger.info(f"Added default component: {key}")

    def _create_custom_components_table(self, cursor):
        """ایجاد جدول custom_components"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                label_fa TEXT NOT NULL,
                label_en TEXT NOT NULL,
                di INTEGER DEFAULT 0,
                do INTEGER DEFAULT 0,
                ai INTEGER DEFAULT 0,
                ao INTEGER DEFAULT 0,
                cable_size TEXT DEFAULT '2x1mm²',
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        logger.info("Created custom_components table")

    def _merge_components(self):
        """ادغام کامپوننت‌های پیش‌فرض و سفارشی"""
        self._all_components = {}
        
        # کامپوننت‌های پیش‌فرض
        for key in COMPONENT_LABELS.keys():
            self._all_components[key] = {
                'fa': COMPONENT_LABELS[key]['fa'],
                'en': COMPONENT_LABELS[key]['en'],
                'io': IO_CALCULATION.get(key, {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0}),
                'cable_size': CABLE_SIZE.get(key, '2x1mm²'),
                'is_default': True,
                'is_active': True
            }
        
        # کامپوننت‌های سفارشی (با اولویت، اگر کلید تکراری باشد، سفارشی جایگزین می‌شود)
        for key, data in self._custom_components.items():
            self._all_components[key] = {
                'fa': data['fa'],
                'en': data['en'],
                'io': data['io'],
                'cable_size': data.get('cable_size', '2x1mm²'),
                'is_default': False,
                'is_active': data.get('is_active', True)
            }

    def get_all_active_components(self) -> Dict[str, Dict]:
        """
        دریافت لیست کامل کامپوننت‌های فعال (پیش‌فرض + سفارشی)
        
        Returns:
            دیکشنری با کلید component_key و اطلاعات کامپوننت (شامل I/O و برچسب)
        """
        components = {}
        
        # کامپوننت‌های پیش‌فرض
        for key in COMPONENT_LABELS.keys():
            components[key] = {
                'fa': COMPONENT_LABELS[key]['fa'],
                'en': COMPONENT_LABELS[key]['en'],
                'io': IO_CALCULATION.get(key, {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0}),
                'cable_size': CABLE_SIZE.get(key, '2x1mm²'),
                'is_default': True,
                'is_active': True
            }
        
        # کامپوننت‌های سفارشی (فقط فعال‌ها)
        custom_components = self.db.get_custom_components()
        for comp in custom_components:
            if comp['is_active']:
                components[comp['key']] = {
                    'fa': comp.get('label_fa', comp['key']),
                    'en': comp.get('label_en', comp['key']),
                    'io': {
                        'DI': comp.get('di', 0),
                        'DO': comp.get('do', 0),
                        'AI': comp.get('ai', 0),
                        'AO': comp.get('ao', 0)
                    },
                    'cable_size': comp.get('cable_size', '2x1mm²'),
                    'is_default': False,
                    'is_active': True
                }
        
        return components

    def get_all_components(self) -> Dict[str, Dict]:
        """دریافت همه کامپوننت‌ها (پیش‌فرض + سفارشی)"""
        self._merge_components()
        return self._all_components.copy()

    def get_component(self, key: str) -> Optional[Dict]:
        """دریافت یک کامپوننت خاص با کلید"""
        all_components = self.get_all_components()
        return all_components.get(key)

    def get_component_keys(self) -> List[str]:
        """دریافت لیست کلیدهای همه کامپوننت‌ها (مرتب شده)"""
        return sorted(self.get_all_components().keys())

    def get_default_io(self, component_key: str) -> Dict[str, int]:
        """دریافت I/O پیش‌فرض یک کامپوننت"""
        comp = self.get_component(component_key)
        if comp:
            return comp.get('io', {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0})
        return {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0}

    def get_component_label(self, component_key: str, lang: str = 'en') -> str:
        """دریافت برچسب یک کامپوننت به زبان مشخص"""
        comp = self.get_component(component_key)
        if comp:
            return comp.get(lang, component_key)
        return component_key

    def get_cable_size(self, component_key: str) -> str:
        """دریافت اندازه کابل برای یک کامپوننت"""
        comp = self.get_component(component_key)
        if comp:
            return comp.get('cable_size', '2x1mm²')
        return '2x1mm²'

    def add_component(self, key: str, label_fa: str, label_en: str,
                      di: int = 0, do: int = 0, ai: int = 0, ao: int = 0,
                      cable_size: str = '2x1mm²') -> bool:
        """افزودن کامپوننت سفارشی جدید"""
        try:
            key = key.upper().strip()
            if not key:
                return False
            
            if not re.match(r'^[A-Z0-9_]+$', key):
                return False
            
            if key in COMPONENT_LABELS or key in self._custom_components:
                return False
            
            di = max(0, int(di))
            do = max(0, int(do))
            ai = max(0, int(ai))
            ao = max(0, int(ao))
            
            component_data = {
                'key': key,
                'label_fa': label_fa,
                'label_en': label_en,
                'di': di,
                'do': do,
                'ai': ai,
                'ao': ao,
                'cable_size': cable_size
            }
            
            if self.db.save_custom_component(component_data):
                now = datetime.now().isoformat()
                self._custom_components[key] = {
                    'fa': label_fa,
                    'en': label_en,
                    'io': {'DI': di, 'DO': do, 'AI': ai, 'AO': ao},
                    'cable_size': cable_size,
                    'is_active': True,
                    'created_at': now,
                    'updated_at': now
                }
                self._merge_components()
                logger.info(f"Added custom component: {key}")
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error adding custom component: {e}")
            return False

    def update_component(self, key: str, **kwargs) -> bool:
        """به‌روزرسانی کامپوننت سفارشی"""
        try:
            if key not in self._custom_components:
                return False
            
            updates = []
            values = []
            
            for field in ['label_fa', 'label_en', 'di', 'do', 'ai', 'ao', 'cable_size']:
                if field in kwargs:
                    value = kwargs[field]
                    if field in ['di', 'do', 'ai', 'ao']:
                        value = max(0, int(value))
                    updates.append(f"{field} = ?")
                    values.append(value)
            
            if not updates:
                return False
            
            now = datetime.now().isoformat()
            updates.append("updated_at = ?")
            values.append(now)
            values.append(key)
            
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            query = f"UPDATE custom_components SET {', '.join(updates)} WHERE key = ?"
            cursor.execute(query, values)
            
            conn.commit()
            conn.close()
            
            self._load_custom_components()
            self._merge_components()
            
            logger.info(f"Updated custom component: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating custom component: {e}")
            return False

    def delete_component(self, key: str) -> bool:
        """حذف کامپوننت سفارشی (غیرفعال‌سازی)"""
        try:
            if key not in self._custom_components:
                return False
            
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            cursor.execute('''
                UPDATE custom_components SET is_active = 0, updated_at = ?
                WHERE key = ?
            ''', (now, key))
            
            conn.commit()
            conn.close()
            
            if key in self._custom_components:
                del self._custom_components[key]
            
            self._merge_components()
            
            logger.info(f"Deleted custom component: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting custom component: {e}")
            return False

    def is_default_component(self, key: str) -> bool:
        """بررسی اینکه آیا کامپوننت پیش‌فرض است"""
        return key in COMPONENT_LABELS

    def get_component_usage_count(self, key: str) -> int:
        """دریافت تعداد استفاده از یک کامپوننت در پروژه‌ها"""
        return 0

    def get_components_by_category(self) -> Dict[str, List[str]]:
        """دسته‌بندی کامپوننت‌ها بر اساس نوع"""
        categories = {
            'Sensors': ['DTS', 'ITS', 'RTS', 'DTHS', 'RTHS', 'AVS', 'FS', 'PS', 'PT', 'DPT', 'DPS', 'AQ', 'FR', 'LS', 'LT', 'SD', 'Knob', 'SOU', 'LUX', 'VIB'],
            'Actuators': ['VA', 'DAM_T1', 'DAM_T2', 'DAM_T3', 'DAM_T4', 'SV', 'MOV'],
            'Equipment': ['PU', 'VSD', 'FC', 'LIG', 'BUZ']
        }
        
        custom_keys = [k for k in self._custom_components.keys() if k not in COMPONENT_LABELS]
        if custom_keys:
            categories['Custom'] = custom_keys
        
        return categories

    def to_dict(self) -> Dict[str, Dict]:
        """تبدیل همه کامپوننت‌ها به دیکشنری"""
        return self.get_all_components()