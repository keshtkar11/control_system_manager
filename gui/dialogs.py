"""دیالوگ‌های برنامه - مدیریت پروژه، بخش، دستگاه و برچسب‌ها"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, scrolledtext
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
import os
import json

from core import (
    Project, ProjectSection, Motor,
    COMPONENT_LABELS, IO_CALCULATION, CABLE_SIZE,
    COLORS, LIMITS,
    validate_device_name, validate_io_value,
    validate_section_name, validate_project_name
)
from gui.theme import create_tooltip, create_hover_effect


# ==================== دیالوگ مدیریت پروژه ====================

class ProjectManagerDialog:
    """دیالوگ مدیریت پروژه‌ها"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = None
        self.listbox = None
    
    def show(self):
        """نمایش دیالوگ"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("📁 Project Manager")
        self.window.geometry("550x450")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # مرکز کردن پنجره
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # عنوان
        tk.Label(
            self.window,
            text="📁 Project Manager",
            font=("Segoe UI", 14, "bold"),
            fg=COLORS['primary']
        ).pack(pady=10)
        
        # فریم لیست
        list_frame = tk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 10),
            selectmode=tk.SINGLE,
            height=12
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        self._refresh_list()
        
        # دکمه‌ها
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=15)
        
        buttons = [
            ("➕ New", self._new_project, COLORS['success']),
            ("📂 Load", self._load_project, COLORS['accent']),
            ("✏️ Edit", self._edit_project, COLORS['warning']),
            ("🗑️ Delete", self._delete_project, COLORS['danger']),
            ("❌ Close", self.window.destroy, COLORS['secondary'])
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=text,
                command=command,
                bg=color,
                fg=COLORS['white'],
                font=("Segoe UI", 9, "bold"),
                relief='flat',
                padx=15,
                pady=6,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=3)
            create_hover_effect(btn, color)
        
        # دابل کلیک برای بارگذاری
        self.listbox.bind("<Double-1>", lambda e: self._load_project())
    
    def _refresh_list(self):
        """بروزرسانی لیست پروژه‌ها"""
        self.listbox.delete(0, tk.END)
        for name, project in self.app.projects.items():
            stats = project.get_statistics()
            display_text = f"{name}  |  Sections: {stats['total_sections']}  |  Devices: {stats['total_devices']}"
            self.listbox.insert(tk.END, display_text)
            
            # هایلایت پروژه جاری
            if name == self.app.current_project_name:
                self.listbox.selection_set(tk.END)
    
    def _get_selected_project(self) -> Optional[str]:
        """دریافت نام پروژه انتخاب شده"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a project.")
            return None
        display_text = self.listbox.get(selection[0])
        return display_text.split("  |")[0].strip()
    
    def _new_project(self):
        """ایجاد پروژه جدید"""
        self.window.destroy()
        self.app._new_project()
    
    def _load_project(self):
        """بارگذاری پروژه انتخاب شده"""
        name = self._get_selected_project()
        if name:
            # استفاده از متد switch_to_project
            if hasattr(self.app, 'switch_to_project'):
                self.app.switch_to_project(name)
            else:
                # اگر متد وجود ندارد، مستقیماً تغییر دهید
                self.app.current_project_name = name
                project = self.app.projects.get(name)
                if project and project.sections:
                    self.app.current_section_name = project.sections[0].name
                self.app._load_component_labels()
                self.app._refresh_ui()
            self.window.destroy()
    
    def _edit_project(self):
        """ویرایش پروژه انتخاب شده"""
        name = self._get_selected_project()
        if name:
            project = self.app.projects.get(name)
            if project:
                self.window.destroy()
                self.app._edit_project_info()
    
    def _delete_project(self):
        """حذف پروژه انتخاب شده"""
        name = self._get_selected_project()
        if not name:
            return
        
        if len(self.app.projects) <= 1:
            messagebox.showwarning("Warning", "Cannot delete the last project.")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete project '{name}' permanently?"):
            # حذف از دیتابیس
            self.app.db.delete_project(name)
            # حذف از حافظه
            del self.app.projects[name]
            # انتخاب پروژه بعدی
            if name == self.app.current_project_name:
                first = next(iter(self.app.projects))
                self.app.switch_to_project(first)
            self._refresh_list()
            messagebox.showinfo("Success", f"Project '{name}' deleted.")


# ==================== دیالوگ مدیریت بخش ====================

class SectionManagerDialog:
    """دیالوگ مدیریت بخش‌های پروژه"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = None
        self.listbox = None
    
    def show(self):
        """نمایش دیالوگ"""
        project = self.app.get_current_project()
        if not project:
            messagebox.showwarning("Warning", "No project selected!")
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"📂 Manage Sections - {project.name}")
        self.window.geometry("500x400")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # مرکز کردن
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # عنوان
        tk.Label(
            self.window,
            text=f"📂 Sections - {project.name}",
            font=("Segoe UI", 14, "bold"),
            fg=COLORS['primary']
        ).pack(pady=10)
        
        # لیست بخش‌ها
        list_frame = tk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 10),
            selectmode=tk.SINGLE,
            height=10
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        self._refresh_list()
        
        # دکمه‌ها
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=15)
        
        buttons = [
            ("➕ Add", self._add_section, COLORS['success']),
            ("✏️ Edit", self._edit_section, COLORS['warning']),
            ("🗑️ Delete", self._delete_section, COLORS['danger']),
            ("❌ Close", self.window.destroy, COLORS['secondary'])
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=text,
                command=command,
                bg=color,
                fg=COLORS['white'],
                font=("Segoe UI", 9, "bold"),
                relief='flat',
                padx=15,
                pady=6,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=3)
            create_hover_effect(btn, color)
    
    def _refresh_list(self):
        """بروزرسانی لیست بخش‌ها"""
        self.listbox.delete(0, tk.END)
        project = self.app.get_current_project()
        if project:
            for section in project.sections:
                device_count = len(section.devices)
                display_text = f"{section.name}  |  Devices: {device_count}"
                self.listbox.insert(tk.END, display_text)
                
                if section.name == self.app.current_section_name:
                    self.listbox.selection_set(tk.END)
    
    def _get_selected_section(self) -> Optional[str]:
        """دریافت نام بخش انتخاب شده"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a section.")
            return None
        display_text = self.listbox.get(selection[0])
        return display_text.split("  |")[0].strip()
    
    def _add_section(self):
        """افزودن بخش جدید"""
        project = self.app.get_current_project()
        if not project:
            return
        
        name = simpledialog.askstring(
            "New Section",
            "Enter section name:",
            parent=self.window
        )
        if not name or not name.strip():
            return
        
        name = name.strip()
        if project.get_section_by_name(name):
            messagebox.showwarning("Warning", "Section already exists!")
            return
        
        description = simpledialog.askstring(
            "Section Description",
            "Enter description (optional):",
            parent=self.window
        )
        
        self.app._save_state()
        project.add_section(name, description or "")
        self.app._save_project()
        self.app._refresh_ui()
        self._refresh_list()
        messagebox.showinfo("Success", f"Section '{name}' added.")
    
    def _edit_section(self):
        """ویرایش بخش انتخاب شده"""
        old_name = self._get_selected_section()
        if not old_name:
            return
        
        project = self.app.get_current_project()
        if not project:
            return
        
        section = project.get_section_by_name(old_name)
        if not section:
            return
        
        new_name = simpledialog.askstring(
            "Edit Section",
            "Enter new section name:",
            initialvalue=old_name,
            parent=self.window
        )
        if not new_name or not new_name.strip():
            return
        
        new_name = new_name.strip()
        if new_name != old_name and project.get_section_by_name(new_name):
            messagebox.showwarning("Warning", "Section already exists!")
            return
        
        self.app._save_state()
        section.name = new_name
        if self.app.current_section_name == old_name:
            self.app.current_section_name = new_name
        
        self.app._save_project()
        self.app._refresh_ui()
        self._refresh_list()
        messagebox.showinfo("Success", "Section updated.")
    
    def _delete_section(self):
        """حذف بخش انتخاب شده"""
        name = self._get_selected_section()
        if not name:
            return
        
        project = self.app.get_current_project()
        if not project or len(project.sections) <= 1:
            messagebox.showwarning("Warning", "Cannot delete the last section.")
            return
        
        section = project.get_section_by_name(name)
        if len(section.devices) > 0:
            if not messagebox.askyesno(
                "Confirm Delete",
                f"Section '{name}' has {len(section.devices)} devices. Delete anyway?"
            ):
                return
        
        self.app._save_state()
        project.delete_section(name)
        if self.app.current_section_name == name:
            self.app.current_section_name = project.sections[0].name
        
        self.app._save_project()
        self.app._refresh_ui()
        self._refresh_list()
        messagebox.showinfo("Success", f"Section '{name}' deleted.")

class DeviceReorderDialog:
    """دیالوگ برای مرتب‌سازی دستی دستگاه‌ها"""
    
    def __init__(self, parent, app, section):
        self.parent = parent
        self.app = app
        self.section = section
        self.window = None
        self.listbox = None
        self.devices = section.devices.copy()  # کپی برای ویرایش
    
    def show(self):
        """نمایش دیالوگ مرتب‌سازی"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("🔄 Reorder Devices")
        self.window.geometry("400x500")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # مرکز کردن
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        tk.Label(
            self.window,
            text="🔄 Reorder Devices",
            font=("Segoe UI", 14, "bold"),
            fg=COLORS['primary']
        ).pack(pady=10)
        
        tk.Label(
            self.window,
            text="Select a device and use buttons to move it",
            font=("Segoe UI", 10),
            fg=COLORS['secondary']
        ).pack()
        
        # لیست
        list_frame = tk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 10),
            selectmode=tk.SINGLE,
            height=12
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        self._refresh_list()
        
        # دکمه‌های جابجایی
        move_frame = tk.Frame(self.window)
        move_frame.pack(pady=10)
        
        tk.Button(
            move_frame,
            text="⬆️ Up",
            command=self._move_up,
            bg=COLORS['accent'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            move_frame,
            text="⬇️ Down",
            command=self._move_down,
            bg=COLORS['accent'],
            fg=COLORS['white'],
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=15,
            pady=5,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        # دکمه‌های اصلی
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=15)
        
        tk.Button(
            btn_frame,
            text="💾 Save Order",
            command=self._save_order,
            bg=COLORS['success'],
            fg=COLORS['white'],
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=25,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="❌ Cancel",
            command=self.window.destroy,
            bg=COLORS['danger'],
            fg=COLORS['white'],
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=25,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
    
    def _refresh_list(self):
        """بروزرسانی لیست"""
        self.listbox.delete(0, tk.END)
        for i, device in enumerate(self.devices):
            name = device.Name or "Unnamed"
            self.listbox.insert(tk.END, f"{i+1:2d}. {name}")
    
    def _move_up(self):
        """جابجایی به بالا"""
        selection = self.listbox.curselection()
        if not selection or selection[0] == 0:
            return
        
        idx = selection[0]
        self.devices[idx], self.devices[idx-1] = self.devices[idx-1], self.devices[idx]
        self._refresh_list()
        self.listbox.selection_set(idx - 1)
    
    def _move_down(self):
        """جابجایی به پایین"""
        selection = self.listbox.curselection()
        if not selection or selection[0] >= len(self.devices) - 1:
            return
        
        idx = selection[0]
        self.devices[idx], self.devices[idx+1] = self.devices[idx+1], self.devices[idx]
        self._refresh_list()
        self.listbox.selection_set(idx + 1)
    
    def _save_order(self):
        """ذخیره ترتیب جدید"""
        self.section.devices = self.devices
        self.app._save_project()
        self.app._refresh_ui()
        self.window.destroy()
        messagebox.showinfo("Success", "Device order updated successfully!")
        
# ==================== دیالوگ ویرایش دستگاه ====================

class DeviceEditDialog:
    """دیالوگ افزودن/ویرایش دستگاه"""
    
    def __init__(self, parent, app, motor: Optional[Motor] = None,
                 section: Optional[ProjectSection] = None, is_new: bool = False):
        self.parent = parent
        self.app = app
        self.motor = motor or Motor()
        self.section = section
        self.is_new = is_new
        self.window = None
        self.entries = {}
        self.component_entries = {}
        self.suggestions_panel = None
        self.suggestion_timer = None
        self.current_suggestions = []
    
    def show(self):
        """نمایش دیالوگ"""
        title = "➕ Add Device" if self.is_new else f"✏️ Edit Device: {self.motor.Name or 'Unnamed'}"
        
        self.window = tk.Toplevel(self.parent)
        self.window.title(title)
        self.window.geometry("700x850")  # افزایش ارتفاع برای پنل پیشنهادات
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # مرکز کردن
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # ===== فریم اصلی با اسکرول =====
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        canvas = tk.Canvas(main_frame, bg=COLORS['background'])
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['background'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ===== اطلاعات پایه =====
        self._create_basic_fields(scrollable_frame)
        
        # ===== پنل پیشنهادات هوشمند =====
        self._create_suggestions_panel(scrollable_frame)
        
        # ===== کامپوننت‌ها =====
        self._create_component_fields(scrollable_frame)
        
        # ===== خلاصه I/O =====
        self._create_io_summary(scrollable_frame)
        
        # ===== دکمه‌ها =====
        btn_frame = tk.Frame(self.window, bg=COLORS['background'])
        btn_frame.pack(pady=15)
        
        tk.Button(
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
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="❌ Cancel",
            command=self.window.destroy,
            bg=COLORS['danger'],
            fg=COLORS['white'],
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=25,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        # محاسبه اولیه
        self._calculate_io()
    
    def _create_suggestions_panel(self, parent):
        """ایجاد پنل پیشنهادات هوشمند"""
        frame = tk.LabelFrame(
            parent,
            text="💡 پیشنهادات هوشمند",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS['background'],
            padx=5,
            pady=5
        )
        frame.pack(fill=tk.X, pady=(0, 10))
        
        self.suggestions_panel = tk.Frame(frame, bg="#F8F9FA", height=100)
        self.suggestions_panel.pack(fill=tk.X, padx=5, pady=5)
        
        # پیام اولیه
        tk.Label(
            self.suggestions_panel,
            text="🔍 در حال شناسایی نوع تجهیز... (نام یا توضیحات را وارد کنید)",
            font=("Segoe UI", 9, "italic"),
            fg="#7F8C8D",
            bg="#F8F9FA"
        ).pack(pady=10, padx=10)
        
        # ذخیره پیشنهادات فعلی
        self.current_suggestions = []
    
    def _on_name_description_changed(self, *args):
        """وقتی نام یا توضیحات تغییر می‌کند، پیشنهادات را به روز کن"""
        # تاخیر برای جلوگیری از درخواست‌های مکرر (Debounce)
        if self.suggestion_timer:
            try:
                self.window.after_cancel(self.suggestion_timer)
            except:
                pass
        
        self.suggestion_timer = self.window.after(500, self._update_live_suggestions)
    
    def _update_live_suggestions(self):
        """به روز رسانی پیشنهادات زنده"""
        device_name = self.entries["Name"].get().strip()
        description = self.entries["Description"].get().strip()
        info = self.entries["INFO"].get().strip()  # ✅ اضافه شد
        
        # اگر هر سه خالی هستند، پنل را مخفی کن
        if not device_name and not description and not info:
            if self.suggestions_panel:
                self._show_empty_suggestions()
            return
        
        # دریافت پیشنهادات از LearningEngine
        section_name = self.section.name if self.section else ""
        result = self.app.learning_engine.get_live_suggestions(device_name, description, info, section_name)
        
        # نمایش پنل پیشنهادات
        self._show_suggestions_panel(result)
    
    def _show_empty_suggestions(self):
        """نمایش پیام خالی"""
        if not self.suggestions_panel:
            return
        
        # پاک کردن محتوای قبلی
        for widget in self.suggestions_panel.winfo_children():
            widget.destroy()
        
        tk.Label(
            self.suggestions_panel,
            text="🔍 در حال شناسایی نوع تجهیز... (نام یا توضیحات را وارد کنید)",
            font=("Segoe UI", 9, "italic"),
            fg="#7F8C8D",
            bg="#F8F9FA"
        ).pack(pady=10, padx=10)
        
        self.current_suggestions = []
    
    def _show_suggestions_panel(self, result: Dict[str, Any]):
        """نمایش پنل پیشنهادات"""
        if not self.suggestions_panel:
            return
        
        # پاک کردن محتوای قبلی
        for widget in self.suggestions_panel.winfo_children():
            widget.destroy()
        
        if not result.get('equipment_type'):
            # نوع تجهیز شناسایی نشد - نمایش راهنما
            tk.Label(
                self.suggestions_panel,
                text="🔍 نوع تجهیز شناسایی نشد...\n\n"
                    "💡 راهنما:\n"
                    "• نام دستگاه را وارد کنید (مثلاً PU-101)\n"
                    "• توضیحات را وارد کنید (مثلاً Boiler Circulation Pump)\n"
                    "• یا نام بخش را انتخاب کنید (مثلاً Boiler Room)",
                font=("Segoe UI", 9),
                fg="#7F8C8D",
                bg="#F8F9FA",
                justify=tk.LEFT
            ).pack(pady=10, padx=10)
            self.current_suggestions = []
            return
        
        # نمایش نوع تجهیز
        equip_type = result['equipment_type']
        suggestions = result['suggestions']
        
        # ذخیره پیشنهادات
        self.current_suggestions = suggestions
        
        # هدر
        header_frame = tk.Frame(self.suggestions_panel, bg="#2C3E50")
        header_frame.pack(fill=tk.X)
        
        tk.Label(
            header_frame,
            text=f"💡 پیشنهادات: {equip_type}",
            font=("Segoe UI", 10, "bold"),
            fg="white",
            bg="#2C3E50",
            pady=5
        ).pack(padx=10, pady=5)
        
        # لیست پیشنهادات
        if suggestions:
            for suggestion in suggestions:
                comp_frame = tk.Frame(self.suggestions_panel, bg="#F8F9FA")
                comp_frame.pack(fill=tk.X, padx=5, pady=2)
                
                # نام کامپوننت
                tk.Label(
                    comp_frame,
                    text=f"• {suggestion['label']} ({suggestion['component']})",
                    font=("Segoe UI", 9),
                    bg="#F8F9FA",
                    anchor="w"
                ).pack(side=tk.LEFT, padx=5, pady=2)
                
                # تعداد
                tk.Label(
                    comp_frame,
                    text=f"× {suggestion['qty']}",
                    font=("Segoe UI", 9, "bold"),
                    fg="#3498DB",
                    bg="#F8F9FA"
                ).pack(side=tk.RIGHT, padx=5, pady=2)
                
                # نمایش I/O
                io_text = f"DI:{suggestion['io'].get('DI',0)} DO:{suggestion['io'].get('DO',0)} AI:{suggestion['io'].get('AI',0)} AO:{suggestion['io'].get('AO',0)}"
                tk.Label(
                    comp_frame,
                    text=io_text,
                    font=("Segoe UI", 8),
                    fg="#7F8C8D",
                    bg="#F8F9FA"
                ).pack(side=tk.RIGHT, padx=5, pady=2)
            
            # دکمه اعمال
            apply_btn = tk.Button(
                self.suggestions_panel,
                text="✅ اعمال همه پیشنهادات",
                command=self._apply_suggestions,
                bg="#27AE60",
                fg="white",
                font=("Segoe UI", 9, "bold"),
                relief='flat',
                padx=10,
                pady=5,
                cursor="hand2"
            )
            apply_btn.pack(fill=tk.X, padx=10, pady=8)
        else:
            tk.Label(
                self.suggestions_panel,
                text="هیچ پیشنهادی یافت نشد",
                font=("Segoe UI", 9, "italic"),
                fg="#7F8C8D",
                bg="#F8F9FA"
            ).pack(pady=10, padx=10)
    
    def _apply_suggestions(self):
        """اعمال پیشنهادات به دستگاه"""
        if not self.current_suggestions:
            return
        
        applied_count = 0
        for suggestion in self.current_suggestions:
            comp_key = suggestion['component']
            if comp_key in self.component_entries:
                # اگر مقدار فعلی 0 است، پیشنهاد را اعمال کن
                current_qty = self.component_entries[comp_key]["qty"].get()
                if current_qty == "0" or not current_qty:
                    self.component_entries[comp_key]["qty"].set(str(suggestion['qty']))
                    applied_count += 1
        
        # محاسبه مجدد I/O
        self._calculate_io()
        
        if applied_count > 0:
            messagebox.showinfo(
                "✅ پیشنهادات اعمال شد",
                f"{applied_count} کامپوننت با موفقیت اعمال شد!"
            )
        else:
            messagebox.showinfo(
                "ℹ️",
                "همه کامپوننت‌ها قبلاً تنظیم شده‌اند."
            )
    
    def _create_basic_fields(self, parent):
        """ایجاد فیلدهای اطلاعات پایه"""
        frame = tk.LabelFrame(
            parent,
            text="📋 Device Information",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS['background'],
            padx=10,
            pady=10
        )
        frame.pack(fill=tk.X, pady=(0, 10))
        
        fields = [
            ("Name:", "Name", 30),
            ("Description:", "Description", 30),
            ("Device:", "INFO", 30),
            
        ]
        
        for i, (label, attr, width) in enumerate(fields):
            tk.Label(
                frame,
                text=label,
                font=("Segoe UI", 9, "bold"),
                bg=COLORS['background']
            ).grid(row=i, column=0, sticky="w", pady=3, padx=(0, 5))
            
            entry = tk.Entry(frame, width=width, font=("Segoe UI", 9))
            entry.insert(0, getattr(self.motor, attr) or "")
            entry.grid(row=i, column=1, sticky="ew", pady=3)
            self.entries[attr] = entry
        
        frame.columnconfigure(1, weight=1)
        
        # ✅ اتصال رویداد تغییر برای پیشنهاد زنده
        self.entries["Name"].bind("<KeyRelease>", self._on_name_description_changed)
        self.entries["Description"].bind("<KeyRelease>", self._on_name_description_changed)
        self.entries["INFO"].bind("<KeyRelease>", self._on_name_description_changed)
    
    def _create_component_fields(self, parent):
        """ایجاد فیلدهای کامپوننت‌ها با Tooltip راهنما - شامل کامپوننت‌های سفارشی"""
        frame = tk.LabelFrame(
            parent,
            text="🔧 Components",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS['background'],
            padx=10,
            pady=10
        )
        frame.pack(fill=tk.X, pady=(0, 10))
        
        # ===== دریافت لیست کامل کامپوننت‌ها (پیش‌فرض + سفارشی) =====
        all_components = self.app.component_manager.get_all_active_components()
        
        # هدر
        header_frame = tk.Frame(frame, bg=COLORS['secondary'])
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        headers = ["Component", "Qty", "DI", "DO", "AI", "AO", ""]
        widths = [25, 8, 8, 8, 8, 8, 4]
        
        for i, (text, width) in enumerate(zip(headers, widths)):
            tk.Label(
                header_frame,
                text=text,
                font=("Segoe UI", 9, "bold"),
                fg=COLORS['white'],
                bg=COLORS['secondary'],
                width=width,
                anchor="center"
            ).pack(side=tk.LEFT, padx=2, pady=4)
        
        # کامپوننت‌ها
        for field, labels in all_components.items():
            row_frame = tk.Frame(frame, bg=COLORS['light'] if len(self.component_entries) % 2 == 0 else COLORS['background'])
            row_frame.pack(fill=tk.X, pady=1)
            
            # ===== نام کامپوننت با Tooltip =====
            name_label = tk.Label(
                row_frame,
                text=f"{labels.get('en', field)} ({field})",
                font=("Segoe UI", 8),
                bg=row_frame["bg"],
                width=25,
                anchor="w",
                cursor="hand2"  # نشانگر دست برای نشان دادن تعامل
            )
            name_label.pack(side=tk.LEFT, padx=2)
            
            # ✅ Tooltip برای نام کامپوننت
            def show_io_tooltip(event, f=field, rf=row_frame):
                from core.constants import IO_REFERENCE
                if f in IO_REFERENCE:
                    ref = IO_REFERENCE[f]
                    tooltip_text = f"{ref['label']} ({f})\n"
                    tooltip_text += "-" * 20 + "\n"
                    if ref.get('di'):
                        tooltip_text += f"DI: {', '.join(ref['di'])}\n"
                    if ref.get('do'):
                        tooltip_text += f"DO: {', '.join(ref['do'])}\n"
                    if ref.get('ai'):
                        tooltip_text += f"AI: {', '.join(ref['ai'])}\n"
                    if ref.get('ao'):
                        tooltip_text += f"AO: {', '.join(ref['ao'])}"
                    
                    # ایجاد Tooltip
                    tooltip = tk.Toplevel(rf)
                    tooltip.wm_overrideredirect(True)
                    tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                    label = tk.Label(
                        tooltip,
                        text=tooltip_text,
                        bg="#2C3E50",
                        fg="white",
                        font=("Segoe UI", 7),
                        relief="solid",
                        bd=1,
                        padx=8,
                        pady=5,
                        justify=tk.LEFT
                    )
                    label.pack()
                    
                    # بستن خودکار با خروج موس
                    def hide_tooltip(e=None):
                        tooltip.destroy()
                    rf.bind("<Leave>", hide_tooltip)
                    # بستن خودکار بعد از 5 ثانیه
                    tooltip.after(3000, tooltip.destroy)
            
            name_label.bind("<Enter>", show_io_tooltip)
            
            # ===== فیلد تعداد =====
            qty_var = tk.StringVar(value=str(getattr(self.motor, field, 0)))
            qty_entry = tk.Entry(
                row_frame,
                textvariable=qty_var,
                width=8,
                font=("Segoe UI", 9),
                justify="center"
            )
            qty_entry.pack(side=tk.LEFT, padx=2)
            
            # ===== فیلدهای I/O (فقط خواندنی) =====
            io_vars = {}
            for io_type in ["DI", "DO", "AI", "AO"]:
                io_var = tk.StringVar(value="0")
                io_entry = tk.Entry(
                    row_frame,
                    textvariable=io_var,
                    width=8,
                    font=("Segoe UI", 8),
                    justify="center",
                    state="readonly",
                    readonlybackground="#f0f0f0"
                )
                io_entry.pack(side=tk.LEFT, padx=2)
                io_vars[io_type] = io_var
            
            # ===== دکمه راهنما (ℹ️) =====
            def show_guide(f=field):
                from core.constants import IO_REFERENCE
                if f not in IO_REFERENCE:
                    messagebox.showinfo("Information", f"No guide available for {f}")
                    return
                
                ref = IO_REFERENCE[f]
                guide_text = f"📖 {ref['label']} ({f}) I/O Guide\n"
                guide_text += "=" * 40 + "\n\n"
                
                if ref.get('di'):
                    guide_text += "🔵 Digital Inputs (DI):\n"
                    for item in ref['di']:
                        guide_text += f"   • {item}\n"
                    guide_text += "\n"
                
                if ref.get('do'):
                    guide_text += "🟢 Digital Outputs (DO):\n"
                    for item in ref['do']:
                        guide_text += f"   • {item}\n"
                    guide_text += "\n"
                
                if ref.get('ai'):
                    guide_text += "🟡 Analog Inputs (AI):\n"
                    for item in ref['ai']:
                        guide_text += f"   • {item}\n"
                    guide_text += "\n"
                
                if ref.get('ao'):
                    guide_text += "🔴 Analog Outputs (AO):\n"
                    for item in ref['ao']:
                        guide_text += f"   • {item}\n"
                    guide_text += "\n"
                
                messagebox.showinfo(f"I/O Guide - {ref['label']}", guide_text)
            
            help_btn = tk.Button(
                row_frame,
                text="ℹ️",
                command=show_guide,
                bg="#3498DB",
                fg="white",
                font=("Segoe UI", 8, "bold"),
                relief='flat',
                width=3,
                cursor="hand2"
            )
            help_btn.pack(side=tk.LEFT, padx=2)
            
            # ذخیره مراجع
            self.component_entries[field] = {
                "qty": qty_var,
                "io": io_vars,
                "qty_entry": qty_entry,
                "default_io": labels.get('io', {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0})  # ✅ ذخیره I/O پیش‌فرض
            }
            
            # رویداد تغییر
            qty_var.trace("w", lambda *args, f=field: self._on_component_change(f))
        
        # ===== دکمه‌های کمکی =====
        btn_frame = tk.Frame(frame, bg=COLORS['background'])
        btn_frame.pack(fill=tk.X, pady=8)
        
        tk.Button(
            btn_frame,
            text="🔄 Apply Default I/O",
            command=self._apply_default_io,
            bg=COLORS['accent'],
            fg=COLORS['white'],
            font=("Segoe UI", 8, "bold"),
            relief='flat',
            padx=10,
            pady=4,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            btn_frame,
            text="🗑️ Reset All",
            command=self._reset_all,
            bg=COLORS['warning'],
            fg=COLORS['white'],
            font=("Segoe UI", 8, "bold"),
            relief='flat',
            padx=10,
            pady=4,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)
        
        # ===== دکمه نمایش همه راهنماها =====
        def show_all_guides():
            from core.constants import IO_REFERENCE
            all_text = "📖 COMPLETE I/O REFERENCE GUIDE\n"
            all_text += "=" * 50 + "\n\n"
            
            for field, ref in sorted(IO_REFERENCE.items()):
                label = ref.get('label', field)
                all_text += f"🔹 {label} ({field})\n"
                if ref.get('di'):
                    all_text += f"   DI: {', '.join(ref['di'])}\n"
                if ref.get('do'):
                    all_text += f"   DO: {', '.join(ref['do'])}\n"
                if ref.get('ai'):
                    all_text += f"   AI: {', '.join(ref['ai'])}\n"
                if ref.get('ao'):
                    all_text += f"   AO: {', '.join(ref['ao'])}\n"
                all_text += "\n"
            
            # نمایش در پنجره جدید
            guide_win = tk.Toplevel(self.window)
            guide_win.title("📖 I/O Reference Guide")
            guide_win.geometry("550x500")
            guide_win.transient(self.window)
            guide_win.grab_set()
            
            text_area = scrolledtext.ScrolledText(
                guide_win,
                wrap=tk.WORD,
                font=("Courier New", 10)
            )
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_area.insert(tk.END, all_text)
            text_area.config(state="disabled")
            
            tk.Button(
                guide_win,
                text="Close",
                command=guide_win.destroy,
                bg=COLORS['secondary'],
                fg=COLORS['white'],
                font=("Segoe UI", 9, "bold"),
                relief='flat',
                padx=20,
                pady=5
            ).pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="📖 Show All Guide",
            command=show_all_guides,
            bg=COLORS['secondary'],
            fg=COLORS['white'],
            font=("Segoe UI", 8, "bold"),
            relief='flat',
            padx=10,
            pady=4,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)

    def _create_io_summary(self, parent):
        """ایجاد خلاصه I/O"""
        frame = tk.LabelFrame(
            parent,
            text="📊 I/O Summary",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS['background'],
            padx=10,
            pady=10
        )
        frame.pack(fill=tk.X)
        
        self.io_labels = {}
        io_types = ["DI", "DO", "AI", "AO"]
        
        for i, io_type in enumerate(io_types):
            tk.Label(
                frame,
                text=f"{io_type}:",
                font=("Segoe UI", 9, "bold"),
                bg=COLORS['background']
            ).grid(row=0, column=i*2, sticky="e", padx=(10, 2))
            
            label = tk.Label(
                frame,
                text="0",
                font=("Segoe UI", 10, "bold"),
                fg=COLORS['accent'],
                bg=COLORS['background'],
                width=6,
                relief="sunken",
                anchor="center"
            )
            label.grid(row=0, column=i*2+1, sticky="w", padx=(0, 10))
            self.io_labels[io_type] = label
        
        # مجموع
        tk.Label(
            frame,
            text="Total:",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS['background']
        ).grid(row=1, column=0, sticky="e", padx=(10, 2))
        
        self.total_label = tk.Label(
            frame,
            text="0",
            font=("Segoe UI", 11, "bold"),
            fg=COLORS['success'],
            bg=COLORS['background'],
            width=6,
            relief="sunken",
            anchor="center"
        )
        self.total_label.grid(row=1, column=1, sticky="w", padx=(0, 10))
    
    def _on_component_change(self, field: str):
        """تغییر در یک کامپوننت"""
        self._calculate_io()

    def _show_guide(self):
        """نمایش راهنمای I/O برای کامپوننت انتخاب شده"""
        from core.constants import IO_REFERENCE
        
        # دریافت کامپوننت انتخاب شده
        selected_component = None
        for field, data in self.component_entries.items():
            if int(data["qty"].get() or 0) > 0:
                selected_component = field
                break
        
        if not selected_component:
            messagebox.showinfo("Information", "Please select a component first.")
            return
        
        if selected_component not in IO_REFERENCE:
            messagebox.showinfo("Information", f"No guide available for {selected_component}")
            return
        
        ref = IO_REFERENCE[selected_component]
        guide_text = f"📖 {ref['label']} ({selected_component}) I/O Guide\n"
        guide_text += "=" * 40 + "\n\n"
        
        if ref.get('di'):
            guide_text += "🔵 Digital Inputs (DI):\n"
            for item in ref['di']:
                guide_text += f"   • {item}\n"
            guide_text += "\n"
        
        if ref.get('do'):
            guide_text += "🟢 Digital Outputs (DO):\n"
            for item in ref['do']:
                guide_text += f"   • {item}\n"
            guide_text += "\n"
        
        if ref.get('ai'):
            guide_text += "🟡 Analog Inputs (AI):\n"
            for item in ref['ai']:
                guide_text += f"   • {item}\n"
            guide_text += "\n"
        
        if ref.get('ao'):
            guide_text += "🔴 Analog Outputs (AO):\n"
            for item in ref['ao']:
                guide_text += f"   • {item}\n"
            guide_text += "\n"
        
        messagebox.showinfo(f"I/O Guide - {ref['label']}", guide_text)
    
    def _calculate_io(self):
        """محاسبه I/O از کامپوننت‌ها (شامل کامپوننت‌های سفارشی)"""
        total_di = total_do = total_ai = total_ao = 0
        
        for field, data in self.component_entries.items():
            try:
                qty = int(data["qty"].get() or 0)
                if qty > 0:
                    # اگر کامپوننت در IO_CALCULATION وجود دارد، از آن استفاده کن
                    if field in IO_CALCULATION:
                        config = IO_CALCULATION[field]
                        di = qty * config.get("DI", 0)
                        do = qty * config.get("DO", 0)
                        ai = qty * config.get("AI", 0)
                        ao = qty * config.get("AO", 0)
                    else:
                        # برای کامپوننت‌های سفارشی، از ComponentManager استفاده کن
                        default_io = data.get("default_io", self.app.component_manager.get_default_io(field))
                        di = qty * default_io.get('DI', 0)
                        do = qty * default_io.get('DO', 0)
                        ai = qty * default_io.get('AI', 0)
                        ao = qty * default_io.get('AO', 0)
                    
                    total_di += di
                    total_do += do
                    total_ai += ai
                    total_ao += ao
                    
                    # بروزرسانی فیلدهای I/O
                    data["io"]["DI"].set(str(di))
                    data["io"]["DO"].set(str(do))
                    data["io"]["AI"].set(str(ai))
                    data["io"]["AO"].set(str(ao))
                else:
                    # Reset I/O fields if qty is 0
                    for io_type in ["DI", "DO", "AI", "AO"]:
                        data["io"][io_type].set("0")
            except ValueError:
                continue
        
        # بروزرسانی خلاصه
        self.io_labels["DI"].config(text=str(total_di))
        self.io_labels["DO"].config(text=str(total_do))
        self.io_labels["AI"].config(text=str(total_ai))
        self.io_labels["AO"].config(text=str(total_ao))
        
        total = total_di + total_do + total_ai + total_ao
        self.total_label.config(text=str(total))
    
    def _apply_default_io(self):
        """اعمال مقادیر پیش‌فرض I/O"""
        for field, data in self.component_entries.items():
            # دریافت I/O پیش‌فرض از ComponentManager
            default_io = data.get("default_io", {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0})
            qty = int(data["qty"].get() or 0)
            if qty > 0:
                data["io"]["DI"].set(str(qty * default_io.get('DI', 0)))
                data["io"]["DO"].set(str(qty * default_io.get('DO', 0)))
                data["io"]["AI"].set(str(qty * default_io.get('AI', 0)))
                data["io"]["AO"].set(str(qty * default_io.get('AO', 0)))
        
        self._calculate_io()
        messagebox.showinfo("Success", "Default I/O values applied!")
    
    def _reset_all(self):
        """بازنشانی همه مقادیر"""
        if messagebox.askyesno("Confirm", "Reset all component quantities to 0?"):
            for field, data in self.component_entries.items():
                data["qty"].set("0")
            self._calculate_io()
    
    def _save(self):
        """ذخیره تغییرات"""
        try:
            # ذخیره فیلدهای پایه
            for attr, entry in self.entries.items():
                setattr(self.motor, attr, entry.get().strip())
            
            # ذخیره کامپوننت‌ها
            for field, data in self.component_entries.items():
                try:
                    qty = int(data["qty"].get() or 0)
                    setattr(self.motor, field, max(0, qty))
                except ValueError:
                    setattr(self.motor, field, 0)
            
            # ===== محاسبه I/O به صورت دستی =====
            total_di = total_do = total_ai = total_ao = 0
            for field, data in self.component_entries.items():
                try:
                    qty = int(data["qty"].get() or 0)
                    if qty > 0:
                        # اگر کامپوننت در IO_CALCULATION وجود دارد
                        if field in IO_CALCULATION:
                            config = IO_CALCULATION[field]
                            total_di += qty * config.get("DI", 0)
                            total_do += qty * config.get("DO", 0)
                            total_ai += qty * config.get("AI", 0)
                            total_ao += qty * config.get("AO", 0)
                        else:
                            # برای کامپوننت‌های سفارشی
                            default_io = data.get("default_io", self.app.component_manager.get_default_io(field))
                            total_di += qty * default_io.get('DI', 0)
                            total_do += qty * default_io.get('DO', 0)
                            total_ai += qty * default_io.get('AI', 0)
                            total_ao += qty * default_io.get('AO', 0)
                except ValueError:
                    continue
            
            # تنظیم مقادیر I/O روی دستگاه
            self.motor.DI = total_di
            self.motor.DO = total_do
            self.motor.AI = total_ai
            self.motor.AO = total_ao
            
            # ذخیره در پروژه
            if self.is_new and self.section:
                self.app._save_state()
                self.section.devices.append(self.motor)
            else:
                self.app._save_state()
            
            self.app._save_project()
            self.app._refresh_ui()
            
            self.window.destroy()
            messagebox.showinfo(
                "Success",
                f"Device {'added' if self.is_new else 'updated'} successfully!"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save device:\n{str(e)}")

# ==================== دیالوگ مدیریت برچسب‌ها ====================

class LabelsManagerDialog:
    """دیالوگ مدیریت برچسب‌های کامپوننت"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = None
        self.entries = {}
    
    def show(self):
        """نمایش دیالوگ"""
        project = self.app.get_current_project()
        if not project:
            messagebox.showwarning("Warning", "No project selected!")
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"🏷️ Manage Labels - {project.name}")
        self.window.geometry("700x600")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # مرکز کردن
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # عنوان
        tk.Label(
            self.window,
            text="🏷️ Component Labels",
            font=("Segoe UI", 14, "bold"),
            fg=COLORS['primary']
        ).pack(pady=10)
        
        # فریم با اسکرول
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # هدر
        header_frame = tk.Frame(scrollable_frame, bg=COLORS['secondary'])
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(
            header_frame,
            text="Component",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS['white'],
            bg=COLORS['secondary'],
            width=15,
            anchor="w"
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Label(
            header_frame,
            text="Persian Label",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS['white'],
            bg=COLORS['secondary'],
            width=25,
            anchor="w"
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Label(
            header_frame,
            text="English Label",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS['white'],
            bg=COLORS['secondary'],
            width=25,
            anchor="w"
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # برچسب‌ها
        labels = self.app.component_labels or COMPONENT_LABELS.copy()
        
        for field, label_data in labels.items():
            row_frame = tk.Frame(scrollable_frame)
            row_frame.pack(fill=tk.X, pady=2)
            
            # کلید
            tk.Label(
                row_frame,
                text=field,
                font=("Courier New", 9, "bold"),
                width=15,
                anchor="w",
                bg=row_frame["bg"]
            ).pack(side=tk.LEFT, padx=5)
            
            # ورودی فارسی
            fa_entry = tk.Entry(row_frame, width=25, font=("Segoe UI", 9))
            fa_entry.insert(0, label_data.get("fa", ""))
            fa_entry.pack(side=tk.LEFT, padx=5)
            
            # ورودی انگلیسی
            en_entry = tk.Entry(row_frame, width=25, font=("Segoe UI", 9))
            en_entry.insert(0, label_data.get("en", ""))
            en_entry.pack(side=tk.LEFT, padx=5)
            
            self.entries[field] = {"fa": fa_entry, "en": en_entry}
        
        # دکمه‌ها
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=15)
        
        tk.Button(
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
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="🔄 Reset Defaults",
            command=self._reset_defaults,
            bg=COLORS['warning'],
            fg=COLORS['white'],
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=25,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="❌ Close",
            command=self.window.destroy,
            bg=COLORS['secondary'],
            fg=COLORS['white'],
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=25,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
    
    def _save(self):
        """ذخیره برچسب‌ها"""
        labels = {}
        for field, entries in self.entries.items():
            fa = entries["fa"].get().strip()
            en = entries["en"].get().strip()
            if not fa:
                fa = field
            if not en:
                en = field
            labels[field] = {"fa": fa, "en": en}
        
        project = self.app.get_current_project()
        if project:
            project.component_labels = labels
            self.app.db.save_component_labels(project.name, labels)
            self.app.component_labels = labels
            messagebox.showinfo("Success", "Labels saved successfully!")
            self.window.destroy()
    
    def _reset_defaults(self):
        """بازنشانی به پیش‌فرض"""
        if messagebox.askyesno("Confirm", "Reset all labels to default values?"):
            for field, entries in self.entries.items():
                if field in COMPONENT_LABELS:
                    entries["fa"].delete(0, tk.END)
                    entries["fa"].insert(0, COMPONENT_LABELS[field]["fa"])
                    entries["en"].delete(0, tk.END)
                    entries["en"].insert(0, COMPONENT_LABELS[field]["en"])

# gui/dialogs.py - اضافه کردن در انتهای فایل

class ImageManagerDialog:
    """دیالوگ مدیریت تصویر دستگاه"""
    
    def __init__(self, parent, app, motor):
        self.parent = parent
        self.app = app
        self.motor = motor
        self.window = None
    
    def show(self):
        """نمایش دیالوگ"""
        import tkinter as tk
        from tkinter import filedialog, messagebox
        from PIL import Image, ImageTk
        
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"🖼️ Manage Image - {self.motor.Name or 'Device'}")
        self.window.geometry("500x450")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # اطلاعات دستگاه
        info_frame = tk.Frame(self.window, padx=10, pady=10)
        info_frame.pack(fill=tk.X)
        
        tk.Label(info_frame, text=f"Device: {self.motor.Name or 'Unnamed'}", 
                font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(info_frame, text=f"Description: {self.motor.Description or 'No description'}").pack(anchor="w")
        tk.Label(info_frame, text=f"I/O: DI={self.motor.DI}, DO={self.motor.DO}, AI={self.motor.AI}, AO={self.motor.AO}").pack(anchor="w")
        
        # پیش‌نمایش تصویر
        preview_frame = tk.Frame(self.window, padx=10, pady=10)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_label = tk.Label(preview_frame, text="No Image", font=("Segoe UI", 10))
        self.preview_label.pack(expand=True)
        
        def update_preview():
            if self.motor.ImagePath and os.path.exists(self.motor.ImagePath):
                try:
                    image = Image.open(self.motor.ImagePath)
                    image.thumbnail((300, 200))
                    photo = ImageTk.PhotoImage(image)
                    self.preview_label.config(image=photo, text="")
                    self.preview_label.image = photo
                except Exception as e:
                    self.preview_label.config(text=f"Error loading image: {str(e)}")
            else:
                self.preview_label.config(image="", text="No image")
        
        update_preview()
        
        # دکمه‌ها
        btn_frame = tk.Frame(self.window, padx=10, pady=10)
        btn_frame.pack(fill=tk.X)
        
        def add_image():
            file_path = filedialog.askopenfilename(
                title="Select Device Image",
                filetypes=[
                    ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                try:
                    from PIL import Image
                    image = Image.open(file_path)
                    image.thumbnail((800, 480))
                    
                    # ذخیره در پوشه دیتابیس
                    image_dir = os.path.dirname(self.app.db.db_path)
                    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in (self.motor.Name or "Device"))
                    image_filename = f"{safe_name}.png"
                    new_path = os.path.join(image_dir, image_filename)
                    image.save(new_path, "PNG")
                    
                    self.motor.ImagePath = new_path
                    update_preview()
                    self.app.db.save_project(self.app.get_current_project())
                    messagebox.showinfo("Success", "Image added successfully!")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to add image:\n{str(e)}")
        
        def remove_image():
            if self.motor.ImagePath and messagebox.askyesno("Confirm", "Remove image?"):
                self.motor.ImagePath = None
                update_preview()
                self.app.db.save_project(self.app.get_current_project())
                messagebox.showinfo("Success", "Image removed!")
        
        def view_image():
            if self.motor.ImagePath and os.path.exists(self.motor.ImagePath):
                try:
                    view_win = tk.Toplevel(self.window)
                    view_win.title(f"Image: {self.motor.Name}")
                    image = Image.open(self.motor.ImagePath)
                    photo = ImageTk.PhotoImage(image)
                    label = tk.Label(view_win, image=photo)
                    label.image = photo
                    label.pack()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to view image:\n{str(e)}")
            else:
                messagebox.showwarning("Warning", "No image to view.")
        
        tk.Button(btn_frame, text="📁 Add Image", command=add_image,
                 bg=COLORS['success'], fg='white', font=("Segoe UI", 9, "bold"),
                 relief='flat', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="👁️ View", command=view_image,
                 bg=COLORS['accent'], fg='white', font=("Segoe UI", 9, "bold"),
                 relief='flat', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="🗑️ Remove", command=remove_image,
                 bg=COLORS['danger'], fg='white', font=("Segoe UI", 9, "bold"),
                 relief='flat', padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="❌ Close", command=self.window.destroy,
                 bg=COLORS['secondary'], fg='white', font=("Segoe UI", 9, "bold"),
                 relief='flat', padx=15, pady=5).pack(side=tk.RIGHT, padx=5)
        
        # import os
        import os
        self.window.update_idletasks()