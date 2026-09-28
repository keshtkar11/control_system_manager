"""اعتبارسنجی ورودی‌های برنامه"""

import re
from typing import Any, Optional, Union
from datetime import datetime


# ==================== اعتبارسنجی عمومی ====================

def validate_required(value: Any, field_name: str = "Field") -> tuple:
    """
    بررسی وجود مقدار
    
    Args:
        value: مقدار ورودی
        field_name: نام فیلد برای نمایش خطا
    
    Returns:
        (is_valid, error_message)
    """
    if value is None:
        return False, f"{field_name} is required"
    if isinstance(value, str) and not value.strip():
        return False, f"{field_name} cannot be empty"
    return True, ""


def validate_length(value: str, min_len: int = 1, max_len: int = 100, 
                   field_name: str = "Field") -> tuple:
    """
    بررسی طول رشته
    
    Args:
        value: رشته ورودی
        min_len: حداقل طول
        max_len: حداکثر طول
        field_name: نام فیلد برای نمایش خطا
    
    Returns:
        (is_valid, error_message)
    """
    if not value:
        return False, f"{field_name} cannot be empty"
    
    length = len(value.strip())
    if length < min_len:
        return False, f"{field_name} must be at least {min_len} characters"
    if length > max_len:
        return False, f"{field_name} must be at most {max_len} characters"
    
    return True, ""


# ==================== اعتبارسنجی نام‌ها ====================

def validate_device_name(name: str) -> tuple:
    """
    اعتبارسنجی نام دستگاه
    
    قوانین:
    - حداقل ۱ و حداکثر ۱۰۰ کاراکتر
    - فقط شامل حروف انگلیسی، اعداد، خط تیره و زیرخط
    - نمی‌تواند با خط تیره شروع یا پایان یابد
    
    Args:
        name: نام دستگاه
    
    Returns:
        (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Device name cannot be empty"
    
    name = name.strip()
    
    if len(name) > 100:
        return False, "Device name must be at most 100 characters"
    
    # فقط حروف انگلیسی، اعداد، خط تیره و زیرخط
    if not re.match(r'^[A-Za-z0-9_-]+$', name):
        return False, "Device name can only contain letters, numbers, '-' and '_'"
    
    # نمی‌تواند با خط تیره شروع یا پایان یابد
    if name.startswith('-') or name.endswith('-'):
        return False, "Device name cannot start or end with '-'"
    
    return True, ""


def validate_project_name(name: str) -> tuple:
    """
    اعتبارسنجی نام پروژه
    
    Args:
        name: نام پروژه
    
    Returns:
        (is_valid, error_message)
    """
    return validate_length(name, 1, 100, "Project name")


def validate_section_name(name: str) -> tuple:
    """
    اعتبارسنجی نام بخش
    
    Args:
        name: نام بخش
    
    Returns:
        (is_valid, error_message)
    """
    return validate_length(name, 1, 100, "Section name")


# ==================== اعتبارسنجی I/O ====================

def validate_io_value(value: Union[int, str]) -> tuple:
    """
    اعتبارسنجی مقدار I/O
    
    قوانین:
    - باید عدد صحیح باشد
    - بین ۰ تا ۹۹۹
    
    Args:
        value: مقدار I/O
    
    Returns:
        (is_valid, error_message)
    """
    try:
        num = int(value)
    except (ValueError, TypeError):
        return False, "I/O value must be a number"
    
    if num < 0:
        return False, "I/O value cannot be negative"
    if num > 999:
        return False, "I/O value cannot exceed 999"
    
    return True, ""


def validate_io_summary(io_dict: dict) -> tuple:
    """
    اعتبارسنجی خلاصه I/O
    
    Args:
        io_dict: دیکشنری شامل DI, DO, AI, AO
    
    Returns:
        (is_valid, error_message)
    """
    required_keys = ['DI', 'DO', 'AI', 'AO']
    
    for key in required_keys:
        if key not in io_dict:
            return False, f"Missing '{key}' in I/O summary"
        
        is_valid, msg = validate_io_value(io_dict[key])
        if not is_valid:
            return False, f"{key}: {msg}"
    
    return True, ""


# ==================== اعتبارسنجی اطلاعات تماس ====================

def validate_phone(phone: str) -> tuple:
    """
    اعتبارسنجی شماره تلفن ایران
    
    فرمت‌های پشتیبانی شده:
    - 09123456789
    - 021-12345678
    - 0912-345-6789
    
    Args:
        phone: شماره تلفن
    
    Returns:
        (is_valid, error_message)
    """
    if not phone or not phone.strip():
        return True, ""  # شماره تلفن اختیاری است
    
    phone = phone.strip()
    
    # حذف فاصله‌ها و خط تیره‌ها
    cleaned = re.sub(r'[\s\-]', '', phone)
    
    # بررسی فرمت‌های مختلف
    patterns = [
        r'^09\d{9}$',           # 09123456789
        r'^0\d{10}$',           # 02112345678
        r'^9\d{9}$',            # 9123456789
        r'^\+989\d{9}$',        # +989123456789
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return True, ""
    
    return False, "Invalid phone number format"


def validate_email(email: str) -> tuple:
    """
    اعتبارسنجی ایمیل
    
    Args:
        email: آدرس ایمیل
    
    Returns:
        (is_valid, error_message)
    """
    if not email or not email.strip():
        return True, ""  # ایمیل اختیاری است
    
    email = email.strip()
    
    # فرمت ساده ایمیل
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(pattern, email):
        return True, ""
    
    return False, "Invalid email format"


# ==================== اعتبارسنجی کامپوننت‌ها ====================

def validate_component_quantity(quantity: Union[int, str]) -> tuple:
    """
    اعتبارسنجی تعداد کامپوننت
    
    قوانین:
    - باید عدد صحیح باشد
    - بین ۰ تا ۱۰۰
    
    Args:
        quantity: تعداد کامپوننت
    
    Returns:
        (is_valid, error_message)
    """
    try:
        num = int(quantity)
    except (ValueError, TypeError):
        return False, "Quantity must be a number"
    
    if num < 0:
        return False, "Quantity cannot be negative"
    if num > 100:
        return False, "Quantity cannot exceed 100"
    
    return True, ""


def validate_component_key(key: str, valid_keys: list) -> tuple:
    """
    اعتبارسنجی کلید کامپوننت
    
    Args:
        key: کلید کامپوننت
        valid_keys: لیست کلیدهای معتبر
    
    Returns:
        (is_valid, error_message)
    """
    if not key or not key.strip():
        return False, "Component key cannot be empty"
    
    if key not in valid_keys:
        return False, f"Invalid component key: {key}"
    
    return True, ""


# ==================== اعتبارسنجی تاریخ ====================

def validate_date(date_str: str, format_str: str = "%Y-%m-%d") -> tuple:
    """
    اعتبارسنجی تاریخ
    
    Args:
        date_str: رشته تاریخ
        format_str: فرمت تاریخ
    
    Returns:
        (is_valid, error_message)
    """
    if not date_str or not date_str.strip():
        return True, ""  # تاریخ اختیاری است
    
    try:
        datetime.strptime(date_str.strip(), format_str)
        return True, ""
    except ValueError:
        return False, f"Invalid date format. Expected: {format_str}"


# ==================== اعتبارسنجی توضیحات ====================

def validate_description(description: str, max_len: int = 500) -> tuple:
    """
    اعتبارسنجی توضیحات
    
    Args:
        description: متن توضیحات
        max_len: حداکثر طول
    
    Returns:
        (is_valid, error_message)
    """
    if not description:
        return True, ""  # توضیحات اختیاری است
    
    if len(description.strip()) > max_len:
        return False, f"Description must be at most {max_len} characters"
    
    return True, ""


# ==================== اعتبارسنجی مقادیر عددی ====================

def validate_positive_number(value: Union[int, float, str], 
                            field_name: str = "Value") -> tuple:
    """
    اعتبارسنجی عدد مثبت
    
    Args:
        value: مقدار ورودی
        field_name: نام فیلد
    
    Returns:
        (is_valid, error_message)
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        return False, f"{field_name} must be a number"
    
    if num < 0:
        return False, f"{field_name} cannot be negative"
    
    return True, ""


def validate_range(value: Union[int, float], min_val: Union[int, float], 
                  max_val: Union[int, float], field_name: str = "Value") -> tuple:
    """
    اعتبارسنجی بازه عددی
    
    Args:
        value: مقدار ورودی
        min_val: حداقل مقدار
        max_val: حداکثر مقدار
        field_name: نام فیلد
    
    Returns:
        (is_valid, error_message)
    """
    try:
        num = float(value)
    except (ValueError, TypeError):
        return False, f"{field_name} must be a number"
    
    if num < min_val:
        return False, f"{field_name} must be at least {min_val}"
    if num > max_val:
        return False, f"{field_name} must be at most {max_val}"
    
    return True, ""


# ==================== اعتبارسنجی ترکیبی ====================

def validate_device_all(name: str, di: int, do: int, ai: int, ao: int) -> tuple:
    """
    اعتبارسنجی کامل یک دستگاه
    
    Args:
        name: نام دستگاه
        di: تعداد DI
        do: تعداد DO
        ai: تعداد AI
        ao: تعداد AO
    
    Returns:
        (is_valid, errors_list)
    """
    errors = []
    
    # اعتبارسنجی نام
    is_valid, msg = validate_device_name(name)
    if not is_valid:
        errors.append(f"Name: {msg}")
    
    # اعتبارسنجی I/O
    for key, value in [('DI', di), ('DO', do), ('AI', ai), ('AO', ao)]:
        is_valid, msg = validate_io_value(value)
        if not is_valid:
            errors.append(f"{key}: {msg}")
    
    return len(errors) == 0, errors


# ==================== توابع کمکی ====================

def sanitize_string(value: str) -> str:
    """
    پاکسازی رشته (حذف فاصله‌های اضافی)
    
    Args:
        value: رشته ورودی
    
    Returns:
        رشته پاکسازی شده
    """
    if not value:
        return ""
    return value.strip()


def is_empty(value: Any) -> bool:
    """
    بررسی خالی بودن مقدار
    
    Args:
        value: مقدار ورودی
    
    Returns:
        True اگر خالی باشد
    """
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict, tuple)):
        return len(value) == 0
    return False


def get_validation_errors(errors: list) -> str:
    """
    تبدیل لیست خطاها به رشته
    
    Args:
        errors: لیست خطاها
    
    Returns:
        رشته خطاها
    """
    if not errors:
        return ""
    return "\n".join(f"• {e}" for e in errors)