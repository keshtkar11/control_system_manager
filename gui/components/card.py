# gui/components/card.py
"""
کامپوننت کارت‌ها
"""

import tkinter as tk
from typing import Callable

from gui.theme import (
    get_color, font, sp, pad, h, radius, ico,
)


# ================================================================
# BASE CARD
# ================================================================

class Card(tk.Frame):
    """
    کارت پایه با قابلیت‌های hover و header
    """
    
    def __init__(
        self,
        parent,
        title: str = "",
        icon: str = None,
        hoverable: bool = False,
        on_click: Callable = None,
        padding: tuple = None,
        **kwargs
    ):
        """
        Args:
            parent: والد
            title: عنوان
            icon: آیکون
            hoverable: قابل hover
            on_click: تابع کلیک
            padding: padding داخلی
        """
        super().__init__(
            parent,
            bg=get_color('card_bg'),
            highlightthickness=1,
            highlightbackground=get_color('card_border'),
            highlightcolor=get_color('card_border'),
            **kwargs
        )
        
        self.title = title
        self.icon = icon
        self.hoverable = hoverable
        self.on_click = on_click
        
        self._content_frame = None
        self._header_frame = None
        
        # ===== Header =====
        if title or icon:
            self._build_header()
        
        # ===== Content =====
        self._build_content(padding)
        
        # ===== رویدادها =====
        if hoverable:
            self._bind_hover_events()
        
        if on_click:
            self._bind_click_events()
    
    def _build_header(self):
        """ساخت header"""
        self._header_frame = tk.Frame(
            self,
            bg=get_color('card_header_bg'),
            height=h('card_header'),
        )
        self._header_frame.pack(fill=tk.X)
        self._header_frame.pack_propagate(False)
        
        # عنوان
        display_text = ""
        if self.icon and self.title:
            display_text = f"{ico(self.icon)}   {self.title}"
        elif self.icon:
            display_text = ico(self.icon)
        else:
            display_text = self.title
        
        self.title_label = tk.Label(
            self._header_frame,
            text=display_text,
            font=font('h3'),
            bg=get_color('card_header_bg'),
            fg=get_color('text_primary'),
            anchor='w',
        )
        self.title_label.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=pad('card')[0],
            pady=sp('sm'),
        )
    
    def _build_content(self, padding):
        """ساخت content"""
        padding = padding or pad('card')
        
        self._content_frame = tk.Frame(
            self,
            bg=get_color('card_bg'),
        )
        self._content_frame.pack(
            fill=tk.BOTH,
            expand=True,
            padx=padding[0],
            pady=padding[1],
        )
    
    def _bind_hover_events(self):
        """اتصال رویدادهای hover"""
        def on_enter(e):
            self.configure(
                highlightbackground=get_color('primary'),
            )
        
        def on_leave(e):
            self.configure(
                highlightbackground=get_color('card_border'),
            )
        
        for widget in self._get_all_widgets():
            widget.bind('<Enter>', on_enter, add='+')
            widget.bind('<Leave>', on_leave, add='+')
    
    def _bind_click_events(self):
        """اتصال رویدادهای کلیک"""
        def on_click(e):
            if self.on_click:
                self.on_click()
        
        for widget in self._get_all_widgets():
            widget.bind('<Button-1>', on_click, add='+')
            widget.configure(cursor='hand2')
    
    def _get_all_widgets(self):
        """دریافت همه ویجت‌ها"""
        widgets = [self]
        if self._header_frame:
            widgets.append(self._header_frame)
            widgets.append(self.title_label)
        return widgets
    
    @property
    def content(self) -> tk.Frame:
        """دسترسی به frame محتوا"""
        return self._content_frame
    
    def set_title(self, title: str):
        """تنظیم عنوان"""
        self.title = title
        if self.title_label:
            display = f"{ico(self.icon)}   {title}" if self.icon else title
            self.title_label.configure(text=display)


# ================================================================
# STAT CARD
# ================================================================

class StatCard(Card):
    """
    کارت آمار - نمایش یک مقدار
    """
    
    def __init__(
        self,
        parent,
        label: str,
        value: str = "0",
        icon: str = None,
        color: str = None,
        **kwargs
    ):
        """
        Args:
            parent: والد
            label: برچسب
            value: مقدار
            icon: آیکون
            color: رنگ accent
        """
        # کارت پایه بدون title
        super().__init__(parent, **kwargs)
        
        self.color = color or get_color('primary')
        
        # حذف content پیش‌فرض
        self._content_frame.destroy()
        
        # ===== Content جدید =====
        content = tk.Frame(self, bg=get_color('card_bg'))
        content.pack(fill=tk.BOTH, expand=True, padx=pad('card')[0], pady=pad('card')[1])
        
        # ===== Icon + Value =====
        top_row = tk.Frame(content, bg=get_color('card_bg'))
        top_row.pack(fill=tk.X)
        
        if icon:
            tk.Label(
                top_row,
                text=ico(icon),
                font=('Segoe UI', 18),
                bg=get_color('card_bg'),
                fg=self.color,
            ).pack(side=tk.LEFT, padx=(0, sp('sm')))
        
        self.value_label = tk.Label(
            top_row,
            text=value,
            font=('Segoe UI', 22, 'bold'),
            bg=get_color('card_bg'),
            fg=get_color('text_primary'),
            anchor='w',
        )
        self.value_label.pack(side=tk.LEFT)
        
        # ===== Label =====
        tk.Label(
            content,
            text=label,
            font=font('small'),
            bg=get_color('card_bg'),
            fg=get_color('text_secondary'),
            anchor='w',
        ).pack(fill=tk.X, pady=(sp('xs'), 0))
    
    def set_value(self, value):
        """تنظیم مقدار"""
        self.value_label.configure(text=str(value))


# ================================================================
# INFO CARD
# ================================================================

class InfoCard(Card):
    """
    کارت اطلاعات - نمایش key-value pairs
    """
    
    def __init__(
        self,
        parent,
        title: str = "Information",
        icon: str = 'info_circle',
        **kwargs
    ):
        super().__init__(parent, title=title, icon=icon, **kwargs)
        
        self._rows = []
    
    def add_row(self, label: str, value: str, value_color: str = None):
        """
        افزودن ردیف اطلاعات
        
        Args:
            label: برچسب
            value: مقدار
            value_color: رنگ مقدار (اختیاری)
        """
        row = tk.Frame(self._content_frame, bg=get_color('card_bg'))
        row.pack(fill=tk.X, pady=sp('xxs'))
        
        # Label
        tk.Label(
            row,
            text=label,
            font=font('body'),
            bg=get_color('card_bg'),
            fg=get_color('text_secondary'),
            anchor='w',
        ).pack(side=tk.LEFT)
        
        # Value
        value_label = tk.Label(
            row,
            text=value,
            font=font('body_bold'),
            bg=get_color('card_bg'),
            fg=value_color or get_color('text_primary'),
            anchor='e',
        )
        value_label.pack(side=tk.RIGHT)
        
        self._rows.append((row, value_label))
    
    def clear(self):
        """پاک کردن همه ردیف‌ها"""
        for row, _ in self._rows:
            row.destroy()
        self._rows = []


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def card(parent, title: str = "", icon: str = None, **kwargs):
    """میانبر برای کارت"""
    return Card(parent, title, icon, **kwargs)


def stat_card(parent, label: str, value: str = "0",
              icon: str = None, color: str = None, **kwargs):
    """میانبر برای کارت آمار"""
    return StatCard(parent, label, value, icon, color, **kwargs)


def info_card(parent, title: str = "Information", **kwargs):
    """میانبر برای کارت اطلاعات"""
    return InfoCard(parent, title, **kwargs)


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'Card',
    'StatCard',
    'InfoCard',
    'card',
    'stat_card',
    'info_card',
]