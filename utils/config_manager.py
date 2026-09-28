# utils/config_manager.py
"""
مدیریت تنظیمات برنامه — خواندن/نوشتن config.json

نسخه 2.0 — سازگار با utils.paths
- استفاده از get_config_dir() برای ذخیره‌سازی
- کاملاً سازگار با EXE و Development
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from utils.paths import get_config_dir

logger = logging.getLogger(__name__)


# ================================================================
# DEFAULT CONFIG
# ================================================================

DEFAULT_CONFIG = {
    # ===== API =====
    'api_key': '',
    'base_url': 'https://codecraftapi.com/v1',
    'model': 'claude-opus-4.8',
    'timeout': 120.0,
    'temperature': 0.7,
    'max_tokens': 8000,
    
    # ===== AI Behavior =====
    'enable_ai_chat': True,
    'enable_ai_proposal': True,
    'language': 'fa',
    
    # ===== UI =====
    'last_window_geometry': '900x650',
}


# ================================================================
# CONFIG MANAGER
# ================================================================

class ConfigManager:
    """
    مدیریت تنظیمات — singleton
    
    Usage:
        config = ConfigManager()
        api_key = config.get('api_key')
        config.set('api_key', 'new_key')
        config.save()
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._config_path = self._get_config_path()
        self._data: Dict[str, Any] = {}
        self._load()
    
    # ============================================================
    # PATH
    # ============================================================
    
    def _get_config_path(self) -> Path:
        """
        مسیر فایل config.json
        
        اولویت:
        1. پوشه config در user_data_dir (پیش‌فرض)
        2. پوشه کاربر (fallback)
        """
        try:
            config_dir = get_config_dir()
            return config_dir / "config.json"
        except Exception as e:
            logger.warning(f"Could not get config dir: {e}")
            # fallback
            return Path.home() / ".control_system_manager" / "config.json"
    
    @property
    def config_path(self) -> Path:
        return self._config_path
    
    # ============================================================
    # LOAD / SAVE
    # ============================================================
    
    def _load(self):
        """بارگذاری از فایل"""
        self._data = dict(DEFAULT_CONFIG)
        
        # ===== 1. از فایل =====
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # Merge با default
                for key, value in user_config.items():
                    self._data[key] = value
                
                logger.info(f"✅ Config loaded: {self._config_path}")
            except Exception as e:
                logger.error(f"❌ Could not load config: {e}")
        else:
            logger.info(
                f"ℹ️ Config file not found, using defaults: {self._config_path}"
            )
        
        # ===== 2. از Environment Variables (override) =====
        env_mappings = {
            'CODECRAFT_API_KEY': 'api_key',
            'CODECRAFT_BASE_URL': 'base_url',
            'CODECRAFT_MODEL': 'model',
        }
        
        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value:
                self._data[config_key] = env_value
                logger.info(f"✅ Env override: {env_key}")
    
    def save(self) -> bool:
        """ذخیره در فایل"""
        try:
            # ===== ساخت پوشه =====
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # ===== نوشتن =====
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(
                    self._data,
                    f,
                    indent=4,
                    ensure_ascii=False,
                )
            
            logger.info(f"✅ Config saved: {self._config_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Could not save config: {e}")
            return False
    
    def reload(self):
        """بارگذاری مجدد از فایل"""
        self._load()
    
    def reset_to_defaults(self) -> bool:
        """بازگشت به مقادیر پیش‌فرض"""
        self._data = dict(DEFAULT_CONFIG)
        return self.save()
    
    # ============================================================
    # GET / SET
    # ============================================================
    
    def get(self, key: str, default: Any = None) -> Any:
        """دریافت مقدار"""
        if key in self._data:
            return self._data[key]
        if default is not None:
            return default
        return DEFAULT_CONFIG.get(key)
    
    def set(self, key: str, value: Any):
        """تنظیم مقدار"""
        self._data[key] = value
    
    def update(self, data: Dict[str, Any]):
        """بروزرسانی چند مقدار"""
        self._data.update(data)
    
    def get_all(self) -> Dict[str, Any]:
        """دریافت همه"""
        return dict(self._data)
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    def validate(self) -> Dict[str, str]:
        """
        اعتبارسنجی تنظیمات
        
        Returns:
            dict: {field: error_message} — خالی اگر معتبر
        """
        errors = {}
        
        # API Key
        api_key = (self.get('api_key', '') or '').strip()
        if not api_key:
            errors['api_key'] = 'API Key خالی است'
        elif len(api_key) < 20:
            errors['api_key'] = 'API Key خیلی کوتاه است'
        
        # Base URL
        base_url = (self.get('base_url', '') or '').strip()
        if not base_url:
            errors['base_url'] = 'Base URL خالی است'
        elif not base_url.startswith(('http://', 'https://')):
            errors['base_url'] = 'Base URL باید با http:// یا https:// شروع شود'
        
        # Model
        model = (self.get('model', '') or '').strip()
        if not model:
            errors['model'] = 'Model انتخاب نشده'
        
        # Timeout
        try:
            timeout = float(self.get('timeout', 0))
            if timeout < 10 or timeout > 600:
                errors['timeout'] = 'Timeout باید بین 10 تا 600 ثانیه باشد'
        except (ValueError, TypeError):
            errors['timeout'] = 'Timeout باید عدد باشد'
        
        # Temperature
        try:
            temp = float(self.get('temperature', 0))
            if temp < 0 or temp > 2:
                errors['temperature'] = 'Temperature باید بین 0 تا 2 باشد'
        except (ValueError, TypeError):
            errors['temperature'] = 'Temperature باید عدد باشد'
        
        return errors
    
    def is_configured(self) -> bool:
        """آیا تنظیمات کامل است؟"""
        return len(self.validate()) == 0


# ================================================================
# SINGLETON GETTER
# ================================================================

_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """دریافت نمونه singleton"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['ConfigManager', 'get_config', 'DEFAULT_CONFIG']