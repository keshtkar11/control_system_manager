# gui/valves/valve_dialog.py
"""
دیالوگ افزودن/ویرایش شیر
با ۳۰ فیلد شرطی بر اساس نوع شیر
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, List

from core.models import Valve
from core.valve_constants import (
    VALVE_TYPES,
    CIRCUIT_TYPES,
    SIGNAL_TYPES,
    FLOW_UNITS,
    DEFAULT_PRESSURE_DROP_PSI,
    DEFAULT_FLOW_UNIT,
    PSI_TO_BAR,
)
from core.valve_calculator import enrich_valve

from gui.theme import (
    get_color, font, sp, pad, h, w, ico,
)
from gui.components import (
    BaseDialog, PrimaryButton, SecondaryButton,
    GhostButton, ToastManager,
)


# ================================================================
# ساختار فیلدها (برای رندر)
# ================================================================
# تعریف هر فیلد:
# (کلید، برچسب، نوع، گروه، readonly، پهنای ستون)
# نوع: 'text', 'number', 'combo', 'readonly'
VALVE_FIELD_DEFINITIONS = [
    # ===== پایه =====
    ('Equipment',      'Equipment',           'text',     'base', False, 40),
    ('Quantity',       'Quantity',            'number',   'base', False, 10),
    ('Circuit',        'Circuit',             'combo',    'base', False, 15),
    ('Flow',           'Flow',                'number',   'base', False, 12),
    ('PressureDrop',   'Pressure Drop (psi)', 'number',   'base', False, 15),
    ('PressureDropBar',   'Pressure Drop (bar)', 'readonly', 'base', True,  15),
    ('Unit',           'Unit',                'combo',    'base', False, 12),
    ('ValveType',      'Valve Type',          'combo',    'base', False, 15),
    
    # ===== محاسبه‌شده پایه =====
    ('MaxFlowLPH',     'Max Flow (L/HR)',     'readonly', 'base', True,  15),
    
    # ===== PICV =====
    ('PICVModel',      'PICV Model',          'text',     'picv', False, 25),
    ('PICVMaxFlow',    'PICV Max Flow (L/HR)','readonly', 'picv', True,  18),
    ('PICVPercent',    'PICV Percent (%)',    'readonly', 'picv', True,  15),
    ('PICVActuator',   'PICV Actuator',       'readonly', 'picv', True,  30),
    ('PICVSignal',     'PICV Signal',         'combo',    'picv', False, 18),
    
    # ===== 3Way =====
    ('KvCalc',         'Kv Calculated',       'readonly', '3way', True,  15),
    ('KvSelected',     'Kv Selected',         'readonly', '3way', True,  15),
    ('3WayDN',         '3-Way DN',            'readonly', '3way', True,  12),
    ('3WayModel',      '3-Way Model',         'readonly', '3way', True,  20),
    ('3WayActuator',   '3-Way Actuator',      'readonly', '3way', True,  25),
    ('3WaySignal',     '3-Way Signal',        'combo',    '3way', False, 18),
    
    # ===== Steam =====
    ('SteamPressure',  'Steam Inlet (bar)',   'number',   'steam', False, 15),
    ('SteamPN',         'PN Rating',           'readonly', 'steam', True,  10),  # ✅ جدید
    ('SteamTMax',       'T Max (°C)',          'readonly', 'steam', True,  10),  # ✅ جدید
    ('SteamMaterial',   'Body Material',       'readonly', 'steam', True,  25),  # ✅ جدید
    
    # ✅ جدید: تبدیل خودکار دبی بخار
    ('SteamFlowKgH',   'Flow (kg/h)',         'readonly', 'steam', True,  15),
    ('SteamFlowLbH',   'Flow (lb/h)',         'readonly', 'steam', True,  15),
    ('SteamFlowTonH',  'Flow (ton/h)',        'readonly', 'steam', True,  15),
    
    ('KvsCalc',        'kvs Calculated',      'readonly', 'steam', True,  15),
    ('KvsSelected',    'kvs Selected',        'readonly', 'steam', True,  15),
    ('SteamDN',        'Steam DN',            'readonly', 'steam', True,  12),
    ('SteamModel',     'Steam Model',         'readonly', 'steam', True,  20),
    ('SteamActuator',  'Steam Actuator',      'readonly', 'steam', True,  25),
    ('SteamSignal',    'Steam Signal',        'combo',    'steam', False, 18),
]



# ================================================================
# VALVE DIALOG
# ================================================================

class ValveDialog(BaseDialog):
    """
    دیالوگ افزودن/ویرایش شیر
    """
    
    def __init__(self, parent, app, valve: Optional[Valve] = None,
                 section=None, is_new: bool = False):
        """
        Args:
            parent: پنجره والد
            app: MotorApp
            valve: شیء Valve (برای ویرایش) یا None (برای جدید)
            section: Section فعلی
            is_new: آیا شیر جدید است؟
        """
        self.app = app
        self.valve = valve or Valve()
        self.section = section
        self.is_new = is_new
        if is_new and not self.valve.Unit:
            self.valve.Unit = 'GPM'
        
        # ============================================================
        # ذخیره entry widgets برای دسترسی بعدی
        # ============================================================
        self.entries: Dict[str, tk.Widget] = {}
        self._last_warning = ''
        self.pressure_drop_hint = None
        
        # ============================================================
        # عنوان
        # ============================================================
        if is_new:
            title = "Add Valve"
        else:
            title = f"Edit Valve: {self.valve.Equipment or 'Unnamed'}"
        
        super().__init__(
            parent,
            title=title,
            width=950,
            height=750,
            resizable=True,
        )
    
    # ================================================================
    # BUILD BODY
    # ================================================================
    
    def build_body(self, parent):
        """ساخت محتوای دیالوگ"""
        
        # ============================================================
        # Container با اسکرول
        # ============================================================
        container = tk.Frame(parent, bg=get_color('bg_app'))
        container.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(
            container,
            bg=get_color('bg_app'),
            highlightthickness=0,
        )
        
        v_scrollbar = ttk.Scrollbar(
            container, orient='vertical', command=canvas.yview
        )
        
        scrollable = tk.Frame(canvas, bg=get_color('bg_app'))
        
        scrollable.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas_window = canvas.create_window(
            (0, 0), window=scrollable, anchor='nw'
        )
        
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind('<Configure>', _on_canvas_configure)
        
        canvas.configure(yscrollcommand=v_scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ============================================================
        # محتوای دیالوگ
        # ============================================================
        self._build_form(scrollable)
        self._build_warning_panel(scrollable)
        
        # ============================================================
        # MouseWheel برای اسکرول
        # ============================================================
        self._bind_mousewheel_recursive(canvas, scrollable)
        
        # ============================================================
        # به‌روزرسانی اولیه
        # ============================================================
        self.after(100, self._recalculate)
    
    def _bind_mousewheel_recursive(self, canvas, widget):
        """اتصال MouseWheel به همه ویجت‌ها"""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
            return "break"
        
        def _on_linux_mousewheel(event):
            if event.num == 4:
                canvas.yview_scroll(-1, 'units')
            elif event.num == 5:
                canvas.yview_scroll(1, 'units')
            return "break"
        
        try:
            widget.bind('<MouseWheel>', _on_mousewheel, add='+')
            widget.bind('<Button-4>', _on_linux_mousewheel, add='+')
            widget.bind('<Button-5>', _on_linux_mousewheel, add='+')
        except:
            pass
        
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(canvas, child)
    
    # ================================================================
    # BUILD FORM
    # ================================================================
    
    def _build_form(self, parent):
        """ساخت فرم ۳۰ فیلد"""
        
        # ============================================================
        # گروه‌بندی فیلدها
        # ============================================================
        groups = {
            'base':  ('📋 Base Information', 'info_circle'),
            'picv':  ('🔵 PICV (Pressure Independent Control Valve)', 'valve'),
            '3way':  ('🟡 3-Way Valve', 'valve'),
            'steam': ('🔴 Steam Valve', 'valve'),
        }
        
        # ============================================================
        # برای هر گروه، یک LabelFrame
        # ============================================================
        for group_key, (group_title, group_icon) in groups.items():
            # فقط اگر فیلدی در این گروه وجود دارد
            group_fields = [
                f for f in VALVE_FIELD_DEFINITIONS 
                if f[3] == group_key
            ]
            
            if not group_fields:
                continue
            
            frame = tk.LabelFrame(
                parent,
                text=f"  {group_title}  ",
                font=font('body_bold'),
                bg=get_color('bg_surface'),
                fg=get_color('text_primary'),
                padx=sp('md'),
                pady=sp('md'),
                labelanchor='nw',
            )
            frame.pack(fill=tk.X, padx=sp('md'), pady=sp('sm'))
            
            # ===== ساخت فیلدها =====
            self._build_group_fields(frame, group_fields)
        
        # ============================================================
        # راهنمای رنگ
        # ============================================================
        hint = tk.Label(
            parent,
            text="💡 Tip: Type 'Flow' unit and 'Valve Type' — other fields will auto-calculate.",
            font=font('caption'),
            bg=get_color('bg_app'),
            fg=get_color('text_muted'),
            anchor='w',
        )
        hint.pack(fill=tk.X, padx=sp('lg'), pady=sp('md'))
        self._build_steam_info_card(parent)

    def _build_steam_info_card(self, parent):
        """
        ساخت کارت اطلاعات Steam — زیر فرم اصلی
        فقط برای ValveType == 'Steam' نمایش داده می‌شود
        """
        
        # ============================================================
        # Frame اصلی
        # ============================================================
        self.steam_info_frame = tk.LabelFrame(
            parent,
            text="  📊 Steam Information (Auto)  ",
            font=font('body_bold'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_primary'),
            padx=sp('md'),
            pady=sp('md'),
            labelanchor='nw',
        )
        
        # ============================================================
        # ردیف ۱: دما + دسته‌بندی
        # ============================================================
        row1 = tk.Frame(self.steam_info_frame, bg=get_color('bg_surface_alt'))
        row1.pack(fill=tk.X, pady=sp('xs'))
        
        # دما
        self.steam_temp_label = tk.Label(
            row1,
            text="🌡️ دمای اشباع:  —",
            font=font('body_bold'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('primary'),
            anchor='w',
        )
        self.steam_temp_label.pack(side=tk.LEFT, padx=(0, sp('lg')))
        
        # دسته‌بندی
        self.steam_cat_label = tk.Label(
            row1,
            text="📊 دسته:  —",
            font=font('body_bold'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_secondary'),
            anchor='w',
        )
        self.steam_cat_label.pack(side=tk.LEFT)
        
        # ============================================================
        # ردیف ۲: کاربردها
        # ============================================================
        self.steam_apps_label = tk.Label(
            self.steam_info_frame,
            text="🏭 کاربردها:  —",
            font=font('body'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_secondary'),
            anchor='w',
            justify='left',
            wraplength=850,
        )
        self.steam_apps_label.pack(fill=tk.X, pady=sp('xs'))
        
        # ============================================================
        # ردیف ۳: هشدارها
        # ============================================================
        self.steam_warnings_label = tk.Label(
            self.steam_info_frame,
            text="",
            font=font('caption'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('danger'),
            anchor='w',
            justify='left',
            wraplength=850,
        )
        self.steam_warnings_label.pack(fill=tk.X, pady=sp('xs'))
    
    def _build_group_fields(self, parent, fields: List):
        """ساخت فیلدهای یک گروه"""
        for i, field_def in enumerate(fields):
            key, label, field_type, group, readonly, width = field_def
            
            row = i
            col_offset = 0
            
            label_widget = tk.Label(
                parent,
                text=f"{label}:",
                font=font('body'),
                bg=get_color('bg_surface'),
                fg=get_color('text_secondary'),
                anchor='w',
                width=22,
            )
            label_widget.grid(
                row=row, column=col_offset,
                sticky='w', padx=(0, sp('sm')), pady=sp('xs')
            )
            
            widget = self._create_field_widget(
                parent, key, field_type, readonly, width
            )
            widget.grid(
                row=row, column=col_offset + 1,
                sticky='ew', padx=(0, sp('lg')), pady=sp('xs')
            )
            
            # ============================================================
            # ✅ راهنمای Pressure Drop
            # ============================================================
            if key == 'PressureDrop':
                self.pressure_drop_hint = tk.Label(
                    parent,
                    text="",
                    font=font('caption'),
                    bg=get_color('bg_surface'),
                    fg=get_color('text_muted'),
                    anchor='w',
                )
                self.pressure_drop_hint.grid(
                    row=row, column=col_offset + 2,
                    sticky='w', padx=(sp('sm'), 0), pady=sp('xs')
                )
            
            self.entries[key] = widget
        
        parent.grid_columnconfigure(1, weight=1)
    
    def _create_field_widget(self, parent, key: str, field_type: str,
                             readonly: bool, width: int) -> tk.Widget:
        """ساخت ویجت مناسب برای هر فیلد"""
        
        # ============================================================
        # مقدار فعلی
        # ============================================================
        current_value = self._get_current_value(key)
        
        # ============================================================
        # Combo
        # ============================================================
        if field_type == 'combo':
            values = self._get_combo_values(key)
            
            combo = ttk.Combobox(
                parent,
                values=values,
                state='readonly',
                width=width,
                font=font('input'),
            )
            
            # ============================================================
            # ✅ مقدار پیش‌فرض
            # ============================================================
            default_value = self._get_default_value(key)
            
            # اولویت: مقدار فعلی → پیش‌فرض → اولین گزینه
            if current_value and str(current_value) in values:
                combo.set(str(current_value))
            elif default_value and default_value in values:
                combo.set(default_value)
            elif values:
                combo.set(values[0])
            
            # ============================================================
            # رویداد تغییر → محاسبه مجدد
            # ============================================================
            combo.bind('<<ComboboxSelected>>', 
                       lambda e: self._on_field_change())
            
            return combo
        
        # ============================================================
        # Readonly (محاسبه‌شده)
        # ============================================================
        if readonly:
            # مقدار نمایشی
            display_value = self._format_display_value(key, current_value)
            
            label = tk.Label(
                parent,
                text=display_value,
                font=font('body_bold'),
                bg=get_color('bg_surface_alt'),
                fg=get_color('primary'),
                anchor='w',
                width=width,
                relief='flat',
                padx=sp('sm'),
                pady=2,
            )
            return label
        
        # ============================================================
        # Text / Number
        # ============================================================
        entry = tk.Entry(
            parent,
            font=font('input'),
            bg=get_color('input_bg'),
            fg=get_color('input_text'),
            insertbackground=get_color('input_text'),
            relief='flat',
            width=width,
            justify='left' if field_type == 'text' else 'center',
        )
        
        # ============================================================
        # ✅ مقدار پیش‌فرض برای فیلدهای Number
        # ============================================================
        if current_value is not None and current_value != '':
            # مقدار فعلی موجود است
            entry.insert(0, str(current_value))
        elif field_type == 'number':
            # مقدار پیش‌فرض برای Number
            default_value = self._get_default_value(key)
            if default_value is not None:
                entry.insert(0, str(default_value))
        
        # ============================================================
        # رویداد تغییر → محاسبه مجدد
        # ============================================================
        entry.bind('<KeyRelease>', lambda e: self._on_field_change())
        entry.bind('<FocusOut>', lambda e: self._on_field_change())
        
        return entry
    
    def _get_combo_values(self, key: str) -> List[str]:
        """مقادیر Combo بر اساس کلید"""
        if key == 'Circuit':
            return CIRCUIT_TYPES
        elif key == 'Unit':
            return list(FLOW_UNITS.keys())
        elif key == 'ValveType':
            return VALVE_TYPES
        elif key in ('PICVSignal', '3WaySignal', 'SteamSignal'):
            return SIGNAL_TYPES
        return []

    def _get_default_value(self, key: str):
        """
        دریافت مقدار پیش‌فرض برای فیلدها
        
        Args:
            key: کلید فیلد
        
        Returns:
            مقدار پیش‌فرض (str برای Combo، عدد برای Number)
        """
        # ============================================================
        # مقادیر پیش‌فرض برای Combo
        # ============================================================
        combo_defaults = {
            'Unit': 'GPM',           # ✅ پیش‌فرض GPM
            'Circuit': 'گرمایش',      # رایج‌ترین
            'ValveType': 'PICV',     # رایج‌ترین
            'PICVSignal': 'Modulating , 24Vac , 0-10V',     # رایج‌ترین
            '3WaySignal': 'Modulating , 24Vac , 0-10V',     # رایج‌ترین
            'SteamSignal': 'Modulating , 24Vac , 0-10V',    # رایج‌ترین
        }
        
        # ============================================================
        # مقادیر پیش‌فرض برای Number
        # ============================================================
        number_defaults = {
            'PressureDrop': 5,       # قبلاً در Valve.__init__
            'Quantity': 1,           # قبلاً در Valve.__init__
            'SteamPressure': 2, 
        }
        
        # ============================================================
        # برگرداندن مقدار
        # ============================================================
        if key in combo_defaults:
            return combo_defaults[key]
        elif key in number_defaults:
            return number_defaults[key]
        
        return ''
    
    def _get_current_value(self, key: str):
        """دریافت مقدار فعلی از شیء Valve"""
        try:
            value = getattr(self.valve, key, '')
            return value
        except Exception:
            return ''
    
    def _format_display_value(self, key: str, value) -> str:
        """فرمت نمایش برای فیلدهای readonly"""
        
        # ============================================================
        # ✅ جدید: فیلدهای VFS 2 (قبل از بلاک خالی)
        # ============================================================
        if key == 'SteamPN':
            info = self.valve.__dict__.get('_vfs2_info', None)
            if info:
                return f"PN {info.get('pn', '?')}"
            return "PN 25"
        
        if key == 'SteamTMax':
            info = self.valve.__dict__.get('_vfs2_info', None)
            if info:
                return f"{info.get('t_max', '?')}°C"
            return "200°C"
        
        if key == 'SteamMaterial':
            info = self.valve.__dict__.get('_vfs2_info', None)
            if info:
                return info.get('body_material_short', 'Ductile Iron')
            return "Ductile Iron"
        
        # ============================================================
        # ✅ فیلدهای تبدیل واحد بخار (قبل از بلاک خالی)
        # ============================================================
        if key in ('SteamFlowKgH', 'SteamFlowLbH', 'SteamFlowTonH'):
            conversions = self.valve.__dict__.get('_steam_conversions', None)
            
            if not conversions:
                return '—'
            
            if key == 'SteamFlowKgH':
                val = conversions.get('kg_h', 0.0)
                return f"{val:.2f}"
            
            if key == 'SteamFlowLbH':
                val = conversions.get('lb_h', 0.0)
                return f"{val:.2f}"
            
            if key == 'SteamFlowTonH':
                val = conversions.get('ton_h', 0.0)
                return f"{val:.4f}"
        
        # ============================================================
        # ✅ حالا بلاک خالی
        # ============================================================
        if value is None or value == '':
            return '—'
        
        # ============================================================
        # اعداد اعشاری
        # ============================================================
        if key in ('PICVMaxFlow', 'KvCalc', 'KvSelected',
                'KvsCalc', 'KvsSelected', 'MaxFlowLPH'):
            try:
                return f"{float(value):.2f}"
            except (ValueError, TypeError):
                return str(value)
        
        # ============================================================
        # درصد
        # ============================================================
        if key == 'PICVPercent':
            try:
                return f"{float(value):.1f}%"
            except (ValueError, TypeError):
                return str(value)
        
        # ============================================================
        # DN
        # ============================================================
        if key in ('3WayDN', 'SteamDN'):
            try:
                return f"DN{int(value)}"
            except (ValueError, TypeError):
                return str(value)
        
        # ============================================================
        # Pressure Drop Bar
        # ============================================================
        if key == 'PressureDropBar':
            try:
                val_psi = float(self.valve.PressureDrop or 0)
                val_bar = val_psi * PSI_TO_BAR
                return f"{val_bar:.4f}"
            except (ValueError, TypeError):
                return '—'
        
        return str(value)

    # ================================================================
    # BUILD WARNING PANEL
    # ================================================================
    
    def _build_warning_panel(self, parent):
        """ساخت پنل هشدار در پایین"""
        
        self.warning_frame = tk.Frame(
            parent,
            bg=get_color('danger_bg'),
            highlightthickness=1,
            highlightbackground=get_color('danger'),
        )
        
        self.warning_label = tk.Label(
            self.warning_frame,
            text="",
            font=font('body'),
            bg=get_color('danger_bg'),
            fg=get_color('danger'),
            anchor='w',
            justify='left',
            wraplength=850,
            padx=sp('md'),
            pady=sp('sm'),
        )
        self.warning_label.pack(fill=tk.X)

    def _build_steam_info_card(self, parent):
        """
        ساخت کارت اطلاعات Steam
        فقط برای ValveType == 'Steam' نمایش داده می‌شود
        """
        
        # ============================================================
        # Frame اصلی
        # ============================================================
        self.steam_info_frame = tk.LabelFrame(
            parent,
            text="  📊 Steam Information (Auto)  ",
            font=font('body_bold'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_primary'),
            padx=sp('md'),
            pady=sp('md'),
            labelanchor='nw',
        )
        
        # ============================================================
        # ردیف ۱: دما + دسته‌بندی
        # ============================================================
        row1 = tk.Frame(self.steam_info_frame, bg=get_color('bg_surface_alt'))
        row1.pack(fill=tk.X, pady=sp('xs'))
        
        self.steam_temp_label = tk.Label(
            row1,
            text="🌡️ دمای اشباع:  —",
            font=font('body_bold'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('primary'),
            anchor='w',
        )
        self.steam_temp_label.pack(side=tk.LEFT, padx=(0, sp('lg')))
        
        self.steam_cat_label = tk.Label(
            row1,
            text="📊 دسته:  —",
            font=font('body_bold'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_secondary'),
            anchor='w',
        )
        self.steam_cat_label.pack(side=tk.LEFT)
        
        # ============================================================
        # ردیف ۲: کاربردها
        # ============================================================
        self.steam_apps_label = tk.Label(
            self.steam_info_frame,
            text="🏭 کاربردها:  —",
            font=font('body'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_secondary'),
            anchor='w',
            justify='left',
            wraplength=850,
        )
        self.steam_apps_label.pack(fill=tk.X, pady=sp('xs'))
        
        # ============================================================
        # ردیف ۳: چگالی و محدوده فشار
        # ============================================================
        self.steam_rho_label = tk.Label(
            self.steam_info_frame,
            text="ℹ️ چگالی:  —",
            font=font('caption'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_muted'),
            anchor='w',
        )
        self.steam_rho_label.pack(fill=tk.X, pady=sp('xs'))
        
        # ============================================================
        # ردیف ۴: هشدارها
        # ============================================================
        self.steam_warnings_label = tk.Label(
            self.steam_info_frame,
            text="",
            font=font('caption'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('danger'),
            anchor='w',
            justify='left',
            wraplength=850,
        )
        self.steam_warnings_label.pack(fill=tk.X, pady=sp('xs'))
    # ================================================================
    # RECALCULATE
    # ================================================================
    
    def _on_field_change(self):
        """هنگام تغییر یک فیلد"""
        # ============================================================
        # ۱. خواندن همه مقادیر از UI
        # ============================================================
        self._read_all_fields_to_valve()
        self._clear_unrelated_fields()
        
        # ============================================================
        # ✅ جدید: اگر ValveType = Steam و SteamPressure = 0
        # ============================================================
        if (self.valve.ValveType == 'Steam' 
            and (not self.valve.SteamPressure or self.valve.SteamPressure <= 0)):
            self.valve.SteamPressure = 2
            
            # به‌روزرسانی UI
            widget = self.entries.get('SteamPressure')
            if widget and isinstance(widget, tk.Entry):
                if not widget.get().strip():
                    widget.delete(0, tk.END)
                    widget.insert(0, '2')
        
        # ============================================================
        # ۲. محاسبه مجدد
        # ============================================================
        self._recalculate()
    
    def _read_all_fields_to_valve(self):
        """خواندن مقادیر از UI به شیء Valve"""
        for key, widget in self.entries.items():
            # ============================================================
            # پیدا کردن field_type
            # ============================================================
            field_type = None
            readonly = False
            
            for field_def in VALVE_FIELD_DEFINITIONS:
                if field_def[0] == key:
                    field_type = field_def[2]
                    readonly = field_def[4]
                    break
            
            # ============================================================
            # اگر readonly بود، رد کن
            # ============================================================
            if readonly:
                continue
            
            # ============================================================
            # خواندن مقدار
            # ============================================================
            try:
                if field_type == 'combo':
                    value = widget.get()
                else:
                    value = widget.get()
            except Exception:
                continue
            
            # ============================================================
            # اعتبارسنجی عددی
            # ============================================================
            if field_type == 'number':
                try:
                    # اگر خالی بود → صفر
                    if not value or not value.strip():
                        value = 0
                    else:
                        # تبدیل به عدد
                        if key in ('Quantity', '3WayDN', 'SteamDN'):
                            value = int(float(value))
                        else:
                            value = float(value)
                except (ValueError, TypeError):
                    value = 0
            
            # ============================================================
            # ذخیره در Valve
            # ============================================================
            try:
                setattr(self.valve, key, value)
            except Exception:
                # اگر فیلد خاص بود (مثل 3WayDN)
                self.valve.__dict__[key] = value

    def _clear_unrelated_fields(self):   # ← 🆕 اینجا اضافه شود
        """پاک‌کردن فیلدهای نامرتبط با نوع شیر فعلی"""
        vtype = self.valve.ValveType or ''
        
        # ============================================================
        # PICV — فقط برای PICV و PICV+3Way
        # ============================================================
        if vtype not in ('PICV', 'PICV+3Way'):
            self.valve.PICVModel = ''
            self.valve.PICVActuator = ''
            self.valve.PICVSignal = ''
            self.valve.PICVMaxFlow = 0
            self.valve.PICVPercent = 0
        
        # ============================================================
        # 3Way — فقط برای 3 Way و PICV+3Way
        # ============================================================
        if vtype not in ('3 Way', 'PICV+3Way'):
            self.valve.KvCalc = 0
            self.valve.KvSelected = 0
            self.valve.__dict__['3WayDN'] = 0
            self.valve.__dict__['3WayModel'] = ''
            self.valve.__dict__['3WayActuator'] = ''
            self.valve.__dict__['3WaySignal'] = ''
        
        # ============================================================
        # Steam — فقط برای Steam
        # ============================================================
        if vtype != 'Steam':
            self.valve.SteamPressure = 0
            self.valve.KvsCalc = 0
            self.valve.KvsSelected = 0
            self.valve.SteamDN = 0
            self.valve.SteamModel = ''
            self.valve.SteamActuator = ''
            self.valve.SteamSignal = ''
            self.valve.__dict__['_steam_conversions'] = None
        # ============================================================
        # Warning ها
        # ============================================================
        if vtype not in ('3 Way', 'PICV+3Way'):
            self.valve.Warning3Way = ''
        if vtype != 'Steam':
            self.valve.WarningSteam = ''
    
    def _recalculate(self):
        """محاسبه مجدد"""
        
        # ============================================================
        # ✅ چک: Pressure Drop > Steam Pressure (با پیام دقیق)
        # ============================================================
        if self.valve.ValveType == 'Steam':
            try:
                p1_bar = float(self.valve.SteamPressure or 0)
            except (ValueError, TypeError):
                p1_bar = 0.0
            
            try:
                dp_psi = float(self.valve.PressureDrop or 0)
            except (ValueError, TypeError):
                dp_psi = 0.0
            
            # ===== تبدیل =====
            dp_bar = dp_psi * PSI_TO_BAR
            dp_max_bar = p1_bar * 0.5
            dp_max_psi = dp_max_bar / PSI_TO_BAR if PSI_TO_BAR > 0 else 0
            
            # ===== چک خطا =====
            if p1_bar > 0 and dp_bar > dp_max_bar:
                self.valve.WarningSteam = (
                    f"❌ افت فشار ({dp_psi:.1f} psi = {dp_bar:.2f} bar) "
                    f"بیشتر از حد مجاز ({dp_max_psi:.1f} psi = {dp_max_bar:.2f} bar) است."
                    f"\n    راه‌حل: افت فشار را کم کنید یا فشار ورودی را بیشتر کنید."
                    f"\n    برای {p1_bar:.2f} bar، حداکثر {dp_max_psi:.1f} psi مجاز است."
                )
                self.valve.WarningGeneral = self.valve.WarningSteam
                self.valve.KvsCalc = 0
                self.valve.KvsSelected = 0
                self.valve.SteamDN = 0
                self.valve.SteamModel = ''
                self.valve.SteamActuator = ''
                
                if hasattr(self, 'warning_label'):
                    self.warning_label.config(text=self.valve.WarningSteam)
                    try:
                        self.warning_frame.pack(
                            fill=tk.X, padx=sp('md'), pady=sp('md')
                        )
                    except Exception:
                        pass
                
                self._refresh_readonly_fields()
                self._refresh_steam_info_card()
                return
            
            # ===== هشدار نزدیک به مرز (85%+) =====
            elif p1_bar > 0 and dp_bar > dp_max_bar * 0.85:
                self.valve.WarningSteam = (
                    f"⚠️ افت فشار ({dp_psi:.1f} psi) نزدیک به حد مجاز "
                    f"({dp_max_psi:.1f} psi) است. Kv واقعی ممکن است متفاوت باشد."
                )
        
        # ============================================================
        # محاسبه
        # ============================================================
        try:
            enrich_valve(self.valve)
            self._update_pressure_drop_hint()
        except Exception as e:
            import traceback
            traceback.print_exc()
            return
        
        # ============================================================
        # به‌روزرسانی UI
        # ============================================================
        self._refresh_readonly_fields()
        self._refresh_warning_panel()
        self._refresh_steam_info_card()
    
    def _refresh_readonly_fields(self):
        """
        به‌روزرسانی مقادیر فیلدهای readonly
        شامل فیلدهای تبدیل واحد بخار (kg/h, lb/h, ton/h)
        """
        # ============================================================
        # ۱. به‌روزرسانی فیلدهای معمولی
        # ============================================================
        for key, widget in self.entries.items():
            # پیدا کردن field_type
            field_type = None
            readonly = False
            
            for field_def in VALVE_FIELD_DEFINITIONS:
                if field_def[0] == key:
                    field_type = field_def[2]
                    readonly = field_def[4]
                    break
            
            if not readonly:
                continue
            
            # ============================================================
            # به‌روزرسانی Label
            # ============================================================
            if isinstance(widget, tk.Label):
                new_value = self._get_current_value(key)
                display = self._format_display_value(key, new_value)
                try:
                    widget.configure(text=display)
                except Exception:
                    pass
        
        # ============================================================
        # ۲. ✅ به‌روزرسانی فیلدهای تبدیل دبی بخار
        # ============================================================
        self._refresh_steam_conversions()

    def _update_pressure_drop_hint(self):
        """به‌روزرسانی راهنمای Pressure Drop"""
        if self.pressure_drop_hint is None:
            return
        
        if self.valve.ValveType != 'Steam':
            try:
                self.pressure_drop_hint.config(text="")
            except Exception:
                pass
            return
        
        try:
            p1_bar = float(self.valve.SteamPressure or 0)
        except (ValueError, TypeError):
            p1_bar = 0.0
        
        if p1_bar <= 0:
            try:
                self.pressure_drop_hint.config(
                    text="← فشار ورودی را وارد کنید",
                    fg=get_color('text_muted'),
                )
            except Exception:
                pass
            return
        
        # حداکثر = نصف فشار ورودی
        dp_max_psi = (p1_bar * 0.5) / PSI_TO_BAR
        
        try:
            self.pressure_drop_hint.config(
                text=f"← حداکثر: {dp_max_psi:.1f} psi",
                fg=get_color('text_muted'),
            )
        except Exception:
            pass

    def _refresh_steam_conversions(self):
        """
        به‌روزرسانی فیلدهای تبدیل دبی بخار:
            - Flow (kg/h)
            - Flow (lb/h)
            - Flow (ton/h)
        """
        # ============================================================
        # چک: آیا ValveType == Steam؟
        # ============================================================
        vtype = self.valve.ValveType or ''
        
        if vtype != 'Steam':
            # پاک کردن فیلدها اگر Steam نیست
            for key in ('SteamFlowKgH', 'SteamFlowLbH', 'SteamFlowTonH'):
                widget = self.entries.get(key)
                if widget and isinstance(widget, tk.Label):
                    try:
                        widget.configure(text='—')
                    except Exception:
                        pass
            return
        
        # ============================================================
        # گرفتن تبدیل‌ها از valve
        # ============================================================
        conversions = self.valve.__dict__.get('_steam_conversions', None)
        
        # ============================================================
        # اگر تبدیل‌ها موجود نیست، خودمان محاسبه می‌کنیم
        # ============================================================
        if not conversions:
            try:
                from core.valve_constants import LB_TO_KG, KG_TO_LB, TON_TO_KG
                
                # ===== دبی اصلی =====
                try:
                    flow_value = float(self.valve.Flow or 0)
                except (ValueError, TypeError):
                    flow_value = 0.0
                
                # ===== تبدیل به kg/h =====
                unit = self.valve.Unit or ''
                
                if unit == 'Kg/h':
                    kg_h = flow_value
                elif unit == 'lb/h':
                    kg_h = flow_value * LB_TO_KG
                elif unit == 'ton/h':
                    kg_h = flow_value * TON_TO_KG
                else:
                    # واحدهای حجمی → تخمینی
                    kg_h = 0.0
                
                conversions = {
                    'kg_h': kg_h,
                    'lb_h': kg_h * KG_TO_LB,
                    'ton_h': kg_h / 1000.0,
                }
                
                # ذخیره برای استفاده بعدی
                self.valve.__dict__['_steam_conversions'] = conversions
            
            except Exception as e:
                # در صورت خطا، صفر نمایش بده
                conversions = {'kg_h': 0.0, 'lb_h': 0.0, 'ton_h': 0.0}
        
        # ============================================================
        # به‌روزرسانی فیلدها
        # ============================================================
        
        # ===== Flow (kg/h) =====
        widget = self.entries.get('SteamFlowKgH')
        if widget and isinstance(widget, tk.Label):
            try:
                val = conversions.get('kg_h', 0.0)
                widget.configure(text=f"{val:.2f}")
            except Exception:
                pass
        
        # ===== Flow (lb/h) =====
        widget = self.entries.get('SteamFlowLbH')
        if widget and isinstance(widget, tk.Label):
            try:
                val = conversions.get('lb_h', 0.0)
                widget.configure(text=f"{val:.2f}")
            except Exception:
                pass
        
        # ===== Flow (ton/h) =====
        widget = self.entries.get('SteamFlowTonH')
        if widget and isinstance(widget, tk.Label):
            try:
                val = conversions.get('ton_h', 0.0)
                # ton/h → 4 رقم اعشار
                widget.configure(text=f"{val:.4f}")
            except Exception:
                pass
    
    def _refresh_warning_panel(self):
        """به‌روزرسانی پنل هشدار"""
        warning_text = self.valve.WarningGeneral or ''
        
        # اگر تغییر نکرده، برنگرد
        if warning_text == self._last_warning:
            return
        
        self._last_warning = warning_text
        
        if warning_text:
            self.warning_label.configure(text=f"⚠️  {warning_text}")
            
            # نمایش پنل
            try:
                self.warning_frame.pack(
                    fill=tk.X, padx=sp('md'), pady=sp('md')
                )
            except:
                pass
        else:
            # پنهان کردن پنل
            try:
                self.warning_frame.pack_forget()
            except:
                pass
    
    # ================================================================
    # OK / SAVE
    # ================================================================
    
    def on_ok(self):
        """ذخیره — با Auto-Numbering برای Quantity > 1"""
        try:
            # ============================================================
            # ۱. خواندن مقادیر از UI
            # ============================================================
            self._read_all_fields_to_valve()
            self._clear_unrelated_fields()
            
            # ============================================================
            # ۲. محاسبه
            # ============================================================
            enrich_valve(self.valve)
            self._clear_unrelated_fields()
            
            # ============================================================
            # ۳. اعتبارسنجی
            # ============================================================
            if not self.valve.is_valid():
                ToastManager.error(
                    "لطفاً حداقل 'Equipment' و 'Valve Type' را وارد کنید."
                )
                return
            
            # ============================================================
            # ۴. ذخیره
            # ============================================================
            if self.is_new:
                if not self.section:
                    ToastManager.error("Section یافت نشد!")
                    return
                
                self.app._save_state()
                
                # ============================================================
                # ✅ Auto-Numbering
                # ============================================================
                quantity = int(self.valve.Quantity or 1)
                equipment = (self.valve.Equipment or '').strip()
                
                if quantity > 1:
                    # ============================================================
                    # ۱. استخراج base_name
                    # مثال: "va-5" → "va"
                    # مثال: "va5" → "va"
                    # مثال: "va" → "va"
                    # ============================================================
                    import re
                    
                    # حذف شماره انتهایی (با یا بدون جداکننده - _ space)
                    base_name = re.sub(r'[-_\s]?\d+$', '', equipment).strip()
                    
                    if not base_name:
                        base_name = equipment
                    
                    # ============================================================
                    # ۲. پیدا کردن آخرین شماره موجود در Section
                    # الگو: "base-N" یا "baseN" یا "base_N" یا "base N"
                    # ============================================================
                    max_num = 0
                    pattern = re.compile(
                        rf'^{re.escape(base_name)}[-_\s]?(\d+)$'
                    )
                    
                    for v in self.section.valves:
                        existing_name = (v.Equipment or '').strip()
                        match = pattern.match(existing_name)
                        if match:
                            try:
                                num = int(match.group(1))
                                if num > max_num:
                                    max_num = num
                            except ValueError:
                                pass
                    
                    # ============================================================
                    # ۳. ساخت N شیر جدید
                    # فرمت: "va-1", "va-2", ...
                    # ============================================================
                    created_names = []
                    for i in range(1, quantity + 1):
                        new_num = max_num + i
                        new_valve = self.valve.copy()
                        new_valve.Equipment = f"{base_name}-{new_num}"
                        new_valve.Quantity = 1   # هر کدام یک عدد
                        self.section.valves.append(new_valve)
                        created_names.append(new_valve.Equipment)
                    
                    self.app._save_project()
                    
                    # ============================================================
                    # ۴. پیام موفقیت
                    # ============================================================
                    if len(created_names) <= 5:
                        names_str = ', '.join(created_names)
                    else:
                        names_str = (
                            ', '.join(created_names[:5])
                            + f" ... (+{len(created_names) - 5} more)"
                        )
                    
                    ToastManager.success(
                        f"{quantity} شیر اضافه شد:\n{names_str}"
                    )
                
                else:
                    # ============================================================
                    # Quantity = 1 → فقط یک شیر
                    # ============================================================
                    self.section.valves.append(self.valve)
                    self.app._save_project()
                    
                    ToastManager.success(
                        f"شیر '{self.valve.Equipment}' اضافه شد!"
                    )
            
            else:
                # ============================================================
                # ویرایش (بدون Auto-Numbering)
                # ============================================================
                self.app._save_state()
                self.app._save_project()
                ToastManager.success(
                    f"شیر '{self.valve.Equipment}' به‌روز شد!"
                )
            
            # ============================================================
            # ۵. Refresh + Close
            # ============================================================
            self.app._refresh_ui()
            self.result = True
            self._close_dialog()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            ToastManager.error(f"خطا در ذخیره: {str(e)}")

    def _refresh_steam_info_card(self):
        """به‌روزرسانی کارت اطلاعات Steam"""
        
        # ============================================================
        # چک: آیا ValveType == Steam؟
        # ============================================================
        vtype = self.valve.ValveType or ''
        
        if vtype != 'Steam':
            # پنهان کردن کارت
            try:
                self.steam_info_frame.pack_forget()
            except Exception:
                pass
            return
        
        # ============================================================
        # نمایش کارت
        # ============================================================
        try:
            self.steam_info_frame.pack(
                fill=tk.X, padx=sp('md'), pady=sp('md')
            )
        except Exception:
            pass
        
        # ============================================================
        # گرفتن اطلاعات از valve.__dict__
        # ============================================================
        steam_info = self.valve.__dict__.get('_steam_info', None)
        choked_info = self.valve.__dict__.get('_choked_info', None)
        
        # اگر اطلاعات نیست، محاسبه کن
        if not steam_info:
            try:
                from core.valve_calculator import get_steam_info
                steam_info = get_steam_info(self.valve.SteamPressure)
            except Exception:
                steam_info = {}
        
        # ============================================================
        # حالت نامعتبر
        # ============================================================
        if not steam_info or steam_info.get('temp_saturation', 0) <= 0:
            self.steam_temp_label.config(text="🌡️ دمای اشباع:  —")
            self.steam_cat_label.config(
                text="📊 دسته:  —",
                fg=get_color('text_muted'),
            )
            self.steam_apps_label.config(text="🏭 کاربردها:  —")
            self.steam_rho_label.config(text="ℹ️ چگالی:  —")
            self.steam_warnings_label.config(text="")
            return
        
        # ============================================================
        # دما
        # ============================================================
        temp = steam_info.get('temp_saturation', 0)
        self.steam_temp_label.config(
            text=f"🌡️ دمای اشباع:  {temp:.1f}°C"
        )
        
        # ============================================================
        # دسته‌بندی
        # ============================================================
        category = steam_info.get('category')
        
        if category:
            cat_text = (
                f"📊 دسته:  {category['icon']} "
                f"{category['name_fa']} ({category['code']})"
            )
            self.steam_cat_label.config(
                text=cat_text,
                fg=category.get('color', get_color('text_secondary')),
            )
        else:
            self.steam_cat_label.config(
                text="📊 دسته:  —",
                fg=get_color('text_muted'),
            )
        
        # ============================================================
        # کاربردها
        # ============================================================
        applications = steam_info.get('applications', [])
        
        if applications:
            apps_text = ' • '.join(
                f"{a['icon']} {a['name_fa']}"
                for a in applications[:3]
            )
            if len(applications) > 3:
                apps_text += f"  ... +{len(applications) - 3}"
            
            self.steam_apps_label.config(
                text=f"🏭 کاربردها:  {apps_text}",
                fg=get_color('text_secondary'),
            )
        else:
            self.steam_apps_label.config(
                text="🏭 کاربردها:  (در محدوده استاندارد نیست)",
                fg=get_color('text_muted'),
            )
        
        # ============================================================
        # چگالی
        # ============================================================
        rho = steam_info.get('rho', 0)
        
        if rho > 0:
            self.steam_rho_label.config(
                text=f"ℹ️ چگالی بخار:  {rho:.3f} kg/m³"
            )
        else:
            self.steam_rho_label.config(text="ℹ️ چگالی بخار:  —")
        
        # ============================================================
        # هشدارها
        # ============================================================
        warnings = list(steam_info.get('warnings', []))
        
        # هشدار Choked Flow
        if choked_info and choked_info.get('is_choked'):
            dp_max = choked_info.get('dp_max', 0)
            warnings.insert(0,
                f"🔴 جریان خفه (Choked Flow): ΔP بیشتر از {dp_max:.2f} bar"
            )

        # ============================================================
        # ✅ جدید: هشدار محدودیت VFS 2
        # ============================================================
        vfs2_info = self.valve.__dict__.get('_vfs2_info', None)
        if vfs2_info:
            # محدودیت فیزیکی ΔP
            try:
                dp_psi = float(self.valve.PressureDrop or 0)
                dp_bar = dp_psi * PSI_TO_BAR
                dp_max = vfs2_info.get('steam_dp_max_physical', 6.0)
                
                if dp_bar > dp_max:
                    warnings.append(
                        f"❌ افت فشار ({dp_bar:.2f} bar) بیشتر از حد فیزیکی "
                        f"VFS 2 ({dp_max} bar) است."
                    )
            except Exception:
                pass
        
        if warnings:
            warnings_text = "⚠️ هشدارها:\n" + "\n".join(
                f"    • {w}" for w in warnings
            )
            self.steam_warnings_label.config(
                text=warnings_text,
                fg=get_color('danger'),
            )
        else:
            self.steam_warnings_label.config(text="")


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['ValveDialog']