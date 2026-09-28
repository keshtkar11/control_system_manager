"""دیالوگ‌های مدیریت کامپوننت‌های سفارشی"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import re
from typing import Optional

from core.constants import COLORS
from gui.theme import create_hover_effect


class ComponentManagerDialog:
    """دیالوگ مدیریت کامپوننت‌های سفارشی"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = None
        self.tree = None
        self.search_var = tk.StringVar()
    
    def show(self):
        """نمایش دیالوگ"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("🧩 Component Manager")
        self.window.geometry("850x550")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # مرکز کردن
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # ===== عنوان =====
        tk.Label(
            self.window,
            text="🧩 Component Manager",
            font=("Segoe UI", 16, "bold"),
            fg=COLORS['primary']
        ).pack(pady=10)
        
        tk.Label(
            self.window,
            text="Manage custom components. Default components cannot be edited or deleted.",
            font=("Segoe UI", 9),
            fg="#6c757d"
        ).pack(pady=(0, 10))
        
        # ===== نوار ابزار =====
        toolbar = tk.Frame(self.window)
        toolbar.pack(fill=tk.X, padx=20, pady=5)
        
        # جستجو
        tk.Label(toolbar, text="🔍 Search:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
        search_entry = tk.Entry(toolbar, textvariable=self.search_var, width=20, font=("Segoe UI", 9))
        search_entry.pack(side=tk.LEFT, padx=(0, 15))
        self.search_var.trace("w", lambda *args: self._refresh_list())
        
        # دکمه‌ها
        btn_add = tk.Button(
            toolbar,
            text="➕ Add Component",
            command=self._add_component,
            bg=COLORS['success'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=15,
            pady=5,
            cursor="hand2"
        )
        btn_add.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_add, COLORS['success'])
        
        btn_edit = tk.Button(
            toolbar,
            text="✏️ Edit",
            command=self._edit_component,
            bg=COLORS['accent'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=15,
            pady=5,
            cursor="hand2"
        )
        btn_edit.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_edit, COLORS['accent'])
        
        btn_delete = tk.Button(
            toolbar,
            text="🗑️ Delete",
            command=self._delete_component,
            bg=COLORS['danger'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=15,
            pady=5,
            cursor="hand2"
        )
        btn_delete.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_delete, COLORS['danger'])
        
        btn_refresh = tk.Button(
            toolbar,
            text="🔄 Refresh",
            command=self._refresh_list,
            bg=COLORS['secondary'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=15,
            pady=5,
            cursor="hand2"
        )
        btn_refresh.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_refresh, COLORS['secondary'])
        
        # ===== لیست کامپوننت‌ها =====
        list_frame = tk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview
        columns = ("Key", "Persian", "English", "DI", "DO", "AI", "AO", "Cable Size", "Type")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # تنظیم ستون‌ها
        col_widths = {
            "Key": 100,
            "Persian": 120,
            "English": 120,
            "DI": 50,
            "DO": 50,
            "AI": 50,
            "AO": 50,
            "Cable Size": 90,
            "Type": 100
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 80), anchor="center")
        
        self.tree.column("Persian", anchor="w")
        self.tree.column("English", anchor="w")
        
        # اسکرول
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # دابل کلیک برای ویرایش
        self.tree.bind("<Double-1>", lambda e: self._edit_component())
        
        # ===== راهنما =====
        help_frame = tk.Frame(self.window, bg=COLORS['light'], relief=tk.GROOVE, bd=1)
        help_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            help_frame,
            text="💡 Tip: Double-click on a custom component to edit it. Default components cannot be edited or deleted.",
            font=("Segoe UI", 9),
            bg=COLORS['light'],
            fg="#6c757d"
        ).pack(pady=5)
        
        # ===== دکمه بستن =====
        btn_close = tk.Button(
            self.window,
            text="❌ Close",
            command=self.window.destroy,
            bg=COLORS['secondary'],
            fg=COLORS['white'],
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=25,
            pady=8,
            cursor="hand2"
        )
        btn_close.pack(pady=10)
        create_hover_effect(btn_close, COLORS['secondary'])
        
        # بارگذاری اولیه
        self._refresh_list()
    
    def _refresh_list(self):
        """بروزرسانی لیست کامپوننت‌ها"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        search_term = self.search_var.get().strip().lower()
        component_manager = self.app.component_manager
        
        for key, data in component_manager.get_all_components().items():
            # فیلتر جستجو
            if search_term:
                fa = data.get('fa', '').lower()
                en = data.get('en', '').lower()
                if search_term not in key.lower() and search_term not in fa and search_term not in en:
                    continue
            
            io = data.get('io', {})
            is_default = data.get('is_default', False)
            
            values = (
                key,
                data.get('fa', key),
                data.get('en', key),
                io.get('DI', 0),
                io.get('DO', 0),
                io.get('AI', 0),
                io.get('AO', 0),
                data.get('cable_size', '2x1mm²'),
                "Default" if is_default else "Custom"
            )
            
            item = self.tree.insert("", "end", values=values)
            
            # رنگ‌بندی
            if is_default:
                self.tree.item(item, tags=('default',))
        
        self.tree.tag_configure('default', foreground='gray')
    
    def _get_selected_key(self) -> Optional[str]:
        """دریافت کلید کامپوننت انتخاب شده"""
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree.item(selection[0])['values'][0]
    
    def _add_component(self):
        """افزودن کامپوننت جدید"""
        dialog = AddComponentDialog(self.window, self.app)
        dialog.show()
        self._refresh_list()
    
    def _edit_component(self):
        """ویرایش کامپوننت انتخاب شده"""
        key = self._get_selected_key()
        if not key:
            messagebox.showwarning("Warning", "Please select a component to edit.")
            return
        
        # بررسی پیش‌فرض بودن
        if self.app.component_manager.is_default_component(key):
            messagebox.showinfo("Info", "Default components cannot be edited.")
            return
        
        dialog = EditComponentDialog(self.window, self.app, key)
        dialog.show()
        self._refresh_list()
    
    def _delete_component(self):
        """حذف کامپوننت انتخاب شده"""
        key = self._get_selected_key()
        if not key:
            messagebox.showwarning("Warning", "Please select a component to delete.")
            return
        
        if self.app.component_manager.is_default_component(key):
            messagebox.showinfo("Info", "Default components cannot be deleted.")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete custom component '{key}' permanently?"):
            if self.app.component_manager.delete_component(key):
                messagebox.showinfo("Success", f"Component '{key}' deleted successfully.")
                self._refresh_list()
            else:
                messagebox.showerror("Error", f"Failed to delete component '{key}'.")


class AddComponentDialog:
    """دیالوگ افزودن کامپوننت جدید"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = None
        self.entries = {}
        self.io_entries = {}
    
    def show(self):
        """نمایش دیالوگ"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("➕ Add New Component")
        self.window.geometry("500x520")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # مرکز کردن
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # ===== عنوان =====
        tk.Label(
            self.window,
            text="➕ Add New Component",
            font=("Segoe UI", 14, "bold"),
            fg=COLORS['primary']
        ).pack(pady=10)
        
        # ===== فرم =====
        form_frame = tk.Frame(self.window, padx=20, pady=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # فیلدها
        fields = [
            ("Component Key (Unique ID):", "key", 20, "e.g. MY_SENSOR"),
            ("Persian Label:", "label_fa", 20, "سنسور سفارشی"),
            ("English Label:", "label_en", 20, "Custom Sensor"),
            ("Cable Size:", "cable_size", 15, "2x1mm²"),
        ]
        
        for i, (label, attr, width, placeholder) in enumerate(fields):
            tk.Label(
                form_frame,
                text=label,
                font=("Segoe UI", 9, "bold")
            ).grid(row=i, column=0, sticky="w", pady=5, padx=(0, 10))
            
            entry = tk.Entry(form_frame, width=width, font=("Segoe UI", 9))
            entry.grid(row=i, column=1, sticky="ew", pady=5)
            if placeholder:
                entry.insert(0, placeholder)
                entry.select_range(0, tk.END)
            self.entries[attr] = entry
        
        # I/O Configuration
        io_frame = tk.LabelFrame(
            form_frame,
            text="I/O Configuration",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=10
        )
        io_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        
        io_types = ["DI", "DO", "AI", "AO"]
        for i, io_type in enumerate(io_types):
            tk.Label(
                io_frame,
                text=f"{io_type}:",
                font=("Segoe UI", 9)
            ).grid(row=0, column=i*2, sticky="e", padx=(0, 5))
            
            entry = tk.Entry(io_frame, width=6, font=("Segoe UI", 9), justify="center")
            entry.insert(0, "0")
            entry.grid(row=0, column=i*2+1, sticky="w", padx=(0, 15))
            self.io_entries[io_type] = entry
        
        # ===== هشدار =====
        warning_frame = tk.Frame(form_frame, bg="#fff3cd", relief=tk.GROOVE, bd=1)
        warning_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        
        tk.Label(
            warning_frame,
            text="⚠️ Component Key must be unique and contain only uppercase letters, numbers, and underscore.",
            font=("Segoe UI", 8),
            bg="#fff3cd",
            fg="#856404"
        ).pack(pady=5)
        
        # ===== دکمه‌ها =====
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=15)
        
        btn_save = tk.Button(
            btn_frame,
            text="💾 Save",
            command=self._save,
            bg=COLORS['success'],
            fg=COLORS['white'],
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=25,
            pady=8,
            cursor="hand2"
        )
        btn_save.pack(side=tk.LEFT, padx=5)
        create_hover_effect(btn_save, COLORS['success'])
        
        btn_cancel = tk.Button(
            btn_frame,
            text="❌ Cancel",
            command=self.window.destroy,
            bg=COLORS['secondary'],
            fg=COLORS['white'],
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=25,
            pady=8,
            cursor="hand2"
        )
        btn_cancel.pack(side=tk.LEFT, padx=5)
        create_hover_effect(btn_cancel, COLORS['secondary'])
        
        # فوکوس روی فیلد اول
        self.entries["key"].focus()
    
    def _save(self):
        """ذخیره کامپوننت جدید"""
        key = self.entries["key"].get().strip().upper()
        label_fa = self.entries["label_fa"].get().strip()
        label_en = self.entries["label_en"].get().strip()
        cable_size = self.entries["cable_size"].get().strip()
        
        # اعتبارسنجی
        if not key:
            messagebox.showerror("Error", "Component Key is required!")
            return
        
        if not re.match(r'^[A-Z0-9_]+$', key):
            messagebox.showerror(
                "Error", 
                "Key can only contain uppercase letters, numbers, and underscore!"
            )
            return
        
        if not label_fa:
            messagebox.showerror("Error", "Persian label is required!")
            return
        
        if not label_en:
            messagebox.showerror("Error", "English label is required!")
            return
        
        try:
            di = int(self.io_entries["DI"].get() or 0)
            do = int(self.io_entries["DO"].get() or 0)
            ai = int(self.io_entries["AI"].get() or 0)
            ao = int(self.io_entries["AO"].get() or 0)
        except ValueError:
            messagebox.showerror("Error", "I/O values must be numbers!")
            return        
        # ذخیره
        if self.app.component_manager.add_component(key, label_fa, label_en, di, do, ai, ao, cable_size):
            messagebox.showinfo("Success", f"Component '{key}' added successfully!")
            self.window.destroy()
        else:
            messagebox.showerror("Error", "Failed to add component. Key may already exist.")


class EditComponentDialog:
    """دیالوگ ویرایش کامپوننت سفارشی"""
    
    def __init__(self, parent, app, key: str):
        self.parent = parent
        self.app = app
        self.key = key
        self.window = None
        self.entries = {}
        self.io_entries = {}
        self.component_data = None
    
    def show(self):
        """نمایش دیالوگ"""
        self.component_data = self.app.component_manager.get_component(self.key)
        if not self.component_data:
            messagebox.showerror("Error", f"Component '{self.key}' not found!")
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"✏️ Edit Component: {self.key}")
        self.window.geometry("500x520")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # مرکز کردن
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # ===== عنوان =====
        tk.Label(
            self.window,
            text=f"✏️ Edit Component: {self.key}",
            font=("Segoe UI", 14, "bold"),
            fg=COLORS['primary']
        ).pack(pady=10)
        
        # ===== فرم =====
        form_frame = tk.Frame(self.window, padx=20, pady=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # فیلدها
        fields = [
            ("Persian Label:", "label_fa", 20),
            ("English Label:", "label_en", 20),
            ("Cable Size:", "cable_size", 15),
        ]
        
        io = self.component_data.get('io', {})
        
        for i, (label, attr, width) in enumerate(fields):
            tk.Label(
                form_frame,
                text=label,
                font=("Segoe UI", 9, "bold")
            ).grid(row=i, column=0, sticky="w", pady=5, padx=(0, 10))
            
            value = self.component_data.get(attr, "")
            if attr == 'cable_size':
                value = self.component_data.get('cable_size', '2x1mm²')
            
            entry = tk.Entry(form_frame, width=width, font=("Segoe UI", 9))
            entry.insert(0, value)
            entry.grid(row=i, column=1, sticky="ew", pady=5)
            self.entries[attr] = entry
        
        # I/O Configuration
        io_frame = tk.LabelFrame(
            form_frame,
            text="I/O Configuration",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=10
        )
        io_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        io_types = ["DI", "DO", "AI", "AO"]
        for i, io_type in enumerate(io_types):
            tk.Label(
                io_frame,
                text=f"{io_type}:",
                font=("Segoe UI", 9)
            ).grid(row=0, column=i*2, sticky="e", padx=(0, 5))
            
            value = io.get(io_type, 0)
            entry = tk.Entry(io_frame, width=6, font=("Segoe UI", 9), justify="center")
            entry.insert(0, str(value))
            entry.grid(row=0, column=i*2+1, sticky="w", padx=(0, 15))
            self.io_entries[io_type] = entry
        
        # ===== دکمه‌ها =====
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=15)
        
        btn_save = tk.Button(
            btn_frame,
            text="💾 Save",
            command=self._save,
            bg=COLORS['success'],
            fg=COLORS['white'],
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=25,
            pady=8,
            cursor="hand2"
        )
        btn_save.pack(side=tk.LEFT, padx=5)
        create_hover_effect(btn_save, COLORS['success'])
        
        btn_cancel = tk.Button(
            btn_frame,
            text="❌ Cancel",
            command=self.window.destroy,
            bg=COLORS['secondary'],
            fg=COLORS['white'],
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=25,
            pady=8,
            cursor="hand2"
        )
        btn_cancel.pack(side=tk.LEFT, padx=5)
        create_hover_effect(btn_cancel, COLORS['secondary'])
    
    def _save(self):
        """ذخیره تغییرات"""
        label_fa = self.entries["label_fa"].get().strip()
        label_en = self.entries["label_en"].get().strip()
        cable_size = self.entries["cable_size"].get().strip()
        
        if not label_fa or not label_en:
            messagebox.showerror("Error", "Both Persian and English labels are required!")
            return
        
        try:
            di = int(self.io_entries["DI"].get() or 0)
            do = int(self.io_entries["DO"].get() or 0)
            ai = int(self.io_entries["AI"].get() or 0)
            ao = int(self.io_entries["AO"].get() or 0)
        except ValueError:
            messagebox.showerror("Error", "I/O values must be numbers!")
            return
        
        # به‌روزرسانی
        if self.app.component_manager.update_component(
            self.key,
            label_fa=label_fa,
            label_en=label_en,
            di=di,
            do=do,
            ai=ai,
            ao=ao,
            cable_size=cable_size
        ):
            messagebox.showinfo("Success", f"Component '{self.key}' updated successfully!")
            self.window.destroy()
        else:
            messagebox.showerror("Error", "Failed to update component.")