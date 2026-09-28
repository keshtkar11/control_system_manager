# export/word_proposal_exporter.py
"""
تولید پروپوزال Word با تصاویر و استایل حرفه‌ای

قابلیت‌ها:
- تبدیل Markdown به Word
- افزودن تصاویر خودکار بر اساس نوع سکشن
- پشتیبانی از قالب‌های اختصاصی
- خروجی: یک فایل کلی + فایل‌های تفکیکی
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from utils.paths import get_resource_path
from core.constants import gregorian_to_jalali
from docx.enum.table import WD_ALIGN_VERTICAL

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

logger = logging.getLogger(__name__)


class WordProposalExporter:
    """تولید پروپوزال Word با تصاویر و استایل حرفه‌ای"""
    
    # ============================================================
    # COMPANY INFO
    # ============================================================
    COMPANY_NAME = "Vahhaj Sanat Energy Co."
    COMPANY_NAME_FA = "وهاج صنعت انرژی"
    DESIGNER_NAME = "Mr. Keshtkar"
    
    # ============================================================
    # SECTION → IMAGE MAPPING
    # ============================================================
    SECTION_IMAGES = {
        'boiler': 'boiler.png',
        'chiller': 'chiller.png',
        'primary_loop': 'primary_loop.png',
        'secondary_loop': 'secondary_loop.png',
        'dhw': 'dhw.png',
        'ahu': 'ahu.png',
        'booster_pump': 'booster_pump.png',
        'expansion_tank': 'expansion_tank.png',
        'hardware': 'hardware.png',
        'panel': 'Panel.png',
        
        # ===== جدید =====
        'mechanical_room': 'mechanical_room.png',
        'exhaust_fan': 'exhaust_fan.png',
        'building': 'building.png',
        'fan': 'fan.png',
        'pump': 'pump.png',
    }
    
    # ============================================================
    # SECTION DETECTION KEYWORDS
    # ============================================================
    SECTION_KEYWORDS = {
        'boiler': ['boiler', 'بویلر', 'دیگ'],
        'chiller': ['chiller', 'چیلر'],
        'primary_loop': ['primary loop', 'مدار اولیه', 'low loss'],
        'secondary_loop': ['secondary loop', 'مدار ثانویه'],
        'dhw': ['dhw', 'آبگرم مصرفی', 'منبع کویلی', 'domestic hot water'],
        'expansion_tank': ['expansion', 'انبساط', 'make-up'],
        'booster_pump': ['booster', 'بوستر'],
        'ahu': ['ahu', 'هواساز', 'air handling'],
        'fancoil': ['fancoil', 'fan coil', 'فن کویل', 'فن‌کویل'],
        'hardware': ['hardware', 'سخت‌افزار', 'controller', 'cbx', 'fbx'],
        'panel': ['panel', 'تابلو', 'پنل'],
        'mechanical_room': ['mechanical', 'موتورخانه', 'plant room'],
        'exhaust_fan': ['exhaust', 'exhuast', 'فن تخلیه'],
        'building': ['floor', 'building', 'طبقه', 'ساختمان'],
        'fan': ['fan', 'فن', 'blower'],
        'pump': ['pump', 'پمپ'],
    }
    
    # ============================================================
    # INIT
    # ============================================================
    
    def __init__(self, images_dir: str = None):
        if images_dir is None:
            self.images_dir = get_resource_path("ai", "proposal_images")
        else:
            self.images_dir = Path(images_dir).resolve()
        
        # ✅ اضافه کنید
        self.fonts_dir = get_resource_path("resources", "fonts")
        
        self.doc = None
        self.image_added_for_section = set()
        
        logger.info(f"📁 Images: {self.images_dir}")
        logger.info(f"📁 Fonts:  {self.fonts_dir}")
    
    # ============================================================
    # FONT HELPER
    # ============================================================
    
    def _set_font(self, run, font_name='Calibri', size=12, bold=False, color=None):
        """تنظیم فونت + RTL برای فارسی"""
        # ===== فونت پایه =====
        run.font.name = font_name
        run.font.size = Pt(size)
        run.font.bold = bold
        if color:
            run.font.color.rgb = color
        
        # ===== پشتیبانی فارسی =====
        r = run._element
        rPr = r.get_or_add_rPr()
        
        # فونت‌ها
        rFonts = OxmlElement('w:rFonts')
        rFonts.set(qn('w:cs'), font_name)
        rFonts.set(qn('w:eastAsia'), font_name)
        rFonts.set(qn('w:ascii'), font_name)
        rFonts.set(qn('w:hAnsi'), font_name)
        rPr.append(rFonts)
        
        # ✅ RTL (راست‌به‌چپ)
        rtl = OxmlElement('w:rtl')
        rPr.append(rtl)
        
        # ✅ Language = Persian
        lang = OxmlElement('w:lang')
        lang.set(qn('w:bidi'), 'fa-IR')
        rPr.append(lang)
    
    # ============================================================
    # HEADING
    # ============================================================
    
    def _add_heading(self, text: str, level: int = 1):
        """افزودن عنوان — وسط‌چین"""
        p = self.doc.add_paragraph()
        
        # ✅ وسط‌چین
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # RTL
        pPr = p._element.get_or_add_pPr()
        bidi = OxmlElement('w:bidi')
        pPr.append(bidi)
        
        sizes = {0: 20, 1: 18, 2: 15, 3: 13, 4: 12}
        colors = {
            0: RGBColor(0x1F, 0x3A, 0x5F),
            1: RGBColor(0x1F, 0x4E, 0x79),
            2: RGBColor(0x2C, 0x3E, 0x50),
            3: RGBColor(0x34, 0x49, 0x5E),
            4: RGBColor(0x5D, 0x6D, 0x7E),
        }
        
        run = p.add_run(text)
        self._set_font(
            run,
            size=sizes.get(level, 12),
            bold=True,
            color=colors.get(level)
        )
        
        p.paragraph_format.space_before = Pt(15)
        p.paragraph_format.space_after = Pt(8)
        
        return p
    
    # ============================================================
    # PARAGRAPH
    # ============================================================
    
    def _add_paragraph(self, text: str):
        """افزودن پاراگراف متنی — وسط‌چین با RTL"""
        p = self.doc.add_paragraph()
        
        # ✅ وسط‌چین
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.space_before = Pt(3)
        
        # RTL
        pPr = p._element.get_or_add_pPr()
        bidi = OxmlElement('w:bidi')
        pPr.append(bidi)
        
        run = p.add_run(text)
        self._set_font(run, size=11)
        
        return p
    
    # ============================================================
    # IMAGE
    # ============================================================
    
    def _detect_section_type(self, text: str) -> Optional[str]:
        """تشخیص نوع سکشن از متن"""
        text_lower = text.lower()
        
        for section_type, keywords in self.SECTION_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    return section_type
        
        return None
    
    def _add_image(self, section_type: str, width_inches: float = 5.0) -> bool:
        """افزودن تصویر مربوط به سکشن"""
        if section_type in self.image_added_for_section:
            return False
        
        image_filename = self.SECTION_IMAGES.get(section_type)
        if not image_filename:
            return False
        
        image_path = self.images_dir / image_filename
        
        if not image_path.exists():
            logger.warning(f"⚠️ Image not found: {image_path}")
            return False
        
        try:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            run = p.add_run()
            run.add_picture(str(image_path), width=Inches(width_inches))
            
            self.image_added_for_section.add(section_type)
            logger.info(f"✅ Image added: {image_path}")
            return True
        
        except Exception as e:
            logger.error(f"⚠️ Error adding image: {e}")
            return False
    
    # ============================================================
    # TABLE
    # ============================================================
    
    def _add_table(self, table_lines: List[str]):
        """افزودن جدول"""
        if len(table_lines) < 2:
            return
        
        # حذف خط جداکننده
        data_lines = [
            l for l in table_lines
            if not re.match(r'^\|[\s\-:|]+\|$', l)
        ]
        
        if not data_lines:
            return
        
        # تجزیه
        rows = []
        for line in data_lines:
            cells = [c.strip() for c in line.strip('|').split('|')]
            rows.append(cells)
        
        if not rows:
            return
        
        n_cols = max(len(r) for r in rows)
        
        # ساخت جدول
        table = self.doc.add_table(rows=len(rows), cols=n_cols)
        table.style = 'Light Grid Accent 1'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        tbl = table._element
        tblPr = tbl.tblPr
        bidiVisual = OxmlElement('w:bidiVisual')
        tblPr.append(bidiVisual)
        
        # پر کردن
        for i, row_data in enumerate(rows):
            for j, cell_text in enumerate(row_data):
                if j < n_cols:
                    cell = table.cell(i, j)
                    cell.text = ''
                    
                    # ✅ وسط‌چین عمودی و افقی
                    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                    
                    p = cell.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    
                    # RTL برای سلول
                    pPr = p._element.get_or_add_pPr()
                    bidi = OxmlElement('w:bidi')
                    pPr.append(bidi)
                    
                    run = p.add_run(cell_text)
                    self._set_font(
                        run,
                        size=9 if i > 0 else 10,
                        bold=(i == 0)
                    )
        
        self.doc.add_paragraph()
    
    # ============================================================
    # MARKDOWN PARSER
    # ============================================================
    
    def _parse_markdown(self, content: str):
        """تجزیه محتوای Markdown"""
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # ===== H3 =====
            if line.startswith('### '):
                text = line[4:].strip()
                self._add_heading(text, level=2)
                
                # تصویر
                section_type = self._detect_section_type(text)
                if section_type:
                    self._add_image(section_type, width_inches=4.5)
            
            # ===== H2 =====
            elif line.startswith('## '):
                text = line[3:].strip()
                self._add_heading(text, level=1)
                
                # تصویر
                section_type = self._detect_section_type(text)
                if section_type:
                    self._add_image(section_type, width_inches=5.0)
            
            # ===== H1 =====
            elif line.startswith('# '):
                text = line[2:].strip()
                self._add_heading(text, level=0)
            
            # ===== Bullet list =====
            elif line.startswith('* ') or line.startswith('- '):
                text = line[2:].strip()
                clean = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
                p = self.doc.add_paragraph(style='List Bullet')
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(clean)
                self._set_font(run, size=10)
            
            # ===== Separator =====
            elif line.startswith('---') or line.startswith('==='):
                p = self.doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run('─' * 50)
                self._set_font(run, size=10, color=RGBColor(0x95, 0xA5, 0xA6))
            
            # ===== Table =====
            elif line.startswith('|'):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                i -= 1
                self._add_table(table_lines)
            
            # ===== Empty =====
            elif not line.strip():
                pass
            
            # ===== Normal text =====
            else:
                clean = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
                if clean.strip():
                    self._add_paragraph(clean)
            
            i += 1
    
    # ============================================================
    # EXPORT MAIN
    # ============================================================
    
    def export(
        self,
        content: str,
        output_path: str,
        project_name: str = "Project",
    ) -> bool:
        """
        تولید فایل Word از محتوای پروپوزال
        
        Args:
            content: متن Markdown پروپوزال
            output_path: مسیر فایل خروجی
            project_name: نام پروژه
        
        Returns:
            True اگر موفق باشد
        """
        try:
            # ===== Document جدید =====
            self.doc = Document()
            self.image_added_for_section = set()
            
            # ===== تنظیم جهت راست‌به‌چپ =====
            self._setup_document()
            
            # ===== تجزیه و افزودن =====
            self._parse_markdown(content)
            
            # ===== ذخیره =====
            self.doc.save(output_path)
            
            logger.info(f"✅ Word saved: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error saving Word: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            return False
    
    def _setup_document(self):
        """تنظیمات اولیه سند"""
        section = self.doc.sections[0]
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        
        # ===== Right-to-Left برای کل سند =====
        try:
            sectPr = section._sectPr
            bidi = OxmlElement('w:bidi')
            sectPr.append(bidi)
        except Exception as e:
            logger.debug(f"Could not set bidi: {e}")
    
    # ============================================================
    # EXPORT MULTI
    # ============================================================
    
    def export_multi(
        self,
        content: str,
        output_dir: str,
        project_name: str,
        revision_name: str = "Rev-0",
        per_section: bool = True,
    ) -> Dict[str, str]:
        """
        تولید چند فایل Word:
        - یک فایل کلی (MAIN)
        - یک فایل برای هر سکشن
        
        Args:
            content: متن کامل پروپوزال
            output_dir: پوشه‌ی خروجی
            project_name: نام پروژه
            revision_name: نام رویژن
            per_section: آیا فایل تفکیکی بسازد؟
        
        Returns:
            dict: {فایل_کلی: path, section_name: path, ...}
        """
        results = {}
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # ===== ۱. فایل کلی =====
            main_filename = f"Proposal_{self._safe_name(project_name)}_{revision_name}_MAIN.docx"
            main_path = os.path.join(output_dir, main_filename)
            
            if self.export(content, main_path, project_name):
                results['main'] = main_path
                logger.info(f"✅ Main file: {main_path}")
            
            # ===== ۲. فایل‌های تفکیکی =====
            if per_section:
                sections = self._split_by_sections(content)
                
                for section_title, section_content in sections.items():
                    safe_title = self._safe_name(section_title, max_len=25)
                    filename = f"Proposal_{self._safe_name(project_name)}_{revision_name}_{safe_title}.docx"
                    file_path = os.path.join(output_dir, filename)
                    
                    if self.export(section_content, file_path, project_name):
                        results[section_title] = file_path
                        logger.info(f"✅ Section file: {file_path}")
            
            return results
        
        except Exception as e:
            logger.error(f"❌ Error in export_multi: {e}", exc_info=True)
            return results
    
    def _split_by_sections(self, content: str) -> Dict[str, str]:
        """تقسیم پروپوزال به بخش‌های تخصصی"""
        sections = {}
        
        # ===== پیدا کردن عنوان‌های "## سناریوی کنترلی X" =====
        lines = content.split('\n')
        current_section = None
        current_content = []
        header_content = []  # محتوای قبل از اولین سکشن
        
        for line in lines:
            # چک: آیا خط یک عنوان سکشن است؟
            if line.startswith('## سناریوی کنترلی') or line.startswith('## Senario'):
                # ذخیره‌ی سکشن قبلی
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # شروع سکشن جدید
                current_section = self._extract_section_name(line)
                current_content = [line]
            elif current_section:
                # محتوای سکشن فعلی
                # چک: آیا به بخش بعدی رسیدیم؟
                if line.startswith('## ') and not line.startswith('## سناریوی کنترلی'):
                    # پایان سکشن فعلی
                    sections[current_section] = '\n'.join(current_content)
                    current_section = None
                    current_content = []
                else:
                    current_content.append(line)
            else:
                # قبل از اولین سکشن
                header_content.append(line)
        
        # ذخیره‌ی آخرین سکشن
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        # ===== اضافه کردن header به ابتدای هر سکشن =====
        header = '\n'.join(header_content)
        if header:
            for section_name in sections:
                sections[section_name] = f"{header}\n\n{sections[section_name]}"
        
        return sections
    
    def _extract_section_name(self, line: str) -> str:
        """استخراج نام سکشن از عنوان"""
        # "## سناریوی کنترلی بویلرها (Boiler)" → "بویلرها (Boiler)"
        name = line.replace('## ', '').strip()
        name = name.replace('سناریوی کنترلی', '').strip()
        return name or "Unknown"
    
    def _safe_name(self, name: str, max_len: int = 50) -> str:
        """نام فایل امن"""
        safe = "".join(
            c if c.isalnum() or c in " _-" else "_"
            for c in name
        ).strip()
        return safe[:max_len] or "Proposal"


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['WordProposalExporter']