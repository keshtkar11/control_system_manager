"""توابع کمکی عمومی برای استفاده در سراسر برنامه"""

import re
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import math


# ==================== تبدیل اعداد به حروف ====================

def number_to_letter(n: int) -> str:
    """
    تبدیل عدد به حروف فارسی
    
    Args:
        n: عدد صحیح
    
    Returns:
        عدد به صورت حروف
    
    Examples:
        >>> number_to_letter(1)
        'یک'
        >>> number_to_letter(25)
        'بیست و پنج'
    """
    if n < 0:
        return "منفی " + number_to_letter(-n)
    
    if n == 0:
        return "صفر"
    
    units = ["", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه"]
    teens = ["ده", "یازده", "دوازده", "سیزده", "چهارده", "پانزده", "شانزده", "هفده", "هجده", "نوزده"]
    tens = ["", "ده", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود"]
    hundreds = ["", "صد", "دویست", "سیصد", "چهارصد", "پانصد", "ششصد", "هفتصد", "هشتصد", "نهصد"]
    
    if n < 10:
        return units[n]
    elif n < 20:
        return teens[n - 10]
    elif n < 100:
        t = n // 10
        u = n % 10
        if u == 0:
            return tens[t]
        return tens[t] + " و " + units[u]
    elif n < 1000:
        h = n // 100
        r = n % 100
        if r == 0:
            return hundreds[h]
        return hundreds[h] + " و " + number_to_letter(r)
    elif n < 1000000:
        th = n // 1000
        r = n % 1000
        if r == 0:
            return number_to_letter(th) + " هزار"
        return number_to_letter(th) + " هزار و " + number_to_letter(r)
    else:
        return str(n)  # برای اعداد بزرگتر


def number_to_english(n: int) -> str:
    """
    تبدیل عدد به حروف انگلیسی
    
    Args:
        n: عدد صحیح
    
    Returns:
        عدد به صورت حروف انگلیسی
    
    Examples:
        >>> number_to_english(1)
        'one'
        >>> number_to_english(25)
        'twenty-five'
    """
    if n < 0:
        return "negative " + number_to_english(-n)
    
    if n == 0:
        return "zero"
    
    units = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", 
             "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "ten", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    
    if n < 10:
        return units[n]
    elif n < 20:
        return teens[n - 10]
    elif n < 100:
        t = n // 10
        u = n % 10
        if u == 0:
            return tens[t]
        return tens[t] + "-" + units[u]
    elif n < 1000:
        h = n // 100
        r = n % 100
        if r == 0:
            return units[h] + " hundred"
        return units[h] + " hundred and " + number_to_english(r)
    else:
        return str(n)


# ==================== محاسبات I/O ====================

def calculate_io(motor: Any) -> Dict[str, int]:
    """
    محاسبه I/O یک دستگاه
    
    Args:
        motor: شیء Motor
    
    Returns:
        دیکشنری شامل DI, DO, AI, AO
    """
    return {
        'DI': getattr(motor, 'DI', 0),
        'DO': getattr(motor, 'DO', 0),
        'AI': getattr(motor, 'AI', 0),
        'AO': getattr(motor, 'AO', 0)
    }


def get_io_summary(devices: List[Any]) -> Dict[str, int]:
    """
    دریافت خلاصه I/O لیست دستگاه‌ها
    
    Args:
        devices: لیست دستگاه‌ها
    
    Returns:
        دیکشنری شامل مجموع DI, DO, AI, AO
    """
    summary = {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0}
    
    for device in devices:
        summary['DI'] += getattr(device, 'DI', 0)
        summary['DO'] += getattr(device, 'DO', 0)
        summary['AI'] += getattr(device, 'AI', 0)
        summary['AO'] += getattr(device, 'AO', 0)
    
    summary['total'] = sum(summary.values())
    return summary


def calculate_controller_count(io_total: int) -> Dict[str, int]:
    """
    محاسبه تعداد کنترلرهای مورد نیاز
    
    Args:
        io_total: تعداد کل I/O
    
    Returns:
        دیکشنری شامل تعداد CBX و FBX
    
    Examples:
        >>> calculate_controller_count(50)
        {'cbx': 1, 'fbx': 2}
    """
    if io_total <= 0:
        return {'cbx': 0, 'fbx': 0}
    
    # هر CBX دارای 64 نقطه I/O
    cbx = math.ceil(io_total / 64)
    
    # هر FBX دارای 16 نقطه I/O
    # یک CBX وجود دارد، بقیه FBX هستند
    remaining = max(0, io_total - cbx * 16)
    fbx = math.ceil(remaining / 16) if remaining > 0 else 0
    
    return {'cbx': cbx, 'fbx': fbx}


# ==================== تاریخ و زمان ====================

def format_datetime(dt: Optional[datetime] = None, 
                   format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    فرمت‌دهی تاریخ و زمان
    
    Args:
        dt: شیء datetime (اگر None باشد، زمان حال استفاده می‌شود)
        format_str: فرمت خروجی
    
    Returns:
        رشته تاریخ فرمت شده
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


def format_date_persian(dt: Optional[datetime] = None) -> str:
    """
    فرمت‌دهی تاریخ به صورت فارسی
    
    Args:
        dt: شیء datetime (اگر None باشد، زمان حال استفاده می‌شود)
    
    Returns:
        تاریخ به صورت فارسی
    
    Examples:
        >>> format_date_persian()
        '۱۴۰۳/۰۶/۱۵ ۱۴:۳۰:۲۵'
    """
    if dt is None:
        dt = datetime.now()
    
    # تبدیل سال میلادی به شمسی
    # این یک پیاده‌سازی ساده است
    # برای پیاده‌سازی کامل می‌توان از کتابخانه jdatetime استفاده کرد
    
    persian_months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    
    # محاسبه تاریخ شمسی (تقریبی)
    year = dt.year - 621
    month = dt.month
    day = dt.day
    
    if month <= 3:
        year += 1
        month = month + 9
    elif month <= 12:
        month = month - 3
    
    return f"{year:04d}/{month:02d}/{day:02d} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"


def get_relative_time(dt: datetime) -> str:
    """
    نمایش زمان به صورت نسبی
    
    Args:
        dt: شیء datetime
    
    Returns:
        زمان نسبی
    
    Examples:
        >>> get_relative_time(datetime.now())
        'لحظاتی پیش'
        >>> get_relative_time(datetime.now() - timedelta(hours=2))
        '۲ ساعت پیش'
    """
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "لحظاتی پیش"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} دقیقه پیش"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} ساعت پیش"
    elif seconds < 604800:
        days = int(seconds // 86400)
        return f"{days} روز پیش"
    elif seconds < 2592000:
        weeks = int(seconds // 604800)
        return f"{weeks} هفته پیش"
    else:
        return format_datetime(dt, "%Y/%m/%d")


# ==================== شناسه‌های یکتا ====================

def generate_unique_id(prefix: str = "", length: int = 8) -> str:
    """
    تولید شناسه یکتا
    
    Args:
        prefix: پیشوند
        length: طول شناسه
    
    Returns:
        شناسه یکتا
    """
    unique_id = uuid.uuid4().hex[:length].upper()
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id


def generate_device_id(device_type: str, counter: int) -> str:
    """
    تولید شناسه دستگاه
    
    Args:
        device_type: نوع دستگاه
        counter: شمارنده
    
    Returns:
        شناسه دستگاه
    
    Examples:
        >>> generate_device_id("PU", 1)
        'PU-001'
    """
    return f"{device_type}-{counter:03d}"


# ==================== متون و رشته‌ها ====================

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    کوتاه کردن متن
    
    Args:
        text: متن ورودی
        max_length: حداکثر طول
        suffix: پسوند نمایش
    
    Returns:
        متن کوتاه شده
    """
    if not text:
        return ""
    
    text = str(text)
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def to_camel_case(text: str) -> str:
    """
    تبدیل متن به CamelCase
    
    Args:
        text: متن ورودی
    
    Returns:
        متن به صورت CamelCase
    
    Examples:
        >>> to_camel_case("hello world")
        'HelloWorld'
    """
    words = re.split(r'[_\s\-]+', text)
    return ''.join(word.capitalize() for word in words)


def to_snake_case(text: str) -> str:
    """
    تبدیل متن به snake_case
    
    Args:
        text: متن ورودی
    
    Returns:
        متن به صورت snake_case
    
    Examples:
        >>> to_snake_case("HelloWorld")
        'hello_world'
    """
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', '_', text)
    text = re.sub(r'[\s\-]+', '_', text)
    return text.lower().strip('_')


def extract_numbers(text: str) -> List[int]:
    """
    استخراج اعداد از متن
    
    Args:
        text: متن ورودی
    
    Returns:
        لیست اعداد
    
    Examples:
        >>> extract_numbers("PU-001 and PU-002")
        [1, 2]
    """
    return [int(x) for x in re.findall(r'\d+', text)]


# ==================== فرمت‌دهی ====================

def format_io(io_dict: Dict[str, int]) -> str:
    """
    فرمت‌دهی I/O برای نمایش
    
    Args:
        io_dict: دیکشنری I/O
    
    Returns:
        رشته فرمت شده
    
    Examples:
        >>> format_io({'DI': 5, 'DO': 3, 'AI': 2, 'AO': 1})
        'DI:5 DO:3 AI:2 AO:1 (Total: 11)'
    """
    total = sum(io_dict.values())
    parts = [f"{k}:{v}" for k, v in io_dict.items() if v > 0]
    return f"{' '.join(parts)} (Total: {total})"


def format_size(bytes_size: int) -> str:
    """
    فرمت‌دهی حجم فایل
    
    Args:
        bytes_size: حجم به بایت
    
    Returns:
        رشته فرمت شده
    
    Examples:
        >>> format_size(1024)
        '1.00 KB'
        >>> format_size(1048576)
        '1.00 MB'
    """
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1048576:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1073741824:
        return f"{bytes_size / 1048576:.2f} MB"
    else:
        return f"{bytes_size / 1073741824:.2f} GB"


# ==================== عملیات امن ====================

def safe_divide(a: Union[int, float], b: Union[int, float], 
                default: float = 0.0) -> float:
    """
    تقسیم امن با مدیریت خطا
    
    Args:
        a: صورت
        b: مخرج
        default: مقدار پیش‌فرض در صورت خطا
    
    Returns:
        نتیجه تقسیم
    
    Examples:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)
        0.0
    """
    try:
        return a / b
    except (ZeroDivisionError, TypeError):
        return default


def safe_get(dictionary: dict, key: str, default: Any = None) -> Any:
    """
    دریافت امن از دیکشنری
    
    Args:
        dictionary: دیکشنری
        key: کلید
        default: مقدار پیش‌فرض
    
    Returns:
        مقدار یافت شده یا پیش‌فرض
    """
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default


# ==================== اعتبارسنجی ====================

def is_valid_io_name(name: str) -> bool:
    """
    بررسی معتبر بودن نام I/O
    
    Args:
        name: نام I/O
    
    Returns:
        True اگر معتبر باشد
    """
    if not name:
        return False
    return bool(re.match(r'^[A-Za-z0-9_\-]+$', name))


def is_valid_number(value: Any) -> bool:
    """
    بررسی عدد بودن
    
    Args:
        value: مقدار ورودی
    
    Returns:
        True اگر عدد باشد
    """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


# ==================== متفرقه ====================

def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """
    ادغام دو دیکشنری (دیکشنری دوم اولویت دارد)
    
    Args:
        dict1: دیکشنری اول
        dict2: دیکشنری دوم
    
    Returns:
        دیکشنری ادغام شده
    """
    result = dict1.copy()
    result.update(dict2)
    return result


def chunk_list(lst: list, chunk_size: int) -> List[list]:
    """
    تقسیم لیست به تکه‌های کوچکتر
    
    Args:
        lst: لیست ورودی
        chunk_size: اندازه هر تکه
    
    Returns:
        لیست تکه‌ها
    
    Examples:
        >>> chunk_list([1,2,3,4,5], 2)
        [[1,2], [3,4], [5]]
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]