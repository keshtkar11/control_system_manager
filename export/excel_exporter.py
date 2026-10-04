# export/excel_exporter.py

"""خروجی‌های Excel با گزارش‌های حرفه‌ای - سایز A3 Landscape"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import math

from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side,
    NamedStyle, numbers
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins
from openpyxl.worksheet.dimensions import ColumnDimension, DimensionHolder
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.formatting.rule import ColorScaleRule
from export.excel_styles import ExcelStyles
from export.excel_utils import ExcelUtils
from core.constants import get_timestamp_for_filename
from collections import defaultdict

from core import Motor, Project, COMPONENT_LABELS, COMPONENT_KEYS
from core.constants import IO_CALCULATION, CABLE_SIZE, EXCLUDED_FROM_COMPONENTS, COLORS
from core.constants import gregorian_to_jalali


class ExcelExporter:
    """صادرکننده گزارش Excel حرفه‌ای - سایز A3 Landscape"""

    def __init__(self, app):
        self.app = app
        self.wb = Workbook()
        self.styles = ExcelStyles()
        self.utils = ExcelUtils(self.styles)
        self.company_name = "Vahhaj Sanat Energy Co."
        self.designer_name = "Mr.Keshtkar"

        # ===== رنگ‌ها =====
        self.primary_color = "1F4E79"
        self.secondary_color = "2C3E50"
        self.accent_color = "3498DB"
        self.success_color = "27AE60"
        self.warning_color = "F39C12"
        self.danger_color = "E74C3C"
        self.light_color = "F8F9FA"
        self.white_color = "FFFFFF"
        self.dark_color = "2C3E50"
        self.total_bg_color = "E6E6FA"

        # ===== استایل‌ها =====
        self.title_font = Font(name="Calibri", size=18, bold=True, color=self.white_color)
        self.subtitle_font = Font(name="Calibri", size=14, bold=True, color=self.primary_color)
        self.section_font = Font(name="Calibri", size=12, bold=True, color=self.white_color)
        self.header_font = Font(name="Calibri", size=10, bold=True, color=self.white_color)
        self.body_font = Font(name="Calibri", size=9, color="000000")
        self.body_bold_font = Font(name="Calibri", size=9, bold=True, color="000000")
        self.total_font = Font(name="Calibri", size=10, bold=True, color="000000")

        self.title_fill = PatternFill(start_color=self.primary_color, end_color=self.primary_color, fill_type="solid")
        self.subtitle_fill = PatternFill(start_color="E8F4FD", end_color="E8F4FD", fill_type="solid")
        self.section_fill = PatternFill(start_color=self.secondary_color, end_color=self.secondary_color, fill_type="solid")
        self.header_fill = PatternFill(start_color=self.primary_color, end_color=self.primary_color, fill_type="solid")
        self.body_fill = PatternFill(start_color=self.white_color, end_color=self.white_color, fill_type="solid")
        self.alt_fill = PatternFill(start_color=self.light_color, end_color=self.light_color, fill_type="solid")
        self.total_fill = PatternFill(start_color=self.total_bg_color, end_color=self.total_bg_color, fill_type="solid")

        self.center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        self.left_alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        self.right_alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)

        self.thin_border = Border(
            left=Side(style="thin", color="D0D0D0"),
            right=Side(style="thin", color="D0D0D0"),
            top=Side(style="thin", color="D0D0D0"),
            bottom=Side(style="thin", color="D0D0D0")
        )

    # ================================================================
    # متدهای کمکی
    # ================================================================

    def _safe_int(self, value):
        """تبدیل امن به عدد صحیح"""
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
        """دریافت اندازه کابل برای کامپوننت"""
        return CABLE_SIZE.get(field, '2x1mm²')

    def _get_device_names_for_component(self, device, field: str, comp_qty: int) -> List[str]:
        """تولید نام دستگاه برای کامپوننت‌های چندتایی"""
        import re
        
        device_name = device.Name or "Unnamed"
        use_index = getattr(device, 'UseIndexNaming', True)
        
        names = []
        
        if use_index:
            # روش حروف
            for i in range(comp_qty):
                suffix = chr(ord('a') + i)
                names.append(f"{device_name}{suffix}")
        else:
            # روش شماره
            match = re.match(r'^(.*?)(\d+)$', device_name)
            
            if match:
                prefix = match.group(1)
                start_num = int(match.group(2))
                for i in range(comp_qty):
                    names.append(f"{prefix}{start_num + i}")
            else:
                # fallback به روش حروف
                for i in range(comp_qty):
                    suffix = chr(ord('a') + i)
                    names.append(f"{device_name}{suffix}")
        
        return names

    def _apply_header_style(self, ws, row: int, col_count: int):
        """اعمال استایل هدر"""
        for col in range(1, col_count + 1):
            cell = ws.cell(row=row, column=col)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border

    def _apply_body_style(self, ws, row: int, col_count: int, is_alt: bool = False):
        """اعمال استایل بدنه"""
        for col in range(1, col_count + 1):
            cell = ws.cell(row=row, column=col)
            cell.font = self.body_font
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
            if is_alt:
                cell.fill = self.alt_fill
            else:
                cell.fill = self.body_fill

    def _apply_total_style(self, ws, row: int, col_count: int):
        """اعمال استایل سطر TOTAL"""
        for col in range(1, col_count + 1):
            cell = ws.cell(row=row, column=col)
            cell.font = self.total_font
            cell.fill = self.total_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border

    def _set_column_widths(self, ws, widths: Dict[str, int]):
        """تنظیم عرض ستون‌ها"""
        for col_letter, width in widths.items():
            ws.column_dimensions[col_letter].width = width

    def _set_row_height(self, ws, row: int, height: int = 20):
        """تنظیم ارتفاع ردیف"""
        ws.row_dimensions[row].height = height

    def _set_page_setup(self, ws, is_cover: bool = False):
        """تنظیمات صفحه برای چاپ"""
        ws.page_setup.paperSize = ws.PAPERSIZE_A3
        ws.page_setup.orientation = 'landscape'
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_margins = PageMargins(left=0.5, right=0.5, top=0.75, bottom=0.75)
        ws.print_title_rows = '1:4'
        
        # ✅ فعال کردن Horizontally Centered
        ws.print_options.horizontalCentered = True
        
        # ✅ تنظیم نمایش Page Break View
        ws.sheet_view.view = 'pageBreakPreview'
        ws.sheet_view.zoomScale = 130
        
        # ===== فوتر =====
        if not is_cover:
            # ✅ افزودن شماره صفحه به فوتر (فقط برای صفحات غیر از Cover)
            ws.oddFooter.left.text = "© Vahhaj Sanat Energy Co."
            ws.oddFooter.left.size = 8
            ws.oddFooter.left.color = "1F4E79"
            ws.oddFooter.right.text = "Page &P of &N"
            
            ws.oddFooter.right.size = 8
            ws.oddFooter.right.color = "1F4E79"
        else:
            # صفحه Cover - بدون شماره صفحه
            ws.oddFooter.left.text = ""
            ws.oddFooter.right.text = ""

    def _add_auto_filter(self, ws, row: int, col_count: int):
        """افزودن AutoFilter"""
        ws.auto_filter.ref = f"A{row}:{get_column_letter(col_count)}{ws.max_row}"

    def _add_conditional_formatting(self, ws, row: int, col_count: int):
        """افزودن قالب‌بندی شرطی برای ستون‌های I/O"""
        for col in range(1, col_count + 1):
            col_letter = get_column_letter(col)
            ws.conditional_formatting.add(
                f"{col_letter}{row}:{col_letter}{ws.max_row}",
                ColorScaleRule(
                    start_type='min', start_color='E8F4FD',
                    mid_type='percentile', mid_value=50, mid_color='BDD7EE',
                    end_type='max', end_color='1F4E79'
                )
            )

    # ================================================================
    # 1. صفحه عنوان
    # ================================================================

    def _create_cover_sheet(self, project: Project, revision_name: str = "Rev-0"):
        """ایجاد صفحه عنوان (با نمایش Revision)"""
        ws = self.wb.active
        ws.title = "Cover"
        self._set_page_setup(ws, is_cover=True)

        # تنظیم عرض ستون‌ها
        self.utils.set_column_widths(ws, {
            'A': 20,
            'B': 40,
            'C': 20,
            'D': 40
        })

        # ===== عنوان اصلی =====
        self.utils.merge_and_center(ws, 1, 1, 1, 4, "CONTROL SYSTEM")
        ws['A1'].font = self.styles.title_font
        ws['A1'].alignment = self.styles.center_alignment
        ws.row_dimensions[1].height = 40

        self.utils.merge_and_center(ws, 2, 1, 2, 4, "BMS REPORT of PROJECT")
        ws['A2'].font = Font(name="Calibri", size=22, bold=True, color=self.styles.PRIMARY_COLOR)
        ws['A2'].alignment = self.styles.center_alignment
        ws.row_dimensions[2].height = 35

        self.utils.merge_and_center(ws, 3, 1, 3, 4, self.company_name)
        ws['A3'].font = Font(name="Calibri", size=14, bold=True, color=self.styles.SECONDARY_COLOR)
        ws['A3'].alignment = self.styles.center_alignment
        ws.row_dimensions[3].height = 25

        self.utils.merge_and_center(ws, 4, 1, 4, 4, f"Designed by: {self.designer_name}")
        ws['A4'].font = Font(name="Calibri", size=12, color=self.styles.SECONDARY_COLOR)
        ws['A4'].alignment = self.styles.center_alignment
        ws.row_dimensions[4].height = 25

        # ============================================================
        # ✅ Revision No. (با مقدار واقعی)
        # ============================================================
        self.utils.merge_and_center(ws, 5, 1, 5, 4, f"Revision: {revision_name}")
        ws['A5'].font = Font(name="Calibri", size=12, bold=True, color=self.styles.PRIMARY_COLOR)
        ws['A5'].alignment = self.styles.center_alignment
        ws.row_dimensions[5].height = 25

        # ===== خط جداکننده =====
        self.utils.merge_and_center(ws, 6, 1, 6, 4)
        ws['A6'].border = Border(bottom=Side(style='thick', color=self.styles.PRIMARY_COLOR))
        ws.row_dimensions[6].height = 10

        # ===== اطلاعات پروژه =====
        row = 8
        now = datetime.now()
        jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
        date_str = f"{jy}/{jm:02d}/{jd:02d} {now.hour:02d}:{now.minute:02d}"

        # ===== لیست اطلاعات پروژه =====
        info_items = [
            ("Project Name:", project.name),
            ("Revision:", revision_name),
            ("Client:", project.client_name or ""),
            ("Consultant:", project.consultant_name or ""),
            ("Contractor:", project.contractor_name or self.company_name),
            ("Designer:", project.designer_name or self.designer_name),
            ("Report Date:", date_str),                       # ✅
        ]

        for label, value in info_items:
            ws.cell(row=row, column=1, value=label).font = Font(name="Calibri", size=12, bold=True)
            ws.cell(row=row, column=2, value=value).font = Font(name="Calibri", size=12)
            ws.cell(row=row, column=1).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(row=row, column=2).alignment = Alignment(horizontal="left", vertical="center")
            ws.row_dimensions[row].height = 22
            row += 1

        # ===== خط جداکننده =====
        self.utils.merge_and_center(ws, row, 1, row, 4)
        ws[f'A{row}'].border = Border(bottom=Side(style='thin', color=self.styles.PRIMARY_COLOR))
        ws.row_dimensions[row].height = 10
        row += 1

        # ===== فوتر =====
        self.utils.merge_and_center(ws, row, 1, row, 4)
        ws[f'A{row}'].value = self.company_name
        ws[f'A{row}'].font = Font(name="Calibri", size=10, color=self.styles.SECONDARY_COLOR)
        ws[f'A{row}'].alignment = self.styles.center_alignment
        row += 1

        self.utils.merge_and_center(ws, row, 1, row, 4)
        ws[f'A{row}'].value = "Generated by Control System Manager"
        ws[f'A{row}'].font = Font(name="Calibri", size=9, color=self.styles.SECONDARY_COLOR)
        ws[f'A{row}'].alignment = self.styles.center_alignment

    # ================================================================
    # 2. خلاصه اجرایی
    # ================================================================

    def _create_executive_summary(self, project: Project, devices: List[Motor]):
        """ایجاد خلاصه اجرایی"""
        ws = self.wb.create_sheet("Executive Summary")
        self._set_page_setup(ws)

        # تنظیم عرض ستون‌ها
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20

        # ===== عنوان =====
        ws.merge_cells('A1:B1')
        ws['A1'].value = "1. EXECUTIVE SUMMARY"
        ws['A1'].font = self.section_font
        ws['A1'].fill = self.section_fill
        ws['A1'].alignment = self.center_alignment
        ws.row_dimensions[1].height = 30

        # ===== محاسبه آمار =====
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

        # ===== جدول =====
        headers = ["Metric", "Value"]
        data = [
            ["Total Sections", len(project.sections)],
            ["Total Devices", total_devices_count],
            ["Active Devices", active_devices_count],
            ["Total I/O Points", project.get_total_io()]
        ]

        row = 3
        for col, header in enumerate(headers, 1):
            ws.cell(row=row, column=col, value=header)
        self._apply_header_style(ws, row, 2)
        ws.row_dimensions[row].height = 25

        row += 1
        for i, item in enumerate(data):
            for col, value in enumerate(item, 1):
                ws.cell(row=row, column=col, value=value)
            self._apply_body_style(ws, row, 2, is_alt=(i % 2 == 1))
            ws.cell(row=row, column=1).alignment = self.left_alignment
            ws.row_dimensions[row].height = 22
            row += 1

    # ================================================================
    # 3. خلاصه I/O
    # ================================================================

    def _create_io_summary(self, devices: List[Motor]):
        """ایجاد خلاصه I/O"""
        ws = self.wb.create_sheet("I_O Summary")
        self._set_page_setup(ws)

        # تنظیم عرض ستون‌ها
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15

        # ===== عنوان =====
        ws.merge_cells('A1:C1')
        ws['A1'].value = "2. I_O Summary"
        ws['A1'].font = self.section_font
        ws['A1'].fill = self.section_fill
        ws['A1'].alignment = self.center_alignment
        ws.row_dimensions[1].height = 30

        total_di = sum(d.DI for d in devices)
        total_do = sum(d.DO for d in devices)
        total_ai = sum(d.AI for d in devices)
        total_ao = sum(d.AO for d in devices)
        total_io = total_di + total_do + total_ai + total_ao

        headers = ["I/O Type", "Count", "Percentage"]
        data = [
            ["Digital Input (DI)", total_di, f"{(total_di/total_io*100):.1f}%" if total_io > 0 else "0%"],
            ["Digital Output (DO)", total_do, f"{(total_do/total_io*100):.1f}%" if total_io > 0 else "0%"],
            ["Analog Input (AI)", total_ai, f"{(total_ai/total_io*100):.1f}%" if total_io > 0 else "0%"],
            ["Analog Output (AO)", total_ao, f"{(total_ao/total_io*100):.1f}%" if total_io > 0 else "0%"],
            ["TOTAL", total_io, "100%"]
        ]

        row = 3
        for col, header in enumerate(headers, 1):
            ws.cell(row=row, column=col, value=header)
        self._apply_header_style(ws, row, 3)
        ws.row_dimensions[row].height = 25

        row += 1
        for i, item in enumerate(data):
            for col, value in enumerate(item, 1):
                ws.cell(row=row, column=col, value=value)
            if i == len(data) - 1:
                self._apply_total_style(ws, row, 3)
            else:
                self._apply_body_style(ws, row, 3, is_alt=(i % 2 == 1))
                ws.cell(row=row, column=1).alignment = self.left_alignment
            ws.row_dimensions[row].height = 22
            row += 1

    # ================================================================
    # 4. تحلیل بخش‌ها
    # ================================================================

    def _create_sections(self, project: Project):
        """ایجاد تحلیل بخش‌ها - گروه‌بندی بر اساس (Section + Description)"""
        ws = self.wb.create_sheet("Sections")
        self._set_page_setup(ws)

        # تنظیم عرض ستون‌ها
        ws.column_dimensions['A'].width = 25   # Section Name
        ws.column_dimensions['B'].width = 40   # Device Description
        ws.column_dimensions['C'].width = 8    # Devices
        ws.column_dimensions['D'].width = 10   # Components  ← جدید
        ws.column_dimensions['E'].width = 5    # DI
        ws.column_dimensions['F'].width = 5    # DO
        ws.column_dimensions['G'].width = 5    # AI
        ws.column_dimensions['H'].width = 5    # AO
        ws.column_dimensions['I'].width = 12   # Total I/O
        ws.column_dimensions['J'].width = 10   # Percentage

        # ===== عنوان =====
        ws.merge_cells('A1:j1')
        ws['A1'].value = "3. IO List for each Device of Project "
        ws['A1'].font = self.section_font
        ws['A1'].fill = self.section_fill
        ws['A1'].alignment = self.center_alignment
        ws.row_dimensions[1].height = 30

        # ================================================================
        # ✅ گروه‌بندی بر اساس (Section + Description)
        # ================================================================
        description_groups = {}

        for section in project.sections:
            section_label = getattr(section, 'display_name', None) or section.name
            for device in section.devices:
                desc = device.Description or "Unknown"
                
                # ✅ کلید ترکیبی: (نام بخش، توضیحات)
                group_key = (section.name, desc)
                
                if group_key not in description_groups:
                    description_groups[group_key] = {
                        'section': section_label,
                        'description': desc,
                        'device_count': 0,      # ✅ تعداد Device های واقعی
                        'component_count': 0,   # ✅ تعداد کل قطعات
                        'di': 0,
                        'do': 0,
                        'ai': 0,
                        'ao': 0
                    }

                # ============================================================
                # ✅ محاسبه device_count (تعداد Device واقعی)
                # ============================================================
                device_count = 1
                for field in COMPONENT_KEYS:
                    if field in ['PU', 'VSD']:
                        qty = self._safe_int(getattr(device, field, 0))
                        if qty > 0:
                            device_count = qty
                            break

                # ============================================================
                # ✅ محاسبه component_count (مجموع کل قطعات این Device)
                # ============================================================
                # همه کامپوننت‌ها (به جز EXCLUDED)
                component_count = 0
                for field in COMPONENT_KEYS:
                    if field in EXCLUDED_FROM_COMPONENTS:
                        continue
                    qty = self._safe_int(getattr(device, field, 0))
                    component_count += qty

                description_groups[group_key]['device_count'] += device_count
                description_groups[group_key]['component_count'] += component_count
                description_groups[group_key]['di'] += device.DI
                description_groups[group_key]['do'] += device.DO
                description_groups[group_key]['ai'] += device.AI
                description_groups[group_key]['ao'] += device.AO

        total_io = project.get_total_io()

        # ===== جدول =====
        headers = ["Section Name", "Device Description", "Devices", "Components", "DI", "DO", "AI", "AO", "Total I/O", "Percentage"]

        row = 3
        for col, header in enumerate(headers, 1):
            ws.cell(row=row, column=col, value=header)
        self._apply_header_style(ws, row, len(headers))
        ws.row_dimensions[row].height = 25

        row += 1
        row_idx = 0
        
        # ================================================================
        # ✅ نمایش گروه‌ها (با ترتیب بخش‌ها)
        # ================================================================
        for group_key, data in description_groups.items():
            group_io = data['di'] + data['do'] + data['ai'] + data['ao']
            percentage = (group_io / total_io * 100) if total_io > 0 else 0

            values = [
                data['section'],           # A: نام بخش
                data['description'],       # B: توضیحات دستگاه
                data['device_count'],      # C: تعداد Device
                data['component_count'],   # D: تعداد کل قطعات ✅ جدید
                data['di'],                # E: DI
                data['do'],                # F: DO
                data['ai'],                # G: AI
                data['ao'],                # H: AO
                group_io,                  # I: Total I/O
                f"{percentage:.1f}%"       # J: Percentage
            ]

            for col, value in enumerate(values, 1):
                ws.cell(row=row, column=col, value=value)
            self._apply_body_style(ws, row, len(headers), is_alt=(row_idx % 2 == 1))
            ws.cell(row=row, column=1).alignment = self.left_alignment
            ws.cell(row=row, column=2).alignment = self.left_alignment
            ws.row_dimensions[row].height = 22
            row += 1
            row_idx += 1
            
    # ================================================================
    # 5. LOM All Sections
    # ================================================================

    def _create_lom_all(self, devices: List[Motor]):
        """ایجاد لیست مواد - کلی با ستون Model-Order Number"""
        ws = self.wb.create_sheet("LOM All Sections")
        self._set_page_setup(ws)

        # ============================================================
        # ✅ تنظیم عرض ستون‌ها
        # A=Component, B=Qty, C=DI, D=DO, E=AI, F=AO, G=Model-Order
        # ============================================================
        ws.column_dimensions['A'].width = 30   # Component
        ws.column_dimensions['B'].width = 10   # Qty
        ws.column_dimensions['C'].width = 5    # DI
        ws.column_dimensions['D'].width = 5    # DO
        ws.column_dimensions['E'].width = 5    # AI
        ws.column_dimensions['F'].width = 5    # AO
        ws.column_dimensions['G'].width = 20   # Model-Order Number

        # ===== عنوان =====
        ws.merge_cells('A1:G1')
        ws['A1'].value = "4.1. LOM For All Sections (Summary)"
        ws['A1'].font = self.section_font
        ws['A1'].fill = self.section_fill
        ws['A1'].alignment = self.center_alignment
        ws.row_dimensions[1].height = 30

        # ============================================================
        # ✅ جدید: جمع‌آوری با گروه‌بندی (field, model_order)
        # ============================================================
        grouped_usage = {}   # {(field, model_order): {'qty': ..., 'di': ..., ...}}

        for device in devices:
            for field in COMPONENT_KEYS:
                if field in EXCLUDED_FROM_COMPONENTS:
                    continue
                qty = self._safe_int(getattr(device, field, 0))
                if qty > 0:
                    # ✅ Model-Order این کامپوننت در این دستگاه
                    model_order = device.get_model_order(field)

                    # ✅ کلید گروه
                    key = (field, model_order)
                    if key not in grouped_usage:
                        grouped_usage[key] = {"qty": 0, "di": 0, "do": 0, "ai": 0, "ao": 0}

                    grouped_usage[key]["qty"] += qty

                    if field in IO_CALCULATION:
                        io = IO_CALCULATION[field]
                        grouped_usage[key]["di"] += qty * io.get("DI", 0)
                        grouped_usage[key]["do"] += qty * io.get("DO", 0)
                        grouped_usage[key]["ai"] += qty * io.get("AI", 0)
                        grouped_usage[key]["ao"] += qty * io.get("AO", 0)

        # ============================================================
        # ✅ ستون‌های Active از component های یکتا
        # ============================================================
        active_keys = sorted(set(field for field, _ in grouped_usage.keys()))

        # ============================================================
        # ✅ ساخت هدر جدول (Model-Order در ستون G)
        # ============================================================
        headers = ["Component", "Qty", "DI", "DO", "AI", "AO", "Model-Order Number"]

        for key in active_keys:
            headers.append(key)

        total_cols = len(headers)

        # ============================================================
        # ✅ تنظیم عرض ستون‌های Active (از ستون H شروع می‌شود)
        # A=1, B=2, C=3, D=4, E=5, F=6, G=7 (Model-Order), H=8 (Active)
        # ============================================================
        for i, key in enumerate(active_keys):
            col_letter = get_column_letter(8 + i)
            ws.column_dimensions[col_letter].width = 8

        # ============================================================
        # ✅ نوشتن هدر
        # ============================================================
        row = 3
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            if col <= 7:   # 7 ستون پایه (A-G)
                self.styles.apply_style(cell, 'TableHeader')
            else:   # ستون‌های Active
                self.styles.apply_style(cell, 'ActiveHeader')
        ws.row_dimensions[row].height = 25

        # ============================================================
        # ✅ نوشتن داده‌ها (گروه‌بندی بر اساس component + model_order)
        # ============================================================
        if grouped_usage:
            # ============================================================
            # ✅ مرتب‌سازی: component (الفبا)، سپس model_order (خالی آخر)
            # ============================================================
            sorted_usage = sorted(
                grouped_usage.items(),
                key=lambda x: (
                    x[0][0],                       # component name
                    x[0][1] == '',                 # خالی آخر
                    x[0][1] if x[0][1] else '',    # model_order
                )
            )

            row += 1
            for i, ((field, model_order), data) in enumerate(sorted_usage):
                name = self._get_component_name(field)

                # ===== مقادیر پایه (با Model-Order) =====
                values = [
                    name,               # A: Component
                    data["qty"],        # B: Qty
                    data["di"],         # C: DI
                    data["do"],         # D: DO
                    data["ai"],         # E: AI
                    data["ao"],         # F: AO
                    model_order or '',  # G: Model-Order (خالی اگر نبود)
                ]

                # ===== مقادیر Active =====
                for key in active_keys:
                    if key == field:
                        values.append(data["qty"])
                    else:
                        values.append(0)

                # ===== ستون‌های پایه =====
                for col in range(1, 8):
                    cell = ws.cell(row=row, column=col, value=values[col - 1])
                    self.styles.apply_style(cell, 'TableBodyAlt' if i % 2 == 1 else 'TableBody')
                    if col == 1:   # Component چپ‌چین
                        cell.alignment = self.styles.left_alignment

                # ===== ستون‌های Active Components =====
                for j, key in enumerate(active_keys):
                    col = 8 + j
                    value = values[7 + j]
                    cell = ws.cell(row=row, column=col, value=value)
                    if value > 0:
                        self.styles.apply_style(cell, 'ActivePositive')
                    else:
                        self.styles.apply_style(cell, 'ActiveZero')

                ws.row_dimensions[row].height = 22
                row += 1

            # ============================================================
            # ✅ سطر TOTAL
            # ============================================================
            total_di = sum(data["di"] for data in grouped_usage.values())
            total_do = sum(data["do"] for data in grouped_usage.values())
            total_ai = sum(data["ai"] for data in grouped_usage.values())
            total_ao = sum(data["ao"] for data in grouped_usage.values())
            total_qty = sum(data["qty"] for data in grouped_usage.values())

            total_values = ["TOTAL", total_qty, total_di, total_do, total_ai, total_ao, ""]

            # ستون‌های Active: مجموع per-component (نه per-group)
            for key in active_keys:
                col_qty = sum(
                    d["qty"]
                    for (f, _), d in grouped_usage.items()
                    if f == key
                )
                total_values.append(col_qty)

            # ===== سطر TOTAL - ستون‌های پایه =====
            for col in range(1, 8):
                cell = ws.cell(row=row, column=col, value=total_values[col - 1])
                self.styles.apply_style(cell, 'Total')

            # ===== سطر TOTAL - ستون‌های Active =====
            for j, key in enumerate(active_keys):
                col = 8 + j
                cell = ws.cell(row=row, column=col, value=total_values[7 + j])
                self.styles.apply_style(cell, 'ActiveTotal')

            ws.row_dimensions[row].height = 25

    # ================================================================
    # 6. LOM By Section
    # ================================================================

    def _create_lom_by_section(self, project: Project):
        """ایجاد لیست مواد - به تفکیک بخش با هدر تکراری و سطر مجموع برای هر بخش"""
        ws = self.wb.create_sheet("LOM By Section")
        self._set_page_setup(ws)

        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 5
        ws.column_dimensions['E'].width = 5
        ws.column_dimensions['F'].width = 5
        ws.column_dimensions['G'].width = 5

        ws.merge_cells('A1:G1')
        ws['A1'].value = "4.2. LOM For each Section"
        ws['A1'].font = self.section_font
        ws['A1'].fill = self.section_fill
        ws['A1'].alignment = self.center_alignment
        ws.row_dimensions[1].height = 30

        # ===== جمع‌آوری همه کامپوننت‌های فعال در تمام بخش‌ها =====
        all_active_keys = set()
        for section in project.sections:
            for device in section.devices:
                for field in COMPONENT_KEYS:
                    if field in EXCLUDED_FROM_COMPONENTS:
                        continue
                    qty = self._safe_int(getattr(device, field, 0))
                    if qty > 0:
                        all_active_keys.add(field)
        
        active_keys = sorted(list(all_active_keys))

        headers = ["Section", "Component", "Qty", "DI", "DO", "AI", "AO"]
        for key in active_keys:
            headers.append(key)

        total_cols = len(headers)

        # ===== تنظیم عرض ستون‌های Active =====
        for i, key in enumerate(active_keys):
            col_letter = get_column_letter(8 + i)
            ws.column_dimensions[col_letter].width = 8

        # ===== متغیرهای جمع کل پروژه =====
        grand_total_qty = 0
        grand_total_di = 0
        grand_total_do = 0
        grand_total_ai = 0
        grand_total_ao = 0
        
        grand_total_active = {}
        for key in active_keys:
            grand_total_active[key] = 0

        row = 3
        
        # ===== برای هر بخش =====
        for section in project.sections:
            if not section.devices:
                continue

            # ✅ اضافه شد: نام نمایشی سکشن — Name (Description)
            section_display = (
                getattr(section, 'display_name', None)
                or getattr(section, 'name', None)
                or 'Unknown Section'
            )

            section_usage = {}
            for device in section.devices:
                for field in COMPONENT_KEYS:
                    if field in EXCLUDED_FROM_COMPONENTS:
                        continue
                    qty = self._safe_int(getattr(device, field, 0))
                    if qty > 0:
                        if field not in section_usage:
                            section_usage[field] = {"qty": 0, "di": 0, "do": 0, "ai": 0, "ao": 0}
                        section_usage[field]["qty"] += qty

                        if field in IO_CALCULATION:
                            io = IO_CALCULATION[field]
                            section_usage[field]["di"] += qty * io.get("DI", 0)
                            section_usage[field]["do"] += qty * io.get("DO", 0)
                            section_usage[field]["ai"] += qty * io.get("AI", 0)
                            section_usage[field]["ao"] += qty * io.get("AO", 0)

            if not section_usage:
                continue

            # ===== عنوان بخش =====
            ws.merge_cells(
                start_row=row,
                start_column=1,
                end_row=row,
                end_column=total_cols
            )
            # ✅ استفاده از section_display (تعریف‌شده در بالا)
            cell = ws.cell(row=row, column=1, value=f"📁 {section_display}")
            cell.font = Font(bold=True, color="FFFFFF", size=10, name="Calibri")
            cell.fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
            cell.alignment = Alignment(horizontal="left", vertical="center")
            ws.row_dimensions[row].height = 25
            row += 1

            # ===== هدر جدول برای این بخش =====
            headers = ["Section", "Component", "Qty", "DI", "DO", "AI", "AO"]
            for key in active_keys:
                headers.append(key)

            total_cols = len(headers)

            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=row, column=col, value=header)
                if col <= 7:
                    self.styles.apply_style(cell, 'TableHeader')
                else:
                    self.styles.apply_style(cell, 'ActiveHeader')
            ws.row_dimensions[row].height = 25
            row += 1

            # ===== محاسبه مجموع این بخش =====
            section_total_qty = 0
            section_total_di = 0
            section_total_do = 0
            section_total_ai = 0
            section_total_ao = 0
            
            section_total_active = {}
            for key in active_keys:
                section_total_active[key] = 0

            # ===== داده‌های این بخش =====
            sorted_section = sorted(section_usage.items(), key=lambda x: x[1]["qty"], reverse=True)

            for i, (field, data) in enumerate(sorted_section):
                name = self._get_component_name(field)
                
                # جمع این بخش
                section_total_qty += data["qty"]
                section_total_di += data["di"]
                section_total_do += data["do"]
                section_total_ai += data["ai"]
                section_total_ao += data["ao"]
                
                if field in section_total_active:
                    section_total_active[field] += data["qty"]
                
                # ✅ استفاده از section_display در ستون Section
                values = [section_display, name, data["qty"], data["di"], data["do"], data["ai"], data["ao"]]
                
                # مقادیر Active
                for key in active_keys:
                    if key == field:
                        values.append(data["qty"])
                    else:
                        values.append(0)
                
                # ===== ستون‌های پایه =====
                for col in range(1, 8):
                    cell = ws.cell(row=row, column=col, value=values[col - 1])
                    self.styles.apply_style(cell, 'TableBodyAlt' if i % 2 == 1 else 'TableBody')
                    if col in [1, 2]:
                        cell.alignment = self.styles.left_alignment
                
                # ===== ستون‌های Active Components =====
                for j, key in enumerate(active_keys):
                    col = 8 + j
                    value = values[7 + j]
                    cell = ws.cell(row=row, column=col, value=value)
                    if value > 0:
                        self.styles.apply_style(cell, 'ActivePositive')
                    else:
                        self.styles.apply_style(cell, 'ActiveZero')
                
                ws.row_dimensions[row].height = 22
                row += 1

            # ===== سطر مجموع این بخش (Subtotal) =====
            grand_total_qty += section_total_qty
            grand_total_di += section_total_di
            grand_total_do += section_total_do
            grand_total_ai += section_total_ai
            grand_total_ao += section_total_ao
            
            for key in active_keys:
                grand_total_active[key] += section_total_active.get(key, 0)

            # ✅ استفاده از section_display در subtotal
            subtotal_values = [section_display, "SUBTOTAL", section_total_qty, section_total_di, 
                            section_total_do, section_total_ai, section_total_ao]
            
            for key in active_keys:
                subtotal_values.append(section_total_active.get(key, 0))

            # ===== سطر مجموع - ستون‌های پایه =====
            for col in range(1, 8):
                cell = ws.cell(row=row, column=col, value=subtotal_values[col - 1])
                cell.font = Font(bold=True, color="1F4E79", size=9, name="Calibri")
                cell.fill = PatternFill(start_color="D6EAF8", end_color="D6EAF8", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = Border(
                    left=Side(style='thin'), right=Side(style='thin'),
                    top=Side(style='thin'), bottom=Side(style='thin')
                )

            # ===== سطر مجموع - ستون‌های Active =====
            for j, key in enumerate(active_keys):
                col = 8 + j
                cell = ws.cell(row=row, column=col, value=subtotal_values[7 + j])
                cell.font = Font(bold=True, color="1F4E79", size=9, name="Calibri")
                cell.fill = PatternFill(start_color="D6EAF8", end_color="D6EAF8", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = Border(
                    left=Side(style='thin'), right=Side(style='thin'),
                    top=Side(style='thin'), bottom=Side(style='thin')
                )

            ws.row_dimensions[row].height = 25
            row += 1
            
            # ===== فاصله بین بخش‌ها =====
            row += 1

        # ===== سطر TOTAL کل پروژه =====
        total_values = ["", "TOTAL", grand_total_qty, grand_total_di, grand_total_do, grand_total_ai, grand_total_ao]
        
        for key in active_keys:
            total_values.append(grand_total_active.get(key, 0))

        # ===== سطر TOTAL - ستون‌های پایه =====
        for col in range(1, 8):
            cell = ws.cell(row=row, column=col, value=total_values[col - 1])
            self.styles.apply_style(cell, 'Total')

        # ===== سطر TOTAL - ستون‌های Active =====
        for j, key in enumerate(active_keys):
            col = 8 + j
            cell = ws.cell(row=row, column=col, value=total_values[7 + j])
            self.styles.apply_style(cell, 'ActiveTotal')

        ws.row_dimensions[row].height = 25

        # ===== AutoFilter =====
        self._add_auto_filter(ws, 3, total_cols)

    # ================================================================
    # 7. لیست کابل‌ها
    # ================================================================

    def _create_cable_list(self, project: Project):
        """ایجاد Detail IO List - با اتصال FS به PU و اعتبارسنجی"""
        from openpyxl.styles import Border, Side, Font, PatternFill, Alignment
        
        # ============================================================
        # ✅ اعتبارسنجی پروژه (قبل از ساخت شیت)
        # ============================================================
        try:
            from core.validation_errors import validate_project_components
            validation = validate_project_components(project)
            print(f"🔍 Validation: {validation.count()} issue(s)")
            for err in validation.errors:
                print(f"   - [{err.severity.value}] {err.code}: {err.title}")
        except ImportError as e:
            print(f"⚠️ validation_errors module not found: {e}")
            validation = None
        except Exception as e:
            print(f"❌ Validation error: {e}")
            import traceback
            traceback.print_exc()
            validation = None
        
        ws = self.wb.create_sheet("Detail IO List")
        self._set_page_setup(ws)

        # ===== تنظیم عرض ستون‌ها =====
        ws.column_dimensions['A'].width = 6
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 25
        ws.column_dimensions['F'].width = 25
        ws.column_dimensions['G'].width = 20
        ws.column_dimensions['H'].width = 15
        ws.column_dimensions['I'].width = 15
        ws.column_dimensions['J'].width = 15
        ws.column_dimensions['K'].width = 15
        ws.column_dimensions['L'].width = 5
        ws.column_dimensions['M'].width = 5
        ws.column_dimensions['N'].width = 5
        ws.column_dimensions['O'].width = 5

        # ===== عنوان =====
        ws.merge_cells('A1:O1')
        ws['A1'].value = "5. Detail IO List (For each Part of Project)"
        ws['A1'].font = self.section_font
        ws['A1'].fill = self.section_fill
        ws['A1'].alignment = self.center_alignment
        ws.row_dimensions[1].height = 40

        # ===== تعریف‌ها =====
        CABLE_LIST_EXCLUDED = ['SPR', 'MOD']
        ACTIVE_COMPONENTS_EXCLUDED = ['FA', 'FE', 'SLE', 'CMD', 'PU', 'VSD', 'SPR', 'MOD', 'FC', 'LIG']

        # ✅ کامپوننت‌هایی که در ستون Name حرف/شماره می‌گیرند
        EQUIPMENT_KEYS = ['PU', 'VSD']
        
        # ✅ کامپوننت‌هایی که به PU متصل می‌شوند
        PU_ATTACHED = ['FS', 'VSD']

        # ============================================================
        # ✅ گزارش خطاها در ابتدای شیت (اگر خطایی هست)
        # ============================================================
        current_row = 2
        if validation and validation.has_any():
            error_count = validation.count()
            
            # هدر گزارش خطا
            ws.merge_cells(start_row=current_row, start_column=1, 
                        end_row=current_row, end_column=15)
            cell = ws.cell(row=current_row, column=1,
                        value=f"⚠️ VALIDATION ERRORS FOUND: {error_count} issue(s)")
            cell.font = Font(bold=True, color="FFFFFF", size=11)
            cell.fill = PatternFill(start_color="C0392B", end_color="C0392B", 
                                fill_type="solid")
            cell.alignment = Alignment(horizontal="left", vertical="center")
            ws.row_dimensions[current_row].height = 25
            current_row += 1
            
            # خطاها
            for err in validation.errors:
                if err.severity.value not in ('error', 'critical', 'warning'):
                    continue
                
                # رنگ بر اساس severity
                color = "C0392B" if err.severity.value in ('error', 'critical') else "E67E22"
                bg_color = "FADBD8" if err.severity.value in ('error', 'critical') else "FDEBD0"
                
                ws.merge_cells(start_row=current_row, start_column=1,
                            end_row=current_row, end_column=15)
                cell = ws.cell(row=current_row, column=1,
                            value=f"  [{err.code}] {err.title} — {err.message.replace(chr(10), ' | ')}")
                cell.font = Font(bold=False, color=color, size=9)
                cell.fill = PatternFill(start_color=bg_color, end_color=bg_color,
                                    fill_type="solid")
                cell.alignment = Alignment(horizontal="left", vertical="center", 
                                        wrap_text=True)
                ws.row_dimensions[current_row].height = 22
                current_row += 1
            
            current_row += 1  # فاصله

        # ===== جمع‌آوری همه کامپوننت‌های فعال =====
        all_active_keys = set()
        for section in project.sections:
            for device in section.devices:
                for comp_field in COMPONENT_KEYS:
                    if comp_field in CABLE_LIST_EXCLUDED:
                        continue
                    if comp_field in ACTIVE_COMPONENTS_EXCLUDED:
                        continue
                    comp_qty = self._safe_int(getattr(device, comp_field, 0))
                    if comp_qty > 0:
                        all_active_keys.add(comp_field)

        active_keys = sorted(list(all_active_keys))

        # ===== تنظیم عرض ستون‌های Active =====
        for i, key in enumerate(active_keys):
            col_letter = get_column_letter(16 + i)
            ws.column_dimensions[col_letter].width = 6

        # ===== تعیین هدرها =====
        headers = ["No", "Section", "Remark", "Name", "Cable Tag", "Equipment", 
                "Location", "Cable Type", "Cable Size", "From", "To", 
                "DI", "DO", "AI", "AO"]
        for key in active_keys:
            headers.append(key)

        total_cols = len(headers)

        # ===== متغیرهای جمع کل =====
        grand_total_di = 0
        grand_total_do = 0
        grand_total_ai = 0
        grand_total_ao = 0

        grand_total_active = {}
        for key in active_keys:
            grand_total_active[key] = 0

        global_cable_counter = 0
        component_counters = defaultdict(int)
        row = current_row

        # ===== مرزها =====
        thick_side = Side(style='medium', color='1F4E79')
        thin_side = Side(style='thin', color='D0D0D0')

        # ================================================================
        # ✅ تابع کمکی: تولید نام پمپ‌ها
        # ================================================================
        def build_pump_names(device_name: str, count: int, use_index: bool) -> list:
            """
            تولید نام پمپ‌ها
            
            Rules:
                count == 0 → []
                count == 1 → [device_name]        (بدون اندیس)
                count >  1 → [device_name+a, ...] (با اندیس)
            
            Returns:
                لیست نام‌ها: ["P5"] یا ["P5a", "P5b", "P5c"]
            """
            if count == 0:
                return []
            
            # ✅ اگر فقط یک پمپ است، بدون اندیس
            if count == 1:
                return [device_name]
            
            names = []
            
            if use_index:
                # روش حروف
                for i in range(count):
                    suffix = chr(ord('a') + i)
                    names.append(f"{device_name}{suffix}")
            else:
                # روش عددی
                import re
                match = re.match(r'^(.*?)(\d+)$', device_name)
                
                if match:
                    prefix = match.group(1)
                    start_num = int(match.group(2))
                    for i in range(count):
                        names.append(f"{prefix}{start_num + i}")
                else:
                    # Fallback به روش حروف
                    for i in range(count):
                        suffix = chr(ord('a') + i)
                        names.append(f"{device_name}{suffix}")
            
            return names

        # ===== برای هر بخش =====
        for section in project.sections:
            if not section.devices:
                continue

            # ✅ اضافه شد: نام نمایشی سکشن — Name (Description)
            section_display = (
                getattr(section, 'display_name', None)
                or getattr(section, 'name', None)
                or 'Unknown Section'
            )
            component_counters.clear()
            cable_data = []
            for device in section.devices:
                device_name = device.Name or "Unnamed"
                info_value = device.INFO or ""
                location = device.Description or ""

                use_index_naming = getattr(device, 'UseIndexNaming', True)
                
                # ✅ تعداد PU
                pu_qty = self._safe_int(getattr(device, 'PU', 0))
                
                # ✅ ساخت نام پمپ‌ها (برای استفاده در FS و VSD)
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

                # ============================================================
                # ✅ تولید tag_suffixes (همیشه حروف برای Cable Tag)
                # ============================================================
                tag_suffixes = {}

                for comp in all_active_components:
                    field = comp['key']
                    comp_qty = comp['qty']

                    if comp_qty > 1:
                        suffixes = []
                        for i in range(comp_qty):
                            suffix = chr(ord('a') + i)
                            suffixes.append(suffix)
                        tag_suffixes[field] = suffixes
                    else:
                        tag_suffixes[field] = ['']

                # ============================================================
                # ساخت کابل‌ها
                # ============================================================
                for comp in all_active_components:
                    field = comp['key']
                    comp_qty = comp['qty']
                    cable_size = self._get_cable_size(field)

                    io = IO_CALCULATION.get(field, {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0})
                    unit_di = io.get('DI', 0)
                    unit_do = io.get('DO', 0)
                    unit_ai = io.get('AI', 0)
                    unit_ao = io.get('AO', 0)

                    if field in ['PU', 'VSD']:
                        from_location = "Power Panel"
                    else:
                        from_location = "Field"

                    # ============================================================
                    # PU: دو کابل (Status و CMD)
                    # ============================================================
                    if field == 'PU':
                        for i in range(comp_qty):
                            display_name = pump_names[i] if i < len(pump_names) else device_name

                            # Status
                            global_cable_counter += 1
                            status_tag = f"{display_name}-Status"

                            cable_data.append({
                                'section': section_display,   # ✅ اصلاح‌شده
                                'remark': info_value,
                                'name': display_name,
                                'cable_tag': status_tag,
                                'equipment': "Motor Status (DI)",
                                'location': location,
                                'cable_type': "NYSLCY",
                                'cable_size': "6x1mm²",
                                'from': from_location,
                                'to': "Control Panel",
                                'di': unit_di,
                                'do': 0,
                                'ai': 0,
                                'ao': 0,
                                'active_components': [
                                    {'key': c['key'], 'qty': 1 if c['key'] in ['FA', 'FE', 'SLE'] else 0}
                                    for c in all_active_components
                                ]
                            })

                            # CMD
                            global_cable_counter += 1
                            cmd_tag = f"{display_name}-CMD"

                            cable_data.append({
                                'section': section_display,   # ✅ اصلاح‌شده
                                'remark': info_value,
                                'name': display_name,
                                'cable_tag': cmd_tag,
                                'equipment': "Motor Command (DO)",
                                'location': location,
                                'cable_type': "NYSLCY",
                                'cable_size': "2x1mm²",
                                'from': from_location,
                                'to': "Control Panel",
                                'di': 0,
                                'do': unit_do,
                                'ai': 0,
                                'ao': 0,
                                'active_components': [
                                    {'key': c['key'], 'qty': 1 if c['key'] == 'CMD' else 0}
                                    for c in all_active_components
                                ]
                            })

                    # ============================================================
                    # VSD: متصل به PU
                    # ============================================================
                    elif field == 'VSD':
                        for i in range(comp_qty):
                            if i < len(pump_names):
                                display_name = pump_names[i]
                            else:
                                display_name = device_name

                            global_cable_counter += 1
                            vsd_tag = f"{display_name}-{field}"

                            cable_data.append({
                                'section': section_display,   # ✅ اصلاح‌شده
                                'remark': info_value,
                                'name': display_name,
                                'cable_tag': vsd_tag,
                                'equipment': comp['label'],
                                'location': location,
                                'cable_type': "NYSLCY",
                                'cable_size': cable_size,
                                'from': from_location,
                                'to': "Control Panel",
                                'di': unit_di,
                                'do': unit_do,
                                'ai': unit_ai,
                                'ao': unit_ao,
                                'active_components': [
                                    {'key': c['key'], 'qty': 1 if c['key'] == field else 0}
                                    for c in all_active_components
                                ]
                            })

                    # ============================================================
                    # ✅ FS: متصل به PU (اصلاح‌شده)
                    # ============================================================
                    elif field == 'FS':
                        for i in range(comp_qty):
                            # اتصال به پمپ متناظر
                            if i < len(pump_names):
                                pump_name = pump_names[i]
                                display_name = f"{pump_name}-FS"
                            else:
                                # اگر تعداد FS بیشتر از PU باشد (خطا)
                                display_name = f"{device_name}-FS"

                            global_cable_counter += 1
                            comp_tag = f"{display_name}"

                            cable_data.append({
                                'section': section_display,   # ✅ اصلاح‌شده
                                'remark': info_value,
                                'name': display_name,
                                'cable_tag': comp_tag,
                                'equipment': comp['label'],
                                'location': location,
                                'cable_type': "NYSLCY",
                                'cable_size': cable_size,
                                'from': from_location,
                                'to': "Control Panel",
                                'di': unit_di,
                                'do': unit_do,
                                'ai': unit_ai,
                                'ao': unit_ao,
                                'active_components': [
                                    {'key': c['key'], 'qty': 1 if c['key'] == field else 0}
                                    for c in all_active_components
                                ]
                            })
                    # ============================================================
                    # سایر کامپوننت‌ها
                    # ============================================================
                    else:
                        for i in range(comp_qty):
                            tag_suffix = tag_suffixes[field][i]
                            display_name = device_name

                            # ✅ شمارنده سراسری (برای ترتیب)
                            global_cable_counter += 1
                            
                            # ✅ شمارنده مستقل برای این field
                            component_counters[field] += 1
                            
                            # ✅ Cable Tag با شمارنده مستقل
                            comp_tag = f"{field}-{component_counters[field]}"

                            cable_data.append({
                                'section': section_display,   # ✅ اصلاح‌شده
                                'remark': info_value,
                                'name': display_name,
                                'cable_tag': comp_tag,
                                'equipment': comp['label'],
                                'location': location,
                                'cable_type': "NYSLCY",
                                'cable_size': cable_size,
                                'from': from_location,
                                'to': "Control Panel",
                                'di': unit_di,
                                'do': unit_do,
                                'ai': unit_ai,
                                'ao': unit_ao,
                                'active_components': [
                                    {'key': c['key'], 'qty': 1 if c['key'] == field else 0}
                                    for c in all_active_components
                                ]
                            })

            if not cable_data:
                continue

            # ===== عنوان بخش =====
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=total_cols)
            cell = ws.cell(row=row, column=1, value=f"📁 {section_display}")   # ✅ اصلاح‌شده
            cell.font = Font(bold=True, color="FFFFFF", size=10, name="Calibri")
            cell.fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
            cell.alignment = Alignment(horizontal="left", vertical="center")
            ws.row_dimensions[row].height = 25
            row += 1

            # ===== هدر جدول =====
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=row, column=col, value=header)
                if col <= 15:
                    self.styles.apply_style(cell, 'TableHeader')
                else:
                    self.styles.apply_style(cell, 'ActiveHeader')
            ws.row_dimensions[row].height = 25
            row += 1

            # ===== مجموع بخش =====
            section_total_di = 0
            section_total_do = 0
            section_total_ai = 0
            section_total_ao = 0

            section_total_active = {}
            for key in active_keys:
                section_total_active[key] = 0

            # ===== نوشتن داده‌ها =====
            for idx, cable in enumerate(cable_data):
                section_total_di += cable['di']
                section_total_do += cable['do']
                section_total_ai += cable['ai']
                section_total_ao += cable['ao']

                for comp in cable['active_components']:
                    if comp['key'] in section_total_active:
                        section_total_active[comp['key']] += comp['qty']

                values = [
                    idx + 1,
                    cable['section'],
                    cable['remark'],
                    cable['name'],
                    cable['cable_tag'],
                    cable['equipment'],
                    cable['location'],
                    cable['cable_type'],
                    cable['cable_size'],
                    cable['from'],
                    cable['to'],
                    cable['di'],
                    cable['do'],
                    cable['ai'],
                    cable['ao']
                ]

                for key in active_keys:
                    qty = 0
                    for comp in cable['active_components']:
                        if comp['key'] == key:
                            qty = comp['qty']
                            break
                    values.append(qty)

                for col in range(1, 16):
                    cell = ws.cell(row=row, column=col, value=values[col - 1])
                    self.styles.apply_style(cell, 'TableBodyAlt' if idx % 2 == 1 else 'TableBody')
                    if col in [2, 3, 5, 6]:
                        cell.alignment = self.styles.left_alignment

                for j, key in enumerate(active_keys):
                    col = 16 + j
                    value = values[15 + j]
                    cell = ws.cell(row=row, column=col, value=value)
                    if value > 0:
                        self.styles.apply_style(cell, 'ActivePositive')
                    else:
                        self.styles.apply_style(cell, 'ActiveZero')

                for col in range(1, total_cols + 1):
                    cell = ws.cell(row=row, column=col)
                    cell.border = Border(
                        left=thin_side, right=thin_side,
                        top=thin_side, bottom=thin_side
                    )

                ws.row_dimensions[row].height = 22
                row += 1

            # ===== Subtotal =====
            grand_total_di += section_total_di
            grand_total_do += section_total_do
            grand_total_ai += section_total_ai
            grand_total_ao += section_total_ao

            for key in active_keys:
                grand_total_active[key] += section_total_active.get(key, 0)

            subtotal_values = ["", section_display, "SUBTOTAL", "", "", "", "", "", "", "", "",
                            section_total_di, section_total_do, section_total_ai, section_total_ao]   # ✅ اصلاح‌شده

            for key in active_keys:
                subtotal_values.append(section_total_active.get(key, 0))

            for col in range(1, 16):
                cell = ws.cell(row=row, column=col, value=subtotal_values[col - 1])
                cell.font = Font(bold=True, color="1F4E79", size=9, name="Calibri")
                cell.fill = PatternFill(start_color="D6EAF8", end_color="D6EAF8", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = Border(left=thin_side, right=thin_side, top=thick_side, bottom=thick_side)

            for j, key in enumerate(active_keys):
                col = 16 + j
                cell = ws.cell(row=row, column=col, value=subtotal_values[15 + j])
                cell.font = Font(bold=True, color="1F4E79", size=9, name="Calibri")
                cell.fill = PatternFill(start_color="D6EAF8", end_color="D6EAF8", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = Border(left=thin_side, right=thin_side, top=thick_side, bottom=thick_side)

            ws.row_dimensions[row].height = 25
            row += 2

        # ===== TOTAL =====
        total_values = ["", "TOTAL", "", "", "", "", "", "", "", "", "",
                    grand_total_di, grand_total_do, grand_total_ai, grand_total_ao]

        for key in active_keys:
            total_values.append(grand_total_active.get(key, 0))

        for col in range(1, 16):
            cell = ws.cell(row=row, column=col, value=total_values[col - 1])
            self.styles.apply_style(cell, 'Total')
            cell.border = Border(left=thick_side, right=thick_side, top=thick_side, bottom=thick_side)

        for j, key in enumerate(active_keys):
            col = 16 + j
            cell = ws.cell(row=row, column=col, value=total_values[15 + j])
            self.styles.apply_style(cell, 'ActiveTotal')
            cell.border = Border(left=thick_side, right=thick_side, top=thick_side, bottom=thick_side)

        ws.row_dimensions[row].height = 25

        # ✅ AutoFilter (اگر خطایی در ابتدای شیت هست، از ردیف درست شروع شود)
        if current_row > 3:
            self._add_auto_filter(ws, current_row, total_cols)
        else:
            self._add_auto_filter(ws, 3, total_cols)
        
    # ================================================================
    # 8. نیازمندی‌های کنترلر
    # ================================================================

    def _create_controller_requirements(self, project: Project):
        """ایجاد نیازمندی‌های کنترلر - با CBX/FBX و MCX (الگوریتم تکرارشونده)"""
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        import math
        
        ws = self.wb.create_sheet("Controller Requirements")
        self._set_page_setup(ws)
        
        # تنظیم عرض ستون‌ها
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 8
        ws.column_dimensions['C'].width = 8
        ws.column_dimensions['D'].width = 8
        ws.column_dimensions['E'].width = 8
        ws.column_dimensions['F'].width = 10
        ws.column_dimensions['G'].width = 12
        ws.column_dimensions['H'].width = 12
        ws.column_dimensions['I'].width = 14
        ws.column_dimensions['J'].width = 14
        
        # عنوان
        ws.merge_cells('A1:J1')
        ws['A1'].value = "6. CONTROLLER REQUIREMENTS (By Section)"
        ws['A1'].font = self.section_font
        ws['A1'].fill = self.section_fill
        ws['A1'].alignment = self.center_alignment
        ws.row_dimensions[1].height = 30
        
        # توضیحات
        ws.merge_cells('A2:J2')
        ws['A2'].value = ("CBX-8R8: 16 I/O (flexible, max 3 FBX) | "
                        "MCX-08m2: 8DI/8DO/8AI/4AO | MCX-06D: 8DI/6DO/4AI/2AO")
        ws['A2'].font = Font(name="Calibri", size=8, italic=True, color="7F8C8D")
        ws['A2'].alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[2].height = 18
        
        # توابع محاسبه
        def calc_cbx_fbx(di, do, ai, ao):
            """محاسبه CBX/FBX"""
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
            """
            محاسبه MCX با الگوریتم تکرارشونده دقیق
            
            1. 06D تنها؟
            2. 08m2 تنها؟
            3. جفت (08m2 + 06D)
            4. تکرار برای باقیمانده
            """
            n_08m2 = 0
            n_06d = 0
            
            rem_di = di
            rem_do = do
            rem_ai = ai
            rem_ao = ao
            
            # حداکثر تکرار برای جلوگیری از حلقه بی‌نهایت
            max_iter = 1000
            iter_count = 0
            
            while (rem_di > 0 or rem_do > 0 or rem_ai > 0 or rem_ao > 0) and iter_count < max_iter:
                iter_count += 1
                
                # 1. بررسی 06D تنها
                if (rem_di <= 8 and rem_do <= 6 and 
                    rem_ai <= 4 and rem_ao <= 2):
                    n_06d += 1
                    rem_di = rem_do = rem_ai = rem_ao = 0
                    break
                
                # 2. بررسی 08m2 تنها
                if (rem_di <= 8 and rem_do <= 8 and 
                    rem_ai <= 8 and rem_ao <= 4):
                    n_08m2 += 1
                    rem_di = rem_do = rem_ai = rem_ao = 0
                    break
                
                # 3. جفت (08m2 + 06D)
                n_08m2 += 1
                n_06d += 1
                
                rem_di = max(0, rem_di - 16)
                rem_do = max(0, rem_do - 14)
                rem_ai = max(0, rem_ai - 12)
                rem_ao = max(0, rem_ao - 6)
            
            return n_08m2, n_06d
        
        # هدرها
        headers = ["Section", "DI", "DO", "AI", "AO", "I/O", 
                "CBX-8R8", "FBX-8R8", "MCX-08m2", "MCX-06D"]
        
        mcx_header_fill = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
        mcx_header_font = Font(name="Calibri", size=10, bold=True, color="856404")
        mcx_body_fill = PatternFill(start_color="FFFBF0", end_color="FFFBF0", fill_type="solid")
        
        # جمع کل
        total_di = total_do = total_ai = total_ao = total_io = 0
        total_cbx = total_fbx = 0
        total_mcx_08m2 = total_mcx_06d = 0
        
        # داده‌ها
        data = []
        
        for section in project.sections:
            section_di = sum(d.DI for d in section.devices)
            section_do = sum(d.DO for d in section.devices)
            section_ai = sum(d.AI for d in section.devices)
            section_ao = sum(d.AO for d in section.devices)
            section_io = section_di + section_do + section_ai + section_ao
            
            cbx, fbx = calc_cbx_fbx(section_di, section_do, section_ai, section_ao)
            mcx_08m2, mcx_06d = calc_mcx(section_di, section_do, section_ai, section_ao)
            
            total_di += section_di
            total_do += section_do
            total_ai += section_ai
            total_ao += section_ao
            total_io += section_io
            total_cbx += cbx
            total_fbx += fbx
            total_mcx_08m2 += mcx_08m2
            total_mcx_06d += mcx_06d

            section_label = getattr(section, 'display_name', None) or section.name
            data.append([
                section_label, section_di, section_do, section_ai, section_ao,
                section_io, cbx, fbx, mcx_08m2, mcx_06d,
            ])
        
        # نوشتن هدر
        row = 4
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            if header in ('MCX-08m2', 'MCX-06D'):
                cell.font = mcx_header_font
                cell.fill = mcx_header_fill
            else:
                cell.font = self.header_font
                cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
        ws.row_dimensions[row].height = 25
        row += 1
        
        # نوشتن داده‌ها
        for i, item in enumerate(data):
            is_alt = (i % 2 == 1)
            for col, value in enumerate(item, 1):
                cell = ws.cell(row=row, column=col, value=value)
                if col >= 9:
                    cell.font = self.body_font
                    cell.fill = mcx_body_fill
                else:
                    cell.font = self.body_font
                    cell.fill = self.alt_fill if is_alt else self.body_fill
                cell.alignment = self.center_alignment
                cell.border = self.thin_border
                if col == 1:
                    cell.alignment = self.left_alignment
            ws.row_dimensions[row].height = 22
            row += 1
        
        # سطر TOTAL
        total_row = ["TOTAL", total_di, total_do, total_ai, total_ao, total_io,
                    total_cbx, total_fbx, total_mcx_08m2, total_mcx_06d]
        
        for col, value in enumerate(total_row, 1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.font = self.total_font
            cell.fill = self.total_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
        ws.row_dimensions[row].height = 25

    # ================================================================
    # 9. ضمیمه‌ها
    # ================================================================

    def _create_appendix(self, devices: List[Motor]):
        """ایجاد ضمیمه‌ها"""
        ws = self.wb.create_sheet("Appendix")
        self._set_page_setup(ws)

        # ===== 7.1 Component Legend =====
        ws.merge_cells('A1:C1')
        ws['A1'].value = "7.1. Component Legend"
        ws['A1'].font = self.section_font
        ws['A1'].fill = self.section_fill
        ws['A1'].alignment = self.center_alignment
        ws.row_dimensions[1].height = 30

        # ================================================================
        # ✅ جمع‌آوری کامپوننت‌های استفاده شده
        # ================================================================
        used_components = set()
        
        for device in devices:
            # ===== کامپوننت‌های عادی (به جز EXCLUDED) =====
            for field in COMPONENT_KEYS:
                if field in EXCLUDED_FROM_COMPONENTS:
                    continue
                qty = self._safe_int(getattr(device, field, 0))
                if qty > 0:
                    used_components.add(field)
            
            # ===== ✅ اضافه کردن PU و VSD در صورت استفاده در پروژه =====
            if self._safe_int(getattr(device, 'PU', 0)) > 0:
                used_components.add('PU')
            if self._safe_int(getattr(device, 'VSD', 0)) > 0:
                used_components.add('VSD')

        if used_components:
            categories = {
                "Sensors": ["DTS", "ITS", "RTS", "DTHS", "RTHS", "AVS", "FS", "PS", "PT", "DPT", "DPS", "AQ", "FR", "LS", "LT", "SD", "Knob", "SOU", "LUX", "VIB"],
                "Actuators": ["VA", 'DAM_T1', 'DAM_T2', 'DAM_T3', 'DAM_T4', "SV", "MOV"],
                "Equipment": ["PU", "VSD", "FC", "LIG", "BUZ"]
            }

            headers = ["Abbreviation", "Full Name", "Category"]
            ws.column_dimensions['A'].width = 20
            ws.column_dimensions['B'].width = 30
            ws.column_dimensions['C'].width = 15

            row = 3
            for col, header in enumerate(headers, 1):
                ws.cell(row=row, column=col, value=header)
            self._apply_header_style(ws, row, 3)
            ws.row_dimensions[row].height = 25

            row += 1
            for field in sorted(used_components):
                full_name = self._get_component_name(field)
                category = "Other"
                for cat_name, cat_fields in categories.items():
                    if field in cat_fields:
                        category = cat_name
                        break

                values = [field, full_name, category]
                for col, value in enumerate(values, 1):
                    ws.cell(row=row, column=col, value=value)
                self._apply_body_style(ws, row, 3)
                ws.row_dimensions[row].height = 22
                row += 1

        # ===== 7.2 IO Reference Guide =====
        row += 2
        ws.merge_cells(f'A{row}:E{row}')
        ws[f'A{row}'].value = "7.2. IO Reference Guide"
        ws[f'A{row}'].font = self.section_font
        ws[f'A{row}'].fill = self.section_fill
        ws[f'A{row}'].alignment = self.center_alignment
        ws.row_dimensions[row].height = 30

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
                    'ao': ao_text
                })

        if used_io:
            headers = ["Component", "DI", "DO", "AI", "AO"]
            ws.column_dimensions['A'].width = 30
            ws.column_dimensions['B'].width = 25
            ws.column_dimensions['C'].width = 25
            ws.column_dimensions['D'].width = 25
            ws.column_dimensions['E'].width = 25

            row += 1
            for col, header in enumerate(headers, 1):
                ws.cell(row=row, column=col, value=header)
            self._apply_header_style(ws, row, 5)
            ws.row_dimensions[row].height = 25

            row += 1
            for i, item in enumerate(used_io):
                values = [item['component'], item['di'], item['do'], item['ai'], item['ao']]
                for col, value in enumerate(values, 1):
                    ws.cell(row=row, column=col, value=value)
                self._apply_body_style(ws, row, 5, is_alt=(i % 2 == 1))
                ws.cell(row=row, column=1).alignment = self.left_alignment
                ws.row_dimensions[row].height = 22
                row += 1

    # ================================================================
    # متد اصلی: صدور گزارش کامل Excel
    # ================================================================

    def export_full_report(self, file_path: str = None) -> Optional[str]:
        """صدور گزارش کامل Excel با تمام بخش‌ها (فقط Current Revision)"""

        project = self.app.get_current_project()
        if not project:
            from tkinter import messagebox
            messagebox.showwarning("Warning", "No project selected!")
            return None

        # ============================================================
        # ✅ دریافت Current Revision
        # ============================================================
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
            
            # ✅ نام فایل شامل Revision
            safe_rev = "".join(
                c if c.isalnum() or c in " _-" else "_"
                for c in revision_name
            ).strip() or "Rev"
            
            safe_proj = "".join(
                c if c.isalnum() or c in " _-" else "_"
                for c in project.name
            ).strip() or "Project"
            
            timestamp = get_timestamp_for_filename()
            
            # ============================================================
            # ✅ پوشه پیش‌فرض: Attachments/{ProjectName}/Reports/
            # ============================================================
            try:
                # دریافت مسیر پوشه پیوست پروژه از AttachmentManager
                project_dir = self.app.attachment_manager.ensure_project_dir(project.name)
                reports_dir = os.path.join(project_dir, "Reports")
                os.makedirs(reports_dir, exist_ok=True)
                default_dir = reports_dir
            except Exception as e:
                # اگه AttachmentManager مشکل داشت، به Desktop برمی‌گردیم
                default_dir = os.path.expanduser("~")
                print(f"⚠️ Could not get attachments folder: {e}")
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Save Excel Report",
                initialdir=default_dir,                                    # ✅ پوشه پیش‌فرض
                initialfile=f"IO_List({safe_proj})_{safe_rev}_{timestamp}.xlsx"
            )
            if not file_path:
                return None

        try:
            # ===== ایجاد شیت‌ها =====
            self._create_cover_sheet(project, revision_name)
            self._create_executive_summary(project, devices)
            self._create_io_summary(devices)
            self._create_sections(project)
            self._create_lom_all(devices)
            self._create_lom_by_section(project)
            self._create_cable_list(project)
            self._create_controller_requirements(project)
            self._create_appendix(devices)

            # ===== ذخیره فایل =====
            self.wb.save(file_path)

            if os.name == 'nt':
                os.startfile(file_path)

            from tkinter import messagebox
            messagebox.showinfo(
                "Success",
                f"Excel Report saved to:\n{file_path}\n\n"
                f"📁 Project: {project.name}\n"
                f"📌 Revision: {revision_name}"
            )

            return file_path

        except Exception as e:
            from tkinter import messagebox
            import traceback
            messagebox.showerror(
                "Excel Export Error",
                f"Failed to generate Excel:\n{str(e)}\n\n{traceback.format_exc()}"
            )
            return None