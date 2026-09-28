# gui/import_proposal_dialog.py
"""دیالوگ Import پروپوزال"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from gui.theme import get_color, font, sp
from gui.components import ToastManager, PrimaryButton, SecondaryButton


class ImportProposalDialog:
    """دیالوگ Import پروپوزال از Word"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        
        self.window = tk.Toplevel(parent)
        self.window.title("📥 Import Proposal")
        self.window.geometry("600x800")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.configure(bg=get_color('bg_app'))
        
        # مرکز کردن
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 300
        y = (self.window.winfo_screenheight() // 2) - 250
        self.window.geometry(f"+{x}+{y}")
        
        self._build()
    
    def _build(self):
        # ===== Header =====
        header = tk.Frame(self.window, bg=get_color('bg_surface'), height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="📥 Import Proposal from Word",
            font=font('h2'),
            bg=get_color('bg_surface'),
            fg=get_color('primary'),
            anchor='w',
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=sp('lg'))
        
        # ===== Info =====
        info_frame = tk.Frame(self.window, bg=get_color('bg_app'))
        info_frame.pack(fill=tk.X, padx=sp('lg'), pady=sp('md'))
        
        info = """این بخش به شما اجازه می‌دهد یک پروپوزال Word قبلی را Import کنید.

سیستم به صورت خودکار:
• متن را از فایل Word استخراج می‌کند
• بخش‌های تخصصی را تشخیص می‌دهد (Boiler, Chiller, ...)
• برای هر بخش، یک قالب جدید ذخیره می‌کند
• از این قالب‌ها در پروپوزال‌های بعدی استفاده می‌کند
"""
        tk.Label(
            info_frame,
            text=info,
            font=font('body'),
            bg=get_color('bg_app'),
            fg=get_color('text_secondary'),
            justify='left',
            anchor='w',
        ).pack(fill=tk.X)
        
        # ===== File Selection =====
        file_frame = tk.Frame(self.window, bg=get_color('bg_app'))
        file_frame.pack(fill=tk.X, padx=sp('lg'), pady=sp('md'))
        
        tk.Label(
            file_frame,
            text="فایل Word:",
            font=font('body_bold'),
            bg=get_color('bg_app'),
            fg=get_color('text_primary'),
        ).pack(anchor='w')
        
        file_row = tk.Frame(file_frame, bg=get_color('bg_app'))
        file_row.pack(fill=tk.X, pady=(sp('xs'), 0))
        
        self.file_entry = tk.Entry(
            file_row,
            font=font('input'),
            bg=get_color('input_bg'),
            fg=get_color('input_text'),
        )
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, sp('sm')))
        
        SecondaryButton(
            file_row,
            text="📂 Browse",
            command=self._browse_file,
        ).pack(side=tk.RIGHT)
        
        # ===== Progress =====
        self.progress_label = tk.Label(
            self.window,
            text="",
            font=font('body'),
            bg=get_color('bg_app'),
            fg=get_color('text_secondary'),
        )
        self.progress_label.pack(fill=tk.X, padx=sp('lg'), pady=sp('sm'))
        
        # ===== Result =====
        result_frame = tk.Frame(self.window, bg=get_color('bg_app'))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=sp('lg'), pady=sp('md'))
        
        tk.Label(
            result_frame,
            text="نتیجه:",
            font=font('body_bold'),
            bg=get_color('bg_app'),
            fg=get_color('text_primary'),
        ).pack(anchor='w')
        
        self.result_text = tk.Text(
            result_frame,
            height=10,
            font=font('body'),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
            relief='flat',
            padx=sp('md'),
            pady=sp('md'),
            wrap=tk.WORD,
        )
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=(sp('xs'), 0))
        
        # ===== Footer =====
        footer = tk.Frame(self.window, bg=get_color('bg_surface'), height=60)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        btn_frame = tk.Frame(footer, bg=get_color('bg_surface'))
        btn_frame.pack(side=tk.RIGHT, padx=sp('lg'), pady=sp('md'))
        
        PrimaryButton(
            btn_frame,
            text="📥 Import",
            command=self._do_import,
        ).pack(side=tk.RIGHT)
        
        SecondaryButton(
            btn_frame,
            text="بستن",
            command=self.window.destroy,
        ).pack(side=tk.RIGHT, padx=(0, sp('sm')))
        
        # ===== مدیریت قالب‌ها =====
        SecondaryButton(
            btn_frame,
            text="📋 لیست قالب‌ها",
            command=self._show_templates,
        ).pack(side=tk.LEFT, padx=(0, sp('sm')))
    
    # ================================================================
    # ACTIONS
    # ================================================================
    
    def _browse_file(self):
        """انتخاب فایل Word"""
        file_path = filedialog.askopenfilename(
            title="انتخاب فایل Word پروپوزال",
            filetypes=[
                ("Word documents", "*.docx"),
                ("All files", "*.*"),
            ],
        )
        
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)
    
    def _do_import(self):
        """اجرای Import"""
        file_path = self.file_entry.get().strip()
        
        if not file_path:
            ToastManager.warning("لطفاً یک فایل انتخاب کنید")
            return
        
        if not file_path.lower().endswith('.docx'):
            ToastManager.warning("فقط فایل Word (.docx) پشتیبانی می‌شود")
            return
        
        # ===== نمایش در نتیجه =====
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "⏳ در حال پردازش...\n")
        self.progress_label.config(text="⏳ در حال Import...")
        self.window.update()
        
        # ===== اجرا =====
        try:
            from ai.proposal_importer import ProposalImporter
            
            importer = ProposalImporter(self.app.db, self.app)
            result = importer.import_from_docx(file_path, auto_detect=True)
            
            # ===== نمایش نتیجه =====
            self._show_result(result)
            
            if result['success']:
                ToastManager.success(
                    f"✅ {len(result['sections_saved'])} قالب ذخیره شد"
                )
                self.progress_label.config(text="✅ Import موفق")
            else:
                ToastManager.error("❌ Import ناموفق")
                self.progress_label.config(text="❌ خطا در Import")
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.result_text.insert(tk.END, f"\n❌ خطا:\n{str(e)}\n")
            self.progress_label.config(text="❌ خطا")
            ToastManager.error(f"خطا: {e}")
    
    def _show_result(self, result: dict):
        """نمایش نتیجه Import"""
        self.result_text.delete(1.0, tk.END)
        
        text = f"✅ Import موفق: {result['success']}\n\n"
        
        # ===== سکشن‌های یافت‌شده =====
        text += f"📂 سکشن‌های یافت‌شده: {len(result['sections_found'])}\n"
        for sec in result['sections_found']:
            text += f"  • {sec}\n"
        
        text += f"\n💾 قالب‌های ذخیره‌شده: {len(result['sections_saved'])}\n"
        for sec in result['sections_saved']:
            text += f"  • {sec['type']} ({sec['length']} کاراکتر)\n"
        
        # ===== خطاها =====
        if result['errors']:
            text += f"\n⚠️ خطاها ({len(result['errors'])}):\n"
            for err in result['errors']:
                text += f"  • {err}\n"
        
        self.result_text.insert(tk.END, text)
    
    def _show_templates(self):
        """نمایش لیست قالب‌ها"""
        try:
            from ai.proposal_importer import ProposalImporter
            
            importer = ProposalImporter(self.app.db, self.app)
            summary = importer.get_all_templates_summary()
            
            self.result_text.delete(1.0, tk.END)
            
            if not summary:
                self.result_text.insert(tk.END, "📭 هیچ قالبی در دیتابیس نیست.\n")
                return
            
            text = "📋 لیست قالب‌های ذخیره‌شده:\n\n"
            
            total = 0
            for section_type, templates in sorted(summary.items()):
                text += f"🔹 {section_type} ({len(templates)} قالب)\n"
                for t in templates:
                    source_icon = {
                        'imported': '📥',
                        'manual': '✏️',
                        'ai': '🤖',
                    }.get(t['source'], '📄')
                    
                    text += (
                        f"   {source_icon} {t['template_name'][:50]}\n"
                        f"      {t['length']} کاراکتر، "
                        f"استفاده: {t['usage_count']}\n"
                    )
                    total += 1
                text += "\n"
            
            text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            text += f"📊 مجموع: {total} قالب\n"
            
            self.result_text.insert(tk.END, text)
        
        except Exception as e:
            self.result_text.insert(tk.END, f"❌ خطا: {e}\n")
    
    def show(self):
        """نمایش دیالوگ"""
        self.window.wait_window()


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['ImportProposalDialog']