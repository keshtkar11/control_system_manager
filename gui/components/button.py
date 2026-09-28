# gui/components/button.py
"""
کامپوننت دکمه‌های سفارشی
"""

import tkinter as tk
from typing import Callable, Optional

from gui.theme import (
    get_color, font, sp, pad,
    ico, icon_with_text,
    create_tooltip,
    _lighten_color, _darken_color,
)


# ================================================================
# BASE BUTTON
# ================================================================

class BaseButton(tk.Frame):
    """
    دکمه پایه با قابلیت‌های hover و states
    """
    
    def __init__(
        self,
        parent,
        text: str = "",
        icon: str = None,
        command: Callable = None,
        width: int = None,
        height: int = None,
        tooltip: str = None,
        **kwargs
    ):
        """
        Args:
            parent: والد
            text: متن دکمه
            icon: نام آیکون (اختیاری)
            command: تابع کلیک
            width: عرض
            height: ارتفاع
            tooltip: متن راهنما
        """
        self.parent = parent
        self.command = command
        self._text = text
        self._icon = icon
        self._enabled = True
        
        # Frame والد
        # Frame والد
        super().__init__(parent, bg=get_color('bg_app'), **kwargs)
        
        # ===== Label داخلی =====
        display_text = self._build_text()
        
        # ✅ تشخیص خودکار فونت Emoji برای آیکون‌های رنگی
        import tkinter.font as tkfont
        available = tkfont.families()
        emoji_font = 'Segoe UI'
        for fn in ['Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji']:
            if fn in available:
                emoji_font = fn
                break
        
        self.label = tk.Label(
            self,
            text=display_text,
            font=(emoji_font, 14),   # ← ✅ فونت Emoji رنگی
            padx=pad('button_md')[0],
            pady=pad('button_md')[1],
            cursor='hand2',
            border=0,
        )
        self.label.pack(fill=tk.BOTH, expand=True)
        
        if width:
            self.configure(width=width)
            self.pack_propagate(False)
        
        if height:
            self.configure(height=height)
            self.pack_propagate(False)
        
        # ===== رویدادها =====
        self._bind_events()
        
        # ===== Tooltip =====
        if tooltip:
            create_tooltip(self, tooltip)
        elif text:
            create_tooltip(self, text)
    
    def _build_text(self) -> str:
        """ساخت متن نهایی"""
        if self._icon and self._text:
            return f"{ico(self._icon)}  {self._text}"
        elif self._icon:
            return ico(self._icon)
        return self._text
    
    def _bind_events(self):
        """اتصال رویدادها"""
        for widget in (self, self.label):
            widget.bind('<Enter>', self._on_enter)
            widget.bind('<Leave>', self._on_leave)
            widget.bind('<Button-1>', self._on_press)
            widget.bind('<ButtonRelease-1>', self._on_release)
    
    def _on_enter(self, event=None):
        """ورود ماوس"""
        if not self._enabled:
            return
        self._apply_hover_style()
    
    def _on_leave(self, event=None):
        """خروج ماوس"""
        if not self._enabled:
            return
        self._apply_normal_style()
    
    def _on_press(self, event=None):
        """فشردن"""
        if not self._enabled:
            return
        self._apply_pressed_style()
    
    def _on_release(self, event=None):
        """رها کردن"""
        if not self._enabled:
            return
        
        # بررسی اینکه ماوس هنوز روی دکمه است
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        if widget in (self, self.label):
            self._apply_hover_style()
            if self.command:
                self.command()
        else:
            self._apply_normal_style()
    
    # ===== استایل‌ها (باید override شوند) =====
    
    def _apply_normal_style(self):
        """استایل عادی"""
        pass
    
    def _apply_hover_style(self):
        """استایل hover"""
        pass
    
    def _apply_pressed_style(self):
        """استایل فشرده"""
        pass
    
    # ===== Public Methods =====
    
    def set_enabled(self, enabled: bool):
        """فعال/غیرفعال کردن دکمه"""
        self._enabled = enabled
        
        if enabled:
            self._apply_normal_style()
            for widget in (self, self.label):
                widget.configure(cursor='hand2')
        else:
            self._apply_disabled_style()
            for widget in (self, self.label):
                widget.configure(cursor='')
    
    def _apply_disabled_style(self):
        """استایل غیرفعال"""
        pass
    
    def set_text(self, text: str):
        """تغییر متن"""
        self._text = text
        self.label.configure(text=self._build_text())
    
    def set_icon(self, icon: str):
        """تغییر آیکون"""
        self._icon = icon
        self.label.configure(text=self._build_text())


# ================================================================
# PRIMARY BUTTON
# ================================================================

class PrimaryButton(BaseButton):
    """دکمه اصلی - برای Action اصلی"""
    
    def _apply_normal_style(self):
        bg = get_color('btn_primary_bg')
        fg = get_color('btn_primary_text')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_hover_style(self):
        bg = get_color('btn_primary_hover')
        fg = get_color('btn_primary_text')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_pressed_style(self):
        bg = get_color('btn_primary_active')
        fg = get_color('btn_primary_text')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_disabled_style(self):
        bg = get_color('bg_surface')
        fg = get_color('text_disabled')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)


# ================================================================
# SECONDARY BUTTON
# ================================================================

class SecondaryButton(BaseButton):
    """دکمه فرعی - برای Action‌های ثانویه"""
    
    def _apply_normal_style(self):
        bg = get_color('btn_secondary_bg')
        fg = get_color('btn_secondary_text')
        
        self.configure(bg=bg, highlightthickness=1,
                       highlightbackground=get_color('border_default'),
                       highlightcolor=get_color('border_default'))
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_hover_style(self):
        bg = get_color('btn_secondary_hover')
        fg = get_color('btn_secondary_text')
        
        self.configure(bg=bg, highlightbackground=get_color('border_strong'))
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_pressed_style(self):
        bg = get_color('bg_active')
        fg = get_color('btn_secondary_text')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_disabled_style(self):
        bg = get_color('bg_surface')
        fg = get_color('text_disabled')
        
        self.configure(bg=bg, highlightbackground=get_color('border_subtle'))
        self.label.configure(bg=bg, fg=fg)


# ================================================================
# GHOST BUTTON
# ================================================================

class GhostButton(BaseButton):
    """دکمه شفاف - برای Action‌های کم‌اهمیت"""
    
    def _apply_normal_style(self):
        bg = get_color('bg_app')
        fg = get_color('btn_ghost_text')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_hover_style(self):
        bg = get_color('btn_ghost_hover')
        fg = get_color('btn_ghost_text_hover')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_pressed_style(self):
        bg = get_color('bg_active')
        fg = get_color('btn_ghost_text_hover')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_disabled_style(self):
        bg = get_color('bg_app')
        fg = get_color('text_disabled')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)


# ================================================================
# DANGER BUTTON
# ================================================================

class DangerButton(BaseButton):
    """دکمه خطرناک - برای Delete و ..."""
    
    def _apply_normal_style(self):
        bg = get_color('btn_danger_bg')
        fg = get_color('btn_danger_text')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_hover_style(self):
        bg = get_color('btn_danger_hover')
        fg = get_color('btn_danger_text')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_pressed_style(self):
        bg = _darken_color(get_color('btn_danger_hover'), 0.15)
        fg = get_color('btn_danger_text')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_disabled_style(self):
        bg = get_color('bg_surface')
        fg = get_color('text_disabled')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)


# ================================================================
# SUCCESS BUTTON
# ================================================================

class SuccessButton(BaseButton):
    """دکمه موفقیت - برای Save و ..."""
    
    def _apply_normal_style(self):
        bg = get_color('success')
        fg = '#FFFFFF'
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_hover_style(self):
        bg = get_color('success_hover')
        fg = '#FFFFFF'
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_pressed_style(self):
        bg = _darken_color(get_color('success_hover'), 0.15)
        fg = '#FFFFFF'
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_disabled_style(self):
        bg = get_color('bg_surface')
        fg = get_color('text_disabled')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)


# ================================================================
# ICON BUTTON (کوچک - فقط آیکون)
# ================================================================

class IconButton(BaseButton):
    """دکمه آیکون - مربعی کوچک"""
    
    def __init__(self, parent, icon: str, command: Callable = None,
                 tooltip: str = None, size: int = 32, **kwargs):
        """
        Args:
            parent: والد
            icon: نام آیکون
            command: تابع کلیک
            tooltip: متن راهنما
            size: اندازه (مربع)
        """
        super().__init__(
            parent,
            text="",
            icon=icon,
            command=command,
            tooltip=tooltip,
            width=size,
            height=size,
            **kwargs
        )
        
        # تنظیم padding کوچک‌تر
        self.label.configure(padx=2, pady=2)
    
    def _build_text(self) -> str:
        """فقط آیکون"""
        return ico(self._icon)
    
    def _apply_normal_style(self):
        bg = get_color('bg_surface')
        fg = get_color('text_secondary')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_hover_style(self):
        bg = get_color('bg_hover')
        fg = get_color('text_primary')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_pressed_style(self):
        bg = get_color('bg_active')
        fg = get_color('primary')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_disabled_style(self):
        bg = get_color('bg_surface')
        fg = get_color('text_disabled')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)

    def set_custom_colors(self, bg: str = None, fg: str = None, 
                          hover_bg: str = None, pressed_bg: str = None):
        """
        تنظیم رنگ‌های دلخواه
        
        Args:
            bg: پس‌زمینه عادی
            fg: رنگ متن
            hover_bg: پس‌زمینه هنگام hover
            pressed_bg: پس‌زمینه هنگام کلیک
        """
        self._custom_bg = bg
        self._custom_fg = fg
        self._custom_hover_bg = hover_bg or bg
        self._custom_pressed_bg = pressed_bg or hover_bg or bg
        
        # ✅ اعمال فوری
        self._apply_normal_style()
    
    def _apply_normal_style(self):
        """استایل عادی (با احترام به رنگ‌های دلخواه)"""
        # ===== اگر رنگ دلخواه داریم =====
        if hasattr(self, '_custom_bg') and self._custom_bg:
            bg = self._custom_bg
            fg = self._custom_fg or 'white'
            
            self.configure(bg=bg)
            self.label.configure(bg=bg, fg=fg)
            return
        
        # ===== حالت پیش‌فرض =====
        bg = get_color('bg_surface')
        fg = get_color('text_secondary')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_hover_style(self):
        """استایل hover (با احترام به رنگ‌های دلخواه)"""
        if hasattr(self, '_custom_hover_bg') and self._custom_hover_bg:
            bg = self._custom_hover_bg
            fg = self._custom_fg or 'white'
            
            self.configure(bg=bg)
            self.label.configure(bg=bg, fg=fg)
            return
        
        # حالت پیش‌فرض
        bg = get_color('bg_hover')
        fg = get_color('text_primary')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)
    
    def _apply_pressed_style(self):
        """استایل فشرده (با احترام به رنگ‌های دلخواه)"""
        if hasattr(self, '_custom_pressed_bg') and self._custom_pressed_bg:
            bg = self._custom_pressed_bg
            fg = self._custom_fg or 'white'
            
            self.configure(bg=bg)
            self.label.configure(bg=bg, fg=fg)
            return
        
        # حالت پیش‌فرض
        bg = get_color('bg_active')
        fg = get_color('primary')
        
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def button(parent, text: str = "", style: str = 'primary',
           icon: str = None, command: Callable = None,
           tooltip: str = None, **kwargs):
    """
    میانبر برای ساخت دکمه
    
    Args:
        style: 'primary', 'secondary', 'ghost', 'danger', 'success'
    
    Returns:
        نمونه دکمه
    """
    button_class = {
        'primary':   PrimaryButton,
        'secondary': SecondaryButton,
        'ghost':     GhostButton,
        'danger':    DangerButton,
        'success':   SuccessButton,
    }.get(style, PrimaryButton)
    
    return button_class(
        parent,
        text=text,
        icon=icon,
        command=command,
        tooltip=tooltip,
        **kwargs
    )


def icon_button(parent, icon: str, command: Callable = None,
                tooltip: str = None, size: int = 32, **kwargs):
    """میانبر برای دکمه آیکون"""
    return IconButton(parent, icon, command, tooltip, size, **kwargs)


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'BaseButton',
    'PrimaryButton',
    'SecondaryButton',
    'GhostButton',
    'DangerButton',
    'SuccessButton',
    'IconButton',
    'button',
    'icon_button',
]