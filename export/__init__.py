"""خروجی‌های Excel"""

import os
from datetime import datetime
from typing import List, Dict, Any

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from core import Motor, Project, COMPONENT_LABELS
from core.constants import COLORS


class ExcelExporter:
    """صادرکننده گزارش Excel"""
    
    def __init__(self, app):
        self.app = app
    
    def export_full_report(self, devices: List[Motor], file_path: str = None):
        """صدور گزارش کامل Excel"""
        if not file_path:
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Save Excel Report"
            )
            if not file_path:
                return
        
        wb = Workbook()
        
        # شیت اصلی
        ws = wb.active
        ws.title = "Devices Report"
        
        # استایل‌ها
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        center_align = Alignment(horizontal="center", vertical="center")
        
        # هدر
        ws.merge_cells('A1:I1')
        ws['A1'] = "CONTROL SYSTEM DEVICES REPORT"
        ws['A1'].font = Font(bold=True, size=16)
        ws['A1'].alignment = center_align
        
        # اطلاعات پروژه
        project = self.app.get_current_project()
        if project:
            ws['A3'] = f"Project: {project.name}"
            ws['A4'] = f"Generated: {datetime.now().strftime('%Y/%m/%d %H:%M')}"
            ws['A5'] = f"Total Devices: {len(devices)}"
        
        # ستون‌ها
        headers = ["No.", "Name", "Description", "INFO", "DI", "DO", "AI", "AO", "Total"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=7, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
            cell.border = border
        
        # داده‌ها
        for i, motor in enumerate(devices, 1):
            row = i + 7
            ws.cell(row=row, column=1, value=i)
            ws.cell(row=row, column=2, value=motor.Name or "")
            ws.cell(row=row, column=3, value=motor.Description or "")
            ws.cell(row=row, column=4, value=motor.DI)
            ws.cell(row=row, column=5, value=motor.DO)
            ws.cell(row=row, column=6, value=motor.AI)
            ws.cell(row=row, column=7, value=motor.AO)
            ws.cell(row=row, column=8, value=motor.get_total_io())
            ws.cell(row=row, column=9, value=motor.INFO or "")
            
            for col in range(1, 10):
                cell = ws.cell(row=row, column=col)
                cell.border = border
                if col in [1, 4, 5, 6, 7, 8]:
                    cell.alignment = center_align
        
        # تنظیم عرض ستون‌ها
        column_widths = [5, 20, 35, 30, 12, 4, 4, 4, 4]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        wb.save(file_path)
        
        # باز کردن فایل
        if os.name == 'nt':
            os.startfile(file_path)
        
        return file_path