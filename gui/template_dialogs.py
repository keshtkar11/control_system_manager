"""دیالوگ‌های مدیریت قالب‌های تجهیزات"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
from typing import Optional, List, Dict, Any
import json

from core.constants import COLORS
from gui.theme import create_hover_effect


class TemplateManagerDialog:
    """دیالوگ مدیریت قالب‌ها"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = None
        self.tree = None
        self.search_var = tk.StringVar()
        self.preview_text = None
    
    def show(self):
        """نمایش دیالوگ"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("📋 Template Manager")
        self.window.geometry("1000x650")
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
            text="📋 Equipment Template Manager",
            font=("Segoe UI", 16, "bold"),
            fg=COLORS['primary']
        ).pack(pady=10)
        
        tk.Label(
            self.window,
            text="Manage equipment templates. Default templates cannot be edited or deleted.",
            font=("Segoe UI", 9),
            fg="#6c757d"
        ).pack(pady=(0, 10))
        
        # ===== پنل اصلی =====
        main_panel = tk.Frame(self.window)
        main_panel.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # ===== سمت چپ: لیست قالب‌ها =====
        left_panel = tk.Frame(main_panel, width=500)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # نوار ابزار
        toolbar = tk.Frame(left_panel)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(toolbar, text="🔍 Search:", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
        search_entry = tk.Entry(toolbar, textvariable=self.search_var, width=15, font=("Segoe UI", 9))
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_var.trace("w", lambda *args: self._refresh_list())
        
        btn_add = tk.Button(
            toolbar,
            text="➕ New",
            command=self._add_template,
            bg=COLORS['success'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_add.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_add, COLORS['success'])
        
        btn_edit = tk.Button(
            toolbar,
            text="✏️ Edit",
            command=self._edit_template,
            bg=COLORS['accent'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_edit.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_edit, COLORS['accent'])
        
        btn_delete = tk.Button(
            toolbar,
            text="🗑️ Delete",
            command=self._delete_template,
            bg=COLORS['danger'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_delete.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_delete, COLORS['danger'])

        btn_duplicate = tk.Button(
            toolbar,
            text="📋 Duplicate",
            command=self._duplicate_template,
            bg='#8E44AD',
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_duplicate.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_duplicate, '#8E44AD')

        btn_reset = tk.Button(
            toolbar,
            text="🔄 Reset Default",
            command=self._reset_to_default,
            bg='#E67E22',
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_reset.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_reset, '#E67E22')
        
        btn_refresh = tk.Button(
            toolbar,
            text="🔄 Refresh",
            command=self._refresh_list,
            bg=COLORS['secondary'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_refresh.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_refresh, COLORS['secondary'])
        
        # Treeview
        tree_frame = tk.Frame(left_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Name", "Category", "Devices", "Usage", "Type")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=18)
        
        col_widths = {"Name": 180, "Category": 120, "Devices": 80, "Usage": 60, "Type": 80}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 80), anchor="center")
        self.tree.column("Name", anchor="w")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._edit_template())
        
        # ===== سمت راست: پیش‌نمایش =====
        right_panel = tk.Frame(main_panel, width=450)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            right_panel,
            text="📄 Template Preview",
            font=("Segoe UI", 11, "bold"),
            fg=COLORS['primary']
        ).pack(anchor="w", pady=(0, 5))
        
        self.preview_text = scrolledtext.ScrolledText(
            right_panel,
            wrap=tk.WORD,
            font=("Courier New", 9),
            bg="#f8f9fa"
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        self.preview_text.config(state=tk.DISABLED)
        
        # دکمه استفاده
        btn_use = tk.Button(
            right_panel,
            text="✅ Use This Template",
            command=self._use_template,
            bg=COLORS['success'],
            fg=COLORS['white'],
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=20,
            pady=8,
            cursor="hand2"
        )
        btn_use.pack(pady=10)
        create_hover_effect(btn_use, COLORS['success'])
        
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
        """بروزرسانی لیست قالب‌ها"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        search_term = self.search_var.get().strip().lower()
        
        for name, data in self.app.template_manager.get_all_templates().items():
            if search_term and search_term not in name.lower():
                continue
            
            devices = data.get('devices', [])
            device_count = len(devices)
            usage = data.get('usage_count', 0)
            is_default = data.get('is_default', False)
            category = data.get('category', 'Other')
            
            values = (
                name,
                category,
                device_count,
                usage,
                "Default" if is_default else "Custom"
            )
            
            item = self.tree.insert("", "end", values=values)
            if is_default:
                self.tree.item(item, tags=('default',))
        
        self.tree.tag_configure('default', foreground='gray')
        
        # پاک کردن پیش‌نمایش
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.config(state=tk.DISABLED)
    
    def _on_select(self, event):
        """انتخاب قالب و نمایش پیش‌نمایش"""
        selection = self.tree.selection()
        if not selection:
            return
        
        values = self.tree.item(selection[0])['values']
        name = values[0]
        
        preview = self.app.template_manager.get_template_preview(name)
        
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, preview)
        self.preview_text.config(state=tk.DISABLED)
    
    def _get_selected_name(self) -> Optional[str]:
        """دریافت نام قالب انتخاب شده"""
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree.item(selection[0])['values'][0]
    
    def _add_template(self):
        """افزودن قالب جدید"""
        dialog = AddTemplateDialog(self.window, self.app)
        dialog.show()
        self._refresh_list()

        if hasattr(self.app, 'refresh_template_list'):
            self.app.refresh_template_list()
    
    def _edit_template(self):
        """ویرایش قالب انتخاب شده"""
        name = self._get_selected_name()
        if not name:
            messagebox.showwarning("Warning", "Please select a template to edit.")
            return
        
        template = self.app.template_manager.get_template(name)
        if not template:
            return
        
        if template.get('is_default', False):
            messagebox.showinfo("Info", "Default templates cannot be edited.\nYou can create a custom version instead.")
            return
        
        dialog = EditTemplateDialog(self.window, self.app, name)
        dialog.show()
        self._refresh_list()

        
        if hasattr(self.app, 'refresh_template_list'):
            self.app.refresh_template_list()
    
    def _delete_template(self):
        """حذف قالب انتخاب شده"""
        name = self._get_selected_name()
        if not name:
            messagebox.showwarning("Warning", "Please select a template to delete.")
            return
        
        template = self.app.template_manager.get_template(name)
        if not template:
            return
        
        if template.get('is_default', False):
            messagebox.showinfo("Info", "Default templates cannot be deleted.")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete template '{name}' permanently?"):
            if self.app.template_manager.delete_template(name):
                messagebox.showinfo("Success", f"Template '{name}' deleted successfully.")
                self._refresh_list()  # بروزرسانی لیست داخل دیالوگ
                
                # ✅ بروزرسانی لیست در پنجره اصلی
                if hasattr(self.app, 'refresh_template_list'):
                    self.app.refresh_template_list()
                
            else:
                messagebox.showerror("Error", f"Failed to delete template '{name}'.")

    def _duplicate_template(self):
        """کپی کردن قالب - استفاده از duplicate_template"""
        name = self._get_selected_name()
        if not name:
            messagebox.showwarning("Warning", "Please select a template to duplicate.")
            return
        
        new_name = simpledialog.askstring(
            "Duplicate Template",
            f"Enter new name for '{name}':",
            parent=self.window
        )
        if not new_name or not new_name.strip():
            return
        
        # استفاده از duplicate_template
        success = self.app.template_manager.duplicate_template(name, new_name.strip())
        
        if success:
            self._refresh_list()
            messagebox.showinfo("Success", f"Template '{name}' duplicated as '{new_name}'!")
        else:
            messagebox.showerror("Error", "Failed to duplicate template!")

        
        if hasattr(self.app, 'refresh_template_list'):
            self.app.refresh_template_list()

    def _reset_to_default(self):
        """بازنشانی قالب به پیش‌فرض - استفاده از reset_template_to_default"""
        name = self._get_selected_name()
        if not name:
            return
        
        template = self.app.template_manager.get_template(name)
        if not template or not template.get('is_default', False):
            messagebox.showinfo("Info", "Only custom templates can be reset to default.")
            return
        
        if messagebox.askyesno(
            "Reset Template",
            f"Reset '{name}' to default version? All custom changes will be lost."
        ):
            # ✅ استفاده از reset_template_to_default
            success = self.app.template_manager.reset_template_to_default(name)
            
            if success:
                self._refresh_list()
                messagebox.showinfo("Success", f"Template '{name}' reset to default!")
            else:
                messagebox.showerror("Error", "Failed to reset template!")

        
        if hasattr(self.app, 'refresh_template_list'):
            self.app.refresh_template_list()
    
    def _use_template(self):
        """استفاده از قالب انتخاب شده"""
        name = self._get_selected_name()
        if not name:
            messagebox.showwarning("Warning", "Please select a template to use.")
            return
        
        # بستن دیالوگ و باز کردن دیالوگ استفاده از قالب
        self.window.destroy()
        # در main_window یک متد برای استفاده از قالب وجود دارد
        self.app._use_template(name)


class AddTemplateDialog:
    """دیالوگ افزودن قالب جدید"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = None
        self.entries = {}
        self.devices_list = []
        self.device_tree = None
    
    def show(self):
        """نمایش دیالوگ"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("➕ Add New Template")
        self.window.geometry("700x600")
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
            text="➕ Add New Template",
            font=("Segoe UI", 14, "bold"),
            fg=COLORS['primary']
        ).pack(pady=10)
        
        # ===== فرم =====
        form_frame = tk.Frame(self.window, padx=20, pady=10)
        form_frame.pack(fill=tk.X)
        
        # نام قالب
        tk.Label(form_frame, text="Template Name:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        name_entry = tk.Entry(form_frame, width=30, font=("Segoe UI", 9))
        name_entry.grid(row=0, column=1, sticky="w", pady=5, padx=(0, 20))
        self.entries['name'] = name_entry
        
        # دسته‌بندی
        tk.Label(form_frame, text="Category:", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", pady=5)
        categories = ["Mechanical", "HVAC", "Electrical", "Plumbing", "Custom"]
        category_combo = ttk.Combobox(form_frame, values=categories, width=15, state="readonly")
        category_combo.set("Mechanical")
        category_combo.grid(row=0, column=3, sticky="w", pady=5)
        self.entries['category'] = category_combo
        
        # ===== لیست دستگاه‌ها =====
        devices_frame = tk.LabelFrame(
            self.window,
            text="📋 Devices in Template",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        devices_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # نوار ابزار دستگاه‌ها
        dev_toolbar = tk.Frame(devices_frame)
        dev_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        btn_add_device = tk.Button(
            dev_toolbar,
            text="➕ Add Device",
            command=self._add_device,
            bg=COLORS['success'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_add_device.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_add_device, COLORS['success'])
        
        btn_remove_device = tk.Button(
            dev_toolbar,
            text="🗑️ Remove Device",
            command=self._remove_device,
            bg=COLORS['danger'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_remove_device.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_remove_device, COLORS['danger'])
        
        btn_clear_devices = tk.Button(
            dev_toolbar,
            text="🗑️ Clear All",
            command=self._clear_devices,
            bg=COLORS['warning'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_clear_devices.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_clear_devices, COLORS['warning'])
        
        # Treeview دستگاه‌ها
        tree_frame = tk.Frame(devices_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("#", "Device Type", "Quantity", "Component", "I/O", "Naming")
        self.device_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        
        col_widths = {"#": 40, "Device Type": 150, "Quantity": 60, "Component": 120, "I/O": 120, "Naming": 120}
        for col in columns:
            self.device_tree.heading(col, text=col)
            self.device_tree.column(col, width=col_widths.get(col, 80), anchor="center")
        self.device_tree.column("Device Type", anchor="w")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.device_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.device_tree.xview)
        self.device_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.device_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # ===== دکمه‌ها =====
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=15)
        
        btn_save = tk.Button(
            btn_frame,
            text="💾 Save Template",
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
        
        # فوکوس روی فیلد نام
        name_entry.focus()
    
    def _add_device(self):
        """افزودن دستگاه"""
        dialog = AddDeviceToTemplateDialog(self.window, self.app)
        device = dialog.show()
        if device:
            self.devices_list.append(device)
            self._refresh_device_list()
    
    def _remove_device(self):
        """حذف دستگاه انتخاب شده"""
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a device to remove.")
            return
        
        index = int(self.device_tree.item(selection[0])['values'][0]) - 1
        if 0 <= index < len(self.devices_list):
            del self.devices_list[index]
            self._refresh_device_list()
    
    def _clear_devices(self):
        """پاک کردن همه دستگاه‌ها"""
        if self.devices_list and messagebox.askyesno("Confirm", "Remove all devices?"):
            self.devices_list = []
            self._refresh_device_list()
    
    def _refresh_device_list(self):
        """بروزرسانی لیست دستگاه‌ها"""
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        for i, device in enumerate(self.devices_list, 1):
            name = device.get('name', 'Unknown')
            # اگر دستگاه دارای کامپوننت‌هاست
            if 'components' in device:
                total_qty = sum(comp.get('quantity', 1) for comp in device['components'])
                comp_count = len(device['components'])
                total_io = sum(
                    comp.get('io', {}).get('DI', 0) + comp.get('io', {}).get('DO', 0) +
                    comp.get('io', {}).get('AI', 0) + comp.get('io', {}).get('AO', 0)
                    for comp in device['components']
                )
                self.device_tree.insert("", "end", values=(i, name, total_qty, comp_count, f"Total IO: {total_io}", '-'))
            else:
                # حالت قدیمی
                io = f"DI:{device.get('di',0)} DO:{device.get('do',0)} AI:{device.get('ai',0)} AO:{device.get('ao',0)}"
                self.device_tree.insert("", "end", values=(i, name, device.get('quantity', 1), 1, io, '-'))
    
    def _save(self):
        """ذخیره قالب"""
        name = self.entries['name'].get().strip()
        category = self.entries['category'].get()
        
        if not name:
            messagebox.showerror("Error", "Template name is required!")
            return
        
        if not self.devices_list:
            messagebox.showerror("Error", "Please add at least one device to the template!")
            return
        
        # ===== انتقال quantity از components به devices =====
        for device in self.devices_list:
            if 'components' in device:
                for comp in device['components']:
                    device['quantity'] = comp.get('quantity', 1)
                    device['di'] = comp.get('io', {}).get('DI', 0)
                    device['do'] = comp.get('io', {}).get('DO', 0)
                    device['ai'] = comp.get('io', {}).get('AI', 0)
                    device['ao'] = comp.get('io', {}).get('AO', 0)
            # اگر quantity در سطح بالای device وجود ندارد، آن را ست کن
            if not device.get('quantity'):
                device['quantity'] = 1
        
        if self.app.template_manager.add_template(name, self.devices_list, category):
            messagebox.showinfo("Success", f"Template '{name}' created successfully!")
            self.window.destroy()
        else:
            messagebox.showerror("Error", "Failed to create template. Name may already exist.")


class AddDeviceToTemplateDialog:
    """دیالوگ افزودن دستگاه به قالب"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = None
        self.result = None
        self.entries = {}
        self.io_entries = {}
    
    def show(self) -> Optional[Dict]:
        """نمایش دیالوگ و بازگرداندن دستگاه"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("➕ Add Device to Template")
        self.window.geometry("550x500")
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
            text="➕ Add Device to Template",
            font=("Segoe UI", 14, "bold"),
            fg=COLORS['primary']
        ).pack(pady=10)
        
        # ===== فرم =====
        form_frame = tk.Frame(self.window, padx=20, pady=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Device Type
        tk.Label(form_frame, text="Device Type:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        type_entry = tk.Entry(form_frame, width=30, font=("Segoe UI", 9))
        type_entry.insert(0, "Temperature Sensor")
        type_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(0, 10))
        self.entries['type'] = type_entry
        
        # Quantity
        tk.Label(form_frame, text="Quantity:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        qty_entry = tk.Entry(form_frame, width=10, font=("Segoe UI", 9), justify="center")
        qty_entry.insert(0, "1")
        qty_entry.grid(row=1, column=1, sticky="w", pady=5)
        self.entries['quantity'] = qty_entry
        
        # Component
        tk.Label(form_frame, text="Component:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        component_keys = self.app.component_manager.get_component_keys()
        component_combo = ttk.Combobox(form_frame, values=component_keys, width=20, state="readonly")
        if component_keys:
            component_combo.set(component_keys[0])
        component_combo.grid(row=2, column=1, sticky="w", pady=5)
        self.entries['component'] = component_combo
        
        # Naming Pattern
        tk.Label(form_frame, text="Naming Pattern:", font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        naming_entry = tk.Entry(form_frame, width=30, font=("Segoe UI", 9))
        naming_entry.insert(0, "{type}-{n}")
        naming_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=(0, 10))
        self.entries['naming'] = naming_entry
        
        # Description Pattern
        tk.Label(form_frame, text="Description Pattern:", font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w", pady=5)
        desc_entry = tk.Entry(form_frame, width=30, font=("Segoe UI", 9))
        desc_entry.insert(0, "{position} Device")
        desc_entry.grid(row=4, column=1, sticky="ew", pady=5, padx=(0, 10))
        self.entries['description'] = desc_entry
        
        # Positions
        tk.Label(form_frame, text="Positions (comma):", font=("Segoe UI", 9, "bold")).grid(row=5, column=0, sticky="w", pady=5)
        pos_entry = tk.Entry(form_frame, width=30, font=("Segoe UI", 9))
        pos_entry.insert(0, "Inlet, Outlet")
        pos_entry.grid(row=5, column=1, sticky="ew", pady=5, padx=(0, 10))
        self.entries['positions'] = pos_entry
        
        # I/O Configuration
        io_frame = tk.LabelFrame(
            form_frame,
            text="I/O Configuration",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=10
        )
        io_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
        
        io_types = ["DI", "DO", "AI", "AO"]
        for i, io_type in enumerate(io_types):
            tk.Label(io_frame, text=f"{io_type}:", font=("Segoe UI", 9)).grid(row=0, column=i*2, sticky="e", padx=(0, 5))
            entry = tk.Entry(io_frame, width=6, font=("Segoe UI", 9), justify="center")
            entry.insert(0, "0")
            entry.grid(row=0, column=i*2+1, sticky="w", padx=(0, 15))
            self.io_entries[io_type] = entry
        
        # Component I/O Info
        def update_io_from_component(*args):
            component_key = component_combo.get()
            if component_key:
                io = self.app.component_manager.get_default_io(component_key)
                self.io_entries["DI"].delete(0, tk.END)
                self.io_entries["DI"].insert(0, str(io.get('DI', 0)))
                self.io_entries["DO"].delete(0, tk.END)
                self.io_entries["DO"].insert(0, str(io.get('DO', 0)))
                self.io_entries["AI"].delete(0, tk.END)
                self.io_entries["AI"].insert(0, str(io.get('AI', 0)))
                self.io_entries["AO"].delete(0, tk.END)
                self.io_entries["AO"].insert(0, str(io.get('AO', 0)))
        
        component_combo.bind("<<ComboboxSelected>>", update_io_from_component)
        
        # ===== دکمه‌ها =====
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=15)
        
        btn_add = tk.Button(
            btn_frame,
            text="✅ Add Device",
            command=self._add,
            bg=COLORS['success'],
            fg=COLORS['white'],
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=25,
            pady=8,
            cursor="hand2"
        )
        btn_add.pack(side=tk.LEFT, padx=5)
        create_hover_effect(btn_add, COLORS['success'])
        
        btn_cancel = tk.Button(
            btn_frame,
            text="❌ Cancel",
            command=self._cancel,
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
        
        # منتظر بمان تا کاربر پاسخ دهد
        self.window.wait_window()
        return self.result
    
    def _add(self):
        """افزودن دستگاه"""
        device_type = self.entries['type'].get().strip()
        quantity = int(self.entries['quantity'].get() or 1)
        component = self.entries['component'].get()
        naming = self.entries['naming'].get().strip()
        description = self.entries['description'].get().strip()
        positions_text = self.entries['positions'].get().strip()
        
        if not device_type:
            messagebox.showerror("Error", "Device type is required!")
            return
        
        positions = [p.strip() for p in positions_text.split(',') if p.strip()]
        
        try:
            di = int(self.io_entries["DI"].get() or 0)
            do = int(self.io_entries["DO"].get() or 0)
            ai = int(self.io_entries["AI"].get() or 0)
            ao = int(self.io_entries["AO"].get() or 0)
        except ValueError:
            messagebox.showerror("Error", "I/O values must be numbers!")
            return
        
        # ===== دریافت I/O پیش‌فرض از ComponentManager =====
        default_io = self.app.component_manager.get_default_io(component)
        
        # اگر کاربر مقدار I/O را دستی وارد نکرده است، از پیش‌فرض استفاده کن
        if di == 0 and do == 0 and ai == 0 and ao == 0:
            di = default_io.get('DI', 0)
            do = default_io.get('DO', 0)
            ai = default_io.get('AI', 0)
            ao = default_io.get('AO', 0)
        
        # ===== ذخیره quantity در سطح device و component =====

        self.result = {
            'name': device_type,
            'description': description,
            'quantity': max(1, quantity),
            'component': component,  # ✅ ذخیره کلید کامپوننت در سطح device
            'components': [
                {
                    'type': device_type,
                    'quantity': max(1, quantity),
                    'component': component,  # ✅ ذخیره کلید کامپوننت
                    'naming': naming or "{type}-{n}",
                    'description': description or "",
                    'positions': positions,
                    'io': {'DI': di, 'DO': do, 'AI': ai, 'AO': ao}
                }
            ]
        }
        
        self.window.destroy()
    
    def _cancel(self):
        """انصراف"""
        self.result = None
        self.window.destroy()

class EditTemplateDialog:
    """دیالوگ ویرایش قالب"""
    
    def __init__(self, parent, app, template_name: str):
        self.parent = parent
        self.app = app
        self.template_name = template_name
        self.window = None
        self.entries = {}
        self.devices_list = []
        self.device_tree = None
        
        # دریافت داده‌های ویرایش از TemplateManager
        edit_data = self.app.template_manager.get_template_edit_data(template_name)
        if not edit_data:
            messagebox.showerror("Error", f"Failed to load template '{template_name}' for editing!")
            return
    
    def show(self):
        """نمایش دیالوگ"""
        template = self.app.template_manager.get_template(self.template_name)
        if not template:
            messagebox.showerror("Error", f"Template '{self.template_name}' not found!")
            return
        
        self.devices_list = template.get('devices', []).copy()
        
        # ===== انتقال quantity از components به device =====
        for device in self.devices_list:
            if 'components' in device:
                # اگر quantity در سطح device نیست، از components بگیر
                if 'quantity' not in device:
                    device['quantity'] = sum(comp.get('quantity', 1) for comp in device['components'])
                # اگر di/do/ai/ao در سطح device نیست، از components بگیر
                if 'di' not in device:
                    device['di'] = sum(comp.get('io', {}).get('DI', 0) for comp in device['components'])
                if 'do' not in device:
                    device['do'] = sum(comp.get('io', {}).get('DO', 0) for comp in device['components'])
                if 'ai' not in device:
                    device['ai'] = sum(comp.get('io', {}).get('AI', 0) for comp in device['components'])
                if 'ao' not in device:
                    device['ao'] = sum(comp.get('io', {}).get('AO', 0) for comp in device['components'])
        
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"✏️ Edit Template: {self.template_name}")
        self.window.geometry("700x600")
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
            text=f"✏️ Edit Template: {self.template_name}",
            font=("Segoe UI", 14, "bold"),
            fg=COLORS['primary']
        ).pack(pady=10)
        
        # ===== فرم =====
        form_frame = tk.Frame(self.window, padx=20, pady=10)
        form_frame.pack(fill=tk.X)
        
        # نام قالب (غیرقابل تغییر)
        tk.Label(form_frame, text="Template Name:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        name_label = tk.Label(form_frame, text=self.template_name, font=("Segoe UI", 9), fg="#6c757d")
        name_label.grid(row=0, column=1, sticky="w", pady=5, padx=(0, 20))
        
        # دسته‌بندی
        tk.Label(form_frame, text="Category:", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", pady=5)
        categories = ["Mechanical", "HVAC", "Electrical", "Plumbing", "Custom"]
        category_combo = ttk.Combobox(form_frame, values=categories, width=15, state="readonly")
        category_combo.set(template.get('category', 'Custom'))
        category_combo.grid(row=0, column=3, sticky="w", pady=5)
        self.entries['category'] = category_combo
        
        # ===== لیست دستگاه‌ها =====
        devices_frame = tk.LabelFrame(
            self.window,
            text="📋 Devices in Template",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10
        )
        devices_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # نوار ابزار
        dev_toolbar = tk.Frame(devices_frame)
        dev_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        btn_add_device = tk.Button(
            dev_toolbar,
            text="➕ Add Device",
            command=self._add_device,
            bg=COLORS['success'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_add_device.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_add_device, COLORS['success'])
        
        btn_edit_device = tk.Button(
            dev_toolbar,
            text="✏️ Edit Device",
            command=self._edit_device,
            bg=COLORS['accent'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_edit_device.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_edit_device, COLORS['accent'])
        
        btn_remove_device = tk.Button(
            dev_toolbar,
            text="🗑️ Remove Device",
            command=self._remove_device,
            bg=COLORS['danger'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=12,
            pady=4,
            cursor="hand2"
        )
        btn_remove_device.pack(side=tk.LEFT, padx=2)
        create_hover_effect(btn_remove_device, COLORS['danger'])
        
        # Treeview
        tree_frame = tk.Frame(devices_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("#", "Device Type", "Quantity", "Component", "I/O", "Naming")
        self.device_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        
        col_widths = {"#": 40, "Device Type": 150, "Quantity": 60, "Component": 120, "I/O": 120, "Naming": 120}
        for col in columns:
            self.device_tree.heading(col, text=col)
            self.device_tree.column(col, width=col_widths.get(col, 80), anchor="center")
        self.device_tree.column("Device Type", anchor="w")
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.device_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.device_tree.xview)
        self.device_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.device_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self._refresh_device_list()
        
        # ===== دکمه‌ها =====
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=15)
        
        btn_save = tk.Button(
            btn_frame,
            text="💾 Save Changes",
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
    
    def _add_device(self):
        """افزودن دستگاه"""
        dialog = AddDeviceToTemplateDialog(self.window, self.app)
        device = dialog.show()
        if device:
            self.devices_list.append(device)
            self._refresh_device_list()
    
    def _edit_device(self):
        """ویرایش دستگاه انتخاب شده"""
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a device to edit.")
            return
        
        index = int(self.device_tree.item(selection[0])['values'][0]) - 1
        if 0 <= index < len(self.devices_list):
            device = self.devices_list[index]
            dialog = EditDeviceInTemplateDialog(self.window, self.app, device, index)
            updated_device = dialog.show()
            if updated_device:
                self.devices_list[index] = updated_device
                category = self.entries['category'].get()
                self.app.template_manager.edit_template(
                    name=self.template_name,
                    devices=self.devices_list,
                    category=category
                )
                self._refresh_device_list()
                messagebox.showinfo("Success", "Device updated in template!")
    
    def _remove_device(self):
        """حذف دستگاه انتخاب شده"""
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a device to remove.")
            return
        
        index = int(self.device_tree.item(selection[0])['values'][0]) - 1
        if 0 <= index < len(self.devices_list):
            del self.devices_list[index]
            self._refresh_device_list()
    
    def _refresh_device_list(self):
        """بروزرسانی لیست دستگاه‌ها"""
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        for i, device in enumerate(self.devices_list, 1):
            name = device.get('name', 'Unknown')
            
            # ===== استانداردسازی: خواندن quantity از components =====
            if 'components' in device:
                # اگر quantity در سطح device نیست، از components بگیر
                total_qty = sum(comp.get('quantity', 1) for comp in device['components'])
                device['quantity'] = total_qty  # تنظیم مجدد برای استفاده‌های بعدی
            else:
                total_qty = device.get('quantity', 1)
            
            # ===== استانداردسازی: خواندن I/O از components =====
            if 'components' in device:
                total_io = sum(
                    comp.get('io', {}).get('DI', 0) + comp.get('io', {}).get('DO', 0) +
                    comp.get('io', {}).get('AI', 0) + comp.get('io', {}).get('AO', 0)
                    for comp in device['components']
                )
            else:
                total_io = device.get('di', 0) + device.get('do', 0) + device.get('ai', 0) + device.get('ao', 0)
            
            # نمایش در جدول
            self.device_tree.insert("", "end", values=(i, name, total_qty, len(device.get('components', [])), f"Total IO: {total_io}", '-'))
    
    def _save(self):
        """ذخیره تغییرات"""
        category = self.entries['category'].get()
        
        if not self.devices_list:
            messagebox.showerror("Error", "Template must have at least one device!")
            return
        
        # ===== انتقال quantity از components به devices =====
        for device in self.devices_list:
            if 'components' in device:
                for comp in device['components']:
                    device['quantity'] = comp.get('quantity', 1)
                    device['di'] = comp.get('io', {}).get('DI', 0)
                    device['do'] = comp.get('io', {}).get('DO', 0)
                    device['ai'] = comp.get('io', {}).get('AI', 0)
                    device['ao'] = comp.get('io', {}).get('AO', 0)
            # اگر quantity در سطح بالای device وجود ندارد، آن را ست کن
            if not device.get('quantity'):
                device['quantity'] = 1
        
        success = self.app.template_manager.edit_template(
            name=self.template_name,
            devices=self.devices_list,
            category=category
        )
        
        if success:
            messagebox.showinfo("Success", f"Template '{self.template_name}' updated successfully!")
            self.window.destroy()
        else:
            messagebox.showerror("Error", "Failed to update template.")

class EditDeviceInTemplateDialog:
    """دیالوگ ویرایش دستگاه در قالب"""
    
    def __init__(self, parent, app, device: Dict, index: int):
        self.parent = parent
        self.app = app
        self.device = device.copy()
        self.index = index
        self.window = None
        self.result = None
        self.entries = {}
        self.io_entries = {}
    
    def show(self) -> Optional[Dict]:
        """نمایش دیالوگ و بازگرداندن دستگاه ویرایش شده"""
        # ===== اگر quantity در device موجود نیست، از components بخوان =====
        if 'quantity' not in self.device or self.device.get('quantity', 0) == 0:
            if 'components' in self.device:
                self.device['quantity'] = sum(comp.get('quantity', 1) for comp in self.device['components'])
            else:
                self.device['quantity'] = 1
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("✏️ Edit Device in Template")
        self.window.geometry("550x500")
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
            text=f"✏️ Edit Device #{self.index + 1}",
            font=("Segoe UI", 14, "bold"),
            fg=COLORS['primary']
        ).pack(pady=10)
        
        # ===== فرم =====
        form_frame = tk.Frame(self.window, padx=20, pady=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Device Type
        tk.Label(form_frame, text="Device Type:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        type_entry = tk.Entry(form_frame, width=30, font=("Segoe UI", 9))
        type_entry.insert(0, self.device.get('type', ''))
        type_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(0, 10))
        self.entries['type'] = type_entry
        
        # Quantity
        tk.Label(form_frame, text="Quantity:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        qty_entry = tk.Entry(form_frame, width=10, font=("Segoe UI", 9), justify="center")
        qty_entry.insert(0, str(self.device.get('quantity', 1)))
        qty_entry.grid(row=1, column=1, sticky="w", pady=5)
        self.entries['quantity'] = qty_entry
        
        # Component
        tk.Label(form_frame, text="Component:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        component_keys = self.app.component_manager.get_component_keys()
        component_combo = ttk.Combobox(form_frame, values=component_keys, width=20, state="readonly")
        component_combo.set(self.device.get('component', ''))
        component_combo.grid(row=2, column=1, sticky="w", pady=5)
        self.entries['component'] = component_combo
        
        # Naming Pattern
        tk.Label(form_frame, text="Naming Pattern:", font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        naming_entry = tk.Entry(form_frame, width=30, font=("Segoe UI", 9))
        naming_entry.insert(0, self.device.get('naming', '{type}-{n}'))
        naming_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=(0, 10))
        self.entries['naming'] = naming_entry
        
        # Description Pattern
        tk.Label(form_frame, text="Description Pattern:", font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w", pady=5)
        desc_entry = tk.Entry(form_frame, width=30, font=("Segoe UI", 9))
        desc_entry.insert(0, self.device.get('description', ''))
        desc_entry.grid(row=4, column=1, sticky="ew", pady=5, padx=(0, 10))
        self.entries['description'] = desc_entry
        
        # Positions
        tk.Label(form_frame, text="Positions (comma):", font=("Segoe UI", 9, "bold")).grid(row=5, column=0, sticky="w", pady=5)
        pos_entry = tk.Entry(form_frame, width=30, font=("Segoe UI", 9))
        pos_entry.insert(0, ", ".join(self.device.get('positions', [])))
        pos_entry.grid(row=5, column=1, sticky="ew", pady=5, padx=(0, 10))
        self.entries['positions'] = pos_entry
        
        # I/O Configuration
        io_frame = tk.LabelFrame(
            form_frame,
            text="I/O Configuration",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=10
        )
        io_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
        
        io = self.device.get('io', {})
        io_types = ["DI", "DO", "AI", "AO"]
        for i, io_type in enumerate(io_types):
            tk.Label(io_frame, text=f"{io_type}:", font=("Segoe UI", 9)).grid(row=0, column=i*2, sticky="e", padx=(0, 5))
            entry = tk.Entry(io_frame, width=6, font=("Segoe UI", 9), justify="center")
            entry.insert(0, str(io.get(io_type, 0)))
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
            command=self._cancel,
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
        
        self.window.wait_window()
        return self.result
    
    def _save(self):
        """ذخیره تغییرات"""
        device_type = self.entries['type'].get().strip()
        quantity = int(self.entries['quantity'].get() or 1)
        component = self.entries['component'].get()
        naming = self.entries['naming'].get().strip()
        description = self.entries['description'].get().strip()
        positions_text = self.entries['positions'].get().strip()
        
        if not device_type:
            messagebox.showerror("Error", "Device type is required!")
            return
        
        positions = [p.strip() for p in positions_text.split(',') if p.strip()]
        
        try:
            di = int(self.io_entries["DI"].get() or 0)
            do = int(self.io_entries["DO"].get() or 0)
            ai = int(self.io_entries["AI"].get() or 0)
            ao = int(self.io_entries["AO"].get() or 0)
        except ValueError:
            messagebox.showerror("Error", "I/O values must be numbers!")
            return
        
        # ===== دریافت I/O پیش‌فرض از ComponentManager =====
        default_io = self.app.component_manager.get_default_io(component)
        
        # اگر کاربر مقدار I/O را دستی وارد نکرده است، از پیش‌فرض استفاده کن
        if di == 0 and do == 0 and ai == 0 and ao == 0:
            di = default_io.get('DI', 0)
            do = default_io.get('DO', 0)
            ai = default_io.get('AI', 0)
            ao = default_io.get('AO', 0)
        
        self.result = {
            'name': device_type,
            'description': description,
            'quantity': max(1, quantity),  # ✅ ذخیره در سطح device
            'component': component,
            'components': [
                {
                    'type': device_type,
                    'quantity': max(1, quantity),  # ✅ ذخیره در سطح component
                    'component': component,
                    'naming': naming or "{type}-{n}",
                    'description': description or "",
                    'positions': positions,
                    'io': {'DI': di, 'DO': do, 'AI': ai, 'AO': ao}
                }
            ]
        }
        
        self.window.destroy()
    
    def _cancel(self):
        """انصراف"""
        self.result = None
        self.window.destroy()