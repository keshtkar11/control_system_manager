# gui/valves/valve_table.py
"""
جدول شیرها - Valve Table
با ستون‌های شرطی بر اساس نوع شیر
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional

from gui.theme import (
    get_color, font, sp, pad, h, ico,
)
from gui.components import (
    SearchInput, Separator, IconButton,
    PrimaryButton, SecondaryButton, DangerButton,
)

from core.valve_constants import (
    VALVE_COLUMNS,
    VALVE_TYPE_FIELDS,
    VALVE_TYPES,
)


class ValveTable(tk.Frame):
    """
    جدول شیرها با ستون‌های شرطی
    
    - ستون‌های پایه همیشه نمایش
    - ستون‌های PICV/3Way/Steam بر اساس نوع شیر
    - دکمه‌های Add/Edit/Delete/Move
    """
    
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, bg=get_color('bg_app'), **kwargs)
        
        self.app = app
        self._all_data: List = []         # همه شیرهای Section فعلی
        self._filtered_data: List = []    # فیلترشده
        self._current_filter_type = "All"     # فیلتر نوع شیر
        self._current_filter_circuit = "All"  # فیلتر مدار
        
        # ===== دکمه‌ها =====
        self.add_btn = None
        self.edit_btn = None
        self.delete_btn = None
        self.move_up_btn = None
        self.move_down_btn = None
        
        # ===== ستون‌های فعال فعلی =====
        self._active_columns = []
        
        self._build_ui()
    
    # ================================================================
    # BUILD UI
    # ================================================================
    
    def _build_ui(self):
        """ساخت UI"""
        # ===== Card =====
        card = tk.Frame(
            self,
            bg=get_color('bg_surface'),
            highlightthickness=1,
            highlightbackground=get_color('border_default'),
        )
        card.pack(fill=tk.BOTH, expand=True)
        
        # ============================================================
        # HEADER
        # ============================================================
        header = tk.Frame(card, bg=get_color('bg_surface_alt'),
                        height=h('table_header'))
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"  {ico('valve')}  Valve List",
            font=font('h3'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_primary'),
        ).pack(side=tk.LEFT, padx=sp('md'))
        
        # Counter
        self.counter_label = tk.Label(
            header,
            text="0 valves",
            font=font('small'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_secondary'),
        )
        self.counter_label.pack(side=tk.RIGHT, padx=sp('md'))
        
        # ============================================================
        # TOOLBAR
        # ============================================================
        toolbar = tk.Frame(card, bg=get_color('bg_surface'))
        toolbar.pack(fill=tk.X, padx=sp('md'), pady=sp('sm'))
        
        # ===== Search =====
        self.search = SearchInput(
            toolbar,
            placeholder="Search valves...",
            on_change=self._on_search,
        )
        self.search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, sp('sm')))
        
        # ===== Filter by Valve Type =====
        self.type_filter_var = tk.StringVar(value="All")
        type_filter = ttk.Combobox(
            toolbar,
            textvariable=self.type_filter_var,
            values=["All"] + VALVE_TYPES,
            state='readonly',
            width=12,
            font=font('input'),
        )
        type_filter.pack(side=tk.LEFT, padx=(0, sp('xs')))
        type_filter.bind('<<ComboboxSelected>>', lambda e: self._on_filter())
        
        # ===== Filter by Circuit =====
        self.circuit_filter_var = tk.StringVar(value="All")
        circuit_filter = ttk.Combobox(
            toolbar,
            textvariable=self.circuit_filter_var,
            values=["All", "گرمایش", "سرمایش", "بخار", "غیره"],
            state='readonly',
            width=10,
            font=font('input'),
        )
        circuit_filter.pack(side=tk.LEFT, padx=(0, sp('sm')))
        circuit_filter.bind('<<ComboboxSelected>>', lambda e: self._on_filter())
        
        # ============================================================
        # DEVICE OPERATIONS (Add/Edit/Delete/Export)
        # ============================================================
        tk.Frame(toolbar, bg=get_color('border_default'), width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs')
        )
        
        self.add_btn = PrimaryButton(
            toolbar,
            text="Add",
            icon='add',
            command=self._on_add,
            tooltip="Add Valve",
        )
        self.add_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        self.edit_btn = SecondaryButton(
            toolbar,
            text="Edit",
            icon='edit',
            command=self._on_edit,
            tooltip="Edit Valve",
        )
        self.edit_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        self.delete_btn = DangerButton(
            toolbar,
            text="Delete",
            icon='delete',
            command=self._on_delete,
            tooltip="Delete Valve",
        )
        self.delete_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ============================================================
        # ✅ Export Excel
        # ============================================================
        self.export_btn = SecondaryButton(
            toolbar,
            text="Export",
            icon='file_excel',
            command=self._on_export,
            tooltip="Export Valves to Excel",
        )
        self.export_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ============================================================
        # ✅ COPY / PASTE (جدید)
        # ============================================================
        tk.Frame(toolbar, bg=get_color('border_default'), width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs')
        )
        
        self.copy_btn = IconButton(
            toolbar,
            icon='copy',
            command=self._on_copy,
            tooltip="Copy Valves (Ctrl+Shift+C)",
            size=32,
        )
        self.copy_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        self.paste_btn = IconButton(
            toolbar,
            icon='paste',
            command=self._on_paste,
            tooltip="Paste Valves (Ctrl+Shift+V)",
            size=32,
        )
        self.paste_btn.pack(side=tk.LEFT, padx=sp('xxs'))

        # ============================================================
        # ✅ FIX DUPLICATES (جدید)
        # ============================================================
        tk.Frame(toolbar, bg=get_color('border_default'), width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs')
        )
        
        self.fix_duplicates_btn = IconButton(
            toolbar,
            icon='search',
            command=self._on_fix_duplicates,
            tooltip="Fix Duplicate Valve Names",
            size=32,
        )
        self.fix_duplicates_btn.pack(side=tk.LEFT, padx=sp('xxs'))

        # ============================================================
        # MOVE BUTTONS
        # ============================================================
        tk.Frame(toolbar, bg=get_color('border_default'), width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs')
        )
        
        self.move_up_btn = IconButton(
            toolbar,
            icon='up',
            command=self._move_up,
            tooltip="Move Up",
            size=32,
        )
        self.move_up_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        self.move_down_btn = IconButton(
            toolbar,
            icon='down',
            command=self._move_down,
            tooltip="Move Down",
            size=32,
        )
        self.move_down_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ============================================================
        # TABLE CONTAINER
        # ============================================================
        table_container = tk.Frame(card, bg=get_color('bg_surface'))
        table_container.pack(fill=tk.BOTH, expand=True,
                            padx=sp('md'), pady=(0, sp('md')))
        
        # ===== Treeview =====
        self.tree = ttk.Treeview(
            table_container,
            columns=(),
            show='headings',
            selectmode='extended',
        )
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_container, orient='vertical',
                           command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient='horizontal',
                           command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # ===== رویدادها =====
        self.tree.bind('<Double-1>', lambda e: self._on_edit())
        self.tree.bind('<Delete>', lambda e: self._on_delete())
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Control-Up>', lambda e: self._move_up())
        self.tree.bind('<Control-Down>', lambda e: self._move_down())
        
        # ============================================================
        # ✅✅✅ این خط حیاتی است! ✅✅✅
        # ============================================================
        self._rebuild_columns()
        
        # ===== وضعیت اولیه =====
        self._update_buttons_state(has_selection=False)


    # ================================================================
    # ستون‌های ثابت (فقط ورودی کاربر)
    # ================================================================
    
    def _get_visible_columns(self) -> List[Dict]:
        """
        دریافت ستون‌های قابل نمایش — فقط فیلدهای ورودی کاربر
        
        ستون‌های محاسبه‌شده در گزارش اکسل نمایش داده می‌شوند،
        نه در جدول UI.
        """
        # ============================================================
        # ۸ ستون پایه (ورودی کاربر)
        # ============================================================
        UI_COLUMN_KEYS = [
            'no',              # ردیف
            'equipment',       # مشخصات تجهیز
            'quantity',        # تعداد
            'circuit',         # مدار
            'flow',            # دبی
            'pressure_drop',   # افت فشار
            'unit',            # واحد
            'valve_type',      # نوع شیر
        ]
        
        # ============================================================
        # فیلتر از VALVE_COLUMNS
        # ============================================================
        return [
            col for col in VALVE_COLUMNS
            if col[1] in UI_COLUMN_KEYS
        ]
    
    def _rebuild_columns(self):
        """
        تنظیم ستون‌های Treeview — فقط یکبار در شروع
        ستون‌ها ثابت هستند (۸ ستون ورودی کاربر)
        """
        # ===== اگر قبلاً ساخته شده، برنگرد =====
        if self._active_columns:
            return
        
        # ===== دریافت ستون‌ها =====
        visible = self._get_visible_columns()
        new_keys = [c[1] for c in visible]
        self._active_columns = new_keys
        
        # ===== تنظیم ستون‌های جدید =====
        self.tree.configure(columns=new_keys)
        
        # ===== تنظیم heading و width =====
        for col_def in visible:
            _, key, label_en, label_fa, group = col_def
            width = self._get_column_width(key, group)
            anchor = self._get_column_anchor(key, group)
            
            self.tree.heading(key, text=label_en)
            self.tree.column(key, width=width, anchor=anchor, minwidth=40)

    
    @staticmethod
    def _get_column_width(key: str, group: str) -> int:
        """عرض پیشنهادی برای هر ستون"""
        widths = {
            'no': 50,
            'equipment': 180,
            'quantity': 60,
            'circuit': 90,
            'flow': 80,
            'pressure_drop': 100,
            'unit': 70,
            'valve_type': 100,
            'max_flow_lph': 110,
            'picv_model': 120,
            'picv_max_flow': 110,
            'picv_percent': 90,
            'picv_actuator': 150,
            'picv_signal': 130,
            'kv_calc': 100,
            'kv_selected': 100,
            '3way_dn': 80,
            '3way_model': 110,
            '3way_actuator': 130,
            '3way_signal': 130,
            'steam_pressure': 110,
            'kvs_calc': 100,
            'kvs_selected': 100,
            'steam_dn': 80,
            'steam_model': 110,
            'steam_actuator': 130,
            'steam_signal': 130,
            'warning_3way': 150,
            'warning_steam': 150,
            'warning_general': 200,
        }
        return widths.get(key, 100)
    
    @staticmethod
    def _get_column_anchor(key: str, group: str) -> str:
        """تراز ستون"""
        left_cols = ['equipment', 'circuit', 'picv_model', 'picv_actuator',
                     '3way_model', '3way_actuator', 'steam_model',
                     'steam_actuator', 'warning_3way', 'warning_steam',
                     'warning_general']
        if key in left_cols:
            return 'w'
        return 'center'
    
    # ================================================================
    # DATA MANAGEMENT
    # ================================================================
    
    def load_data(self, valves: List):
        """بارگذاری داده‌ها"""
        
        
        self._all_data = list(valves)
        
       
        
        self._apply_filters()
        
        
    
    def _apply_filters(self):
        """اعمال فیلتر + جستجو"""
        filtered = list(self._all_data)
        
        # ============================================================
        # ۱. فیلتر نوع شیر
        # ============================================================
        filter_type = self.type_filter_var.get()
        if filter_type != "All":
            filtered = [v for v in filtered if v.ValveType == filter_type]
        
        # ============================================================
        # ۲. فیلتر مدار
        # ============================================================
        filter_circuit = self.circuit_filter_var.get()
        if filter_circuit != "All":
            filtered = [v for v in filtered if v.Circuit == filter_circuit]
        
        # ============================================================
        # ۳. جستجو
        # ============================================================
        query = ''
        try:
            query = self.search.get()
        except:
            pass
        
        if query and query.strip():
            q = query.lower().strip()
            filtered_search = []
            for valve in filtered:
                # فیلدهای قابل جستجو
                fields = [
                    valve.Equipment or '',
                    valve.Circuit or '',
                    valve.ValveType or '',
                    valve.PICVModel or '',
                    getattr(valve, '3WayModel', '') or '',
                    valve.SteamModel or '',
                ]
                combined = ' '.join(fields).lower()
                if q in combined:
                    filtered_search.append(valve)
            filtered = filtered_search
        
        # ============================================================
        # ۴. بازسازی ستون‌ها + نمایش
        # ============================================================
        
        self._populate_table(filtered)
    
    def _populate_table(self, valves: List):
        """
        پر کردن جدول با داده‌های فیلترشده
        
        Args:
            valves: لیست شیرها
        """
       
        # ============================================================
        # ۱. پاک کردن ردیف‌های قبلی
        # ============================================================
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # ============================================================
        # ۲. ذخیره داده فعلی
        # ============================================================
        self._filtered_data = valves
        
        # ============================================================
        # ۳. تنظیم رنگ‌ها (یکبار، قبل از درج)
        # ============================================================
        self.tree.tag_configure(
            'normal',
            foreground=get_color('text_primary'),
        )
        self.tree.tag_configure(
            'warning',
            foreground=get_color('danger'),
        )
        
        # ============================================================
        # ۴. افزودن ردیف‌ها
        # ============================================================
        for i, valve in enumerate(valves, 1):
            # مقادیر ردیف
            values = self._build_row_values(valve, i)
            
            # تشخیص رنگ بر اساس هشدار (با احتیاط)
            tag = 'normal'
            try:
                if hasattr(valve, 'has_warning') and valve.has_warning():
                    tag = 'warning'
            except Exception:
                pass
            
            self.tree.insert('', 'end', values=values, tags=(tag,))
        
        # ============================================================
        # ۵. به‌روزرسانی شمارنده
        # ============================================================
        total = len(self._all_data)
        shown = len(valves)
        
        if shown == total:
            self.counter_label.configure(text=f"{total} valves")
        else:
            self.counter_label.configure(text=f"{shown} of {total} valves")
        
        # ============================================================
        # ۶. به‌روزرسانی وضعیت دکمه‌ها
        # ============================================================
        self._update_buttons_state(has_selection=False)
        self._update_move_buttons()
    
    def _build_row_values(self, valve, index: int) -> tuple:
        """ساخت مقادیر ردیف بر اساس ستون‌های فعال"""
        values = []
        
        for key in self._active_columns:
            value = self._get_column_value(valve, key, index)
            values.append(value)
        
        return tuple(values)
    
    def _get_column_value(self, valve, key: str, index: int):
        """دریافت مقدار یک ستون خاص — فقط فیلدهای ورودی کاربر"""
        if key == 'no':
            return index
        elif key == 'equipment':
            return valve.Equipment or ''
        elif key == 'quantity':
            return valve.Quantity
        elif key == 'circuit':
            return valve.Circuit or ''
        elif key == 'flow':
            return valve.Flow
        elif key == 'pressure_drop':
            return valve.PressureDrop
        elif key == 'unit':
            return valve.Unit or ''
        elif key == 'valve_type':
            return valve.ValveType or ''
        
        return ''
    
    def get_selected_indices(self) -> List[int]:
        """دریافت ایندکس‌های انتخاب‌شده در داده اصلی"""
        indices = []
        
        for item in self.tree.selection():
            values = self.tree.item(item, 'values')
            if not values:
                continue
            
            # ===== ستون اول = شماره ردیف =====
            try:
                row_num = int(values[0])
                # تبدیل به ایندکس در _all_data
                if 0 < row_num <= len(self._filtered_data):
                    valve = self._filtered_data[row_num - 1]
                    try:
                        real_index = self._all_data.index(valve)
                        indices.append(real_index)
                    except ValueError:
                        indices.append(row_num - 1)
            except (ValueError, TypeError):
                continue
        
        return indices
    
    # ================================================================
    # ACTIONS
    # ================================================================
    
    def _on_add(self):
        """افزودن شیر"""
        if self.app and hasattr(self.app, '_add_valve'):
            self.app._add_valve()
    
    def _on_edit(self):
        """ویرایش شیر"""
        if self.app and hasattr(self.app, '_edit_valve'):
            self.app._edit_valve()
    
    def _on_delete(self):
        """حذف شیر"""
        if self.app and hasattr(self.app, '_delete_valve'):
            self.app._delete_valve()

    def _on_export(self):
        """Export Valves به Excel"""
        if self.app and hasattr(self.app, '_export_valves_excel'):
            self.app._export_valves_excel()
    
    def _move_up(self):
        """جابجایی بالا"""
        if self.app and hasattr(self.app, '_move_valve_up'):
            self.app._move_valve_up()
    
    def _move_down(self):
        """جابجایی پایین"""
        if self.app and hasattr(self.app, '_move_valve_down'):
            self.app._move_valve_down()

    def _on_copy(self):
        """کپی شیرها"""
        if self.app and hasattr(self.app, '_copy_valve'):
            self.app._copy_valve()
    
    def _on_paste(self):
        """چسباندن شیرها"""
        if self.app and hasattr(self.app, '_paste_valve'):
            self.app._paste_valve()

    def _on_fix_duplicates(self):
        """اصلاح نام‌های تکراری"""
        if self.app and hasattr(self.app, '_fix_valve_duplicates'):
            self.app._fix_valve_duplicates()
    
    # ================================================================
    # EVENTS
    # ================================================================
    
    def _on_search(self, query: str):
        """جستجو"""
        self._apply_filters()
    
    def _on_filter(self):
        """فیلتر"""
        self._apply_filters()
    
    def _on_select(self, event=None):
        """انتخاب"""
        has_selection = len(self.tree.selection()) > 0
        self._update_buttons_state(has_selection=has_selection)
        self._update_move_buttons()
    
    # ================================================================
    # BUTTONS STATE
    # ================================================================
    
    def _update_buttons_state(self, has_selection: bool):
        """به‌روزرسانی وضعیت دکمه‌ها"""
        if self.edit_btn:
            self._set_button_enabled(self.edit_btn, has_selection)
        
        if self.delete_btn:
            self._set_button_enabled(self.delete_btn, has_selection)
        
        if self.add_btn:
            self._set_button_enabled(self.add_btn, True)
    
    def _set_button_enabled(self, button, enabled: bool):
        """تنظیم وضعیت دکمه"""
        try:
            if hasattr(button, 'set_enabled'):
                button.set_enabled(enabled)
            else:
                state = 'normal' if enabled else 'disabled'
                button.configure(state=state)
        except Exception:
            pass
    
    def _update_move_buttons(self):
        """به‌روزرسانی دکمه‌های جابجایی"""
        if not self.move_up_btn or not self.move_down_btn:
            return
        
        selection = self.tree.selection()
        
        if not selection:
            self._set_button_enabled(self.move_up_btn, False)
            self._set_button_enabled(self.move_down_btn, False)
            return
        
        first_idx = self.tree.index(selection[0])
        total = len(self.tree.get_children())
        
        self._set_button_enabled(self.move_up_btn, first_idx > 0)
        self._set_button_enabled(self.move_down_btn, first_idx < total - 1)


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['ValveTable']