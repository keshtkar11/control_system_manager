# export/valves_excel_exporter.py
"""
گزارش Excel حرفه‌ای برای بخش Valves (شیرها)

شامل Sheets:
- Cover (صفحه عنوان)
- Valves — PICV
- Valves — 3 Way
- Valves — Steam
- Valves — PICV+3Way
- Valves — All
- Valves — LOM (لیست مواد — ۲ جدول: شیرها و موتورها)
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side,
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins

from core.constants import (
    get_timestamp_for_filename,
    gregorian_to_jalali,
)


# ================================================================
# VALVES EXCEL EXPORTER
# ================================================================

class ValvesExcelExporter:
    """
    صادرکننده گزارش Excel برای شیرها
    """
    
    def __init__(self, app):
        """
        Args:
            app: MotorApp
        """
        self.app = app
        self.wb = Workbook()
        
        # ============================================================
        # رنگ‌ها و استایل‌ها
        # ============================================================
        self.primary_color = "1F4E79"      # آبی تیره
        self.secondary_color = "2C3E50"    # خاکستری تیره
        self.accent_color = "3498DB"       # آبی روشن
        self.success_color = "27AE60"      # سبز
        self.warning_color = "F39C12"      # نارنجی
        self.danger_color = "E74C3C"       # قرمز
        self.light_color = "F8F9FA"        # خاکستری روشن
        self.white_color = "FFFFFF"
        self.total_bg_color = "E6E6FA"     # بنفش روشن
        self.picv_color = "0A84FF"         # آبی PICV
        self.three_way_color = "FF9F0A"    # نارنجی 3Way
        self.steam_color = "FF453A"        # قرمز Steam
        
        # ============================================================
        # فونت‌ها
        # ============================================================
        self.title_font = Font(
            name="Calibri", size=18, bold=True, color=self.white_color
        )
        self.section_font = Font(
            name="Calibri", size=12, bold=True, color=self.white_color
        )
        self.header_font = Font(
            name="Calibri", size=10, bold=True, color=self.white_color
        )
        self.body_font = Font(
            name="Calibri", size=9, color="000000"
        )
        self.body_bold_font = Font(
            name="Calibri", size=9, bold=True, color="000000"
        )
        self.total_font = Font(
            name="Calibri", size=10, bold=True, color="000000"
        )
        
        # ============================================================
        # Fill ها
        # ============================================================
        self.title_fill = PatternFill(
            start_color=self.primary_color, end_color=self.primary_color,
            fill_type="solid"
        )
        self.section_fill = PatternFill(
            start_color=self.secondary_color, end_color=self.secondary_color,
            fill_type="solid"
        )
        self.header_fill = PatternFill(
            start_color=self.primary_color, end_color=self.primary_color,
            fill_type="solid"
        )
        self.body_fill = PatternFill(
            start_color=self.white_color, end_color=self.white_color,
            fill_type="solid"
        )
        self.alt_fill = PatternFill(
            start_color=self.light_color, end_color=self.light_color,
            fill_type="solid"
        )
        self.total_fill = PatternFill(
            start_color=self.total_bg_color, end_color=self.total_bg_color,
            fill_type="solid"
        )
        
        # ============================================================
        # Alignment
        # ============================================================
        self.center_alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        self.left_alignment = Alignment(
            horizontal="left", vertical="center", wrap_text=True
        )
        self.right_alignment = Alignment(
            horizontal="right", vertical="center", wrap_text=True
        )
        
        # ============================================================
        # Border
        # ============================================================
        self.thin_border = Border(
            left=Side(style="thin", color="D0D0D0"),
            right=Side(style="thin", color="D0D0D0"),
            top=Side(style="thin", color="D0D0D0"),
            bottom=Side(style="thin", color="D0D0D0"),
        )
        self.thick_border = Border(
            left=Side(style="thin", color="D0D0D0"),
            right=Side(style="thin", color="D0D0D0"),
            top=Side(style="medium", color=self.primary_color),
            bottom=Side(style="medium", color=self.primary_color),
        )
        
        # ============================================================
        # اطلاعات شرکت
        # ============================================================
        self.company_name = "Vahhaj Sanat Energy Co."
        self.designer_name = "Mr.Keshtkar"
    
    # ================================================================
    # متدهای کمکی
    # ================================================================
    
    def _set_page_setup(self, ws, is_cover: bool = False):
        """تنظیمات صفحه — مشابه Device Excel"""
        # ===== Paper و Orientation =====
        ws.page_setup.paperSize = ws.PAPERSIZE_A3
        ws.page_setup.orientation = 'landscape'
        
        # ===== Fit to Width =====
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        
        # ===== Margins =====
        ws.page_margins = PageMargins(
            left=0.5, right=0.5, top=0.75, bottom=0.75
        )
        
        # ===== Print Title Rows (برای همه صفحات) =====
        if not is_cover:
            ws.print_title_rows = '1:4'
            
            # ===== Horizontal Centered =====
            ws.print_options.horizontalCentered = True
            
            # ===== Page Break Preview =====
            ws.sheet_view.view = 'pageBreakPreview'
            ws.sheet_view.zoomScale = 130
        
        # ===== Header (برای همه) =====
        if not is_cover:
            ws.oddHeader.left.text = f"{self.company_name}"
            ws.oddHeader.left.size = 9
            ws.oddHeader.left.color = self.primary_color
            
            ws.oddHeader.right.text = "Valves Report"
            ws.oddHeader.right.size = 9
            ws.oddHeader.right.color = self.primary_color
        
        # ===== Footer (برای همه) =====
        ws.oddFooter.left.text = "© Vahhaj Sanat Energy Co."
        ws.oddFooter.left.size = 8
        ws.oddFooter.left.color = self.primary_color
        
        ws.oddFooter.right.text = "Page &P of &N"  # ← شماره صفحه
        ws.oddFooter.right.size = 8
        ws.oddFooter.right.color = self.primary_color
    
    def _apply_header_style(self, ws, row: int, col_count: int):
        """اعمال استایل هدر"""
        for col in range(1, col_count + 1):
            cell = ws.cell(row=row, column=col)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
    
    def _apply_body_style(self, ws, row: int, col_count: int, 
                          is_alt: bool = False):
        """اعمال استایل بدنه"""
        for col in range(1, col_count + 1):
            cell = ws.cell(row=row, column=col)
            cell.font = self.body_font
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
            cell.fill = self.alt_fill if is_alt else self.body_fill
    
    def _apply_total_style(self, ws, row: int, col_count: int):
        """اعمال استایل TOTAL"""
        for col in range(1, col_count + 1):
            cell = ws.cell(row=row, column=col)
            cell.font = self.total_font
            cell.fill = self.total_fill
            cell.alignment = self.center_alignment
            cell.border = self.thick_border
    
    def _write_title_row(self, ws, title: str, col_count: int, 
                          row: int = 1, color: str = None):
        """نوشتن سطر عنوان"""
        ws.merge_cells(
            start_row=row, start_column=1,
            end_row=row, end_column=col_count
        )
        cell = ws.cell(row=row, column=1, value=title)
        cell.font = self.section_font
        
        if color:
            fill = PatternFill(
                start_color=color, end_color=color, fill_type="solid"
            )
            cell.fill = fill
        else:
            cell.fill = self.section_fill
        
        cell.alignment = self.center_alignment
        ws.row_dimensions[row].height = 30
    
    def _write_subtitle_row(self, ws, subtitle: str, col_count: int,
                             row: int = 2):
        """نوشتن سطر زیرعنوان"""
        ws.merge_cells(
            start_row=row, start_column=1,
            end_row=row, end_column=col_count
        )
        cell = ws.cell(row=row, column=1, value=subtitle)
        cell.font = Font(
            name="Calibri", size=10, italic=True, color="7F8C8D"
        )
        cell.alignment = self.center_alignment
        ws.row_dimensions[row].height = 20
    
    @staticmethod
    def _safe_float(value, default: float = 0.0) -> float:
        """تبدیل امن به float"""
        try:
            if value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _safe_str(value) -> str:
        """تبدیل امن به str"""
        if value is None:
            return ''
        return str(value)
    
    @staticmethod
    def _safe_int(value, default: int = 0) -> int:
        """تبدیل امن به int"""
        try:
            if value is None:
                return default
            return int(value)
        except (ValueError, TypeError):
            return default
    
    # ================================================================
    # ۱. Cover Sheet
    # ================================================================
    
    def _create_cover_sheet(self, project, revision_name: str):
        """ایجاد صفحه عنوان"""
        ws = self.wb.active
        ws.title = "Cover"
        self._set_page_setup(ws, is_cover=True)
        
        # ===== عرض ستون‌ها =====
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 40
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 40
        
        # ===== عنوان اصلی =====
        ws.merge_cells('A1:D1')
        ws['A1'].value = "VALVES REPORT"
        ws['A1'].font = Font(
            name="Calibri", size=28, bold=True, color=self.primary_color
        )
        ws['A1'].alignment = self.center_alignment
        ws.row_dimensions[1].height = 50
        
        ws.merge_cells('A2:D2')
        ws['A2'].value = "BMS Project - Valves List"
        ws['A2'].font = Font(
            name="Calibri", size=16, color=self.secondary_color
        )
        ws['A2'].alignment = self.center_alignment
        ws.row_dimensions[2].height = 30
        
        # ===== شرکت =====
        ws.merge_cells('A3:D3')
        ws['A3'].value = self.company_name
        ws['A3'].font = Font(
            name="Calibri", size=14, bold=True, color=self.secondary_color
        )
        ws['A3'].alignment = self.center_alignment
        ws.row_dimensions[3].height = 25
        
        # ===== خط جداکننده =====
        ws.merge_cells('A4:D4')
        ws['A4'].border = Border(
            bottom=Side(style='thick', color=self.primary_color)
        )
        ws.row_dimensions[4].height = 10
        
        # ===== اطلاعات پروژه =====
        row = 6
        now = datetime.now()
        jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
        date_str = f"{jy}/{jm:02d}/{jd:02d} {now.hour:02d}:{now.minute:02d}"
        
        info_items = [
            ("Project Name:", project.name),
            ("Revision:", revision_name),
            ("Client:", project.client_name or "—"),
            ("Consultant:", project.consultant_name or "—"),
            ("Contractor:", project.contractor_name or self.company_name),
            ("Designer:", project.designer_name or self.designer_name),
            ("Report Date:", date_str),
        ]
        
        for label, value in info_items:
            ws.cell(row=row, column=1, value=label).font = Font(
                name="Calibri", size=12, bold=True
            )
            ws.cell(row=row, column=2, value=value).font = Font(
                name="Calibri", size=12
            )
            ws.cell(row=row, column=1).alignment = self.right_alignment
            ws.cell(row=row, column=2).alignment = self.left_alignment
            ws.row_dimensions[row].height = 22
            row += 1
        
        # ===== خط جداکننده =====
        ws.merge_cells(
            start_row=row, start_column=1,
            end_row=row, end_column=4
        )
        ws.cell(row=row, column=1).border = Border(
            bottom=Side(style='thin', color=self.primary_color)
        )
        ws.row_dimensions[row].height = 10
        row += 2
        
        # ===== شمارش شیرها =====
        all_valves = self._collect_all_valves()
        
        ws.merge_cells(
            start_row=row, start_column=1,
            end_row=row, end_column=4
        )
        ws.cell(
            row=row, column=1,
            value=f"📊 Total Valves: {len(all_valves)}"
        ).font = Font(
            name="Calibri", size=14, bold=True, color=self.primary_color
        )
        ws.cell(row=row, column=1).alignment = self.center_alignment
        ws.row_dimensions[row].height = 30
    
    # ================================================================
    # ۲. Sheet های هر نوع شیر
    # ================================================================
    
    def _create_valve_type_sheet(self, valve_type: str, valves: List, 
                                  sheet_title: str, sheet_color: str):
        """
        ایجاد Sheet برای یک نوع شیر
        
        Args:
            valve_type: نوع شیر ('PICV', '3 Way', 'Steam', 'PICV+3Way')
            valves: لیست شیرهای این نوع
            sheet_title: عنوان Sheet (نام در تب)
            sheet_color: رنگ برای هدر
        """
        if not valves:
            return  # اگر شیری از این نوع نیست، Sheet ساخته نشود
        
        ws = self.wb.create_sheet(sheet_title)
        self._set_page_setup(ws)
        
        # ============================================================
        # تعریف ستون‌ها بر اساس نوع
        # ============================================================
        columns = self._get_columns_for_type(valve_type)
        
        col_count = len(columns)
        
        # ============================================================
        # عنوان
        # ============================================================
        self._write_title_row(
            ws, f"🔧 {valve_type} Valves", col_count, row=1,
            color=sheet_color
        )
        
        # ============================================================
        # زیرعنوان
        # ============================================================
        now = datetime.now()
        jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
        date_str = f"{jy}/{jm:02d}/{jd:02d}"
        
        project = self.app.get_current_project()
        project_name = project.name if project else "—"
        
        subtitle = (
            f"Project: {project_name}  |  "
            f"Total: {len(valves)} valves  |  "
            f"Date: {date_str}"
        )
        self._write_subtitle_row(ws, subtitle, col_count, row=2)
        
        # ============================================================
        # هدر جدول
        # ============================================================
        header_row = 4
        for col_idx, (key, label, width, align) in enumerate(columns, 1):
            cell = ws.cell(row=header_row, column=col_idx, value=label)
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = width
        
        self._apply_header_style(ws, header_row, col_count)
        ws.row_dimensions[header_row].height = 25
        
        # ============================================================
        # داده‌ها
        # ============================================================
        row = header_row + 1
        for i, valve in enumerate(valves, 1):
            is_alt = (i % 2 == 0)
            
            for col_idx, (key, label, width, align) in enumerate(columns, 1):
                value = self._get_cell_value(valve, key, i)
                
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.font = self.body_font
                cell.alignment = self.center_alignment
                cell.border = self.thin_border
                cell.fill = self.alt_fill if is_alt else self.body_fill
            
            ws.row_dimensions[row].height = 20
            row += 1
        
        # ============================================================
        # TOTAL
        # ============================================================
        total_row = row
        total_qty = sum(int(v.Quantity or 0) for v in valves)
        
        # اولین سلول: TOTAL
        ws.cell(row=total_row, column=1, value="TOTAL")
        
        # سلول تعداد (پیدا کردن ستون Qty)
        for col_idx, (key, label, width, align) in enumerate(columns, 1):
            if key == 'quantity':
                ws.cell(row=total_row, column=col_idx, value=total_qty)
        
        self._apply_total_style(ws, total_row, col_count)
        ws.row_dimensions[total_row].height = 25
        
        # ============================================================
        # AutoFilter
        # ============================================================
        ws.auto_filter.ref = (
            f"A{header_row}:{get_column_letter(col_count)}{total_row}"
        )
        
        # ============================================================
        # Freeze Panes
        # ============================================================
        ws.freeze_panes = f"A{header_row + 1}"
    
    # ================================================================
    # ۳. Sheet جامع (All)
    # ================================================================
    def _create_section_sheet(self, section_name: str, valves: List):
        """ایجاد Sheet برای یک سکشن — همه انواع شیر در یک شیت"""
        if not valves:
            return
        
        # ===== نام شیت امن (max 31 char) =====
        safe_name = "".join(
            c if c.isalnum() or c in " _-" else "_"
            for c in section_name
        ).strip()[:25] or "Section"
        
        # جلوگیری از نام تکراری
        base_name = safe_name
        idx = 1
        while f"S - {safe_name}" in self.wb.sheetnames:
            idx += 1
            safe_name = f"{base_name}_{idx}"
        
        ws = self.wb.create_sheet(f"S - {safe_name}")
        self._set_page_setup(ws)
        
        # ===== ستون‌های جامع =====
        columns = self._get_all_columns(valves)
        col_count = len(columns)
        
        # ===== عنوان =====
        self._write_title_row(
            ws, f"🔧 Section: {section_name} — Valves",
            col_count, row=1, color=self.primary_color
        )
        
        # ===== زیرعنوان =====
        now = datetime.now()
        jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
        date_str = f"{jy}/{jm:02d}/{jd:02d}"
        
        type_counts = defaultdict(int)
        for v in valves:
            type_counts[v.ValveType or 'Unknown'] += 1
        counts_str = "  |  ".join(f"{k}: {v}" for k, v in sorted(type_counts.items()))
        
        subtitle = (
            f"Section: {section_name}  |  "
            f"Total: {len(valves)}  |  {counts_str}  |  Date: {date_str}"
        )
        self._write_subtitle_row(ws, subtitle, col_count, row=2)
        
        # ===== هدر =====
        header_row = 4
        for col_idx, (key, label, width, align) in enumerate(columns, 1):
            ws.cell(row=header_row, column=col_idx, value=label)
            ws.column_dimensions[get_column_letter(col_idx)].width = width
        
        self._apply_header_style(ws, header_row, col_count)
        ws.row_dimensions[header_row].height = 25
        
        # ===== داده‌ها =====
        row = header_row + 1
        for i, valve in enumerate(valves, 1):
            is_alt = (i % 2 == 0)
            for col_idx, (key, label, width, align) in enumerate(columns, 1):
                value = self._get_cell_value(valve, key, i)
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.font = self.body_font
                cell.alignment = self.center_alignment
                cell.border = self.thin_border
                cell.fill = self.alt_fill if is_alt else self.body_fill
            ws.row_dimensions[row].height = 20
            row += 1
        
        # ===== TOTAL =====
        total_row = row
        total_qty = sum(int(v.Quantity or 0) for v in valves)
        ws.cell(row=total_row, column=1, value="TOTAL")
        for col_idx, (key, label, width, align) in enumerate(columns, 1):
            if key == 'quantity':
                ws.cell(row=total_row, column=col_idx, value=total_qty)
        self._apply_total_style(ws, total_row, col_count)
        ws.row_dimensions[total_row].height = 25
        
        ws.auto_filter.ref = (
            f"A{header_row}:{get_column_letter(col_count)}{total_row}"
        )
        ws.freeze_panes = f"A{header_row + 1}"

    # ===== ۴. Sheet جامع =====
    def _create_all_sheet(self, all_valves: List):
        """ایجاد Sheet جامع — همه شیرها"""
        if not all_valves:
            return
        
        ws = self.wb.create_sheet("Valves — All")
        self._set_page_setup(ws)
        
        # ============================================================
        # ستون‌های جامع (همه ۳۰ ستون مرتبط)
        # ============================================================
        columns = self._get_all_columns(all_valves)
        col_count = len(columns)
        
        # ============================================================
        # عنوان
        # ============================================================
        self._write_title_row(
            ws, "🔧 ALL Valves — Complete List", col_count, row=1,
            color=self.primary_color
        )
        
        # ============================================================
        # زیرعنوان
        # ============================================================
        now = datetime.now()
        jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
        date_str = f"{jy}/{jm:02d}/{jd:02d}"
        
        project = self.app.get_current_project()
        project_name = project.name if project else "—"
        
        # شمارش هر نوع
        type_counts = defaultdict(int)
        for v in all_valves:
            type_counts[v.ValveType or 'Unknown'] += 1
        
        counts_str = "  |  ".join(
            f"{k}: {v}" for k, v in sorted(type_counts.items())
        )
        
        subtitle = (
            f"Project: {project_name}  |  "
            f"Total: {len(all_valves)}  |  "
            f"{counts_str}  |  "
            f"Date: {date_str}"
        )
        self._write_subtitle_row(ws, subtitle, col_count, row=2)
        
        # ============================================================
        # هدر
        # ============================================================
        header_row = 4
        for col_idx, (key, label, width, align) in enumerate(columns, 1):
            ws.cell(row=header_row, column=col_idx, value=label)
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = width
        
        self._apply_header_style(ws, header_row, col_count)
        ws.row_dimensions[header_row].height = 25
        
        # ============================================================
        # داده‌ها
        # ============================================================
        row = header_row + 1
        for i, valve in enumerate(all_valves, 1):
            is_alt = (i % 2 == 0)
            
            for col_idx, (key, label, width, align) in enumerate(columns, 1):
                value = self._get_cell_value(valve, key, i)
                
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.font = self.body_font
                cell.alignment = (
                    self.left_alignment if align == 'left'
                    else self.right_alignment if align == 'right'
                    else self.center_alignment
                )
                cell.border = self.thin_border
                cell.fill = self.alt_fill if is_alt else self.body_fill
            
            ws.row_dimensions[row].height = 20
            row += 1
        
        # ============================================================
        # TOTAL
        # ============================================================
        total_row = row
        total_qty = sum(int(v.Quantity or 0) for v in all_valves)
        
        ws.cell(row=total_row, column=1, value="TOTAL")
        
        for col_idx, (key, label, width, align) in enumerate(columns, 1):
            if key == 'quantity':
                ws.cell(row=total_row, column=col_idx, value=total_qty)
        
        self._apply_total_style(ws, total_row, col_count)
        ws.row_dimensions[total_row].height = 25
        
        # ============================================================
        # AutoFilter + Freeze
        # ============================================================
        ws.auto_filter.ref = (
            f"A{header_row}:{get_column_letter(col_count)}{total_row}"
        )
        ws.freeze_panes = f"A{header_row + 1}"
    
    # ================================================================
    # 5. LOM Sheet (دو جدول: شیرها + موتورها)
    # ================================================================
    
    def _create_lom_sheet(self, all_valves: List):
        """ایجاد Sheet لیست مواد (LOM) با دو جدول"""
        if not all_valves:
            return
        
        ws = self.wb.create_sheet("Valves — LOM")
        self._set_page_setup(ws)
        
        # ============================================================
        # عرض ستون‌ها (بدون DN — ستون E جداکننده)
        # ============================================================
        col_widths = {
            'A': 6,    # No (Valve)
            'B': 15,   # Valve Type
            'C': 40,   # Valve Model
            'D': 10,   # Qty (Valve)
            'E': 4,    # فاصله (جداکننده)
            'F': 6,    # No (Actuator)
            'G': 35,   # Actuator Model
            'H': 20,   # Signal
            'I': 10,   # Qty (Actuator)
        }
        
        for col_letter, width in col_widths.items():
            ws.column_dimensions[col_letter].width = width
        
        # ============================================================
        # عنوان اصلی
        # ============================================================
        # جدول ۱: A تا D
        ws.merge_cells('A1:D1')
        cell = ws.cell(row=1, column=1, value="🔧 VALVE BODIES (LOM)")
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.center_alignment
        
        # جدول ۲: F تا I
        ws.merge_cells('F1:I1')
        cell = ws.cell(row=1, column=6, value="⚙️ ACTUATORS (LOM)")
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.center_alignment
        
        ws.row_dimensions[1].height = 30
        
        # ============================================================
        # هدر جدول ۱ (A تا D)
        # ============================================================
        header_row = 2
        
        valve_headers = ["No", "Valve Type", "Valve Model", "Qty"]
        for col_idx, header in enumerate(valve_headers, 1):
            ws.cell(row=header_row, column=col_idx, value=header)
        
        # ============================================================
        # هدر جدول ۲ (F تا I)
        # ============================================================
        actuator_headers = ["No", "Actuator Model", "Signal", "Qty"]
        for col_idx, header in enumerate(actuator_headers, 6):
            ws.cell(row=header_row, column=col_idx, value=header)
        
        # ===== اعمال استایل هدرها (1-4 و 6-9) =====
        for col in list(range(1, 5)) + list(range(6, 10)):
            cell = ws.cell(row=header_row, column=col)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
        
        ws.row_dimensions[header_row].height = 25

        # ============================================================
        # جدول ۱: جمع‌آوری شیرها (بدون DN)
        # ✅ اصلاح‌شده: PICV+3Way → دو ردیف (PICV و 3Way)
        # ============================================================
        valve_groups = defaultdict(int)
        
        for valve in all_valves:
            valve_type = valve.ValveType or 'Unknown'
            qty = int(valve.Quantity or 0)
            
            # ============================================================
            # PICV تنها
            # ============================================================
            if valve_type == 'PICV':
                model = valve.PICVModel or '—'
                key = ('PICV', model)
                valve_groups[key] += qty
            
            # ============================================================
            # 3 Way تنها
            # ============================================================
            elif valve_type == '3 Way':
                model = valve.__dict__.get('3WayModel', '') or '—'
                key = ('3 Way', model)
                valve_groups[key] += qty
            
            # ============================================================
            # Steam
            # ============================================================
            elif valve_type == 'Steam':
                model = valve.SteamModel or '—'
                key = ('Steam', model)
                valve_groups[key] += qty
            
            # ============================================================
            # ✅ PICV+3Way → دو ردیف جداگانه
            # ============================================================
            elif valve_type == 'PICV+3Way':
                # ===== ۱. ردیف PICV =====
                picv_model = valve.PICVModel or '—'
                key_picv = ('PICV', picv_model)
                valve_groups[key_picv] += qty
                
                # ===== ۲. ردیف 3Way =====
                three_way_model = valve.__dict__.get('3WayModel', '') or '—'
                key_3way = ('3 Way', three_way_model)
                valve_groups[key_3way] += qty
            
            # ============================================================
            # Unknown
            # ============================================================
            else:
                key = ('Unknown', '—')
                valve_groups[key] += qty
        
        # ============================================================
        # مرتب‌سازی شیرها
        # ============================================================
        sorted_valves = sorted(
            valve_groups.items(),
            key=lambda x: (x[0][0], -x[1])
        )
        
        # ============================================================
        # نوشتن جدول ۱
        # ============================================================
        row = header_row + 1
        valve_total = 0
        
        for i, ((v_type, v_model), qty) in enumerate(sorted_valves, 1):
            is_alt = (i % 2 == 0)
            
            values = [i, v_type, v_model, qty]
            
            for col_idx, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.font = self.body_font
                cell.alignment = self.center_alignment
                cell.border = self.thin_border
                cell.fill = self.alt_fill if is_alt else self.body_fill
            
            valve_total += qty
            ws.row_dimensions[row].height = 20
            row += 1
        
        # ===== TOTAL جدول ۱ =====
        total_row = row
        ws.cell(row=total_row, column=1, value="TOTAL")
        ws.cell(row=total_row, column=4, value=valve_total)
        
        for col in range(1, 5):
            cell = ws.cell(row=total_row, column=col)
            cell.font = self.total_font
            cell.fill = self.total_fill
            cell.alignment = self.center_alignment
            cell.border = self.thick_border
        
        ws.row_dimensions[total_row].height = 25
        
        # ============================================================
        # جدول ۲: جمع‌آوری موتورها
        # ============================================================
        actuator_groups = defaultdict(int)
        
        for valve in all_valves:
            valve_type = valve.ValveType or ''
            
            actuator = ''
            signal = ''
            
            if valve_type == 'PICV':
                actuator = valve.PICVActuator or ''
                signal = valve.PICVSignal or ''
            elif valve_type == '3 Way':
                actuator = valve.__dict__.get('3WayActuator', '') or ''
                signal = valve.__dict__.get('3WaySignal', '') or ''
            elif valve_type == 'Steam':
                actuator = valve.SteamActuator or ''
                signal = valve.SteamSignal or ''
            elif valve_type == 'PICV+3Way':
                actuator = valve.__dict__.get('3WayActuator', '') or ''
                signal = valve.__dict__.get('3WaySignal', '') or ''
            
            if not actuator:
                continue
            
            key = (actuator, signal)
            actuator_groups[key] += int(valve.Quantity or 0)
        
        # ============================================================
        # مرتب‌سازی موتورها
        # ============================================================
        sorted_actuators = sorted(
            actuator_groups.items(),
            key=lambda x: (-x[1], x[0][0])
        )
        
        # ============================================================
        # نوشتن جدول ۲ (F تا I)
        # ============================================================
        row = header_row + 1
        actuator_total = 0
        
        for i, ((actuator, signal), qty) in enumerate(sorted_actuators, 1):
            is_alt = (i % 2 == 0)
            
            values = [i, actuator, signal or '—', qty]
            
            for col_idx, value in enumerate(values, 6):
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.font = self.body_font
                cell.alignment = self.center_alignment
                cell.border = self.thin_border
                cell.fill = self.alt_fill if is_alt else self.body_fill
            
            actuator_total += qty
            ws.row_dimensions[row].height = 20
            row += 1
        
        # ===== TOTAL جدول ۲ =====
        total_row_2 = row
        ws.cell(row=total_row_2, column=6, value="TOTAL")
        ws.cell(row=total_row_2, column=9, value=actuator_total)
        
        for col in range(6, 10):
            cell = ws.cell(row=total_row_2, column=col)
            cell.font = self.total_font
            cell.fill = self.total_fill
            cell.alignment = self.center_alignment
            cell.border = self.thick_border
        
        ws.row_dimensions[total_row_2].height = 25
        
        # ============================================================
        # خط جداکننده بین دو جدول (E)
        # ============================================================
        for r in range(header_row, max(row, total_row_2) + 1):
            sep_cell = ws.cell(row=r, column=5)
            sep_cell.fill = PatternFill(
                start_color="D0D0D0", end_color="D0D0D0",
                fill_type="solid"
            )

    def _create_lom_total_sheet(self, all_valves: List, by_section: Dict[str, List]):
        """
        LOM Total — جمع کل شیرها و موتورهای کل پروژه
        + جدول خلاصه به تفکیک سکشن
        """
        if not all_valves:
            return
        
        ws = self.wb.create_sheet("LOM — TOTAL")
        self._set_page_setup(ws)
        
        col_widths = {
            'A': 6, 'B': 15, 'C': 40, 'D': 10,
            'E': 4,
            'F': 6, 'G': 35, 'H': 20, 'I': 10,
        }
        for col_letter, width in col_widths.items():
            ws.column_dimensions[col_letter].width = width
        
        # ===== عنوان اصلی =====
        ws.merge_cells('A1:I1')
        cell = ws.cell(row=1, column=1, value="📊 PROJECT TOTAL — LOM (All Sections)")
        cell.font = self.title_font
        cell.fill = self.title_fill
        cell.alignment = self.center_alignment
        ws.row_dimensions[1].height = 35
        
        # ===== جدول ۱: VALVE BODIES =====
        ws.merge_cells('A2:D2')
        cell = ws.cell(row=2, column=1, value="🔧 VALVE BODIES — TOTAL")
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.center_alignment
        
        # ===== جدول ۲: ACTUATORS =====
        ws.merge_cells('F2:I2')
        cell = ws.cell(row=2, column=6, value="⚙️ ACTUATORS — TOTAL")
        cell.font = self.section_font
        cell.fill = self.section_fill
        cell.alignment = self.center_alignment
        
        ws.row_dimensions[2].height = 28
        
        # ===== هدر جدول‌ها =====
        header_row = 3
        for col_idx, header in enumerate(["No", "Valve Type", "Valve Model", "Qty"], 1):
            ws.cell(row=header_row, column=col_idx, value=header)
        for col_idx, header in enumerate(["No", "Actuator Model", "Signal", "Qty"], 6):
            ws.cell(row=header_row, column=col_idx, value=header)
        
        for col in list(range(1, 5)) + list(range(6, 10)):
            cell = ws.cell(row=header_row, column=col)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
        
        ws.row_dimensions[header_row].height = 25
        
        # ============================================================
        # جدول ۱: شیرها — جمع کل پروژه
        # ============================================================
        valve_groups = defaultdict(int)
        for valve in all_valves:
            vtype = valve.ValveType or 'Unknown'
            qty = int(valve.Quantity or 0)
            
            if vtype == 'PICV':
                valve_groups[('PICV', valve.PICVModel or '—')] += qty
            elif vtype == '3 Way':
                valve_groups[('3 Way', getattr(valve, '3WayModel', '') or '—')] += qty
            elif vtype == 'Steam':
                valve_groups[('Steam', valve.SteamModel or '—')] += qty
            elif vtype == 'PICV+3Way':
                valve_groups[('PICV', valve.PICVModel or '—')] += qty
                valve_groups[('3 Way', getattr(valve, '3WayModel', '') or '—')] += qty
            else:
                valve_groups[('Unknown', '—')] += qty
        
        sorted_valves = sorted(valve_groups.items(), key=lambda x: (x[0][0], -x[1]))
        
        row = header_row + 1
        valve_total = 0
        for i, ((v_type, v_model), qty) in enumerate(sorted_valves, 1):
            is_alt = (i % 2 == 0)
            for col_idx, value in enumerate([i, v_type, v_model, qty], 1):
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.font = self.body_font
                cell.alignment = self.center_alignment
                cell.border = self.thin_border
                cell.fill = self.alt_fill if is_alt else self.body_fill
            valve_total += qty
            ws.row_dimensions[row].height = 20
            row += 1
        
        total_row = row
        ws.cell(row=total_row, column=1, value="TOTAL")
        ws.cell(row=total_row, column=4, value=valve_total)
        for col in range(1, 5):
            cell = ws.cell(row=total_row, column=col)
            cell.font = self.total_font
            cell.fill = self.total_fill
            cell.alignment = self.center_alignment
            cell.border = self.thick_border
        ws.row_dimensions[total_row].height = 25
        
        # ============================================================
        # جدول ۲: موتورها — جمع کل پروژه
        # ============================================================
        actuator_groups = defaultdict(int)
        for valve in all_valves:
            vtype = valve.ValveType or ''
            actuator = signal = ''
            if vtype == 'PICV':
                actuator = valve.PICVActuator or ''
                signal = valve.PICVSignal or ''
            elif vtype == '3 Way':
                actuator = getattr(valve, '3WayActuator', '') or ''
                signal = getattr(valve, '3WaySignal', '') or ''
            elif vtype == 'Steam':
                actuator = valve.SteamActuator or ''
                signal = valve.SteamSignal or ''
            elif vtype == 'PICV+3Way':
                actuator = getattr(valve, '3WayActuator', '') or ''
                signal = getattr(valve, '3WaySignal', '') or ''
            if not actuator:
                continue
            actuator_groups[(actuator, signal)] += int(valve.Quantity or 0)
        
        sorted_actuators = sorted(actuator_groups.items(), key=lambda x: (-x[1], x[0][0]))
        
        row = header_row + 1
        actuator_total = 0
        for i, ((actuator, signal), qty) in enumerate(sorted_actuators, 1):
            is_alt = (i % 2 == 0)
            for col_idx, value in enumerate([i, actuator, signal or '—', qty], 6):
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.font = self.body_font
                cell.alignment = self.center_alignment
                cell.border = self.thin_border
                cell.fill = self.alt_fill if is_alt else self.body_fill
            actuator_total += qty
            ws.row_dimensions[row].height = 20
            row += 1
        
        total_row_2 = row
        ws.cell(row=total_row_2, column=6, value="TOTAL")
        ws.cell(row=total_row_2, column=9, value=actuator_total)
        for col in range(6, 10):
            cell = ws.cell(row=total_row_2, column=col)
            cell.font = self.total_font
            cell.fill = self.total_fill
            cell.alignment = self.center_alignment
            cell.border = self.thick_border
        ws.row_dimensions[total_row_2].height = 25
        
        # ===== خط جداکننده E =====
        for r in range(header_row, max(row, total_row_2) + 1):
            sep_cell = ws.cell(row=r, column=5)
            sep_cell.fill = PatternFill(
                start_color="D0D0D0", end_color="D0D0D0", fill_type="solid"
            )
        
    def _create_summary_sheet(self, by_section: Dict[str, List], all_valves: List):
        """
        ایجاد Sheet مستقل برای خلاصه سکشن‌ها
        
        شامل جدول:
        - جمع هر نوع شیر به تفکیک سکشن
        - ✅ PICV+3Way به دو ستون PICV و 3Way تفکیک می‌شود
        - جمع کل پروژه
        """
        if not by_section:
            return
        
        ws = self.wb.create_sheet("Summary — Sections")
        self._set_page_setup(ws)
        
        # ============================================================
        # عرض ستون‌ها
        # ============================================================
        col_widths = {
            'A': 6,     # #
            'B': 35,    # Section Name
            'C': 12,    # PICV
            'D': 12,    # 3 Way
            'E': 12,    # Steam
            'F': 12,    # Total Qty
        }
        for col_letter, width in col_widths.items():
            ws.column_dimensions[col_letter].width = width
        
        total_cols = 6  # A تا F
        
        # ============================================================
        # عنوان اصلی
        # ============================================================
        ws.merge_cells(
            start_row=1, start_column=1,
            end_row=1, end_column=total_cols
        )
        cell = ws.cell(row=1, column=1, value="📋 Section Summary — Valves Count")
        cell.font = self.title_font
        cell.fill = self.title_fill
        cell.alignment = self.center_alignment
        ws.row_dimensions[1].height = 35
        
        # ============================================================
        # زیرعنوان
        # ============================================================
        now = datetime.now()
        jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
        date_str = f"{jy}/{jm:02d}/{jd:02d}"
        
        project = self.app.get_current_project()
        project_name = project.name if project else "—"
        
        subtitle = (
            f"Project: {project_name}  |  "
            f"Sections: {len(by_section)}  |  "
            f"Total Valves: {len(all_valves)}  |  "
            f"Date: {date_str}"
        )
        ws.merge_cells(
            start_row=2, start_column=1,
            end_row=2, end_column=total_cols
        )
        cell = ws.cell(row=2, column=1, value=subtitle)
        cell.font = Font(
            name="Calibri", size=10, italic=True, color="7F8C8D"
        )
        cell.alignment = self.center_alignment
        ws.row_dimensions[2].height = 20
        
        # ============================================================
        # هدر جدول
        # ============================================================
        header_row = 4
        headers = [
            "#", "Section Name",
            "PICV", "3 Way", "Steam",
            "Total Qty",
        ]
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_idx, value=h)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
        ws.row_dimensions[header_row].height = 28
        
        # ============================================================
        # داده‌ها
        # ============================================================
        row = header_row + 1
        grand_total = 0
        grand_by_type = defaultdict(int)
        
        for i, (sec_name, sec_valves) in enumerate(by_section.items(), 1):
            # ============================================================
            # ✅ محاسبه‌ی تفکیکی — PICV+3Way به دو ستون پخش می‌شود
            # ============================================================
            picv_count = 0
            three_way_count = 0
            steam_count = 0
            
            for v in sec_valves:
                vtype = v.ValveType or 'Unknown'
                qty = int(v.Quantity or 0)
                
                if vtype == 'PICV':
                    picv_count += qty
                elif vtype == '3 Way':
                    three_way_count += qty
                elif vtype == 'Steam':
                    steam_count += qty
                elif vtype == 'PICV+3Way':
                    # ✅ یک شیر PICV+3Way = یک PICV + یک 3Way
                    picv_count += qty
                    three_way_count += qty
                # Unknown → نادیده یا اضافه به هیچ‌کدام
            
            sec_total = picv_count + three_way_count + steam_count
            grand_total += sec_total
            
            # جمع کل هر نوع
            grand_by_type['PICV'] += picv_count
            grand_by_type['3 Way'] += three_way_count
            grand_by_type['Steam'] += steam_count
            
            values = [
                i,
                sec_name,
                picv_count,
                three_way_count,
                steam_count,
                sec_total,
            ]
            
            is_alt = (i % 2 == 0)
            for col_idx, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.font = self.body_font
                cell.alignment = (
                    self.left_alignment if col_idx == 2
                    else self.center_alignment
                )
                cell.border = self.thin_border
                cell.fill = self.alt_fill if is_alt else self.body_fill
            
            ws.row_dimensions[row].height = 22
            row += 1
        
        # ============================================================
        # TOTAL نهایی
        # ============================================================
        total_row = row
        values = [
            "TOTAL",
            "All Sections",
            grand_by_type.get('PICV', 0),
            grand_by_type.get('3 Way', 0),
            grand_by_type.get('Steam', 0),
            grand_total,
        ]
        for col_idx, value in enumerate(values, 1):
            cell = ws.cell(row=total_row, column=col_idx, value=value)
            cell.font = self.total_font
            cell.fill = self.total_fill
            cell.alignment = (
                self.left_alignment if col_idx == 2
                else self.center_alignment
            )
            cell.border = self.thick_border
        
        ws.row_dimensions[total_row].height = 28
        
        # ============================================================
        # Freeze Panes
        # ============================================================
        ws.freeze_panes = f"A{header_row + 1}"
        
    # ================================================================
    # 6. متدهای کمکی — ستون‌ها
    # ================================================================
    
    def _get_columns_for_type(self, valve_type: str) -> List[tuple]:
        """
        دریافت ستون‌های مرتبط با نوع شیر
        
        Returns:
            لیست تاپل (key, label, width, align)
        """
        # ===== ستون‌های پایه (همه انواع) =====
        base_columns = [
            ('no', 'No', 5, 'center'),
            ('equipment', 'Equipment', 25, 'center'),
            ('quantity', 'Qty', 6, 'center'),
            ('circuit', 'Circuit', 12, 'center'),
            ('flow', 'Flow', 8, 'center'),
            ('pressure_drop', 'PD (psi)', 8, 'center'),
            ('unit', 'Unit', 8, 'center'),
            ('valve_type', 'Valve Type', 12, 'center'),
            ('max_flow_lph', 'Max Flow (L/HR)', 12, 'center'),
        ]
        
        # ===== ستون‌های مخصوص هر نوع =====
        if valve_type == 'PICV':
            type_columns = [
                ('picv_model', 'PICV Model', 15, 'center'),
                ('picv_max_flow', 'PICV Max Flow', 12, 'center'),
                ('picv_percent', 'PICV %', 8, 'center'),
                ('picv_actuator', 'PICV Actuator', 20, 'center'),
                ('picv_signal', 'PICV Signal', 15, 'center'),
            ]
        
        elif valve_type == '3 Way':
            type_columns = [
                ('kv_calc', 'Kv Calc', 8, 'center'),
                ('kv_selected', 'Kv Selected', 10, 'center'),
                # ✅ DN حذف شد
                ('3way_model', 'Valve Model', 20, 'center'),
                ('3way_actuator', 'Actuator', 18, 'center'),
                ('3way_signal', 'Signal', 15, 'center'),
            ]
        
        elif valve_type == 'Steam':
            type_columns = [
                ('steam_pressure', 'Steam Inlet (bar)', 12, 'center'),
                ('kvs_calc', 'kvs Calc', 8, 'center'),
                ('kvs_selected', 'kvs Selected', 10, 'center'),
                # ✅ DN حذف شد
                ('steam_model', 'Valve Model', 20, 'center'),
                ('steam_actuator', 'Actuator', 18, 'center'),
                ('steam_signal', 'Signal', 15, 'center'),
            ]
        
        elif valve_type == 'PICV+3Way':
            type_columns = [
                ('picv_model', 'PICV Model', 15, 'center'),
                ('picv_max_flow', 'PICV Max', 10, 'center'),
                ('picv_percent', 'PICV %', 8, 'center'),
                # بدون Actuator PICV
                ('kv_calc', 'Kv Calc', 8, 'center'),
                ('kv_selected', 'Kv Sel', 8, 'center'),
                # ✅ DN حذف شد
                ('3way_model', 'Model', 20, 'center'),
                ('3way_actuator', 'Actuator', 18, 'center'),
                ('3way_signal', 'Signal', 15, 'center'),
            ]
        
        else:
            type_columns = []
        
        # ===== ستون هشدار (آخر) =====
        warning_columns = [
            ('warning', 'Warning', 30, 'center'),
        ]
        
        return base_columns + type_columns + warning_columns
    
    def _get_all_columns(self, all_valves) -> List[tuple]:
        """
        دریافت ستون‌های فعال بر اساس انواع موجود در all_valves
        """
        # ===== ۱. تشخیص انواع موجود =====
        existing_types = set()
        for valve in all_valves:
            if valve.ValveType:
                existing_types.add(valve.ValveType)
        
        # ===== ۲. ستون‌های پایه (همیشه) =====
        columns = [
            ('no', 'No', 5, 'center'),
            ('equipment', 'Equipment', 20, 'center'),
            ('quantity', 'Qty', 6, 'center'),
            ('circuit', 'Circuit', 10, 'center'),
            ('flow', 'Flow', 8, 'center'),
            ('pressure_drop', 'PD (psi)', 8, 'center'),
            ('unit', 'Unit', 8, 'center'),
            ('valve_type', 'Valve Type', 10, 'center'),
            ('max_flow_lph', 'Max Flow (L/HR)', 12, 'center'),
        ]
        
        # ===== ۳. ستون‌های PICV (اگر PICV یا PICV+3Way موجود است) =====
        if 'PICV' in existing_types or 'PICV+3Way' in existing_types:
            columns.extend([
                ('picv_model', 'PICV Model', 15, 'center'),
                ('picv_max_flow', 'PICV Max', 10, 'center'),
                ('picv_percent', 'PICV %', 8, 'center'),
                ('picv_actuator', 'PICV Actuator', 20, 'center'),
                ('picv_signal', 'PICV Signal', 15, 'center'),
            ])
        
        # ===== ۴. ستون‌های 3Way =====
        if '3 Way' in existing_types or 'PICV+3Way' in existing_types:
            columns.extend([
                ('kv_calc', 'Kv Calc', 8, 'center'),
                ('kv_selected', 'Kv Sel', 8, 'center'),
                # ✅ DN حذف شد
                ('3way_model', '3W Model', 20, 'center'),
                ('3way_actuator', '3W Actuator', 18, 'center'),
                ('3way_signal', '3W Signal', 15, 'center'),
            ])
        
        # ===== ۵. ستون‌های Steam =====
        if 'Steam' in existing_types:
            columns.extend([
                ('steam_pressure', 'Steam (bar)', 10, 'center'),
                ('kvs_calc', 'kvs Calc', 8, 'center'),
                ('kvs_selected', 'kvs Sel', 8, 'center'),
                # ✅ DN حذف شد
                ('steam_model', 'Steam Model', 20, 'center'),
                ('steam_actuator', 'Steam Act', 18, 'center'),
                ('steam_signal', 'Steam Sig', 15, 'center'),
            ])
        
        # ===== ۶. ستون هشدار (آخر) =====
        columns.append(('warning', 'Warning', 30, 'center'))
        
        return columns
    
    def _get_cell_value(self, valve, key: str, index: int):
        """دریافت مقدار یک سلول — فقط فیلدهای مرتبط با نوع شیر"""
        try:
            # ============================================================
            # فیلدهای پایه (همه انواع)
            # ============================================================
            if key == 'no':
                return index
            elif key == 'equipment':
                return valve.Equipment or ''
            elif key == 'quantity':
                return int(valve.Quantity or 0)
            elif key == 'circuit':
                return valve.Circuit or ''
            elif key == 'flow':
                return self._safe_float(valve.Flow)
            elif key == 'pressure_drop':
                return self._safe_float(valve.PressureDrop)
            elif key == 'unit':
                return valve.Unit or ''
            elif key == 'valve_type':
                return valve.ValveType or ''
            elif key == 'max_flow_lph':
                return f"{self._safe_float(valve.MaxFlowLPH):.0f}"
            
            # ============================================================
            # ✅ تشخیص نوع شیر — فقط فیلدهای همان نوع برگردانده می‌شوند
            # ============================================================
            vtype = valve.ValveType or ''
            is_picv = (vtype == 'PICV')
            is_3way = (vtype == '3 Way')
            is_steam = (vtype == 'Steam')
            is_picv_3way = (vtype == 'PICV+3Way')
            
            # ============================================================
            # PICV — فقط برای PICV و PICV+3Way
            # ============================================================
            if key == 'picv_model':
                if is_picv or is_picv_3way:
                    return valve.PICVModel or ''
                return ''
            
            elif key == 'picv_max_flow':
                if is_picv or is_picv_3way:
                    return (
                        f"{self._safe_float(valve.PICVMaxFlow):.0f}"
                        if valve.PICVMaxFlow else ''
                    )
                return ''
            
            elif key == 'picv_percent':
                if is_picv or is_picv_3way:
                    return (
                        f"{self._safe_float(valve.PICVPercent):.1f}%"
                        if valve.PICVPercent else ''
                    )
                return ''
            
            elif key == 'picv_actuator':
                if is_picv:  # ← فقط PICV خالص، نه PICV+3Way
                    return valve.PICVActuator or ''
                return ''
            
            elif key == 'picv_signal':
                if is_picv:  # ← فقط PICV خالص
                    return valve.PICVSignal or ''
                return ''
            
            # ============================================================
            # 3Way — فقط برای 3Way و PICV+3Way
            # ============================================================
            elif key == 'kv_calc':
                if is_3way or is_picv_3way:
                    return (
                        f"{self._safe_float(valve.KvCalc):.2f}"
                        if valve.KvCalc else ''
                    )
                return ''
            
            elif key == 'kv_selected':
                if is_3way or is_picv_3way:
                    return (
                        f"{self._safe_float(valve.KvSelected):.2f}"
                        if valve.KvSelected else ''
                    )
                return ''
            
            elif key == '3way_dn':
                if is_3way or is_picv_3way:
                    dn = getattr(valve, '3WayDN', 0) or 0
                    return f"DN{dn}" if dn else ''
                return ''
            
            elif key == '3way_model':
                if is_3way or is_picv_3way:
                    return getattr(valve, '3WayModel', '') or ''
                return ''
            
            elif key == '3way_actuator':
                if is_3way or is_picv_3way:
                    return getattr(valve, '3WayActuator', '') or ''
                return ''
            
            elif key == '3way_signal':
                if is_3way or is_picv_3way:
                    return getattr(valve, '3WaySignal', '') or ''
                return ''
            
            # ============================================================
            # Steam — فقط برای Steam
            # ============================================================
            elif key == 'steam_pressure':
                if is_steam:
                    return self._safe_float(valve.SteamPressure)
                return ''
            
            elif key == 'kvs_calc':
                if is_steam:
                    return (
                        f"{self._safe_float(valve.KvsCalc):.2f}"
                        if valve.KvsCalc else ''
                    )
                return ''
            
            elif key == 'kvs_selected':
                if is_steam:
                    return (
                        f"{self._safe_float(valve.KvsSelected):.2f}"
                        if valve.KvsSelected else ''
                    )
                return ''
            
            elif key == 'steam_dn':
                if is_steam:
                    dn = valve.SteamDN or 0
                    return f"DN{dn}" if dn else ''
                return ''
            
            elif key == 'steam_model':
                if is_steam:
                    return valve.SteamModel or ''
                return ''
            
            elif key == 'steam_actuator':
                if is_steam:
                    return valve.SteamActuator or ''
                return ''
            
            elif key == 'steam_signal':
                if is_steam:
                    return valve.SteamSignal or ''
                return ''
            
            # ============================================================
            # Warning — برای همه انواع (هر هشداری که دارد)
            # ============================================================
            elif key == 'warning':
                warnings = []
                if is_3way or is_picv_3way:
                    if valve.Warning3Way:
                        warnings.append(valve.Warning3Way)
                if is_steam:
                    if valve.WarningSteam:
                        warnings.append(valve.WarningSteam)
                if valve.WarningGeneral and not warnings:
                    warnings.append(valve.WarningGeneral)
                return ' | '.join(warnings) if warnings else ''
        
        except Exception:
            return ''
        
        return ''
    
    # ================================================================
    # 7. جمع‌آوری همه شیرها
    # ================================================================
    
    def _collect_valves_by_section(self) -> Dict[str, List]:
        """
        جمع‌آوری شیرها به تفکیک سکشن از رویژن فعلی
        
        Returns:
            dict: {section_name: [valves]}
        """
        project = self.app.get_current_project()
        if not project:
            return {}
        
        current_revision = project.get_current_revision()
        if not current_revision:
            return {}
        
        result = {}
        for section in current_revision.sections:
            section_name = getattr(section, 'name', None) or f"Section_{id(section)}"
            valves = list(getattr(section, 'valves', []) or [])
            if valves:
                result[section_name] = valves
        
        return result


    def _collect_all_valves(self) -> List:
        """جمع‌آوری همه شیرها از همه سکشن‌های رویژن فعلی"""
        all_valves = []
        for valves in self._collect_valves_by_section().values():
            all_valves.extend(valves)
        return all_valves
    
    # ================================================================
    # 8. متد اصلی Export
    # ================================================================
    
    def export_full_report(self, file_path: str = None) -> Optional[str]:
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
        
        # ============================================================
        # جمع‌آوری شیرها — به تفکیک سکشن
        # ============================================================
        by_section = self._collect_valves_by_section()
        
        if not by_section:
            from tkinter import messagebox
            messagebox.showwarning(
                "Warning",
                "No valves found in any section of this revision!"
            )
            return None
        
        all_valves = []
        for valves in by_section.values():
            all_valves.extend(valves)
        
        # ============================================================
        # دیالوگ ذخیره
        # ============================================================
        if not file_path:
            from tkinter import filedialog
            safe_rev = "".join(
                c if c.isalnum() or c in " _-" else "_" for c in revision_name
            ).strip() or "Rev"
            safe_proj = "".join(
                c if c.isalnum() or c in " _-" else "_" for c in project.name
            ).strip() or "Project"
            timestamp = get_timestamp_for_filename()
            
            try:
                project_dir = self.app.attachment_manager.ensure_project_dir(project.name)
                reports_dir = os.path.join(project_dir, "Reports")
                os.makedirs(reports_dir, exist_ok=True)
                default_dir = reports_dir
            except Exception:
                default_dir = os.path.expanduser("~")
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Save Valves Excel Report",
                initialdir=default_dir,
                initialfile=f"Valves_List({safe_proj})_{safe_rev}_{timestamp}.xlsx",
            )
            if not file_path:
                return None
        
        # ============================================================
        # ساخت Sheets
        # ============================================================
        try:
            # ۱. Cover
            self._create_cover_sheet(project, revision_name)
            
            # ۲. یک Sheet به ازای هر سکشن
            for sec_name, sec_valves in by_section.items():
                self._create_section_sheet(sec_name, sec_valves)
            
            # ۳. Sheet های تفکیک بر اساس نوع (کل پروژه)
            picv_valves = [v for v in all_valves if v.ValveType == 'PICV']
            three_way_valves = [v for v in all_valves if v.ValveType == '3 Way']
            steam_valves = [v for v in all_valves if v.ValveType == 'Steam']
            picv_3way_valves = [v for v in all_valves if v.ValveType == 'PICV+3Way']
            
            self._create_valve_type_sheet(
                'PICV', picv_valves, 'Valves — PICV', self.picv_color
            )
            self._create_valve_type_sheet(
                '3 Way', three_way_valves, 'Valves — 3 Way', self.three_way_color
            )
            self._create_valve_type_sheet(
                'Steam', steam_valves, 'Valves — Steam', self.steam_color
            )
            self._create_valve_type_sheet(
                'PICV+3Way', picv_3way_valves, 'Valves — PICV+3Way',
                self.accent_color
            )
            
            # ۴. Sheet جامع
            self._create_all_sheet(all_valves)
            
            # ۵. LOM TOTAL (جمع کل پروژه + خلاصه سکشن‌ها)
            self._create_lom_total_sheet(all_valves, by_section)

            # ۶. ✅ Sheet مستقل Summary Sections      ← 🆕 این دو خط
            self._create_summary_sheet(by_section, all_valves)
            
            # ============================================================
            # ذخیره
            # ============================================================
            self.wb.save(file_path)
            
            if os.name == 'nt':
                os.startfile(file_path)
            
            from tkinter import messagebox
            messagebox.showinfo(
                "Success",
                f"Valves Excel Report saved to:\n{file_path}\n\n"
                f"📁 Project: {project.name}\n"
                f"📌 Revision: {revision_name}\n"
                f"🗂 Sections: {len(by_section)}\n"
                f"🔧 Total Valves: {len(all_valves)}"
            )
            return file_path
        
        except Exception as e:
            from tkinter import messagebox
            import traceback
            traceback.print_exc()
            messagebox.showerror(
                "Excel Export Error",
                f"Failed to generate Valves Excel:\n{str(e)}"
            )
            return None

# ================================================================
# EXPORTS
# ================================================================

__all__ = ['ValvesExcelExporter']