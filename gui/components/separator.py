# gui/components/separator.py
"""
کامپوننت جداکننده - Separator
"""

import tkinter as tk
from gui.theme import get_color, sp, h


class Separator(tk.Frame):
    """
    جداکننده افقی یا عمودی
    
    مثال:
        Separator(parent)  # افقی
        Separator(parent, orientation='vertical')  # عمودی
    """
    
    def __init__(
        self,
        parent,
        orientation: str = 'horizontal',
        color: str = None,
        thickness: int = 1,
        spacing: int = None,
        **kwargs
    ):
        """
        Args:
            parent: والد
            orientation: 'horizontal' یا 'vertical'
            color: رنگ جداکننده (پیش‌فرض: border_default)
            thickness: ضخامت
            spacing: فاصله از اطراف
        """
        self.orientation = orientation
        self.border_color = color or get_color('border_default')
        self.thickness = thickness
        self.spacing = spacing if spacing is not None else sp('md')
        
        if orientation == 'horizontal':
            super().__init__(
                parent,
                bg=self.border_color,
                height=thickness,
                **kwargs
            )
            self.pack_configure(
                fill=tk.X,
                pady=self.spacing
            )
        else:
            super().__init__(
                parent,
                bg=self.border_color,
                width=thickness,
                **kwargs
            )
            self.pack_configure(
                fill=tk.Y,
                padx=self.spacing
            )


class Divider(tk.Frame):
    """
    جداکننده با متن در وسط
    """
    
    def __init__(
        self,
        parent,
        text: str = "",
        color: str = None,
        text_color: str = None,
        **kwargs
    ):
        """
        Args:
            parent: والد
            text: متن وسط جداکننده
            color: رنگ خط
            text_color: رنگ متن
        """
        from gui.theme import font
        
        self.border_color = color or get_color('border_default')
        self.text_color = text_color or get_color('text_muted')
        
        super().__init__(parent, bg=get_color('bg_app'), **kwargs)
        
        if text:
            # خط چپ
            left_line = tk.Frame(
                self,
                bg=self.border_color,
                height=1
            )
            left_line.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=sp('md'))
            
            # متن وسط
            tk.Label(
                self,
                text=text,
                bg=get_color('bg_app'),
                fg=self.text_color,
                font=font('caption'),
            ).pack(side=tk.LEFT, padx=sp('sm'))
            
            # خط راست
            right_line = tk.Frame(
                self,
                bg=self.border_color,
                height=1
            )
            right_line.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=sp('md'))
        else:
            # فقط خط
            line = tk.Frame(
                self,
                bg=self.border_color,
                height=1
            )
            line.pack(fill=tk.X, pady=sp('md'))


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['Separator', 'Divider']