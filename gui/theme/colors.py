# gui/theme/colors.py
"""
پالت رنگ حرفه‌ای - Control System Manager
Design System: Modern Professional Engineering
"""

# ================================================================
# DARK THEME (پیش‌فرض)
# ================================================================

DARK_COLORS = {
    # ═══════════════════════════════════════════════════════════
    # PRIMARY - رنگ اصلی برند
    # ═══════════════════════════════════════════════════════════
    'primary':              '#0A84FF',   # آبی مدرن
    'primary_hover':        '#0A6FD8',
    'primary_active':       '#085BB0',
    'primary_subtle':       '#0F2A4A',   # پس‌زمینه کم‌رنگ
    'primary_text':         '#FFFFFF',   # متن روی primary
    
    # ═══════════════════════════════════════════════════════════
    # BACKGROUNDS - پس‌زمینه‌ها
    # ═══════════════════════════════════════════════════════════
    'bg_app':               '#1A1A1A',   # پس‌زمینه اصلی
    'bg_surface':           '#222222',   # پنل‌ها
    'bg_surface_alt':       '#2A2A2A',   # جدول‌ها
    'bg_surface_elevated':  '#2F2F2F',   # کارت‌ها
    'bg_hover':             '#333333',   # hover
    'bg_active':            '#3D3D3D',   # active
    'bg_selected':          '#0F2A4A',   # انتخاب شده
    'bg_overlay':           '#00000080', # overlay (با شفافیت)
    
    # ═══════════════════════════════════════════════════════════
    # BORDERS - مرزها
    # ═══════════════════════════════════════════════════════════
    'border_default':       '#333333',
    'border_subtle':        '#2A2A2A',
    'border_strong':        '#4A4A4A',
    'border_focus':         '#0A84FF',
    'border_error':         '#FF453A',
    
    # ═══════════════════════════════════════════════════════════
    # TEXT - متون
    # ═══════════════════════════════════════════════════════════
    'text_primary':         '#E8E8E8',   # متن اصلی
    'text_secondary':       '#A0A0A0',   # متن فرعی
    'text_muted':           '#707070',   # متن کم‌اهمیت
    'text_disabled':        '#505050',   # غیرفعال
    'text_inverse':         '#1A1A1A',   # متن روی پس‌زمینه روشن
    'text_link':            '#5AC8FA',   # لینک
    'text_code':            '#7EC8E3',   # کد
    
    # ═══════════════════════════════════════════════════════════
    # STATUS - وضعیت‌ها
    # ═══════════════════════════════════════════════════════════
    'success':              '#30D158',
    'success_hover':        '#28B84C',
    'success_bg':           '#1A3A1F',
    
    'warning':              '#FF9F0A',
    'warning_hover':        '#E68A08',
    'warning_bg':           '#3A2D0F',
    
    'danger':               '#FF453A',
    'danger_hover':         '#E63A30',
    'danger_bg':            '#3A1A1A',
    
    'info':                 '#64D2FF',
    'info_hover':           '#50B8E0',
    'info_bg':              '#0F2A3A',
    
    # ═══════════════════════════════════════════════════════════
    # ACCENT - لهجه‌ها
    # ═══════════════════════════════════════════════════════════
    'accent_orange':        '#FF6B35',   # Action
    'accent_purple':        '#BF5AF2',   # AI
    'accent_cyan':          '#5AC8FA',   # Highlight
    'accent_yellow':        '#FFD60A',   # Warning
    'accent_pink':          '#FF375F',   # Special
    
    # ═══════════════════════════════════════════════════════════
    # SIDEBAR - سایدبار
    # ═══════════════════════════════════════════════════════════
    'sidebar_bg':           '#141414',
    'sidebar_bg_alt':       '#1A1A1A',
    'sidebar_hover':        '#1F1F1F',
    'sidebar_active':       '#2A2A2A',
    'sidebar_border':       '#2A2A2A',
    'sidebar_text':         '#E8E8E8',
    'sidebar_text_muted':   '#808080',
    
    # ═══════════════════════════════════════════════════════════
    # TOOLBAR - نوار ابزار
    # ═══════════════════════════════════════════════════════════
    'toolbar_bg':           '#1E1E1E',
    'toolbar_border':       '#333333',
    'toolbar_text':         '#E8E8E8',
    
    # ═══════════════════════════════════════════════════════════
    # TABLE - جدول
    # ═══════════════════════════════════════════════════════════
    'table_header_bg':      '#2A2A2A',
    'table_header_text':    '#E8E8E8',
    'table_row_bg':         '#1A1A1A',
    'table_row_alt':        '#1F1F1F',
    'table_row_hover':      '#2F2F2F',
    'table_row_selected':   '#0F2A4A',
    'table_border':         '#333333',
    'table_stripe':         '#1F1F1F',
    
    # ═══════════════════════════════════════════════════════════
    # CARD - کارت‌ها
    # ═══════════════════════════════════════════════════════════
    'card_bg':              '#252525',
    'card_border':          '#333333',
    'card_hover':           '#2F2F2F',
    'card_header_bg':       '#2A2A2A',
    
    # ═══════════════════════════════════════════════════════════
    # INPUT - ورودی‌ها
    # ═══════════════════════════════════════════════════════════
    'input_bg':             '#1F1F1F',
    'input_border':         '#333333',
    'input_border_hover':   '#4A4A4A',
    'input_border_focus':   '#0A84FF',
    'input_text':           '#E8E8E8',
    'input_placeholder':    '#707070',
    'input_disabled_bg':    '#1A1A1A',
    'input_disabled_text':  '#505050',
    
    # ═══════════════════════════════════════════════════════════
    # BUTTON - دکمه‌ها
    # ═══════════════════════════════════════════════════════════
    'btn_primary_bg':       '#0A84FF',
    'btn_primary_hover':    '#0A6FD8',
    'btn_primary_active':   '#085BB0',
    'btn_primary_text':     '#FFFFFF',
    
    'btn_secondary_bg':     '#2A2A2A',
    'btn_secondary_hover':  '#333333',
    'btn_secondary_text':   '#E8E8E8',
    'btn_secondary_border': '#3D3D3D',
    
    'btn_ghost_bg':         '#00000000',  # شفاف
    'btn_ghost_hover':      '#2A2A2A',
    'btn_ghost_text':       '#A0A0A0',
    'btn_ghost_text_hover': '#E8E8E8',
    
    'btn_danger_bg':        '#FF453A',
    'btn_danger_hover':     '#E63A30',
    'btn_danger_text':      '#FFFFFF',
    
    # ═══════════════════════════════════════════════════════════
    # SCROLLBAR - اسکرول‌بار
    # ═══════════════════════════════════════════════════════════
    'scrollbar_bg':         '#1A1A1A',
    'scrollbar_track':      '#1F1F1F',
    'scrollbar_thumb':      '#3D3D3D',
    'scrollbar_thumb_hover':'#4A4A4A',
}


# ================================================================
# LIGHT THEME
# ================================================================

LIGHT_COLORS = {
    # ═══ PRIMARY ═══
    'primary':              '#0066CC',
    'primary_hover':        '#0057B0',
    'primary_active':       '#004A99',
    'primary_subtle':       '#E6F0FA',
    'primary_text':         '#FFFFFF',
    
    # ═══ BACKGROUNDS ═══
    'bg_app':               '#F5F5F5',
    'bg_surface':           '#FFFFFF',
    'bg_surface_alt':       '#FAFAFA',
    'bg_surface_elevated':  '#FFFFFF',
    'bg_hover':             '#F0F0F0',
    'bg_active':            '#E5E5E5',
    'bg_selected':          '#E6F0FA',
    'bg_overlay':           '#00000030',
    
    # ═══ BORDERS ═══
    'border_default':       '#E0E0E0',
    'border_subtle':        '#EEEEEE',
    'border_strong':        '#C0C0C0',
    'border_focus':         '#0066CC',
    'border_error':         '#E74C3C',
    
    # ═══ TEXT ═══
    'text_primary':         '#1A1A1A',
    'text_secondary':       '#505050',
    'text_muted':           '#808080',
    'text_disabled':        '#B0B0B0',
    'text_inverse':         '#FFFFFF',
    'text_link':            '#0066CC',
    'text_code':            '#0066CC',
    
    # ═══ STATUS ═══
    'success':              '#28B84C',
    'success_hover':        '#1F9A3E',
    'success_bg':           '#E6F7EC',
    
    'warning':              '#F39C12',
    'warning_hover':        '#D68910',
    'warning_bg':           '#FFF3E0',
    
    'danger':               '#E74C3C',
    'danger_hover':         '#C0392B',
    'danger_bg':            '#FCEAEA',
    
    'info':                 '#3498DB',
    'info_hover':           '#2980B9',
    'info_bg':              '#E8F4FD',
    
    # ═══ ACCENT ═══
    'accent_orange':        '#FF6B35',
    'accent_purple':        '#9B59B6',
    'accent_cyan':          '#3498DB',
    'accent_yellow':        '#F1C40F',
    'accent_pink':          '#E91E63',
    
    # ═══ SIDEBAR ═══
    'sidebar_bg':           '#FFFFFF',
    'sidebar_bg_alt':       '#F8F8F8',
    'sidebar_hover':        '#F0F0F0',
    'sidebar_active':       '#E6F0FA',
    'sidebar_border':       '#E0E0E0',
    'sidebar_text':         '#1A1A1A',
    'sidebar_text_muted':   '#808080',
    
    # ═══ TOOLBAR ═══
    'toolbar_bg':           '#FFFFFF',
    'toolbar_border':       '#E0E0E0',
    'toolbar_text':         '#1A1A1A',
    
    # ═══ TABLE ═══
    'table_header_bg':      '#F0F0F0',
    'table_header_text':    '#1A1A1A',
    'table_row_bg':         '#FFFFFF',
    'table_row_alt':        '#FAFAFA',
    'table_row_hover':      '#F0F0F0',
    'table_row_selected':   '#E6F0FA',
    'table_border':         '#E0E0E0',
    'table_stripe':         '#FAFAFA',
    
    # ═══ CARD ═══
    'card_bg':              '#FFFFFF',
    'card_border':          '#E0E0E0',
    'card_hover':           '#F8F8F8',
    'card_header_bg':       '#F8F8F8',
    
    # ═══ INPUT ═══
    'input_bg':             '#FFFFFF',
    'input_border':         '#D0D0D0',
    'input_border_hover':   '#B0B0B0',
    'input_border_focus':   '#0066CC',
    'input_text':           '#1A1A1A',
    'input_placeholder':    '#A0A0A0',
    'input_disabled_bg':    '#F0F0F0',
    'input_disabled_text':  '#B0B0B0',
    
    # ═══ BUTTON ═══
    'btn_primary_bg':       '#0066CC',
    'btn_primary_hover':    '#0057B0',
    'btn_primary_active':   '#004A99',
    'btn_primary_text':     '#FFFFFF',
    
    'btn_secondary_bg':     '#F0F0F0',
    'btn_secondary_hover':  '#E5E5E5',
    'btn_secondary_text':   '#1A1A1A',
    'btn_secondary_border': '#D0D0D0',
    
    'btn_ghost_bg':         '#00000000',
    'btn_ghost_hover':      '#F0F0F0',
    'btn_ghost_text':       '#606060',
    'btn_ghost_text_hover': '#1A1A1A',
    
    'btn_danger_bg':        '#E74C3C',
    'btn_danger_hover':     '#C0392B',
    'btn_danger_text':      '#FFFFFF',
    
    # ═══ SCROLLBAR ═══
    'scrollbar_bg':         '#F5F5F5',
    'scrollbar_track':      '#EEEEEE',
    'scrollbar_thumb':      '#C0C0C0',
    'scrollbar_thumb_hover':'#A0A0A0',
}


# ================================================================
# CURRENT THEME (متغیر سراسری)
# ================================================================

# این متغیر توسط theme_manager پر می‌شود
CURRENT_COLORS = DARK_COLORS.copy()


def get_color(key: str, default: str = '#000000') -> str:
    """دریافت یک رنگ از تم فعلی"""
    return CURRENT_COLORS.get(key, default)


def set_theme_colors(colors: dict):
    """تنظیم رنگ‌های تم فعلی"""
    global CURRENT_COLORS
    CURRENT_COLORS = colors.copy()