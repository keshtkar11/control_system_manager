# export/pdf_proposal_exporter.py
"""
تولید پروپوزال PDF با تصاویر — با پشتیبانی کامل فارسی

نسخه 2.0:
- فونت فارسی
- RTL کامل
- arabic-reshaper + python-bidi
"""

import os
import re
from datetime import datetime
import logging

from utils.paths import get_resource_path
from utils.pdf_helpers import fa, fa_paragraph, fa_mixed, fa_bold

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)


class PDFProposalExporter:
    """تولید پروپوزال PDF با تصاویر و پشتیبانی فارسی"""
    
    def __init__(self, images_dir: str = None):
        """
        Args:
            images_dir: مسیر تصاویر
        """
        
        if images_dir is None:
            self.images_dir = get_resource_path("ai", "proposal_images")
        else:
            self.images_dir = os.path.abspath(images_dir)
        
        self.section_images = {
            "boiler": "boiler.png",
            "chiller": "chiller.png",
            "primary_loop": "primary_loop.png",
            "secondary_loop": "secondary_loop.png",
            "dhw": "dhw.png",
            "ahu": "ahu.png",
            "booster": "booster_pump.png",
            "expansion": "expansion_tank.png",
            "hardware": "hardware.png",
            "panel": "Panel.png",
            
            # ✅ جدید: سکشن‌های جدید
            "mechanical_room": "mechanical_room.png",
            "exhaust_fan": "exhaust_fan.png",
            "building": "building.png",
            "fan": "fan.png",
            "pump": "pump.png",
        }
        
        # ✅ جدید: ثبت فونت فارسی
        self.persian_font = "Helvetica"
        self._setup_fonts()
        
        logger.info(f"📁 Proposal images: {self.images_dir}")
        logger.info(f"🔤 Persian font: {self.persian_font}")
    
    # ============================================================
    # FONT SETUP
    # ============================================================
    
    def _setup_fonts(self):
        """ثبت فونت فارسی"""
        try:
            # ===== مسیرهای ممکن =====
            font_paths = [
                get_resource_path("resources", "fonts", "tahoma.ttf"),
                get_resource_path("resources", "fonts", "essential", "tahoma.ttf"),
                get_resource_path("resources", "fonts", "BNazanin.ttf"),
                get_resource_path("resources", "fonts", "essential", "BNazanin.ttf"),
            ]
            
            for font_path in font_paths:
                if font_path.exists():
                    pdfmetrics.registerFont(TTFont('PersianFont', str(font_path)))
                    self.persian_font = "PersianFont"
                    logger.info(f"✅ Persian font loaded: {font_path.name}")
                    return
            
            logger.warning("⚠️ No Persian font found, using Helvetica")
            self.persian_font = "Helvetica"
        except Exception as e:
            logger.error(f"Font setup failed: {e}")
            self.persian_font = "Helvetica"
    
    # ============================================================
    # SECTION DETECTION
    # ============================================================
    
    def _detect_section(self, text: str) -> str:
        """تشخیص نوع بخش"""
        text_lower = text.lower()
        
        keywords = {
            "boiler": ["بویلر", "دیگ", "boiler"],
            "chiller": ["چیلر", "chiller"],
            "primary_loop": ["مدار اولیه", "primary loop"],
            "secondary_loop": ["مدار ثانویه", "secondary loop"],
            "dhw": ["آبگرم مصرفی", "dhw"],
            "ahu": ["هواساز", "ahu", "icu", "cath lab"],
            "booster": ["بوستر", "booster"],
            "expansion": ["انبساط", "expansion"],
            "hardware": ["سخت‌افزار", "سخت افزار", "controller", "cbx", "fbx"],
            "panel": ["تابلو", "panel", "پنل"],
            "mechanical_room": ["موتورخانه", "mechanical room"],
            "exhaust_fan": ["فن تخلیه", "exhaust"],
            "building": ["ساختمان", "building", "floor", "طبقه"],
        }
        
        for section, kws in keywords.items():
            for kw in kws:
                if kw in text_lower:
                    return section
        
        return None
    
    # ============================================================
    # BUILD STYLES
    # ============================================================
    
    def _build_styles(self):
        """ساخت استایل‌های PDF"""
        styles = getSampleStyleSheet()
        
        FONT = self.persian_font
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            fontName=FONT,
            fontSize=18,
            textColor=HexColor('#1F3A5F'),
            spaceAfter=12,
            leading=24,
        )
        
        h1_style = ParagraphStyle(
            'CustomH1',
            parent=styles['Heading1'],
            alignment=TA_RIGHT,
            fontName=FONT,
            fontSize=15,
            textColor=HexColor('#1F3A5F'),
            spaceAfter=8,
            leading=22,
        )
        
        h2_style = ParagraphStyle(
            'CustomH2',
            parent=styles['Heading2'],
            alignment=TA_RIGHT,
            fontName=FONT,
            fontSize=13,
            textColor=HexColor('#2C3E50'),
            spaceAfter=6,
            leading=20,
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            alignment=TA_RIGHT,
            fontName=FONT,
            fontSize=10,
            leading=18,
            spaceAfter=6,
        )
        
        table_style = ParagraphStyle(
            'TableStyle',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontName=FONT,
            fontSize=8,
            leading=12,
        )
        
        return {
            'title': title_style,
            'h1': h1_style,
            'h2': h2_style,
            'body': body_style,
            'table': table_style,
        }
    
    # ============================================================
    # BUILD TABLE
    # ============================================================
    
    def _build_table(self, table_lines, styles):
        """ساخت جدول از خطوط Markdown"""
        if len(table_lines) < 2:
            return None
        
        data = []
        for tl in table_lines:
            # ===== حذف خط جداکننده =====
            if re.match(r'^\|[\s\-:|]+\|$', tl):
                continue
            
            cells = [c.strip() for c in tl.strip('|').split('|')]
            
            # ===== reshape هر سلول =====
            cells = [fa(cell) for cell in cells]
            data.append(cells)
        
        if not data:
            return None
        
        try:
            t = Table(data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1F3A5F')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#BDC3C7')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [
                    HexColor('#FFFFFF'),
                    HexColor('#F8F9FA'),
                ]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            return t
        except Exception as e:
            logger.error(f"Table build failed: {e}")
            return None
    
    # ============================================================
    # BUILD IMAGE
    # ============================================================
    
    def _build_image(self, section_type: str, image_added: set):
        """ساخت تصویر سکشن"""
        if section_type in image_added:
            return None
        
        image_filename = self.section_images.get(section_type)
        if not image_filename:
            return None
        
        img_path = self.images_dir / image_filename
        
        if not img_path.exists():
            logger.debug(f"Image not found: {img_path}")
            return None
        
        try:
            img = Image(str(img_path), width=12 * cm, height=8 * cm)
            img.hAlign = 'CENTER'
            image_added.add(section_type)
            logger.debug(f"✅ Image added: {img_path.name}")
            return img
        except Exception as e:
            logger.error(f"Error adding image: {e}")
            return None
    
    # ============================================================
    # MAIN EXPORT
    # ============================================================
    
    def export(self, content: str, output_path: str,
               project_name: str = "Project") -> bool:
        """تولید فایل PDF"""
        try:
            # ===== ساخت Document =====
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm,
                title=f"Proposal - {project_name}",
            )
            
            story = []
            styles = self._build_styles()
            
            # ===== تجزیه خط به خط =====
            lines = content.split('\n')
            image_added = set()
            
            i = 0
            while i < len(lines):
                line = lines[i].rstrip()
                
                # ===== H1: # =====
                if line.startswith('# '):
                    text = line[2:].strip()
                    story.append(Paragraph(fa(text), styles['title']))
                    story.append(Spacer(1, 0.3*cm))
                
                # ===== H2: ## =====
                elif line.startswith('## '):
                    text = line[3:].strip()
                    story.append(Paragraph(fa(text), styles['h1']))
                    
                    # ===== تصویر =====
                    section = self._detect_section(text)
                    if section:
                        img = self._build_image(section, image_added)
                        if img:
                            story.append(img)
                            story.append(Spacer(1, 0.3*cm))
                
                # ===== H3: ### =====
                elif line.startswith('### '):
                    text = line[4:].strip()
                    story.append(Paragraph(fa(text), styles['h2']))
                
                # ===== List: - یا * =====
                elif line.startswith('* ') or line.startswith('- '):
                    text = line[2:].strip()
                    # ===== حذف bold markers =====
                    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
                    story.append(Paragraph(f"• {fa(text)}", styles['body']))
                
                # ===== Separator =====
                elif line.startswith('---') or line.startswith('==='):
                    story.append(Spacer(1, 0.2*cm))
                
                # ===== Table =====
                elif line.startswith('|'):
                    table_lines = []
                    while i < len(lines) and lines[i].strip().startswith('|'):
                        table_lines.append(lines[i].strip())
                        i += 1
                    i -= 1
                    
                    t = self._build_table(table_lines, styles)
                    if t:
                        story.append(t)
                        story.append(Spacer(1, 0.3*cm))
                
                # ===== متن معمولی =====
                elif line.strip():
                    text = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
                    story.append(Paragraph(fa(text), styles['body']))
                
                i += 1
            
            # ===== ساخت PDF =====
            doc.build(story)
            
            logger.info(f"✅ PDF saved: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error saving PDF: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            return False


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['PDFProposalExporter']