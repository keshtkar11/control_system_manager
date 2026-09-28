# gui/layout/toolbar.py
"""
نوار ابزار - Toolbar
"""

import tkinter as tk
from typing import Callable, List, Dict

from gui.theme import (
    get_color, font, sp, pad, h, ico,
)
from gui.components import (
    PrimaryButton, SecondaryButton, GhostButton,
    IconButton, Separator,
)


class Toolbar(tk.Frame):
    """
    نوار ابزار بالای پنجره
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=get_color('toolbar_bg'),
            height=h('toolbar'),
            **kwargs
        )
        
        self.pack_propagate(False)
        
        # ===== بخش چپ =====
        self.left_frame = tk.Frame(self, bg=get_color('toolbar_bg'))
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=sp('sm'))
        
        # ===== بخش وسط =====
        self.center_frame = tk.Frame(self, bg=get_color('toolbar_bg'))
        self.center_frame.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        
        # ===== بخش راست =====
        self.right_frame = tk.Frame(self, bg=get_color('toolbar_bg'))
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=sp('sm'))
    
    def add_button(
        self,
        text: str,
        icon: str = None,
        command: Callable = None,
        style: str = 'secondary',
        tooltip: str = None,
        side: str = 'left',
    ):
        """
        افزودن دکمه
        
        Args:
            text: متن دکمه
            icon: آیکون
            command: تابع
            style: 'primary', 'secondary', 'ghost', 'danger', 'success'
            tooltip: راهنما
            side: 'left', 'center', 'right'
        """
        button_classes = {
            'primary':   PrimaryButton,
            'secondary': SecondaryButton,
            'ghost':     GhostButton,
        }
        
        if style == 'danger':
            from gui.components import DangerButton
            btn_class = DangerButton
        elif style == 'success':
            from gui.components import SuccessButton
            btn_class = SuccessButton
        else:
            btn_class = button_classes.get(style, SecondaryButton)
        
        btn = btn_class(
            self._get_container(side),
            text=text,
            icon=icon,
            command=command,
            tooltip=tooltip or text,
        )
        btn.pack(side=tk.LEFT, padx=sp('xxs'), pady=sp('sm'))
        
        return btn
    
    def add_icon_button(
        self,
        icon: str,
        command: Callable = None,
        tooltip: str = None,
        side: str = 'left',
        size: int = 32,
        bg: str = None,
        fg: str = None,
        hover_bg: str = None,
    ):
        """
        افزودن دکمه آیکون
        
        Args:
            icon: نام آیکون
            command: تابع کلیک
            tooltip: راهنما
            side: 'left', 'center', 'right'
            size: اندازه
            bg: پس‌زمینه دلخواه (اختیاری)
            fg: رنگ متن دلخواه (اختیاری)
            hover_bg: پس‌زمینه هنگام hover (اختیاری)
        """
        btn = IconButton(
            self._get_container(side),
            icon=icon,
            command=command,
            tooltip=tooltip,
            size=size,
        )
        
        # ============================================================
        # ✅ اعمال رنگ‌های دلخواه
        # ============================================================
        if bg or fg:
            btn.set_custom_colors(bg=bg, fg=fg, hover_bg=hover_bg)
        
        btn.pack(side=tk.LEFT, padx=sp('xxs'), pady=sp('sm'))
        return btn

    def add_separator(self, side: str = 'left'):
        """افزودن جداکننده"""
        sep = tk.Frame(
            self._get_container(side),
            bg=get_color('border_default'),
            width=1,
            height=24,
        )
        sep.pack(side=tk.LEFT, padx=sp('sm'), pady=sp('md'))
    
    def add_spacer(self, side: str = 'left'):
        """افزودن فاصله"""
        spacer = tk.Frame(
            self._get_container(side),
            bg=get_color('toolbar_bg'),
            width=sp('lg'),
        )
        spacer.pack(side=tk.LEFT)
    
    def add_label(self, text: str, icon: str = None, side: str = 'left'):
        """افزودن label"""
        display = f"{ico(icon)}  {text}" if icon else text
        
        label = tk.Label(
            self._get_container(side),
            text=display,
            font=font('body'),
            bg=get_color('toolbar_bg'),
            fg=get_color('text_primary'),
        )
        label.pack(side=tk.LEFT, padx=sp('sm'), pady=sp('md'))
        
        return label
    
    def _get_container(self, side: str) -> tk.Frame:
        """دریافت container بر اساس side"""
        return {
            'left':   self.left_frame,
            'center': self.center_frame,
            'right':  self.right_frame,
        }.get(side, self.left_frame)
    
    def clear(self, side: str = None):
        """پاک کردن دکمه‌ها"""
        frames = {
            'left':   [self.left_frame],
            'center': [self.center_frame],
            'right':  [self.right_frame],
        }
        
        if side:
            frames_to_clear = frames.get(side, [])
        else:
            frames_to_clear = [self.left_frame, self.center_frame, self.right_frame]
        
        for frame in frames_to_clear:
            for widget in frame.winfo_children():
                widget.destroy()


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['Toolbar']