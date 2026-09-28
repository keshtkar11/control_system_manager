r"""
مسیرهای برنامه — مدیریت تفکیک منابع و داده‌های نوشتنی

معماری:
- منابع فقط-خواندنی: در EXE از sys._MEIPASS خوانده می‌شوند
- داده‌های نوشتنی (Database, Logs, Config): با اولویت‌بندی زیر
    1. Environment Variable: CSM_DATA_DIR
    2. Config در کنار EXE/پروژه: app_config.json → data_dir
    3. D:\BMS Projects\IO_List_Generator (اگر D: وجود داشت)
    4. %APPDATA%\ControlSystemManager (EXE)
    5. <project_root>/data (Development)

⚠️ این فایل تنها منبع تعیین مسیر داده‌هاست.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional


# ================================================================
# 1. APP INFO
# ================================================================

APP_NAME = "ControlSystemManager"
APP_AUTHOR = "VahhajSanat"

# مسیر پیش‌فرض در D:
DEFAULT_DATA_DIR_D = Path(r"D:\BMS Projects\IO_List_Generator")

# فایل config کاربر (کنار EXE یا پروژه)
APP_CONFIG_FILE = "app_config.json"


# ================================================================
# 2. BUNDLE ROOT (منابع فقط-خواندنی)
# ================================================================

def get_bundle_root() -> Path:
    """
    مسیر ریشه منابع همراه برنامه (فقط-خواندنی).
    
    در EXE: پوشه موقت sys._MEIPASS
    در Python: ریشه پروژه
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS).resolve()
    
    return Path(__file__).resolve().parents[1]


def get_resource_path(*parts: str) -> Path:
    """
    مسیر فایل‌های همراه برنامه (فقط-خواندنی).
    
    مثال:
        get_resource_path("ai", "proposal_images", "boiler.png")
        get_resource_path("resources", "fonts", "BNazanin.ttf")
    """
    return get_bundle_root().joinpath(*parts)


# ================================================================
# 3. APP CONFIG (تنظیمات مسیر داده)
# ================================================================

def get_app_config_path() -> Path:
    """
    مسیر فایل تنظیمات اصلی برنامه (app_config.json).
    
    کنار EXE یا ریشه پروژه.
    """
    return get_bundle_root() / APP_CONFIG_FILE


def _load_app_config() -> dict:
    """
    بارگذاری app_config.json (اگر وجود دارد).
    
    فرمت:
        {
            "data_dir": "E:\\MyCustomPath",
            "language": "fa"
        }
    """
    config_path = get_app_config_path()
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


# ================================================================
# 4. USER DATA DIR (داده‌های نوشتنی)
# ================================================================

def get_user_data_dir() -> Path:
    r"""
    مسیر ذخیره‌سازی داده‌های کاربر (نوشتنی).
    
    اولویت (به ترتیب):
    1. Environment Variable: CSM_DATA_DIR
    2. app_config.json → data_dir
    3. D:\BMS Projects\IO_List_Generator (اگر D: موجود)
    4. %APPDATA%\ControlSystemManager (EXE)
    5. <project_root>/data (Development)
    
    ⚠️ این تابع منبع اصلی است. تمام توابع دیگر از این استفاده می‌کنند.
    """
    path = None
    
    # ============================================================
    # اولویت 1: Environment Variable
    # ============================================================
    env_dir = os.environ.get("CSM_DATA_DIR")
    if env_dir:
        try:
            path = Path(env_dir).resolve()
        except Exception:
            path = None
    
    # ============================================================
    # اولویت 2: app_config.json
    # ============================================================
    if not path:
        app_config = _load_app_config()
        config_dir = app_config.get("data_dir")
        if config_dir:
            try:
                path = Path(config_dir).resolve()
            except Exception:
                path = None
    
    # ============================================================
    # اولویت 3: D:\ (اگر وجود داشت)
    # ============================================================
    if not path and os.path.exists("D:\\"):
        path = DEFAULT_DATA_DIR_D
    
    # ============================================================
    # اولویت 4: EXE → %APPDATA%
    # ============================================================
    if not path and getattr(sys, "frozen", False):
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        path = base / APP_NAME
    
    # ============================================================
    # اولویت 5: Development
    # ============================================================
    if not path:
        path = Path(__file__).resolve().parents[1] / "data"
    
    # ============================================================
    # ساخت پوشه
    # ============================================================
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        # fallback به %APPDATA%
        fallback = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
        fallback.mkdir(parents=True, exist_ok=True)
        path = fallback
    
    return path


# ================================================================
# 5. DATABASE PATH
# ================================================================

def get_database_path() -> Path:
    """
    مسیر دیتابیس اصلی (نوشتنی).
    
    ⚠️ هرگز از get_resource_path برای دیتابیس استفاده نکنید!
    """
    return get_user_data_dir() / "IO_List_Generator.db"


# ================================================================
# 6. LOGS / CONFIG / OUTPUT DIRS
# ================================================================

def get_logs_dir() -> Path:
    """مسیر پوشه logs (نوشتنی)"""
    logs_dir = get_user_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_config_dir() -> Path:
    """مسیر پوشه config (نوشتنی)"""
    config_dir = get_user_data_dir() / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_output_dir() -> Path:
    """مسیر پیش‌فرض خروجی‌های کاربر (Reports, Proposals و ...)"""
    output_dir = get_user_data_dir() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_backups_dir() -> Path:
    """مسیر پوشه Backups (نوشتنی)"""
    backups_dir = get_user_data_dir() / "Backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    return backups_dir


def get_project_backups_dir() -> Path:
    """مسیر پوشه Project_Backups (نوشتنی)"""
    proj_backups_dir = get_user_data_dir() / "Project_Backups"
    proj_backups_dir.mkdir(parents=True, exist_ok=True)
    return proj_backups_dir


def get_attachments_dir() -> Path:
    """مسیر پوشه Attachments (نوشتنی)"""
    attachments_dir = get_user_data_dir() / "Attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)
    return attachments_dir


# ================================================================
# 7. HELPERS
# ================================================================

def is_frozen() -> bool:
    """آیا برنامه در حالت EXE اجرا می‌شود؟"""
    return getattr(sys, "frozen", False)


def get_app_root() -> Path:
    """
    ریشه پروژه (حالت توسعه) یا پوشه EXE (حالت frozen).
    """
    if is_frozen():
        return Path(sys.executable).parent.resolve()
    return Path(__file__).resolve().parents[1]


def get_data_dir_info() -> dict:
    """
    اطلاعات کامل مسیرهای داده (برای Debug).
    
    Returns:
        {
            'user_data_dir': str,
            'database': str,
            'backups': str,
            'config': str,
            'logs': str,
            'attachments': str,
            'source': str,   # از کدام اولویت انتخاب شد
        }
    """
    data_dir = get_user_data_dir()
    
    # تشخیص منبع
    source = "unknown"
    if os.environ.get("CSM_DATA_DIR"):
        source = "env:CSM_DATA_DIR"
    elif _load_app_config().get("data_dir"):
        source = "app_config.json"
    elif os.path.exists("D:\\") and data_dir == DEFAULT_DATA_DIR_D:
        source = "D_drive_default"
    elif is_frozen():
        source = "%APPDATA%"
    else:
        source = "development"
    
    return {
        'user_data_dir': str(data_dir),
        'database': str(get_database_path()),
        'backups': str(get_backups_dir()),
        'config': str(get_config_dir()),
        'logs': str(get_logs_dir()),
        'attachments': str(get_attachments_dir()),
        'source': source,
    }


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'APP_NAME',
    'APP_AUTHOR',
    'get_bundle_root',
    'get_resource_path',
    'get_user_data_dir',
    'get_database_path',
    'get_logs_dir',
    'get_config_dir',
    'get_output_dir',
    'get_backups_dir',
    'get_project_backups_dir',
    'get_attachments_dir',
    'is_frozen',
    'get_app_root',
    'get_data_dir_info',
]