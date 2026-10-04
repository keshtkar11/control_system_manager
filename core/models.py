"""مدل‌های داده اصلی برنامه"""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import json
from .constants import (
    COMPONENT_LABELS, IO_CALCULATION, CABLE_SIZE,
    DEFAULT_SECTIONS, LIMITS
)


class Motor:
    """مدل دستگاه - شامل تمام کامپوننت‌ها و I/O"""
    
    # لیست تمام فیلدهای عددی (I/O و کامپوننت‌ها)
    NUMERIC_FIELDS = [
        'DI', 'DO', 'AI', 'AO',  # I/O
        'FS', 'DTS', 'ITS', 'DTHS', 'FR', 'AQ',  # سنسورها
        'DAM_T1', 'DAM_T2', 'DAM_T3', 'DAM_T4',  # دمپرها
        'RTS', 'RTHS', 'SD', 'AVS',  # سنسورهای اتاق
        'VA', 'LS', 'LT', 'PS', 'PT', 'DPT', 'DPS',  # شیرها و سوئیچ‌ها
        'PU', 'VSD', 'SV', 'FC', 'LIG', 'Knob',  # تجهیزات
        'FA', 'FE', 'SLE', 'CMD', 'SPR', 'MOD' , # 🆕 کامپوننت‌های جدید
        'MOV','SOU','LUX','VIB','BUZ','HMI','FCV'

    ]

    # ===== به‌روزرسانی خودکار: اضافه کردن تمام کامپوننت‌های جدید =====
    NUMERIC_FIELDS = list(set(NUMERIC_FIELDS + list(COMPONENT_LABELS.keys())))
    
    STRING_FIELDS = ['Name', 'Description', 'INFO', 'ImagePath', 'SmartTag']
    BOOLEAN_FIELDS = ['UseIndexNaming']
    
    def __init__(self, **kwargs):
        """ایجاد دستگاه جدید با مقادیر ورودی"""
        
        # فیلدهای رشته‌ای
        self.Name = self._validate_string(kwargs.get('Name'), 'Name')
        self.Description = self._validate_string(kwargs.get('Description'), 'Description')
        self.INFO = self._validate_string(kwargs.get('INFO', ''), 'INFO')
        self.SmartTag = self._validate_string(kwargs.get('SmartTag', ''), 'SmartTag')
        self.ImagePath = kwargs.get('ImagePath', None)

        self.UseIndexNaming = bool(kwargs.get('UseIndexNaming', True))
        
        # فیلدهای عددی
        for field in self.NUMERIC_FIELDS:
            value = kwargs.get(field, 0)
            setattr(self, field, self._validate_int(value, field))

        self.ModelOrders: Dict[str, str] = kwargs.get('ModelOrders', {}) or {}
        
        # تاریخ ایجاد
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    @staticmethod
    def _validate_string(value: Any, field_name: str) -> str:
        """اعتبارسنجی فیلدهای رشته‌ای"""
        if value is None:
            return ""
        if not isinstance(value, str):
            return str(value)
        # محدودیت طول
        max_len = LIMITS.get(f'max_{field_name.lower()}_length', 500)
        if len(value) > max_len:
            return value[:max_len]
        return value
    
    @staticmethod
    def _validate_int(value: Any, field_name: str) -> int:
        """اعتبارسنجی فیلدهای عددی"""
        try:
            if isinstance(value, bool):
                return 1 if value else 0
            if isinstance(value, (int, float)):
                return max(0, int(value))
            if isinstance(value, str):
                return max(0, int(value) if value.strip() else 0)
            return 0
        except (ValueError, TypeError):
            return 0
    
    def copy(self) -> 'Motor':
        """ایجاد کپی عمیق از دستگاه"""
        return Motor(**self.to_dict())
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری برای ذخیره‌سازی"""
        result = {}
        for field in self.STRING_FIELDS:
            result[field] = getattr(self, field, "")
        for field in self.NUMERIC_FIELDS:
            result[field] = getattr(self, field, 0)

        result['UseIndexNaming'] = getattr(self, 'UseIndexNaming', True)
        
        # ✅ جدید (v2.1): ModelOrders
        result['ModelOrders'] = getattr(self, 'ModelOrders', {}) or {}
        
        return result
        
    
    def from_dict(self, data: Dict[str, Any]) -> 'Motor':
        """بارگذاری از دیکشنری"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # ✅ جدید (v2.1): اطمینان از وجود ModelOrders
        if not hasattr(self, 'ModelOrders') or not isinstance(self.ModelOrders, dict):
            self.ModelOrders = {}
        
        return self

    # ============================================================
    # ✅ جدید (v2.1): متدهای Model-Order
    # ============================================================
    
    def set_model_order(self, component_key: str, model_order: str) -> None:
        """
        ذخیره Model-Order برای یک کامپوننت
        
        Args:
            component_key: کلید کامپوننت (مثلاً 'DTS')
            model_order: کد Model-Order (مثلاً 'DTS-01')
        """
        if not hasattr(self, 'ModelOrders') or not isinstance(self.ModelOrders, dict):
            self.ModelOrders = {}
        
        model_order = (model_order or '').strip()
        
        if model_order:
            self.ModelOrders[component_key] = model_order
        elif component_key in self.ModelOrders:
            del self.ModelOrders[component_key]
    
    def get_model_order(self, component_key: str) -> str:
        """
        دریافت Model-Order یک کامپوننت
        
        Args:
            component_key: کلید کامپوننت (مثلاً 'DTS')
        
        Returns:
            کد Model-Order یا '' اگر تنظیم نشده
        """
        if not hasattr(self, 'ModelOrders') or not isinstance(self.ModelOrders, dict):
            return ''
        return self.ModelOrders.get(component_key, '')
    
    def get_all_model_orders(self) -> Dict[str, str]:
        """دریافت همه Model-Order ها (فقط غیرخالی)"""
        if not hasattr(self, 'ModelOrders') or not isinstance(self.ModelOrders, dict):
            return {}
        return {k: v for k, v in self.ModelOrders.items() if v}
    
    def get_total_io(self) -> int:
        """محاسبه مجموع I/O"""
        return self.DI + self.DO + self.AI + self.AO
    
    def get_active_components(self, use_labels: bool = True) -> List[Dict[str, Any]]:
        """
        دریافت کامپوننت‌های فعال (مقدار > 0)
        
        Args:
            use_labels: اگر True باشد، از برچسب‌های COMPONENT_LABELS استفاده می‌کند
        
        Returns:
            لیست دیکشنری‌های کامپوننت‌های فعال
        """
        active = []
        for field in self.NUMERIC_FIELDS:
            if field in ['DI', 'DO', 'AI', 'AO']:
                continue  # I/O را جداگانه محاسبه می‌کنیم
            
            value = getattr(self, field, 0)
            if value > 0:
                component_info = {
                    'key': field,
                    'quantity': value,
                    'cable_size': CABLE_SIZE.get(field, "2x1mm²")
                }
                
                if use_labels and field in COMPONENT_LABELS:
                    component_info['label_fa'] = COMPONENT_LABELS[field]['fa']
                    component_info['label_en'] = COMPONENT_LABELS[field]['en']
                else:
                    component_info['label_fa'] = field
                    component_info['label_en'] = field
                
                # اضافه کردن محاسبه I/O
                if field in IO_CALCULATION:
                    io_config = IO_CALCULATION[field]
                    component_info['di_per_unit'] = io_config.get('DI', 0)
                    component_info['do_per_unit'] = io_config.get('DO', 0)
                    component_info['ai_per_unit'] = io_config.get('AI', 0)
                    component_info['ao_per_unit'] = io_config.get('AO', 0)
                    component_info['total_di'] = value * io_config.get('DI', 0)
                    component_info['total_do'] = value * io_config.get('DO', 0)
                    component_info['total_ai'] = value * io_config.get('AI', 0)
                    component_info['total_ao'] = value * io_config.get('AO', 0)
                
                active.append(component_info)
        
        return active

    def recalculate_io(self):
        """محاسبه I/O بر اساس تمام کامپوننت‌ها"""
        total_di = 0
        total_do = 0
        total_ai = 0
        total_ao = 0
        
        for field in COMPONENT_LABELS.keys():
            qty = getattr(self, field, 0)
            if qty > 0:
                if field in IO_CALCULATION:
                    config = IO_CALCULATION[field]
                    total_di += qty * config.get("DI", 0)
                    total_do += qty * config.get("DO", 0)
                    total_ai += qty * config.get("AI", 0)
                    total_ao += qty * config.get("AO", 0)
                else:
                    # برای کامپوننت‌های سفارشی، از ComponentManager استفاده کن
                    if hasattr(self, 'component_manager'):
                        default_io = self.component_manager.get_default_io(field)
                        total_di += qty * default_io.get('DI', 0)
                        total_do += qty * default_io.get('DO', 0)
                        total_ai += qty * default_io.get('AI', 0)
                        total_ao += qty * default_io.get('AO', 0)
        
        self.DI = total_di
        self.DO = total_do
        self.AI = total_ai
        self.AO = total_ao

    
    def get_io_breakdown(self) -> Dict[str, Dict[str, int]]:
        """
        دریافت تفکیک I/O برای هر کامپوننت
        
        Returns:
            دیکشنری با کلید کامپوننت و مقادیر I/O
        """
        breakdown = {}
        for field in self.NUMERIC_FIELDS:
            if field in ['DI', 'DO', 'AI', 'AO']:
                continue
            
            qty = getattr(self, field, 0)
            if qty > 0 and field in IO_CALCULATION:
                config = IO_CALCULATION[field]
                breakdown[field] = {
                    'quantity': qty,
                    'di': qty * config.get('DI', 0),
                    'do': qty * config.get('DO', 0),
                    'ai': qty * config.get('AI', 0),
                    'ao': qty * config.get('AO', 0)
                }
        
        return breakdown
    
    def get_cable_tags(self) -> List[Dict[str, str]]:
        """
        تولید برچسب‌های کابل برای کامپوننت‌های فعال
        
        Returns:
            لیست دیکشنری‌های برچسب کابل
        """
        tags = []
        base_name = self.Name or "Device"
        # پاکسازی نام برای استفاده در برچسب
        base_name = "".join(c for c in base_name if c.isalnum() or c in " _-")
        if not base_name:
            base_name = "Device"
        
        counter = 1
        for field in self.NUMERIC_FIELDS:
            if field in ['DI', 'DO', 'AI', 'AO']:
                continue
            
            qty = getattr(self, field, 0)
            if qty > 0:
                label = COMPONENT_LABELS.get(field, {}).get('en', field)
                # ===== برای هر تعداد (Quantity)، تگ جداگانه بساز =====
                for i in range(qty):
                    tags.append({
                        'component': field,
                        'label': label,
                        'tag': f"{base_name}-{counter:02d}",
                        'cable_type': "NYSLCY",
                        'cable_size': CABLE_SIZE.get(field, "2x1mm²"),
                        'index': i + 1
                    })
                    counter += 1
        
        return tags
    
    def __repr__(self) -> str:
        return f"Motor(Name='{self.Name}', Total_IO={self.get_total_io()})"


class ProjectSection:
    """مدل بخش پروژه"""
    
    def __init__(self, name: str = "New Section", description: str = ""):
        self.name = self._validate_name(name)
        self.description = description
        self.devices: List[Motor] = []
        self.valves: List['Valve'] = []
        self.order_index = 0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


    @property
    def display_name(self) -> str:
        """
        نام نمایشی سکشن — Name (Description)
        
        برای گزارش‌های Excel/PDF استفاده می‌شود.
        """
        name = (self.name or '').strip()
        desc = (self.description or '').strip()
        
        if name and desc:
            return f"{name} ({desc})"
        return name or desc or 'Unknown Section'
    
    @staticmethod
    def _validate_name(name: str) -> str:
        """اعتبارسنجی نام بخش"""
        if not name or not name.strip():
            return "New Section"
        max_len = LIMITS.get('max_section_name', 50)
        return name.strip()[:max_len]
    
    def copy(self) -> 'ProjectSection':
        """ایجاد کپی عمیق از بخش"""
        new_section = ProjectSection(self.name, self.description)
        new_section.devices = [device.copy() for device in self.devices]
        new_section.valves = [valve.copy() for valve in self.valves]
        new_section.order_index = self.order_index
        return new_section
    
    def add_device(self, motor: Motor) -> None:
        """اضافه کردن دستگاه به بخش"""
        self.devices.append(motor)
        self.updated_at = datetime.now()
    
    def delete_device(self, index: int) -> bool:
        """حذف دستگاه از بخش"""
        if 0 <= index < len(self.devices):
            del self.devices[index]
            self.updated_at = datetime.now()
            return True
        return False

    def add_valve(self, valve):
        """اضافه کردن شیر به بخش"""
        self.valves.append(valve)
        self.updated_at = datetime.now()

    def delete_valve(self, index):
        """حذف شیر از بخش"""
        if 0 <= index < len(self.valves):
            del self.valves[index]
            self.updated_at = datetime.now()
            return True
        return False

    def get_valve_count(self) -> int:
        """تعداد شیرهای بخش"""
        return len(self.valves)

    def get_valve_statistics(self) -> Dict[str, Any]:
        """آمار شیرهای بخش"""
        return {
            'total_valves': len(self.valves),
            'by_type': self._count_by_type(),
        }

    def _count_by_type(self) -> Dict[str, int]:
        """شمارش بر اساس نوع"""
        counts = {}
        for valve in self.valves:
            vt = valve.ValveType or 'Unknown'
            counts[vt] = counts.get(vt, 0) + 1
        return counts
    
    def get_total_io(self) -> int:
        """محاسبه مجموع I/O بخش"""
        return sum(device.get_total_io() for device in self.devices)
    
    def get_device_count(self) -> int:
        """تعداد دستگاه‌های بخش"""
        return len(self.devices)
    
    def get_statistics(self) -> Dict[str, Any]:
        """دریافت آمار بخش"""
        total_io = self.get_total_io()
        device_count = self.get_device_count()
        
        return {
            'name': self.name,
            'device_count': device_count,
            'total_io': total_io,
            'avg_io_per_device': total_io / device_count if device_count > 0 else 0,
            'total_di': sum(d.DI for d in self.devices),
            'total_do': sum(d.DO for d in self.devices),
            'total_ai': sum(d.AI for d in self.devices),
            'total_ao': sum(d.AO for d in self.devices)
        }
    
    def get_active_devices(self) -> List[Motor]:
        """دریافت دستگاه‌های فعال (I/O > 0)"""
        return [d for d in self.devices if d.get_total_io() > 0]
    
    def get_component_usage(self) -> Dict[str, int]:
        """دریافت استفاده از کامپوننت‌ها در بخش"""
        usage = {}
        for device in self.devices:
            for field in Motor.NUMERIC_FIELDS:
                if field in ['DI', 'DO', 'AI', 'AO']:
                    continue
                value = getattr(device, field, 0)
                if value > 0:
                    usage[field] = usage.get(field, 0) + value
        return usage
    
    def __repr__(self) -> str:
        return f"ProjectSection(Name='{self.name}', Devices={len(self.devices)})"


# ================================================================
# ✅ کلاس جدید: Revision (رویژن/نسخه)
# ================================================================

class Revision:
    """
    مدل رویژن (نسخه) پروژه
    
    هر پروژه می‌تواند چند رویژن داشته باشد.
    هر رویژن شامل Section ها و Device های خودش است.
    """
    
    def __init__(self, name: str = "Rev-0", project_name: str = ""):
        """
        Args:
            name: نام رویژن (مثلاً "Rev-0", "Rev-1", "Final")
            project_name: نام پروژه‌ای که این رویژن به آن تعلق دارد
        """
        self.name = self._validate_name(name)
        self.project_name = project_name
        self.sections: List[ProjectSection] = []
        self.description = ""
        
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    @staticmethod
    def _validate_name(name: str) -> str:
        """اعتبارسنجی نام رویژن"""
        if not name or not name.strip():
            return "Rev-0"
        max_len = 50
        return name.strip()[:max_len]
    
    def copy(self, new_name: str = None) -> 'Revision':
        """
        کپی عمیق از رویژن
        
        Args:
            new_name: اگر داده شود، نام رویژن جدید این می‌شود
                     وگرنه همان نام کپی می‌شود (با پسوند)
        """
        if new_name is None:
            new_name = f"{self.name}-Copy"
        
        new_revision = Revision(new_name, self.project_name)
        new_revision.description = self.description
        new_revision.sections = [section.copy() for section in self.sections]
        return new_revision
    
    def add_section(self, name: str, description: str = "") -> ProjectSection:
        """اضافه کردن بخش جدید به رویژن"""
        new_section = ProjectSection(name, description)
        new_section.order_index = len(self.sections)
        self.sections.append(new_section)
        self.updated_at = datetime.now()
        return new_section
    
    def delete_section(self, name: str) -> bool:
        """حذف یک بخش"""
        section = self.get_section_by_name(name)
        if section:
            self.sections.remove(section)
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_section_by_name(self, name: str) -> Optional[ProjectSection]:
        """دریافت بخش بر اساس نام"""
        for section in self.sections:
            if section.name == name:
                return section
        return None
    
    def get_all_devices(self) -> List[Motor]:
        """دریافت تمام دستگاه‌های رویژن"""
        return [device for section in self.sections for device in section.devices]
    
    def get_total_io(self) -> int:
        """محاسبه مجموع I/O کل رویژن"""
        return sum(section.get_total_io() for section in self.sections)
    
    def get_statistics(self) -> Dict[str, Any]:
        """دریافت آمار کامل رویژن"""
        all_devices = self.get_all_devices()
        
        stats = {
            'name': self.name,
            'project_name': self.project_name,
            'total_sections': len(self.sections),
            'total_devices': len(all_devices),
            'total_di': 0,
            'total_do': 0,
            'total_ai': 0,
            'total_ao': 0,
            'total_io': 0,
            'active_devices': 0,
            'inactive_devices': 0
        }
        
        for device in all_devices:
            stats['total_di'] += device.DI
            stats['total_do'] += device.DO
            stats['total_ai'] += device.AI
            stats['total_ao'] += device.AO
            
            if device.get_total_io() > 0:
                stats['active_devices'] += 1
            else:
                stats['inactive_devices'] += 1
        
        stats['total_io'] = stats['total_di'] + stats['total_do'] + stats['total_ai'] + stats['total_ao']
        
        return stats
    
    def get_component_usage(self) -> Dict[str, int]:
        """دریافت استفاده از کامپوننت‌ها در رویژن"""
        usage = {}
        for device in self.get_all_devices():
            for field in Motor.NUMERIC_FIELDS:
                if field in ['DI', 'DO', 'AI', 'AO']:
                    continue
                value = getattr(device, field, 0)
                if value > 0:
                    usage[field] = usage.get(field, 0) + value
        return usage
    
    def __repr__(self) -> str:
        return f"Revision(Name='{self.name}', Sections={len(self.sections)}, Devices={len(self.get_all_devices())})"


# ================================================================
# ✅ کلاس Project (تغییر یافته)
# ================================================================

class Project:
    """
    مدل پروژه
    
    ساختار جدید:
        Project
        ├── revisions: List[Revision]
        ├── current_revision_name: str
        └── ...
    
    نکته: برای سازگاری با کد قبلی، property sections اضافه شده
          که به current_revision.sections اشاره می‌کند.
    """
    
    def __init__(self, name: str = "Untitled Project"):
        self.name = self._validate_name(name)
        self.description = ""
        
        # اطلاعات مشتری
        self.client_name = ""
        self.client_phone = ""
        self.client_address = ""
        
        # اطلاعات مشاور
        self.consultant_name = ""
        self.consultant_phone = ""
        self.consultant_address = ""
        
        # اطلاعات پیمانکار
        self.contractor_name = ""
        self.contractor_phone = ""
        self.contractor_address = ""
        
        # اطلاعات طراح
        self.designer_name = ""
        
        # ============================================================
        # ✅ تغییر اصلی: Revisions
        # ============================================================
        self.revisions: List[Revision] = []
        self.current_revision_name: Optional[str] = None
        
        # برچسب‌های کامپوننت
        self.component_labels: Dict[str, Dict[str, str]] = {}
        
        # اطلاعات زمانی
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    @staticmethod
    def _validate_name(name: str) -> str:
        """اعتبارسنجی نام پروژه"""
        if not name or not name.strip():
            return "Untitled Project"
        max_len = LIMITS.get('max_project_name', 100)
        return name.strip()[:max_len]
    
    # ============================================================
    # ✅ متدهای Revision
    # ============================================================
    
    def get_current_revision(self) -> Optional[Revision]:
        """
        دریافت رویژن فعلی
        
        Returns:
            Revision فعلی یا None
        """
        if not self.current_revision_name:
            return None
        
        for rev in self.revisions:
            if rev.name == self.current_revision_name:
                return rev
        
        return None
    
    def get_revision_by_name(self, name: str) -> Optional[Revision]:
        """دریافت رویژن بر اساس نام"""
        for rev in self.revisions:
            if rev.name == name:
                return rev
        return None
    
    def add_revision(self, name: str, description: str = "") -> Revision:
        """
        افزودن رویژن جدید (خالی)
        
        Args:
            name: نام رویژن
            description: توضیحات
        
        Returns:
            Revision جدید
        
        Raises:
            ValueError: اگر نام تکراری باشد
        """
        if self.get_revision_by_name(name):
            raise ValueError(f"Revision '{name}' already exists")
        
        new_revision = Revision(name, self.name)
        new_revision.description = description
        self.revisions.append(new_revision)
        self.updated_at = datetime.now()
        
        return new_revision
    
    def copy_revision(self, source_name: str, new_name: str, 
                      description: str = "") -> Revision:
        """
        کپی از رویژن دیگر
        
        Args:
            source_name: نام رویژن مبدأ
            new_name: نام رویژن جدید
            description: توضیحات
        
        Returns:
            Revision جدید (کپی شده)
        
        Raises:
            ValueError: اگر مبدأ وجود نداشته باشد یا نام جدید تکراری باشد
        """
        source = self.get_revision_by_name(source_name)
        if not source:
            raise ValueError(f"Source revision '{source_name}' not found")
        
        if self.get_revision_by_name(new_name):
            raise ValueError(f"Revision '{new_name}' already exists")
        
        new_revision = source.copy(new_name)
        new_revision.description = description or f"Copy of {source_name}"
        self.revisions.append(new_revision)
        self.updated_at = datetime.now()
        
        return new_revision
    
    def delete_revision(self, name: str) -> bool:
        """
        حذف رویژن
        
        Args:
            name: نام رویژن
        
        Returns:
            True اگر موفق باشد
        """
        # نمی‌توان آخرین رویژن را حذف کرد
        if len(self.revisions) <= 1:
            return False
        
        revision = self.get_revision_by_name(name)
        if not revision:
            return False
        
        self.revisions.remove(revision)
        
        # اگر رویژن فعلی حذف شد، اولین رویژن را فعلی کن
        if self.current_revision_name == name:
            self.current_revision_name = self.revisions[0].name if self.revisions else None
        
        self.updated_at = datetime.now()
        return True
    
    def rename_revision(self, old_name: str, new_name: str) -> bool:
        """
        تغییر نام رویژن
        
        Args:
            old_name: نام فعلی
            new_name: نام جدید
        
        Returns:
            True اگر موفق باشد
        """
        if old_name == new_name:
            return True
        
        # چک تکراری نبودن
        if self.get_revision_by_name(new_name):
            return False
        
        revision = self.get_revision_by_name(old_name)
        if not revision:
            return False
        
        revision.name = new_name
        revision.updated_at = datetime.now()
        
        # اگر رویژن فعلی بود، نام جدید را ثبت کن
        if self.current_revision_name == old_name:
            self.current_revision_name = new_name
        
        self.updated_at = datetime.now()
        return True
    
    def switch_to_revision(self, name: str) -> bool:
        """
        سوئیچ به رویژن دیگر
        
        Args:
            name: نام رویژن هدف
        
        Returns:
            True اگر موفق باشد
        """
        if not self.get_revision_by_name(name):
            return False
        
        self.current_revision_name = name
        return True
    
    def get_revision_names(self) -> List[str]:
        """دریافت لیست نام رویژن‌ها"""
        return [rev.name for rev in self.revisions]
    
    def has_revisions(self) -> bool:
        """آیا پروژه رویژن دارد؟"""
        return len(self.revisions) > 0
    
    # ============================================================
    # ✅ Property برای سازگاری Backward
    # ============================================================
    
    @property
    def sections(self) -> List[ProjectSection]:
        """
        Sections of current revision (سازگاری Backward)
        
        این property باعث می‌شود کد قدیمی که از project.sections
        استفاده می‌کند، بدون تغییر کار کند.
        """
        rev = self.get_current_revision()
        return rev.sections if rev else []
    
    @sections.setter
    def sections(self, value: List[ProjectSection]):
        """Setter برای سازگاری Backward"""
        rev = self.get_current_revision()
        if rev:
            rev.sections = value
    
    # ============================================================
    # ✅ متدهای قدیمی (که حالا از current_revision استفاده می‌کنند)
    # ============================================================
    
    def get_all_devices(self) -> List[Motor]:
        """
        دریافت تمام دستگاه‌های رویژن فعلی
        
        برای دریافت دستگاه‌های یک رویژن خاص:
            project.get_revision_by_name('Rev-0').get_all_devices()
        """
        rev = self.get_current_revision()
        return rev.get_all_devices() if rev else []
    
    def get_section_by_name(self, name: str) -> Optional[ProjectSection]:
        """دریافت بخش بر اساس نام (از رویژن فعلی)"""
        rev = self.get_current_revision()
        return rev.get_section_by_name(name) if rev else None
    
    def add_section(self, name: str, description: str = "") -> Optional[ProjectSection]:
        """
        اضافه کردن بخش جدید (به رویژن فعلی)
        
        Returns:
            ProjectSection جدید یا None اگر رویژن فعلی وجود نداشته باشد
        """
        rev = self.get_current_revision()
        if not rev:
            return None
        return rev.add_section(name, description)
    
    def delete_section(self, name: str) -> bool:
        """حذف بخش از رویژن فعلی"""
        rev = self.get_current_revision()
        if not rev:
            return False
        
        # نمی‌توان آخرین بخش را حذف کرد
        #if len(rev.sections) <= 1:
        #    return False
        
        return rev.delete_section(name)
    
    def get_total_io(self) -> int:
        """محاسبه مجموع I/O رویژن فعلی"""
        rev = self.get_current_revision()
        return rev.get_total_io() if rev else 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """دریافت آمار رویژن فعلی"""
        rev = self.get_current_revision()
        
        if not rev:
            return {
                'name': self.name,
                'total_sections': 0,
                'total_devices': 0,
                'total_di': 0,
                'total_do': 0,
                'total_ai': 0,
                'total_ao': 0,
                'total_io': 0,
                'active_devices': 0,
                'inactive_devices': 0
            }
        
        stats = rev.get_statistics()
        stats['name'] = self.name  # نام پروژه (نه رویژن)
        return stats
    
    def get_component_usage(self) -> Dict[str, int]:
        """دریافت استفاده از کامپوننت‌ها در رویژن فعلی"""
        rev = self.get_current_revision()
        return rev.get_component_usage() if rev else {}
    
    def get_controller_requirements(self) -> Dict[str, int]:
        """محاسبه تعداد کنترلرهای مورد نیاز (رویژن فعلی)"""
        total_io = self.get_total_io()
        cbx_count = max(0, (total_io + 63) // 64)
        fbx_count = max(0, (total_io + 15) // 16 - cbx_count)
        
        return {
            'cbx_8r8': cbx_count,
            'fbx_8r8': fbx_count,
            'total_io': total_io
        }
    
    # ============================================================
    # ✅ برچسب‌های کامپوننت
    # ============================================================
    
    def get_component_labels(self, db_manager=None) -> Dict[str, Dict[str, str]]:
        """دریافت برچسب‌های کامپوننت این پروژه"""
        if self.component_labels:
            return self.component_labels
        
        if db_manager:
            self.component_labels = db_manager.load_component_labels(self.name)
            if not self.component_labels:
                self.component_labels = COMPONENT_LABELS.copy()
                if hasattr(db_manager, 'save_component_labels'):
                    db_manager.save_component_labels(self.name, self.component_labels)
            return self.component_labels
        
        return COMPONENT_LABELS.copy()
    
    def update_component_labels(self, labels_dict: Dict[str, Dict[str, str]], db_manager=None):
        """بروزرسانی برچسب‌های کامپوننت این پروژه"""
        self.component_labels = labels_dict
        if db_manager and hasattr(db_manager, 'save_component_labels'):
            db_manager.save_component_labels(self.name, labels_dict)
    
    # ============================================================
    # ✅ Utility
    # ============================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری (برای بکاپ JSON)"""
        return {
            'name': self.name,
            'description': self.description,
            'client_name': self.client_name,
            'client_phone': self.client_phone,
            'client_address': self.client_address,
            'consultant_name': self.consultant_name,
            'consultant_phone': self.consultant_phone,
            'consultant_address': self.consultant_address,
            'contractor_name': self.contractor_name,
            'contractor_phone': self.contractor_phone,
            'contractor_address': self.contractor_address,
            'designer_name': self.designer_name,
            'current_revision_name': self.current_revision_name,
            'revisions': [
                {
                    'name': rev.name,
                    'description': rev.description,
                    'sections': [
                        {
                            'name': s.name,
                            'description': s.description,
                            'order_index': s.order_index,
                            'devices': [d.to_dict() for d in s.devices]
                        }
                        for s in rev.sections
                    ]
                }
                for rev in self.revisions
            ]
        }
    
    def __repr__(self) -> str:
        return (f"Project(Name='{self.name}', "
                f"Revisions={len(self.revisions)}, "
                f"Current='{self.current_revision_name}')")

# ================================================================
# ✅ کلاس جدید: Valve (شیر)
# ================================================================

class Valve:
    """
    مدل شیر - شامل تمام فیلدهای تخصصی شیرها
    
    تفاوت‌ها با Motor:
    - بدون I/O (DI, DO, AI, AO)
    - فیلدهای تخصصی PICV، 3Way، Steam
    - فیلدهای محاسبه‌شده (Kv, kvs, درصد)
    """
    
    # ============================================================
    # فیلدهای رشته‌ای
    # ============================================================
    STRING_FIELDS = [
        'Equipment',          # مشخصات تجهیز
        'Circuit',            # مدار
        'Unit',               # واحد
        'ValveType',          # نوع شیر
        'PICVModel',          # مدل شیر PICV
        'PICVActuator',       # مدل موتور PICV
        'PICVSignal',         # نوع سیگنال موتور PICV
        '3WayModel',          # مدل شیر سه راهه
        '3WayActuator',       # مدل موتور سه راهه
        '3WaySignal',         # نوع سیگنال موتور سه راهه
        'SteamModel',         # مدل شیر بخار
        'SteamActuator',      # مدل موتور شیر بخار
        'SteamSignal',        # نوع سیگنال موتور بخار
        'Warning3Way',        # هشدار VRG 3
        'WarningSteam',       # هشدار Steam
        'WarningGeneral',     # هشدار کلی
    ]
    
    # ============================================================
    # فیلدهای عددی (شامل اعداد صحیح و اعشاری)
    # ============================================================
    NUMERIC_FIELDS = [
        'Quantity',           # تعداد
        'Flow',               # دبی
        'PressureDrop',       # Pressure Drop (psi)
        'MaxFlowLPH',         # حداکثر دبی (L/HR)
        'PICVMaxFlow',        # حداکثر دبی PICV
        'PICVPercent',        # درصد تنظیم PICV
        'KvCalc',             # Kv محاسبه‌شده
        'KvSelected',         # Kv انتخاب‌شده
        '3WayDN',             # DN شیر سه راهه
        'SteamPressure',      # فشار ورودی بخار
        'KvsCalc',            # kvs محاسبه‌شده
        'KvsSelected',        # kvs انتخاب‌شده
        'SteamDN',            # DN شیر بخار
    ]
    
    # ============================================================
    # فیلدهای Boolean (اختیاری - برای آینده)
    # ============================================================
    BOOLEAN_FIELDS = []
    
    def __init__(self, **kwargs):
        """ایجاد شیر جدید با مقادیر ورودی"""
        
        # ============================================================
        # فیلدهای رشته‌ای
        # ============================================================
        for field in self.STRING_FIELDS:
            value = kwargs.get(field, '')
            setattr(self, field, self._validate_string(value, field))
        
        # ============================================================
        # فیلدهای عددی
        # ============================================================
        # مقادیر پیش‌فرض خاص
        defaults = {
            'Quantity': 1,
            'PressureDrop': 5,        # پیش‌فرض 5 psi
        }
        
        for field in self.NUMERIC_FIELDS:
            if field in kwargs:
                value = kwargs[field]
            else:
                value = defaults.get(field, 0)
            setattr(self, field, self._validate_number(value, field))
        
        # ============================================================
        # تاریخ ایجاد
        # ============================================================
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
    
    @staticmethod
    def _validate_string(value, field_name: str) -> str:
        """اعتبارسنجی فیلدهای رشته‌ای"""
        if value is None:
            return ''
        if not isinstance(value, str):
            return str(value)
        max_len = 500
        if len(value) > max_len:
            return value[:max_len]
        return value
    
    @staticmethod
    def _validate_number(value, field_name: str) -> float:
        """
        اعتبارسنجی فیلدهای عددی
        برای فیلدهای خاص، int و برای بقیه float
        """
        try:
            if isinstance(value, bool):
                return 1 if value else 0
            
            if isinstance(value, (int, float)):
                num = float(value)
            elif isinstance(value, str):
                if not value.strip():
                    return 0
                num = float(value)
            else:
                return 0
            
            # ============================================================
            # فیلدهای عدد صحیح
            # ============================================================
            int_fields = ['Quantity', '3WayDN', 'SteamDN']
            if field_name in int_fields:
                return int(num)
            
            # ============================================================
            # فیلدهای اعشاری
            # ============================================================
            return round(num, 4)
            
        except (ValueError, TypeError):
            return 0
    
    # ============================================================
    # متدهای کمکی
    # ============================================================
    
    def copy(self) -> 'Valve':
        """ایجاد کپی عمیق از شیر"""
        return Valve(**self.to_dict())
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری برای ذخیره‌سازی"""
        result = {}
        
        # فیلدهای رشته‌ای
        for field in self.STRING_FIELDS:
            result[field] = getattr(self, field, '')
        
        # فیلدهای عددی
        for field in self.NUMERIC_FIELDS:
            result[field] = getattr(self, field, 0)
        
        # تاریخ‌ها
        if hasattr(self, 'created_at'):
            if isinstance(self.created_at, datetime):
                result['created_at'] = self.created_at.isoformat()
            else:
                result['created_at'] = str(self.created_at)
        
        if hasattr(self, 'updated_at'):
            if isinstance(self.updated_at, datetime):
                result['updated_at'] = self.updated_at.isoformat()
            else:
                result['updated_at'] = str(self.updated_at)
        
        return result
    
    def from_dict(self, data: Dict[str, Any]) -> 'Valve':
        """بارگذاری از دیکشنری"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
    
    def is_valid(self) -> bool:
        """آیا شیر داده‌های اساسی را دارد؟"""
        return bool(self.Equipment and self.ValveType)
    
    def get_active_fields(self) -> List[str]:
        """
        دریافت فیلدهای فعال بر اساس نوع شیر
        
        Returns:
            لیست نام فیلدهای فعال
        """
        from core.valve_constants import VALVE_TYPE_FIELDS
        
        base_fields = [
            'Equipment', 'Quantity', 'Circuit',
            'Flow', 'PressureDrop', 'Unit',
            'ValveType', 'MaxFlowLPH',
        ]
        
        # فیلدهای مخصوص نوع شیر
        type_fields = VALVE_TYPE_FIELDS.get(self.ValveType, [])
        
        # تبدیل key های snake_case به CamelCase
        type_fields_camel = []
        for key in type_fields:
            camel = self._snake_to_camel(key)
            type_fields_camel.append(camel)
        
        return base_fields + type_fields_camel
    
    @staticmethod
    def _snake_to_camel(snake: str) -> str:
        """تبدیل snake_case به CamelCase"""
        # map دستی برای موارد خاص
        mapping = {
            'picv_model': 'PICVModel',
            'picv_max_flow': 'PICVMaxFlow',
            'picv_percent': 'PICVPercent',
            'picv_actuator': 'PICVActuator',
            'picv_signal': 'PICVSignal',
            'kv_calc': 'KvCalc',
            'kv_selected': 'KvSelected',
            '3way_dn': '3WayDN',
            '3way_model': '3WayModel',
            '3way_actuator': '3WayActuator',
            '3way_signal': '3WaySignal',
            'steam_pressure': 'SteamPressure',
            'kvs_calc': 'KvsCalc',
            'kvs_selected': 'KvsSelected',
            'steam_dn': 'SteamDN',
            'steam_model': 'SteamModel',
            'steam_actuator': 'SteamActuator',
            'steam_signal': 'SteamSignal',
            'warning_3way': 'Warning3Way',
            'warning_steam': 'WarningSteam',
            'warning_general': 'WarningGeneral',
        }
        return mapping.get(snake, snake)
    
    def has_warning(self) -> bool:
        """آیا شیر هشداری دارد؟"""
        return bool(self.Warning3Way or self.WarningSteam or self.WarningGeneral)
    
    def __repr__(self) -> str:
        return (
            f"Valve(Equipment='{self.Equipment}', "
            f"Type='{self.ValveType}', "
            f"Qty={self.Quantity})"
        )

__all__ = [
    'Motor',
    'ProjectSection',
    'Revision',   # ✅ جدید
    'Project',
    'Valve',
]