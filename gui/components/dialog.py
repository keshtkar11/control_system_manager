# gui/components/dialog.py
"""کلاس پایه دیالوگ‌های سفارشی - نسخه نهایی"""

import tkinter as tk
from typing import Callable, Optional

from gui.theme import (
    get_color, font, sp, pad, h, w, radius, ico,
)
from .button import PrimaryButton, SecondaryButton, GhostButton


# ================================================================
# BASE DIALOG
# ================================================================

class BaseDialog(tk.Toplevel):
    """کلاس پایه برای همه دیالوگ‌های برنامه"""
    
    def __init__(
        self,
        parent,
        title: str = "Dialog",
        width: int = None,
        height: int = None,
        modal: bool = True,
        resizable: bool = False,
        **kwargs
    ):
        super().__init__(parent)
        
        self.parent = parent
        self.result = None
        self._is_closing = False
        
        # ===== تنظیمات پنجره =====
        self.title(title)
        self.configure(bg=get_color('bg_app'))
        self.transient(parent)
        
        if modal:
            self.grab_set()
        
        if not resizable:
            self.resizable(False, False)
        
        # ===== اندازه و موقعیت =====
        w_val = width or w('dialog_md')
        h_val = height or 500
        self._center_window(w_val, h_val)
        
        # ===== آیکون =====
        try:
            self.iconbitmap("resources/icons/icon.ico")
        except:
            pass
        
        # ===== ساخت UI =====
        self._build_ui()
        
        # ===== رویدادها =====
        self.bind('<Escape>', lambda e: self.on_cancel())
        self.protocol('WM_DELETE_WINDOW', self.on_cancel)
        
        # ===== فوکوس =====
        self.focus_set()
    
    def _center_window(self, width: int, height: int):
        """وسط‌چین کردن پنجره"""
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _build_ui(self):
        """ساخت UI پایه"""
        # ✅ ترتیب: Header → Body → Footer
        
        # ===== Header =====
        self._build_header()
        
        # ===== Footer (اول ساخته می‌شود تا در پایین ثابت بماند) =====
        self._build_footer()
        
        # ===== Body (بعد از Footer، فضای باقی‌مانده را پر می‌کند) =====
        self.body_frame = tk.Frame(self, bg=get_color('bg_app'))
        self.body_frame.pack(fill=tk.BOTH, expand=True, padx=sp('lg'), pady=sp('lg'))
        
        self.build_body(self.body_frame)
    
    def _build_header(self):
        """ساخت header"""
        header = tk.Frame(self, bg=get_color('bg_surface'), height=h('toolbar'))
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        self.title_label = tk.Label(
            header,
            text=f"  {self.title()}",
            font=font('h2'),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
            anchor='w',
        )
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=sp('lg'))
        
        close_btn = tk.Label(
            header,
            text=ico('close'),
            font=('Segoe UI', 12),
            bg=get_color('bg_surface'),
            fg=get_color('text_secondary'),
            cursor='hand2',
        )
        close_btn.pack(side=tk.RIGHT, padx=sp('lg'))
        close_btn.bind('<Button-1>', lambda e: self.on_cancel())
    
    def _build_footer(self):
        """
        ساخت footer - این متد در ConfirmDialog و MessageDialog override می‌شود
        """
        footer = tk.Frame(self, bg=get_color('bg_surface'), height=60)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        btn_frame = tk.Frame(footer, bg=get_color('bg_surface'))
        btn_frame.pack(side=tk.RIGHT, padx=sp('lg'), pady=sp('md'))
        
        # Cancel
        SecondaryButton(
            btn_frame,
            text="Cancel",
            command=self.on_cancel,
        ).pack(side=tk.RIGHT, padx=(sp('sm'), 0))
        
        # OK
        PrimaryButton(
            btn_frame,
            text="OK",
            command=self.on_ok,
        ).pack(side=tk.RIGHT)
    
    # ===== Methods to override =====
    
    def build_body(self, parent):
        """ساخت محتوای دیالوگ"""
        pass
    
    def on_ok(self):
        """تایید"""
        self.result = True
        self._close_dialog()
    
    def on_cancel(self):
        """انصراف"""
        self.result = None
        self._close_dialog()
    
    def _close_dialog(self):
        """بستن امن دیالوگ"""
        if self._is_closing:
            return
        
        self._is_closing = True
        
        try:
            self.grab_release()
        except:
            pass
        
        try:
            self.destroy()
        except:
            pass
    
    # ===== Public Methods =====
    
    def show(self):
        """نمایش و انتظار برای بستن"""
        try:
            self.wait_window()
        except:
            pass
        
        return self.result


# ================================================================
# MESSAGE DIALOG
# ================================================================

class MessageDialog(BaseDialog):
    """دیالوگ پیام"""
    
    def __init__(
        self,
        parent,
        title: str = "Message",
        message: str = "",
        msg_type: str = 'info',
        **kwargs
    ):
        self.message = message
        self.msg_type = msg_type
        
        super().__init__(parent, title=title, width=450, height=220, **kwargs)
    
    def _build_header(self):
        """Header با آیکون"""
        colors = {
            'info':    (get_color('info'), 'info_circle'),
            'success': (get_color('success'), 'check_circle'),
            'warning': (get_color('warning'), 'warning_triangle'),
            'error':   (get_color('danger'), 'x_circle'),
        }
        
        color, icon_name = colors.get(self.msg_type, colors['info'])
        
        header = tk.Frame(self, bg=get_color('bg_surface'), height=h('toolbar'))
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=ico(icon_name),
            font=('Segoe UI', 20),
            bg=get_color('bg_surface'),
            fg=color,
        ).pack(side=tk.LEFT, padx=(sp('lg'), sp('sm')))
        
        tk.Label(
            header,
            text=self.title(),
            font=font('h2'),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
            anchor='w',
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def build_body(self, parent):
        """متن پیام"""
        tk.Label(
            parent,
            text=self.message,
            font=font('body'),
            bg=get_color('bg_app'),
            fg=get_color('text_primary'),
            anchor='w',
            justify='left',
            wraplength=380,
        ).pack(fill=tk.BOTH, expand=True)
    
    def _build_footer(self):
        """Footer با یک دکمه OK"""
        footer = tk.Frame(self, bg=get_color('bg_surface'), height=60)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        PrimaryButton(
            footer,
            text="OK",
            command=self.on_ok,
        ).pack(side=tk.RIGHT, padx=sp('lg'), pady=sp('md'))


# ================================================================
# CONFIRM DIALOG
# ================================================================

class ConfirmDialog(BaseDialog):
    """دیالوگ تایید"""
    
    def __init__(
        self,
        parent,
        title: str = "Confirm",
        message: str = "Are you sure?",
        msg_type: str = 'question',
        ok_text: str = "Yes",
        cancel_text: str = "No",
        **kwargs
    ):
        self.message = message
        self.msg_type = msg_type
        self.ok_text = ok_text
        self.cancel_text = cancel_text
        
        super().__init__(parent, title=title, width=450, height=240, **kwargs)
    
    def _build_header(self):
        """Header با آیکون"""
        colors = {
            'question': (get_color('primary'), 'question'),
            'warning':  (get_color('warning'), 'warning_triangle'),
            'danger':   (get_color('danger'), 'warning_triangle'),
        }
        
        color, icon_name = colors.get(self.msg_type, colors['question'])
        
        header = tk.Frame(self, bg=get_color('bg_surface'), height=h('toolbar'))
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=ico(icon_name),
            font=('Segoe UI', 20),
            bg=get_color('bg_surface'),
            fg=color,
        ).pack(side=tk.LEFT, padx=(sp('lg'), sp('sm')))
        
        tk.Label(
            header,
            text=self.title(),
            font=font('h2'),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
            anchor='w',
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def build_body(self, parent):
        """متن پیام"""
        tk.Label(
            parent,
            text=self.message,
            font=font('body'),
            bg=get_color('bg_app'),
            fg=get_color('text_primary'),
            anchor='w',
            justify='left',
            wraplength=380,
        ).pack(fill=tk.BOTH, expand=True)
    
    def _build_footer(self):
        """
        ✅ Footer با دو دکمه
        این متد در ConfirmDialog استفاده می‌شود نه BaseDialog
        """
        footer = tk.Frame(self, bg=get_color('bg_surface'), height=60)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        btn_frame = tk.Frame(footer, bg=get_color('bg_surface'))
        btn_frame.pack(side=tk.RIGHT, padx=sp('lg'), pady=sp('md'))
        
        # ===== Cancel Button =====
        SecondaryButton(
            btn_frame,
            text=self.cancel_text,
            command=self.on_cancel,
        ).pack(side=tk.RIGHT, padx=(sp('sm'), 0))
        
        # ===== OK Button =====
        if self.msg_type == 'danger':
            # دکمه قرمز برای Danger
            DangerButton(
                btn_frame,
                text=self.ok_text,
                command=self.on_ok,
            ).pack(side=tk.RIGHT)
        else:
            PrimaryButton(
                btn_frame,
                text=self.ok_text,
                command=self.on_ok,
            ).pack(side=tk.RIGHT)


# Import برای DangerButton
from .button import DangerButton


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def message_dialog(parent, message: str, title: str = "Message",
                   msg_type: str = 'info') -> bool:
    """نمایش دیالوگ پیام"""
    dialog = MessageDialog(parent, title, message, msg_type)
    dialog.show()
    return True


def confirm_dialog(parent, message: str, title: str = "Confirm",
                   msg_type: str = 'question',
                   ok_text: str = "Yes",
                   cancel_text: str = "No") -> bool:
    """
    نمایش دیالوگ تایید
    
    Returns:
        True اگر کاربر تایید کند
        False اگر کاربر انصراف دهد
    """
    dialog = ConfirmDialog(
        parent=parent,
        title=title,
        message=message,
        msg_type=msg_type,
        ok_text=ok_text,
        cancel_text=cancel_text,
    )
    
    result = dialog.show()
    
    return result is True


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'BaseDialog',
    'MessageDialog',
    'ConfirmDialog',
    'message_dialog',
    'confirm_dialog',
]