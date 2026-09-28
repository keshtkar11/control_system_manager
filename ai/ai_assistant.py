"""دستیار هوشمند AI برای کمک به طراحی سیستم کنترل — نسخه 3.0 (اصلاح‌شده)"""
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
import threading
import queue
from typing import List, Dict, Any, Optional
import math
import logging

from core import Project, Motor, COMPONENT_LABELS, COLORS
from ai.deepseek_client import DeepSeekClient
from ai.learning_engine import LearningEngine
from ai.project_query_engine import ProjectQueryEngine

logger = logging.getLogger(__name__)


class AIProjectAssistant:
    """
    دستیار هوشمند پروژه با قابلیت گفتگو
    
    ✅ نسخه 3.0 — اصلاحات:
    - Thread safety با Lock
    - یکسان‌سازی نمایش در _generate_local_proposal
    - اصلاح _get_learning_stats (کلید 'label' و format)
    - اصلاح _get_predictions (کلید 'label')
    - اصلاح _get_optimization_suggestions
    - اصلاح _get_project_info (sections در current_revision)
    - مدیریت خطا بهتر
    """
    
    # ================================================================
    # INIT
    # ================================================================
    
    def __init__(self, db_manager, app):
        self.db = db_manager
        self.app = app
        self.client = DeepSeekClient()
        self.conversation_history: List[Dict[str, str]] = []
        self.window: Optional[tk.Toplevel] = None
        self.text_area: Optional[scrolledtext.ScrolledText] = None
        self.input_entry: Optional[tk.Entry] = None
        self.last_proposal: Optional[str] = None
        self.is_processing = False
        self.result_queue: queue.Queue = queue.Queue()
        self.thread: Optional[threading.Thread] = None
        
        # ✅ جدید: Lock برای Thread Safety
        self._thread_lock = threading.Lock()
        
        # ===== موتورها =====
        self.learning_engine = LearningEngine(db_manager)
        self.query_engine = ProjectQueryEngine(db_manager, app)
    
    # ================================================================
    # THREAD MANAGEMENT
    # ================================================================
    
    def _run_in_thread(self, func, *args, **kwargs):
        """
        اجرای تابع در Thread و انتقال نتیجه به UI
        
        ✅ اصلاح: با Lock از race condition جلوگیری می‌شود
        """
        # ===== چک: اگر thread قبلی هنوز در حال اجراست =====
        with self._thread_lock:
            if self.thread is not None and self.thread.is_alive():
                logger.warning("⚠️ Thread still running, ignoring new request")
                self.is_processing = False
                return
        
        def worker():
            try:
                result = func(*args, **kwargs)
                self.result_queue.put(("success", result))
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.result_queue.put(("error", str(e)))
        
        self.thread = threading.Thread(target=worker, daemon=True)
        self.thread.start()
        
        # ===== زمان‌بندی چک نتیجه =====
        try:
            self.app.root.after(100, self._check_result)
        except Exception as e:
            logger.error(f"❌ Could not schedule _check_result: {e}")
            self.is_processing = False
    
    def _check_result(self):
        """بررسی نتیجه Thread و اعمال به UI"""
        try:
            # ===== چک Queue =====
            try:
                status, result = self.result_queue.get_nowait()
            except queue.Empty:
                # هنوز نتیجه‌ای نیست، دوباره بررسی کن
                if self.thread and self.thread.is_alive():
                    try:
                        self.app.root.after(100, self._check_result)
                    except Exception:
                        self.is_processing = False
                else:
                    logger.debug("⚠️ [_check_result] Thread dead, no result")
                    self.is_processing = False
                return
            
            logger.debug(f"📥 [_check_result] status={status}")
            
            # ===== پردازش =====
            if status == "success":
                try:
                    self._on_success(result)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    logger.error(f"❌ [_on_success] Error: {e}")
                    # ===== fallback: نمایش ساده =====
                    try:
                        preview = str(result)[:1500] if result else "(empty)"
                        self._add_message(
                            "assistant",
                            f"🤖 Assistant:\n{preview}\n\n"
                            f"⚠️ نمایش خلاصه (خطا در نمایش کامل)"
                        )
                    except Exception:
                        pass
                    self.is_processing = False
            else:
                try:
                    self._on_error(result)
                except Exception as e:
                    logger.error(f"❌ [_on_error] Error: {e}")
                    self.is_processing = False
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"❌ [_check_result] Unexpected: {e}")
            self.is_processing = False
    
    def _on_success(self, result):
        """
        اعمال نتیجه موفق به UI
        
        ✅ اصلاح: طولانی‌ترین متن را preview می‌کند
        """
        try:
            if result is None or result == "":
                # ✅ اگر نتیجه خالی بود، پیام پیش‌فرض
                logger.debug("ℹ️ Empty result, skipping display")
                self.is_processing = False
                return
            
            result_str = str(result)
            logger.debug(f"📏 [_on_success] Result length: {len(result_str)}")
            
            if len(result_str) > 1500:
                preview = result_str[:1500]
                self._add_message(
                    "assistant",
                    f"🤖 Assistant:\n{preview}\n\n"
                    f"{'━' * 50}\n"
                    f"📏 **کل محتوا:** {len(result_str)} کاراکتر\n"
                    f"✅ برای مشاهده کامل، از دکمه‌های «💾 Save Word» استفاده کنید."
                )
            else:
                self._add_message("assistant", f"🤖 Assistant:\n{result_str}")
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"❌ Error in _on_success: {e}", exc_info=True)
            try:
                self._add_message("error", f"❌ خطا در نمایش نتیجه: {e}")
            except Exception:
                pass
        
        self.is_processing = False
        try:
            if self.text_area:
                self.text_area.see(tk.END)
        except Exception:
            pass
    
    def _on_error(self, error):
        """اعمال خطا به UI"""
        try:
            self._add_message("error", f"❌ Error: {error}")
        except Exception:
            pass
        self.is_processing = False
        try:
            if self.text_area:
                self.text_area.see(tk.END)
        except Exception:
            pass
    
    # ================================================================
    # LEARNING ENGINE WRAPPERS
    # ================================================================
    
    def _learn_from_current_project(self) -> str:
        """یادگیری از پروژه فعلی و بازگرداندن نتیجه به صورت متن"""
        project = self.app.get_current_project()
        if not project:
            return "❌ لطفاً ابتدا یک پروژه انتخاب کنید"
        
        devices = project.get_all_devices()
        if not devices:
            return "❌ پروژه هیچ دستگاهی ندارد. ابتدا دستگاه‌ها را اضافه کنید."
        
        # یادگیری از پروژه
        self.learning_engine.learn_from_project(project)
        
        # تحلیل و نمایش نتایج
        analysis = self.learning_engine.analyze_project(project)
        
        # ===== چک خطا =====
        if 'error' in analysis:
            return f"❌ خطا در تحلیل پروژه: {analysis['error']}"
        
        result = f"""
📚 **یادگیری از پروژه: {project.name}**

**نتایج تحلیل:**
• تعداد دستگاه‌ها: {analysis.get('total_devices', 0)}
• کل I/O: {analysis.get('total_io', 0)}
• میانگین I/O در هر دستگاه: {analysis.get('avg_io_per_device', 0):.1f}

**کامپوننت‌های شناسایی شده:**
"""
        component_usage = analysis.get('component_usage', {})
        for comp, count in sorted(component_usage.items(), key=lambda x: x[1], reverse=True)[:5]:
            label = COMPONENT_LABELS.get(comp, {}).get('fa', comp)
            result += f"• {label}: {count} عدد\n"
        
        # ===== الگوهای شناسایی شده =====
        patterns = analysis.get('patterns', {})
        if patterns.get('common_combinations'):
            result += "\n**الگوهای تکراری شناسایی شده:**\n"
            for pattern in patterns['common_combinations'][:3]:
                components = [
                    COMPONENT_LABELS.get(c, {}).get('fa', c)
                    for c in pattern.get('components', [])
                ]
                result += f"• {', '.join(components)}: {pattern.get('count', 0)} بار تکرار\n"
        
        result += "\n✅ الگوهای این پروژه به حافظه یادگیری اضافه شد!"
        return result
    
    def _get_predictions(self) -> str:
        """
        دریافت پیش‌بینی‌های کامپوننتی
        
        ✅ اصلاح: استفاده از label امن
        """
        project = self.app.get_current_project()
        if not project:
            return "❌ لطفاً ابتدا یک پروژه انتخاب کنید"
        
        devices = project.get_all_devices()
        predictions = self.learning_engine.predict_component_needs(devices)
        
        if not predictions:
            return (
                "📊 هنوز داده‌های کافی برای پیش‌بینی وجود ندارد.\n"
                "برای بهبود پیش‌بینی‌ها، دستور 'learn' را روی چند پروژه اجرا کنید."
            )
        
        result = "🔮 **پیش‌بینی نیازهای کامپوننتی**\n\n"
        result += "بر اساس تحلیل پروژه‌های قبلی، این کامپوننت‌ها ممکن است در پروژه شما مفید باشند:\n\n"
        
        for pred in predictions:
            # ✅ استفاده امن از کلیدها
            priority = pred.get('priority', 'medium')
            emoji = "🔴" if priority == 'high' else "🟡"
            
            # ✅ چک کلید label یا equipment_type
            label = pred.get('label') or pred.get('equipment_type', '?')
            reason = pred.get('reason', '')
            
            result += f"{emoji} **{label}**\n"
            if reason:
                result += f"   دلیل: {reason}\n"
            
            # ===== کامپوننت‌های پیشنهادی =====
            suggested = pred.get('suggested_components', [])
            if suggested:
                result += f"   کامپوننت‌ها: {', '.join(str(s) for s in suggested[:5])}\n"
            
            result += "\n"
        
        return result
    
    def _get_learning_stats(self) -> str:
        """
        دریافت آمار سیستم یادگیری
        
        ✅ اصلاح کامل: استفاده از get و label امن
        """
        stats = self.learning_engine.get_statistics()
        
        result = f"""
📊 **آمار سیستم یادگیری**

**پروژه‌های تحلیل شده:** {stats.get('total_projects_analyzed', 0)}
**Revision های تحلیل شده:** {stats.get('total_revisions_analyzed', 0)}
**کامپوننت‌های یادگیری:** {stats.get('total_components_learned', 0)}
**الگوهای تجهیزات:** {stats.get('total_io_patterns', 0)}
**انواع تجهیزات:** {stats.get('total_equipment_types', 0)}

**پرکاربردترین کامپوننت‌ها:**
"""
        # ===== کامپوننت‌ها =====
        most_common = stats.get('most_common_components', [])
        if most_common:
            for comp in most_common:
                key = comp.get('component', '?')
                count = comp.get('count', 0)
                # ✅ label امن
                label = comp.get('label') or COMPONENT_LABELS.get(key, {}).get('fa', key)
                result += f"• {label} ({key}): {count} بار\n"
        else:
            result += "  (هنوز داده‌ای نیست)\n"
        
        # ===== انواع تجهیزات =====
        top_equipment = stats.get('top_equipment_types', [])
        if top_equipment:
            result += "\n**پرکاربردترین تجهیزات:**\n"
            for eq in top_equipment[:5]:
                result += f"• {eq.get('type', '?')}: {eq.get('count', 0)} بار\n"
        
        # ===== لیست پروژه‌های تحلیل‌شده =====
        analyzed = stats.get('analyzed_list', [])
        if analyzed:
            result += f"\n**پروژه‌های تحلیل شده ({len(analyzed)} Revision):**\n"
            for item in analyzed[:10]:
                result += (
                    f"• **{item.get('project', '?')}** / {item.get('revision', '?')} — "
                    f"{item.get('devices', 0)} دستگاه، {item.get('io', 0)} I/O\n"
                )
            if len(analyzed) > 10:
                result += f"  ... و {len(analyzed) - 10} مورد دیگر\n"
        
        return result
    
    def _get_optimization_suggestions(self) -> str:
        """
        دریافت پیشنهادات بهینه‌سازی
        
        ✅ اصلاح: استفاده امن از label
        """
        project = self.app.get_current_project()
        if not project:
            return "❌ لطفاً ابتدا یک پروژه انتخاب کنید"
        
        devices = project.get_all_devices()
        if not devices:
            return "❌ پروژه هیچ دستگاهی ندارد. ابتدا دستگاه‌ها را اضافه کنید."
        
        current_io = {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0}
        for device in devices:
            current_io['DI'] += getattr(device, 'DI', 0)
            current_io['DO'] += getattr(device, 'DO', 0)
            current_io['AI'] += getattr(device, 'AI', 0)
            current_io['AO'] += getattr(device, 'AO', 0)
        
        # ===== چک امن متد =====
        try:
            if hasattr(self.learning_engine, '_suggest_io_optimization'):
                suggestions = self.learning_engine._suggest_io_optimization(current_io)
            else:
                suggestions = self._fallback_io_suggestions(current_io)
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            suggestions = self._fallback_io_suggestions(current_io)
        
        result = "⚡ **پیشنهادات بهینه‌سازی I/O**\n\n"
        result += f"**I/O فعلی:** DI={current_io['DI']}, DO={current_io['DO']}, "
        result += f"AI={current_io['AI']}, AO={current_io['AO']}\n"
        result += f"**مجموع:** {sum(current_io.values())}\n\n"
        
        for suggestion in suggestions:
            msg = suggestion.get('message', '')
            sug = suggestion.get('suggestion', '')
            result += f"💡 {msg}\n"
            if sug:
                result += f"   ✅ {sug}\n"
            result += "\n"
        
        return result
    
    def _fallback_io_suggestions(self, current_io: Dict[str, int]) -> List[Dict]:
        """پیشنهادات پیش‌فرض اگر متد اصلی موجود نبود"""
        suggestions = []
        total = sum(current_io.values())
        
        if total > 500:
            suggestions.append({
                'message': f'مجموع I/O شما ({total}) زیاد است.',
                'suggestion': 'استفاده از کنترلرهای توزیع‌شده را در نظر بگیرید.',
            })
        elif total < 50:
            suggestions.append({
                'message': f'مجموع I/O کوچک است ({total}).',
                'suggestion': 'می‌توان از کنترلرهای کوچک‌تر مثل MCX-08m2 استفاده کرد.',
            })
        else:
            suggestions.append({
                'message': f'مجموع I/O متعادل است ({total}).',
                'suggestion': 'طراحی فعلی مناسب به نظر می‌رسد.',
            })
        
        return suggestions
    
    def _find_similar_projects(self) -> str:
        """یافتن پروژه‌های مشابه"""
        project = self.app.get_current_project()
        if not project:
            return "❌ لطفاً ابتدا یک پروژه انتخاب کنید"
        
        try:
            similar = self.learning_engine._find_similar_projects(project)
        except Exception as e:
            logger.error(f"Error finding similar projects: {e}")
            return f"❌ خطا در جستجو: {e}"
        
        if not similar:
            return "🔍 هیچ پروژه مشابهی در حافظه یادگیری یافت نشد."
        
        result = "🔗 **پروژه‌های مشابه**\n\n"
        result += f"پروژه فعلی: **{project.name}**\n"
        result += f"تعداد دستگاه‌ها: {len(project.get_all_devices())}\n\n"
        result += "**پروژه‌های مشابه:**\n"
        
        for proj in similar:
            result += f"• **{proj.get('project_name', '?')}**\n"
            result += f"  شباهت: {proj.get('similarity', 0)}%\n"
            result += f"  I/O: {proj.get('io_total', 0)} | دستگاه‌ها: {proj.get('devices_count', 0)}\n\n"
        
        return result
    
    def _get_project_templates(self) -> str:
        """دریافت قالب‌های پروژه"""
        try:
            if hasattr(self.learning_engine, '_get_project_templates'):
                templates = self.learning_engine._get_project_templates()
            else:
                templates = []
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            templates = []
        
        if not templates:
            return (
                "📝 هنوز قالب پروژه‌ای در سیستم وجود ندارد.\n"
                "با دستور 'learn' پروژه‌های خود را به سیستم معرفی کنید."
            )
        
        result = "📋 **قالب‌های پروژه موجود**\n\n"
        result += "این قالب‌ها از پروژه‌های قبلی استخراج شده‌اند:\n\n"
        
        for i, template in enumerate(templates, 1):
            result += f"{i}. **{template.get('name', '?')}**\n"
            result += f"   {template.get('description', '')}\n"
            result += f"   بخش‌ها: {template.get('sections', '')}\n\n"
        
        result += "💡 برای استفاده از یک قالب، می‌توانید ساختار آن را کپی کنید."
        return result
    
    def _get_recommendations(self) -> str:
        """دریافت توصیه‌های کلی"""
        project = self.app.get_current_project()
        
        try:
            if hasattr(self.learning_engine, '_get_best_practices'):
                practices = self.learning_engine._get_best_practices(project)
            else:
                practices = self._default_best_practices()
        except Exception as e:
            logger.error(f"Error getting practices: {e}")
            practices = self._default_best_practices()
        
        result = "💡 **بهترین شیوه‌های مهندسی کنترل**\n\n"
        for i, practice in enumerate(practices, 1):
            result += f"{i}. {practice}\n"
        
        return result
    
    def _default_best_practices(self) -> List[str]:
        """بهترین شیوه‌های پیش‌فرض"""
        return [
            "از نام‌گذاری یکتا برای دستگاه‌ها استفاده کنید (P5a، P5b یا P5، P6، P7)",
            "برای هر پمپ، یک فلوسوئیچ (FS) در نظر بگیرید",
            "در صورت استفاده از VFD، تعداد VSD برابر با PU باشد",
            "دستگاه‌های مشابه را در سکشن‌های اختصاصی گروه‌بندی کنید",
            "نام‌گذاری کامپوننت‌ها را در همه پروژه‌ها یکسان نگه دارید",
            "برای توسعه‌های آینده، I/O ذخیره (SPR) در نظر بگیرید",
            "دستگاه‌های Modbus را به صورت جداگانه مستند کنید",
            "برای اندازه‌گیری‌های حیاتی از سنسورهای AI استفاده کنید",
            "اندازه کابل را با نیاز کامپوننت مطابقت دهید",
            "قبل از خروجی، خطاهای اعتبارسنجی را بررسی کنید",
        ]
    
    # ================================================================
    # UI
    # ================================================================
    
    def start_conversation(self):
        """شروع گفتگو با دستیار"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.title("🤖 AI Project Assistant")
        self.window.geometry("900x650")
        self.window.transient(self.app.root)
        
        # مرکز کردن
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # ===== هدر =====
        header = tk.Frame(self.window, bg='#2C3E50', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="🤖 AI Project Assistant",
            font=("Segoe UI", 14, "bold"),
            fg='white',
            bg='#2C3E50'
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        tk.Label(
            header,
            text="Vahhaj Sanat Co.",
            font=("Segoe UI", 10),
            fg='#BDC3C7',
            bg='#2C3E50'
        ).pack(side=tk.RIGHT, padx=20, pady=15)
        
        # ===== نوار ابزار =====
        toolbar = tk.Frame(self.window, bg='#F8F9FA', height=40)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        buttons = [
            ("🗑️ Clear", self._clear_conversation, '#E74C3C'),
            ("📊 Info", self._show_project_info, '#3498DB'),
            ("📋 Suggestions", self._show_suggestions, '#27AE60'),
            ("📄 Local Proposal", self._generate_local_proposal_clicked, '#8E44AD'),
            ("💾 Save Word", self._save_as_word, '#2980B9'),
            ("📁 Save Multi", self._save_multi_word, '#16A085'),
            ("⚙️ Settings", self._open_settings, '#F39C12'),    # ← ✅ جدید
            ("❌ Close", self.window.destroy, '#95A5A6'),
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                toolbar,
                text=text,
                command=command,
                bg=color,
                fg='white',
                font=("Segoe UI", 8, "bold"),
                relief='flat',
                padx=12,
                pady=4,
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=4, pady=4)
        
        # ===== ناحیه گفتگو =====
        chat_frame = tk.Frame(self.window)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.text_area = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            bg='#FFFFFF'
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        self.text_area.tag_configure("user", foreground="#2C3E50", font=("Segoe UI", 10, "bold"))
        self.text_area.tag_configure("assistant", foreground="#3498DB", font=("Segoe UI", 10))
        self.text_area.tag_configure("system", foreground="#7F8C8D", font=("Segoe UI", 9, "italic"))
        self.text_area.tag_configure("error", foreground="#E74C3C", font=("Segoe UI", 10, "bold"))
        
        self.text_area.config(state=tk.DISABLED)
        
        # ===== ورودی =====
        input_frame = tk.Frame(self.window)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.input_entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 10),
            relief=tk.GROOVE,
            bd=2
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self._send_message())
        
        send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self._send_message,
            bg='#3498DB',
            fg='white',
            font=("Segoe UI", 10, "bold"),
            relief='flat',
            padx=20,
            pady=5,
            cursor='hand2'
        )
        send_btn.pack(side=tk.RIGHT)
        
        # پیام خوش‌آمدگویی
        welcome = """👋 **Welcome to AI Project Assistant!**

I can help you with:
• Analyzing your project data
• Suggesting equipment and components
• Answering technical questions
• Generating proposals
• Providing best practices

**Quick Commands:**
• Type 'help' for this message
• Type 'project info' for project details
• Type 'suggestions' for component suggestions
• Type 'learn' to learn from current project
• Type 'clear' to clear conversation

What would you like to know? 🚀
"""
        self._add_message("assistant", welcome)
        
        self.input_entry.focus()
    
    # ================================================================
    # MESSAGE HANDLING
    # ================================================================

    def _open_settings(self):
        """باز کردن تنظیمات AI"""
        try:
            from gui.ai_settings_dialog import AISettingsDialog
            
            dialog = AISettingsDialog(
                parent=self.window,
                on_save=self._on_settings_saved,
                client=self.client,
            )
            dialog.show()
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror(
                "خطا",
                f"باز کردن تنظیمات ناموفق:\n{e}",
                parent=self.window,
            )

    def _on_settings_saved(self, settings: Dict[str, Any]):
        """Callback بعد از ذخیره تنظیمات"""
        logger.info(f"✅ Settings saved: {list(settings.keys())}")
        
        # بروزرسانی client
        try:
            self.client.reload_from_config()
        except Exception as e:
            logger.error(f"Failed to reload client: {e}")
        
        self._add_message(
            "assistant",
            "✅ **تنظیمات AI با موفقیت ذخیره شد.**\n\n"
            "از این پس درخواست‌ها با تنظیمات جدید ارسال می‌شوند."
        )
    
    def _send_message(self):
        """ارسال پیام کاربر"""
        if self.is_processing:
            logger.debug("⏳ Processing... ignoring")
            return
        
        if not self.input_entry:
            return
        
        message = self.input_entry.get().strip()
        if not message:
            return
        
        # پاک کردن ورودی
        self.input_entry.delete(0, tk.END)
        
        # نمایش پیام کاربر
        self._add_message("user", f"👤 You: {message}")
        
        # ✅ پردازش در Thread
        self.is_processing = True
        self._run_in_thread(self._process_message_logic, message)
    
    def _process_message_logic(self, message: str) -> str:
        """منطق پردازش پیام (بدون دسترسی به UI)"""
        lower_msg = message.lower().strip()
        
        # ============================================================
        # دستورات سریع
        # ============================================================
        if lower_msg == 'help':
            return self._get_help()
        elif lower_msg == 'clear':
            # ✅ اینجا safe است چون clear سبک است
            self._clear_conversation()
            return ""
        elif lower_msg == 'project info':
            return self._get_project_info()
        elif lower_msg == 'suggestions':
            return self._get_suggestions()
        elif 'statistics' in lower_msg or lower_msg == 'stats':
            return self._get_statistics()
        elif lower_msg == 'components':
            return self._get_component_info()
        
        # ============================================================
        # دستورات یادگیری
        # ============================================================
        elif lower_msg == 'learn' or lower_msg == 'یادگیری':
            return self._learn_from_current_project()
        elif lower_msg == 'predict' or lower_msg == 'پیش‌بینی':
            return self._get_predictions()
        elif lower_msg in ('learning stats', 'آمار یادگیری'):
            return self._get_learning_stats()
        elif lower_msg in ('optimize', 'بهینه‌سازی'):
            return self._get_optimization_suggestions()
        elif lower_msg in ('similar', 'مشابه'):
            return self._find_similar_projects()
        elif lower_msg in ('template', 'قالب'):
            return self._get_project_templates()
        elif 'recommend' in lower_msg or 'توصیه' in lower_msg:
            return self._get_recommendations()
        
        # ============================================================
        # پروپوزال‌ها
        # ============================================================
        elif lower_msg in ('proposal', 'پروپوزال', 'local proposal', 'پروپوزال محلی'):
            # ✅ اصلاح: فقط return کن، _on_success نمایش می‌دهد
            return self._generate_local_proposal()
        
        elif lower_msg in ('save word', 'saveword', 'ذخیره word', 'ذخیره ورد'):
            # ✅ مستقیم صدا بزن (خودش _add_message دارد)
            try:
                self._save_as_word()
            except Exception as e:
                return f"❌ خطا در ذخیره Word: {e}"
            return ""
        
        elif lower_msg in ('save multi', 'savemulti', 'ذخیره چند', 'چند فایل'):
            try:
                self._save_multi_word()
            except Exception as e:
                return f"❌ خطا در ذخیره Multi: {e}"
            return ""
        
        elif 'proposal' in lower_msg:
            # AI proposal
            return self._generate_proposal()
        
        # ============================================================
        # درخواست از AI
        # ============================================================
        else:
            return self._query_ai(message)
    
    def _add_message(self, tag: str, content: str):
        """افزودن پیام به ناحیه گفتگو"""
        if not self.text_area:
            return
        
        try:
            self.text_area.config(state=tk.NORMAL)
            
            if tag != "system":
                self.text_area.insert(tk.END, "\n" + "─" * 60 + "\n", "system")
            
            self.text_area.insert(tk.END, content + "\n\n", tag)
            self.text_area.config(state=tk.DISABLED)
            self.text_area.see(tk.END)
        except Exception as e:
            logger.error(f"Error adding message: {e}")
    
    # ================================================================
    # HELP / INFO
    # ================================================================
    
    def _get_help(self) -> str:
        """دریافت راهنما"""
        return """
**📚 دستورات موجود:**

**دستورات عمومی:**
• **help** - نمایش این راهنما
• **clear** - پاک کردن گفتگو
• **project info** - نمایش اطلاعات پروژه فعلی
• **statistics** - نمایش آمار I/O پروژه
• **components** - لیست کامپوننت‌های موجود

**دستورات هوش مصنوعی:**
• **suggestions** - دریافت پیشنهادات هوشمند
• **proposal** - تولید پروپوزال فنی (با AI)
• **پروپوزال محلی** - تولید پروپوزال محلی (بدون AI)

**🚀 دستورات یادگیری:**
• **learn** - یادگیری از پروژه فعلی و ذخیره الگوها
• **predict** - پیش‌بینی نیازهای کامپوننتی
• **learning stats** - نمایش آمار سیستم یادگیری
• **optimize** - پیشنهادات بهینه‌سازی I/O
• **similar** - یافتن پروژه‌های مشابه
• **template** - مشاهده قالب‌های پروژه
• **recommend** - دریافت بهترین شیوه‌ها

**💾 ذخیره:**
• **save word** - ذخیره پروپوزال به Word
• **save multi** - ذخیره به چند فایل Word

**📝 مثال‌های کاربردی:**
1. پروژه جدید باز کنید → `learn` → `predict`
2. `optimize` برای بهبود طراحی
3. `similar` برای یافتن ایده از پروژه‌های قبلی
4. `template` برای مشاهده ساختار پروژه‌های موفق
"""
    
    def _get_project_info(self) -> str:
        """
        دریافت اطلاعات پروژه
        
        ✅ اصلاح: sections از current_revision خوانده می‌شود
        """
        project = self.app.get_current_project()
        if not project:
            return "❌ No project is currently selected. Please create or open a project first."
        
        # ✅ اصلاح: sections در revision است نه project
        current_rev = project.get_current_revision()
        sections_count = len(current_rev.sections) if current_rev else 0
        devices_count = len(current_rev.get_all_devices()) if current_rev else 0
        
        info = f"""
**📋 Project Information**

**Name:** {project.name}
**Client:** {project.client_name or 'Not specified'}
**Consultant:** {project.consultant_name or 'Not specified'}
**Contractor:** {project.contractor_name or 'Not specified'}
**Designer:** {project.designer_name or 'Not specified'}

**Revision:** {current_rev.name if current_rev else '—'}
**Sections:** {sections_count}
**Total Devices:** {devices_count}
**Total Revisions:** {len(project.revisions)}

_Type 'statistics' for detailed I/O statistics_
"""
        return info
    
    def _get_statistics(self) -> str:
        """دریافت آمار پروژه"""
        project = self.app.get_current_project()
        if not project:
            return "❌ No project is currently selected."
        
        # ✅ اصلاح: از current_revision استفاده کن
        current_rev = project.get_current_revision()
        if not current_rev:
            return "❌ Project has no active revision."
        
        stats = current_rev.get_statistics()
        devices = current_rev.get_all_devices()
        
        usage = {}
        for device in devices:
            for field in COMPONENT_LABELS.keys():
                qty = getattr(device, field, 0)
                if qty > 0:
                    usage[field] = usage.get(field, 0) + qty
        
        top_components = sorted(usage.items(), key=lambda x: x[1], reverse=True)[:5]
        
        info = f"""
**📊 Project Statistics**

**I/O Summary:**
• DI: {stats.get('total_di', 0)}
• DO: {stats.get('total_do', 0)}
• AI: {stats.get('total_ai', 0)}
• AO: {stats.get('total_ao', 0)}
• **Total I/O:** {stats.get('total_io', 0)}

**Device Status:**
• Active: {stats.get('active_devices', 0)}
• Inactive: {stats.get('inactive_devices', 0)}

**Top Components:**
"""
        for field, qty in top_components:
            label = COMPONENT_LABELS.get(field, {}).get('en', field)
            info += f"• {label}: {qty}\n"
        
        return info
    
    def _get_suggestions(self) -> str:
        """دریافت پیشنهادها"""
        project = self.app.get_current_project()
        if project:
            # ✅ اصلاح: از current_revision
            current_rev = project.get_current_revision()
            devices = current_rev.get_all_devices() if current_rev else []
            
            if devices:
                total_io = sum(d.get_total_io() for d in devices)
                info = f"""
**💡 Smart Suggestions**

Based on your current project:
• **Total I/O:** {total_io}
• **Devices:** {len(devices)}

**Recommendations:**
"""
                if total_io > 0:
                    cbx = (total_io + 63) // 64
                    fbx = max(0, (total_io + 15) // 16 - cbx)
                    info += f"• Consider using {cbx} ABB CBX-8R8 controllers\n"
                    if fbx > 0:
                        info += f"• Consider using {fbx} ABB FBX-8R8 expansion modules\n"
                
                # ===== چک ایمن =====
                has_motor = any(getattr(d, 'PU', 0) > 0 for d in devices)
                has_sensor = any(
                    getattr(d, 'DTS', 0) > 0 or getattr(d, 'ITS', 0) > 0 or getattr(d, 'RTS', 0) > 0
                    for d in devices
                )
                has_valve = any(getattr(d, 'VA', 0) > 0 for d in devices)
                
                if not has_motor:
                    info += "• You may need motors (PU) for your system\n"
                if not has_sensor:
                    info += "• Consider adding temperature sensors (DTS, ITS, RTS)\n"
                if not has_valve:
                    info += "• Consider adding valve actuators (VA)\n"
            else:
                info = self._get_empty_project_suggestions()
        else:
            info = """
**💡 Suggestions**

Please create a project first to get specific suggestions.

**Common System Types:**
• HVAC Control Systems
• Chiller Plant Controls
• AHU Control Systems
• Pump Control Systems
• Building Management Systems
"""
        
        return info
    
    def _get_empty_project_suggestions(self) -> str:
        """پیشنهادات برای پروژه خالی"""
        return """
**💡 Getting Started Suggestions**

Your project is empty. Here's what to add:

1. **Essential Components:**
   • Motors (PU) - for pumps and fans
   • Temperature Sensors (DTS, ITS, RTS)
   • Pressure Sensors (PT, DPT)
   • Valves (VA) for control

2. **Typical System Components:**
   • Flow Switches (FS)
   • Dampers (DAM_T1, DAM_T2, DAM_T3, DAM_T4)
   • VSD Drives for motor control

3. **Create sections like:**
   • Chiller Plant
   • AHU Systems
   • Pumps
   • Controls
"""
    
    def _get_component_info(self) -> str:
        """دریافت اطلاعات کامپوننت‌ها"""
        return """
**🔧 Available Components**

**Sensors:**
• **DTS** - Duct Temperature Sensor (AI)
• **ITS** - Immersion Temperature Sensor (AI)
• **RTS** - Room Temperature Sensor (AI)
• **DTHS** - Duct Temp & Humidity Sensor (AI)
• **RTHS** - Room Temp & Humidity Sensor (AI)
• **AVS** - Air Velocity Sensor (AI)
• **FS** - Flow Switch (DI)
• **PS** - Pressure Switch (DI)
• **PT** - Pressure Transmitter (AI)
• **DPT** - Differential Pressure Transmitter (AI)

**Actuators:**
• **VA** - Valve Actuator (AI/AO)
• **DAM_T1, DAM_T2** - Damper (DO)
• **DAM_T3, DAM_T4** - Damper (AI/AO)

**Equipment:**
• **PU** - Motor/Pump (DI/DO)
• **VSD** - Variable Speed Drive (AI/AO)
• **SV** - Solenoid Valve (DO)
• **FC** - Fancoil (DO)
• **LIG** - Lighting (DI/DO)

**Other:**
• **FR** - Freeze Protection (DI)
• **AQ** - Air Quality Sensor (AI)
• **SD** - Smoke Detector (DI)
• **LS** - Level Switch (DI)
• **LT** - Level Transmitter (AI)
"""
    
    # ================================================================
    # AI PROPOSAL (External)
    # ================================================================
    
    def _generate_proposal(self) -> str:
        """تولید پیشنهاد پروژه با AI"""
        project = self.app.get_current_project()
        if not project:
            return "❌ Please create a project first to generate a proposal."
        
        # ✅ اصلاح: از current_revision
        current_rev = project.get_current_revision()
        if not current_rev:
            return "❌ Project has no active revision."
        
        devices = current_rev.get_all_devices()
        if not devices:
            return "❌ Please add devices to your project first."
        
        try:
            from ai.deepseek_client import DeepSeekClient
            client = DeepSeekClient()
            
            if not client.api_key:
                return "⚠️ API Key تنظیم نشده است. لطفاً از «پروپوزال محلی» استفاده کنید."
            
            project_data = {
                'name': project.name,
                'client_name': project.client_name,
                'client_phone': project.client_phone,
                'client_address': project.client_address,
                'consultant_name': project.consultant_name,
                'consultant_phone': project.consultant_phone,
                'contractor_name': project.contractor_name,
                'contractor_phone': project.contractor_phone,
                'designer_name': project.designer_name,
                'revision_name': current_rev.name,
            }
            
            proposal = client.generate_proposal(project_data, devices)
            if proposal:
                self.last_proposal = proposal
                return proposal
            else:
                return "⚠️ Could not generate AI proposal. Please check your API key."
        
        except Exception as e:
            logger.error(f"Error generating proposal: {e}", exc_info=True)
            return f"❌ Error generating proposal: {str(e)}"
    
    def _query_ai(self, message: str) -> str:
        """پرسش از AI با Context از Query Engine"""
        try:
            # ============================================================
            # 1. پردازش سوال با Query Engine
            # ============================================================
            result = self.query_engine.process_question(message)
            
            # ============================================================
            # 2. اگر پاسخ مستقیم دارد → همون را برگردان
            # ============================================================
            if result.get('can_answer_directly'):
                logger.info(f"✅ Direct answer for intent: {result.get('intent')}")
                return result.get('direct_answer', '')
            
            # ============================================================
            # 3. چک API key
            # ============================================================
            if not self.client.api_key:
                return (
                    f"{result.get('context', '')}\n\n"
                    "⚠️ برای پاسخ‌های هوشمندتر، لطفاً API Key را در config.json تنظیم کنید."
                )
            
            # ============================================================
            # 4. ساخت prompt با Context
            # ============================================================
            enriched_message = f"""
{result.get('context', '')}

────────────────────────────────────
سوال کاربر: {message}

با توجه به اطلاعات بالا، لطفاً پاسخ دقیق و کامل به کاربر بده.
اگر داده‌ای در Context نیست، صریح بگو که اطلاعات کافی نداری.
"""
            
            # ============================================================
            # 5. ارسال به AI
            # ============================================================
            response = self.client.chat(enriched_message, self.conversation_history)
            
            # ذخیره در تاریخچه
            self.conversation_history.append({"role": "user", "content": message})
            if response:
                self.conversation_history.append({"role": "assistant", "content": response})
            
            return response or "❌ پاسخ خالی از AI"
        
        except Exception as e:
            logger.error(f"Error in _query_ai: {e}", exc_info=True)
            return f"❌ خطا در پردازش سوال: {str(e)}"
    
    # ================================================================
    # LOCAL PROPOSAL
    # ================================================================
    
    def _generate_local_proposal(self) -> str:
        """
        تولید پروپوزال محلی (بدون AI خارجی)
        
        ✅ اصلاح کامل:
        - فقط return می‌کند (نمایش توسط _on_success)
        - Preview حذف شد چون _on_success خودش انجام می‌دهد
        """
        try:
            from ai.local_proposal_generator import LocalProposalGenerator
            
            # ===== چک پروژه =====
            project = self.app.get_current_project()
            if not project:
                return "❌ لطفاً ابتدا یک پروژه انتخاب کنید."
            
            revision = project.get_current_revision()
            if not revision:
                return "❌ پروژه هیچ رویژنی ندارد."
            
            if not revision.sections:
                return "❌ پروژه هیچ سکشنی ندارد."
            
            # ===== تولید =====
            logger.info(f"📄 Generating local proposal for '{project.name}' / '{revision.name}'")
            
            generator = LocalProposalGenerator(self.db, self.app)
            proposal = generator.generate(project, revision.name)
            
            if not proposal:
                return "❌ خطا در تولید پروپوزال (خروجی خالی)"
            
            # ===== ذخیره برای ذخیره‌های بعدی =====
            self.last_proposal = proposal
            logger.info(f"✅ Local proposal generated: {len(proposal)} chars")
            
            # ✅ فقط return کن — _on_success نمایش می‌دهد
            return proposal
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error in _generate_local_proposal: {e}", exc_info=True)
            return f"❌ خطا: {e}"
    
    def _generate_local_proposal_clicked(self):
        """کلیک روی دکمه Local Proposal در toolbar"""
        if self.is_processing:
            return
        self.is_processing = True
        self._run_in_thread(self._generate_local_proposal)
    
    # ================================================================
    # SAVE
    # ================================================================
    
    def _save_as_word(self):
        """ذخیره پروپوزال آخر به صورت Word — در پوشه پروژه"""
        # ===== چک پروپوزال =====
        if not self.last_proposal:
            self._add_message(
                "error",
                "❌ هیچ پروپوزالی تولید نشده.\n\n"
                "ابتدا دکمه «📄 Local Proposal» را بزنید."
            )
            return
        
        # ===== اطلاعات پروژه =====
        project = self.app.get_current_project()
        if not project:
            self._add_message("error", "❌ لطفاً ابتدا یک پروژه انتخاب کنید.")
            return
        
        project_name = project.name
        revision = project.get_current_revision()
        revision_name = revision.name if revision else "Rev-0"
        
        # ===== ساخت پوشه =====
        try:
            project_dir = self.app.attachment_manager.ensure_project_dir(project_name)
            proposals_dir = os.path.join(project_dir, "Reports", "Proposals")
            os.makedirs(proposals_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"❌ Could not create proposals dir: {e}")
            self._add_message("error", f"❌ خطا در ساخت پوشه: {e}")
            return
        
        # ===== نام فایل =====
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_proj = "".join(
            c if c.isalnum() or c in " _-" else "_"
            for c in project_name
        ).strip() or "Project"
        
        filename = f"Proposal_{safe_proj}_{revision_name}_{timestamp}.docx"
        file_path = os.path.join(proposals_dir, filename)
        
        # ===== تولید فایل =====
        try:
            from export.word_proposal_exporter import WordProposalExporter
            
            exporter = WordProposalExporter()
            success = exporter.export(
                content=self.last_proposal,
                output_path=file_path,
                project_name=project_name,
            )
            
            if success:
                size_kb = os.path.getsize(file_path) / 1024
                self._add_message(
                    "assistant",
                    f"✅ **فایل Word ذخیره شد:**\n\n"
                    f"📁 `{file_path}`\n\n"
                    f"📏 حجم: {size_kb:.1f} KB"
                )
                
                if os.name == 'nt':
                    try:
                        os.startfile(file_path)
                    except Exception:
                        pass
            else:
                self._add_message("error", "❌ خطا در ذخیره Word")
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"❌ Error in _save_as_word: {e}", exc_info=True)
            self._add_message("error", f"❌ خطا: {e}")
    
    def _save_multi_word(self):
        """ذخیره پروپوزال به صورت چند فایل Word در پوشه پروژه"""
        if not self.last_proposal:
            self._add_message("error", "❌ هیچ پروپوزالی تولید نشده.")
            return
        
        project = self.app.get_current_project()
        if not project:
            self._add_message("error", "❌ لطفاً ابتدا یک پروژه انتخاب کنید.")
            return
        
        project_name = project.name
        revision = project.get_current_revision()
        if not revision:
            self._add_message("error", "❌ پروژه هیچ رویژنی ندارد.")
            return
        
        revision_name = revision.name
        
        # ===== پوشه =====
        try:
            project_dir = self.app.attachment_manager.ensure_project_dir(project_name)
            proposals_dir = os.path.join(project_dir, "Reports", "Proposals", "Multi")
            os.makedirs(proposals_dir, exist_ok=True)
        except Exception as e:
            self._add_message("error", f"❌ خطا در ساخت پوشه: {e}")
            return
        
        try:
            from export.word_proposal_exporter import WordProposalExporter
            from ai.local_proposal_generator import LocalProposalGenerator
            
            exporter = WordProposalExporter()
            generator = LocalProposalGenerator(self.db, self.app)
            
            results = {}
            
            # ===== ۱. فایل کلی =====
            main_filename = f"Proposal_{project_name}_{revision_name}_MAIN.docx"
            main_path = os.path.join(proposals_dir, main_filename)
            
            if exporter.export(self.last_proposal, main_path, project_name):
                results['main'] = main_path
                logger.info(f"✅ Main: {main_path}")
            
            # ===== ۲. فایل‌های تفکیکی =====
            sections_by_type = generator.detector.group_sections_by_type(revision.sections)
            
            for section_type, sections in sections_by_type.items():
                if section_type == '_unknown':
                    continue
                
                section_content = generator.generate_section_only(
                    project, revision_name, section_type
                )
                
                if not section_content or '❌' in section_content[:20]:
                    continue
                
                display_name = generator.detector.get_section_type_display_name(section_type)
                safe_name = "".join(
                    c if c.isalnum() or c in " _-" else "_"
                    for c in display_name
                ).strip()[:25] or section_type
                
                filename = f"Proposal_{project_name}_{revision_name}_{safe_name}.docx"
                file_path = os.path.join(proposals_dir, filename)
                
                if exporter.export(section_content, file_path, project_name):
                    results[display_name] = file_path
                    logger.info(f"✅ Section: {file_path}")
            
            # ===== گزارش =====
            if results:
                report = f"✅ **{len(results)} فایل Word ذخیره شد:**\n\n"
                report += f"📁 **مسیر:** `{proposals_dir}`\n\n"
                
                if 'main' in results:
                    report += f"📄 **فایل کلی:**\n  • `{os.path.basename(results['main'])}`\n\n"
                
                section_files = {k: v for k, v in results.items() if k != 'main'}
                if section_files:
                    report += f"📂 **فایل‌های تفکیکی ({len(section_files)}):**\n"
                    for section_name, path in section_files.items():
                        try:
                            size_kb = os.path.getsize(path) / 1024
                        except Exception:
                            size_kb = 0
                        report += f"  • `{os.path.basename(path)}` ({size_kb:.1f} KB)\n"
                
                self._add_message("assistant", report)
                
                if os.name == 'nt':
                    try:
                        os.startfile(proposals_dir)
                    except Exception:
                        pass
            else:
                self._add_message("error", "❌ خطا در ذخیره فایل‌ها")
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"❌ Error: {e}", exc_info=True)
            self._add_message("error", f"❌ خطا: {e}")
    
    # ================================================================
    # CLEAR / SHOW
    # ================================================================
    
    def _clear_conversation(self):
        """پاک کردن گفتگو"""
        if not self.text_area:
            return
        
        try:
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete(1.0, tk.END)
            self.text_area.config(state=tk.DISABLED)
            self.conversation_history = []
            self.last_proposal = None
            
            self._add_message("assistant", "🔄 Conversation cleared. How can I help you?")
            
            if self.input_entry:
                self.input_entry.focus()
        except Exception as e:
            logger.error(f"Error clearing: {e}")
    
    def _show_project_info(self):
        """نمایش اطلاعات پروژه"""
        try:
            response = self._get_project_info()
            self._add_message("assistant", response)
        except Exception as e:
            self._add_message("error", f"❌ خطا: {e}")
    
    def _show_suggestions(self):
        """نمایش پیشنهادها"""
        try:
            response = self._get_suggestions()
            self._add_message("assistant", response)
        except Exception as e:
            self._add_message("error", f"❌ خطا: {e}")
    
    # ================================================================
    # PDF SAVE
    # ================================================================
    
    def _get_last_assistant_message(self) -> str:
        """دریافت آخرین پیام assistant از text_area"""
        if not self.text_area:
            return ""
        
        try:
            full_text = self.text_area.get(1.0, tk.END)
            marker = "🤖 Assistant:"
            idx = full_text.rfind(marker)
            
            if idx == -1:
                return full_text.strip()
            
            content = full_text[idx + len(marker):].strip()
            return content
        except Exception as e:
            logger.error(f"Error getting last assistant message: {e}")
            return ""
    
    def _save_as_pdf(self):
        """ذخیره پروپوزال آخر به صورت PDF"""
        content = self._get_last_assistant_message()
        
        if not content:
            self._add_message(
                "error",
                "❌ متنی برای ذخیره وجود ندارد.\nابتدا یک پروپوزال تولید کنید."
            )
            return
        
        project = self.app.get_current_project()
        project_name = project.name if project else "Project"
        
        safe_name = "".join(
            c if c.isalnum() or c in " _-" else "_"
            for c in project_name
        ).strip() or "Project"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"Proposal_{safe_name}_{timestamp}.pdf"
        
        file_path = filedialog.asksaveasfilename(
            title="ذخیره پروپوزال PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=default_filename,
        )
        
        if not file_path:
            return
        
        try:
            from export.pdf_proposal_exporter import PDFProposalExporter
            
            exporter = PDFProposalExporter()
            success = exporter.export(
                content=content,
                output_path=file_path,
                project_name=project_name,
            )
            
            if success:
                self._add_message("assistant", f"✅ **PDF ذخیره شد:**\n{file_path}")
                
                if os.name == 'nt':
                    try:
                        os.startfile(file_path)
                    except Exception:
                        pass
            else:
                self._add_message("error", "❌ خطا در ذخیره PDF")
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._add_message("error", f"❌ خطا در ذخیره PDF: {e}")