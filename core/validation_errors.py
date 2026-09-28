"""
سیستم مدیریت خطاهای اعتبارسنجی پروژه
قابل توسعه برای خطاهای بیشتر در آینده

این فایل جدا از validators.py است:
- validators.py: اعتبارسنجی ورودی کاربر (نام، تلفن، ایمیل)
- validation_errors.py: اعتبارسنجی منطق پروژه (تعداد PU، FS، VSD)
"""

from typing import List, Dict, Any
from enum import Enum


# ============================================================
# تنظیمات اتصال کامپوننت‌ها (قابل توسعه)
# ============================================================

# کامپوننت‌هایی که به PU متصل می‌شوند
# در آینده می‌توان موارد بیشتری اضافه کرد:
#   - 'PS'   (Pressure Switch)
#   - 'DPS'  (Differential Pressure Switch)
#   - 'FA'   (Fault Alarm)
#   - 'FE'   (Run Feedback)
PU_ATTACHED_COMPONENTS = [
    'FS',   # Flow Switch
    'VSD',  # Variable Speed Drive
]


# ============================================================
# ENUMS
# ============================================================

class ErrorSeverity(Enum):
    """سطح خطا"""
    INFO = "info"          # اطلاع‌رسانی
    WARNING = "warning"    # هشدار
    ERROR = "error"        # خطای جدی
    CRITICAL = "critical"  # خطای بحرانی


# ============================================================
# VALIDATION ERROR
# ============================================================

class ValidationError:
    """یک خطای اعتبارسنجی"""
    
    def __init__(
        self,
        code: str,
        severity: ErrorSeverity,
        title: str,
        message: str,
        suggestion: str = "",
        context: Dict[str, Any] = None,
    ):
        self.code = code
        self.severity = severity
        self.title = title
        self.message = message
        self.suggestion = suggestion
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            'code': self.code,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'suggestion': self.suggestion,
            'context': self.context,
        }
    
    def __repr__(self):
        return f"[{self.severity.value.upper()}] {self.code}: {self.title}"


# ============================================================
# VALIDATION ERROR COLLECTOR
# ============================================================

class ValidationErrorCollector:
    """جمع‌آورنده خطاها برای یک پروژه/بخش"""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
    
    # ===== افزودن خطا =====
    
    def add(self, error: ValidationError):
        """افزودن خطا"""
        self.errors.append(error)
    
    def add_component_mismatch(
        self,
        device_name: str,
        section_name: str,
        component_a: str,
        count_a: int,
        component_b: str,
        count_b: int,
    ):
        """
        افزودن خطای عدم تطابق تعداد کامپوننت‌ها
        
        مثال: PU=3 اما FS=2
        """
        self.add(ValidationError(
            code="COMPONENT_COUNT_MISMATCH",
            severity=ErrorSeverity.ERROR,
            title=f"عدم تطابق تعداد {component_a} و {component_b}",
            message=(
                f"دستگاه '{device_name}' در بخش '{section_name}':\n"
                f"  • تعداد {component_a}: {count_a}\n"
                f"  • تعداد {component_b}: {count_b}\n"
                f"تعداد این دو کامپوننت باید برابر باشد یا هر دو صفر."
            ),
            suggestion=(
                f"تعداد {component_b} را به {count_a} تغییر دهید "
                f"یا تعداد {component_a} را به {count_b}."
            ),
            context={
                'device_name': device_name,
                'section_name': section_name,
                'component_a': component_a,
                'count_a': count_a,
                'component_b': component_b,
                'count_b': count_b,
            }
        ))
    
    def add_missing_component(
        self,
        device_name: str,
        section_name: str,
        component_key: str,
    ):
        """افزودن خطای کامپوننت گم‌شده"""
        self.add(ValidationError(
            code="MISSING_COMPONENT",
            severity=ErrorSeverity.WARNING,
            title=f"کامپوننت {component_key} تعریف نشده",
            message=(
                f"دستگاه '{device_name}' در بخش '{section_name}':\n"
                f"کامپوننت {component_key} تعریف نشده است."
            ),
            suggestion=f"کامپوننت {component_key} را اضافه کنید یا نادیده بگیرید.",
            context={
                'device_name': device_name,
                'section_name': section_name,
                'component': component_key,
            }
        ))
    
    # ===== بررسی‌ها =====
    
    def has_errors(self) -> bool:
        """آیا خطای ERROR یا بالاتر وجود دارد؟"""
        return any(
            e.severity in (ErrorSeverity.ERROR, ErrorSeverity.CRITICAL)
            for e in self.errors
        )
    
    def has_warnings(self) -> bool:
        """آیا هشدار وجود دارد؟"""
        return any(
            e.severity == ErrorSeverity.WARNING
            for e in self.errors
        )
    
    def has_any(self) -> bool:
        """آیا هر خطایی وجود دارد؟"""
        return len(self.errors) > 0
    
    def get_by_severity(self, severity: ErrorSeverity) -> List[ValidationError]:
        """دریافت خطاها بر اساس سطح"""
        return [e for e in self.errors if e.severity == severity]
    
    def count(self) -> int:
        """تعداد کل خطاها"""
        return len(self.errors)
    
    def clear(self):
        """پاک کردن همه خطاها"""
        self.errors.clear()
    
    # ===== گزارش =====
    
    def to_report(self) -> str:
        """تبدیل به گزارش متنی"""
        if not self.errors:
            return "✅ No validation errors found.\n"
        
        report = "⚠️ VALIDATION REPORT\n"
        report += "=" * 75 + "\n\n"
        
        # گروه‌بندی بر اساس severity
        severity_order = [
            ErrorSeverity.CRITICAL,
            ErrorSeverity.ERROR,
            ErrorSeverity.WARNING,
            ErrorSeverity.INFO,
        ]
        
        for severity in severity_order:
            errors = self.get_by_severity(severity)
            if not errors:
                continue
            
            icon = {
                ErrorSeverity.CRITICAL: '🔴',
                ErrorSeverity.ERROR: '🟠',
                ErrorSeverity.WARNING: '🟡',
                ErrorSeverity.INFO: '🔵',
            }[severity]
            
            report += f"\n{icon} {severity.value.upper()} ({len(errors)})\n"
            report += "-" * 75 + "\n"
            
            for err in errors:
                report += f"  [{err.code}] {err.title}\n"
                report += f"    {err.message}\n"
                if err.suggestion:
                    report += f"    💡 {err.suggestion}\n"
                report += "\n"
        
        report += "=" * 75 + "\n"
        report += f"Total: {self.count()} issue(s)\n"
        
        return report


# ============================================================
# DEVICE VALIDATION
# ============================================================

def validate_device_components(
    device,
    section_name: str = "",
    collector: ValidationErrorCollector = None,
) -> ValidationErrorCollector:
    """
    اعتبارسنجی کامپوننت‌های یک دستگاه
    
    قوانین:
        PU=0 → تمام کامپوننت‌های متصل، عادی هستند (بدون خطا)
        PU>0 → تعداد هر کامپوننت متصل باید با PU برابر باشد
    
    Args:
        device: دستگاه (Motor)
        section_name: نام بخش
        collector: جمع‌آورنده خطا (اختیاری)
    
    Returns:
        ValidationErrorCollector
    """
    if collector is None:
        collector = ValidationErrorCollector()
    
    device_name = device.Name or "Unnamed"
    pu_count = getattr(device, 'PU', 0)
    
    # ============================================================
    # اگر PU=0، هیچ اعتبارسنجی نیاز نیست
    # (FS=N یا VSD=N بدون PU، عادی است)
    # ============================================================
    if pu_count == 0:
        return collector
    
    # ============================================================
    # اعتبارسنجی برای هر کامپوننت متصل به PU
    # ============================================================
    for comp_key in PU_ATTACHED_COMPONENTS:
        comp_count = getattr(device, comp_key, 0)
        
        # حالت: PU>0, comp=0 → عادی
        if comp_count == 0:
            continue
        
        # حالت: PU>0, comp>0, PU == comp → عادی
        if pu_count == comp_count:
            continue
        
        # حالت: PU>0, comp>0, PU != comp → خطا
        collector.add_component_mismatch(
            device_name=device_name,
            section_name=section_name,
            component_a='PU',
            count_a=pu_count,
            component_b=comp_key,
            count_b=comp_count,
        )
    
    return collector


# ============================================================
# PROJECT VALIDATION
# ============================================================

def validate_project_components(project) -> ValidationErrorCollector:
    """
    اعتبارسنجی همه دستگاه‌های یک پروژه
    
    Args:
        project: پروژه
    
    Returns:
        ValidationErrorCollector
    """
    collector = ValidationErrorCollector()
    
    for section in project.sections:
        for device in section.devices:
            validate_device_components(
                device,
                section_name=section.name,
                collector=collector,
            )
    
    return collector


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    'ErrorSeverity',
    'ValidationError',
    'ValidationErrorCollector',
    'PU_ATTACHED_COMPONENTS',
    'validate_device_components',
    'validate_project_components',
]