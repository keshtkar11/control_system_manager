# export/pdf_exporter.py
"""
خروجی PDF حرفه‌ای — با پشتیبانی کامل فارسی

نسخه 2.0:
- فونت فارسی
- RTL کامل
- arabic-reshaper + python-bidi
"""

import os
from datetime import datetime
from typing import List, Optional
import math

from utils.pdf_helpers import fa, fa_paragraph, fa_mixed, fa_bold

from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line

from core import Motor, Project, COMPONENT_LABELS, COMPONENT_KEYS
from core.constants import (
    IO_CALCULATION, CABLE_SIZE, EXCLUDED_FROM_COMPONENTS,
    get_timestamp_for_filename, gregorian_to_jalali,
)


class PDFExporter:
    """صادرکننده گزارش PDF حرفه‌ای — A3 Landscape با فارسی"""
    
    def __init__(self, app):
        self.app = app
        self.persian_font = "Helvetica"
        self.persian_font_bold = "Helvetica-Bold"
        self._setup_fonts()
        
        self.company_name = "Vahhaj Sanat Energy Co."
        self.designer_name = "Mr.Keshtkar"
    
    # ============================================================
    # FONT SETUP
    # ============================================================

    @staticmethod
    def _sanitize_cable_tag(text) -> str:
        """
        پاک‌سازی Cable Tag — فقط ASCII
        
        - حفظ: حروف انگلیسی، اعداد، خط تیره، زیرخط، نقطه
        - حذف: کاراکترهای فارسی/عربی و خاص
        """
        if not text:
            return ''
        
        text = str(text)
        
        # ===== حفظ فقط کاراکترهای مجاز =====
        result = ''.join(
            c for c in text
            if ord(c) < 128 and (c.isalnum() or c in '-_.')
        )
        
        return result or 'TAG'
    
    def _setup_fonts(self):
        """ثبت فونت فارسی"""
        try:
            import sys
            
            # ===== مسیر base =====
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            resources_fonts = os.path.join(base_path, 'resources', 'fonts')
            
            # ===== مسیرهای ممکن =====
            font_candidates = [
                os.path.join(resources_fonts, "essential", "tahoma.ttf"),
                os.path.join(resources_fonts, "tahoma.ttf"),
                os.path.join(resources_fonts, "essential", "BNazanin.ttf"),
                os.path.join(resources_fonts, "BNazanin.ttf"),
                "C:/Windows/Fonts/tahoma.ttf",
                "C:/Windows/Fonts/BNazanin.ttf",
            ]
            
            for font_path in font_candidates:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('PersianFont', font_path))
                    self.persian_font = "PersianFont"
                    self.persian_font_bold = "PersianFont"  # همان فونت
                    print(f"✅ Font loaded: {os.path.basename(font_path)}")
                    break
            else:
                print("⚠️ No Persian font found, using Helvetica")
                self.persian_font = "Helvetica"
                self.persian_font_bold = "Helvetica-Bold"
        
        except Exception as e:
            print(f"Font setup failed: {e}")
            self.persian_font = "Helvetica"
            self.persian_font_bold = "Helvetica-Bold"
    
    # ============================================================
    # HELPERS
    # ============================================================
    
    def _safe_int(self, value):
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    
    def _get_component_name(self, field: str) -> str:
        """دریافت نام کامل کامپوننت"""
        component_labels = self.app.get_current_component_labels()
        name = component_labels.get(field, {}).get('en', '')
        if not name:
            name = COMPONENT_LABELS.get(field, {}).get('en', field)
        return name
    
    def _get_cable_size(self, field: str) -> str:
        """دریافت اندازه کابل"""
        return CABLE_SIZE.get(field, '2x1mm²')
    
    # ============================================================
    # STYLES
    # ============================================================
    
    def _create_styles(self):
        """ایجاد استایل‌ها — همه با فونت فارسی"""
        styles = getSampleStyleSheet()
        FONT = self.persian_font
        
        # ===== MainTitle =====
        styles.add(ParagraphStyle(
            name='MainTitle',
            parent=styles['Heading1'],
            fontName=FONT,
            fontSize=24,
            alignment=1,
            spaceAfter=15,
            leading=30,
            textColor=colors.HexColor('#1F4E79')
        ))
        
        # ===== SubTitle =====
        styles.add(ParagraphStyle(
            name='SubTitle',
            parent=styles['Normal'],
            fontName=FONT,
            fontSize=14,
            alignment=1,
            spaceAfter=8,
            leading=20,
            textColor=colors.HexColor('#7F8C8D')
        ))
        
        # ===== SectionTitle =====
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            fontName=FONT,
            fontSize=16,
            alignment=1,
            spaceAfter=10,
            spaceBefore=14,
            leading=22,
            textColor=colors.HexColor('#1F4E79')
        ))
        
        # ===== SubSectionTitle =====
        styles.add(ParagraphStyle(
            name='SubSectionTitle',
            parent=styles['Heading3'],
            fontName=FONT,
            fontSize=18,
            alignment=1,
            spaceAfter=10,
            spaceBefore=14,
            leading=24,
            textColor=colors.HexColor('#2C3E50')
        ))
        
        # ===== SectionNameTitle =====
        styles.add(ParagraphStyle(
            name='SectionNameTitle',
            parent=styles['Heading4'],
            fontName=FONT,
            fontSize=16,
            alignment=1,
            spaceAfter=10,
            spaceBefore=14,
            leading=22,
            textColor=colors.HexColor('#1F4E79')
        ))
        
        # ===== NormalText =====
        styles.add(ParagraphStyle(
            name='NormalText',
            parent=styles['Normal'],
            fontName=FONT,
            fontSize=10,
            alignment=1,
            spaceAfter=4,
            leading=15,
        ))
        
        # ===== TableText =====
        styles.add(ParagraphStyle(
            name='TableText',
            parent=styles['Normal'],
            fontName=FONT,
            fontSize=9,
            alignment=1,
            spaceAfter=2,
            leading=14,
        ))
        
        # ===== TableHeader =====
        styles.add(ParagraphStyle(
            name='TableHeader',
            parent=styles['Normal'],
            fontName=FONT,
            fontSize=9,
            alignment=1,
            textColor=colors.white,
            spaceAfter=2,
            leading=14,
        ))
        
        # ===== FooterStyle =====
        styles.add(ParagraphStyle(
            name='FooterStyle',
            parent=styles['Normal'],
            fontName=FONT,
            fontSize=12,
            alignment=1,
            textColor=colors.HexColor('#7F8C8D'),
            spaceAfter=0,
            spaceBefore=0,
            leading=16,
        ))
        
        return styles
    
    # ============================================================
    # FOOTER
    # ============================================================
    
    def _add_footer(self, canvas, doc):
        """اضافه کردن فوتر"""
        page_width, page_height = landscape(A3)
        margin = 15 * mm
        
        canvas.setStrokeColor(colors.HexColor('#3498DB'))
        canvas.setLineWidth(0.5)
        canvas.line(margin, 20 * mm, page_width - margin, 20 * mm)
        
        canvas.setFont(self.persian_font, 8)
        canvas.setFillColor(colors.HexColor('#7F8C8D'))
        canvas.drawCentredString(page_width / 2, 15 * mm, self.company_name)
    
    # ============================================================
    # HORIZONTAL LINE
    # ============================================================
    
    def _create_horizontal_line(self, width: float, color, thickness: int = 1):
        """ایجاد خط افقی"""
        class HorizontalLine(Flowable):
            def __init__(self, width, color, thickness):
                Flowable.__init__(self)
                self.width = width
                self.color = color
                self.thickness = thickness
            
            def draw(self):
                d = Drawing(self.width, self.thickness + 2)
                d.add(Line(0, 1, self.width, 1,
                          strokeColor=self.color,
                          strokeWidth=self.thickness))
                d.drawOn(self.canv, 0, 0)
            
            def wrap(self, availWidth, availHeight):
                return (self.width, self.thickness + 2)
        
        return HorizontalLine(width, color, thickness)
    
    # ============================================================
    # TITLE PAGE
    # ============================================================
    
    def _create_title_page(self, project: Project, styles, width: float,
                          revision_name: str = "Rev-0"):
        """صفحه عنوان"""
        elements = []
        
        elements.append(Spacer(1, 60))
        
        elements.append(Paragraph("CONTROL SYSTEM", styles['MainTitle']))
        elements.append(Paragraph("EQUIPMENT REPORT", styles['MainTitle']))
        elements.append(Spacer(1, 8))
        
        elements.append(Paragraph(self.company_name, styles['SubTitle']))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(
            f"Designed by: {self.designer_name}",
            styles['SubTitle']
        ))
        elements.append(Spacer(1, 10))
        
        elements.append(self._create_horizontal_line(
            width, colors.HexColor('#3498DB'), 3
        ))
        elements.append(Spacer(1, 15))
        
        # ===== Revision =====
        revision_style = ParagraphStyle(
            'RevisionStyle',
            parent=styles['Normal'],
            fontName=self.persian_font,
            fontSize=16,
            alignment=1,
            spaceAfter=6,
            leading=22,
            textColor=colors.HexColor('#27AE60')
        )
        elements.append(Paragraph(
            f"Revision: {revision_name}",
            revision_style
        ))
        elements.append(Spacer(1, 15))
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontName=self.persian_font,
            fontSize=12,
            alignment=1,
            spaceAfter=6,
            leading=18,
        )
        
        elements.append(Paragraph(
            f"<b>Project Name:</b> {fa(project.name)}",
            info_style
        ))
        
        if project.client_name:
            elements.append(Paragraph(
                f"<b>Client:</b> {fa(project.client_name)}",
                info_style
            ))
        if project.consultant_name:
            elements.append(Paragraph(
                f"<b>Consultant:</b> {fa(project.consultant_name)}",
                info_style
            ))
        if project.contractor_name:
            elements.append(Paragraph(
                f"<b>Contractor:</b> {fa(project.contractor_name)}",
                info_style
            ))
        
        elements.append(Spacer(1, 10))
        now = datetime.now()
        jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
        date_str = f"{jy}/{jm:02d}/{jd:02d} {now.hour:02d}:{now.minute:02d}"
        
        elements.append(Paragraph(
            f"<b>Report Date:</b> {date_str}",
            info_style
        ))
        
        elements.append(Spacer(1, 50))
        elements.append(self._create_horizontal_line(
            width, colors.HexColor('#3498DB'), 1
        ))
        elements.append(Spacer(1, 10))
        
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontName=self.persian_font,
            fontSize=9,
            alignment=1,
            leading=14,
            textColor=colors.HexColor('#7F8C8D')
        )
        elements.append(Paragraph(self.company_name, footer_style))
        elements.append(Paragraph(
            "Generated by Control System Manager",
            footer_style
        ))
        
        return elements
    
    # ============================================================
    # EXECUTIVE SUMMARY
    # ============================================================
    
    def _create_executive_summary(self, project, devices, styles, width):
        elements = []
        
        elements.append(Paragraph("1. EXECUTIVE SUMMARY", styles['SectionTitle']))
        elements.append(Spacer(1, 6))
        
        total_devices_count = 0
        active_devices_count = 0
        
        for device in devices:
            device_count = 1
            for field in COMPONENT_KEYS:
                if field in ['PU', 'VSD']:
                    qty = self._safe_int(getattr(device, field, 0))
                    if qty > 0:
                        device_count = qty
                        break
            
            total_devices_count += device_count
            
            if device.get_total_io() > 0:
                active_devices_count += device_count
        
        summary_data = [
            ["Metric", "Value"],
            ["Total Sections", str(len(project.sections))],
            ["Total Devices", str(total_devices_count)],
            ["Active Devices", str(active_devices_count)],
            ["Total I/O Points", str(project.get_total_io())]
        ]
        
        col_widths = [width * 0.4, width * 0.4]
        table = Table(summary_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(table)
        return elements
    
    # ============================================================
    # IO SUMMARY
    # ============================================================
    
    def _create_io_summary(self, devices, styles, width):
        elements = []
        
        elements.append(Paragraph("2. I/O SUMMARY", styles['SectionTitle']))
        elements.append(Spacer(1, 6))
        
        total_di = sum(d.DI for d in devices)
        total_do = sum(d.DO for d in devices)
        total_ai = sum(d.AI for d in devices)
        total_ao = sum(d.AO for d in devices)
        total_io = total_di + total_do + total_ai + total_ao
        
        io_data = [
            ["I/O Type", "Count", "Percentage"],
            ["Digital Input (DI)", str(total_di),
             f"{(total_di/total_io*100):.1f}%" if total_io > 0 else "0%"],
            ["Digital Output (DO)", str(total_do),
             f"{(total_do/total_io*100):.1f}%" if total_io > 0 else "0%"],
            ["Analog Input (AI)", str(total_ai),
             f"{(total_ai/total_io*100):.1f}%" if total_io > 0 else "0%"],
            ["Analog Output (AO)", str(total_ao),
             f"{(total_ao/total_io*100):.1f}%" if total_io > 0 else "0%"],
            ["TOTAL", str(total_io), "100%"]
        ]
        
        col_widths = [width * 0.35, width * 0.25, width * 0.25]
        table = Table(io_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E6E6FA')),
        ]))
        
        elements.append(table)
        return elements
    
    # ============================================================
    # SECTIONS ANALYSIS
    # ============================================================
    
    def _create_sections_analysis(self, project, styles, width):
        elements = []
        
        elements.append(Paragraph(
            "3. IO List for each Device of Project",
            styles['SectionTitle']
        ))
        elements.append(Spacer(1, 6))
        
        total_io = project.get_total_io()
        
        table_data = [[
            "Section Name", "Device Description", "Devices",
            "DI", "DO", "AI", "AO", "Total I/O", "Percentage"
        ]]
        
        for section in project.sections:
            description_groups = {}
            
            for device in section.devices:
                desc = device.Description or "Unknown"
                if desc not in description_groups:
                    description_groups[desc] = {
                        'count': 0, 'di': 0, 'do': 0, 'ai': 0, 'ao': 0
                    }
                
                device_count = 1
                for field in COMPONENT_KEYS:
                    if field in ['PU', 'VSD']:
                        qty = self._safe_int(getattr(device, field, 0))
                        if qty > 0:
                            device_count = qty
                            break
                
                description_groups[desc]['count'] += device_count
                description_groups[desc]['di'] += device.DI
                description_groups[desc]['do'] += device.DO
                description_groups[desc]['ai'] += device.AI
                description_groups[desc]['ao'] += device.AO
            
            for desc, data in description_groups.items():
                group_io = data['di'] + data['do'] + data['ai'] + data['ao']
                percentage = (group_io / total_io * 100) if total_io > 0 else 0
                
                # ✅ reshape متن فارسی
                table_data.append([
                    fa(section.name),
                    fa(desc),
                    str(data['count']),
                    str(data['di']),
                    str(data['do']),
                    str(data['ai']),
                    str(data['ao']),
                    str(group_io),
                    f"{percentage:.1f}%"
                ])
        
        col_widths = [
            width * 0.20, width * 0.35, width * 0.08,
            width * 0.05, width * 0.05, width * 0.05,
            width * 0.05, width * 0.10, width * 0.07
        ]
        
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#F8F9FA')]),
        ]))
        
        elements.append(table)
        return elements
    
    # ============================================================
    # COMPONENTS ANALYSIS
    # ============================================================
    
    def _create_components_analysis(self, project, devices, styles, width):
        elements = []
        
        elements.append(Paragraph("4. List of Materials Report", styles['MainTitle']))
        elements.append(Spacer(1, 6))
        
        # ===== 4.1 Summary =====
        elements.append(Paragraph(
            "4.1. LOM For All Sections (Summary)",
            styles['SubSectionTitle']
        ))
        elements.append(Spacer(1, 4))
        
        usage = {}
        for device in devices:
            for field in COMPONENT_KEYS:
                if field in EXCLUDED_FROM_COMPONENTS:
                    continue
                qty = self._safe_int(getattr(device, field, 0))
                if qty > 0:
                    if field not in usage:
                        usage[field] = {"qty": 0, "di": 0, "do": 0, "ai": 0, "ao": 0}
                    usage[field]["qty"] += qty
                    
                    if field in IO_CALCULATION:
                        io = IO_CALCULATION[field]
                        usage[field]["di"] += qty * io.get("DI", 0)
                        usage[field]["do"] += qty * io.get("DO", 0)
                        usage[field]["ai"] += qty * io.get("AI", 0)
                        usage[field]["ao"] += qty * io.get("AO", 0)
        
        if usage:
            sorted_usage = sorted(
                usage.items(), key=lambda x: x[1]["qty"], reverse=True
            )
            active_keys = sorted(usage.keys())
            
            table_data = [["Component", "Qty", "DI", "DO", "AI", "AO"]]
            for key in active_keys:
                table_data[0].append(key)
            
            for field, data in sorted_usage[:30]:
                name = self._get_component_name(field)
                row = [fa(name), str(data["qty"]),
                       str(data["di"]), str(data["do"]),
                       str(data["ai"]), str(data["ao"])]
                
                for key in active_keys:
                    if key == field:
                        row.append(str(data["qty"]))
                    else:
                        row.append("0")
                
                table_data.append(row)
            
            col_widths = [width * 0.35, width * 0.08,
                         width * 0.08, width * 0.08,
                         width * 0.08, width * 0.08]
            for _ in active_keys:
                col_widths.append(width * 0.03)
            
            total_width = sum(col_widths)
            if total_width > 1.0:
                scale_factor = 1.0 / total_width
                col_widths = [w * scale_factor for w in col_widths]
            col_widths = [w * width for w in col_widths]
            
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor('#F8F9FA')]),
            ]))
            elements.append(table)
        
        elements.append(Spacer(1, 10))
        
        # ===== 4.2 By Sections =====
        if len(project.sections) > 1:
            elements.append(Paragraph(
                "4.2. LOM For each Section",
                styles['SubSectionTitle']
            ))
            elements.append(Spacer(1, 4))
            
            for section in project.sections:
                if not section.devices:
                    continue
                
                section_usage = {}
                for device in section.devices:
                    for field in COMPONENT_KEYS:
                        if field in EXCLUDED_FROM_COMPONENTS:
                            continue
                        qty = self._safe_int(getattr(device, field, 0))
                        if qty > 0:
                            if field not in section_usage:
                                section_usage[field] = {
                                    "qty": 0, "di": 0, "do": 0, "ai": 0, "ao": 0
                                }
                            section_usage[field]["qty"] += qty
                            
                            if field in IO_CALCULATION:
                                io = IO_CALCULATION[field]
                                section_usage[field]["di"] += qty * io.get("DI", 0)
                                section_usage[field]["do"] += qty * io.get("DO", 0)
                                section_usage[field]["ai"] += qty * io.get("AI", 0)
                                section_usage[field]["ao"] += qty * io.get("AO", 0)
                
                if not section_usage:
                    continue
                
                # ✅ reshape نام سکشن
                elements.append(Paragraph(
                    f"<b>{fa(section.name)}</b>",
                    styles['SectionNameTitle']
                ))
                
                sorted_section = sorted(
                    section_usage.items(),
                    key=lambda x: x[1]["qty"],
                    reverse=True
                )
                section_active_keys = sorted(section_usage.keys())
                
                table_data = [["Component", "Qty", "DI", "DO", "AI", "AO"]]
                for key in section_active_keys:
                    table_data[0].append(key)
                
                sec_total = {"qty": 0, "di": 0, "do": 0, "ai": 0, "ao": 0}
                
                for field, data in sorted_section[:20]:
                    name = self._get_component_name(field)
                    
                    sec_total["qty"] += data["qty"]
                    sec_total["di"] += data["di"]
                    sec_total["do"] += data["do"]
                    sec_total["ai"] += data["ai"]
                    sec_total["ao"] += data["ao"]
                    
                    row = [fa(name), str(data["qty"]),
                           str(data["di"]), str(data["do"]),
                           str(data["ai"]), str(data["ao"])]
                    
                    for key in section_active_keys:
                        if key == field:
                            row.append(str(data["qty"]))
                        else:
                            row.append("0")
                    
                    table_data.append(row)
                
                # ===== Subtotal =====
                subtotal_row = [
                    "SUBTOTAL",
                    str(sec_total["qty"]),
                    str(sec_total["di"]),
                    str(sec_total["do"]),
                    str(sec_total["ai"]),
                    str(sec_total["ao"])
                ]
                for key in section_active_keys:
                    subtotal_row.append(
                        str(section_usage.get(key, {}).get("qty", 0))
                    )
                table_data.append(subtotal_row)
                
                col_widths = [width * 0.35, width * 0.08,
                             width * 0.08, width * 0.08,
                             width * 0.08, width * 0.08]
                for _ in section_active_keys:
                    col_widths.append(width * 0.03)
                
                total_width = sum(col_widths)
                if total_width > 1.0:
                    scale_factor = 1.0 / total_width
                    col_widths = [w * scale_factor for w in col_widths]
                col_widths = [w * width for w in col_widths]
                
                table = Table(table_data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                    ('FONTSIZE', (0, 0), (-1, -2), 10),
                    ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -2),
                     [colors.HexColor('#F0F8FF'), colors.HexColor('#E8F4FD')]),
                    # ===== Subtotal =====
                    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D6EAF8')),
                    ('FONTNAME', (0, -1), (-1, -1), self.persian_font),
                    ('FONTSIZE', (0, -1), (-1, -1), 9),
                    ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1F4E79')),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 6))
        
        return elements
    
    # ============================================================
    # DETAIL IO LIST
    # ============================================================
    
    def _create_cable_list_by_section(self, project, styles, width):
        """Detail IO List به تفکیک بخش‌ها"""
        elements = []
        
        elements.append(Paragraph(
            "<br/><br/><br/><br/><br/><br/>5. Detail IO List<br/><br/>"
            "For each Part of Project",
            styles['MainTitle']
        ))
        elements.append(Spacer(2, 12))
        
        # ===== اعتبارسنجی =====
        try:
            from core.validation_errors import validate_project_components
            validation = validate_project_components(project)
        except Exception:
            validation = None
        
        # ===== نمایش خطاها =====
        if validation and validation.has_any():
            error_style = ParagraphStyle(
                'ErrorHeader',
                parent=styles['Normal'],
                fontName=self.persian_font,
                fontSize=12,
                textColor=colors.white,
                backColor=colors.HexColor('#C0392B'),
                alignment=0,
                spaceAfter=4,
                spaceBefore=8,
                leftIndent=6,
                rightIndent=6,
                borderPadding=6,
            )
            
            error_msg_style = ParagraphStyle(
                'ErrorMessage',
                parent=styles['Normal'],
                fontName=self.persian_font,
                fontSize=9,
                leading=14,
                textColor=colors.HexColor('#C0392B'),
                backColor=colors.HexColor('#FADBD8'),
                alignment=0,
                spaceAfter=3,
                leftIndent=6,
                rightIndent=6,
                borderPadding=4,
            )
            
            warn_msg_style = ParagraphStyle(
                'WarningMessage',
                parent=styles['Normal'],
                fontName=self.persian_font,
                fontSize=9,
                leading=14,
                textColor=colors.HexColor('#B9770E'),
                backColor=colors.HexColor('#FDEBD0'),
                alignment=0,
                spaceAfter=3,
                leftIndent=6,
                rightIndent=6,
                borderPadding=4,
            )
            
            elements.append(Paragraph(
                f"⚠️ VALIDATION ERRORS FOUND: {validation.count()} issue(s)",
                error_style
            ))
            elements.append(Spacer(1, 4))
            
            for err in validation.errors:
                if err.severity.value in ('error', 'critical'):
                    msg_style = error_msg_style
                else:
                    msg_style = warn_msg_style
                
                # ✅ reshape متن فارسی
                title_text = fa(str(err.title))
                message_text = fa(str(err.message).replace('\n', ' | '))
                
                elements.append(Paragraph(
                    f"<b>[{err.code}]</b> {title_text} — {message_text}",
                    msg_style
                ))
                elements.append(Spacer(1, 2))
            
            elements.append(Spacer(1, 10))
        
        has_cables = False
        MAX_ACTIVE_COLS = 30
        CABLE_LIST_EXCLUDED = ['SPR', 'MOD']
        ACTIVE_COMPONENTS_EXCLUDED = [
            'FA', 'FE', 'SLE', 'CMD', 'PU', 'VSD', 'SPR', 'MOD', 'FC', 'LIG'
        ]
        
        EQUIPMENT_KEYS = ['PU', 'VSD']
        global_cable_counter = 0
        
        def build_pump_names(device_name: str, count: int, use_index: bool) -> list:
            """تولید نام پمپ‌ها"""
            if count == 0:
                return []
            
            names = []
            if use_index:
                for i in range(count):
                    suffix = chr(ord('a') + i)
                    names.append(f"{device_name}{suffix}")
            else:
                import re
                match = re.match(r'^(.*?)(\d+)$', device_name)
                if match:
                    prefix = match.group(1)
                    start_num = int(match.group(2))
                    for i in range(count):
                        names.append(f"{prefix}{start_num + i}")
                else:
                    for i in range(count):
                        suffix = chr(ord('a') + i)
                        names.append(f"{device_name}{suffix}")
            
            return names
        
        for section in project.sections:
            if not section.devices:
                continue
            
            cable_list = []
            for device in section.devices:
                device_name = device.Name or "Unnamed"
                info_value = device.INFO or ""
                location = device.Description or ""
                use_index_naming = getattr(device, 'UseIndexNaming', True)
                
                pu_qty = self._safe_int(getattr(device, 'PU', 0))
                pump_names = build_pump_names(device_name, pu_qty, use_index_naming)
                
                all_active_components = []
                for comp_field in COMPONENT_KEYS:
                    if comp_field in CABLE_LIST_EXCLUDED:
                        continue
                    comp_qty = self._safe_int(getattr(device, comp_field, 0))
                    if comp_qty > 0:
                        all_active_components.append({
                            'key': comp_field,
                            'qty': comp_qty,
                            'label': self._get_component_name(comp_field)
                        })
                
                tag_suffixes = {}
                for comp in all_active_components:
                    field = comp['key']
                    comp_qty = comp['qty']
                    
                    if comp_qty > 1:
                        suffixes = [chr(ord('a') + i) for i in range(comp_qty)]
                        tag_suffixes[field] = suffixes
                    else:
                        tag_suffixes[field] = ['']
                
                for comp in all_active_components:
                    field = comp['key']
                    comp_qty = comp['qty']
                    cable_size = self._get_cable_size(field)
                    
                    io = IO_CALCULATION.get(field, {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0})
                    unit_di = io.get('DI', 0)
                    unit_do = io.get('DO', 0)
                    unit_ai = io.get('AI', 0)
                    unit_ao = io.get('AO', 0)
                    
                    from_location = (
                        "Power Panel" if field in ['PU', 'VSD'] else "Field"
                    )
                    
                    if field == 'PU':
                        for i in range(comp_qty):
                            display_name = (
                                pump_names[i] if i < len(pump_names) else device_name
                            )
                            
                            # Status
                            global_cable_counter += 1
                            safe_name = self._sanitize_cable_tag(display_name)
                            status_tag = f"{safe_name}-Status-{global_cable_counter }"
                            
                            cable_list.append({
                                'tag': status_tag,
                                'device_name': display_name,
                                'info_value': info_value,
                                'description': "Motor Status (DI)",
                                'location': location,
                                'cable_type': "NYSLCY",
                                'cable_size': "6x1mm²",
                                'from': from_location,
                                'to': "Control Panel",
                                'di': unit_di, 'do': 0, 'ai': 0, 'ao': 0,
                                'active_components': [
                                    {'key': c['key'],
                                     'qty': 1 if c['key'] in ['FA', 'FE', 'SLE'] else 0}
                                    for c in all_active_components
                                ]
                            })
                            
                            # CMD
                            global_cable_counter += 1
                            cmd_tag = f"{safe_name}-CMD-{global_cable_counter }"
                            
                            cable_list.append({
                                'tag': cmd_tag,
                                'device_name': display_name,
                                'info_value': info_value,
                                'description': "Motor Command (DO)",
                                'location': location,
                                'cable_type': "NYSLCY",
                                'cable_size': "2x1mm²",
                                'from': from_location,
                                'to': "Control Panel",
                                'di': 0, 'do': unit_do, 'ai': 0, 'ao': 0,
                                'active_components': [
                                    {'key': c['key'],
                                     'qty': 1 if c['key'] == 'CMD' else 0}
                                    for c in all_active_components
                                ]
                            })
                    
                    elif field == 'VSD':
                        for i in range(comp_qty):
                            display_name = (
                                pump_names[i] if i < len(pump_names) else device_name
                            )
                            
                            global_cable_counter += 1
                            vsd_tag = f"{safe_name}-{field}-{global_cable_counter }"
                            
                            cable_list.append({
                                'tag': vsd_tag,
                                'device_name': display_name,
                                'info_value': info_value,
                                'description': comp['label'],
                                'location': location,
                                'cable_type': "NYSLCY",
                                'cable_size': cable_size,
                                'from': from_location,
                                'to': "Control Panel",
                                'di': unit_di, 'do': unit_do,
                                'ai': unit_ai, 'ao': unit_ao,
                                'active_components': [
                                    {'key': c['key'],
                                     'qty': 1 if c['key'] == field else 0}
                                    for c in all_active_components
                                ]
                            })
                    
                    elif field == 'FS':
                        for i in range(comp_qty):
                            if i < len(pump_names):
                                pump_name = pump_names[i]
                                pump_name_safe = self._sanitize_cable_tag(pump_name)
                                display_name = f"{pump_name_safe}-FS"
                            else:
                                display_name = f"{device_name}-FS"
                            
                            global_cable_counter += 1
                            comp_tag = f"{display_name}-{global_cable_counter }"
                            
                            cable_list.append({
                                'tag': comp_tag,
                                'device_name': display_name,
                                'info_value': info_value,
                                'description': comp['label'],
                                'location': location,
                                'cable_type': "NYSLCY",
                                'cable_size': cable_size,
                                'from': from_location,
                                'to': "Control Panel",
                                'di': unit_di, 'do': unit_do,
                                'ai': unit_ai, 'ao': unit_ao,
                                'active_components': [
                                    {'key': c['key'],
                                     'qty': 1 if c['key'] == field else 0}
                                    for c in all_active_components
                                ]
                            })
                    
                    else:
                        for i in range(comp_qty):
                            tag_suffix = tag_suffixes[field][i]
                            display_name = device_name
                            
                            global_cable_counter += 1
                            safe_device = self._sanitize_cable_tag(device_name)
                            safe_suffix = self._sanitize_cable_tag(tag_suffix)
                            comp_tag = f"{safe_device}{safe_suffix}-{field}-{global_cable_counter }"
                            
                            cable_list.append({
                                'tag': comp_tag,
                                'device_name': display_name,
                                'info_value': info_value,
                                'description': comp['label'],
                                'location': location,
                                'cable_type': "NYSLCY",
                                'cable_size': cable_size,
                                'from': from_location,
                                'to': "Control Panel",
                                'di': unit_di, 'do': unit_do,
                                'ai': unit_ai, 'ao': unit_ao,
                                'active_components': [
                                    {'key': c['key'],
                                     'qty': 1 if c['key'] == field else 0}
                                    for c in all_active_components
                                ]
                            })
            
            if not cable_list:
                continue
            
            has_cables = True
            elements.append(PageBreak())
            
            # ✅ reshape نام سکشن
            elements.append(Paragraph(
                f"<b>{fa(section.name)}</b>",
                styles['SectionNameTitle']
            ))
            
            active_keys_set = set()
            for cable in cable_list:
                for comp in cable['active_components']:
                    if (comp['qty'] > 0 and
                        comp['key'] not in ACTIVE_COMPONENTS_EXCLUDED):
                        active_keys_set.add(comp['key'])
            
            active_keys = sorted(list(active_keys_set))
            active_cols = min(len(active_keys), MAX_ACTIVE_COLS)
            
            headers = [
                "No", "Name", "Remark", "Cable Tag", "Equipment", "Location",
                "Cable Type", "Cable Size", "From", "To",
                "DI", "DO", "AI", "AO"
            ]
            for i in range(active_cols):
                if i < len(active_keys):
                    headers.append(active_keys[i])
                else:
                    headers.append(f"Comp-{i+1}")
            
            table_data = [headers]
            
            sec_total = {'di': 0, 'do': 0, 'ai': 0, 'ao': 0}
            section_total_active = {k: 0 for k in active_keys}
            
            for idx, cable in enumerate(cable_list, 1):
                sec_total['di'] += cable['di']
                sec_total['do'] += cable['do']
                sec_total['ai'] += cable['ai']
                sec_total['ao'] += cable['ao']
                
                for comp in cable['active_components']:
                    if comp['key'] in section_total_active:
                        section_total_active[comp['key']] += comp['qty']
                
                # ✅ reshape نام‌ها و توضیحات
                def _fa_safe(text):
                    """فقط اگر متن غیر-ASCII داشت، reshape کن"""
                    if not text:
                        return ''
                    text = str(text)
                    # اگر همه ASCII است → برگردان همان‌طور
                    if all(ord(c) < 128 for c in text):
                        return text
                    return fa(text)

                row = [
                    str(idx),
                    _fa_safe(cable['device_name']),      # ← اگر فارسی است، reshape می‌شود
                    _fa_safe(cable['info_value']),
                    cable['tag'],                         # ← Cable Tag خالص ASCII
                    _fa_safe(cable['description']),
                    _fa_safe(cable['location']),
                    cable['cable_type'],
                    cable['cable_size'],
                    _fa_safe(cable['from']),
                    _fa_safe(cable['to']),
                    str(cable['di']),
                    str(cable['do']),
                    str(cable['ai']),
                    str(cable['ao'])
                ]
                
                for i in range(active_cols):
                    if i < len(active_keys):
                        key = active_keys[i]
                        qty = 0
                        for comp in cable['active_components']:
                            if comp['key'] == key:
                                qty = comp['qty']
                                break
                        row.append(str(qty))
                    else:
                        row.append("")
                
                table_data.append(row)
            
            # Subtotal
            subtotal_row = [
                "", "SUBTOTAL", "", "", "", "", "", "", "", "",
                str(sec_total['di']), str(sec_total['do']),
                str(sec_total['ai']), str(sec_total['ao'])
            ]
            for i in range(active_cols):
                if i < len(active_keys):
                    subtotal_row.append(str(section_total_active.get(active_keys[i], 0)))
                else:
                    subtotal_row.append("")
            
            table_data.append(subtotal_row)
            
            col_widths = [
                0.01, 0.06, 0.09, 0.08, 0.09, 0.12,
                0.05, 0.05, 0.05, 0.05,
                0.015, 0.015, 0.015, 0.015,
            ]
            for i in range(active_cols):
                col_widths.append(0.02)
            
            total_width = sum(col_widths)
            if total_width > 1.0:
                scale_factor = 1.0 / total_width
                col_widths = [w * scale_factor for w in col_widths]
            col_widths = [w * width for w in col_widths]
            
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -2), 8),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # Subtotal
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D6EAF8')),
                ('FONTSIZE', (0, -1), (-1, -1), 9),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1F4E79')),
            ]
            
            for i in range(active_cols):
                col_idx = 14 + i
                style.append(('FONTSIZE', (col_idx, 0), (col_idx, 0), 6))
                style.append(('FONTSIZE', (col_idx, 1), (col_idx, -2), 6))
                style.append(('ALIGN', (col_idx, 0), (col_idx, -1), 'CENTER'))
            
            table.setStyle(TableStyle(style))
            elements.append(table)
            elements.append(Spacer(1, 8))
        
        if not has_cables:
            elements.append(Paragraph(
                "No cables found in any section.",
                styles['NormalText']
            ))
        
        return elements
    
    # ============================================================
    # CONTROLLER REQUIREMENTS
    # ============================================================
    
    def _create_controller_requirements_by_section(self, project, styles, width):
        elements = []
        
        elements.append(Paragraph(
            "6. CONTROLLER REQUIREMENTS (By Section)",
            styles['SectionTitle']
        ))
        elements.append(Spacer(1, 4))
        
        desc_style = ParagraphStyle(
            'ControllerDesc',
            parent=styles['Normal'],
            fontName=self.persian_font,
            fontSize=8,
            leading=12,
            textColor=colors.HexColor('#7F8C8D'),
            alignment=0,
            spaceAfter=6,
        )
        elements.append(Paragraph(
            "CBX-8R8: 16 I/O (flexible, max 3 FBX) | "
            "MCX-08m2: 8DI/8DO/8AI/4AO | MCX-06D: 8DI/6DO/4AI/2AO",
            desc_style
        ))
        elements.append(Spacer(1, 6))
        
        def calc_cbx_fbx(di, do, ai, ao):
            total = di + do + ai + ao
            if total == 0:
                return 0, 0
            min_by_di = math.ceil(di / 16)
            min_by_do = math.ceil(do / 8)
            min_by_ai = math.ceil(ai / 16)
            min_by_ao = math.ceil(ao / 8)
            min_by_total = math.ceil(total / 16)
            n_ctrl = max(min_by_di, min_by_do, min_by_ai, min_by_ao, min_by_total)
            if n_ctrl == 0:
                return 0, 0
            cbx = math.ceil(n_ctrl / 4)
            fbx = n_ctrl - cbx
            return cbx, fbx
        
        def calc_mcx(di, do, ai, ao):
            n_08m2 = 0
            n_06d = 0
            rem_di, rem_do, rem_ai, rem_ao = di, do, ai, ao
            max_iter = 1000
            iter_count = 0
            
            while (rem_di > 0 or rem_do > 0 or rem_ai > 0 or rem_ao > 0) \
                    and iter_count < max_iter:
                iter_count += 1
                
                if rem_di <= 8 and rem_do <= 6 and rem_ai <= 4 and rem_ao <= 2:
                    n_06d += 1
                    break
                
                if rem_di <= 8 and rem_do <= 8 and rem_ai <= 8 and rem_ao <= 4:
                    n_08m2 += 1
                    break
                
                n_08m2 += 1
                n_06d += 1
                
                rem_di = max(0, rem_di - 16)
                rem_do = max(0, rem_do - 14)
                rem_ai = max(0, rem_ai - 12)
                rem_ao = max(0, rem_ao - 6)
            
            return n_08m2, n_06d
        
        headers = ["Section", "DI", "DO", "AI", "AO", "I/O",
                   "CBX-8R8", "FBX-8R8", "MCX-08m2", "MCX-06D"]
        table_data = [headers]
        
        total_di = total_do = total_ai = total_ao = total_io = 0
        total_cbx = total_fbx = 0
        total_mcx_08m2 = total_mcx_06d = 0
        
        for section in project.sections:
            s_di = sum(d.DI for d in section.devices)
            s_do = sum(d.DO for d in section.devices)
            s_ai = sum(d.AI for d in section.devices)
            s_ao = sum(d.AO for d in section.devices)
            s_io = s_di + s_do + s_ai + s_ao
            
            cbx, fbx = calc_cbx_fbx(s_di, s_do, s_ai, s_ao)
            mcx_08m2, mcx_06d = calc_mcx(s_di, s_do, s_ai, s_ao)
            
            total_di += s_di; total_do += s_do
            total_ai += s_ai; total_ao += s_ao
            total_io += s_io
            total_cbx += cbx; total_fbx += fbx
            total_mcx_08m2 += mcx_08m2; total_mcx_06d += mcx_06d
            
            table_data.append([
                fa(section.name),
                str(s_di), str(s_do), str(s_ai), str(s_ao), str(s_io),
                str(cbx), str(fbx), str(mcx_08m2), str(mcx_06d),
            ])
        
        table_data.append([
            "TOTAL",
            str(total_di), str(total_do), str(total_ai), str(total_ao),
            str(total_io), str(total_cbx), str(total_fbx),
            str(total_mcx_08m2), str(total_mcx_06d),
        ])
        
        col_widths = [
            width * 0.22, width * 0.06, width * 0.06,
            width * 0.06, width * 0.06, width * 0.07,
            width * 0.09, width * 0.09, width * 0.11, width * 0.11,
        ]
        total_w = sum(col_widths)
        if total_w > width:
            scale = width / total_w
            col_widths = [w * scale for w in col_widths]
        
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (-1, -2), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2),
             [colors.white, colors.HexColor('#F8F9FA')]),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('BACKGROUND', (8, 0), (9, 0), colors.HexColor('#FFF3CD')),
            ('TEXTCOLOR', (8, 0), (9, 0), colors.HexColor('#856404')),
            ('BACKGROUND', (8, 1), (9, -2), colors.HexColor('#FFFBF0')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E6E6FA')),
            ('FONTSIZE', (0, -1), (-1, -1), 9),
            ('BACKGROUND', (8, -1), (9, -1), colors.HexColor('#FFF3CD')),
            ('TEXTCOLOR', (8, -1), (9, -1), colors.HexColor('#856404')),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 10))
        return elements
    
    # ============================================================
    # APPENDICES
    # ============================================================
    
    def _create_appendices(self, devices, styles, width):
        elements = []
        
        elements.append(Paragraph("7. APPENDICES", styles['SectionTitle']))
        elements.append(Spacer(1, 6))
        
        # ===== 7.1 Legend =====
        elements.append(Paragraph(
            "7.1. Component Legend",
            styles['SubSectionTitle']
        ))
        elements.append(Spacer(1, 4))
        
        used_components = set()
        for device in devices:
            for field in COMPONENT_KEYS:
                if field in EXCLUDED_FROM_COMPONENTS:
                    continue
                qty = self._safe_int(getattr(device, field, 0))
                if qty > 0:
                    used_components.add(field)
            
            if self._safe_int(getattr(device, 'PU', 0)) > 0:
                used_components.add('PU')
            if self._safe_int(getattr(device, 'VSD', 0)) > 0:
                used_components.add('VSD')
        
        if used_components:
            categories = {
                "Sensors": ["DTS", "ITS", "RTS", "DTHS", "RTHS", "AVS",
                           "FS", "PS", "PT", "DPT", "DPS", "AQ", "FR",
                           "LS", "LT", "SD", "Knob", "SOU", "LUX", "VIB"],
                "Actuators": ["VA", 'DAM_T1', 'DAM_T2', 'DAM_T3',
                             'DAM_T4', "SV", "MOV"],
                "Equipment": ["PU", "VSD", "FC", "LIG", "BUZ"],
            }
            
            legend_data = [["Abbreviation", "Full Name", "Category"]]
            
            for field in sorted(used_components):
                full_name = self._get_component_name(field)
                category = "Other"
                for cat_name, cat_fields in categories.items():
                    if field in cat_fields:
                        category = cat_name
                        break
                legend_data.append([field, full_name, category])
            
            col_widths = [width * 0.25, width * 0.45, width * 0.2]
            table = Table(legend_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor('#F8F9FA')]),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph(
                "No components found.",
                styles['NormalText']
            ))
        
        elements.append(Spacer(1, 10))
        
        # ===== 7.2 IO Reference =====
        elements.append(Paragraph(
            "7.2. IO Reference Guide",
            styles['SubSectionTitle']
        ))
        elements.append(Spacer(1, 4))
        
        from core.constants import IO_REFERENCE
        
        used_io = []
        for field in sorted(used_components):
            if field in IO_REFERENCE:
                ref = IO_REFERENCE[field]
                di_text = ", ".join(ref.get('di', [])) if ref.get('di') else "-"
                do_text = ", ".join(ref.get('do', [])) if ref.get('do') else "-"
                ai_text = ", ".join(ref.get('ai', [])) if ref.get('ai') else "-"
                ao_text = ", ".join(ref.get('ao', [])) if ref.get('ao') else "-"
                
                used_io.append({
                    'component': f"{field} ({ref.get('label', field)})",
                    'di': di_text,
                    'do': do_text,
                    'ai': ai_text,
                    'ao': ao_text,
                })
        
        if used_io:
            io_data = [["Component", "DI", "DO", "AI", "AO"]]
            for item in used_io:
                io_data.append([
                    fa(item['component']),
                    fa(item['di']),
                    fa(item['do']),
                    fa(item['ai']),
                    fa(item['ao']),
                ])
            
            col_widths = [width * 0.25, width * 0.2,
                         width * 0.2, width * 0.2, width * 0.15]
            table = Table(io_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, -1), self.persian_font),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor('#F8F9FA')]),
            ]))
            elements.append(table)
        
        elements.append(Spacer(1, 20))
        
        # ===== END =====
        end_style = ParagraphStyle(
            'EndStyle',
            parent=styles['Normal'],
            fontName=self.persian_font,
            fontSize=14,
            alignment=1,
            leading=20,
            textColor=colors.HexColor('#1F4E79')
        )
        
        elements.append(Paragraph("END OF REPORT", end_style))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(self.company_name, styles['SubTitle']))
        elements.append(Paragraph(
            f"Designed by: {self.designer_name}",
            styles['SubTitle']
        ))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(
            "Generated by Control System Manager",
            styles['NormalText']
        ))
        
        return elements
    
    # ============================================================
    # MAIN EXPORT
    # ============================================================
    
    def export_full_report(self, file_path: str = None) -> Optional[str]:
        """صدور گزارش کامل PDF"""
        
        project = self.app.get_current_project()
        if not project:
            from tkinter import messagebox
            messagebox.showwarning("Warning", "No project selected!")
            return None
        
        current_revision = project.get_current_revision()
        if not current_revision:
            from tkinter import messagebox
            messagebox.showwarning("Warning", "No current revision!")
            return None
        
        revision_name = current_revision.name
        devices = project.get_all_devices()
        
        if not devices:
            from tkinter import messagebox
            messagebox.showwarning("Warning", "No devices found!")
            return None
        
        if not file_path:
            from tkinter import filedialog
            
            safe_rev = "".join(
                c if c.isalnum() or c in " _-" else "_"
                for c in revision_name
            ).strip() or "Rev"
            
            safe_proj = "".join(
                c if c.isalnum() or c in " _-" else "_"
                for c in project.name
            ).strip() or "Project"
            
            timestamp = get_timestamp_for_filename()
            
            try:
                project_dir = self.app.attachment_manager.ensure_project_dir(project.name)
                reports_dir = os.path.join(project_dir, "Reports")
                os.makedirs(reports_dir, exist_ok=True)
                default_dir = reports_dir
            except Exception as e:
                default_dir = os.path.expanduser("~")
                print(f"⚠️ Could not get attachments folder: {e}")
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save PDF Report",
                initialdir=default_dir,
                initialfile=f"IO_List({safe_proj})_{safe_rev}_{timestamp}.pdf"
            )
            if not file_path:
                return None
        
        try:
            PAGE_WIDTH, PAGE_HEIGHT = landscape(A3)
            MARGIN = 15 * mm
            USABLE_WIDTH = PAGE_WIDTH - (2 * MARGIN)
            
            doc = SimpleDocTemplate(
                file_path,
                pagesize=landscape(A3),
                rightMargin=MARGIN,
                leftMargin=MARGIN,
                topMargin=MARGIN,
                bottomMargin=25 * mm,
                title=f"IO List - {project.name} ({revision_name})",
            )
            
            styles = self._create_styles()
            elements = []
            
            # ===== صفحه‌ها =====
            elements.extend(self._create_title_page(
                project, styles, USABLE_WIDTH, revision_name
            ))
            elements.append(PageBreak())
            
            elements.extend(self._create_executive_summary(
                project, devices, styles, USABLE_WIDTH
            ))
            elements.append(PageBreak())
            
            elements.extend(self._create_io_summary(
                devices, styles, USABLE_WIDTH
            ))
            elements.append(PageBreak())
            
            elements.extend(self._create_sections_analysis(
                project, styles, USABLE_WIDTH
            ))
            elements.append(PageBreak())
            
            elements.extend(self._create_components_analysis(
                project, devices, styles, USABLE_WIDTH
            ))
            elements.append(PageBreak())
            
            elements.extend(self._create_cable_list_by_section(
                project, styles, USABLE_WIDTH
            ))
            elements.append(PageBreak())
            
            elements.extend(self._create_controller_requirements_by_section(
                project, styles, USABLE_WIDTH
            ))
            elements.append(PageBreak())
            
            elements.extend(self._create_appendices(
                devices, styles, USABLE_WIDTH
            ))
            
            def footer(canvas, doc):
                self._add_footer(canvas, doc)
            
            doc.build(elements, onFirstPage=footer, onLaterPages=footer)
            
            if os.name == 'nt':
                os.startfile(file_path)
            
            from tkinter import messagebox
            messagebox.showinfo(
                "Success",
                f"PDF Report saved to:\n{file_path}\n\n"
                f"📁 Project: {project.name}\n"
                f"📌 Revision: {revision_name}"
            )
            
            return file_path
        
        except Exception as e:
            from tkinter import messagebox
            import traceback
            messagebox.showerror(
                "PDF Export Error",
                f"Failed to generate PDF:\n{str(e)}\n\n"
                f"{traceback.format_exc()}"
            )
            return None


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['PDFExporter']