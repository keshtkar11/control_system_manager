# utils/pdf_helpers.py
"""
توابع کمکی برای PDF — پشتیبانی کامل از فارسی

استفاده:
    from utils.pdf_helpers import fa, fa_paragraph, fa_mixed, fa_bold
    
    text = fa("سلام")               # برای متن ساده
    text = fa_paragraph("پروژه")    # برای Paragraph
    text = fa_mixed("پروژه ABC")    # برای ترکیبی
    text = fa_bold("مهم")           # برای bold
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ================================================================
# تلاش برای import کتابخانه‌های فارسی
# ================================================================
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_BIDI = True
    logger.info("✅ arabic-reshaper + python-bidi available")
except ImportError:
    HAS_BIDI = False
    logger.warning(
        "⚠️ arabic-reshaper یا python-bidi نصب نیستند. "
        "برای نصب: pip install arabic-reshaper python-bidi"
    )


# ================================================================
# تبدیل متن فارسی
# ================================================================

def fa(text: Any) -> str:
    """
    آماده‌سازی متن فارسی برای reportlab
    
    Args:
        text: متن (str یا هر چیز دیگر)
    
    Returns:
        متن reshape شده + RTL (اگر کتابخانه موجود باشد)
    """
    if text is None:
        return ''
    
    if not isinstance(text, str):
        text = str(text)
    
    if not text.strip():
        return text
    
    if not HAS_BIDI:
        return text
    
    try:
        # ===== reshape: چسباندن حروف =====
        reshaped = arabic_reshaper.reshape(text)
        
        # ===== bidi: راست‌به‌چپ کردن =====
        bidi_text = get_display(reshaped)
        
        return bidi_text
    except Exception as e:
        logger.debug(f"reshape failed for '{text[:50]}': {e}")
        return text


def fa_mixed(text: Any) -> str:
    """
    برای متن‌های ترکیبی (فارسی + انگلیسی)
    
    مثال: "پروژه Rabbani با 53 دستگاه"
    """
    if text is None:
        return ''
    
    if not isinstance(text, str):
        text = str(text)
    
    if not HAS_BIDI:
        return text
    
    try:
        # ===== اگر هیچ کاراکتر فارسی نیست → برگردان همان‌طور =====
        persian_pattern = re.compile(r'[\u0600-\u06FF\u200c\u200f\u200e]+')
        if not persian_pattern.search(text):
            return text
        
        # ===== reshape کل متن =====
        return fa(text)
    except Exception as e:
        logger.debug(f"fa_mixed failed: {e}")
        return text


def fa_paragraph(text: Any) -> str:
    """
    آماده‌سازی متن برای Paragraph در reportlab
    
    همچنین کاراکترهای خاص XML را escape می‌کند.
    """
    if text is None:
        return ''
    
    if not isinstance(text, str):
        text = str(text)
    
    # ===== escape کاراکترهای XML =====
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    
    # ===== reshape =====
    return fa(text)


def fa_bold(text: Any) -> str:
    """
    متن فارسی با تگ bold برای reportlab
    
    Returns:
        "<b>متن</b>" با reshape
    """
    if text is None:
        return ''
    
    reshaped = fa(text)
    return f"<b>{reshaped}</b>"


def fa_title(text: Any) -> str:
    """
    عنوان فارسی (bold + reshape)
    
    مثال: "## سناریوی کنترلی بویلرها"
    """
    return fa_bold(text)


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'fa',
    'fa_mixed',
    'fa_paragraph',
    'fa_bold',
    'fa_title',
    'HAS_BIDI',
]