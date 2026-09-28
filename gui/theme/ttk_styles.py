# gui/theme/ttk_styles.py
"""
استایل‌های ttk - یکپارچه‌سازی Theme با ویجت‌های ttk
"""

from tkinter import ttk
from .theme_manager import get_theme_manager
from .colors import get_color
from .typography import get_font_tuple


def apply_ttk_styles(root):
    """
    اعمال استایل‌های ttk به برنامه
    
    Args:
        root: پنجره اصلی
    """
    tm = get_theme_manager()
    
    style = ttk.Style()
    
    # استفاده از تم clam برای کنترل بیشتر
    try:
        style.theme_use('clam')
    except Exception:
        pass
    
    # ================================================================
    # TTK FRAME
    # ================================================================
    style.configure(
        'TFrame',
        background=get_color('bg_app'),
        borderwidth=0,
    )
    
    style.configure(
        'Surface.TFrame',
        background=get_color('bg_surface'),
    )
    
    style.configure(
        'SurfaceAlt.TFrame',
        background=get_color('bg_surface_alt'),
    )
    
    # ================================================================
    # TTK LABEL
    # ================================================================
    style.configure(
        'TLabel',
        background=get_color('bg_app'),
        foreground=get_color('text_primary'),
        font=get_font_tuple('body'),
    )
    
    style.configure(
        'Primary.TLabel',
        background=get_color('bg_app'),
        foreground=get_color('text_primary'),
        font=get_font_tuple('body'),
    )
    
    style.configure(
        'Secondary.TLabel',
        background=get_color('bg_app'),
        foreground=get_color('text_secondary'),
        font=get_font_tuple('small'),
    )
    
    style.configure(
        'Muted.TLabel',
        background=get_color('bg_app'),
        foreground=get_color('text_muted'),
        font=get_font_tuple('small'),
    )
    
    style.configure(
        'H1.TLabel',
        background=get_color('bg_app'),
        foreground=get_color('text_primary'),
        font=get_font_tuple('h1'),
    )
    
    style.configure(
        'H2.TLabel',
        background=get_color('bg_app'),
        foreground=get_color('text_primary'),
        font=get_font_tuple('h2'),
    )
    
    style.configure(
        'H3.TLabel',
        background=get_color('bg_app'),
        foreground=get_color('text_primary'),
        font=get_font_tuple('h3'),
    )
    
    # ================================================================
    # TTK BUTTON
    # ================================================================
    style.configure(
        'TButton',
        background=get_color('btn_secondary_bg'),
        foreground=get_color('btn_secondary_text'),
        font=get_font_tuple('button'),
        borderwidth=1,
        relief='flat',
        padding=(16, 8),
        focuscolor='none',
    )
    
    style.map(
        'TButton',
        background=[
            ('active', get_color('btn_secondary_hover')),
            ('pressed', get_color('bg_active')),
            ('disabled', get_color('bg_disabled', '#333333')),
        ],
        foreground=[
            ('disabled', get_color('text_disabled')),
        ],
    )
    
    # Primary Button
    style.configure(
        'Primary.TButton',
        background=get_color('btn_primary_bg'),
        foreground=get_color('btn_primary_text'),
        font=get_font_tuple('button'),
        borderwidth=0,
        padding=(16, 8),
        focuscolor='none',
    )
    
    style.map(
        'Primary.TButton',
        background=[
            ('active', get_color('btn_primary_hover')),
            ('pressed', get_color('btn_primary_active')),
            ('disabled', get_color('bg_disabled', '#333333')),
        ],
        foreground=[
            ('disabled', get_color('text_disabled')),
        ],
    )
    
    # Danger Button
    style.configure(
        'Danger.TButton',
        background=get_color('btn_danger_bg'),
        foreground=get_color('btn_danger_text'),
        font=get_font_tuple('button'),
        borderwidth=0,
        padding=(16, 8),
        focuscolor='none',
    )
    
    style.map(
        'Danger.TButton',
        background=[
            ('active', get_color('btn_danger_hover')),
            ('pressed', get_color('btn_danger_hover')),
        ],
    )
    
    # ================================================================
    # TTK ENTRY
    # ================================================================
    style.configure(
        'TEntry',
        fieldbackground=get_color('input_bg'),
        foreground=get_color('input_text'),
        insertcolor=get_color('input_text'),
        font=get_font_tuple('input'),
        borderwidth=1,
        relief='flat',
        padding=(12, 8),
    )
    
    style.map(
        'TEntry',
        fieldbackground=[
            ('disabled', get_color('input_disabled_bg')),
            ('focus', get_color('input_bg')),
        ],
        foreground=[
            ('disabled', get_color('input_disabled_text')),
        ],
        bordercolor=[
            ('focus', get_color('input_border_focus')),
            ('!focus', get_color('input_border')),
        ],
    )
    
    # ================================================================
    # TTK COMBOBOX
    # ================================================================
    style.configure(
        'TCombobox',
        fieldbackground=get_color('input_bg'),
        background=get_color('input_bg'),
        foreground=get_color('input_text'),
        arrowcolor=get_color('text_secondary'),
        bordercolor=get_color('input_border'),
        lightcolor=get_color('input_bg'),
        darkcolor=get_color('input_bg'),
        font=get_font_tuple('input'),
        padding=(8, 4),
    )
    
    style.map(
        'TCombobox',
        fieldbackground=[
            ('readonly', get_color('input_bg')),
            ('disabled', get_color('input_disabled_bg')),
        ],
        foreground=[
            ('disabled', get_color('input_disabled_text')),
        ],
        bordercolor=[
            ('focus', get_color('input_border_focus')),
        ],
        arrowcolor=[
            ('active', get_color('primary')),
        ],
    )
    
    # Combobox dropdown
    root.option_add('*TCombobox*Listbox.background', get_color('bg_surface_alt'))
    root.option_add('*TCombobox*Listbox.foreground', get_color('text_primary'))
    root.option_add('*TCombobox*Listbox.selectBackground', get_color('primary'))
    root.option_add('*TCombobox*Listbox.selectForeground', get_color('primary_text'))
    root.option_add('*TCombobox*Listbox.font', get_font_tuple('input'))
    
    # ================================================================
    # TTK TREEVIEW (TABLE)
    # ================================================================
    style.configure(
        'Treeview',
        background=get_color('table_row_bg'),
        foreground=get_color('text_primary'),
        fieldbackground=get_color('table_row_bg'),
        font=get_font_tuple('table'),
        rowheight=28,
        borderwidth=0,
        relief='flat',
    )
    
    style.map(
        'Treeview',
        background=[
            ('selected', get_color('table_row_selected')),
            ('!selected', get_color('table_row_bg')),
        ],
        foreground=[
            ('selected', get_color('text_primary')),
        ],
    )
    
    style.configure(
        'Treeview.Heading',
        background=get_color('table_header_bg'),
        foreground=get_color('table_header_text'),
        font=get_font_tuple('table_header'),
        borderwidth=0,
        relief='flat',
        padding=(8, 6),
    )
    
    style.map(
        'Treeview.Heading',
        background=[
            ('active', get_color('bg_hover')),
        ],
        foreground=[
            ('active', get_color('text_primary')),
        ],
    )
    
    # ================================================================
    # TTK SCROLLBAR
    # ================================================================
    style.configure(
        'Vertical.TScrollbar',
        background=get_color('scrollbar_thumb'),
        troughcolor=get_color('scrollbar_track'),
        bordercolor=get_color('scrollbar_track'),
        arrowcolor=get_color('text_secondary'),
        gripcount=0,
        relief='flat',
        borderwidth=0,
    )
    
    style.map(
        'Vertical.TScrollbar',
        background=[
            ('active', get_color('scrollbar_thumb_hover')),
        ],
    )
    
    style.configure(
        'Horizontal.TScrollbar',
        background=get_color('scrollbar_thumb'),
        troughcolor=get_color('scrollbar_track'),
        bordercolor=get_color('scrollbar_track'),
        arrowcolor=get_color('text_secondary'),
        gripcount=0,
        relief='flat',
        borderwidth=0,
    )
    
    style.map(
        'Horizontal.TScrollbar',
        background=[
            ('active', get_color('scrollbar_thumb_hover')),
        ],
    )
    
    # ================================================================
    # TTK NOTEBOOK (TABS)
    # ================================================================
    style.configure(
        'TNotebook',
        background=get_color('bg_app'),
        borderwidth=0,
        tabmargins=(0, 0, 0, 0),
    )
    
    style.configure(
        'TNotebook.Tab',
        background=get_color('bg_surface'),
        foreground=get_color('text_secondary'),
        font=get_font_tuple('body'),
        padding=(16, 8),
        borderwidth=0,
    )
    
    style.map(
        'TNotebook.Tab',
        background=[
            ('selected', get_color('bg_surface_alt')),
            ('active', get_color('bg_hover')),
        ],
        foreground=[
            ('selected', get_color('text_primary')),
            ('active', get_color('text_primary')),
        ],
    )
    
    # ================================================================
    # TTK PROGRESSBAR
    # ================================================================
    style.configure(
        'TProgressbar',
        background=get_color('primary'),
        troughcolor=get_color('bg_surface'),
        bordercolor=get_color('bg_surface'),
        lightcolor=get_color('primary'),
        darkcolor=get_color('primary'),
        borderwidth=0,
    )
    
    # ================================================================
    # TTK SEPARATOR
    # ================================================================
    style.configure(
        'TSeparator',
        background=get_color('border_default'),
    )
    
    # ================================================================
    # TTK CHECKBUTTON
    # ================================================================
    style.configure(
        'TCheckbutton',
        background=get_color('bg_app'),
        foreground=get_color('text_primary'),
        font=get_font_tuple('body'),
        focuscolor='none',
        indicatorcolor=get_color('input_bg'),
    )
    
    style.map(
        'TCheckbutton',
        background=[
            ('active', get_color('bg_app')),
        ],
        indicatorcolor=[
            ('selected', get_color('primary')),
            ('!selected', get_color('input_bg')),
        ],
    )
    
    # ================================================================
    # TTK RADIOBUTTON
    # ================================================================
    style.configure(
        'TRadiobutton',
        background=get_color('bg_app'),
        foreground=get_color('text_primary'),
        font=get_font_tuple('body'),
        focuscolor='none',
    )
    
    # ================================================================
    # TTK LABELFRAME
    # ================================================================
    style.configure(
        'TLabelframe',
        background=get_color('bg_app'),
        bordercolor=get_color('border_default'),
        relief='solid',
        borderwidth=1,
    )
    
    style.configure(
        'TLabelframe.Label',
        background=get_color('bg_app'),
        foreground=get_color('text_secondary'),
        font=get_font_tuple('body_bold'),
    )
    
    # ================================================================
    # TTK PANEDWINDOW
    # ================================================================
    style.configure(
        'TPanedwindow',
        background=get_color('bg_app'),
    )


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['apply_ttk_styles']