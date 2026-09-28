# gui/theme/typography.py
"""
سیستم تایپوگرافی - Control System Manager
"""

# ================================================================
# FONT FAMILIES
# ================================================================

FONT_FAMILIES = {
    'primary':   'Segoe UI',    # ویندوز
    'mono':      'Consolas',    # کد و تگ
    'fallback':  'Arial',       # جایگزین
}


# ================================================================
# FONT SIZES
# ================================================================

FONT_SIZES = {
    'display':   24,    # عنوان اصلی
    'h1':        18,    # عنوان صفحه
    'h2':        15,    # عنوان بخش
    'h3':        13,    # عنوان زیربخش
    'body':      11,    # متن اصلی
    'body_lg':   12,    # متن اصلی بزرگ
    'small':     10,    # متن فرعی
    'caption':    9,    # توضیحات
    'micro':      8,    # ریز
    'button':    11,    # دکمه‌ها
    'input':     11,    # ورودی‌ها
    'table':     10,    # جدول
    'mono':      11,    # کد
}


# ================================================================
# FONT WEIGHTS
# ================================================================

FONT_WEIGHTS = {
    'normal':    'normal',
    'bold':      'bold',
    # Tkinter از medium/semibold پشتیبانی نمی‌کند
}


# ================================================================
# TEXT STYLES (آماده استفاده)
# ================================================================

TEXT_STYLES = {
    # ═══ Titles ═══
    'display': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['display'],
        'weight': FONT_WEIGHTS['bold'],
    },
    'h1': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['h1'],
        'weight': FONT_WEIGHTS['bold'],
    },
    'h2': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['h2'],
        'weight': FONT_WEIGHTS['bold'],
    },
    'h3': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['h3'],
        'weight': FONT_WEIGHTS['bold'],
    },
    
    # ═══ Body ═══
    'body': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['body'],
        'weight': FONT_WEIGHTS['normal'],
    },
    'body_bold': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['body'],
        'weight': FONT_WEIGHTS['bold'],
    },
    'body_lg': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['body_lg'],
        'weight': FONT_WEIGHTS['normal'],
    },
    
    # ═══ Small ═══
    'small': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['small'],
        'weight': FONT_WEIGHTS['normal'],
    },
    'caption': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['caption'],
        'weight': FONT_WEIGHTS['normal'],
    },
    'micro': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['micro'],
        'weight': FONT_WEIGHTS['normal'],
    },
    
    # ═══ Components ═══
    'button': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['button'],
        'weight': FONT_WEIGHTS['bold'],
    },
    'input': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['input'],
        'weight': FONT_WEIGHTS['normal'],
    },
    'table': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['table'],
        'weight': FONT_WEIGHTS['normal'],
    },
    'table_header': {
        'family': FONT_FAMILIES['primary'],
        'size':   FONT_SIZES['table'],
        'weight': FONT_WEIGHTS['bold'],
    },
    
    # ═══ Mono ═══
    'mono': {
        'family': FONT_FAMILIES['mono'],
        'size':   FONT_SIZES['mono'],
        'weight': FONT_WEIGHTS['normal'],
    },
}


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def get_font_tuple(style_name: str):
    """
    دریافت tuple فونت برای استفاده در Tkinter
    
    Returns:
        tuple: (family, size, weight) یا (family, size)
    """
    style = TEXT_STYLES.get(style_name, TEXT_STYLES['body'])
    
    if style['weight'] == 'normal':
        return (style['family'], style['size'])
    return (style['family'], style['size'], style['weight'])


def get_font(style_name: str) -> dict:
    """دریافت دیکشنری فونت"""
    return TEXT_STYLES.get(style_name, TEXT_STYLES['body']).copy()


def font(style_name: str = 'body'):
    """میانبر برای دریافت tuple فونت"""
    return get_font_tuple(style_name)


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'FONT_FAMILIES',
    'FONT_SIZES',
    'FONT_WEIGHTS',
    'TEXT_STYLES',
    'get_font_tuple',
    'get_font',
    'font',
]