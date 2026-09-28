# gui/theme/theme_manager.py
"""
مدیریت تم - Dark/Light Switch
"""

import json
import os
from tkinter import ttk
from typing import Optional, Dict

from .colors import (
    DARK_COLORS, LIGHT_COLORS,
    CURRENT_COLORS, set_theme_colors, get_color
)
from .typography import TEXT_STYLES, get_font_tuple
from .spacing import (
    SPACING, PADDING, HEIGHTS, WIDTHS, RADIUS
)


class ThemeManager:
    """
    مدیریت تم برنامه
    - Dark/Light Mode
    - ذخیره انتخاب کاربر
    - تغییر آنی
    """
    
    THEME_FILE = os.path.join(
        os.environ.get('APPDATA', os.path.expanduser('~')),
        'ControlSystemManager',
        'theme.json'
    )
    
    def __init__(self):
        self.current_theme = 'dark'  # پیش‌فرض
        self._load_theme_preference()
        self._apply_theme_to_colors()
    
    # ================================================================
    # LOAD / SAVE
    # ================================================================
    
    def _load_theme_preference(self):
        """بارگذاری تم ذخیره شده"""
        try:
            if os.path.exists(self.THEME_FILE):
                with open(self.THEME_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_theme = data.get('theme', 'dark')
        except Exception:
            self.current_theme = 'dark'
    
    def _save_theme_preference(self):
        """ذخیره انتخاب کاربر"""
        try:
            os.makedirs(os.path.dirname(self.THEME_FILE), exist_ok=True)
            with open(self.THEME_FILE, 'w', encoding='utf-8') as f:
                json.dump({'theme': self.current_theme}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _apply_theme_to_colors(self):
        """اعمال تم به رنگ‌های سراسری"""
        if self.current_theme == 'light':
            set_theme_colors(LIGHT_COLORS)
        else:
            set_theme_colors(DARK_COLORS)
    
    # ================================================================
    # THEME SWITCHING
    # ================================================================
    
    def set_theme(self, theme: str):
        """
        تنظیم تم
        
        Args:
            theme: 'dark' یا 'light'
        """
        if theme not in ('dark', 'light'):
            return
        
        self.current_theme = theme
        self._apply_theme_to_colors()
        self._save_theme_preference()
    
    def toggle_theme(self):
        """تغییر بین Dark و Light"""
        new_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.set_theme(new_theme)
        return new_theme
    
    def is_dark(self) -> bool:
        """آیا تم تیره فعال است؟"""
        return self.current_theme == 'dark'
    
    def is_light(self) -> bool:
        """آیا تم روشن فعال است؟"""
        return self.current_theme == 'light'
    
    # ================================================================
    # COLORS
    # ================================================================
    
    def get_color(self, key: str, default: str = '#000000') -> str:
        """دریافت رنگ از تم فعلی"""
        return get_color(key, default)
    
    @property
    def colors(self) -> dict:
        """دریافت پالت رنگ فعلی"""
        return CURRENT_COLORS
    
    # ================================================================
    # FONTS
    # ================================================================
    
    @staticmethod
    def get_font(style_name: str = 'body'):
        """دریافت tuple فونت"""
        return get_font_tuple(style_name)
    
    @staticmethod
    def font(style_name: str = 'body'):
        """میانبر برای get_font"""
        return get_font_tuple(style_name)


# ================================================================
# SINGLETON
# ================================================================

_theme_manager_instance: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """دریافت نمونه Singleton از ThemeManager"""
    global _theme_manager_instance
    if _theme_manager_instance is None:
        _theme_manager_instance = ThemeManager()
    return _theme_manager_instance


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'ThemeManager',
    'get_theme_manager',
]