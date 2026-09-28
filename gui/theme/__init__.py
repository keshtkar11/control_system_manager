# gui/theme/__init__.py
"""
Design System - Control System Manager

Modern Professional Engineering Desktop Application

این ماژول شامل:
- Design System جدید (colors, typography, spacing, icons)
- توابع legacy برای سازگاری با کدهای قدیمی
"""

# ================================================================
# LEGACY FUNCTIONS (سازگاری با کد قدیمی)
# ================================================================

def apply_theme(root):
    """
    Legacy function - اعمال تم (برای سازگاری با کد قدیمی)
    
    در Design System جدید از apply_ttk_styles استفاده می‌شود.
    """
    apply_ttk_styles(root)
    root.configure(bg=get_color('bg_app'))


def create_hover_effect(widget, base_color: str, hover_color: str = None):
    """
    ایجاد افکت hover برای ویجت (legacy)
    
    Args:
        widget: ویجت tkinter
        base_color: رنگ پایه
        hover_color: رنگ هنگام hover (اگر None باشد، از رنگ روشن‌تر استفاده می‌شود)
    """
    if hover_color is None:
        # استفاده از رنگ پیش‌فرض hover از تم
        hover_color = _lighten_color(base_color, 0.1)
    
    def on_enter(e):
        try:
            widget.config(bg=hover_color)
        except:
            pass
    
    def on_leave(e):
        try:
            widget.config(bg=base_color)
        except:
            pass
    
    widget.bind("<Enter>", on_enter, add="+")
    widget.bind("<Leave>", on_leave, add="+")

def create_tooltip(widget, text: str, delay: int = 500, duration: int = 3000,
                   position: str = 'below'):
    """
    ایجاد Tooltip برای ویجت (legacy)

    Args:
        widget: ویجت موردنظر
        text: متن tooltip
        delay: تاخیر قبل از نمایش (ms)
        duration: مدت نمایش (ms)
        position: موقعیت tooltip
            - 'below' (پیش‌فرض): زیر ویجت
            - 'above': بالای ویجت  ← ✅ جدید
            - 'auto': خودکار (بر اساس فضای موجود)
    """
    import tkinter as tk

    tooltip = None
    tooltip_after_id = None

    def show_tooltip():
        nonlocal tooltip
        if tooltip:
            return

        # ===== استایل =====
        bg = get_color('bg_surface_elevated', '#2F2F2F')
        fg = get_color('text_primary', '#E8E8E8')
        border_color = get_color('border_default', '#333333')

        # ===== ساخت Tooltip (اول بدون موقعیت) =====
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.attributes('-topmost', True)

        frame = tk.Frame(
            tooltip,
            bg=bg,
            highlightthickness=1,
            highlightbackground=border_color,
            highlightcolor=border_color,
        )
        frame.pack()

        tk.Label(
            frame,
            text=text,
            bg=bg,
            fg=fg,
            font=font('small'),
            padx=10,
            pady=6,
            justify='left',
            wraplength=300,
        ).pack()

        # ===== محاسبه موقعیت بعد از ساخت =====
        tooltip.update_idletasks()

        widget_x = widget.winfo_rootx()
        widget_y = widget.winfo_rooty()
        widget_w = widget.winfo_width()
        widget_h = widget.winfo_height()

        tooltip_w = tooltip.winfo_reqwidth()
        tooltip_h = tooltip.winfo_reqheight()

        screen_w = tooltip.winfo_screenwidth()
        screen_h = tooltip.winfo_screenheight()

        # ===== تشخیص موقعیت =====
        actual_position = position

        if position == 'auto':
            # اگه فضای زیر کافی نیست، بالا نشون بده
            if widget_y + widget_h + tooltip_h + 10 > screen_h:
                actual_position = 'above'
            else:
                actual_position = 'below'

        if actual_position == 'above':
            # ✅ بالای ویجت
            x = widget_x + (widget_w - tooltip_w) // 2
            y = widget_y - tooltip_h - 5
        else:
            # پیش‌فرض: زیر ویجت
            x = widget_x + (widget_w - tooltip_w) // 2
            y = widget_y + widget_h + 5

        # ===== اطمینان از باقی موندن در صفحه =====
        if x < 0:
            x = 5
        elif x + tooltip_w > screen_w:
            x = screen_w - tooltip_w - 5

        if y < 0:
            # اگه بالا نشد، بیار پایین
            y = widget_y + widget_h + 5

        tooltip.wm_geometry(f"+{x}+{y}")

        # بستن خودکار
        tooltip.after(duration, hide_tooltip)

    def hide_tooltip():
        nonlocal tooltip, tooltip_after_id
        if tooltip_after_id:
            try:
                widget.after_cancel(tooltip_after_id)
            except:
                pass
            tooltip_after_id = None
        if tooltip:
            tooltip.destroy()
            tooltip = None

    def on_enter(e):
        nonlocal tooltip_after_id
        tooltip_after_id = widget.after(delay, show_tooltip)

    def on_leave(e):
        hide_tooltip()

    widget.bind("<Enter>", on_enter, add="+")
    widget.bind("<Leave>", on_leave, add="+")
    widget.bind("<Button-1>", lambda e: hide_tooltip(), add="+")


def create_section_header(parent, text: str, icon: str = "📋"):
    """
    ایجاد هدر برای بخش‌های مختلف (legacy)
    
    Returns:
        Frame: فریم هدر
    """
    import tkinter as tk
    
    frame = tk.Frame(
        parent,
        bg=get_color('bg_surface_alt'),
        height=h('section_header'),
    )
    frame.pack(fill=tk.X, pady=(0, sp('sm')))
    frame.pack_propagate(False)
    
    label = tk.Label(
        frame,
        text=f"{icon}  {text}",
        font=font('h3'),
        fg=get_color('text_primary'),
        bg=get_color('bg_surface_alt'),
    )
    label.pack(anchor="w", padx=sp('lg'), pady=sp('sm'))
    
    return frame


def _lighten_color(hex_color: str, factor: float = 0.1) -> str:
    """
    روشن‌تر کردن یک رنگ hex
    
    Args:
        hex_color: رنگ به صورت hex (مثل '#0A84FF')
        factor: میزان روشن‌تر شدن (0.0 تا 1.0)
    
    Returns:
        رنگ جدید hex
    """
    try:
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # روشن‌تر کردن
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        
        return f"#{r:02X}{g:02X}{b:02X}"
    except Exception:
        return hex_color


def _darken_color(hex_color: str, factor: float = 0.1) -> str:
    """
    تیره‌تر کردن یک رنگ hex
    """
    try:
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        
        return f"#{r:02X}{g:02X}{b:02X}"
    except Exception:
        return hex_color


# ================================================================
# COLORS
# ================================================================
from .colors import (
    DARK_COLORS,
    LIGHT_COLORS,
    CURRENT_COLORS,
    get_color,
    set_theme_colors,
)

# ================================================================
# TYPOGRAPHY
# ================================================================
from .typography import (
    FONT_FAMILIES,
    FONT_SIZES,
    FONT_WEIGHTS,
    TEXT_STYLES,
    get_font_tuple,
    get_font,
    font,
)

# ================================================================
# SPACING
# ================================================================
from .spacing import (
    SPACING,
    PADDING,
    MARGIN,
    HEIGHTS,
    WIDTHS,
    RADIUS,
    BORDER_WIDTH,
    sp,
    pad,
    h,
    w,
    radius,
)

# ================================================================
# ICONS
# ================================================================
from .icons import (
    ICONS,
    ICON_SIZES,
    ico,
    icon_with_text,
)

# ================================================================
# THEME MANAGER
# ================================================================
from .theme_manager import (
    ThemeManager,
    get_theme_manager,
)

# ================================================================
# TTK STYLES
# ================================================================
from .ttk_styles import apply_ttk_styles


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    # ===== LEGACY =====
    'apply_theme',
    'create_hover_effect',
    'create_tooltip',
    'create_section_header',
    
    # ===== Colors =====
    'DARK_COLORS',
    'LIGHT_COLORS',
    'CURRENT_COLORS',
    'get_color',
    'set_theme_colors',
    
    # ===== Typography =====
    'FONT_FAMILIES',
    'FONT_SIZES',
    'FONT_WEIGHTS',
    'TEXT_STYLES',
    'get_font_tuple',
    'get_font',
    'font',
    
    # ===== Spacing =====
    'SPACING',
    'PADDING',
    'MARGIN',
    'HEIGHTS',
    'WIDTHS',
    'RADIUS',
    'BORDER_WIDTH',
    'sp',
    'pad',
    'h',
    'w',
    'radius',
    
    # ===== Icons =====
    'ICONS',
    'ICON_SIZES',
    'ico',
    'icon_with_text',
    
    # ===== Theme Manager =====
    'ThemeManager',
    'get_theme_manager',
    
    # ===== TTK =====
    'apply_ttk_styles',
]