# gui/valves/valves_panel.py
"""
پنل اصلی مدیریت شیرها (Valves Panel)
این پنل داخل Tab «Valves» در Notebook اصلی قرار می‌گیرد.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from typing import Optional, List

from gui.theme import (
    get_color, font, sp, pad, h, ico,
)
from gui.components import (
    ToastManager, confirm_dialog,
)

from gui.valves.valve_table import ValveTable
from gui.valves.valve_dialog import ValveDialog


# ================================================================
# VALVES PANEL
# ================================================================

class ValvesPanel(tk.Frame):
    """
    پنل مدیریت شیرها
    
    ساختار:
        ValvesPanel
        └── ValveTable (جدول + toolbar داخلی)
    
    وظایف:
    - مدیریت Section فعلی
    - هماهنگی با MotorApp
    - عملیات Add/Edit/Delete/Move
    """
    
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, bg=get_color('bg_app'), **kwargs)
        
        self.app = app
        
        # ===== ✅ جدید: Toolbar Import/Export =====
        self._build_io_toolbar()
        
        # ===== ساخت جدول =====
        self.table = ValveTable(self, app=app)
        self.table.pack(fill=tk.BOTH, expand=True)
        
        # ===== وضعیت اولیه =====
        self._current_section_name = None

    # ================================================================
    # ✅ NEW: IO TOOLBAR (Import/Export/Template)
    # ================================================================
    
    def _build_io_toolbar(self):
        """ساخت Toolbar برای Import/Export/Template"""
        from gui.components import SecondaryButton, PrimaryButton
        
        toolbar = tk.Frame(
            self,
            bg=get_color('bg_surface'),
            height=45,
        )
        toolbar.pack(fill=tk.X, padx=sp('md'), pady=(sp('sm'), 0))
        toolbar.pack_propagate(False)
        
        # ===== Title =====
        tk.Label(
            toolbar,
            text="📊  Valves Import / Export",
            font=font('body_bold'),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
            anchor='w',
        ).pack(side=tk.LEFT, padx=sp('sm'))
        
        # ===== Separator =====
        tk.Frame(
            toolbar,
            bg=get_color('border_default'),
            width=1,
        ).pack(side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs'))
        
        # ===== 📄 Template Button =====
        self.template_btn = SecondaryButton(
            toolbar,
            text="📄  Template",
            command=self._on_download_template,
            tooltip="Download Excel template for bulk import",
        )
        self.template_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ===== 📤 Export Button =====
        self.export_btn = SecondaryButton(
            toolbar,
            text="📤  Export",
            command=self._on_export_simple,
            tooltip="Export valves to Excel (with calculations)",
        )
        self.export_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ===== 📥 Import Button =====
        self.import_btn = PrimaryButton(
            toolbar,
            text="📥  Import",
            command=self._on_import_simple,
            tooltip="Import valves from Excel (auto-calculate)",
        )
        self.import_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ===== Separator =====
        tk.Frame(
            toolbar,
            bg=get_color('border_default'),
            width=1,
        ).pack(side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs'))
        
        # ===== Hint =====
        tk.Label(
            toolbar,
            text="💡 Import: فقط ۸ فیلد ورودی را پر کنید، محاسبات خودکار انجام می‌شود",
            font=font('caption'),
            bg=get_color('bg_surface'),
            fg=get_color('text_muted'),
            anchor='w',
        ).pack(side=tk.LEFT, padx=sp('sm'))
    
    # ================================================================
    # ✅ NEW: TEMPLATE / EXPORT / IMPORT HANDLERS
    # ================================================================
    
    def _on_download_template(self):
        """دانلود فایل Template در مسیر پروژه"""
        from tkinter import messagebox
        from datetime import datetime
        
        try:
            from export.valves_excel_importer import ValvesExcelImporter
            
            # ===== بررسی پروژه =====
            project = self.app.get_current_project()
            if not project:
                ToastManager.warning("No project selected!")
                return
            
            # ===== مسیر پیش‌فرض: پوشه پروژه =====
            try:
                project_dir = self.app.attachment_manager.ensure_project_dir(project.name)
                reports_dir = os.path.join(project_dir, "Reports")
                os.makedirs(reports_dir, exist_ok=True)
                default_dir = reports_dir
            except Exception as e:
                default_dir = os.path.expanduser("~")
                print(f"⚠️ Could not get project folder: {e}")
            
            # ===== نام فایل =====
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f"Valves_Template_{timestamp}.xlsx"
            
            # ===== دیالوگ (مسیر پیش‌فرض پر است) =====
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Save Valves Template",
                initialdir=default_dir,
                initialfile=default_name,
            )
            
            if not file_path:
                return
            
            # ===== ساخت =====
            importer = ValvesExcelImporter(self.app)
            success = importer.create_template(file_path)
            
            if success:
                if os.name == 'nt':
                    try:
                        os.startfile(file_path)
                    except:
                        pass
                
                messagebox.showinfo(
                    "Template Saved",
                    f"Template saved to:\n{file_path}\n\n"
                    f"📁 Project: {project.name}\n\n"
                    f"فرمت فایل:\n"
                    f"  • Equipment: نام شیر\n"
                    f"  • ValveType: PICV / 3 Way / Steam / PICV+3Way\n"
                    f"  • Flow: عدد\n"
                    f"  • Unit: L/HR, L/min, m³/h, GPM, Kg/h, lb/h, ton/h\n"
                    f"  • PressureDrop: عدد (psi)\n"
                    f"  • SteamPressure: عدد (bar) — فقط برای Steam\n"
                    f"  • Circuit: نام مدار\n"
                    f"  • Quantity: عدد\n\n"
                    f"💡 ردیف‌های نمونه (Sample) در Import نادیده گرفته می‌شوند."
                )
                
                ToastManager.success("Template saved!")
            else:
                ToastManager.error("Failed to create template!")
        
        except ImportError:
            ToastManager.error(
                "ValvesExcelImporter not available!\n"
                "Please ensure 'export/valves_excel_importer.py' exists."
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            ToastManager.error(f"Failed: {str(e)}")
    
    def _on_export_simple(self):
        """Export ساده — فقط Section فعلی"""
        from tkinter import filedialog
        
        section = self.get_current_section()
        if not section:
            ToastManager.warning("لطفاً ابتدا یک Section را انتخاب کنید!")
            return
        
        valves = getattr(section, 'valves', [])
        if not valves:
            ToastManager.warning("هیچ شیری در این Section وجود ندارد!")
            return
        
        try:
            from export.valves_excel_importer import ValvesExcelImporter
            from datetime import datetime
            
            # نام فایل
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_section = "".join(
                c if c.isalnum() or c in " _-" else "_"
                for c in section.name
            ).strip() or "Section"
            
            # پوشه پیش‌فرض
            try:
                project = self.app.get_current_project()
                project_dir = self.app.attachment_manager.ensure_project_dir(project.name)
                reports_dir = os.path.join(project_dir, "Reports")
                os.makedirs(reports_dir, exist_ok=True)
                default_dir = reports_dir
            except Exception:
                default_dir = os.path.expanduser("~")
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="Save Valves Export",
                initialdir=default_dir,
                initialfile=f"Valves_{safe_section}_{timestamp}.xlsx",
            )
            
            if not file_path:
                return
            
            try:
                importer = ValvesExcelImporter(self.app)
                success = importer.export_valves(valves, section.name, file_path)
                
                if success:
                    if os.name == 'nt':
                        try:
                            os.startfile(file_path)
                        except:
                            pass
                    
                    ToastManager.success(
                        f"{len(valves)} valves exported!"
                    )
                else:
                    ToastManager.error("Export failed!")
            except PermissionError:
                from tkinter import messagebox
                messagebox.showerror(
                    "❌ فایل باز است",
                    f"فایل زیر باز است و قابل ذخیره نیست:\n\n"
                    f"📄 {os.path.basename(file_path)}\n\n"
                    f"لطفاً آن را در Excel ببندید و دوباره تلاش کنید."
                )
            else:
                ToastManager.error("Export failed!")
        
        except ImportError:
            ToastManager.error(
                "ValvesExcelImporter not available!\n"
                "Please ensure 'export/valves_excel_importer.py' exists."
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            ToastManager.error(f"Export failed: {str(e)}")
    
    def _on_import_simple(self):
        """Import شیرها از فایل Excel"""
        import traceback
        from tkinter import filedialog
        
        print("=" * 70)
        print("🔵 _on_import_simple START")
        print("=" * 70)
        
        section = self.get_current_section()
        print(f"📍 section: {section}")
        if section:
            print(f"   name: {section.name!r}")
            print(f"   valves BEFORE: {len(section.valves)}")
        
        if not section:
            ToastManager.warning(
                "لطفاً ابتدا یک Section را انتخاب کنید!\n"
                "(شیرها به Section فعلی اضافه می‌شوند)"
            )
            return
        
        # ===== انتخاب فایل =====
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx")],
            title="Select Valves Excel File",
        )
        print(f"📂 Selected: {file_path!r}")
        
        if not file_path:
            print("❌ No file selected — abort")
            return
        
        try:
            print("📦 Importing ValvesExcelImporter...")
            from export.valves_excel_importer import ValvesExcelImporter
            
            importer = ValvesExcelImporter(self.app)
            print(f"✅ importer created")
            
            # ===== مرحله ۱: خواندن =====
            print("📖 Calling read_and_validate...")
            result = importer.read_and_validate(file_path)
            print(f"   success: {result['success']}")
            print(f"   valves: {len(result['valves'])}")
            print(f"   warnings: {len(result['warnings'])}")
            
            if not result['success']:
                print(f"❌ read failed: {result['error']}")
                ToastManager.error(result['error'])
                return
            
            # ===== مرحله ۲: Preview =====
            print("🎨 Creating preview dialog...")
            from gui.valves.import_preview_dialog import ImportPreviewDialog
            
            preview_dialog = ImportPreviewDialog(
                parent=self.app.root,
                app=self.app,
                import_result=result,
                section=section,
            )
            preview_dialog.show()
            print(f"   show() returned, result = {preview_dialog.result}")
            
            # ===== مرحله ۳: اعمال =====
            if preview_dialog.result:
                print("✅ User confirmed — applying import...")
                print(f"   Section BEFORE: {len(section.valves)}")
                
                # ===== اعمال =====
                added_count = importer.apply_import(
                    result['valves'],
                    section,
                )
                print(f"   apply_import returned: {added_count}")
                print(f"   Section AFTER: {len(section.valves)}")
                
                # ===== ذخیره =====
                self.app._save_project()
                print(f"✅ Project saved")
                
                # ===== چک دیتابیس =====
                try:
                    fresh_projects = self.app.db.load_all_projects()
                    current_name = self.app.current_project_name
                    print(f"   current project name: {current_name!r}")
                    
                    if current_name in fresh_projects:
                        fresh_project = fresh_projects[current_name]
                        fresh_rev = fresh_project.get_current_revision()
                        
                        if fresh_rev:
                            print(f"   current revision: {fresh_rev.name!r}")
                            for sec in fresh_rev.sections:
                                marker = "🟢" if len(sec.valves) > 0 else "  "
                                print(f"   {marker} DB Section: {sec.name!r} → {len(sec.valves)} valves")
                except Exception as e:
                    print(f"⚠️ DB check failed: {e}")
                    traceback.print_exc()
                
                # ===== به‌روزرسانی UI =====
                try:
                    self.table.load_data(section.valves)
                    print(f"✅ Table reloaded: {len(section.valves)} valves")
                except Exception as e:
                    print(f"⚠️ Table reload failed: {e}")
                
                try:
                    self.app.sidebar.refresh_tree(
                        self.app.projects,
                        preserve_state=True,
                    )
                    print(f"✅ Sidebar refreshed")
                except Exception as e:
                    print(f"⚠️ Sidebar refresh failed: {e}")
                
                self.app._update_statusbar()
                self.app._update_stats()
                
                ToastManager.success(
                    f"✅ {added_count} valve(s) imported successfully!"
                )
            else:
                print("❌ User cancelled")
        
        except Exception as e:
            print(f"❌❌❌ EXCEPTION: {e}")
            traceback.print_exc()
            ToastManager.error(f"Import failed: {str(e)}")
        
        print("=" * 70)
        print("🔵 _on_import_simple END")
        print("=" * 70)
    
    # ================================================================
    # SECTION MANAGEMENT
    # ================================================================
    
    def set_section(self, section_name: Optional[str]):
        """
        تنظیم Section فعلی
        
        Args:
            section_name: نام Section یا None
        """
        self._current_section_name = section_name
        
        # ===== بارگذاری شیرهای Section =====
        self.refresh()
    
    def get_current_section(self):
        """دریافت Section فعلی از app"""
        if not self.app:
            return None
        
        if hasattr(self.app, 'get_current_section'):
            return self.app.get_current_section()
        
        return None
    
    # ================================================================
    # REFRESH
    # ================================================================
    
    def refresh(self):
        """به‌روزرسانی جدول"""
        section = self.get_current_section()
        
        if not section:
            self.table.load_data([])
            return
        
        valves = getattr(section, 'valves', [])
        self.table.load_data(valves)
    
    # ================================================================
    # ACTIONS (از ValveTable صدا زده می‌شوند)
    # ================================================================
    
    def add_valve(self):
        """افزودن شیر جدید"""
        if not self.app:
            return
        
        section = self.get_current_section()
        if not section:
            ToastManager.warning(
                "لطفاً ابتدا یک Section را انتخاب کنید!"
            )
            return
        
        # ===== باز کردن دیالوگ =====
        dialog = ValveDialog(
            parent=self.app.root,
            app=self.app,
            valve=None,
            section=section,
            is_new=True,
        )
        dialog.show()
        
        # ===== Refresh =====
        self.refresh()
    
    def edit_valve(self):
        """ویرایش شیر انتخاب‌شده"""
        if not self.app:
            return
        
        # ===== دریافت شیرهای انتخاب‌شده =====
        indices = self.table.get_selected_indices()
        
        if not indices:
            ToastManager.warning("لطفاً یک شیر را انتخاب کنید.")
            return
        
        if len(indices) > 1:
            ToastManager.warning("لطفاً فقط یک شیر انتخاب کنید.")
            return
        
        # ===== دریافت Section =====
        section = self.get_current_section()
        if not section:
            return
        
        # ===== بررسی ایندکس =====
        idx = indices[0]
        if idx >= len(section.valves):
            ToastManager.error("شیر یافت نشد.")
            return
        
        valve = section.valves[idx]
        
        # ===== باز کردن دیالوگ =====
        dialog = ValveDialog(
            parent=self.app.root,
            app=self.app,
            valve=valve,
            section=section,
            is_new=False,
        )
        dialog.show()
        
        # ===== Refresh =====
        self.refresh()
    
    def delete_valves(self):
        """حذف شیرهای انتخاب‌شده"""
        if not self.app:
            return
        
        # ===== دریافت شیرهای انتخاب‌شده =====
        indices = self.table.get_selected_indices()
        
        if not indices:
            ToastManager.warning("لطفاً حداقل یک شیر انتخاب کنید.")
            return
        
        # ===== تایید =====
        count = len(indices)
        
        if count == 1:
            section = self.get_current_section()
            valve_name = 'شیر'
            if section and indices[0] < len(section.valves):
                valve_name = section.valves[indices[0]].Equipment or 'شیر'
            
            msg = f"حذف '{valve_name}'؟\n\nاین عمل قابل بازگشت است (Undo)."
        else:
            msg = (
                f"حذف {count} شیر؟\n\n"
                f"این عمل قابل بازگشت است (Undo)."
            )
        
        if not confirm_dialog(
            self.app.root,
            msg,
            "تایید حذف",
            'danger',
            "حذف",
            "انصراف",
        ):
            return
        
        # ===== حذف =====
        section = self.get_current_section()
        if not section:
            return
        
        # ===== ذخیره state برای Undo =====
        self.app._save_state()
        
        # ===== حذف از انتها به ابتدا =====
        for idx in sorted(indices, reverse=True):
            if 0 <= idx < len(section.valves):
                del section.valves[idx]
        
        # ===== ذخیره =====
        self.app._save_project()
        
        # ===== Refresh =====
        self.refresh()
        self.app._update_stats()
        
        ToastManager.success(f"{count} شیر حذف شد.")
    
    def move_valve_up(self):
        """جابجایی شیر به بالا"""
        self._move_valve(direction=-1)
    
    def move_valve_down(self):
        """جابجایی شیر به پایین"""
        self._move_valve(direction=+1)
    
    def _move_valve(self, direction: int):
        """
        جابجایی شیر
        
        Args:
            direction: -1 (بالا) یا +1 (پایین)
        """
        if not self.app:
            return
        
        # ===== دریافت ایندکس =====
        indices = self.table.get_selected_indices()
        
        if not indices:
            return
        
        section = self.get_current_section()
        if not section:
            return
        
        idx = indices[0]
        new_idx = idx + direction
        
        # ===== بررسی مرزها =====
        if new_idx < 0 or new_idx >= len(section.valves):
            return
        
        # ===== ذخیره state =====
        self.app._save_state()
        
        # ===== تعویض =====
        section.valves[idx], section.valves[new_idx] = (
            section.valves[new_idx],
            section.valves[idx],
        )
        
        # ===== ذخیره =====
        self.app._save_project()
        
        # ===== Refresh =====
        self.refresh()
        
        # ===== انتخاب مجدد =====
        self._select_row_in_table(new_idx)
    
    def _select_row_in_table(self, index: int):
        """انتخاب ردیف در جدول بر اساس ایندکس"""
        try:
            children = self.table.tree.get_children()
            if 0 <= index < len(children):
                self.table.tree.selection_set(children[index])
                self.table.tree.focus(children[index])
                self.table.tree.see(children[index])
        except Exception:
            pass
    
    def duplicate_valves(self):
        """کپی شیرهای انتخاب‌شده"""
        if not self.app:
            return
        
        indices = self.table.get_selected_indices()
        
        if not indices:
            ToastManager.warning("لطفاً حداقل یک شیر انتخاب کنید.")
            return
        
        section = self.get_current_section()
        if not section:
            return
        
        # ===== ذخیره state =====
        self.app._save_state()
        
        # ===== کپی =====
        count = 0
        for idx in indices:
            if 0 <= idx < len(section.valves):
                original = section.valves[idx]
                new_valve = original.copy()
                # Equipment + (Copy)
                new_valve.Equipment = f"{original.Equipment} (Copy)"
                section.valves.append(new_valve)
                count += 1
        
        # ===== ذخیره =====
        self.app._save_project()
        
        # ===== Refresh =====
        self.refresh()
        self.app._update_stats()
        
        ToastManager.success(f"{count} شیر کپی شد.")

    # ================================================================
    # ✅ COPY / PASTE OPERATIONS
    # ================================================================
    
    def copy_valves(self):
        """کپی شیرهای انتخاب‌شده"""
        if not self.app:
            return
        
        indices = self.table.get_selected_indices()
        
        if not indices:
            ToastManager.warning("لطفاً حداقل یک شیر انتخاب کنید.")
            return
        
        section = self.get_current_section()
        if not section:
            return
        
        # ===== کپی در MotorApp =====
        self.app.copied_valves = []
        for idx in indices:
            if 0 <= idx < len(section.valves):
                self.app.copied_valves.append(section.valves[idx].copy())
        
        count = len(self.app.copied_valves)
        ToastManager.success(f"{count} شیر کپی شد.")
    
    def paste_valves(self):
        """چسباندن شیرهای کپی‌شده"""
        if not self.app:
            return
        
        if not self.app.copied_valves:
            ToastManager.warning("هیچ شیری برای چسباندن وجود ندارد.")
            return
        
        section = self.get_current_section()
        if not section:
            ToastManager.warning("لطفاً ابتدا یک Section را انتخاب کنید.")
            return
        
        # ===== ذخیره state =====
        self.app._save_state()
        
        # ===== چسباندن =====
        count = 0
        for valve in self.app.copied_valves:
            new_valve = valve.copy()
            # ✅ نام اصلی حفظ می‌شود
            section.valves.append(new_valve)
            count += 1
        
        # ===== ذخیره =====
        self.app._save_project()
        
        # ===== Refresh =====
        self.refresh()
        self.app._update_stats()
        
        ToastManager.success(f"{count} شیر چسبانده شد.")

    # ================================================================
    # ✅ CHECK / FIX DUPLICATE NAMES
    # ================================================================
    
    def check_duplicate_names(self):
        """بررسی نام‌های تکراری شیرها"""
        from collections import defaultdict
        import tkinter as tk
        from tkinter import messagebox
        
        section = self.get_current_section()
        if not section:
            ToastManager.warning("لطفاً ابتدا یک Section را انتخاب کنید!")
            return
        
        if not section.valves:
            ToastManager.info("هیچ شیری در این Section وجود ندارد!")
            return
        
        # ============================================================
        # پیدا کردن نام‌های تکراری
        # ============================================================
        name_groups = defaultdict(list)
        
        for idx, valve in enumerate(section.valves):
            name = (valve.Equipment or "Unnamed").strip() or "Unnamed"
            
            name_groups[name].append({
                'index': idx,
                'name': valve.Equipment or "Unnamed",
                'valve_type': valve.ValveType or '—',
                'circuit': valve.Circuit or '—',
                'flow': valve.Flow,
                'unit': valve.Unit or '—',
                'qty': valve.Quantity,
            })
        
        # فیلتر: فقط نام‌های تکراری
        duplicates = {
            name: valves
            for name, valves in name_groups.items()
            if len(valves) > 1
        }
        
        # ============================================================
        # ساخت گزارش
        # ============================================================
        project = self.app.get_current_project()
        project_name = project.name if project else "Unknown"
        
        report = "🔍 VALVE DUPLICATE NAME REPORT\n"
        report += "=" * 70 + "\n\n"
        report += f"📁 Project: {project_name}\n"
        report += f"📂 Section: {section.name}\n"
        report += f"🔢 Total Valves: {len(section.valves)}\n"
        report += f"📝 Unique Names: {len(name_groups)}\n"
        report += "=" * 70 + "\n\n"
        
        if not duplicates:
            report += "✅ NO DUPLICATES FOUND!\n\n"
            report += f"All {len(section.valves)} valve(s) have unique names.\n"
            
            messagebox.showinfo("🔍 Valve Duplicate Check", report)
            ToastManager.success("No duplicates found in valves!")
            return
        
        # ===== با تکراری =====
        total_duplicated = sum(len(v) for v in duplicates.values())
        
        report += f"❌ FOUND {len(duplicates)} DUPLICATE GROUP(S)\n"
        report += f"⚠️  Affected Valves: {total_duplicated}\n"
        report += "=" * 70 + "\n\n"
        
        for i, (name, valves) in enumerate(sorted(duplicates.items()), 1):
            report += f"┌─ [{i}] Name: \"{name}\"  ({len(valves)} valves)\n"
            report += "│\n"
            
            for j, valve in enumerate(valves, 1):
                report += f"│  {j}. Row #{valve['index'] + 1}\n"
                report += f"│     Type: {valve['valve_type']}\n"
                report += f"│     Circuit: {valve['circuit']}\n"
                report += f"│     Flow: {valve['flow']} {valve['unit']}\n"
                report += f"│     Qty: {valve['qty']}\n"
                report += "│\n"
            
            report += "└" + "─" * 68 + "\n\n"
        
        report += "=" * 70 + "\n"
        report += "💡 RECOMMENDATIONS:\n"
        report += "-" * 70 + "\n"
        report += "• Rename manually (Edit Valve)\n"
        report += "• Use Fix Duplicate Names button for auto-fix\n"
        report += "• Use unique naming (Va-1/Va-2 or Va1/Va2)\n"
        report += "=" * 70 + "\n"
        
        # ============================================================
        # نمایش گزارش
        # ============================================================
        self._show_duplicate_report(report, len(duplicates))
        
        ToastManager.warning(f"Found {len(duplicates)} duplicate group(s) in valves!")
    
    def fix_duplicate_names(self):
        """
        اصلاح نام‌های تکراری شیرها با پر کردن شماره‌های خالی
        
        مثال:
            ورودی: Va-1, Va-2, Va-5, Va, Va
            خروجی: Va-1, Va-2, Va-3, Va-4, Va-5
        """
        import re
        from tkinter import messagebox
        
        section = self.get_current_section()
        if not section:
            ToastManager.warning("لطفاً ابتدا یک Section را انتخاب کنید!")
            return
        
        if not section.valves:
            ToastManager.info("هیچ شیری در این Section وجود ندارد!")
            return
        
        # ============================================================
        # 1. پیدا کردن نام‌های تکراری
        # ============================================================
        name_count = {}
        for valve in section.valves:
            name = (valve.Equipment or "Unnamed").strip() or "Unnamed"
            if name not in name_count:
                name_count[name] = []
            name_count[name].append(valve)
        
        duplicates = {
            name: valves 
            for name, valves in name_count.items() 
            if len(valves) > 1
        }
        
        if not duplicates:
            ToastManager.success("All valve names are unique!")
            return
        
        duplicate_count = sum(len(v) for v in duplicates.values())
        
        if not messagebox.askyesno(
            "Fix Valve Duplicate Names",
            f"Found {len(duplicates)} duplicate name(s) affecting {duplicate_count} valves.\n\n"
            f"Fix automatically by filling gaps in numbering?"
        ):
            return
        
        self.app._save_state()
        
        # ============================================================
        # 2. جمع‌آوری شماره‌های موجود برای هر prefix
        # ============================================================
        prefix_numbers = {}
        
        for valve in section.valves:
            valve_name = (valve.Equipment or "").strip()
            if not valve_name:
                continue
            
            match = re.match(r'^(.*?)-(\d+)$', valve_name)
            if match:
                prefix = match.group(1).strip()
                num = int(match.group(2))
                
                if prefix not in prefix_numbers:
                    prefix_numbers[prefix] = set()
                prefix_numbers[prefix].add(num)
        
        # ============================================================
        # 3. مرتب‌سازی گروه‌های تکراری
        # ============================================================
        sorted_duplicates = sorted(
            duplicates.items(),
            key=lambda x: (0 if '-' in x[0] else 1, x[0])
        )
        
        # ============================================================
        # 4. اصلاح
        # ============================================================
        fixed_count = 0
        fix_log = []
        
        for name, valves in sorted_duplicates:
            match = re.match(r'^(.*?)-(\d+)$', name)
            
            if match:
                base_prefix = match.group(1).strip()
            else:
                base_prefix = name.strip()
            
            if base_prefix not in prefix_numbers:
                prefix_numbers[base_prefix] = set()
            
            existing_numbers = prefix_numbers[base_prefix]
            needed = len(valves)
            
            # ===== پیدا کردن شماره‌های خالی =====
            available_numbers = []
            candidate = 1
            max_search = 10000
            
            while len(available_numbers) < needed and candidate <= max_search:
                if candidate not in existing_numbers:
                    available_numbers.append(candidate)
                candidate += 1
            
            # ===== اگر کم بود، از max+1 =====
            if len(available_numbers) < needed:
                max_existing = max(existing_numbers) if existing_numbers else 0
                next_num = max_existing + 1
                
                while len(available_numbers) < needed:
                    if next_num not in existing_numbers:
                        available_numbers.append(next_num)
                    next_num += 1
            
            # ===== اعمال =====
            for i, valve in enumerate(valves):
                new_num = available_numbers[i]
                new_name = f"{base_prefix}-{new_num}"
                
                old_name = valve.Equipment
                valve.Equipment = new_name
                fixed_count += 1
                
                existing_numbers.add(new_num)
                fix_log.append(f"  • '{old_name}' → '{new_name}'")
        
        # ============================================================
        # 5. ذخیره و نمایش
        # ============================================================
        self.app._save_project()
        self.refresh()
        
        result_msg = f"✅ Fixed {fixed_count} valve name(s)!\n\n"
        result_msg += "Changes:\n"
        result_msg += "\n".join(fix_log[:30])
        
        if len(fix_log) > 30:
            result_msg += f"\n\n... and {len(fix_log) - 30} more"
        
        messagebox.showinfo("✅ Fix Valve Duplicates", result_msg)
        ToastManager.success(f"Fixed {fixed_count} valve name(s)!")
    
    def _show_duplicate_report(self, report: str, duplicates_count: int):
        """نمایش گزارش تکراری‌ها در پنجره"""
        import tkinter as tk
        from tkinter import ttk, filedialog
        from gui.theme import get_color, font, sp
        from gui.components import PrimaryButton, SecondaryButton
        from datetime import datetime
        
        win = tk.Toplevel(self.app.root)
        win.title("🔍 Valve Duplicate Names")
        win.geometry("800x600")
        win.transient(self.app.root)
        win.grab_set()
        win.configure(bg=get_color('bg_app'))
        
        # مرکز کردن
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
        y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")
        
        # ===== Header =====
        header = tk.Frame(win, bg=get_color('bg_surface'), height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        has_duplicates = duplicates_count > 0
        header_color = get_color('danger') if has_duplicates else get_color('success')
        header_icon = '🔴' if has_duplicates else '✅'
        
        tk.Label(
            header,
            text=f"{header_icon} Valve Duplicate Report",
            font=font('h2'),
            bg=get_color('bg_surface'),
            fg=header_color,
            anchor='w',
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=sp('lg'))
        
        # ===== Text Area =====
        text_frame = tk.Frame(win, bg=get_color('bg_surface'))
        text_frame.pack(fill=tk.BOTH, expand=True, padx=sp('lg'), pady=sp('md'))
        
        from tkinter import scrolledtext
        text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
        )
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert('1.0', report)
        text_area.config(state='disabled')
        
        # ===== Footer =====
        footer = tk.Frame(win, bg=get_color('bg_surface'), height=60)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        btn_frame = tk.Frame(footer, bg=get_color('bg_surface'))
        btn_frame.pack(side=tk.RIGHT, padx=sp('lg'), pady=sp('md'))
        
        PrimaryButton(
            btn_frame,
            text="Close",
            command=win.destroy,
        ).pack(side=tk.RIGHT)
    # ================================================================
    # ✅ EXPORT OPERATIONS
    # ================================================================
    
    def export_to_excel(self, file_path: str = None):
        """
        Export Valves به Excel
        
        Args:
            file_path: مسیر فایل (اختیاری — اگر None، دیالوگ باز می‌شود)
        
        Returns:
            مسیر فایل ذخیره‌شده یا None
        """
        if not self.app:
            return None
        
        # ===== بررسی پروژه =====
        project = self.app.get_current_project()
        if not project:
            ToastManager.warning("No project selected!")
            return None
        
        # ===== بررسی Section =====
        section = self.get_current_section()
        if not section:
            ToastManager.warning(
                "لطفاً ابتدا یک Section را انتخاب کنید!"
            )
            return None
        
        # ===== بررسی وجود شیر =====
        valves = getattr(section, 'valves', [])
        if not valves:
            ToastManager.warning(
                "هیچ شیری در این Section وجود ندارد!"
            )
            return None
        
        # ===== فراخوانی Exporter =====
        try:
            from export.valves_excel_exporter import ValvesExcelExporter
            
            exporter = ValvesExcelExporter(self.app)
            result = exporter.export_full_report(file_path)
            
            if result:
                ToastManager.success(
                    f"Excel Report saved: {os.path.basename(result)}"
                )
            
            return result
        
        except ImportError as e:
            ToastManager.error(
                f"Excel exporter not found!\n"
                f"Please ensure 'export/valves_excel_exporter.py' exists.\n\n"
                f"Error: {e}"
            )
            return None
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            ToastManager.error(f"Export failed: {str(e)}")
            return None
    
    # ================================================================
    # HELPER METHODS (از MotorApp)
    # ================================================================
    
    def get_statistics(self) -> dict:
        """آمار شیرهای Section فعلی"""
        section = self.get_current_section()
        
        if not section:
            return {
                'total': 0,
                'by_type': {},
                'by_circuit': {},
                'with_warnings': 0,
            }
        
        valves = getattr(section, 'valves', [])
        
        # ===== شمارش =====
        by_type = {}
        by_circuit = {}
        with_warnings = 0
        
        for valve in valves:
            # توسط نوع
            vt = valve.ValveType or 'Unknown'
            by_type[vt] = by_type.get(vt, 0) + 1
            
            # توسط مدار
            circuit = valve.Circuit or 'Unknown'
            by_circuit[circuit] = by_circuit.get(circuit, 0) + 1
            
            # هشدار
            if hasattr(valve, 'has_warning') and valve.has_warning():
                with_warnings += 1
        
        return {
            'total': len(valves),
            'by_type': by_type,
            'by_circuit': by_circuit,
            'with_warnings': with_warnings,
        }
    
    def select_all(self):
        """انتخاب همه"""
        self.table.tree.selection_set(self.table.tree.get_children())
    
    def clear_selection(self):
        """پاک کردن انتخاب"""
        self.table.tree.selection_remove(self.table.tree.selection())


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['ValvesPanel']