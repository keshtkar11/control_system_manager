"""تنظیمات سیستم لاگینگ — منبع واحد"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path

# ✅ منبع واحد برای مسیر لاگ
from utils.paths import get_logs_dir


# ==================== تنظیمات پایه ====================

LOG_DIR = get_logs_dir()

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

MAX_LOG_SIZE = 10 * 1024 * 1024
BACKUP_COUNT = 5


# ==================== کلاس‌های سفارشی ====================

class ColoredFormatter(logging.Formatter):
    """فرمت‌دهی رنگی برای کنسول"""
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        log_msg = super().format(record)
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        return f"{color}{log_msg}{self.COLORS['RESET']}"


class ContextLogger:
    """لاگر با قابلیت زمینه (context)"""
    
    def __init__(self, name: str = "app"):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def set_context(self, **kwargs):
        self.context.update(kwargs)
    
    def clear_context(self):
        self.context.clear()
    
    def _format_message(self, message: str) -> str:
        if not self.context:
            return message
        context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
        return f"[{context_str}] {message}"
    
    def debug(self, message, *args, **kwargs):
        self.logger.debug(self._format_message(message), *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        self.logger.info(self._format_message(message), *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        self.logger.warning(self._format_message(message), *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        self.logger.error(self._format_message(message), *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        self.logger.critical(self._format_message(message), *args, **kwargs)
    
    def exception(self, message, *args, **kwargs):
        self.logger.exception(self._format_message(message), *args, **kwargs)


# ==================== Root Logger Setup (اول از همه) ====================

def _setup_root_logger():
    """
    تنظیم root logger — همه لاگ‌ها اینجا
    
    ✅ این تابع قبل از هر get_logger اجرا می‌شود.
    """
    root_logger = logging.getLogger()
    
    if root_logger.handlers:
        return
    
    root_logger.setLevel(logging.DEBUG)
    
    # ===== FileHandler =====
    try:
        file_handler = RotatingFileHandler(
            LOG_DIR / "control_system.log",
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"⚠️ Could not create file handler: {e}")
    
    # ===== ErrorFileHandler =====
    try:
        error_handler = RotatingFileHandler(
            LOG_DIR / "control_system_error.log",
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        root_logger.addHandler(error_handler)
    except Exception as e:
        print(f"⚠️ Could not create error handler: {e}")
    
    # ===== ConsoleHandler =====
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
        console_formatter = ColoredFormatter(LOG_FORMAT, LOG_DATE_FORMAT)
    else:
        console_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)


# ✅ اجرا — قبل از هر get_logger
_setup_root_logger()


# ==================== توابع اصلی ====================

def get_logger(name: str = "app", level: str = "INFO") -> logging.Logger:
    """
    دریافت یک لاگر
    
    ✅ جدید: هیچ handler اضافه نمی‌کند — از root استفاده می‌کند.
    (به همین دلیل propagate باید True باشد)
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
    logger.propagate = True      # ← به root propagate کن
    return logger


def get_context_logger(name: str = "app", level: str = "INFO") -> ContextLogger:
    """دریافت لاگر با قابلیت زمینه"""
    logger = get_logger(name, level)
    return ContextLogger(name)


def log_function_call(logger: logging.Logger = None):
    """دکوراتور برای ثبت ورود و خروج توابع"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger()
            
            func_name = func.__name__
            logger.debug(f"→ Entering {func_name}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"← Exiting {func_name}")
                return result
            except Exception as e:
                logger.error(f"✗ Error in {func_name}: {e}")
                raise
        
        return wrapper
    return decorator


def log_performance(logger: logging.Logger = None):
    """دکوراتور برای اندازه‌گیری زمان اجرا"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger()
            
            start = datetime.now()
            func_name = func.__name__
            
            result = func(*args, **kwargs)
            
            elapsed = (datetime.now() - start).total_seconds()
            logger.debug(f"⏱ {func_name} took {elapsed:.4f}s")
            
            return result
        return wrapper
    return decorator


# ==================== لاگرهای پیش‌فرض ====================

app_logger = get_logger("control_system")
context_logger = get_context_logger("control_system")


# ==================== توابع کمکی ====================

def set_global_log_level(level: str):
    """تنظیم سطح لاگ برای تمام لاگرها"""
    level_value = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    for name in logging.root.manager.loggerDict:
        logger = logging.getLogger(name)
        logger.setLevel(level_value)


def get_log_files() -> list:
    """دریافت لیست فایل‌های لاگ"""
    return sorted(LOG_DIR.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)


def clear_logs(days: int = 30):
    """پاک کردن فایل‌های لاگ قدیمی"""
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
    
    for log_file in LOG_DIR.glob("*.log*"):
        if log_file.stat().st_mtime < cutoff:
            try:
                log_file.unlink()
                app_logger.info(f"Removed old log file: {log_file.name}")
            except Exception as e:
                app_logger.error(f"Error removing {log_file.name}: {e}")


def get_log_stats() -> dict:
    """دریافت آمار فایل‌های لاگ"""
    stats = {'total_files': 0, 'total_size': 0, 'files': []}
    
    for log_file in LOG_DIR.glob("*.log*"):
        size = log_file.stat().st_size
        stats['total_files'] += 1
        stats['total_size'] += size
        stats['files'].append({
            'name': log_file.name,
            'size': size,
            'modified': datetime.fromtimestamp(log_file.stat().st_mtime)
        })
    
    stats['total_size_mb'] = round(stats['total_size'] / (1024 * 1024), 2)
    
    return stats


# ==================== لاگرهای مخصوص ====================

def get_db_logger():
    return get_logger("database")


def get_ai_logger():
    return get_logger("ai")


def get_gui_logger():
    return get_logger("gui")


def get_export_logger():
    return get_logger("export")


def get_core_logger():
    return get_logger("core")