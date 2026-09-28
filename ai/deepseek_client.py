# ai/deepseek_client.py
"""
کلاینت API CodeCraft — نسخه 4.0

✅ API Key از config.json خوانده می‌شود
✅ پشتیبانی از Environment Variables
✅ امکان تغییر مدل، Base URL، Timeout و...
✅ متد تست اتصال
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from openai import OpenAI

from utils.paths import get_resource_path
from utils.config_manager import get_config
from core import COMPONENT_LABELS, CABLE_SIZE

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """
    کلاینت ارتباط با API CodeCraft (سازگار با OpenAI)
    
    Usage:
        client = DeepSeekClient()
        if client.is_configured():
            response = client.chat("سلام")
    """
    
    # ===== مقادیر پیش‌فرض =====
    DEFAULT_BASE_URL = "https://codecraftapi.com/v1"
    DEFAULT_MODEL = "claude-opus-4.8"
    DEFAULT_TIMEOUT = 120.0
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_TOKENS = 4000
    
    # ===== مدل‌های پیشنهادی =====
    AVAILABLE_MODELS = [
        "claude-opus-4.8",
        "claude-sonnet-4.5",
        "claude-haiku-4",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "deepseek-chat",
        "deepseek-reasoner",
    ]
    
    def __init__(self, config_manager=None):
        """
        Args:
            config_manager: (اختیاری) نمونه ConfigManager
        """
        self.config = config_manager or get_config()
        self.client: Optional[OpenAI] = None
        
        # ===== بارگذاری تنظیمات =====
        self._load_settings()
        
        # ===== ساخت کلاینت =====
        self._init_client()
    
    # ============================================================
    # SETTINGS
    # ============================================================
    
    def _load_settings(self):
        """بارگذاری تنظیمات از config"""
        self.api_key = (self.config.get('api_key', '') or '').strip()
        self.base_url = (self.config.get('base_url', '') or self.DEFAULT_BASE_URL).strip()
        self.model = (self.config.get('model', '') or self.DEFAULT_MODEL).strip()
        
        try:
            self.timeout = float(self.config.get('timeout', self.DEFAULT_TIMEOUT))
        except (ValueError, TypeError):
            self.timeout = self.DEFAULT_TIMEOUT
        
        try:
            self.temperature = float(self.config.get('temperature', self.DEFAULT_TEMPERATURE))
        except (ValueError, TypeError):
            self.temperature = self.DEFAULT_TEMPERATURE
        
        try:
            self.max_tokens = int(self.config.get('max_tokens', self.DEFAULT_MAX_TOKENS))
        except (ValueError, TypeError):
            self.max_tokens = self.DEFAULT_MAX_TOKENS
    
    def _init_client(self):
        """ساخت کلاینت OpenAI"""
        self.client = None
        
        if not self.api_key:
            logger.warning("⚠️ API Key not configured")
            return
        
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                max_retries=0,
                timeout=self.timeout,
            )
            logger.info(f"✅ OpenAI client initialized (model={self.model})")
        except Exception as e:
            logger.error(f"❌ Could not init client: {e}")
            self.client = None
    
    # ============================================================
    # RELOAD
    # ============================================================
    
    def reload_from_config(self):
        """بارگذاری مجدد تنظیمات از config.json"""
        logger.info("🔄 Reloading config...")
        self.config.reload()
        self._load_settings()
        self._init_client()
    
    def set_api_key(self, api_key: str):
        """تنظیم API Key و ذخیره"""
        self.config.set('api_key', api_key)
        self.api_key = api_key.strip()
        self._init_client()
    
    def update_settings(self, settings: Dict[str, Any]):
        """
        بروزرسانی چند تنظیم
        
        Args:
            settings: {'api_key': '...', 'model': '...', ...}
        """
        for key, value in settings.items():
            self.config.set(key, value)
        
        # ذخیره در فایل
        self.config.save()
        
        # بارگذاری مجدد
        self._load_settings()
        self._init_client()
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    def is_configured(self) -> bool:
        """آیا تنظیمات کامل است؟"""
        return bool(self.api_key) and bool(self.base_url) and bool(self.model)
    
    def get_config_errors(self) -> Dict[str, str]:
        """دریافت خطاهای تنظیمات"""
        return self.config.validate()
    
    # ============================================================
    # CONNECTION TEST
    # ============================================================
    
    def test_connection(self) -> Dict[str, Any]:
        """
        تست اتصال به API
        
        Returns:
            {
                'success': bool,
                'message': str,
                'models': list,
                'elapsed': float,
            }
        """
        import time
        start = time.time()
        
        result = {
            'success': False,
            'message': '',
            'models': [],
            'elapsed': 0.0,
        }
        
        # ===== چک تنظیمات =====
        if not self.api_key:
            result['message'] = '❌ API Key تنظیم نشده است'
            return result
        
        if not self.client:
            self._init_client()
        
        if not self.client:
            result['message'] = '❌ کلاینت API ساخته نشد'
            return result
        
        # ===== تست =====
        try:
            models = self.client.models.list()
            models_list = [m.id for m in models.data] if models else []
            
            result['success'] = True
            result['message'] = f'✅ اتصال موفق — {len(models_list)} مدل موجود'
            result['models'] = models_list
        
        except Exception as e:
            error_msg = str(e)
            
            # پیام‌های دوستانه
            if "401" in error_msg or "invalid" in error_msg.lower():
                result['message'] = '❌ API Key نامعتبر است'
            elif "502" in error_msg or "Bad Gateway" in error_msg:
                result['message'] = '❌ سرور در دسترس نیست (502)'
            elif "timeout" in error_msg.lower():
                result['message'] = '⏱️ Timeout — سرور پاسخ نداد'
            elif "connection" in error_msg.lower():
                result['message'] = '❌ خطای اتصال — اینترنت را بررسی کنید'
            elif "404" in error_msg:
                result['message'] = f'❌ مدل "{self.model}" یافت نشد'
            else:
                result['message'] = f'❌ خطا: {error_msg[:200]}'
        
        result['elapsed'] = time.time() - start
        return result
    
    def list_available_models(self) -> List[str]:
        """دریافت لیست مدل‌های موجود"""
        if not self.client:
            return []
        
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    # ============================================================
    # CHAT
    # ============================================================
    
    def chat(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Optional[str]:
        """
        ارسال پیام و دریافت پاسخ
        
        Args:
            message: متن پیام
            history: تاریخچه گفتگو
            max_tokens: حداکثر توکن (None → از config)
            temperature: دمای مدل (None → از config)
        
        Returns:
            پاسخ یا پیام خطا
        """
        # ===== چک تنظیمات =====
        if not self.api_key:
            return (
                "⚠️ API Key تنظیم نشده است.\n\n"
                "برای تنظیم، از منوی «⚙️ Settings» استفاده کنید."
            )
        
        if not self.client:
            self._init_client()
            if not self.client:
                return "❌ خطا در ساخت کلاینت API"
        
        try:
            # ===== ساخت messages =====
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a professional control systems engineer and technical consultant. "
                        "You help with building automation, HVAC controls, and industrial control systems. "
                        "Provide clear, accurate, and helpful responses in Persian (فارسی). "
                        "Use professional technical terminology. Be practical and solution-oriented."
                    )
                }
            ]
            
            if history:
                messages.extend(history[-10:])
            
            messages.append({"role": "user", "content": message})
            
            # ===== فراخوانی API =====
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            )
            
            if response and response.choices:
                return response.choices[0].message.content
            else:
                return "❌ پاسخ خالی از API"
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Chat error: {error_msg}")
            
            if "502" in error_msg or "Bad Gateway" in error_msg:
                return f"❌ خطای سرور (502). لطفاً دوباره تلاش کنید.\n{error_msg[:200]}"
            elif "404" in error_msg:
                return f"❌ مدل '{self.model}' یافت نشد.\n{error_msg[:200]}"
            elif "401" in error_msg:
                return f"❌ API Key نامعتبر است.\n{error_msg[:200]}"
            elif "timeout" in error_msg.lower():
                return f"⏱️ Timeout — سرور پاسخ نداد.\n{error_msg[:200]}"
            else:
                return f"❌ خطا: {error_msg[:300]}"
    
    # ============================================================
    # PROPOSAL TEMPLATE
    # ============================================================
    
    def _load_proposal_template(self) -> str:
        """بارگذاری قالب پروپوزال از فایل"""
        template_path = get_resource_path("ai", "proposal_template.txt")
        
        try:
            if not template_path.exists():
                logger.warning(f"Template file not found: {template_path}")
                return ""
            
            return template_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error loading proposal template: {e}")
            return ""
    
    def _load_proposal_instructions(self) -> str:
        """بارگذاری دستورالعمل پروپوزال از فایل"""
        instructions_path = get_resource_path("ai", "proposal_instructions.txt")
        
        try:
            if not instructions_path.exists():
                logger.warning(f"Instructions file not found: {instructions_path}")
                return ""
            
            return instructions_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error loading proposal instructions: {e}")
            return ""
    
    # ============================================================
    # PROPOSAL
    # ============================================================
    
    def generate_proposal(self, project_data: Dict, devices: List) -> Optional[str]:
        """تولید پروپوزال فنی بر اساس نمونه قالب"""
        if not self.api_key:
            return None
        
        try:
            import math
            
            # ===== بارگذاری قالب =====
            template = self._load_proposal_template()
            instructions = self._load_proposal_instructions()
            
            if not template:
                return "⚠️ فایل قالب (proposal_template.txt) یافت نشد."
            
            if not instructions:
                return "⚠️ فایل دستورالعمل (proposal_instructions.txt) یافت نشد."
            
            # ===== محاسبات I/O =====
            total_di = sum(getattr(d, 'DI', 0) for d in devices)
            total_do = sum(getattr(d, 'DO', 0) for d in devices)
            total_ai = sum(getattr(d, 'AI', 0) for d in devices)
            total_ao = sum(getattr(d, 'AO', 0) for d in devices)
            total_io = total_di + total_do + total_ai + total_ao
            
            cbx_total = math.ceil(total_io / 64) if total_io > 0 else 0
            fbx_total = max(0, math.ceil(total_io / 16) - cbx_total) if total_io > 0 else 0
            
            # ===== ساخت لیست دستگاه‌ها =====
            devices_detail = []
            
            for i, motor in enumerate(devices, 1):
                name = getattr(motor, 'Name', '') or f'دستگاه {i}'
                description = getattr(motor, 'Description', '') or 'ندارد'
                info = getattr(motor, 'INFO', '') or ''
                smart_tag = getattr(motor, 'SmartTag', '') or ''
                
                di = getattr(motor, 'DI', 0)
                do = getattr(motor, 'DO', 0)
                ai = getattr(motor, 'AI', 0)
                ao = getattr(motor, 'AO', 0)
                device_io = di + do + ai + ao
                
                active_components = []
                if hasattr(motor, 'get_active_components'):
                    try:
                        for comp in motor.get_active_components(use_labels=True):
                            active_components.append(
                                f"{comp['label_fa']} ({comp['key']}): {comp['quantity']}"
                            )
                    except Exception:
                        pass
                
                device_text = f"\nدستگاه {i}: {name}"
                if smart_tag:
                    device_text += f"\n  - SmartTag: {smart_tag}"
                device_text += f"\n  - توضیحات: {description}"
                if info:
                    device_text += f"\n  - اطلاعات: {info}"
                device_text += f"\n  - I/O: DI={di}, DO={do}, AI={ai}, AO={ao} (جمع: {device_io})"
                if active_components:
                    device_text += f"\n  - کامپوننت‌ها: {', '.join(active_components)}"
                
                devices_detail.append(device_text)
            
            devices_text = "\n".join(devices_detail)
            
            # ===== جایگزینی متغیرها =====
            filled_template = template \
                .replace("{PROJECT_NAME}", project_data.get('name', 'N/A')) \
                .replace("{CLIENT_NAME}", project_data.get('client_name', 'N/A')) \
                .replace("{DATE}", datetime.now().strftime('%Y/%m/%d')) \
                .replace("{REVISION}", project_data.get('revision_name', 'Rev-0')) \
                .replace("{COMPANY_NAME}", "Vahhaj Sanat Energy")
            
            # ===== ساخت prompt =====
            prompt = f"""
{instructions}

═══════════════════════════════════════════════════════════
نمونه پروپوزال مرجع:
═══════════════════════════════════════════════════════════
{filled_template}

═══════════════════════════════════════════════════════════
داده‌های پروژه فعلی:
═══════════════════════════════════════════════════════════
- نام پروژه: {project_data.get('name', 'N/A')}
- مشتری: {project_data.get('client_name', 'N/A')}
- مشاور: {project_data.get('consultant_name', 'N/A')}
- پیمانکار: {project_data.get('contractor_name', 'N/A')}
- طراح: {project_data.get('designer_name', 'N/A')}
- تاریخ: {datetime.now().strftime('%Y/%m/%d')}

═══════════════════════════════════════════════════════════
خلاصه فنی:
═══════════════════════════════════════════════════════════
- مجموع DI: {total_di}
- مجموع DO: {total_do}
- مجموع AI: {total_ai}
- مجموع AO: {total_ao}
- مجموع I/O: {total_io}
- تعداد دستگاه‌ها: {len(devices)}
- CBX-8R8: {cbx_total}
- FBX-8R8: {fbx_total}

═══════════════════════════════════════════════════════════
لیست کامل دستگاه‌ها:
═══════════════════════════════════════════════════════════
{devices_text}

═══════════════════════════════════════════════════════════
حالا پروپوزال کامل بنویسید.
"""
            
            return self.chat(prompt, [], max_tokens=self.max_tokens)
        
        except Exception as e:
            logger.error(f"Error generating proposal: {e}", exc_info=True)
            return None


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['DeepSeekClient']