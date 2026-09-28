"""مدیریت قالب‌های تجهیزات - کاربرمحور بدون قالب پیش‌فرض"""

import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from core.models import Motor, Project, ProjectSection
from core.constants import COMPONENT_LABELS

logger = logging.getLogger(__name__)


class TemplateManager:
    """
    مدیریت قالب‌های تجهیزات - کاربر قالب‌ها را از پروژه‌ها ذخیره می‌کند
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        self._templates: Dict[str, Dict] = {}
        self._load_templates()
    
    # ==================== متدهای پایه ====================
    
    def _load_templates(self):
        """بارگذاری قالب‌ها از دیتابیس"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # ایجاد جدول templates
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    source_project TEXT,
                    source_section TEXT,
                    devices TEXT NOT NULL,
                    device_count INTEGER DEFAULT 0,
                    total_io INTEGER DEFAULT 0,
                    usage_count INTEGER DEFAULT 0,
                    last_used TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    created_by TEXT DEFAULT 'user'
                )
            ''')
            conn.commit()
            
            # ===== بررسی و اضافه کردن ستون‌های گم‌شده =====
            cursor.execute("PRAGMA table_info(templates)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            
            columns_to_add = {
                'description': 'TEXT',
                'source_project': 'TEXT',
                'source_section': 'TEXT',
                'device_count': 'INTEGER DEFAULT 0',
                'total_io': 'INTEGER DEFAULT 0',
                'usage_count': 'INTEGER DEFAULT 0',
                'last_used': 'TEXT',
                'created_at': 'TEXT',
                'updated_at': 'TEXT',
                'created_by': "TEXT DEFAULT 'user'"
            }
            
            for col_name, col_type in columns_to_add.items():
                if col_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE templates ADD COLUMN {col_name} {col_type}")
                        logger.info(f"Added column '{col_name}' to templates table")
                        conn.commit()
                    except sqlite3.Error as e:
                        logger.warning(f"Could not add column '{col_name}': {e}")
            
            # ===== بارگذاری قالب‌ها =====
            cursor.execute("SELECT * FROM templates ORDER BY name")
            rows = cursor.fetchall()
            
            # دریافت نام ستون‌ها
            cursor.execute("PRAGMA table_info(templates)")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            
            for row in rows:
                row_dict = dict(zip(column_names, row))
                name = row_dict.get('name', '')
                
                if not name:
                    continue
                
                devices_json = row_dict.get('devices', '[]')
                
                try:
                    devices = json.loads(devices_json)
                    
                    # ===== استانداردسازی ساختار داده‌ای =====
                    standardized_devices = self._standardize_devices(devices)
                    
                    # ذخیره در دیکشنری
                    self._templates[name] = {
                        'name': name,
                        'description': row_dict.get('description', ''),
                        'source_project': row_dict.get('source_project', ''),
                        'source_section': row_dict.get('source_section', ''),
                        'devices': standardized_devices,
                        'device_count': len(standardized_devices),
                        'total_io': self._calculate_total_io(standardized_devices),
                        'usage_count': row_dict.get('usage_count', 0) or 0,
                        'last_used': row_dict.get('last_used'),
                        'created_at': row_dict.get('created_at', datetime.now().isoformat()),
                        'updated_at': row_dict.get('updated_at', datetime.now().isoformat()),
                        'created_by': row_dict.get('created_by', 'user')
                    }
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error loading template '{name}': {e}")
                except Exception as e:
                    logger.error(f"Error processing template '{name}': {e}")
            
            cursor.close()
            logger.info(f"Loaded {len(self._templates)} templates")
            
        except sqlite3.Error as e:
            logger.error(f"Error loading templates: {e}")
    
    def _standardize_devices(self, devices: List) -> List[Dict]:
        """استانداردسازی ساختار داده‌های دستگاه‌ها"""
        standardized_devices = []
        
        for device in devices:
            # اگر device رشته است، از آن بگذر
            if isinstance(device, str):
                continue
            
            # اگر device دیکشنری نیست، از آن بگذر
            if not isinstance(device, dict):
                continue
            
            # ===== استانداردسازی device =====
            new_device = device.copy()
            
            # اگر device دارای components است
            if 'components' in new_device and isinstance(new_device['components'], list):
                # فیلتر کردن components: فقط دیکشنری‌ها
                valid_components = []
                for comp in new_device['components']:
                    if isinstance(comp, dict):
                        valid_components.append(comp)
                
                new_device['components'] = valid_components
                
                # اگر quantity در سطح device نیست، از components بگیر
                if 'quantity' not in new_device:
                    new_device['quantity'] = sum(comp.get('quantity', 1) for comp in valid_components)
                
                # اگر di/do/ai/ao در سطح device نیست، از components بگیر
                if 'di' not in new_device:
                    new_device['di'] = sum(comp.get('io', {}).get('DI', 0) for comp in valid_components)
                if 'do' not in new_device:
                    new_device['do'] = sum(comp.get('io', {}).get('DO', 0) for comp in valid_components)
                if 'ai' not in new_device:
                    new_device['ai'] = sum(comp.get('io', {}).get('AI', 0) for comp in valid_components)
                if 'ao' not in new_device:
                    new_device['ao'] = sum(comp.get('io', {}).get('AO', 0) for comp in valid_components)
                
                # اگر component در سطح device نیست، از components بگیر
                if 'component' not in new_device and valid_components:
                    new_device['component'] = valid_components[0].get('component', '')
            
            # اگر device دارای components نیست، یک components بساز
            elif 'components' not in new_device:
                new_device['components'] = [{
                    'type': new_device.get('type', new_device.get('name', 'Unknown')),
                    'quantity': new_device.get('quantity', 1),
                    'component': new_device.get('component', ''),
                    'naming': new_device.get('naming', '{type}-{n}'),
                    'description': new_device.get('description', ''),
                    'positions': new_device.get('positions', []),
                    'io': {
                        'DI': new_device.get('di', 0),
                        'DO': new_device.get('do', 0),
                        'AI': new_device.get('ai', 0),
                        'AO': new_device.get('ao', 0)
                    }
                }]
            
            standardized_devices.append(new_device)
        
        return standardized_devices
    
    def _calculate_total_io(self, devices: List[Dict]) -> int:
        """محاسبه مجموع I/O دستگاه‌ها (شامل تعداد)"""
        total = 0
        for device in devices:
            if not isinstance(device, dict):
                continue
            
            # اگر دستگاه دارای کامپوننت‌هاست
            if 'components' in device and isinstance(device['components'], list):
                for comp in device['components']:
                    if not isinstance(comp, dict):
                        continue
                    
                    qty = comp.get('quantity', 1)  # تعداد کامپوننت
                    try:
                        qty = int(qty) if qty else 1
                    except (ValueError, TypeError):
                        qty = 1
                    
                    io = comp.get('io', {})
                    total += qty * (io.get('DI', 0) + io.get('DO', 0) + io.get('AI', 0) + io.get('AO', 0))
            else:
                # حالت قدیمی (فقط یک کامپوننت)
                qty = device.get('quantity', 1)
                try:
                    qty = int(qty) if qty else 1
                except (ValueError, TypeError):
                    qty = 1
                
                total += qty * (device.get('di', 0) + device.get('do', 0) + device.get('ai', 0) + device.get('ao', 0))
        
        return total
    
    def get_template_preview(self, template_name: str) -> str:
        """دریافت پیش‌نمایش یک قالب به صورت متن"""
        template = self.get_template(template_name)
        if not template:
            return "قالب یافت نشد"
        
        devices = template.get('devices', [])
        if not devices:
            return "این قالب خالی است"
        
        preview = f"📋 {template_name}\n"
        preview += "=" * 40 + "\n\n"
        
        if template.get('description'):
            preview += f"📝 {template['description']}\n\n"
        
        if template.get('source_project'):
            preview += f"📁 مبدا: {template['source_project']}"
            if template.get('source_section'):
                preview += f" → {template['source_section']}"
            preview += "\n\n"
        
        preview += f"🔢 تعداد دستگاه‌ها: {len(devices)}\n"
        preview += f"📊 کل I/O: {template.get('total_io', 0)}\n"
        preview += f"📈 تعداد استفاده: {template.get('usage_count', 0)}\n\n"
        
        preview += "🔧 دستگاه‌ها:\n"
        for i, device in enumerate(devices, 1):
            if not isinstance(device, dict):
                continue
            
            name = device.get('name', 'Unnamed')
            
            if 'components' in device and isinstance(device['components'], list):
                preview += f"  {i}. {name} (شامل {len(device['components'])} کامپوننت):\n"
                for j, comp in enumerate(device['components'], 1):
                    if not isinstance(comp, dict):
                        continue
                    
                    comp_name = comp.get('type', 'Unknown')
                    comp_qty = comp.get('quantity', 1)
                    io = comp.get('io', {})
                    comp_io = f"DI:{io.get('DI',0)} DO:{io.get('DO',0)} AI:{io.get('AI',0)} AO:{io.get('AO',0)}"
                    preview += f"      {j}. {comp_name} (Qty: {comp_qty}) - {comp_io}\n"
            else:
                io = f"DI:{device.get('di',0)} DO:{device.get('do',0)} AI:{device.get('ai',0)} AO:{device.get('ao',0)}"
                preview += f"  {i}. {name} - {io}\n"
        
        return preview
    
    # ==================== متدهای اصلی ====================
    
    def get_template(self, name: str) -> Optional[Dict]:
        """دریافت یک قالب"""
        return self._templates.get(name)
    
    def get_all_templates(self) -> Dict[str, Dict]:
        """دریافت همه قالب‌ها"""
        return self._templates.copy()
    
    def get_template_names(self) -> List[str]:
        """دریافت لیست اسامی قالب‌ها (مرتب شده)"""
        return sorted(self._templates.keys())
    
    def add_template(self, name: str, devices: List[Dict], category: str = "Custom") -> bool:
        """افزودن قالب جدید"""
        if not name or not name.strip():
            return False
        
        if not devices:
            return False
        
        if name in self._templates:
            return False
        
        # استانداردسازی داده‌ها
        standardized_devices = self._standardize_devices(devices)
        if not standardized_devices:
            return False
        
        # ایجاد داده‌های قالب
        template_data = {
            'name': name.strip(),
            'description': '',
            'source_project': '',
            'source_section': '',
            'devices': standardized_devices,
            'device_count': len(standardized_devices),
            'total_io': self._calculate_total_io(standardized_devices),
            'usage_count': 0,
            'last_used': None,
            'created_at': datetime.now().isoformat(),
            'created_by': 'user',
            'category': category
        }
        
        # ذخیره در دیتابیس
        self._templates[name.strip()] = template_data
        self._save_template_to_db(template_data)
        
        return True
    
    def create_template_from_devices(self, name: str, devices: List[Motor], 
                                     description: str = "",
                                     source_project: str = "",
                                     source_section: str = "") -> bool:
        """
        ایجاد قالب از لیست دستگاه‌ها
        """
        if not name or not name.strip():
            return False
        
        if not devices:
            return False
        
        if name in self._templates:
            return False
        
        # تبدیل دستگاه‌ها به دیکشنری
        devices_data = []
        for motor in devices:
            device_dict = {
                'name': motor.Name or '',
                'description': motor.Description or '',
                'components': [
                    {
                        'type': motor.Name or '',
                        'quantity': 1,
                        'component': '',
                        'naming': '',
                        'description': motor.Description or '',
                        'positions': [],
                        'io': {
                            'DI': motor.DI,
                            'DO': motor.DO,
                            'AI': motor.AI,
                            'AO': motor.AO
                        }
                    }
                ]
            }
            
            devices_data.append(device_dict)
        
        template_data = {
            'name': name.strip(),
            'description': description,
            'source_project': source_project,
            'source_section': source_section,
            'devices': devices_data,
            'device_count': len(devices_data),
            'total_io': self._calculate_total_io(devices_data),
            'usage_count': 0,
            'last_used': None,
            'created_at': datetime.now().isoformat(),
            'created_by': 'user'
        }
        
        self._templates[name.strip()] = template_data
        self._save_template_to_db(template_data)
        
        return True
    
    def create_template_from_selected(self, name: str, devices: List[Motor],
                                      source_project: str = "",
                                      source_section: str = "") -> bool:
        """ایجاد قالب از دستگاه‌های انتخاب شده"""
        if not devices:
            return False
        
        description = f"قالب از {len(devices)} دستگاه"
        if source_section:
            description += f" در بخش {source_section}"
        
        return self.create_template_from_devices(
            name=name,
            devices=devices,
            description=description,
            source_project=source_project,
            source_section=source_section
        )
    
    def edit_template(self, name: str, devices: List[Dict], category: str = "Custom") -> bool:
        """ویرایش یک قالب"""
        if name not in self._templates:
            return False
        
        if not devices:
            return False
        
        # استانداردسازی داده‌ها
        standardized_devices = self._standardize_devices(devices)
        if not standardized_devices:
            return False
        
        template = self._templates[name]
        template['devices'] = standardized_devices
        template['device_count'] = len(standardized_devices)
        template['total_io'] = self._calculate_total_io(standardized_devices)
        template['category'] = category
        
        self._save_template_to_db(template)
        
        return True
    
    def delete_template(self, name: str) -> bool:
        """حذف یک قالب"""
        if name not in self._templates:
            return False
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM templates WHERE name = ?", (name,))
            conn.commit()
            cursor.close()
            
            del self._templates[name]
            logger.info(f"Template '{name}' deleted successfully")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error deleting template '{name}': {e}")
            return False
    
    def duplicate_template(self, name: str, new_name: str) -> bool:
        """کپی کردن یک قالب با نام جدید"""
        if name not in self._templates:
            return False
        
        if new_name in self._templates or not new_name.strip():
            return False
        
        template = self._templates[name].copy()
        template['name'] = new_name.strip()
        template['usage_count'] = 0
        template['last_used'] = None
        template['created_at'] = datetime.now().isoformat()
        template['created_by'] = 'user'
        template['category'] = template.get('category', 'Custom')
        
        self._templates[new_name.strip()] = template
        self._save_template_to_db(template)
        
        return True
    
    def use_template(self, name: str) -> bool:
        """ثبت استفاده از یک قالب"""
        if name not in self._templates:
            return False
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            cursor.execute('''
                UPDATE templates 
                SET usage_count = usage_count + 1, last_used = ?, updated_at = ?
                WHERE name = ?
            ''', (now, now, name))
            conn.commit()
            cursor.close()
            
            self._templates[name]['usage_count'] += 1
            self._templates[name]['last_used'] = now
            
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error updating template usage: {e}")
            return False
    
    def generate_devices(self, template_name: str, group_name: str = "") -> List[Motor]:
        """تولید دستگاه‌ها از یک قالب"""
        template = self.get_template(template_name)
        if not template:
            return []
        
        devices_data = template.get('devices', [])
        if not devices_data:
            return []
        
        generated_devices = []
        for device_data in devices_data:
            if not isinstance(device_data, dict):
                continue
            
            if 'components' in device_data and isinstance(device_data['components'], list):
                for comp in device_data['components']:
                    if not isinstance(comp, dict):
                        continue
                    
                    qty = comp.get('quantity', 1)
                    try:
                        qty = int(qty) if qty else 1
                    except (ValueError, TypeError):
                        qty = 1
                    
                    for _ in range(qty):
                        motor = Motor(
                            Name=comp.get('type', 'Unknown'),
                            Description=comp.get('description', ''),
                            INFO=group_name or '',
                            DI=comp.get('io', {}).get('DI', 0),
                            DO=comp.get('io', {}).get('DO', 0),
                            AI=comp.get('io', {}).get('AI', 0),
                            AO=comp.get('io', {}).get('AO', 0)
                        )
                        
                        generated_devices.append(motor)
            else:
                qty = device_data.get('quantity', 1)
                try:
                    qty = int(qty) if qty else 1
                except (ValueError, TypeError):
                    qty = 1
                
                for _ in range(qty):
                    motor = Motor(
                        Name=device_data.get('name', ''),
                        Description=device_data.get('description', ''),
                        INFO=group_name or device_data.get('info', ''),
                        DI=device_data.get('di', 0),
                        DO=device_data.get('do', 0),
                        AI=device_data.get('ai', 0),
                        AO=device_data.get('ao', 0)
                    )
                    
                    generated_devices.append(motor)
        
        # ثبت استفاده
        if generated_devices:
            self.use_template(template_name)
        
        return generated_devices
    
    def _save_template_to_db(self, template_data: Dict):
        """ذخیره قالب در دیتابیس"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            # استانداردسازی داده‌ها
            devices = self._standardize_devices(template_data.get('devices', []))
            
            cursor.execute('''
                INSERT OR REPLACE INTO templates (
                    name, description, source_project, source_section,
                    devices, device_count, total_io, usage_count,
                    last_used, updated_at, created_at, created_by, category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                template_data['name'],
                template_data.get('description', ''),
                template_data.get('source_project', ''),
                template_data.get('source_section', ''),
                json.dumps(devices, ensure_ascii=False),
                template_data.get('device_count', len(devices)),
                template_data.get('total_io', self._calculate_total_io(devices)),
                template_data.get('usage_count', 0),
                template_data.get('last_used'),
                now,
                template_data.get('created_at', now),
                template_data.get('created_by', 'user'),
                template_data.get('category', 'Custom')
            ))
            
            conn.commit()
            cursor.close()
            logger.info(f"Template '{template_data['name']}' saved successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Error saving template: {e}")
            raise
    
    def get_most_used_templates(self, limit: int = 5) -> List[Dict]:
        """دریافت پرکاربردترین قالب‌ها"""
        sorted_templates = sorted(
            self._templates.values(),
            key=lambda x: x.get('usage_count', 0),
            reverse=True
        )
        return sorted_templates[:limit]
    
    def get_recent_templates(self, limit: int = 5) -> List[Dict]:
        """دریافت آخرین قالب‌های استفاده شده"""
        sorted_templates = sorted(
            [t for t in self._templates.values() if t.get('last_used')],
            key=lambda x: x.get('last_used', ''),
            reverse=True
        )
        return sorted_templates[:limit]
    
    def get_template_edit_data(self, template_name: str) -> Optional[Dict]:
        """دریافت داده‌های قالب برای ویرایش"""
        template = self.get_template(template_name)
        if not template:
            return None
        
        return template
    
    def export_templates(self, template_names: List[str] = None) -> Dict:
        """صادر کردن قالب‌ها به صورت JSON"""
        if template_names:
            templates = {k: self._templates[k] for k in template_names if k in self._templates}
        else:
            templates = self._templates
        
        return {
            'version': '1.0',
            'export_date': datetime.now().isoformat(),
            'templates': templates
        }
    
    def import_templates(self, import_data: Dict) -> int:
        """وارد کردن قالب‌ها از JSON"""
        count = 0
        templates = import_data.get('templates', {})
        
        for name, data in templates.items():
            if name in self._templates:
                continue
            
            if 'devices' not in data or not data['devices']:
                continue
            
            self._templates[name] = data
            self._save_template_to_db(data)
            count += 1
        
        return count