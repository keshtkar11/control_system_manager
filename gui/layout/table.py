# gui/layout/table.py
"""
جدول سفارشی - Device Table
با Toolbar داخلی شامل: Search, Filter, Add/Edit/Delete, Move Up/Down, Fix Names
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Dict, Any, Optional

from gui.theme import (
    get_color, font, sp, pad, h, ico,
)
from gui.components import (
    SearchInput, Separator, IconButton,
    PrimaryButton, SecondaryButton, DangerButton,
)


class DeviceTable(tk.Frame):
    """
    جدول دستگاه‌ها با toolbar داخلی
    شامل: Search, Filter, Add/Edit/Delete, Move Up/Down, Fix Names
    """
    
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, bg=get_color('bg_app'), **kwargs)
        
        self.app = app
        self._columns = []
        self._data = []              # داده فعلی (فیلترشده)
        self._all_data = []          # داده اصلی (بدون فیلتر)
        self._current_filter = 'All'
        
        # ===== دکمه‌ها برای مدیریت وضعیت =====
        self.add_btn = None
        self.edit_btn = None
        self.delete_btn = None
        self.move_up_btn = None
        self.move_down_btn = None
        self.fix_names_btn = None
        
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
        
        # ===== Header =====
        header = tk.Frame(card, bg=get_color('bg_surface_alt'), height=h('table_header'))
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Title
        tk.Label(
            header,
            text=f"  {ico('table')}  Device List",
            font=font('h3'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_primary'),
        ).pack(side=tk.LEFT, padx=sp('md'))
        
        # Counter
        self.counter_label = tk.Label(
            header,
            text="0 devices",
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
            placeholder="Search devices...",
            on_change=self._on_search,
        )
        self.search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, sp('sm')))
        
        # ===== Filter Combo =====
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(
            toolbar,
            textvariable=self.filter_var,
            values=["All", "Active", "Inactive"],
            state='readonly',
            width=10,
            font=font('input'),
        )
        filter_combo.pack(side=tk.LEFT, padx=(0, sp('sm')))
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self._on_filter())
        
        # ============================================================
        # ✅ DEVICE OPERATIONS (منتقل‌شده از Toolbar اصلی)
        # ============================================================
        
        # Separator
        tk.Frame(
            toolbar, 
            bg=get_color('border_default'), 
            width=1
        ).pack(side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs'))
        
        # ➕ Add
        self.add_btn = PrimaryButton(
            toolbar,
            text="Add",
            icon='add',
            command=self._on_add,
            tooltip="Add Device (Ctrl+Shift+A)",
        )
        self.add_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ✏️ Edit
        self.edit_btn = SecondaryButton(
            toolbar,
            text="Edit",
            icon='edit',
            command=self._on_edit,
            tooltip="Edit Device (Ctrl+E)",
        )
        self.edit_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # 🗑️ Delete
        self.delete_btn = DangerButton(
            toolbar,
            text="Delete",
            icon='delete',
            command=self._on_delete,
            tooltip="Delete Device (Delete)",
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
            tooltip="Export Devices to Excel",
        )
        self.export_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ============================================================
        # ✅ COPY / PASTE (جدید — منتقل‌شده از Toolbar اصلی)
        # ============================================================
        tk.Frame(toolbar, bg=get_color('border_default'), width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs')
        )
        
        self.copy_btn = IconButton(
            toolbar,
            icon='copy',
            command=self._on_copy,
            tooltip="Copy Devices (Ctrl+C)",
            size=32,
        )
        self.copy_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        self.paste_btn = IconButton(
            toolbar,
            icon='paste',
            command=self._on_paste,
            tooltip="Paste Devices (Ctrl+V)",
            size=32,
        )
        self.paste_btn.pack(side=tk.LEFT, padx=sp('xxs'))
    
                
        # ============================================================
        # ✅ MOVE BUTTONS
        # ============================================================
        
        # Separator
        tk.Frame(
            toolbar, 
            bg=get_color('border_default'), 
            width=1
        ).pack(side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs'))
        
        # ⬆️ Move Up
        self.move_up_btn = IconButton(
            toolbar,
            icon='up',
            command=self._move_up,
            tooltip="Move Up (Ctrl+↑)",
            size=32,
        )
        self.move_up_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ⬇️ Move Down
        self.move_down_btn = IconButton(
            toolbar,
            icon='down',
            command=self._move_down,
            tooltip="Move Down (Ctrl+↓)",
            size=32,
        )
        self.move_down_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ============================================================
        # ✅ FIX NAMES BUTTON
        # ============================================================
        
        # Separator
        tk.Frame(
            toolbar, 
            bg=get_color('border_default'), 
            width=1
        ).pack(side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs'))
        
        # 🔍 Fix Names
        self.fix_names_btn = IconButton(
            toolbar,
            icon='search',
            command=self._fix_names,
            tooltip="Fix Duplicate Names",
            size=32,
        )
        self.fix_names_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ============================================================
        # TABLE CONTAINER
        # ============================================================
        table_container = tk.Frame(card, bg=get_color('bg_surface'))
        table_container.pack(fill=tk.BOTH, expand=True, padx=sp('md'), pady=(0, sp('md')))
        
        # ===== Treeview =====
        columns = ('no', 'name', 'description', 'di', 'do', 'ai', 'ao', 'total', 'info')
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show='headings',
            selectmode='extended',
        )
        
        # تنظیم ستون‌ها
        column_configs = {
            'no':          ('No',          50,  'center'),
            'name':        ('Name',        180, 'w'),
            'description': ('Description', 200, 'w'),
            'di':          ('DI',          50,  'center'),
            'do':          ('DO',          50,  'center'),
            'ai':          ('AI',          50,  'center'),
            'ao':          ('AO',          50,  'center'),
            'total':       ('Total',       60,  'center'),
            'info':        ('Device',      150, 'w'),
        }
        
        for col, (title, width, align) in column_configs.items():
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor=align, minwidth=40)
        
        # Scrollbars
        vsb = ttk.Scrollbar(
            table_container,
            orient='vertical',
            command=self.tree.yview,
        )
        hsb = ttk.Scrollbar(
            table_container,
            orient='horizontal',
            command=self.tree.xview,
        )
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Pack
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # ===== رویدادها =====
        self.tree.bind('<Double-1>', lambda e: self._on_edit())
        self.tree.bind('<Delete>', lambda e: self._on_delete())
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        
        # ===== کلیدهای میانبر =====
        self.tree.bind('<Control-Up>', lambda e: self._move_up())
        self.tree.bind('<Control-Down>', lambda e: self._move_down())
        self.tree.bind('<Alt-Up>', lambda e: self._move_up())
        self.tree.bind('<Alt-Down>', lambda e: self._move_down())
        
        # ===== وضعیت اولیه دکمه‌ها =====
        self._update_buttons_state(has_selection=False)
    
    # ================================================================
    # DATA MANAGEMENT
    # ================================================================
    
    def load_data(self, devices: List):
        """
        بارگذاری داده‌ها
        
        Args:
            devices: لیست دستگاه‌ها
        """
        # ============================================================
        # ✅ ذخیره داده اصلی (بدون فیلتر)
        # ============================================================
        self._all_data = list(devices)
        self._data = devices
        
        # ============================================================
        # ✅ اعمال فیلتر فعلی (اگر وجود دارد)
        # ============================================================
        current_query = ''
        if hasattr(self, 'search'):
            try:
                current_query = self.search.get()
            except Exception:
                pass
        
        self._apply_filters(search_query=current_query)
    
    def _apply_filters(self, search_query: str = ''):
        """
        اعمال فیلتر + جستجو
        
        Args:
            search_query: متن جستجو
        """
        # ============================================================
        # 1. شروع از داده اصلی
        # ============================================================
        filtered = list(self._all_data)
        
        # ============================================================
        # 2. اعمال فیلتر وضعیت (Active/Inactive)
        # ============================================================
        filter_value = self._current_filter
        
        if filter_value == 'Active':
            filtered = [d for d in filtered if d.get_total_io() > 0]
        elif filter_value == 'Inactive':
            filtered = [d for d in filtered if d.get_total_io() == 0]
        # 'All' → بدون فیلتر
        
        # ============================================================
        # 3. اعمال جستجو
        # ============================================================
        if search_query and search_query.strip():
            query_lower = search_query.lower().strip()
            
            filtered_search = []
            for device in filtered:
                # ===== فیلدهای قابل جستجو =====
                name = (device.Name or '').lower()
                description = (device.Description or '').lower()
                info = (device.INFO or '').lower()
                smart_tag = (getattr(device, 'SmartTag', '') or '').lower()
                
                # ===== بررسی مطابقت =====
                if (query_lower in name or
                    query_lower in description or
                    query_lower in info or
                    query_lower in smart_tag):
                    filtered_search.append(device)
            
            filtered = filtered_search
        
        # ============================================================
        # 4. نمایش
        # ============================================================
        self._populate_table(filtered)
    
    def _populate_table(self, devices: List):
        """
        پر کردن جدول با داده‌های فیلترشده
        
        Args:
            devices: لیست دستگاه‌ها
        """
        # ===== پاک کردن =====
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # ===== ذخیره داده فعلی =====
        self._data = devices
        
        # ===== افزودن =====
        for i, device in enumerate(devices, 1):
            values = (
                i,
                device.Name or "",
                device.Description or "",
                device.DI,
                device.DO,
                device.AI,
                device.AO,
                device.get_total_io(),
                device.INFO or "",
            )
            
            # تشخیص رنگ بر اساس I/O
            total_io = device.get_total_io()
            tag = 'inactive' if total_io == 0 else 'active'
            
            self.tree.insert('', 'end', values=values, tags=(tag,))
        
        # ===== تنظیم رنگ‌ها =====
        self.tree.tag_configure('active', foreground=get_color('text_primary'))
        self.tree.tag_configure('inactive', foreground=get_color('text_muted'))
        
        # ===== به‌روزرسانی شمارنده =====
        total = len(self._all_data)
        shown = len(devices)
        
        if shown == total:
            self.counter_label.configure(text=f"{total} devices")
        else:
            self.counter_label.configure(text=f"{shown} of {total} devices")
        
        # ===== به‌روزرسانی وضعیت دکمه‌ها =====
        self._update_move_buttons()
        self._update_buttons_state(has_selection=False)
    
    def get_selected_indices(self) -> List[int]:
        """دریافت ایندکس دستگاه‌های انتخاب شده (بر اساس داده اصلی)"""
        indices = []
        
        for item in self.tree.selection():
            values = self.tree.item(item, 'values')
            if not values:
                continue
            
            # ===== پیدا کردن دستگاه در داده اصلی =====
            row_num = int(values[0])          # شماره ردیف در جدول فعلی
            device_name = values[1]            # نام دستگاه
            
            # ===== پیدا کردن در self._data (فیلترشده) =====
            if 0 < row_num <= len(self._data):
                device = self._data[row_num - 1]
                
                # ===== پیدا کردن ایندکس در self._all_data =====
                try:
                    real_index = self._all_data.index(device)
                    indices.append(real_index)
                except ValueError:
                    # اگر پیدا نشد، از شماره فعلی استفاده کن
                    indices.append(row_num - 1)
        
        return indices
    
    def select_all(self):
        """انتخاب همه"""
        self.tree.selection_set(self.tree.get_children())
    
    def clear_selection(self):
        """پاک کردن انتخاب"""
        self.tree.selection_remove(self.tree.selection())
    
    # ================================================================
    # DEVICE OPERATIONS (جدید - منتقل‌شده از Toolbar اصلی)
    # ================================================================
    
    def _on_add(self):
        """افزودن دستگاه"""
        if self.app and hasattr(self.app, '_add_device'):
            self.app._add_device()
    
    def _on_edit(self):
        """ویرایش دستگاه"""
        if self.app and hasattr(self.app, '_edit_device'):
            self.app._edit_device()
    
    def _on_delete(self):
        """حذف دستگاه"""
        if self.app and hasattr(self.app, '_delete_device'):
            self.app._delete_device()

    def _on_export(self):
        """Export Devices به Excel"""
        if self.app and hasattr(self.app, '_export_excel'):
            self.app._export_excel()

    def _on_copy(self):
        """کپی دستگاه‌ها"""
        if self.app and hasattr(self.app, '_copy_device'):
            self.app._copy_device()
    
    def _on_paste(self):
        """چسباندن دستگاه‌ها"""
        if self.app and hasattr(self.app, '_paste_device'):
            self.app._paste_device()

    # ================================================================
    # MOVE OPERATIONS
    # ================================================================
    
    def _move_up(self):
        """جابجایی دستگاه به بالا"""
        if not self.app:
            return
        
        if hasattr(self.app, '_move_device_up'):
            self.app._move_device_up()
    
    def _move_down(self):
        """جابجایی دستگاه به پایین"""
        if not self.app:
            return
        
        if hasattr(self.app, '_move_device_down'):
            self.app._move_device_down()
    
    def _fix_names(self):
        """اصلاح نام‌های تکراری"""
        if not self.app:
            return
        
        if hasattr(self.app, '_fix_duplicate_names'):
            self.app._fix_duplicate_names()
    
    # ================================================================
    # BUTTONS STATE MANAGEMENT
    # ================================================================
    
    def _update_buttons_state(self, has_selection: bool = False):
        """
        به‌روزرسانی وضعیت دکمه‌ها
        
        Args:
            has_selection: آیا چیزی انتخاب شده؟
        """
        # ============================================================
        # Edit و Delete: نیاز به انتخاب
        # ============================================================
        if self.edit_btn:
            self._set_button_enabled(self.edit_btn, has_selection)
        
        if self.delete_btn:
            self._set_button_enabled(self.delete_btn, has_selection)
        
        # ============================================================
        # Add: همیشه فعال
        # ============================================================
        if self.add_btn:
            self._set_button_enabled(self.add_btn, True)
        
        # ============================================================
        # Fix Names: همیشه فعال (اگر داده داشته باشیم)
        # ============================================================
        if self.fix_names_btn:
            self._set_button_enabled(
                self.fix_names_btn, 
                len(self._all_data) > 0
            )
    
    def _set_button_enabled(self, button, enabled: bool):
        """تنظیم وضعیت یک دکمه (با پشتیبانی از set_enabled)"""
        try:
            if hasattr(button, 'set_enabled'):
                button.set_enabled(enabled)
            else:
                # Fallback: استفاده از configure
                state = 'normal' if enabled else 'disabled'
                button.configure(state=state)
        except Exception:
            pass
    
    def _update_move_buttons(self):
        """به‌روزرسانی وضعیت دکمه‌های جابجایی"""
        if not self.move_up_btn or not self.move_down_btn:
            return
        
        selection = self.tree.selection()
        
        if not selection:
            self._set_button_enabled(self.move_up_btn, False)
            self._set_button_enabled(self.move_down_btn, False)
            return
        
        # ایندکس اولین انتخاب
        first_idx = self.tree.index(selection[0])
        total = len(self.tree.get_children())
        
        # فعال/غیرفعال
        can_move_up = first_idx > 0
        can_move_down = first_idx < total - 1
        
        self._set_button_enabled(self.move_up_btn, can_move_up)
        self._set_button_enabled(self.move_down_btn, can_move_down)
    
    # ================================================================
    # EVENTS
    # ================================================================
    
    def _on_search(self, query: str):
        """جستجو در جدول"""
        self._apply_filters(search_query=query)
    
    def _on_filter(self):
        """فیلتر بر اساس وضعیت"""
        self._current_filter = self.filter_var.get()
        
        current_query = self.search.get() if hasattr(self, 'search') else ''
        self._apply_filters(search_query=current_query)
    
    def _on_select(self, event=None):
        """انتخاب"""
        has_selection = len(self.tree.selection()) > 0
        
        # ===== دکمه‌های Edit/Delete =====
        self._update_buttons_state(has_selection=has_selection)
        
        # ===== دکمه‌های Move =====
        self._update_move_buttons()


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['DeviceTable']