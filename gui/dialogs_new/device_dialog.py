# gui/dialogs_new/device_dialog.py
"""
دیالوگ افزودن/ویرایش دستگاه
با Smart Suggestion و Auto-Complete
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, List

from core import Motor, ProjectSection
from core.constants import IO_CALCULATION
from gui.theme import (
    get_color, font, sp, pad, h, w, ico,
)
from gui.components import (
    BaseDialog, PrimaryButton, SecondaryButton,
    GhostButton, LabeledInput, LabeledText,
    Separator, ToastManager,
)


# ================================================================
# SMART SUGGESTIONS DATABASE
# ================================================================

SMART_SUGGESTIONS = {
    # ===== کلمات کلیدی → کامپوننت‌های پیشنهادی =====
    'pump': {
        'keywords': ['pump', 'پمپ', 'boiler', 'chiller', 'circulator'],
        'components': {
            'PU': 1,
            'FA': 1,
            'FE': 1,
            'SLE': 1,
            'CMD': 1,
        }
    },
    'fan': {
        'keywords': ['fan', 'فن', 'blower', 'ahu', 'supply', 'return'],
        'components': {
            'PU': 1,
            'FA': 1,
            'FE': 1,
            'SLE': 1,
            'CMD': 1,
        }
    },
    'temperature sensor': {
        'keywords': ['temp', 'temperature', 'دما', 'sensor', 'sensor'],
        'components': {
            'DTS': 1,
        }
    },
    'humidity sensor': {
        'keywords': ['humidity', 'رطوبت'],
        'components': {
            'RTHS': 1,
        }
    },
    'damper': {
        'keywords': ['damper', 'دمپر'],
        'components': {
            'DAM_T4': 1,
        }
    },
    'valve': {
        'keywords': ['valve', 'شیر', 'actuator'],
        'components': {
            'VA': 1,
        }
    },
    'pressure': {
        'keywords': ['pressure', 'فشار'],
        'components': {
            'PT': 1,
        }
    },
    'flow': {
        'keywords': ['flow', 'جریان'],
        'components': {
            'FS': 1,
        }
    },
    'vfd': {
        'keywords': ['vfd', 'vsd', 'drive', 'inverter', 'درایو'],
        'components': {
            'VSD': 1,
            'FA': 1,
            'FE': 1,
        }
    },
    'lighting': {
        'keywords': ['light', 'lighting', 'روشنایی', 'lamp'],
        'components': {
            'LIG': 1,
        }
    },
    'smoke': {
        'keywords': ['smoke', 'دود', 'fire'],
        'components': {
            'SD': 1,
        }
    },
    'fancoil': {
        'keywords': ['fancoil', 'fcu', 'فن کویل'],
        'components': {
            'FC': 1,
        }
    },
    'freeze': {
        'keywords': ['freeze', 'یخ', 'frost'],
        'components': {
            'FR': 1,
        }
    },
}


class DeviceDialog(BaseDialog):
    """
    دیالوگ افزودن/ویرایش دستگاه
    با Smart Suggestion
    """
    
    def __init__(
        self,
        parent,
        app,
        motor: Optional[Motor] = None,
        section: Optional[ProjectSection] = None,
        is_new: bool = False,
    ):
        self.app = app
        self.motor = motor or Motor()
        self.section = section
        self.is_new = is_new
        
        self.component_entries = {}
        self.model_order_entries = {}
        self._suggested_components = set()
        
        # ============================================================
        # ✅ متغیرهای جدید برای Live Update (ACTIVE/INACTIVE)
        # ============================================================
        self._refresh_timer = None
        self._is_refreshing = False
        self._components_parent = None
        self.active_container = None
        self.inactive_container = None
        self.active_header = None
        self.inactive_header = None
        self.active_header_label = None
        self.inactive_header_label = None
        self.active_empty_label = None
        
        title = "Add Device" if is_new else f"Edit Device: {self.motor.Name or 'Unnamed'}"
        
        super().__init__(
            parent,
            title=title,
            width=w('dialog_xl'),
            height=900,
            resizable=True,
        )
        
        # ✅ اعمال پیشنهادات اولیه بر اساس Description موجود
        if not is_new and self.motor.Description:
            self.root_after_suggestion()
    
    def root_after_suggestion(self):
        """پس از ساخت UI، پیشنهادات را اعمال می‌کند"""
        self.after(100, lambda: self._apply_suggestions_for_text(self.motor.Description or ""))
    
    # ================================================================
    # BUILD BODY
    # ================================================================
    def build_body(self, parent):
        """ساخت محتوای دیالوگ"""
        
        # ============================================================
        # Canvas با اسکرول عمودی و افقی
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
        
        h_scrollbar = ttk.Scrollbar(
            container, orient='horizontal', command=canvas.xview
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
        
        canvas.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # ============================================================
        # محتوای دیالوگ
        # ============================================================
        
        self._build_basic_info(scrollable)
        self._build_components(scrollable)
        self._build_io_summary(scrollable)
        self._calculate_io()
        
        # ✅ اتصال MouseWheel به همه ویجت‌های داخل Canvas
        self._bind_mousewheel_recursive(canvas, scrollable)


    def _bind_mousewheel_recursive(self, canvas, widget):
        """اتصال MouseWheel به همه ویجت‌های داخل Canvas (بازگشتی)"""
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
            return "break"
        
        def _on_shift_mousewheel(event):
            canvas.xview_scroll(int(-1 * (event.delta / 120)), 'units')
            return "break"
        
        def _on_linux_mousewheel(event):
            if event.num == 4:
                canvas.yview_scroll(-1, 'units')
            elif event.num == 5:
                canvas.yview_scroll(1, 'units')
            return "break"
        
        # اتصال به ویجت جاری
        try:
            widget.bind('<MouseWheel>', _on_mousewheel, add='+')
            widget.bind('<Shift-MouseWheel>', _on_shift_mousewheel, add='+')
            widget.bind('<Button-4>', _on_linux_mousewheel, add='+')
            widget.bind('<Button-5>', _on_linux_mousewheel, add='+')
        except:
            pass
        
        # اتصال به فرزندان
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(canvas, child)

    
    def _build_basic_info(self, parent):
        """اطلاعات پایه"""
        self._section_header(parent, "Device Information", 'info_circle')
        
        container = tk.Frame(parent, bg=get_color('bg_app'))
        container.pack(fill=tk.X, padx=sp('lg'), pady=sp('md'))
        
        # Name
        self.name_input = LabeledInput(
            container,
            label="Name",
            value=self.motor.Name or "",
            placeholder="e.g., P5",
            required=True,
        )
        self.name_input.pack(fill=tk.X, pady=sp('sm'))
        
        # Description
        desc_frame = tk.Frame(container, bg=get_color('bg_app'))
        desc_frame.pack(fill=tk.X, pady=sp('sm'))
        
        self.description_input = LabeledInput(
            desc_frame,
            label="Description (Type device type for smart suggestions)",
            value=self.motor.Description or "",
            placeholder="e.g., Boiler Pump, Duct Temp Sensor...",
        )
        self.description_input.pack(fill=tk.X)
        self.description_input.entry.bind('<KeyRelease>', self._on_description_changed)
        
        # ===== Suggestion Hint =====
        self.suggestion_label = tk.Label(
            container,
            text="",
            font=font('caption'),
            bg=get_color('bg_app'),
            fg=get_color('accent_cyan'),
            anchor='w',
        )
        self.suggestion_label.pack(fill=tk.X, pady=(0, sp('sm')))
        
        # INFO
        self.info_input = LabeledInput(
            container,
            label="Device Name",
            value=self.motor.INFO or "",
            placeholder="e.g., Mechanical Room",
        )
        self.info_input.pack(fill=tk.X, pady=sp('sm'))

        # ============================================================
        # ✅ Smart Suggestion (جدید)
        # ============================================================
        self._build_smart_suggestion(container)
        
        # ============================================================
        # ✅ Checkbox: نحوه نام‌گذاری
        # ============================================================
        naming_frame = tk.Frame(container, bg=get_color('bg_surface'))
        naming_frame.pack(fill=tk.X, pady=sp('sm'))
        
        # هدر
        tk.Label(
            naming_frame,
            text="📝 Naming Method for Multiple Components:",
            font=font('small'),
            bg=get_color('bg_surface'),
            fg=get_color('text_secondary'),
            anchor='w',
        ).pack(fill=tk.X, pady=(sp('sm'), sp('xs')))
        
        # Checkbox
        self.use_index_naming_var = tk.BooleanVar(value=getattr(self.motor, 'UseIndexNaming', True))
        
        checkbox = tk.Checkbutton(
            naming_frame,
            text="Use Index Naming (a, b, c, ...)",
            variable=self.use_index_naming_var,
            font=font('body'),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
            activebackground=get_color('bg_surface'),
            activeforeground=get_color('accent_cyan'),
            selectcolor=get_color('bg_surface_alt'),
            anchor='w',
            cursor='hand2',
            command=self._on_naming_method_changed,
        )
        checkbox.pack(fill=tk.X, padx=sp('sm'), pady=sp('xs'))
        
        # Hint
        self.naming_hint_label = tk.Label(
            naming_frame,
            text="",
            font=font('caption'),
            bg=get_color('bg_surface'),
            fg=get_color('text_muted'),
            anchor='w',
            justify='left',
        )
        self.naming_hint_label.pack(fill=tk.X, padx=sp('sm'), pady=(0, sp('sm')))
        
        # ✅ به‌روزرسانی hint اولیه
        self._update_naming_hint()

    def _build_smart_suggestion(self, parent):
        """ساخت پنل Smart Suggestion"""
        
        # ===== Frame =====
        suggestion_frame = tk.Frame(
            parent,
            bg=get_color('bg_surface'),
            highlightthickness=1,
            highlightbackground=get_color('border_default'),
        )
        suggestion_frame.pack(fill=tk.X, pady=sp('md'))
        
        # ===== Header =====
        header = tk.Frame(suggestion_frame, bg=get_color('bg_surface_alt'))
        header.pack(fill=tk.X)
        
        tk.Label(
            header,
            text="  💡 Smart Suggestion",
            font=font('body_bold'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('accent_cyan'),
            anchor='w',
        ).pack(fill=tk.X, padx=sp('sm'), pady=sp('xs'))
        
        # ===== Body =====
        body = tk.Frame(suggestion_frame, bg=get_color('bg_surface'))
        body.pack(fill=tk.X, padx=sp('sm'), pady=sp('sm'))
        
        # ===== Input =====
        self.suggestion_input = tk.Entry(
            body,
            font=font('input'),
            bg=get_color('input_bg'),
            fg=get_color('input_text'),
            insertbackground=get_color('input_text'),
            relief='flat',
        )
        self.suggestion_input.pack(fill=tk.X, ipady=6)
        self.suggestion_input.bind('<KeyRelease>', self._on_suggestion_search)
        
        # ===== Hint =====
        tk.Label(
            body,
            text="💬 مثلاً: boiler, AHU, chiller, fancoil...",
            font=font('caption'),
            bg=get_color('bg_surface'),
            fg=get_color('text_muted'),
            anchor='w',
        ).pack(fill=tk.X, pady=(sp('xs'), 0))
        
        # ===== Loading/Status =====
        self.suggestion_status = tk.Label(
            body,
            text="",
            font=font('caption'),
            bg=get_color('bg_surface'),
            fg=get_color('text_muted'),
            anchor='w',
            justify='left',
        )
        self.suggestion_status.pack(fill=tk.X, pady=(sp('xs'), 0))
        
        # ===== Results Container (Scrollable) =====
        results_frame = tk.Frame(body, bg=get_color('bg_surface'))
        results_frame.pack(fill=tk.X, pady=sp('xs'))
        
        # Canvas برای اسکرول
        canvas = tk.Canvas(
            results_frame,
            bg=get_color('bg_surface'),
            highlightthickness=0,
            height=0,  # ← ارتفاع داینامیک
        )
        scrollbar = ttk.Scrollbar(
            results_frame,
            orient='vertical',
            command=canvas.yview,
        )
        self.suggestion_results = tk.Frame(canvas, bg=get_color('bg_surface'))
        
        self.suggestion_results.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        canvas_window = canvas.create_window(
            (0, 0),
            window=self.suggestion_results,
            anchor='nw',
        )
        
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind('<Configure>', _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ذخیره برای استفاده بعدی
        self._suggestion_canvas = canvas
        self._suggestion_results_frame = results_frame

    def _on_suggestion_search(self, event=None):
        """جستجوی مدل‌های مشابه"""
        
        # ===== فقط برای key release (نه Tab و Shift) =====
        if event and event.keysym in ('Tab', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R'):
            return
        
        keyword = self.suggestion_input.get().strip()
        
        # ===== پاک کردن نتایج قبلی =====
        for widget in self.suggestion_results.winfo_children():
            widget.destroy()
        
        # ===== اگه خیلی کوتاه =====
        if len(keyword) < 2:
            self.suggestion_status.configure(
                text="💬 حداقل ۲ کاراکتر بنویسید...",
                fg=get_color('text_muted'),
            )
            self._resize_suggestion_panel(0)
            return
        
        # ============================================================
        # ✅ دریافت Learning Engine (Lazy Loading)
        # ============================================================
        engine = self.app._get_learning_engine()
        if not engine:
            self.suggestion_status.configure(
                text="⚠️ AI module not available",
                fg=get_color('warning'),
            )
            self._resize_suggestion_panel(0)
            return
        
        # ===== جستجو =====
        try:
            models = engine.get_similar_models(keyword, limit=10)
        except Exception as e:
            logger.error(f"Error searching models: {e}", exc_info=True)
            self.suggestion_status.configure(
                text=f"❌ خطا: {str(e)[:50]}",
                fg=get_color('danger'),
            )
            self._resize_suggestion_panel(0)
            return
        
        # ===== اگه چیزی نبود =====
        if not models:
            self.suggestion_status.configure(
                text=f"❌ هیچ مدلی برای '{keyword}' پیدا نشد",
                fg=get_color('text_muted'),
            )
            self._resize_suggestion_panel(0)
            return
        
        # ===== نمایش هدر =====
        self.suggestion_status.configure(
            text=f"💡 {len(models)} مدل پیدا شد (روی هر کدوم کلیک کنید):",
            fg=get_color('success'),
        )
        
        # ===== ساخت کارت‌ها =====
        for i, model in enumerate(models, 1):
            self._create_model_card(model, i)
        
        # ===== تنظیم ارتفاع =====
        self._resize_suggestion_panel(len(models))


    def _resize_suggestion_panel(self, count: int):
        """تنظیم ارتفاع پنل نتایج"""
        if count == 0:
            height = 0
        else:
            # هر کارت حدود 60 پیکسل
            height = min(count * 62, 400)  # حداکثر 400 پیکسل
        
        try:
            self._suggestion_canvas.configure(height=height)
        except:
            pass


    def _create_model_card(self, model: Dict, index: int):
        """ساخت کارت یک مدل"""
        
        card = tk.Frame(
            self.suggestion_results,
            bg=get_color('bg_surface_alt'),
            highlightthickness=1,
            highlightbackground=get_color('border_default'),
            cursor='hand2',
        )
        card.pack(fill=tk.X, pady=2, padx=2)
        
        # ===== Row 1: Name + Usage =====
        row1 = tk.Frame(card, bg=get_color('bg_surface_alt'))
        row1.pack(fill=tk.X, padx=sp('sm'), pady=(sp('xs'), 0))

        tk.Label(
            row1,
            text=f"{index}. 🏗️ {model['name']}",
            font=font('body_bold'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_primary'),
            anchor='w',
        ).pack(side=tk.LEFT)

        tk.Label(
            row1,
            text=f"📊 {model['usage_count']}×",
            font=font('caption'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('success'),
        ).pack(side=tk.RIGHT)

        # ============================================================
        # ✅ Row 2: Description (اگه باشه)
        # ============================================================
        description = model.get('description', '').strip()
        if description:
            tk.Label(
                card,
                text=f"📝 {description}",
                font=font('caption'),
                bg=get_color('bg_surface_alt'),
                fg=get_color('text_muted'),
                anchor='w',
                justify='left',
                wraplength=400,
            ).pack(fill=tk.X, padx=sp('sm'), pady=(2, 0))

        # ============================================================
        # ✅ Row 3: INFO (اگه باشه)
        # ============================================================
        info = model.get('info', '').strip()
        if info:
            tk.Label(
                card,
                text=f"📍 {info}",
                font=font('caption'),
                bg=get_color('bg_surface_alt'),
                fg=get_color('text_muted'),
                anchor='w',
            ).pack(fill=tk.X, padx=sp('sm'), pady=(2, 0))

        # ============================================================
        # ✅ Row 4: Components
        # ============================================================
        components_text = ", ".join(
            f"{qty} {key}"
            for key, qty in sorted(model['components'].items())
        )

        tk.Label(
            card,
            text=f"🔧 {components_text}",
            font=font('small'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_secondary'),
            anchor='w',
            justify='left',
        ).pack(fill=tk.X, padx=sp('sm'), pady=(2, sp('xs')))
        
        # ===== Hover Effect =====
        all_widgets = [card, row1] + list(card.winfo_children()) + list(row1.winfo_children())
        
        def on_enter(e):
            for w in all_widgets:
                try:
                    w.configure(bg=get_color('primary_subtle'))
                except:
                    pass
            card.configure(highlightbackground=get_color('primary'))
        
        def on_leave(e):
            for w in all_widgets:
                try:
                    w.configure(bg=get_color('bg_surface_alt'))
                except:
                    pass
            card.configure(highlightbackground=get_color('border_default'))
        
        def on_click(e):
            self._apply_model(model)
        
        for w in all_widgets:
            try:
                w.bind('<Enter>', on_enter)
                w.bind('<Leave>', on_leave)
                w.bind('<Button-1>', on_click)
            except:
                pass


    def _apply_model(self, model: Dict):
        """اعمال یک مدل (overwrite همه فیلدها)"""
        
        try:
            # ============================================================
            # 1. پر کردن Name (همیشه overwrite)
            # ============================================================
            if model.get('name'):
                self.name_input.set(model['name'])
            
            # ============================================================
            # 2. پر کردن Description
            # ============================================================
            if hasattr(self, 'description_input'):
                description = model.get('description', '')
                if description:
                    self.description_input.set(description)
            
            # ============================================================
            # 3. پر کردن INFO (Device Name)
            # ============================================================
            if hasattr(self, 'info_input'):
                info = model.get('info', '')
                if info:
                    self.info_input.set(info)
            
            # ============================================================
            # 4. پر کردن SmartTag (اگه فیلد وجود داره)
            # ============================================================
            if hasattr(self, 'smart_tag_input'):
                smart_tag = model.get('smart_tag', '')
                if smart_tag:
                    self.smart_tag_input.set(smart_tag)
            
            # ============================================================
            # 5. Overwrite همه کامپوننت‌ها
            # ============================================================
            for comp_key, data in self.component_entries.items():
                if comp_key in model['components']:
                    qty = model['components'][comp_key]
                    data['qty'].set(str(qty))
                else:
                    # اگه در مدل نبود → صفر کن
                    data['qty'].set("0")
            
            # ============================================================
            # 6. محاسبه مجدد I/O
            # ============================================================
            self._calculate_io()
            
            # ============================================================
            # 7. پاک کردن نتایج
            # ============================================================
            for widget in self.suggestion_results.winfo_children():
                widget.destroy()
            
            self.suggestion_status.configure(
                text=f"✅ مدل '{model['name']}' اعمال شد",
                fg=get_color('success'),
            )
            
            self._resize_suggestion_panel(0)
            
            # ============================================================
            # 8. Toast
            # ============================================================
            ToastManager.success(f"مدل '{model['name']}' اعمال شد")
            
        except Exception as e:
            logger.error(f"Error applying model: {e}", exc_info=True)
            ToastManager.error(f"خطا در اعمال مدل: {e}")

    def _on_naming_method_changed(self):
        """تغییر روش نام‌گذاری"""
        self._update_naming_hint()

    def _update_naming_hint(self):
        """به‌روزرسانی راهنما بر اساس روش انتخابی"""
        use_index = self.use_index_naming_var.get()
        
        if use_index:
            hint = "💡 Example: P5 with 3 pumps → P5a, P5b, P5c"
            color = get_color('accent_cyan')
        else:
            hint = "💡 Example: P5 with 3 pumps → P5, P6, P7"
            color = get_color('accent_orange')
        
        self.naming_hint_label.configure(text=hint, fg=color)
    
    def _on_description_changed(self, event=None):
        """رویداد تغییر Description"""
        # فقط برای کلیدهای حرفی/عددی
        if event and event.keysym in ('Tab', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R'):
            return
        
        text = self.description_input.get().lower().strip()
        self._apply_suggestions_for_text(text)
    
    def _apply_suggestions_for_text(self, text: str):
        """اعمال پیشنهادات بر اساس متن"""
        if not text:
            self.suggestion_label.configure(text="")
            self._suggested_components = set()
            return
        
        # ===== پیدا کردن همه کامپوننت‌های پیشنهادی =====
        suggested = {}
        matched_categories = []
        
        for category, data in SMART_SUGGESTIONS.items():
            keywords = data['keywords']
            
            # بررسی مطابقت با هر کلمه کلیدی
            for keyword in keywords:
                if keyword in text:
                    matched_categories.append(category)
                    for comp, qty in data['components'].items():
                        suggested[comp] = suggested.get(comp, 0) + qty
                    break
        
        # ===== ذخیره پیشنهادات =====
        self._suggested_components = set(suggested.keys())
        
        # ===== به‌روزرسانی Label =====
        if suggested:
            comp_names = []
            for comp in list(suggested.keys())[:5]:
                label = self.app.component_manager.get_component_label(comp, 'en')
                comp_names.append(f"{comp}")
            
            hint = f"💡 Smart Suggestion: {', '.join(comp_names)}"
            if len(suggested) > 5:
                hint += f" +{len(suggested) - 5} more"
            
            self.suggestion_label.configure(
                text=hint,
                fg=get_color('accent_cyan'),
            )
        else:
            self.suggestion_label.configure(text="")
        
        # ===== هایلایت کامپوننت‌های پیشنهادی =====
        self._highlight_suggested_components()
    
    def _highlight_suggested_components(self):
        """هایلایت کردن کامپوننت‌های پیشنهادی"""
        for field, data in self.component_entries.items():
            row = data.get('row')
            if not row:
                continue
            
            if field in self._suggested_components:
                # هایلایت
                try:
                    row.configure(bg=get_color('primary_subtle', '#0F2A4A'))
                    data['name_label'].configure(
                        bg=get_color('primary_subtle', '#0F2A4A'),
                        fg=get_color('accent_cyan'),
                    )
                except:
                    pass
            else:
                # برداشتن هایلایت
                try:
                    bg = get_color('bg_surface')
                    row.configure(bg=bg)
                    data['name_label'].configure(
                        bg=bg,
                        fg=get_color('text_primary'),
                    )
                except:
                    pass
    
    def _apply_suggestions(self):
        """اعمال پیشنهادات (پر کردن Qty)"""
        if not self._suggested_components:
            ToastManager.info("No suggestions available!")
            return
        
        # ===== پیدا کردن مقادیر پیشنهادی =====
        suggested_qty = {}
        text = self.description_input.get().lower().strip()
        
        for category, data in SMART_SUGGESTIONS.items():
            for keyword in data['keywords']:
                if keyword in text:
                    for comp, qty in data['components'].items():
                        suggested_qty[comp] = qty
                    break
        
        # ===== اعمال =====
        applied = 0
        for field, qty in suggested_qty.items():
            if field in self.component_entries:
                self.component_entries[field]['qty'].set(str(qty))
                applied += 1
        
        # ===== محاسبه مجدد =====
        self._calculate_io()
        
        ToastManager.success(f"Applied {applied} suggestion(s)!")
    
    # ================================================================
    # COMPONENTS
    # ================================================================

    def _build_components(self, parent):
        """کامپوننت‌ها با ساختار ACTIVE/INACTIVE"""
        
        self._section_header(parent, "Components", 'wrench')
        
        container = tk.Frame(parent, bg=get_color('bg_surface'))
        container.pack(fill=tk.X, padx=sp('lg'), pady=sp('md'))
        
        self._components_parent = container
        
        # ===== Apply Suggestions =====
        suggest_btn_frame = tk.Frame(container, bg=get_color('bg_surface'))
        suggest_btn_frame.pack(fill=tk.X, padx=sp('xs'), pady=sp('xs'))
        
        self.suggest_btn = SecondaryButton(
            suggest_btn_frame,
            text="💡 Apply Smart Suggestions",
            command=self._apply_suggestions,
        )
        self.suggest_btn.pack(side=tk.LEFT)
        
        # ============================================================
        # ACTIVE Section
        # ============================================================
        self.active_header = tk.Frame(container, bg=get_color('bg_surface'))
        
        self.active_header_label = tk.Label(
            self.active_header,
            text="🟢 ACTIVE COMPONENTS (0)",
            font=font('h4'),
            bg=get_color('bg_surface'),
            fg=get_color('success', '#27AE60'),
            anchor='w',
        )
        self.active_header_label.pack(fill=tk.X, padx=sp('md'), pady=sp('sm'))
        
        self.active_container = tk.Frame(container, bg=get_color('bg_surface'))
        
        # ✅ هدر جدول ACTIVE (با pack)
        self._create_pack_header(self.active_container)
        
        # پیام خالی
        self.active_empty_label = tk.Label(
            container,
            text="💡 تعداد کامپوننت‌های موردنیاز را وارد کنید",
            font=font('caption'),
            bg=get_color('bg_surface'),
            fg=get_color('text_muted'),
            anchor='w',
        )
        
        # ============================================================
        # INACTIVE Section
        # ============================================================
        self.inactive_header = tk.Frame(container, bg=get_color('bg_surface'))
        
        self.inactive_header_label = tk.Label(
            self.inactive_header,
            text="⚪ INACTIVE COMPONENTS (0)",
            font=font('h4'),
            bg=get_color('bg_surface'),
            fg=get_color('text_secondary'),
            anchor='w',
        )
        self.inactive_header_label.pack(fill=tk.X, padx=sp('md'), pady=sp('sm'))
        
        self.inactive_container = tk.Frame(container, bg=get_color('bg_surface'))
        
        # ✅ هدر جدول INACTIVE (با pack)
        self._create_pack_header(self.inactive_container)
        
        # ============================================================
        # ساخت rows
        # ============================================================
        all_components = self.app.component_manager.get_all_active_components()
        
        for field, labels in all_components.items():
            self._build_component_row(container, field, labels)
        
        # مرتب‌سازی اولیه
        self._refresh_component_order()


    def _create_pack_header(self, parent):
        """ساخت هدر جدول با pack (عرض ثابت)"""
        
        header_frame = tk.Frame(parent, bg=get_color('bg_surface_alt'))
        header_frame.pack(fill=tk.X, pady=(0, 2))
        
        # ✅ عرض ستون‌ها (ثابت — باید با rows یکسان باشد)
        columns = [
            ("Component", 45, 'center'),
            ("Qty", 6, 'center'),
            ("DI", 6, 'center'),
            ("DO", 6, 'center'),
            ("AI", 6, 'center'),
            ("AO", 6, 'center'),
            ("Model-Order", 25, 'center'),   # ✅ جدید
        ]
        
        for text, width, align in columns:
            tk.Label(
                header_frame,
                text=text,
                font=font('table_header'),
                bg=get_color('bg_surface_alt'),
                fg=get_color('text_primary'),
                width=width,
                anchor=align,
            ).pack(side=tk.LEFT, padx=sp('xs'), pady=sp('xs'))


    def _create_grid_header(self, parent):
        """ساخت هدر جدول با grid (برای هر بخش)"""
        
        header_frame = tk.Frame(parent, bg=get_color('bg_surface_alt'))
        header_frame.pack(fill=tk.X, pady=(0, 2))
        
        # ============================================================
        # ✅ عرض ستون‌ها (مستقل برای هر بخش)
        # ============================================================
        columns = [
            ("Component", 41, 'w'),      # وزن ستون
            ("Qty", 6, 'center'),
            ("DI", 6, 'center'),
            ("DO", 6, 'center'),
            ("AI", 6, 'center'),
            ("AO", 6, 'center'),
        ]
        
        for col, (text, width, align) in enumerate(columns):
            label = tk.Label(
                header_frame,
                text=text,
                font=font('table_header'),
                bg=get_color('bg_surface_alt'),
                fg=get_color('text_primary'),
                width=width,
                anchor=align,
            )
            label.grid(row=0, column=col, padx=sp('xs'), pady=sp('xs'), sticky='ew')
        
        # ============================================================
        # تنظیم وزن ستون‌ها
        # ============================================================
        # ستون 0 (Component) کشیده می‌شود
        header_frame.grid_columnconfigure(0, weight=1)
        # ستون‌های دیگر (Qty, DI, DO, AI, AO) ثابت
        for col in range(1, len(columns)):
            header_frame.grid_columnconfigure(col, weight=0)

    def _create_table_header(self, parent, columns):
        """ساخت هدر جدول برای یک بخش (با pack + عرض مستقل)
        
        Args:
            parent: والد (active_container یا inactive_container)
            columns: لیست تاپل‌های (text, width, align)
        """
        
        header_frame = tk.Frame(parent, bg=get_color('bg_surface_alt'))
        header_frame.pack(fill=tk.X, pady=(0, 2))
        
        for text, width, align in columns:
            tk.Label(
                header_frame,
                text=text,
                font=font('table_header'),
                bg=get_color('bg_surface_alt'),
                fg=get_color('text_primary'),
                width=width,
                anchor=align,
            ).pack(side=tk.LEFT, padx=sp('xs'), pady=sp('xs'))
    
    def _build_component_row(self, parent, field, labels):
        """ساخت یک row (با pack + عرض ثابت)"""
        
        # I/O default
        if field in IO_CALCULATION:
            default_io = IO_CALCULATION[field]
        else:
            default_io = self.app.component_manager.get_default_io(field)
        
        if not default_io:
            default_io = {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0}
        
        current_qty = getattr(self.motor, field, 0)
        
        # row
        row = tk.Frame(parent, bg=get_color('bg_surface'))
        
        # ============================================================
        # ✅ عرض‌های ثابت (باید با هدر یکسان باشد)
        # ============================================================
        NAME_WIDTH = 45
        QTY_WIDTH = 6
        IO_WIDTH = 6
        
        # ستون 0: نام
        name_label = tk.Label(
            row,
            text=f"{labels.get('en', field)} ({field})",
            font=font('small'),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
            width=NAME_WIDTH,
            anchor='w',
            cursor='hand2',
        )
        name_label.pack(side=tk.LEFT, padx=sp('xs'), pady=sp('xs'))
        
        # ستون 1: Qty
        qty_var = tk.StringVar(value=str(current_qty))
        qty_entry = tk.Entry(
            row,
            textvariable=qty_var,
            font=font('input'),
            bg=get_color('input_bg'),
            fg=get_color('input_text'),
            insertbackground=get_color('input_text'),
            relief='flat',
            width=QTY_WIDTH,
            justify='center',
        )
        qty_entry.pack(side=tk.LEFT, padx=sp('xs'), pady=sp('xs'))
        
        # ستون‌های 2-5: I/O
        io_vars = {}
        for io_type in ['DI', 'DO', 'AI', 'AO']:
            io_value = current_qty * default_io.get(io_type, 0) if current_qty > 0 else 0
            io_var = tk.StringVar(value=str(io_value))
            
            io_label = tk.Label(
                row,
                textvariable=io_var,
                font=font('small'),
                bg=get_color('bg_surface_alt'),
                fg=get_color('text_secondary'),
                width=IO_WIDTH,
                relief='flat',
            )
            io_label.pack(side=tk.LEFT, padx=sp('xs'), pady=sp('xs'))
            
            io_vars[io_type] = io_var
        
        # ذخیره
        # ============================================================
        # ✅ جدید: ستون Model-Order
        # ============================================================
        MODEL_ORDER_WIDTH = 25
        
        current_model_order = self.motor.get_model_order(field)
        model_order_var = tk.StringVar(value=current_model_order)
        
        model_order_entry = tk.Entry(
            row,
            textvariable=model_order_var,
            font=font('small'),
            bg=get_color('input_bg'),
            fg=get_color('input_text'),
            insertbackground=get_color('input_text'),
            relief='flat',
            width=MODEL_ORDER_WIDTH,
        )
        model_order_entry.pack(side=tk.LEFT, padx=sp('xs'), pady=sp('xs'))
        
        # ذخیره
        self.model_order_entries[field] = model_order_var
        
        # ذخیره در component_entries هم
        self.component_entries[field] = {
            'qty': qty_var,
            'io': io_vars,
            'default_io': default_io,
            'row': row,
            'name_label': name_label,
            'qty_entry': qty_entry,
            'model_order_var': model_order_var,   # ✅ جدید
            'model_order_entry': model_order_entry,
        }
        
        # رویداد
        qty_var.trace('w', lambda *args, f=field: self._on_qty_change(f))
        
        if current_qty > 0:
            self._update_row_style(field)

    def _on_qty_change(self, field):
        """هنگام تغییر qty"""
        
        # 1. رنگ‌بندی فوری
        self._update_row_style(field)
        
        # 2. به‌روزرسانی I/O
        self._calculate_io()
        
        # 3. Debounce برای مرتب‌سازی
        if self._refresh_timer:
            try:
                self.after_cancel(self._refresh_timer)
            except:
                pass
        
        self._refresh_timer = self.after(150, self._refresh_component_order)

    def _update_row_style(self, field):
        """رنگ‌بندی فوری متن بر اساس qty"""
        data = self.component_entries.get(field)
        if not data:
            return
        
        try:
            qty = int(data['qty'].get() or 0)
        except ValueError:
            qty = 0
        
        if qty > 0:
            # ===== ACTIVE: متن سبز تیره + Bold =====
            text_color = '#1B4332'
            font_style = 'body_bold'
        else:
            # ===== INACTIVE: متن معمولی =====
            text_color = get_color('text_primary')
            font_style = 'body'
        
        try:
            # ===== فقط نام کامپوننت تغییر می‌کند =====
            data['name_label'].configure(
                fg=text_color,
                font=font(font_style),
            )
        except Exception as e:
            print(f"⚠️ Error in _update_row_style({field}): {e}")

    def _refresh_component_order(self):
        """مرتب‌سازی مجدد کامپوننت‌ها (با pack)"""
        
        if self._is_refreshing:
            return
        
        self._is_refreshing = True
        
        try:
            # 1. ذخیره Focus + Cursor
            focused_widget = self.focus_get()
            cursor_pos = None
            if focused_widget and isinstance(focused_widget, tk.Entry):
                try:
                    cursor_pos = focused_widget.index(tk.INSERT)
                except:
                    pass
            
            # 2. جداسازی ACTIVE / INACTIVE
            active_fields = []
            inactive_fields = []
            
            for field, data in self.component_entries.items():
                try:
                    qty = int(data['qty'].get() or 0)
                except ValueError:
                    qty = 0
                
                if qty > 0:
                    active_fields.append(field)
                else:
                    inactive_fields.append(field)
            
            # 3. مرتب‌سازی بر اساس نام کامل انگلیسی
            all_components = self.app.component_manager.get_all_active_components()
            
            def sort_key(field):
                labels = all_components.get(field, {})
                return labels.get('en', field).lower()
            
            active_fields.sort(key=sort_key)
            inactive_fields.sort(key=sort_key)
            
            # 4. حذف همه rows
            for data in self.component_entries.values():
                data['row'].pack_forget()
            
            # 5. pack() در ACTIVE (بعد از هدر)
            for field in active_fields:
                data = self.component_entries[field]
                data['row'].pack(
                    in_=self.active_container,
                    fill=tk.X, pady=1,
                )
            
            # 6. pack() در INACTIVE (بعد از هدر)
            for field in inactive_fields:
                data = self.component_entries[field]
                data['row'].pack(
                    in_=self.inactive_container,
                    fill=tk.X, pady=1,
                )
            
            # 7. به‌روزرسانی هدرها
            self._update_section_headers(active_fields, inactive_fields)
            
            # 8. مخفی/نمایش ACTIVE
            if not active_fields:
                self.active_header.pack_forget()
                self.active_container.pack_forget()
                self.active_empty_label.pack(
                    in_=self._components_parent,
                    fill=tk.X, padx=sp('lg'), pady=sp('sm'),
                )
            else:
                self.active_empty_label.pack_forget()
                
                self.active_header.pack(
                    in_=self._components_parent,
                    fill=tk.X, padx=sp('xs'), pady=(sp('md'), 0),
                )
                self.active_container.pack(
                    in_=self._components_parent,
                    fill=tk.X, padx=sp('xs'),
                )
            
            # 9. INACTIVE
            self.inactive_header.pack(
                in_=self._components_parent,
                fill=tk.X, padx=sp('xs'), pady=(sp('md'), 0),
            )
            self.inactive_container.pack(
                in_=self._components_parent,
                fill=tk.X, padx=sp('xs'),
            )
            
            # 10. بازیابی Focus + Cursor
            if focused_widget and cursor_pos is not None:
                try:
                    focused_widget.focus_set()
                    focused_widget.icursor(cursor_pos)
                except:
                    pass
        
        finally:
            self._is_refreshing = False

    def _update_section_headers(self, active_fields, inactive_fields):
        """به‌روزرسانی هدرها"""
        
        # محاسبه Total I/O ACTIVE
        total_active_io = 0
        for field in active_fields:
            try:
                qty = int(self.component_entries[field]['qty'].get() or 0)
                default_io = self.component_entries[field]['default_io']
                total_active_io += qty * (
                    default_io.get('DI', 0) +
                    default_io.get('DO', 0) +
                    default_io.get('AI', 0) +
                    default_io.get('AO', 0)
                )
            except:
                pass
        
        # ACTIVE header
        if active_fields:
            self.active_header_label.configure(
                text=f"🟢 ACTIVE COMPONENTS ({len(active_fields)}) — Total I/O: {total_active_io}"
            )
        
        # INACTIVE header
        self.inactive_header_label.configure(
            text=f"⚪ INACTIVE COMPONENTS ({len(inactive_fields)})"
        )
    
    def _build_io_summary(self, parent):
        """خلاصه I/O"""
        self._section_header(parent, "I/O Summary", 'chart')
        
        container = tk.Frame(parent, bg=get_color('bg_app'))
        container.pack(fill=tk.X, padx=sp('lg'), pady=sp('md'))
        
        grid = tk.Frame(container, bg=get_color('bg_app'))
        grid.pack()
        
        self.io_labels = {}
        
        for i, io_type in enumerate(['DI', 'DO', 'AI', 'AO']):
            tk.Label(
                grid,
                text=f"{io_type}:",
                font=font('body_bold'),
                bg=get_color('bg_app'),
                fg=get_color('text_secondary'),
            ).grid(row=0, column=i*2, padx=sp('sm'), pady=sp('sm'), sticky='e')
            
            value_label = tk.Label(
                grid,
                text="0",
                font=font('h3'),
                bg=get_color('bg_surface'),
                fg=get_color('primary'),
                width=6,
                relief='flat',
            )
            value_label.grid(row=0, column=i*2+1, padx=sp('sm'), pady=sp('sm'))
            
            self.io_labels[io_type] = value_label
        
        # ===== Total =====
        tk.Label(
            grid,
            text="Total:",
            font=font('body_bold'),
            bg=get_color('bg_app'),
            fg=get_color('text_primary'),
        ).grid(row=1, column=0, columnspan=4, padx=sp('sm'), pady=sp('sm'), sticky='e')
        
        self.total_label = tk.Label(
            grid,
            text="0",
            font=font('h2'),
            bg=get_color('bg_surface'),
            fg=get_color('success'),
            width=6,
            relief='flat',
        )
        self.total_label.grid(row=1, column=4, columnspan=4, padx=sp('sm'), pady=sp('sm'))
    
    def _section_header(self, parent, title: str, icon: str = None):
        """هدر بخش"""
        Separator(parent, spacing=sp('sm'))
        
        header = tk.Frame(parent, bg=get_color('bg_surface_alt'))
        header.pack(fill=tk.X, padx=sp('lg'), pady=(sp('sm'), 0))
        
        display_text = f"{ico(icon)}  {title}" if icon else title
        
        tk.Label(
            header,
            text=display_text,
            font=font('h3'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_primary'),
            anchor='w',
        ).pack(fill=tk.X, padx=sp('md'), pady=sp('sm'))
    
    def _calculate_io(self):
        """محاسبه I/O"""
        total_di = total_do = total_ai = total_ao = 0
        
        for field, data in self.component_entries.items():
            try:
                qty = int(data['qty'].get() or 0)
                
                if qty > 0:
                    # ===== استفاده از default_io ذخیره شده =====
                    config = data['default_io']
                    
                    di = qty * config.get('DI', 0)
                    do = qty * config.get('DO', 0)
                    ai = qty * config.get('AI', 0)
                    ao = qty * config.get('AO', 0)
                    
                    total_di += di
                    total_do += do
                    total_ai += ai
                    total_ao += ao
                    
                    data['io']['DI'].set(str(di))
                    data['io']['DO'].set(str(do))
                    data['io']['AI'].set(str(ai))
                    data['io']['AO'].set(str(ao))
                else:
                    for io_type in ['DI', 'DO', 'AI', 'AO']:
                        data['io'][io_type].set("0")
            except ValueError:
                continue
        
        self.io_labels['DI'].configure(text=str(total_di))
        self.io_labels['DO'].configure(text=str(total_do))
        self.io_labels['AI'].configure(text=str(total_ai))
        self.io_labels['AO'].configure(text=str(total_ao))
        
        total = total_di + total_do + total_ai + total_ao
        self.total_label.configure(text=str(total))
    
    # ================================================================
    # SAVE
    # ================================================================
    
    def on_ok(self):
        """ذخیره"""
        try:
            # ===== اعتبارسنجی =====
            name = self.name_input.get().strip()
            if not name:
                ToastManager.error("Device name is required!")
                return
            
            # ===== ذخیره اطلاعات پایه =====
            self.motor.Name = name
            self.motor.Description = self.description_input.get().strip()
            self.motor.INFO = self.info_input.get().strip()

            self.motor.UseIndexNaming = self.use_index_naming_var.get()
            
            # ===== ذخیره کامپوننت‌ها =====
            total_di = total_do = total_ai = total_ao = 0
            
            for field, data in self.component_entries.items():
                try:
                    qty = int(data['qty'].get() or 0)
                    setattr(self.motor, field, max(0, qty))
                    
                    if qty > 0:
                        config = data['default_io']
                        total_di += qty * config.get('DI', 0)
                        total_do += qty * config.get('DO', 0)
                        total_ai += qty * config.get('AI', 0)
                        total_ao += qty * config.get('AO', 0)
                    
                    # ============================================================
                    # ✅ جدید: ذخیره Model-Order
                    # ============================================================
                    if 'model_order_var' in data:
                        model_order_value = data['model_order_var'].get().strip()
                        self.motor.set_model_order(field, model_order_value)
                    
                except ValueError:
                    setattr(self.motor, field, 0)
            
            self.motor.DI = total_di
            self.motor.DO = total_do
            self.motor.AI = total_ai
            self.motor.AO = total_ao
            
            # ===== ذخیره در پروژه =====
            if self.is_new and self.section:
                self.app._save_state()
                self.section.devices.append(self.motor)
            else:
                self.app._save_state()
            
            self.app._save_project()
            
            ToastManager.success(f"Device '{name}' {'added' if self.is_new else 'updated'}!")
            
            self.result = True
            self._close_dialog()
            
        except Exception as e:
            ToastManager.error(f"Failed to save: {str(e)}")


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['DeviceDialog']