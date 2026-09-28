# gui/components/input.py
"""
کامپوننت ورودی‌های سفارشی
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List

from gui.theme import (
    get_color, font, sp, pad, h,
    ico,
)


# ================================================================
# LABELED INPUT
# ================================================================

class LabeledInput(tk.Frame):
    """
    ورودی با label
    """
    
    def __init__(
        self,
        parent,
        label: str = "",
        value: str = "",
        placeholder: str = "",
        width: int = None,
        show_label: bool = True,
        required: bool = False,
        **kwargs
    ):
        """
        Args:
            parent: والد
            label: برچسب
            value: مقدار اولیه
            placeholder: متن راهنما
            width: عرض
            show_label: نمایش label
            required: آیا الزامی است
        """
        super().__init__(parent, bg=get_color('bg_app'), **kwargs)
        
        self.required = required
        
        # ===== Label =====
        if show_label and label:
            label_text = f"{label} *" if required else label
            
            self.label_widget = tk.Label(
                self,
                text=label_text,
                font=font('small'),
                bg=get_color('bg_app'),
                fg=get_color('text_secondary'),
                anchor='w',
            )
            self.label_widget.pack(fill=tk.X, pady=(0, sp('xs')))
        
        # ===== Entry Frame =====
        entry_frame = tk.Frame(
            self,
            bg=get_color('input_bg'),
            highlightthickness=1,
            highlightbackground=get_color('input_border'),
            highlightcolor=get_color('input_border_focus'),
        )
        entry_frame.pack(fill=tk.X)
        
        # ===== Entry =====
        self.entry = tk.Entry(
            entry_frame,
            font=font('input'),
            bg=get_color('input_bg'),
            fg=get_color('input_text'),
            insertbackground=get_color('input_text'),
            relief='flat',
            border=0,
        )
        self.entry.pack(
            fill=tk.BOTH,
            expand=True,
            padx=pad('input')[0],
            pady=pad('input')[1],
        )
        
        if width:
            self.entry.configure(width=width)
        
        # ===== Placeholder =====
        self.placeholder = placeholder
        self._placeholder_active = False
        
        if placeholder and not value:
            self._show_placeholder()
        
        # ===== Value =====
        if value:
            self.entry.insert(0, value)
        
        # ===== رویدادها =====
        self.entry.bind('<FocusIn>', self._on_focus_in)
        self.entry.bind('<FocusOut>', self._on_focus_out)
    
    def _show_placeholder(self):
        """نمایش placeholder"""
        self.entry.insert(0, self.placeholder)
        self.entry.configure(fg=get_color('input_placeholder'))
        self._placeholder_active = True
    
    def _hide_placeholder(self):
        """مخفی کردن placeholder"""
        self.entry.delete(0, tk.END)
        self.entry.configure(fg=get_color('input_text'))
        self._placeholder_active = False
    
    def _on_focus_in(self, event=None):
        """ورود فوکوس"""
        if self._placeholder_active:
            self._hide_placeholder()
        
        # تغییر رنگ border
        self.entry.master.configure(
            highlightbackground=get_color('input_border_focus')
        )
    
    def _on_focus_out(self, event=None):
        """خروج فوکوس"""
        if not self.entry.get() and self.placeholder:
            self._show_placeholder()
        
        # برگرداندن رنگ border
        self.entry.master.configure(
            highlightbackground=get_color('input_border')
        )
    
    # ===== Methods =====
    
    def get(self) -> str:
        """دریافت مقدار"""
        if self._placeholder_active:
            return ""
        return self.entry.get()
    
    def set(self, value: str):
        """تنظیم مقدار"""
        if self._placeholder_active:
            self._hide_placeholder()
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
    
    def clear(self):
        """پاک کردن"""
        self.entry.delete(0, tk.END)
        if self.placeholder:
            self._show_placeholder()
    
    def focus(self):
        """فوکوس روی ورودی"""
        self.entry.focus_set()


# ================================================================
# LABELED COMBOBOX
# ================================================================

class LabeledCombobox(tk.Frame):
    """
    کمبوباکس با label
    """
    
    def __init__(
        self,
        parent,
        label: str = "",
        values: List[str] = None,
        value: str = "",
        width: int = None,
        show_label: bool = True,
        readonly: bool = True,
        on_change: Callable = None,
        **kwargs
    ):
        super().__init__(parent, bg=get_color('bg_app'), **kwargs)
        
        self.on_change = on_change
        
        # ===== Label =====
        if show_label and label:
            tk.Label(
                self,
                text=label,
                font=font('small'),
                bg=get_color('bg_app'),
                fg=get_color('text_secondary'),
                anchor='w',
            ).pack(fill=tk.X, pady=(0, sp('xs')))
        
        # ===== Combobox =====
        self.combo = ttk.Combobox(
            self,
            values=values or [],
            font=font('input'),
            state='readonly' if readonly else 'normal',
        )
        self.combo.pack(fill=tk.X)
        
        if width:
            self.combo.configure(width=width)
        
        if value:
            self.combo.set(value)
        elif values:
            self.combo.current(0)
        
        # ===== رویداد =====
        if on_change:
            self.combo.bind('<<ComboboxSelected>>', lambda e: self.on_change(self.get()))
    
    def get(self) -> str:
        """دریافت مقدار"""
        return self.combo.get()
    
    def set(self, value: str):
        """تنظیم مقدار"""
        self.combo.set(value)
    
    def set_values(self, values: List[str]):
        """تنظیم لیست مقادیر"""
        self.combo['values'] = values


# ================================================================
# LABELED TEXT (Multiline)
# ================================================================

class LabeledText(tk.Frame):
    """
    ورودی چند خطی با label
    """
    
    def __init__(
        self,
        parent,
        label: str = "",
        value: str = "",
        height: int = 5,
        show_label: bool = True,
        **kwargs
    ):
        super().__init__(parent, bg=get_color('bg_app'), **kwargs)
        
        # ===== Label =====
        if show_label and label:
            tk.Label(
                self,
                text=label,
                font=font('small'),
                bg=get_color('bg_app'),
                fg=get_color('text_secondary'),
                anchor='w',
            ).pack(fill=tk.X, pady=(0, sp('xs')))
        
        # ===== Text Frame =====
        text_frame = tk.Frame(
            self,
            bg=get_color('input_bg'),
            highlightthickness=1,
            highlightbackground=get_color('input_border'),
            highlightcolor=get_color('input_border_focus'),
        )
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== Text =====
        self.text = tk.Text(
            text_frame,
            font=font('input'),
            bg=get_color('input_bg'),
            fg=get_color('input_text'),
            insertbackground=get_color('input_text'),
            relief='flat',
            border=0,
            height=height,
            wrap=tk.WORD,
        )
        self.text.pack(
            fill=tk.BOTH,
            expand=True,
            padx=pad('input')[0],
            pady=pad('input')[1],
        )
        
        if value:
            self.text.insert('1.0', value)
        
        # ===== رویدادها =====
        self.text.bind('<FocusIn>', lambda e: text_frame.configure(
            highlightbackground=get_color('input_border_focus')
        ))
        self.text.bind('<FocusOut>', lambda e: text_frame.configure(
            highlightbackground=get_color('input_border')
        ))
    
    def get(self) -> str:
        """دریافت متن"""
        return self.text.get('1.0', tk.END).strip()
    
    def set(self, value: str):
        """تنظیم متن"""
        self.text.delete('1.0', tk.END)
        self.text.insert('1.0', value)


# ================================================================
# SEARCH INPUT
# ================================================================

class SearchInput(tk.Frame):
    """
    ورودی جستجو با آیکون
    """
    
    def __init__(
        self,
        parent,
        placeholder: str = "Search...",
        on_change: Callable = None,
        width: int = None,
        **kwargs
    ):
        super().__init__(
            parent,
            bg=get_color('input_bg'),
            highlightthickness=1,
            highlightbackground=get_color('input_border'),
            highlightcolor=get_color('input_border_focus'),
            **kwargs
        )
        
        self.on_change = on_change
        self.placeholder = placeholder
        
        # ===== Icon =====
        tk.Label(
            self,
            text=ico('search'),
            font=('Segoe UI', 11),
            bg=get_color('input_bg'),
            fg=get_color('text_muted'),
        ).pack(side=tk.LEFT, padx=(sp('sm'), 0))
        
        # ===== Entry =====
        self.entry = tk.Entry(
            self,
            font=font('input'),
            bg=get_color('input_bg'),
            fg=get_color('input_placeholder'),
            insertbackground=get_color('input_text'),
            relief='flat',
            border=0,
        )
        self.entry.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=sp('xs'),
            pady=pad('input')[1],
        )
        
        if width:
            self.entry.configure(width=width)
        
        # ===== Placeholder =====
        self._placeholder_active = True
        self.entry.insert(0, placeholder)
        
        # ===== Clear Button =====
        self.clear_btn = tk.Label(
            self,
            text=ico('close'),
            font=('Segoe UI', 9),
            bg=get_color('input_bg'),
            fg=get_color('text_muted'),
            cursor='hand2',
        )
        self.clear_btn.bind('<Button-1>', lambda e: self.clear())
        
        # ===== رویدادها =====
        self.entry.bind('<FocusIn>', self._on_focus_in)
        self.entry.bind('<FocusOut>', self._on_focus_out)
        self.entry.bind('<KeyRelease>', self._on_key_release)
    
    def _on_focus_in(self, event=None):
        if self._placeholder_active:
            self.entry.delete(0, tk.END)
            self.entry.configure(fg=get_color('input_text'))
            self._placeholder_active = False
        
        self.configure(highlightbackground=get_color('input_border_focus'))
    
    def _on_focus_out(self, event=None):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.configure(fg=get_color('input_placeholder'))
            self._placeholder_active = True
        
        self.configure(highlightbackground=get_color('input_border'))
    
    def _on_key_release(self, event=None):
        value = self.get()
        
        # نمایش/مخفی کردن دکمه clear
        if value:
            if not self.clear_btn.winfo_ismapped():
                self.clear_btn.pack(side=tk.RIGHT, padx=sp('sm'))
        else:
            self.clear_btn.pack_forget()
        
        # فراخوانی callback
        if self.on_change:
            self.on_change(value)
    
    def get(self) -> str:
        """دریافت متن جستجو"""
        if self._placeholder_active:
            return ""
        return self.entry.get()
    
    def set(self, value: str):
        """تنظیم متن"""
        if self._placeholder_active:
            self.entry.delete(0, tk.END)
            self._placeholder_active = False
        
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.entry.configure(fg=get_color('input_text'))
        
        if value:
            self.clear_btn.pack(side=tk.RIGHT, padx=sp('sm'))
    
    def clear(self):
        """پاک کردن"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self.placeholder)
        self.entry.configure(fg=get_color('input_placeholder'))
        self._placeholder_active = True
        self.clear_btn.pack_forget()
        
        if self.on_change:
            self.on_change("")


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def input_field(parent, label: str = "", value: str = "",
                placeholder: str = "", **kwargs):
    """میانبر برای ورودی"""
    return LabeledInput(parent, label, value, placeholder, **kwargs)


def combo_field(parent, label: str = "", values: List[str] = None,
                value: str = "", **kwargs):
    """میانبر برای کمبوباکس"""
    return LabeledCombobox(parent, label, values, value, **kwargs)


def search_box(parent, placeholder: str = "Search...",
               on_change: Callable = None, **kwargs):
    """میانبر برای جستجو"""
    return SearchInput(parent, placeholder, on_change, **kwargs)


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'LabeledInput',
    'LabeledCombobox',
    'LabeledText',
    'SearchInput',
    'input_field',
    'combo_field',
    'search_box',
]