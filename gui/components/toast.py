# gui/components/toast.py
"""
کامپوننت اعلان‌ها - Toast Notifications
"""

import tkinter as tk
from typing import Callable, List, Optional
from enum import Enum
import threading

from gui.theme import (
    get_color, font, sp, pad, radius, ico, h,
)


class ToastType(Enum):
    """نوع اعلان"""
    SUCCESS = 'success'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'


# ================================================================
# TOAST
# ================================================================

class Toast(tk.Toplevel):
    """
    اعلان Toast - پنجره کوچک شناور
    """
    
    _active_toasts: List['Toast'] = []
    
    def __init__(
        self,
        parent,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration: int = 3000,
        position: str = 'top-right',
        on_close: Callable = None,
    ):
        """
        Args:
            parent: والد
            message: متن پیام
            toast_type: نوع اعلان
            duration: مدت نمایش (ms)
            position: موقعیت
            on_close: تابع بستن
        """
        super().__init__(parent)
        
        self.message = message
        self.toast_type = toast_type
        self.duration = duration
        self.on_close = on_close
        
        # ===== تنظیمات پنجره =====
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        
        # ===== استایل =====
        self._build_ui()
        
        # ===== موقعیت =====
        self._position_window(parent, position)
        
        # ===== بستن خودکار =====
        self.after(duration, self._fade_out)
        
        # ===== اضافه به لیست =====
        Toast._active_toasts.append(self)
        
        # ===== فید این =====
        self._fade_in()
    
    def _build_ui(self):
        """ساخت UI"""
        # رنگ‌ها بر اساس نوع
        colors = {
            ToastType.SUCCESS: (get_color('success'), 'check_circle'),
            ToastType.ERROR:   (get_color('danger'), 'x_circle'),
            ToastType.WARNING: (get_color('warning'), 'warning_triangle'),
            ToastType.INFO:    (get_color('info'), 'info_circle'),
        }
        
        accent_color, icon_name = colors.get(
            self.toast_type,
            (get_color('info'), 'info_circle')
        )
        
        # ===== Frame اصلی =====
        main_frame = tk.Frame(
            self,
            bg=get_color('bg_surface_elevated'),
            highlightthickness=2,
            highlightbackground=accent_color,
        )
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== Content =====
        content = tk.Frame(main_frame, bg=get_color('bg_surface_elevated'))
        content.pack(fill=tk.BOTH, expand=True, padx=sp('lg'), pady=sp('md'))
        
        # ===== Icon =====
        tk.Label(
            content,
            text=ico(icon_name),
            font=('Segoe UI', 20),
            bg=get_color('bg_surface_elevated'),
            fg=accent_color,
        ).pack(side=tk.LEFT, padx=(0, sp('md')))
        
        # ===== Message =====
        text_frame = tk.Frame(content, bg=get_color('bg_surface_elevated'))
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            text_frame,
            text=self.toast_type.value.upper(),
            font=font('caption'),
            bg=get_color('bg_surface_elevated'),
            fg=accent_color,
            anchor='w',
        ).pack(fill=tk.X)
        
        tk.Label(
            text_frame,
            text=self.message,
            font=font('body'),
            bg=get_color('bg_surface_elevated'),
            fg=get_color('text_primary'),
            anchor='w',
            wraplength=300,
            justify='left',
        ).pack(fill=tk.X)
        
        # ===== Close Button =====
        close_btn = tk.Label(
            content,
            text=ico('close'),
            font=('Segoe UI', 10),
            bg=get_color('bg_surface_elevated'),
            fg=get_color('text_muted'),
            cursor='hand2',
        )
        close_btn.pack(side=tk.RIGHT, padx=(sp('sm'), 0))
        close_btn.bind('<Button-1>', lambda e: self._close())
        
        # تنظیم اندازه
        self.update_idletasks()
        self.configure(width=350)
    
    def _position_window(self, parent, position: str):
        """موقعیت‌دهی پنجره"""
        self.update_idletasks()
        
        # اندازه Toast
        w = 350
        h = self.winfo_reqheight()
        
        # صفحه
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        
        # فاصله از لبه‌ها
        margin = sp('xl')
        
        # محاسبه موقعیت
        if position == 'top-right':
            x = screen_w - w - margin
            y = margin + len(Toast._active_toasts) * (h + sp('sm'))
        elif position == 'top-left':
            x = margin
            y = margin + len(Toast._active_toasts) * (h + sp('sm'))
        elif position == 'bottom-right':
            x = screen_w - w - margin
            y = screen_h - h - margin - len(Toast._active_toasts) * (h + sp('sm'))
        elif position == 'bottom-left':
            x = margin
            y = screen_h - h - margin - len(Toast._active_toasts) * (h + sp('sm'))
        elif position == 'top-center':
            x = (screen_w - w) // 2
            y = margin + len(Toast._active_toasts) * (h + sp('sm'))
        elif position == 'bottom-center':
            x = (screen_w - w) // 2
            y = screen_h - h - margin - len(Toast._active_toasts) * (h + sp('sm'))
        else:  # default: top-right
            x = screen_w - w - margin
            y = margin
        
        self.geometry(f"{w}x{h}+{x}+{y}")
    
    def _fade_in(self):
        """انیمیشن ورود"""
        try:
            self.attributes('-alpha', 0.0)
            
            def animate(alpha=0.0):
                alpha += 0.1
                if alpha <= 1.0:
                    self.attributes('-alpha', alpha)
                    self.after(20, lambda: animate(alpha))
            
            animate()
        except:
            self.attributes('-alpha', 1.0)
    
    def _fade_out(self):
        """انیمیشن خروج"""
        try:
            def animate(alpha=1.0):
                alpha -= 0.1
                if alpha >= 0.0:
                    try:
                        self.attributes('-alpha', alpha)
                        self.after(20, lambda: animate(alpha))
                    except:
                        pass
                else:
                    self._close()
            
            animate()
        except:
            self._close()
    
    def _close(self):
        """بستن"""
        if self in Toast._active_toasts:
            Toast._active_toasts.remove(self)
        
        try:
            self.destroy()
        except:
            pass
        
        if self.on_close:
            self.on_close()


# ================================================================
# TOAST MANAGER
# ================================================================

class ToastManager:
    """
    مدیریت اعلان‌ها - Singleton
    """
    
    _instance = None
    _parent = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def set_parent(cls, parent):
        """تنظیم والد"""
        cls._parent = parent
    
    @classmethod
    def show(cls, message: str, toast_type: ToastType = ToastType.INFO,
             duration: int = 3000, position: str = 'top-right'):
        """
        نمایش Toast
        
        Args:
            message: متن پیام
            toast_type: نوع اعلان
            duration: مدت نمایش (ms)
            position: موقعیت
        """
        if not cls._parent:
            print(f"⚠️ Toast: {message}")
            return
        
        Toast(
            cls._parent,
            message=message,
            toast_type=toast_type,
            duration=duration,
            position=position,
        )
    
    @classmethod
    def success(cls, message: str, duration: int = 3000):
        """نمایش پیام موفقیت"""
        cls.show(message, ToastType.SUCCESS, duration)
    
    @classmethod
    def error(cls, message: str, duration: int = 4000):
        """نمایش پیام خطا"""
        cls.show(message, ToastType.ERROR, duration)
    
    @classmethod
    def warning(cls, message: str, duration: int = 3500):
        """نمایش پیام هشدار"""
        cls.show(message, ToastType.WARNING, duration)
    
    @classmethod
    def info(cls, message: str, duration: int = 3000):
        """نمایش پیام اطلاعات"""
        cls.show(message, ToastType.INFO, duration)


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def toast(parent, message: str, toast_type: str = 'info', duration: int = 3000):
    """
    نمایش Toast سریع
    
    Args:
        parent: والد
        message: پیام
        toast_type: 'success', 'error', 'warning', 'info'
        duration: مدت (ms)
    """
    type_map = {
        'success': ToastType.SUCCESS,
        'error': ToastType.ERROR,
        'warning': ToastType.WARNING,
        'info': ToastType.INFO,
    }
    
    toast_type_enum = type_map.get(toast_type, ToastType.INFO)
    
    Toast(parent, message, toast_type_enum, duration)


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'Toast',
    'ToastType',
    'ToastManager',
    'toast',
]