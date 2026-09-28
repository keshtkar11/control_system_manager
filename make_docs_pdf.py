# make_docs_pdf.py
"""
ساخت PDF از راهنمای پروژه — با پشتیبانی کامل فارسی
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# ✅ نصب: pip install reportlab arabic-reshaper python-bidi

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak,
        Table, TableStyle, Preformatted
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("❌ reportlab نصب نیست:")
    print("   pip install reportlab")
    sys.exit(1)

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False
    print("⚠️ کتابخانه‌های فارسی نصب نیستند!")
    print("   pip install arabic-reshaper python-bidi")
    print()


# ============================================================
# مسیرها
# ============================================================
PROJECT_ROOT = Path(__file__).parent
FONTS_DIR = PROJECT_ROOT / "resources" / "fonts"
OUTPUT_PDF = PROJECT_ROOT / "ControlSystemManager_Docs.pdf"


# ============================================================
# تبدیل متن فارسی برای PDF
# ============================================================

def fa(text: str) -> str:
    """
    آماده‌سازی متن فارسی برای reportlab
    
    reportlab از RTL پشتیبانی نمی‌کند، پس متن را با
    arabic_reshaper و python-bidi اصلاح می‌کنیم.
    """
    if not text:
        return text
    
    if not HAS_BIDI:
        return text
    
    try:
        # ===== reshape =====
        reshaped = arabic_reshaper.reshape(text)
        # ===== RTL =====
        bidi_text = get_display(reshaped)
        return bidi_text
    except Exception:
        return text


# ============================================================
# ثبت فونت‌ها
# ============================================================

def register_fonts():
    """ثبت فونت‌های فارسی"""
    
    fonts = {
        'Tahoma': FONTS_DIR / 'tahoma.ttf',
        'BNazanin': FONTS_DIR / 'BNazanin.ttf',
        'BLotus': FONTS_DIR / 'BLotus.ttf',
        'BMitra': FONTS_DIR / 'BMitra.ttf',
    }
    
    registered = []
    
    for name, path in fonts.items():
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(path)))
                registered.append(name)
                print(f"✅ فونت ثبت شد: {name}")
            except Exception as e:
                print(f"⚠️ فونت {name}: {e}")
    
    # ===== انتخاب فونت =====
    # Tahoma بهترین گزینه برای فارسی
    if 'Tahoma' in registered:
        return 'Tahoma'
    elif registered:
        return registered[0]
    return 'Helvetica'


# ============================================================
# استایل‌ها
# ============================================================

def create_styles(font_name='Helvetica'):
    """ساخت استایل‌های PDF"""
    
    styles = getSampleStyleSheet()
    
    COLOR_DARK = HexColor('#1F3A5F')
    COLOR_MEDIUM = HexColor('#2C3E50')
    COLOR_ACCENT = HexColor('#3498DB')
    COLOR_CODE_BG = HexColor('#F4F4F4')
    
    custom_styles = {
        'Title': ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=28,
            textColor=COLOR_DARK,
            alignment=TA_CENTER,
            spaceAfter=30,
        ),
        'H1': ParagraphStyle(
            'CustomH1',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=20,
            textColor=COLOR_DARK,
            spaceBefore=20,
            spaceAfter=15,
            alignment=TA_RIGHT,
        ),
        'H3': ParagraphStyle(
            'CustomH3',
            parent=styles['Heading3'],
            fontName=font_name,
            fontSize=13,
            textColor=COLOR_ACCENT,
            spaceBefore=10,
            spaceAfter=8,
            alignment=TA_RIGHT,
        ),
        'Body': ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontName=font_name,
            fontSize=10,
            textColor=black,
            leading=16,
            spaceAfter=6,
            alignment=TA_RIGHT,
        ),
        'Code': ParagraphStyle(
            'CustomCode',
            parent=styles['Code'],
            fontName='Courier',
            fontSize=8,
            textColor=HexColor('#333333'),
            backColor=COLOR_CODE_BG,
            borderPadding=6,
            leading=12,
            leftIndent=10,
            rightIndent=10,
            alignment=TA_LEFT,   # ← کد چپ‌چین
        ),
    }
    
    return custom_styles


# ============================================================
# ساخت PDF
# ============================================================

def create_pdf():
    """ساخت فایل PDF"""
    
    print("\n" + "=" * 70)
    print("📄 ساخت PDF راهنما")
    print("=" * 70)
    
    if not HAS_BIDI:
        print("⚠️ بدون پشتیبانی فارسی، متن‌ها درست نمایش داده نمی‌شوند.")
        print("   برای رفع: pip install arabic-reshaper python-bidi\n")
    
    # ===== ثبت فونت =====
    font_name = register_fonts()
    styles = create_styles(font_name)
    
    # ===== Document =====
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Control System Manager - Documentation",
        author="Vahhaj Sanat Energy Co.",
    )
    
    story = []
    
    # ============================================================
    # صفحه عنوان
    # ============================================================
    story.append(Spacer(1, 3 * cm))
    
    story.append(Paragraph(
        fa("🏗️ Control System Manager"),
        styles['Title']
    ))
    
    story.append(Spacer(1, 0.5 * cm))
    
    story.append(Paragraph(
        fa("راهنمای کامل معماری و گسترش"),
        ParagraphStyle(
            'Subtitle',
            fontName=font_name,
            fontSize=16,
            alignment=TA_CENTER,
            textColor=HexColor('#7F8C8D'),
        )
    ))
    
    story.append(Spacer(1, 2 * cm))
    
    story.append(Paragraph(
        fa("نسخه 1.0"),
        ParagraphStyle(
            'Version',
            fontName=font_name,
            fontSize=12,
            alignment=TA_CENTER,
        )
    ))
    
    story.append(Paragraph(
        f"تاریخ: {datetime.now().strftime('%Y/%m/%d')}",
        ParagraphStyle(
            'Date',
            fontName=font_name,
            fontSize=10,
            alignment=TA_CENTER,
            textColor=HexColor('#7F8C8D'),
        )
    ))
    
    story.append(Spacer(1, 3 * cm))
    
    story.append(Paragraph(
        "Vahhaj Sanat Energy Co.",
        ParagraphStyle(
            'Company',
            fontName=font_name,
            fontSize=14,
            alignment=TA_CENTER,
            textColor=HexColor('#1F3A5F'),
        )
    ))
    
    story.append(PageBreak())
    
    # ============================================================
    # فهرست مطالب
    # ============================================================
    story.append(Paragraph(fa("📑 فهرست مطالب"), styles['H1']))
    story.append(Spacer(1, 0.3 * cm))
    
    toc_items = [
        "1. نمای کلی معماری",
        "2. ریشه پروژه (Root Files)",
        "3. core/ — منطق تجاری",
        "4. ai/ — هوش مصنوعی",
        "5. gui/ — رابط کاربری",
        "6. export/ — خروجی‌ها",
        "7. utils/ — توابع کمکی",
        "8. resources/ — منابع",
        "9. data/ و tests/",
        "10. ۵ قانون طلایی گسترش",
        "11. چک‌لیست تغییرات",
        "12. راهنمای سریع گسترش",
    ]
    
    for item in toc_items:
        story.append(Paragraph(
            fa(f"• {item}"),
            styles['Body']
        ))
    
    story.append(PageBreak())
    
    # ============================================================
    # 1. نمای کلی
    # ============================================================
    story.append(Paragraph(fa("1️⃣ نمای کلی معماری"), styles['H1']))
    
    story.append(Paragraph(
        fa("معماری این برنامه از ۵ لایه اصلی تشکیل شده است:"),
        styles['Body']
    ))
    
    story.append(Spacer(1, 0.3 * cm))
    
    # ===== جدول لایه‌ها =====
    layers_data = [
        [fa("لایه"), fa("وابستگی‌ها"), fa("هدف")],
        ["core/", "sqlite3, dataclasses", fa("منطق تجاری")],
        ["ai/", "core + openai", fa("هوش مصنوعی")],
        ["gui/", "core + ai + tkinter", fa("رابط کاربری")],
        ["export/", "core + docx + reportlab", fa("خروجی‌ها")],
        ["utils/", "استاندارد", fa("کمکی")],
    ]
    
    layers_table = Table(layers_data, colWidths=[3 * cm, 6 * cm, 6 * cm])
    layers_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#F8F9FA')),
    ]))
    
    story.append(layers_table)
    
    story.append(Spacer(1, 0.5 * cm))
    
    story.append(Paragraph(
        fa("⚠️ قانون مهم: core/ هرگز نباید به gui/ وابسته باشد."),
        styles['Body']
    ))
    
    story.append(PageBreak())
    
    # ============================================================
    # 2. ریشه پروژه
    # ============================================================
    story.append(Paragraph(fa("2️⃣ ریشه پروژه (Root Files)"), styles['H1']))
    
    root_files = [
        [fa("فایل"), fa("کاربرد")],
        ["main.py", fa("نقطه ورود برنامه")],
        ["main.spec", fa("تنظیمات PyInstaller")],
        ["requirements.txt", fa("لیست پکیج‌ها")],
        ["README.md", fa("مستندات توسعه‌دهنده")],
        ["Help.txt", fa("راهنمای کاربر")],
        ["analyze_project.py", fa("تست Learning Engine")],
    ]
    
    root_table = Table(root_files, colWidths=[6 * cm, 9 * cm])
    root_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
    ]))
    
    story.append(root_table)
    story.append(PageBreak())
    
    # ============================================================
    # 3. core/
    # ============================================================
    story.append(Paragraph(fa("3️⃣ core/ — منطق تجاری"), styles['H1']))
    
    story.append(Paragraph(
        fa("قلب برنامه. بدون وابستگی به GUI."),
        styles['Body']
    ))
    
    story.append(Spacer(1, 0.3 * cm))
    
    core_files = [
        [fa("فایل"), fa("کاربرد")],
        ["models.py", fa("کلاس‌های اصلی")],
        ["database.py", fa("SQLite CRUD")],
        ["constants.py", fa("ثابت‌ها و برچسب‌ها")],
        ["attachments.py", fa("مدیریت ضمیمه‌ها")],
        ["component_manager.py", fa("کامپوننت سفارشی")],
        ["template_manager.py", fa("مدیریت قالب‌ها")],
        ["history.py", "Undo/Redo"],
        ["validators.py", fa("اعتبارسنجی")],
        ["valve_constants.py", fa("جداول شیرها")],
        ["valve_calculator.py", fa("محاسبات شیر")],
        ["steam_kv_calculator.py", "Kv بخار (IEC 60534)"],
    ]
    
    core_table = Table(core_files, colWidths=[6 * cm, 9 * cm])
    core_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
    ]))
    
    story.append(core_table)
    story.append(PageBreak())
    
    # ============================================================
    # 4. ai/
    # ============================================================
    story.append(Paragraph(fa("4️⃣ ai/ — هوش مصنوعی"), styles['H1']))
    
    ai_files = [
        [fa("فایل"), fa("کاربرد")],
        ["ai_assistant.py", fa("دستیار گفتگو")],
        ["deepseek_client.py", fa("کلاینت OpenAI")],
        ["learning_engine.py", fa("یادگیری از پروژه‌ها")],
        ["local_proposal_generator.py", fa("پروپوزال محلی")],
        ["project_query_engine.py", fa("پاسخ به سوالات")],
        ["query_templates.py", fa("الگوهای intent")],
        ["proposal_section_detector.py", fa("تشخیص نوع سکشن")],
        ["proposal_importer.py", fa("import از Word")],
        ["pattern_extractor.py", fa("استخراج الگو")],
        ["pattern_matcher.py", fa("تطبیق الگو")],
        ["project_matcher.py", fa("تطبیق نام پروژه")],
    ]
    
    ai_table = Table(ai_files, colWidths=[6 * cm, 9 * cm])
    ai_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
    ]))
    
    story.append(ai_table)
    story.append(PageBreak())
    
    # ============================================================
    # 5. gui/
    # ============================================================
    story.append(Paragraph(fa("5️⃣ gui/ — رابط کاربری"), styles['H1']))
    
    gui_files = [
        [fa("فایل"), fa("کاربرد")],
        ["main_window.py", fa("پنجره اصلی")],
        ["ai_settings_dialog.py", fa("تنظیمات AI")],
        ["dialogs.py", fa("دیالوگ‌های عمومی")],
        ["attachments_panel.py", fa("پنل ضمیمه‌ها")],
        ["component_dialogs.py", fa("دیالوگ کامپوننت")],
        ["components/", fa("کامپوننت‌های UI")],
        ["layout/", fa("چیدمان")],
        ["theme/", fa("ظاهر و رنگ")],
        ["valves/valve_dialog.py", fa("دیالوگ شیر")],
        ["valves/valves_panel.py", fa("پنل شیرها")],
    ]
    
    gui_table = Table(gui_files, colWidths=[6 * cm, 9 * cm])
    gui_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
    ]))
    
    story.append(gui_table)
    story.append(PageBreak())
    
    # ============================================================
    # 6. export/
    # ============================================================
    story.append(Paragraph(fa("6️⃣ export/ — خروجی‌ها"), styles['H1']))
    
    export_files = [
        [fa("فایل"), fa("فرمت"), fa("کاربرد")],
        ["excel_exporter.py", ".xlsx", fa("Excel عمومی")],
        ["valves_excel_exporter.py", ".xlsx", fa("Excel شیرها")],
        ["pdf_exporter.py", ".pdf", fa("PDF عمومی")],
        ["pdf_proposal_exporter.py", ".pdf", fa("PDF پروپوزال")],
        ["word_proposal_exporter.py", ".docx", fa("Word پروپوزال")],
        ["report_generator.py", ".docx", fa("گزارش")],
    ]
    
    export_table = Table(export_files, colWidths=[6 * cm, 2 * cm, 7 * cm])
    export_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
    ]))
    
    story.append(export_table)
    story.append(PageBreak())
    
    # ============================================================
    # 7. utils/
    # ============================================================
    story.append(Paragraph(fa("7️⃣ utils/ — توابع کمکی"), styles['H1']))
    
    utils_files = [
        [fa("فایل"), fa("کاربرد")],
        ["config_manager.py", "ConfigManager (singleton)"],
        ["paths.py", fa("مسیرهای برنامه")],
        ["helpers.py", fa("توابع عمومی")],
        ["logger.py", fa("تنظیمات logging")],
    ]
    
    utils_table = Table(utils_files, colWidths=[6 * cm, 9 * cm])
    utils_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
    ]))
    
    story.append(utils_table)
    
    story.append(Spacer(1, 0.5 * cm))
    
    story.append(Paragraph(fa("💡 استفاده:"), styles['H3']))
    
    code_example = """from utils.config_manager import get_config
config = get_config()
api_key = config.get('api_key')
config.set('api_key', 'new_key')
config.save()"""
    
    story.append(Preformatted(code_example, styles['Code']))
    
    story.append(PageBreak())
    
    # ============================================================
    # 8. resources/
    # ============================================================
    story.append(Paragraph(fa("8️⃣ resources/ — منابع"), styles['H1']))
    
    story.append(Paragraph(
        fa("resources/fonts/ — فونت‌های فارسی و انگلیسی"),
        styles['Body']
    ))
    
    fonts_data = [
        [fa("فونت"), fa("کاربرد")],
        ["BNazanin.ttf", fa("متن عمومی")],
        ["BLotus.ttf", fa("تیتر")],
        ["BMitra.ttf", fa("متن")],
        ["tahoma.ttf", fa("سیستم")],
        ["arial.ttf", fa("انگلیسی")],
    ]
    
    fonts_table = Table(fonts_data, colWidths=[6 * cm, 9 * cm])
    fonts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
    ]))
    
    story.append(fonts_table)
    story.append(PageBreak())
    
    # ============================================================
    # 10. ۵ قانون
    # ============================================================
    story.append(Paragraph(fa("🔟 ۵ قانون طلایی گسترش"), styles['H1']))
    
    rules = [
        ("قانون ۱: جدا نگه داشتن لایه‌ها",
         "core/ هرگز نباید به gui/ وابسته باشد."),
        ("قانون ۲: استفاده از logger",
         "import logging; logger = logging.getLogger(__name__)"),
        ("قانون ۳: Exception Handling",
         "همیشه try/except با logging داشته باشید."),
        ("قانون ۴: Type Hints",
         "از typing استفاده کنید: Optional, List, Dict, Any"),
        ("قانون ۵: تست قبل از Build",
         "python test_full_system.py && python -m PyInstaller main.spec"),
    ]
    
    for title, content in rules:
        story.append(Paragraph(fa(title), styles['H3']))
        story.append(Paragraph(fa(content), styles['Body']))
        story.append(Spacer(1, 0.3 * cm))
    
    story.append(PageBreak())
    
    # ============================================================
    # 12. راهنمای سریع
    # ============================================================
    story.append(Paragraph(fa("🎯 راهنمای سریع گسترش"), styles['H1']))
    
    scenarios = [
        ("سناریو ۱: افزودن کامپوننت جدید",
         "1. core/constants.py\n2. core/models.py"),
        ("سناریو ۲: افزودن سکشن به پروپوزال",
         "1. ai/proposal_images/new.png\n2. ai/proposal_templates/new.txt\n"
         "3. local_proposal_generator.py\n4. word_proposal_exporter.py"),
        ("سناریو ۳: افزودن دستور AI",
         "1. ai_assistant.py → _process_message_logic"),
        ("سناریو ۴: افزودن نوع شیر جدید",
         "1. valve_constants.py\n2. valve_calculator.py\n3. valve_dialog.py"),
        ("سناریو ۵: افزودن خروجی جدید",
         "1. export/new_exporter.py\n2. gui/ai_assistant.py"),
    ]
    
    for title, steps in scenarios:
        story.append(Paragraph(fa(title), styles['H3']))
        story.append(Preformatted(steps, styles['Code']))
        story.append(Spacer(1, 0.2 * cm))
    
    story.append(PageBreak())
    
    # ============================================================
    # پایان
    # ============================================================
    story.append(Spacer(1, 3 * cm))
    
    story.append(Paragraph(
        fa("✅ پایان راهنما"),
        styles['Title']
    ))
    
    story.append(Spacer(1, 1 * cm))
    
    story.append(Paragraph(
        fa(f"نسخه 1.0 — {datetime.now().strftime('%Y/%m/%d')}"),
        ParagraphStyle(
            'EndVersion',
            fontName=font_name,
            fontSize=12,
            alignment=TA_CENTER,
        )
    ))
    
    story.append(Spacer(1, 1 * cm))
    
    story.append(Paragraph(
        "Vahhaj Sanat Energy Co.",
        ParagraphStyle(
            'EndCompany',
            fontName=font_name,
            fontSize=14,
            alignment=TA_CENTER,
            textColor=HexColor('#1F3A5F'),
        )
    ))
    
    # ============================================================
    # Build
    # ============================================================
    try:
        doc.build(story)
        
        print(f"\n✅ PDF ساخته شد: {OUTPUT_PDF}")
        print(f"📏 حجم: {OUTPUT_PDF.stat().st_size / 1024:.1f} KB")
        
        return True
    except Exception as e:
        print(f"\n❌ خطا در ساخت PDF: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = create_pdf()
    
    if success:
        import os
        if os.name == 'nt':
            try:
                os.startfile(str(OUTPUT_PDF))
            except Exception:
                pass