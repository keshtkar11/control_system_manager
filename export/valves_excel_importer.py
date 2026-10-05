# export/valves_excel_importer.py
"""
Valves Excel Importer/Exporter

قابلیت‌ها:
- create_template(): ساخت فایل Template برای Import
- export_valves(): Export کامل شیرها (ورودی + محاسبه‌شده)
- read_and_validate(): خواندن فایل و validate کردن
- apply_import(): افزودن شیرها به Section

فرمت فایل Import (فقط ۸ ستون ورودی):
    Equipment | ValveType | Flow | Unit | PressureDrop | SteamPressure | Circuit | Quantity
"""

import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from openpyxl import Workbook, load_workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side,
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.comments import Comment

from core.models import Valve
from core.valve_constants import (
    VALVE_TYPE_FIELDS,
    FLOW_UNITS,
)
from core.valve_calculator import enrich_valve


logger = logging.getLogger(__name__)


# ================================================================
# CONSTANTS
# ================================================================

# فیلدهای ورودی کاربر (فقط این ۸ تا)
INPUT_FIELDS = [
    'Equipment',
    'ValveType',
    'Flow',
    'Unit',
    'PressureDrop',
    'SteamPressure',
    'Circuit',
    'Quantity',
]
HIDDEN_FIELDS = ['_Sample']
# هدرهای فارسی/انگلیسی
FIELD_LABELS = {
    'Equipment':     ('Equipment',     'نام شیر'),
    'ValveType':     ('ValveType',     'نوع شیر'),
    'Flow':          ('Flow',          'دبی'),
    'Unit':          ('Unit',          'واحد'),
    'PressureDrop':  ('PressureDrop',  'افت فشار (psi)'),
    'SteamPressure': ('SteamPressure', 'فشار بخار (bar)'),
    'Circuit':       ('Circuit',       'مدار'),
    'Quantity':      ('Quantity',      'تعداد'),
}

# توضیحات هر فیلد
FIELD_HINTS = {
    'Equipment':     'نام منحصربفرد شیر (مثلاً PICV-AHU1)',
    'ValveType':     'یکی از: PICV, 3 Way, Steam, PICV+3Way',
    'Flow':          'عدد مثبت (مثلاً 1000)',
    'Unit':          'L/HR, L/min, m³/h, Kg/h, lb/h, ton/h, gpm, ...',
    'PressureDrop':  'عدد مثبت بر حسب psi (مثلاً 30)',
    'SteamPressure': 'فقط برای Steam — فشار مطلق (bar)',
    'Circuit':       'نام مدار (مثلاً Circuit A)',
    'Quantity':      'عدد صحیح ≥ 1',
}

# انواع مجاز شیر
ALLOWED_VALVE_TYPES = [
    'PICV',
    '3 Way',
    'Steam',
    'PICV+3Way',
]

# واحدهای مجاز
ALLOWED_UNITS = [
    'L/HR',
    'L/min',
    'L/s',
    'm³/h',
    'gpm',
    'Kg/h',
    'lb/h',
    'ton/h',
]


# ================================================================
# CLASS
# ================================================================

class ValvesExcelImporter:
    """Import/Export شیرها از/به Excel"""
    
    def __init__(self, app):
        self.app = app
        
        # رنگ‌ها
        self.header_fill = PatternFill(
            start_color="1F4E79", end_color="1F4E79", fill_type="solid"
        )
        self.sample_fill = PatternFill(
            start_color="E8F4FD", end_color="E8F4FD", fill_type="solid"
        )
        self.hint_fill = PatternFill(
            start_color="FFF3CD", end_color="FFF3CD", fill_type="solid"
        )
        self.required_fill = PatternFill(
            start_color="FFEBEE", end_color="FFEBEE", fill_type="solid"
        )
        
        self.header_font = Font(
            name="Calibri", size=11, bold=True, color="FFFFFF"
        )
        self.sample_font = Font(
            name="Calibri", size=10, italic=True, color="7F8C8D"
        )
        self.hint_font = Font(
            name="Calibri", size=9, italic=True, color="856404"
        )
        self.body_font = Font(
            name="Calibri", size=10, color="000000"
        )
        
        self.center_align = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        self.left_align = Alignment(
            horizontal="left", vertical="center", wrap_text=True
        )
        
        self.thin_border = Border(
            left=Side(style='thin', color='D0D0D0'),
            right=Side(style='thin', color='D0D0D0'),
            top=Side(style='thin', color='D0D0D0'),
            bottom=Side(style='thin', color='D0D0D0'),
        )
    
    # ============================================================
    # ✅ 1. CREATE TEMPLATE
    # ============================================================
    
    def create_template(self, file_path: str) -> bool:
        """
        ساخت فایل Template برای Import
        
        شامل:
        - ۸ ستون ورودی
        - ۳ ردیف نمونه
        - Data Validation (Dropdown)
        - Comment روی هر هدر
        - Sheet راهنما (اختیاری)
        
        Args:
            file_path: مسیر ذخیره
        
        Returns:
            True اگر موفق
        """
        try:
            wb = Workbook()
            
            # ===== Sheet 1: Valves (اصلی) =====
            ws = wb.active
            ws.title = "Valves"
            
            self._build_template_sheet(ws)
            
            # ===== Sheet 2: Guide (راهنما) =====
            ws_guide = wb.create_sheet("Guide")
            self._build_guide_sheet(ws_guide)
            
            # ===== Sheet 3: Examples (نمونه‌ها) =====
            ws_examples = wb.create_sheet("Examples")
            self._build_examples_sheet(ws_examples)
            
            # ===== ذخیره =====
            wb.save(file_path)
            logger.info(f"Template created: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create template: {e}", exc_info=True)
            return False
    
    def _build_template_sheet(self, ws):
        """ساخت Sheet اصلی Template"""
        
        # ============================================================
        # ردیف ۱: عنوان
        # ============================================================
        ws.merge_cells('A1:H1')
        title_cell = ws['A1']
        title_cell.value = "📋  Valves Import Template — پر کردن ۸ فیلد، محاسبات خودکار"
        title_cell.font = Font(
            name="Calibri", size=14, bold=True, color="FFFFFF"
        )
        title_cell.fill = PatternFill(
            start_color="2C3E50", end_color="2C3E50", fill_type="solid"
        )
        title_cell.alignment = self.center_align
        ws.row_dimensions[1].height = 35
        
        # ============================================================
        # ردیف ۲: راهنما
        # ============================================================
        ws.merge_cells('A2:H2')
        hint_cell = ws['A2']
        hint_cell.value = (
            "⚠️  فقط این ۸ ستون را پر کنید. "
            "برای هر نوع شیر (PICV, 3 Way, Steam, PICV+3Way) مقادیر مخصوص لازم است. "
            "ستون‌های اجباری: Equipment, ValveType, Flow, Unit, PressureDrop, Quantity"
        )
        hint_cell.font = self.hint_font
        hint_cell.fill = self.hint_fill
        hint_cell.alignment = Alignment(
            horizontal="left", vertical="center", wrap_text=True
        )
        ws.row_dimensions[2].height = 30
        
        # ============================================================
        # ============================================================
        # ردیف ۳: هدرها
        # ============================================================
        header_row = 3
        for col_idx, field in enumerate(INPUT_FIELDS, 1):
            cell = ws.cell(row=header_row, column=col_idx)
            cell.value = FIELD_LABELS[field][0]
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_align
            cell.border = self.thin_border
            
            comment = Comment(FIELD_HINTS[field], "Template")
            comment.width = 250
            comment.height = 60
            cell.comment = comment
        
        # ✅ ستون مخفی _Sample
        sample_col = len(INPUT_FIELDS) + 1   # ستون I
        cell = ws.cell(row=header_row, column=sample_col)
        cell.value = "_Sample"
        cell.font = Font(name="Calibri", size=9, italic=True, color="B0B0B0")
        cell.fill = self.sample_fill
        cell.alignment = self.center_align
        
        # ✅ مخفی کردن ستون
        col_letter = get_column_letter(sample_col)
        ws.column_dimensions[col_letter].hidden = True
        ws.column_dimensions[col_letter].width = 10
        

        # ============================================================
        # ردیف ۴-۶: نمونه‌ها (با علامت _Sample)
        # ============================================================
        samples = [
            # Equipment, ValveType, Flow, Unit, PD, SP, Circuit, Qty, _Sample
            ['PICV-AHU1', 'PICV', 1000, 'L/HR', 30, '', 'Circuit A', 1, 'SAMPLE'],
            ['3W-AHU1', '3 Way', 500, 'L/HR', 10, '', 'Circuit B', 2, 'SAMPLE'],
            ['ST-Boiler', 'Steam', 50, 'Kg/h', 5, 4, 'Steam Line', 1, 'SAMPLE'],
        ]
        
        for row_offset, sample in enumerate(samples):
            row = header_row + 1 + row_offset
            for col_idx, value in enumerate(sample, 1):
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.font = self.sample_font
                cell.fill = self.sample_fill
                cell.alignment = self.center_align
                cell.border = self.thin_border
            ws.row_dimensions[row].height = 20
        
        # ============================================================
        # تنظیم عرض ستون‌ها
        # ============================================================
        column_widths = {
            'A': 18,   # Equipment
            'B': 14,   # ValveType
            'C': 10,   # Flow
            'D': 10,   # Unit
            'E': 14,   # PressureDrop
            'F': 14,   # SteamPressure
            'G': 18,   # Circuit
            'H': 10,   # Quantity
        }
        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width
        
        # ============================================================
        # Data Validation
        # ============================================================
        # ===== ValveType Dropdown =====
        dv_valve_type = DataValidation(
            type="list",
            formula1=f'"{",".join(ALLOWED_VALVE_TYPES)}"',
            allow_blank=False,
            showDropDown=False,  # Excel quirk: False = Show dropdown!
        )
        dv_valve_type.error = "لطفاً یکی از مقادیر مجاز را انتخاب کنید"
        dv_valve_type.errorTitle = "ValveType نامعتبر"
        dv_valve_type.prompt = "نوع شیر را انتخاب کنید"
        dv_valve_type.promptTitle = "ValveType"
        ws.add_data_validation(dv_valve_type)
        dv_valve_type.add(f'B{header_row + 1}:B1000')
        
        # ===== Unit Dropdown =====
        dv_unit = DataValidation(
            type="list",
            formula1=f'"{",".join(ALLOWED_UNITS)}"',
            allow_blank=False,
            showDropDown=False,
        )
        dv_unit.error = "لطفاً یکی از واحدهای مجاز را انتخاب کنید"
        dv_unit.errorTitle = "Unit نامعتبر"
        dv_unit.prompt = "واحد دبی را انتخاب کنید"
        dv_unit.promptTitle = "Unit"
        ws.add_data_validation(dv_unit)
        dv_unit.add(f'D{header_row + 1}:D1000')
        
        # ===== Freeze Panes =====
        ws.freeze_panes = f'A{header_row + 1}'
    
    def _build_guide_sheet(self, ws):
        """ساخت Sheet راهنما"""
        
        # ===== عنوان =====
        ws.merge_cells('A1:D1')
        cell = ws['A1']
        cell.value = "📖  راهنمای استفاده"
        cell.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
        cell.fill = PatternFill(
            start_color="1F4E79", end_color="1F4E79", fill_type="solid"
        )
        cell.alignment = self.center_align
        ws.row_dimensions[1].height = 35
        
        # ===== راهنما =====
        guide_lines = [
            ("گام ۱:", "Sheet 'Valves' را باز کنید"),
            ("گام ۲:", "۳ ردیف نمونه را پاک کنید"),
            ("گام ۳:", "داده‌های خود را در ستون‌های A تا H وارد کنید"),
            ("گام ۴:", "ستون‌های اجباری: Equipment, ValveType, Flow, Unit, PressureDrop, Quantity"),
            ("گام ۵:", "برای Steam باید SteamPressure هم پر شود"),
            ("گام ۶:", "فایل را Save کنید"),
            ("گام ۷:", "در برنامه → Tab Valves → دکمه Import → فایل را انتخاب کنید"),
            ("", ""),
            ("نکات:", ""),
            ("", "• Equipment باید منحصربفرد باشد (اگر تکراری باشد، (2) اضافه می‌شود)"),
            ("", "• Flow باید عدد مثبت باشد"),
            ("", "• Unit باید یکی از مقادیر مجاز باشد"),
            ("", "• ValveType باید یکی از ۴ نوع باشد"),
            ("", "• محاسبات (Kv, Kvs, Model, DN, Actuator, Signal) خودکار انجام می‌شود"),
        ]
        
        row = 3
        for label, text in guide_lines:
            cell_label = ws.cell(row=row, column=1, value=label)
            cell_label.font = Font(name="Calibri", size=11, bold=True)
            cell_label.alignment = self.left_align
            
            cell_text = ws.cell(row=row, column=2, value=text)
            cell_text.font = Font(name="Calibri", size=11)
            cell_text.alignment = self.left_align
            
            ws.row_dimensions[row].height = 22
            row += 1
        
        # ===== تنظیم عرض =====
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 80
    
    def _build_examples_sheet(self, ws):
        """ساخت Sheet نمونه‌ها"""
        
        # ===== عنوان =====
        ws.merge_cells('A1:H1')
        cell = ws['A1']
        cell.value = "📝  نمونه‌های کامل — برای هر نوع شیر"
        cell.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
        cell.fill = PatternFill(
            start_color="1F4E79", end_color="1F4E79", fill_type="solid"
        )
        cell.alignment = self.center_align
        ws.row_dimensions[1].height = 35
        
        # ===== هدرها =====
        header_row = 3
        for col_idx, field in enumerate(INPUT_FIELDS, 1):
            cell = ws.cell(row=header_row, column=col_idx)
            cell.value = FIELD_LABELS[field][0]
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_align
            cell.border = self.thin_border
        
        ws.row_dimensions[header_row].height = 25
        
        # ===== نمونه‌ها =====
        examples = [
            # ===== PICV =====
            ['PICV-AHU1', 'PICV', 1000, 'L/HR', 30, '', 'Circuit A', 1],
            ['PICV-AHU2', 'PICV', 2500, 'L/HR', 25, '', 'Circuit A', 1],
            ['PICV-FCU1', 'PICV', 200, 'L/HR', 20, '', 'FCU Line', 4],
            ['PICV-FCU2', 'PICV', 0.5, 'm³/h', 15, '', 'FCU Line', 2],
            
            # ===== 3 Way =====
            ['3W-AHU1', '3 Way', 3000, 'L/HR', 10, '', 'Circuit B', 1],
            ['3W-AHU2', '3 Way', 50, 'L/min', 8, '', 'Circuit B', 1],
            ['3W-Boiler', '3 Way', 5000, 'L/HR', 12, '', 'Boiler', 2],
            
            # ===== Steam =====
            ['ST-Boiler', 'Steam', 50, 'Kg/h', 5, 4, 'Steam Line', 1],
            ['ST-HX1', 'Steam', 100, 'Kg/h', 8, 6, 'HX Line', 1],
            ['ST-HX2', 'Steam', 110, 'lb/h', 10, 5, 'HX Line', 2],
            ['ST-DHW', 'Steam', 0.5, 'ton/h', 6, 8, 'DHW Line', 1],
            
            # ===== PICV+3Way =====
            ['P3W-AHU1', 'PICV+3Way', 1500, 'L/HR', 25, '', 'Circuit C', 1],
        ]
        
        row = header_row + 1
        for example in examples:
            for col_idx, value in enumerate(example, 1):
                cell = ws.cell(row=row, column=col_idx, value=value)
                cell.font = self.body_font
                cell.alignment = self.center_align
                cell.border = self.thin_border
            ws.row_dimensions[row].height = 22
            row += 1
        
        # ===== تنظیم عرض =====
        column_widths = {
            'A': 18, 'B': 14, 'C': 10, 'D': 10,
            'E': 14, 'F': 14, 'G': 18, 'H': 10,
        }
        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width
    
    # ============================================================
    # ✅ 2. EXPORT VALVES
    # ============================================================
    
    def export_valves(
        self, valves: List[Valve], section_name: str, file_path: str
    ) -> bool:
        """
        Export شیرها به Excel (ورودی + محاسبه‌شده)
        
        Args:
            valves: لیست شیرها
            section_name: نام Section
            file_path: مسیر ذخیره
        
        Returns:
            True اگر موفق
        """
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Valves"
            
            # ============================================================
            # ستون‌ها
            # ============================================================
            columns = [
                # ===== ورودی =====
                ('Equipment', 'Equipment', 18),
                ('ValveType', 'ValveType', 14),
                ('Flow', 'Flow', 10),
                ('Unit', 'Unit', 10),
                ('PressureDrop', 'PressureDrop', 14),
                ('SteamPressure', 'SteamPressure', 14),
                ('Circuit', 'Circuit', 18),
                ('Quantity', 'Quantity', 10),
                
                # ===== محاسبه‌شده =====
                ('MaxFlowLPH', 'MaxFlowLPH', 12),
                ('PICVModel', 'PICVModel', 14),
                ('PICVMaxFlow', 'PICVMaxFlow', 12),
                ('PICVPercent', 'PICV%', 10),
                ('PICVActuator', 'PICVActuator', 22),
                ('PICVSignal', 'PICVSignal', 18),
                ('KvCalc', 'KvCalc', 10),
                ('KvSelected', 'KvSelected', 10),
                ('3WayModel', '3WayModel', 18),
                ('3WayActuator', '3WayActuator', 22),
                ('3WaySignal', '3WaySignal', 18),
                ('KvsCalc', 'KvsCalc', 10),
                ('KvsSelected', 'KvsSelected', 10),
                ('SteamModel', 'SteamModel', 18),
                ('SteamActuator', 'SteamActuator', 22),
                ('SteamSignal', 'SteamSignal', 18),
                ('Warning', 'Warning', 40),
            ]
            
            # ============================================================
            # عنوان
            # ============================================================
            total_cols = len(columns)
            ws.merge_cells(
                start_row=1, start_column=1,
                end_row=1, end_column=total_cols
            )
            title_cell = ws.cell(row=1, column=1)
            title_cell.value = (
                f"📤  Valves Export — {section_name}  "
                f"({len(valves)} valves)  —  {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            title_cell.font = Font(
                name="Calibri", size=12, bold=True, color="FFFFFF"
            )
            title_cell.fill = PatternFill(
                start_color="2C3E50", end_color="2C3E50", fill_type="solid"
            )
            title_cell.alignment = self.center_align
            ws.row_dimensions[1].height = 30
            
            # ============================================================
            # هدرها
            # ============================================================
            header_row = 3
            for col_idx, (key, label, width) in enumerate(columns, 1):
                cell = ws.cell(row=header_row, column=col_idx, value=label)
                cell.font = self.header_font
                cell.fill = self.header_fill
                cell.alignment = self.center_align
                cell.border = self.thin_border
                
                col_letter = get_column_letter(col_idx)
                ws.column_dimensions[col_letter].width = width
            
            ws.row_dimensions[header_row].height = 28
            
            # ============================================================
            # داده‌ها
            # ============================================================
            row = header_row + 1
            for i, valve in enumerate(valves):
                is_alt = (i % 2 == 1)
                
                for col_idx, (key, label, width) in enumerate(columns, 1):
                    value = self._get_export_value(valve, key)
                    
                    cell = ws.cell(row=row, column=col_idx, value=value)
                    cell.font = self.body_font
                    cell.alignment = self.center_align
                    cell.border = self.thin_border
                    
                    if is_alt:
                        cell.fill = PatternFill(
                            start_color="F8F9FA",
                            end_color="F8F9FA",
                            fill_type="solid",
                        )
                
                ws.row_dimensions[row].height = 20
                row += 1
            
            # ============================================================
            # AutoFilter + Freeze
            # ============================================================
            ws.freeze_panes = f'A{header_row + 1}'
            
            # ============================================================
            # ذخیره
            # ============================================================
            wb.save(file_path)
            logger.info(f"Exported {len(valves)} valves to {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to export valves: {e}", exc_info=True)
            return False
    
    def _get_export_value(self, valve: Valve, key: str) -> Any:
        """دریافت مقدار یک فیلد از Valve"""
        try:
            # ===== فیلدهای ساده =====
            if key == 'Warning':
                return valve.WarningGeneral or valve.Warning3Way or valve.WarningSteam or ''
            
            if key == 'PICV%':
                return getattr(valve, 'PICVPercent', 0)
            
            # ===== فیلدهای دیگر =====
            value = getattr(valve, key, None)
            
            if value is None:
                # ===== 3Way (با __dict__ چون نام با عدد شروع می‌شود) =====
                if key.startswith('3Way'):
                    value = valve.__dict__.get(key, '')
                else:
                    value = ''
            
            return value
        
        except Exception as e:
            logger.debug(f"Export value error for {key}: {e}")
            return ''
    
    # ============================================================
    # ✅ 3. READ AND VALIDATE
    # ============================================================
    
    def read_and_validate(self, file_path: str) -> Dict[str, Any]:
        """
        خواندن فایل و validate کردن
        
        Args:
            file_path: مسیر فایل Excel
        
        Returns:
            {
                'success': bool,
                'error': str (اگر خطا),
                'valves': List[Valve],
                'warnings': List[str],
                'stats': {'total': int, 'by_type': {...}},
            }
        """
        result = {
            'success': False,
            'error': '',
            'valves': [],
            'warnings': [],
            'stats': {'total': 0, 'by_type': {}},
        }
        
        try:
            # ===== ۱. باز کردن فایل =====
            if not os.path.exists(file_path):
                result['error'] = f"فایل پیدا نشد: {file_path}"
                return result
            
            wb = load_workbook(file_path, data_only=True)
            
            # ===== ۲. پیدا کردن Sheet 'Valves' =====
            if 'Valves' in wb.sheetnames:
                ws = wb['Valves']
            else:
                ws = wb.active   # اگر Sheet به این نام نبود
            
            # ===== ۳. پیدا کردن ردیف هدر =====
            header_row = self._find_header_row(ws)
            if not header_row:
                result['error'] = "هدر ستون‌ها پیدا نشد. فایل Template معتبر نیست."
                return result
            
            # ===== ۴. نگاشت ستون‌ها =====
            col_map = self._map_columns(ws, header_row)
            
            if not col_map:
                result['error'] = "ستون‌های فایل با Template مطابقت ندارد."
                return result
            
            # ===== ۵. خواندن ردیف‌ها =====
            valves = []
            warnings = []
            type_counts = {}
            
            row_num = header_row + 1
            max_row = ws.max_row
            
            while row_num <= max_row:
                row_data = self._read_row(ws, row_num, col_map)
                
                # ✅ چک خالی
                equipment_val = row_data.get('equipment', '')
                valve_type_val = row_data.get('valvetype', '')
                
                if not equipment_val and not valve_type_val:
                    row_num += 1
                    continue
                
                # ✅ چک ستون _Sample — اگر ردیف نمونه است، رد کن
                sample_val = ws.cell(
                    row=row_num,
                    column=len(INPUT_FIELDS) + 1
                ).value
                
                if sample_val and str(sample_val).strip().upper() == 'SAMPLE':
                    print(f"   ⏭️ Skipping sample row {row_num}")
                    row_num += 1
                    continue
                
                # ===== Validate =====
                is_valid, error, valve = self._validate_row(row_data, row_num)
                
                if is_valid:
                    valves.append(valve)
                    vt = valve.ValveType
                    type_counts[vt] = type_counts.get(vt, 0) + 1
                else:
                    warnings.append(f"ردیف {row_num}: {error}")
                
                row_num += 1
            
            # ===== ۶. نتیجه =====
            if not valves:
                result['error'] = (
                    "هیچ شیر معتبری در فایل پیدا نشد.\n\n"
                    f"تعداد هشدارها: {len(warnings)}"
                )
                if warnings:
                    result['error'] += "\n\n" + "\n".join(warnings[:10])
                return result
            
            result['success'] = True
            result['valves'] = valves
            result['warnings'] = warnings
            result['stats'] = {
                'total': len(valves),
                'by_type': type_counts,
            }
            
            logger.info(
                f"Read {len(valves)} valves from {file_path} "
                f"({len(warnings)} warnings)"
            )
            return result
        
        except Exception as e:
            logger.error(f"Read failed: {e}", exc_info=True)
            result['error'] = f"خطا در خواندن فایل: {str(e)}"
            return result
    
    def _find_header_row(self, ws) -> Optional[int]:
        """پیدا کردن ردیف هدر (که شامل 'Equipment' است)"""
        for row in range(1, min(ws.max_row + 1, 20)):
            for col in range(1, 15):
                cell = ws.cell(row=row, column=col)
                if cell.value and str(cell.value).strip().lower() == 'equipment':
                    return row
        return None
    
    def _map_columns(self, ws, header_row: int) -> Dict[str, int]:
        """نگاشت نام ستون → شماره ستون"""
        col_map = {}
        
        for col in range(1, 20):
            cell = ws.cell(row=header_row, column=col)
            if not cell.value:
                continue
            
            header = str(cell.value).strip().lower()
            
            # ===== نگاشت =====
            for field in INPUT_FIELDS:
                if header == field.lower():
                    col_map[field] = col
                    break
        
        return col_map
    
    def _read_row(self, ws, row_num: int, col_map: Dict[str, int]) -> Dict[str, Any]:
        """خواندن یک ردیف"""
        data = {}
        
        for field in INPUT_FIELDS:
            if field in col_map:
                cell = ws.cell(row=row_num, column=col_map[field])
                value = cell.value
            else:
                value = None
            
            # ===== نرمال‌سازی =====
            if value is None:
                value = ''
            elif isinstance(value, str):
                value = value.strip()
            
            data[field.lower()] = value
        
        return data
    
    def _validate_row(
        self, row_data: Dict[str, Any], row_num: int
    ) -> Tuple[bool, str, Optional[Valve]]:
        """
        Validate یک ردیف و ساخت Valve
        
        Returns:
            (is_valid, error_message, valve_object)
        """
        try:
            # ============================================================
            # Equipment
            # ============================================================
            equipment = str(row_data.get('equipment', '')).strip()
            if not equipment:
                return False, "Equipment خالی است", None
            

            # ============================================================
            # ValveType — ✅ case-insensitive
            # ============================================================
            valve_type = str(row_data.get('valvetype', '')).strip()
            if not valve_type:
                return False, "ValveType خالی است", None
            
            # نرمال‌سازی: 'picv' → 'PICV', '3 way' → '3 Way'
            valve_type_normalized = None
            for allowed in ALLOWED_VALVE_TYPES:
                if valve_type.lower() == allowed.lower():
                    valve_type_normalized = allowed
                    break
            
            if not valve_type_normalized:
                return False, (
                    f"ValveType نامعتبر: '{valve_type}'. "
                    f"مجاز: {', '.join(ALLOWED_VALVE_TYPES)}"
                ), None
            
            valve_type = valve_type_normalized
            
            # ============================================================
            # Flow
            # ============================================================
            try:
                flow = float(row_data.get('flow', 0))
                if flow <= 0:
                    return False, "Flow باید بزرگ‌تر از صفر باشد", None
            except (ValueError, TypeError):
                return False, f"Flow نامعتبر: '{row_data.get('flow')}'", None
            
            
            # ============================================================
            # Unit — ✅ case-insensitive
            # ============================================================
            unit = str(row_data.get('unit', '')).strip()
            if not unit:
                return False, "Unit خالی است", None
            
            # نرمال‌سازی: 'gpm' → 'GPM', 'lb/hr' → 'lb/h'
            unit_normalized = None
            unit_mapping = {
                'l/hr': 'L/HR', 'l/hr': 'L/HR',
                'l/h': 'L/HR', 'lph': 'L/HR',
                'l/min': 'L/min',
                'l/s': 'L/s',
                'm³/h': 'm³/h', 'm3/h': 'm³/h',
                'gpm': 'GPM', 'GPM': 'GPM',
                'kg/h': 'Kg/h', 'kg/hr': 'Kg/h',
                'lb/h': 'lb/h', 'lb/hr': 'lb/h',
                'ton/h': 'ton/h', 'ton/hr': 'ton/h',
            }
            
            unit_lower = unit.lower()
            if unit_lower in unit_mapping:
                unit_normalized = unit_mapping[unit_lower]
            else:
                return False, (
                    f"Unit نامعتبر: '{unit}'. "
                    f"مجاز: L/HR, L/min, m³/h, GPM, Kg/h, lb/h, ton/h"
                ), None
            
            unit = unit_normalized
            
            # ============================================================
            # PressureDrop
            # ============================================================
            try:
                pressure_drop = float(row_data.get('pressuredrop', 0))
                if pressure_drop <= 0:
                    return False, "PressureDrop باید بزرگ‌تر از صفر باشد", None
            except (ValueError, TypeError):
                return False, (
                    f"PressureDrop نامعتبر: '{row_data.get('pressuredrop')}'"
                ), None
            
            # ============================================================
            # SteamPressure
            # ============================================================
            steam_pressure = 0.0
            if valve_type == 'Steam':
                try:
                    steam_pressure = float(row_data.get('steampressure', 0))
                    if steam_pressure <= 0:
                        return False, (
                            "برای Steam باید SteamPressure > 0 باشد"
                        ), None
                except (ValueError, TypeError):
                    return False, (
                        f"SteamPressure نامعتبر: "
                        f"'{row_data.get('steampressure')}'"
                    ), None
            
            # ============================================================
            # Circuit
            # ============================================================
            circuit = str(row_data.get('circuit', '')).strip()
            
            # ============================================================
            # Quantity
            # ============================================================
            try:
                quantity = int(row_data.get('quantity', 1))
                if quantity <= 0:
                    quantity = 1
            except (ValueError, TypeError):
                quantity = 1
            
            # ============================================================
            # ساخت Valve
            # ============================================================
            valve = Valve(
                Equipment=equipment,
                ValveType=valve_type,
                Flow=flow,
                Unit=unit,
                PressureDrop=pressure_drop,
                SteamPressure=steam_pressure,
                Circuit=circuit,
                Quantity=quantity,
            )
            
            # ============================================================
            # ✅ محاسبه خودکار
            # ============================================================
            try:
                enrich_valve(valve)
            except Exception as e:
                logger.warning(
                    f"enrich_valve failed for row {row_num} "
                    f"({equipment}): {e}"
                )
                # ادامه می‌دهیم — شیر با داده خالی ساخته می‌شود
            
            return True, '', valve
        
        except Exception as e:
            logger.error(f"Validate row {row_num} failed: {e}", exc_info=True)
            return False, f"خطای غیرمنتظره: {str(e)}", None
    
    # ============================================================
    # ✅ 4. APPLY IMPORT
    # ============================================================
    
    def apply_import(
        self, valves: List[Valve], section
    ) -> int:
        """
        افزودن شیرها به Section
        """
        try:
            print("=" * 70)
            print("🔧 apply_import START")
            print("=" * 70)
            
            if not section:
                print("❌ section is None")
                return 0
            
            print(f"📍 section: {section}")
            print(f"   name: {section.name!r}")
            print(f"   valves BEFORE: {len(getattr(section, 'valves', []))}")
            
            # ===== لیست Equipment موجود =====
            existing_names = set()
            for v in getattr(section, 'valves', []):
                existing_names.add(v.Equipment or '')
            
            print(f"   existing_names: {len(existing_names)}")
            
            # ===== افزودن =====
            added_count = 0
            errors = []
            
            for i, valve in enumerate(valves, 1):
                try:
                    new_valve = valve.copy()
                    
                    if new_valve.Equipment in existing_names:
                        base_name = new_valve.Equipment
                        counter = 2
                        new_name = f"{base_name} ({counter})"
                        
                        while new_name in existing_names:
                            counter += 1
                            new_name = f"{base_name} ({counter})"
                        
                        new_valve.Equipment = new_name
                    
                    section.valves.append(new_valve)
                    existing_names.add(new_valve.Equipment)
                    added_count += 1
                
                except Exception as e:
                    errors.append(f"Valve {i} ({valve.Equipment}): {e}")
                    print(f"❌ Error adding valve {i}: {e}")
            
            print(f"✅ added_count: {added_count}")
            print(f"   valves AFTER: {len(getattr(section, 'valves', []))}")
            
            if errors:
                print(f"⚠️ {len(errors)} errors:")
                for e in errors[:5]:
                    print(f"   • {e}")
            
            print("=" * 70)
            print("🔧 apply_import END")
            print("=" * 70)
            
            return added_count
        
        except Exception as e:
            import traceback
            print(f"❌❌❌ apply_import EXCEPTION: {e}")
            traceback.print_exc()
            return 0

# ================================================================
# EXPORTS
# ================================================================

__all__ = ['ValvesExcelImporter']