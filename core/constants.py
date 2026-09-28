"""ثابت‌های عمومی برنامه - همه تنظیمات در یکجا"""
"""ثابت‌های عمومی برنامه - همه تنظیمات در یکجا"""

import os
import sys
from typing import Dict
from datetime import datetime
from pathlib import Path


# ============================================================
# ✅ مسیرهای برنامه (قبل از هر چیز)
# ============================================================

# ===== مسیر base (Development یا EXE) =====
if getattr(sys, 'frozen', False):
    # EXE: پوشه‌ی exe
    APP_ROOT = os.path.dirname(sys.executable)
else:
    # Development: ریشه پروژه
    APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ============================================================
# ✅ تابع محاسبه مسیر داده (Development / EXE)
# ============================================================
# ================================================================
# مسیر داده‌های کاربر (USER DATA PATH)
# ================================================================

def _compute_app_data_path() -> str:
    """
    محاسبه مسیر داده‌های نوشتنی.
    
    ✅ جدید: این تابع فقط از utils.paths استفاده می‌کند (منبع واحد).
    
    Returns:
        مسیر به صورت str
    """
    try:
        from utils.paths import get_user_data_dir
        return str(get_user_data_dir())
    except Exception as e:
        # ===== Fallback: منطق قدیمی =====
        import logging
        logging.getLogger(__name__).warning(
            f"⚠️ Could not import utils.paths, using fallback: {e}"
        )
        
        import os
        import sys
        from pathlib import Path
        
        # اولویت: D:\ → %APPDATA% → development
        if os.path.exists("D:\\"):
            return r"D:\BMS Projects\IO_List_Generator"
        
        if getattr(sys, 'frozen', False):
            base = Path(os.environ.get("APPDATA", Path.home()))
            return str(base / "ControlSystemManager")
        
        return str(Path(__file__).resolve().parents[1] / "data")


APP_DATA_PATH = _compute_app_data_path()


# ================================================================
# مسیر دیتابیس
# ================================================================

def _compute_db_path() -> str:
    """
    محاسبه مسیر دیتابیس.
    
    ✅ جدید: این تابع فقط از utils.paths استفاده می‌کند.
    """
    try:
        from utils.paths import get_database_path
        return str(get_database_path())
    except Exception:
        # ===== Fallback =====
        import os
        return os.path.join(APP_DATA_PATH, "IO_List_Generator.db")


DEFAULT_DB_PATH = _compute_db_path()


# ================================================================
# مسیر قدیمی (برای Migration)
# ================================================================

OLD_APP_DATA_PATH = os.path.join(
    os.environ.get('PROGRAMDATA', 'C:\\ProgramData'),
    'IO_List_Generator'
)


# ============================================================
# ✅ مسیر آیکون — با پشتیبانی از EXE و Development
# ============================================================

def _compute_icon_path() -> str:
    """مسیر آیکون — با پشتیبانی از EXE و Development"""
    if getattr(sys, 'frozen', False):
        # EXE: از _MEIPASS
        return os.path.join(sys._MEIPASS, "resources", "icons", "icon.ico")
    else:
        # Development
        return os.path.join(APP_ROOT, "resources", "icons", "icon.ico")


ICON_PATH = _compute_icon_path()

# ==================== API ====================
DEFAULT_API_KEY = "sk-127147a27dc0408da3d9921c7f5ed841"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# ==================== پنجره ====================
WINDOW = {
    'width_ratio': 0.9,
    'height_ratio': 0.85,
    'min_width': 1400,
    'min_height': 600,
    'title': "Control System Devices Manager (Vahhaj Sanat Co.)"
}

# ==================== محدودیت‌ها ====================
LIMITS = {
    'max_history': 50,
    'max_device_name': 100,      # ✅ برای device
    'max_name_length': 100,      # ✅ برای سازگاری
    'max_description': 500,
    'max_info_length': 200,
    'max_section_name': 50,
    'max_project_name': 100,
    'max_io': 999,
    'min_io': 0,
}

# ==================== رنگ‌ها ====================
COLORS = {
    'primary': '#2C3E50',
    'secondary': '#34495E',
    'accent': '#3498DB',
    'success': '#27AE60',
    'warning': '#F39C12',
    'danger': '#E74C3C',
    'light': '#ECF0F1',
    'dark': '#2C3E50',
    'background': '#F8F9FA',
    'white': '#FFFFFF',
    'black': '#000000'
}


# ============================================================
# تاریخ شمسی
# ============================================================

def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple:
    """تبدیل تاریخ میلادی به شمسی"""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    
    if gm > 2:
        gy2 = gy + 1
    else:
        gy2 = gy
    
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + \
           ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    
    return jy, jm, jd


def get_timestamp_for_filename() -> str:
    """دریافت timestamp برای نام فایل (تاریخ شمسی + ساعت)"""
    now = datetime.now()
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    return f"{jy}-{jm:02d}-{jd:02d}_{now.hour:02d}-{now.minute:02d}"


# ============================================================
# توابع کمکی
# ============================================================

def validate_device_name(name: str) -> bool:
    """اعتبارسنجی نام دستگاه"""
    if not name or len(name) > LIMITS.get('max_device_name', 100):
        return False
    return True


def validate_io_value(value: int) -> bool:
    """اعتبارسنجی مقدار I/O"""
    if not isinstance(value, int):
        return False
    return LIMITS['min_io'] <= value <= LIMITS['max_io']


# ==================== برچسب‌های کامپوننت ====================
COMPONENT_LABELS: Dict[str, Dict[str, str]] = {
    'FS': {"fa": "سوئیچ جریان", "en": "Flow Switch"},
    'DTS': {"fa": "سنسور دمای کانال", "en": "Duct Temp Sensor"},
    'ITS': {"fa": "سنسور دمای غوطه‌وری", "en": "Immersion Temp Sensor"},
    'DTHS': {"fa": "سنسور دما و رطوبت کانال", "en": "Duct Temp & Humidity Sensor"},
    'FR': {"fa": "محافظ یخ‌زدگی", "en": "Freeze Protection"},
    'AQ': {"fa": "سنسور کیفیت هوا", "en": "Air Quality"},
    'DAM_T1': {"fa": "دمپر ON/OFF با فنر", "en": "ON/OFF Damper  With Spring"},
    'DAM_T2': {"fa": "دمپر ON/OFF بدون فنر", "en": "ON/OFF Damper  Without Spring"},
    'DAM_T3': {"fa": "دمپر Modulating با فنر", "en": "Modulating Damper  With Spring"},
    'DAM_T4': {"fa": "دمپر Modulating بدون فنر", "en": "Modulating Damper  Without Spring"},
    'RTS': {"fa": "سنسور دمای اتاق", "en": "Room Temp Sensor"},
    'RTHS': {"fa": "سنسور دما و رطوبت اتاق", "en": "Room Temp & Humidity"},
    'SD': {"fa": "آشکارساز دود", "en": "Smoke Detector"},
    'AVS': {"fa": "سنسور سرعت هوا", "en": "Air Velocity Sensor"},
    'VA': {"fa": "اکچویتور شیر", "en": "Valve Actuator"},
    'LS': {"fa": "سوئیچ سطح", "en": "Level Switch"},
    'LT': {"fa": "ترانسمیتر سطح", "en": "Level Transmitter"},
    'PS': {"fa": "سوئیچ فشار", "en": "Pressure Switch"},
    'PT': {"fa": "ترانسمیتر فشار", "en": "Pressure Transmitter"},
    'DPT': {"fa": "ترانسمیتر فشار تفاضلی", "en": "Diff. Pressure Transmitter"},
    'DPS': {"fa": "سوئیچ فشار تفاضلی", "en": "Differential Pressure Switch"},
    'PU': {"fa": "موتور", "en": "Motor"},
    'VSD': {"fa": "درایو سرعت متغیر", "en": "Variable Speed Drive"},
    'SV': {"fa": "شیر برقی قطع-وصل", "en": "Solenoid Valve"},
    'FC': {"fa": "فن کویل", "en": "Fancoil"},
    'LIG': {"fa": "خط روشنایی", "en": "Lighting"},
    'Knob': {"fa": "تنظیم دما دیواری", "en": "Setpoint Knob"},
    'FA': {"fa": "وضعیت خطا", "en": "Fault Status"},
    'FE': {"fa": "وضعیت روشن", "en": "Run Status"},
    'SLE': {"fa": "وضعیت سلکتور", "en": 'Local/Remote Status'},
    'CMD': {'fa': 'شروع/توقف فرمان', 'en': 'Start/Stop Command'},
    'SPR': {'fa': 'رزرو', 'en': 'Reserve'},
    'MOD': {'fa': 'مدباس', 'en': 'Modbus'},
    'MOV': {"fa": "شیر موتوری", "en": "Motorize Valve"},
    'SOU': {"fa": "صدا سنج", "en": "Sound Meter"},
    'LUX': {"fa": "نور سنج", "en": "Lux Meter"},
    'VIB': {"fa": "لرزش سنج", "en": "Vibration Sensor"},
    'BUZ': {"fa": "زنگ خطر", "en": "Buzzer Alarm"},
    'HMI': {"fa": "پنل اپراتور", "en": "HMI Panel"},
    'FCV': {"fa": "شیر کنترل فن‌کویل", "en": "Fancoil Control Valve"},
}

STATUS_KEYS = ['FA', 'FE', 'SLE', 'CMD']
COMMAND_KEYS = ['CMD']
RESERVED_KEYS = ['SPR', 'MOD']
EQUIPMENT_KEYS = ['PU', 'VSD', 'LIG', 'FC']

EXCLUDED_FROM_COMPONENTS = (
    STATUS_KEYS + COMMAND_KEYS + RESERVED_KEYS + EQUIPMENT_KEYS
)

COMPONENT_TYPES = {
    'PU': {'type': 'equipment', 'io_type': 'DI/DO'},
    'DTS': {'type': 'sensor', 'io_type': 'AI'},
    'ITS': {'type': 'sensor', 'io_type': 'AI'},
    'RTS': {'type': 'sensor', 'io_type': 'AI'},
    'DTHS': {'type': 'sensor', 'io_type': 'AI'},
    'RTHS': {'type': 'sensor', 'io_type': 'AI'},
    'AVS': {'type': 'sensor', 'io_type': 'AI'},
    'FS': {'type': 'sensor', 'io_type': 'DI'},
    'PS': {'type': 'sensor', 'io_type': 'DI'},
    'PT': {'type': 'sensor', 'io_type': 'AI'},
    'DPT': {'type': 'sensor', 'io_type': 'AI'},
    'VA': {'type': 'actuator', 'io_type': 'AI/AO'},
    'DAM_T1': {'type': 'actuator', 'io_type': 'DO'},
    'DAM_T2': {'type': 'actuator', 'io_type': 'DO'},
    'DAM_T3': {'type': 'actuator', 'io_type': 'AI/AO'},
    'DAM_T4': {'type': 'actuator', 'io_type': 'AI/AO'},
    'VSD': {'type': 'equipment', 'io_type': 'AI/AO'},
    'SV': {'type': 'actuator', 'io_type': 'DO'},
    'FC': {'type': 'equipment', 'io_type': 'DO'},
    'LIG': {'type': 'equipment', 'io_type': 'DI/DO'},
    'FR': {'type': 'sensor', 'io_type': 'DI'},
    'AQ': {'type': 'sensor', 'io_type': 'AI'},
    'SD': {'type': 'sensor', 'io_type': 'DI'},
    'LS': {'type': 'sensor', 'io_type': 'DI'},
    'LT': {'type': 'sensor', 'io_type': 'AI'},
    'FA': {'type': 'status', 'io_type': 'DI'},
    'FE': {'type': 'status', 'io_type': 'DI'},
    'SLE': {'type': 'status', 'io_type': 'DI'},
    'CMD': {'type': 'Command', 'io_type': 'DO'},
    'SPR': {'type': 'Command', 'io_type': 'DI/DO/AI/AO'},
    'MOD': {'type': 'equipment', 'io_type': ''},
    'MOV': {'type': 'actuator', 'io_type': 'DI/DO'},
    'SOU': {'type': 'sensor', 'io_type': 'AI'},
    'LUX': {'type': 'sensor', 'io_type': 'AI'},
    'VIB': {'type': 'sensor', 'io_type': 'AI'},
    'BUZ': {'type': 'sensor', 'io_type': 'DO'},
    'HMI': {'type': 'controller', 'io_type': ''},
    'FCV': {'type': 'actuator', 'io_type': 'DO'},
}

# ==================== نام‌های همنام برای سازگاری ====================
COMPONENT_LABELS_FA = {k: v['fa'] for k, v in COMPONENT_LABELS.items()}
COMPONENT_LABELS_EN = {k: v['en'] for k, v in COMPONENT_LABELS.items()}

# ==================== محاسبه I/O ====================
IO_CALCULATION: Dict[str, Dict[str, int]] = {
    'FS': {"DI": 1, "DO": 0, "AI": 0, "AO": 0},
    'DTS': {"DI": 0, "DO": 0, "AI": 1, "AO": 0},
    'ITS': {"DI": 0, "DO": 0, "AI": 1, "AO": 0},
    'DTHS': {"DI": 0, "DO": 0, "AI": 2, "AO": 0},
    'FR': {"DI": 1, "DO": 0, "AI": 0, "AO": 0},
    'AQ': {"DI": 0, "DO": 0, "AI": 1, "AO": 0},
    'DAM_T1': {"DI": 0, "DO": 1, "AI": 0, "AO": 0},
    'DAM_T2': {"DI": 0, "DO": 1, "AI": 0, "AO": 0},
    'DAM_T3': {"DI": 0, "DO": 0, "AI": 1, "AO": 1},
    'DAM_T4': {"DI": 0, "DO": 0, "AI": 1, "AO": 1},
    'RTS': {"DI": 0, "DO": 0, "AI": 1, "AO": 0},
    'RTHS': {"DI": 0, "DO": 0, "AI": 2, "AO": 0},
    'SD': {"DI": 1, "DO": 0, "AI": 0, "AO": 0},
    'AVS': {"DI": 0, "DO": 0, "AI": 1, "AO": 0},
    'VA': {"DI": 0, "DO": 0, "AI": 1, "AO": 1},
    'LS': {"DI": 1, "DO": 0, "AI": 0, "AO": 0},
    'LT': {"DI": 0, "DO": 0, "AI": 1, "AO": 0},
    'PS': {"DI": 1, "DO": 0, "AI": 0, "AO": 0},
    'PT': {"DI": 0, "DO": 0, "AI": 1, "AO": 0},
    'DPT': {"DI": 0, "DO": 0, "AI": 1, "AO": 0},
    'DPS': {"DI": 1, "DO": 0, "AI": 0, "AO": 0},
    'PU': {"DI": 3, "DO": 1, "AI": 0, "AO": 0},
    'VSD': {"DI": 0, "DO": 0, "AI": 1, "AO": 1},
    'SV': {"DI": 0, "DO": 1, "AI": 0, "AO": 0},
    'FC': {"DI": 0, "DO": 3, "AI": 0, "AO": 0},
    'LIG': {"DI": 2, "DO": 1, "AI": 0, "AO": 0},
    'Knob': {"DI": 0, "DO": 0, "AI": 1, "AO": 0},
    'FA': {"DI": 1, "DO": 0, "AI": 0, "AO": 0},
    'FE': {"DI": 1, "DO": 0, "AI": 0, "AO": 0},
    'SLE': {"DI": 1, "DO": 0, "AI": 0, "AO": 0},
    'CMD': {"DI": 0, "DO": 1, "AI": 0, "AO": 0},
    'SPR': {"DI": 1, "DO": 1, "AI": 1, "AO": 1},
    'MOD': {"DI": 0, "DO": 0, "AI": 0, "AO": 0},
    'MOV': {"DI": 2, "DO": 2, "AI": 0, "AO": 0},
    'SOU': {"DI": 0, "DO": 0, "AI": 1, "AO": 0},
    'LUX': {"DI": 0, "DO": 0, "AI": 1, "AO": 0},
    'VIB': {"DI": 0, "DO": 0, "AI": 1, "AO": 0},
    'BUZ': {"DI": 0, "DO": 1, "AI": 0, "AO": 0},
    'HMI': {"DI": 0, "DO": 0, "AI": 0, "AO": 0},
    'FCV': {"DI": 0, "DO": 1, "AI": 0, "AO": 0},
}

DEFAULT_IO_CONFIG = IO_CALCULATION

# ==================== اندازه کابل ====================
CABLE_SIZE: Dict[str, str] = {
    'FS': "2x1mm²", 'DTS': "2x1mm²", 'ITS': "2x1mm²", 'DTHS': "4x1mm²",
    'FR': "2x1mm²", 'AQ': "4x1mm²",
    'DAM_T1': "2x1mm²", 'DAM_T2': "2x1mm²",
    'DAM_T3': "4x1mm²", 'DAM_T4': "4x1mm²",
    'RTS': "2x1mm²", 'RTHS': "5x1mm²", 'SD': "4x1mm²", 'AVS': "4x1mm²",
    'VA': "4x1mm²", 'LS': "2x1mm²", 'LT': "4x1mm²", 'PS': "2x1mm²",
    'PT': "2x1mm²", 'DPT': "4x1mm²", 'DPS': "2x1mm²", 'PU': "6x1mm²",
    'VSD': "4x1mm²", 'SV': "2x1mm²", 'FC': "5x1mm²", 'LIG': "4x1mm²",
    'Knob': "4x1mm²", 'CMD': "2x1mm²", 'FA': "2x1mm²", 'FE': "2x1mm²",
    'SLE': "2x1mm²", 'MOD': "3x1mm²", 'MOV': "4x(2x1mm²)", 'SOU': "4x1mm²",
    'LUX': "4x1mm²", 'VIB': "4x1mm²", 'BUZ': "2x1mm²", 'HMI': "5x1mm²",
    'FCV': "2x1mm²"
}

CABLE_SIZE_MAP = CABLE_SIZE

# ==================== بخش‌های پیش‌فرض ====================
DEFAULT_SECTIONS = [
    ("Mechanical Room", " موتورخانه  "),
    ("AHU", "هوارسانها   "),
    ("Fancoil", "فن‌کویل‌ها   "),
    ("Exhaust Fan", "اگزاست فن‌ها"),
    ("Lighting", "سیستم روشنایی   ")
]

# ==================== ستون‌های جدول ====================
TABLE_COLUMNS = [
    "No", "Name", "Description", "DI", "DO", "AI", "AO", "Total", "Device"
]

# ==================== تنظیمات خروجی ====================
EXPORT = {
    'pdf_page_size': 'A4',
    'pdf_orientation': 'landscape',
    'excel_auto_open': True,
    'include_images': False
}

# ==================== لیست کامپوننت‌ها ====================
COMPONENT_KEYS = list(COMPONENT_LABELS.keys())
COMPONENT_FIELDS = COMPONENT_KEYS


# ==================== راهنمای I/O ====================
IO_REFERENCE = {
    'PU': {
        'label': 'Motor',
        'di': ['Selector (Local/Remote)', 'Fault (Alarm)', 'Feedback (Running Status)'],
        'do': ['Command (Start/Stop)'],
        'ai': [],
        'ao': []
    },
    'VSD': {
        'label': 'Variable Speed Drive',
        'di': [], 'do': [],
        'ai': ['Speed Feedback (0-10V / 4-20mA)'],
        'ao': ['Speed Command (0-10V / 4-20mA)']
    },
    'DTHS': {
        'label': 'Duct Temp & Humidity',
        'di': [], 'do': [],
        'ai': ['Temperature', 'Humidity'],
        'ao': []
    },
    'RTHS': {
        'label': 'Room Temp & Humidity',
        'di': [], 'do': [],
        'ai': ['Temperature', 'Humidity'],
        'ao': []
    },
    'RTS': {
        'label': 'Room Temperature Sensor',
        'di': [], 'do': [],
        'ai': ['Temperature'],
        'ao': []
    },
    'DTS': {
        'label': 'Duct Temperature Sensor',
        'di': [], 'do': [],
        'ai': ['Temperature'],
        'ao': []
    },
    'ITS': {
        'label': 'Immersion Temperature Sensor',
        'di': [], 'do': [],
        'ai': ['Temperature'],
        'ao': []
    },
    'FC': {
        'label': 'Fancoil',
        'di': [],
        'do': ['Command (Low Speed)', 'Command (Medium Speed)', 'Command (High Speed)'],
        'ai': [], 'ao': []
    },
    'LIG': {
        'label': 'Lighting',
        'di': ['Remote (On/Off)', 'Feedback (Status)'],
        'do': ['Command (On/Off)'],
        'ai': [], 'ao': []
    },
    'VA': {
        'label': 'Valve Actuator',
        'di': [], 'do': [],
        'ai': ['Position Feedback (0-10V)'],
        'ao': ['Position Command (0-10V)']
    },
    'FS': {
        'label': 'Flow Switch',
        'di': ['Flow Status (No Flow/Flow)'],
        'do': [], 'ai': [], 'ao': []
    },
    'DAM_T1': {
        'label': 'ON/OFF Damper  With Spring',
        'di': [],
        'do': ['Command (Open/Close)'],
        'ai': [], 'ao': []
    },
    'DAM_T2': {
        'label': 'ON/OFF Damper  Without Spring',
        'di': [],
        'do': ['Command (Open/Close)'],
        'ai': [], 'ao': []
    },
    'DAM_T3': {
        'label': 'Modulating Damper  With Spring',
        'di': [], 'do': [],
        'ai': ['Position Feedback (0-10V / 4-20mA)'],
        'ao': ['Position Command (0-10V / 4-20mA)']
    },
    'DAM_T4': {
        'label': 'Modulating Damper  Without Spring',
        'di': [], 'do': [],
        'ai': ['Position Feedback (0-10V / 4-20mA)'],
        'ao': ['Position Command (0-10V / 4-20mA)']
    },
    'PT': {
        'label': 'Pressure Transmitter',
        'di': [], 'do': [],
        'ai': ['Pressure (4-20mA)'],
        'ao': []
    },
    'DPT': {
        'label': 'Diff. Pressure Transmitter',
        'di': [], 'do': [],
        'ai': ['Differential Pressure (4-20mA)'],
        'ao': []
    },
    'DPS': {
        'label': 'Differential Pressure Switch',
        'di': ['Pressure Status'],
        'do': [], 'ai': [], 'ao': []
    },
    'PS': {
        'label': 'Pressure Switch',
        'di': ['Pressure Status'],
        'do': [], 'ai': [], 'ao': []
    },
    'SV': {
        'label': 'Solenoid Valve',
        'di': ['Feedback (Open)', 'Feedback (Close)'],
        'do': ['Command (Open/Close)'],
        'ai': [], 'ao': []
    },
    'AQ': {
        'label': 'Air Quality Sensor',
        'di': [], 'do': [],
        'ai': ['Air Quality (CO2/VOC)'],
        'ao': []
    },
    'SD': {
        'label': 'Smoke Detector',
        'di': ['Alarm Status'],
        'do': [], 'ai': [], 'ao': []
    },
    'FR': {
        'label': 'Freeze Protection',
        'di': ['Freeze Status'],
        'do': [], 'ai': [], 'ao': []
    },
    'LS': {
        'label': 'Level Switch',
        'di': ['Level Status (High/Low)'],
        'do': [], 'ai': [], 'ao': []
    },
    'LT': {
        'label': 'Level Transmitter',
        'di': [], 'do': [],
        'ai': ['Level (4-20mA)'],
        'ao': []
    },
    'AVS': {
        'label': 'Air Velocity Sensor',
        'di': [], 'do': [],
        'ai': ['Air Velocity'],
        'ao': []
    },
    'Knob': {
        'label': 'Setpoint Knob',
        'di': [], 'do': [],
        'ai': ['Setpoint (0-10V)'],
        'ao': []
    },
    'FA': {
        'label': 'Fault Status',
        'di': ['Fault Status'],
        'do': [], 'ai': [], 'ao': []
    },
    'FE': {
        'label': 'Run Status',
        'di': ['Run Status'],
        'do': [], 'ai': [], 'ao': []
    },
    'SLE': {
        'label': 'Slector Status',
        'di': ['Local/Remote Status'],
        'do': [], 'ai': [], 'ao': []
    },
    'CMD': {
        'label': 'Start/Stop Command',
        'di': [],
        'do': ['Command (Start/Stop)'],
        'ai': [], 'ao': []
    },
    'SPR': {
        'label': 'Reserve IO',
        'di': ['Spare'],
        'do': ['Spare'],
        'ai': ['Spare'],
        'ao': ['Spare']
    },
    'MOD': {
        'label': 'Modbus',
        'di': [], 'do': [], 'ai': [], 'ao': []
    },
    'MOV': {
        'label': 'Motorize Valve',
        'di': ['Close Limit', 'Open Limit'],
        'do': ['Close CMD', 'Open CMD'],
        'ai': [], 'ao': []
    },
    'SOU': {
        'label': 'Sound Meter',
        'di': [], 'do': [],
        'ai': ['Sound Meter (4-20 mA)'],
        'ao': []
    },
    'LUX': {
        'label': 'Lux Meter',
        'di': [], 'do': [],
        'ai': ['LUX Meter (4-20 mA)'],
        'ao': []
    },
    'VIB': {
        'label': 'Vibration Sensor',
        'di': [], 'do': [],
        'ai': ['Vibration Meter (4-20 mA)'],
        'ao': []
    },
    'BUZ': {
        'label': 'Buzzer',
        'di': [],
        'do': ['Buzzer Alarm'],
        'ai': [], 'ao': []
    },
    'HMI': {
        'label': 'HMI Panel',
        'di': [], 'do': [], 'ai': [], 'ao': []
    },
    'FCV': {
        'label': 'Fancoil Control Valve',
        'di': [],
        'do': ['Command (Open/Close)'],
        'ai': [], 'ao': []
    },
}

# ==================== صادرات ====================
__all__ = [
    'APP_ROOT',
    'APP_DATA_PATH',
    'OLD_APP_DATA_PATH',
    'DEFAULT_DB_PATH',
    'ICON_PATH',
    'DEFAULT_API_KEY',
    'DEEPSEEK_API_URL',
    'WINDOW',
    'LIMITS',
    'COLORS',
    'COMPONENT_LABELS',
    'COMPONENT_LABELS_FA',
    'COMPONENT_LABELS_EN',
    'IO_CALCULATION',
    'DEFAULT_IO_CONFIG',
    'CABLE_SIZE',
    'CABLE_SIZE_MAP',
    'DEFAULT_SECTIONS',
    'TABLE_COLUMNS',
    'EXPORT',
    'COMPONENT_KEYS',
    'COMPONENT_FIELDS',
    'IO_REFERENCE',
    'STATUS_KEYS',
    'COMMAND_KEYS',
    'RESERVED_KEYS',
    'EXCLUDED_FROM_COMPONENTS',
    'COMPONENT_TYPES',
    'get_timestamp_for_filename',
    'gregorian_to_jalali',
    'validate_device_name',
    'validate_io_value',
]