# gui/ai_settings_dialog.py
"""
دیالوگ تنظیمات AI — تنظیم API Key، Model، و...
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any
import threading

from utils.config_manager import get_config
from ai.deepseek_client import DeepSeekClient


class AISettingsDialog:
    """
    دیالوگ تنظیمات AI
    
    Usage:
        dialog = AISettingsDialog(parent, on_save=my_callback)
        dialog.show()
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        on_save: Optional[Callable[[Dict[str, Any]], None]] = None,
        client: Optional[DeepSeekClient] = None,
    ):
        self.parent = parent
        self.on_save = on_save
        self.config = get_config()
        self.client = client or DeepSeekClient()
        
        self.window: Optional[tk.Toplevel] = None
        
        # ===== Variables =====
        self.var_api_key = tk.StringVar()
        self.var_base_url = tk.StringVar()
        self.var_model = tk.StringVar()
        self.var_timeout = tk.StringVar()
        self.var_temperature = tk.StringVar()
        self.var_max_tokens = tk.StringVar()
        self.var_show_key = tk.BooleanVar(value=False)
        
        # ===== Status =====
        self.status_label: Optional[tk.Label] = None
        self.test_button: Optional[tk.Button] = None
        self.is_testing = False
    
    # ============================================================
    # SHOW
    # ============================================================
    
    def show(self):
        """نمایش دیالوگ"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self._build_window()
        self._load_current_settings()
    
    def _build_window(self):
        """ساخت پنجره"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("⚙️ AI Settings")
        self.window.geometry("700x650")
        self.window.transient(self.parent)
        self.window.resizable(False, False)
        
        # ===== Center =====
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 350
        y = (self.window.winfo_screenheight() // 2) - 365
        self.window.geometry(f"+{x}+{y}")
        
        # ===== Header =====
        header = tk.Frame(self.window, bg='#2C3E50', height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="⚙️ AI Settings",
            font=("Segoe UI", 16, "bold"),
            fg='white',
            bg='#2C3E50',
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        tk.Label(
            header,
            text="تنظیمات هوش مصنوعی",
            font=("Segoe UI", 11),
            fg='#BDC3C7',
            bg='#2C3E50',
        ).pack(side=tk.RIGHT, padx=20, pady=15)
        
        # ===== Main frame =====
        main = tk.Frame(self.window, bg='white', padx=20, pady=20)
        main.pack(fill=tk.BOTH, expand=True)
        
        # ===== API Key =====
        self._add_label(main, "🔑 API Key:", "کلید دسترسی به API", required=True)
        
        key_frame = tk.Frame(main, bg='white')
        key_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.entry_api_key = tk.Entry(
            key_frame,
            textvariable=self.var_api_key,
            font=("Consolas", 10),
            relief=tk.SOLID,
            bd=1,
            show='*',
        )
        self.entry_api_key.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Checkbutton(
            key_frame,
            text="👁",
            variable=self.var_show_key,
            command=self._toggle_key_visibility,
            bg='white',
            activebackground='white',
            bd=0,
        ).pack(side=tk.RIGHT, padx=5)
        
        # ===== Base URL =====
        self._add_label(main, "🌐 Base URL:", "آدرس سرور API", required=True)
        self._add_entry(main, self.var_base_url)
        
        # ===== Model =====
        self._add_label(main, "🤖 Model:", "مدل هوش مصنوعی", required=True)
        
        model_frame = tk.Frame(main, bg='white')
        model_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.var_model,
            values=DeepSeekClient.AVAILABLE_MODELS,
            font=("Segoe UI", 10),
            state='normal',
        )
        self.model_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Button(
            model_frame,
            text="🔄",
            command=self._refresh_models,
            bg='#3498DB',
            fg='white',
            relief='flat',
            padx=8,
            cursor='hand2',
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # ===== Timeout + Temperature =====
        row_frame = tk.Frame(main, bg='white')
        row_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Timeout
        timeout_frame = tk.Frame(row_frame, bg='white')
        timeout_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Label(
            timeout_frame,
            text="⏱️ Timeout (ثانیه):",
            font=("Segoe UI", 9, "bold"),
            bg='white',
            anchor='w',
        ).pack(fill=tk.X)
        
        tk.Entry(
            timeout_frame,
            textvariable=self.var_timeout,
            font=("Segoe UI", 10),
            relief=tk.SOLID,
            bd=1,
        ).pack(fill=tk.X, pady=(2, 0))
        
        # Temperature
        temp_frame = tk.Frame(row_frame, bg='white')
        temp_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(
            temp_frame,
            text="🌡️ Temperature (0-2):",
            font=("Segoe UI", 9, "bold"),
            bg='white',
            anchor='w',
        ).pack(fill=tk.X)
        
        tk.Entry(
            temp_frame,
            textvariable=self.var_temperature,
            font=("Segoe UI", 10),
            relief=tk.SOLID,
            bd=1,
        ).pack(fill=tk.X, pady=(2, 0))
        
        # ===== Max Tokens =====
        self._add_label(main, "📝 Max Tokens:", "حداکثر طول پاسخ", required=False)
        self._add_entry(main, self.var_max_tokens)
        
        # ===== Separator =====
        tk.Frame(main, bg='#ECF0F1', height=1).pack(fill=tk.X, pady=15)
        
        # ===== Status =====
        self.status_label = tk.Label(
            main,
            text="ℹ️ برای تست اتصال، دکمه «🧪 Test Connection» را بزنید",
            font=("Segoe UI", 9),
            bg='white',
            fg='#7F8C8D',
            anchor='w',
            justify=tk.LEFT,
            wraplength=560,
        )
        self.status_label.pack(fill=tk.X, pady=(0, 10))
        
        # ===== Buttons =====
        btn_frame = tk.Frame(self.window, bg='#F8F9FA', pady=15)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Reset
        tk.Button(
            btn_frame,
            text="♻️ Reset",
            command=self._reset_defaults,
            bg='#95A5A6',
            fg='white',
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=15,
            pady=6,
            cursor='hand2',
        ).pack(side=tk.LEFT, padx=15)
        
        # Test
        self.test_button = tk.Button(
            btn_frame,
            text="🧪 Test Connection",
            command=self._test_connection,
            bg='#3498DB',
            fg='white',
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=15,
            pady=6,
            cursor='hand2',
        )
        self.test_button.pack(side=tk.LEFT, padx=5)
        
        # Save
        tk.Button(
            btn_frame,
            text="💾 Save",
            command=self._save,
            bg='#27AE60',
            fg='white',
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=20,
            pady=6,
            cursor='hand2',
        ).pack(side=tk.RIGHT, padx=15)
        
        # Cancel
        tk.Button(
            btn_frame,
            text="❌ Cancel",
            command=self._cancel,
            bg='#E74C3C',
            fg='white',
            font=("Segoe UI", 9, "bold"),
            relief='flat',
            padx=15,
            pady=6,
            cursor='hand2',
        ).pack(side=tk.RIGHT, padx=5)
    
    # ============================================================
    # UI HELPERS
    # ============================================================
    
    def _add_label(self, parent, text: str, hint: str = "", required: bool = False):
        """افزودن label"""
        frame = tk.Frame(parent, bg='white')
        frame.pack(fill=tk.X, pady=(8, 2))
        
        label_text = text
        if required:
            label_text += " *"
        
        tk.Label(
            frame,
            text=label_text,
            font=("Segoe UI", 10, "bold"),
            bg='white',
            fg='#2C3E50' if not required else '#C0392B',
            anchor='w',
        ).pack(side=tk.LEFT)
        
        if hint:
            tk.Label(
                frame,
                text=f"({hint})",
                font=("Segoe UI", 8),
                bg='white',
                fg='#7F8C8D',
                anchor='w',
            ).pack(side=tk.LEFT, padx=(8, 0))
    
    def _add_entry(self, parent, var: tk.StringVar):
        """افزودن entry"""
        entry = tk.Entry(
            parent,
            textvariable=var,
            font=("Segoe UI", 10),
            relief=tk.SOLID,
            bd=1,
        )
        entry.pack(fill=tk.X, pady=(0, 15))
        return entry
    
    # ============================================================
    # LOAD / SAVE
    # ============================================================
    
    def _load_current_settings(self):
        """بارگذاری تنظیمات فعلی"""
        self.var_api_key.set(self.config.get('api_key', ''))
        self.var_base_url.set(self.config.get('base_url', ''))
        self.var_model.set(self.config.get('model', ''))
        self.var_timeout.set(str(self.config.get('timeout', 120)))
        self.var_temperature.set(str(self.config.get('temperature', 0.7)))
        self.var_max_tokens.set(str(self.config.get('max_tokens', 8000)))
    
    def _save(self):
        """ذخیره تنظیمات"""
        # ===== جمع‌آوری =====
        settings = {
            'api_key': self.var_api_key.get().strip(),
            'base_url': self.var_base_url.get().strip(),
            'model': self.var_model.get().strip(),
            'timeout': self.var_timeout.get().strip(),
            'temperature': self.var_temperature.get().strip(),
            'max_tokens': self.var_max_tokens.get().strip(),
        }
        
        # ===== اعتبارسنجی =====
        errors = self._validate(settings)
        if errors:
            messagebox.showerror(
                "خطا در تنظیمات",
                "\n".join(f"• {err}" for err in errors.values()),
                parent=self.window,
            )
            return
        
        # ===== تبدیل =====
        try:
            settings['timeout'] = float(settings['timeout'])
            settings['temperature'] = float(settings['temperature'])
            settings['max_tokens'] = int(settings['max_tokens'])
        except (ValueError, TypeError):
            messagebox.showerror(
                "خطا",
                "مقادیر Timeout، Temperature و Max Tokens باید عدد باشند",
                parent=self.window,
            )
            return
        
        # ===== ذخیره =====
        self.config.update(settings)
        if not self.config.save():
            messagebox.showerror(
                "خطا",
                "ذخیره تنظیمات ناموفق بود",
                parent=self.window,
            )
            return
        
        # ===== Reload client =====
        try:
            self.client.reload_from_config()
        except Exception as e:
            messagebox.showwarning(
                "هشدار",
                f"تنظیمات ذخیره شد ولی reload client با خطا مواجه شد:\n{e}",
                parent=self.window,
            )
        
        # ===== Callback =====
        if self.on_save:
            try:
                self.on_save(settings)
            except Exception as e:
                print(f"Callback error: {e}")
        
        messagebox.showinfo(
            "موفق",
            "✅ تنظیمات با موفقیت ذخیره شد",
            parent=self.window,
        )
        
        self.window.destroy()
    
    def _validate(self, settings: Dict[str, str]) -> Dict[str, str]:
        """اعتبارسنجی"""
        errors = {}
        
        # API Key
        if not settings['api_key']:
            errors['api_key'] = "API Key الزامی است"
        elif len(settings['api_key']) < 20:
            errors['api_key'] = "API Key خیلی کوتاه است (حداقل ۲۰ کاراکتر)"
        
        # Base URL
        if not settings['base_url']:
            errors['base_url'] = "Base URL الزامی است"
        elif not settings['base_url'].startswith(('http://', 'https://')):
            errors['base_url'] = "Base URL باید با http:// یا https:// شروع شود"
        
        # Model
        if not settings['model']:
            errors['model'] = "Model الزامی است"
        
        # Timeout
        try:
            t = float(settings['timeout'])
            if t < 10 or t > 600:
                errors['timeout'] = "Timeout باید بین ۱۰ تا ۶۰۰ ثانیه باشد"
        except (ValueError, TypeError):
            errors['timeout'] = "Timeout باید عدد باشد"
        
        # Temperature
        try:
            temp = float(settings['temperature'])
            if temp < 0 or temp > 2:
                errors['temperature'] = "Temperature باید بین ۰ تا ۲ باشد"
        except (ValueError, TypeError):
            errors['temperature'] = "Temperature باید عدد باشد"
        
        # Max Tokens
        try:
            mt = int(settings['max_tokens'])
            if mt < 100 or mt > 32000:
                errors['max_tokens'] = "Max Tokens باید بین ۱۰۰ تا ۳۲۰۰۰ باشد"
        except (ValueError, TypeError):
            errors['max_tokens'] = "Max Tokens باید عدد باشد"
        
        return errors
    
    # ============================================================
    # TEST
    # ============================================================
    
    def _test_connection(self):
        """تست اتصال"""
        if self.is_testing:
            return
        
        # ===== ذخیره موقت =====
        api_key = self.var_api_key.get().strip()
        base_url = self.var_base_url.get().strip()
        model = self.var_model.get().strip()
        timeout = self.var_timeout.get().strip()
        
        if not api_key:
            self._set_status("❌ ابتدا API Key را وارد کنید", 'error')
            return
        
        if not base_url:
            self._set_status("❌ ابتدا Base URL را وارد کنید", 'error')
            return
        
        # ===== غیرفعال کردن دکمه =====
        self.is_testing = True
        self.test_button.config(state=tk.DISABLED, text="⏳ Testing...")
        self._set_status("⏳ در حال تست اتصال...", 'info')
        
        # ===== در Thread =====
        def worker():
            try:
                # ساخت client موقت
                temp_client = DeepSeekClient.__new__(DeepSeekClient)
                temp_client.api_key = api_key
                temp_client.base_url = base_url
                temp_client.model = model or 'claude-opus-4.8'
                temp_client.timeout = float(timeout) if timeout else 120.0
                temp_client.temperature = 0.7
                temp_client.max_tokens = 4000
                temp_client.config = self.config
                temp_client._init_client()
                
                # تست
                result = temp_client.test_connection()
                
                # نمایش در UI thread
                self.window.after(0, lambda: self._show_test_result(result))
            except Exception as e:
                self.window.after(0, lambda: self._show_test_result({
                    'success': False,
                    'message': f'❌ خطا: {e}',
                    'models': [],
                }))
        
        threading.Thread(target=worker, daemon=True).start()
    
    def _show_test_result(self, result: Dict[str, Any]):
        """نمایش نتیجه تست"""
        self.is_testing = False
        self.test_button.config(state=tk.NORMAL, text="🧪 Test Connection")
        
        if result.get('success'):
            models_count = len(result.get('models', []))
            elapsed = result.get('elapsed', 0)
            
            self._set_status(
                f"✅ اتصال موفق — {models_count} مدل موجود — {elapsed:.2f}s",
                'success'
            )
            
            # بروزرسانی combo
            if result.get('models'):
                self.model_combo['values'] = result['models']
        else:
            self._set_status(result.get('message', '❌ خطا'), 'error')
    
    def _refresh_models(self):
        """بروزرسانی لیست مدل‌ها"""
        self._test_connection()
    
    # ============================================================
    # HELPERS
    # ============================================================
    
    def _set_status(self, message: str, level: str = 'info'):
        """تنظیم وضعیت"""
        colors = {
            'info': '#7F8C8D',
            'success': '#27AE60',
            'error': '#E74C3C',
            'warning': '#F39C12',
        }
        
        if self.status_label:
            self.status_label.config(
                text=message,
                fg=colors.get(level, '#7F8C8D'),
            )
    
    def _toggle_key_visibility(self):
        """نمایش/مخفی کردن API Key"""
        self.entry_api_key.config(show='' if self.var_show_key.get() else '*')
    
    def _reset_defaults(self):
        """بازگشت به مقادیر پیش‌فرض"""
        if not messagebox.askyesno(
            "تایید",
            "آیا مطمئن هستید که می‌خواهید به مقادیر پیش‌فرض بازگردید؟",
            parent=self.window,
        ):
            return
        
        from utils.config_manager import DEFAULT_CONFIG
        
        self.var_api_key.set('')
        self.var_base_url.set(DEFAULT_CONFIG['base_url'])
        self.var_model.set(DEFAULT_CONFIG['model'])
        self.var_timeout.set(str(DEFAULT_CONFIG['timeout']))
        self.var_temperature.set(str(DEFAULT_CONFIG['temperature']))
        self.var_max_tokens.set(str(DEFAULT_CONFIG['max_tokens']))
        
        self._set_status("ℹ️ مقادیر پیش‌فرض بارگذاری شد (ذخیره نشده)", 'info')
    
    def _cancel(self):
        """انصراف"""
        self.window.destroy()


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['AISettingsDialog']