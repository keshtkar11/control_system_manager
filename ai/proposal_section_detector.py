# ai/proposal_section_detector.py
"""
تشخیص نوع سکشن از نام/توضیحات

نسخه 2.0 — اصلاح‌شده
- ✅ اولویت: توضیحات > نام
- ✅ Regex برای نام‌های ترکیبی
- ✅ تشخیص بر اساس دستگاه‌ها (fallback)
- ✅ پشتیبانی از نام‌های بیمارستانی
- ✅ پشتیبانی از نام‌های فارسی
"""

import re
import logging
from typing import Optional, Dict, List, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


# ================================================================
# SECTION TYPE DEFINITIONS
# ================================================================

SECTION_KEYWORDS = {
    'boiler': [
        # انگلیسی
        'boiler', 'boilers', 'hwb', 'hot water boiler', 'steam boiler',
        # فارسی
        'بویلر', 'دیگ', 'دیگ بخار', 'دیگ آبگرم', 'بویلرها', 'دیگ‌ها',
        # اختصارات
        'bl-', 'blr-',
    ],
    'chiller': [
        'chiller', 'chillers', 'air-cooled chiller', 'water-cooled chiller',
        'چیلر', 'چیلرها', 'چیلر هوا خنک', 'چیلر آب خنک',
        'ch-', 'chl-', 'chiller-',
    ],
    'primary_loop': [
        'primary loop', 'primary', 'low loss header', 'llh',
        'مدار اولیه', 'لوپ اولیه', 'هدر',
        'pl-', 'pri-',
    ],
    'secondary_loop': [
        'secondary loop', 'secondary', 'variable speed pump',
        'مدار ثانویه', 'لوپ ثانویه', 'پمپ دور متغیر',
        'sl-', 'sec-',
    ],
    'dhw': [
        'dhw', 'domestic hot water', 'hot water cylinder', 'calorifier',
        'آبگرم مصرفی', 'آب گرم مصرفی', 'منبع کویلی', 'مخزن dhw',
        'dhw-',
    ],
    'expansion_tank': [
        'expansion', 'expansion tank', 'make-up', 'make up',
        'انبساط', 'منبع انبساط', 'منبع انبساط بسته', 'میکاپ',
        'et-', 'exp-', 'ex-',
    ],
    'booster_pump': [
        'booster', 'booster pump', 'fire pump', 'jockey',
        'بوستر', 'بوستر پمپ', 'پمپ آتش نشانی', 'پمپ بوستر',
        'bp-', 'boost-',
    ],
    'ahu': [
        'ahu', 'air handling', 'air handler', 'air handling unit',
        'air handeling unit',  # ✅ غلط املایی رایج
        'هواساز', 'یونیت', 'هواسازها',
        'ahu-', 'air-',
        # ✅ نام‌های تخصصی بیمارستانی
        'icu', 'nicu', 'ccu', 'cath lab', 'post cath', 'cardiac',
        'surgery room', 'operating room', 'or-', 'clean room',
        'isolation room', 'emergency room', 'er-',
        'pharmacy', 'laboratory', 'lab-',
        # ✅ نام‌های عمومی
        'air handling', 'supply air', 'return air',
    ],
    'fancoil': [
        'fancoil', 'fan coil', 'fcu', 'fan-coil',
        'فن کویل', 'فن‌کویل', 'فنکویل',
        'fcu-', 'fc-',
    ],
    'cooling_tower': [
        'cooling tower', 'ct-', 'tower',
        'برج خنک', 'برج خنک‌کننده', 'کولینگ تاور',
        'tower-',
    ],
    'heat_exchanger': [
        'heat exchanger', 'hx-', 'phe', 'plate heat exchanger',
        'مبدل', 'مبدل حرارتی', 'هیت اکسچنجر',
        'hex-',
    ],
    'exhaust_fan': [
        'exhaust fan', 'exhuast fan', 'exhaust', 'ef-', 'ex-',
        'فن تخلیه', 'هوای تخلیه', 'اگزاست',
    ],
    'supply_fan': [
        'supply fan', 'supply air', 'sf-', 'sa-',
        'فن تازه', 'هوای تازه',
    ],
    'pump': [
        'pump', 'pumps', 'circulation pump', 'circ pump',
        'پمپ', 'پمپ‌ها', 'پمپ سیرکولاسیون',
        'p-', 'pmp-',
    ],
    'fan': [
        'fan', 'fans', 'blower',
        'فن', 'فن‌ها', 'بلوور',
        'f-',
    ],
    'mechanical_room': [
        'mechanical room', 'mech room', 'plant room', 'equipment room',
        'موتورخانه', 'اتاق تاسیسات', 'اتاق مکانیک',
        'mr-', 'mech-',
    ],
    'building': [
        'building', 'floor', 'level', 'zone',
        'ساختمان', 'طبقه', 'گراند فلور', 'grand floor',
        'fl-', 'floor-',
    ],
    'panel': [
        'panel', 'control panel', 'mcc', 'motor control center',
        'تابلو', 'تابلو برق', 'پنل', 'کنترل پنل',
        'mcc-', 'panel-',
    ],
    'hardware': [
        'hardware', 'controller', 'cbx', 'fbx', 'mcx',
        'سخت‌افزار', 'سخت افزار', 'کنترلر', 'کنترل‌کننده',
    ],
}

# ================================================================
# SPECIAL KEYWORDS FOR DESCRIPTION
# ================================================================

# این کلمات در توضیحات، خیلی دقیق‌تر از نام عمل می‌کنند
DESCRIPTION_PRIORITY_KEYWORDS = {
    'ahu': [
        'air handling', 'air handeling', 'ahu',
        'هواساز', 'یونیت هواساز',
    ],
    'chiller': ['chiller', 'چیلر'],
    'boiler': ['boiler', 'دیگ', 'بویلر'],
    'mechanical_room': ['mechanical room', 'موتورخانه'],
    'exhaust_fan': ['exhaust fan', 'exhuast fan', 'فن تخلیه'],
    'pump': ['pump', 'پمپ'],
    'fan': ['fan', 'فن'],
}


# ================================================================
# SECTION DETECTOR
# ================================================================

class ProposalSectionDetector:
    """
    تشخیص نوع سکشن بر اساس نام، توضیحات و دستگاه‌ها
    
    اولویت:
    1. توضیحات (اگر شامل کلمه کلیدی باشد)
    2. نام (regex + keyword)
    3. دستگاه‌ها (analysis)
    """
    
    def __init__(self):
        self.section_keywords = SECTION_KEYWORDS
        self.description_keywords = DESCRIPTION_PRIORITY_KEYWORDS
    
    # ================================================================
    # MAIN DETECT
    # ================================================================
    
    def detect(self, section_name: str, section_description: str = '') -> Optional[str]:
        """
        تشخیص نوع سکشن
        
        Args:
            section_name: نام سکشن
            section_description: توضیحات (اختیاری)
        
        Returns:
            section_type یا None
        """
        if not section_name:
            return None
        
        # ============================================================
        # 1. اولویت اول: توضیحات
        # ============================================================
        if section_description:
            desc_type = self._detect_from_description(section_description)
            if desc_type:
                logger.debug(
                    f"✅ Section '{section_name}' → '{desc_type}' "
                    f"(from description)"
                )
                return desc_type
        
        # ============================================================
        # 2. اولویت دوم: نام (با regex و keyword)
        # ============================================================
        name_type = self._detect_from_name(section_name)
        if name_type:
            logger.debug(
                f"✅ Section '{section_name}' → '{name_type}' "
                f"(from name)"
            )
            return name_type
        
        # ============================================================
        # 3. ترکیب نام + توضیحات
        # ============================================================
        combined = f"{section_name} {section_description}".strip()
        combined_type = self._detect_from_name(combined)
        if combined_type:
            logger.debug(
                f"✅ Section '{section_name}' → '{combined_type}' "
                f"(from combined)"
            )
            return combined_type
        
        logger.debug(f"⚠️ Section '{section_name}' — unknown type")
        return None
    
    def _detect_from_description(self, description: str) -> Optional[str]:
        """تشخیص از توضیحات"""
        if not description:
            return None
        
        desc_lower = description.lower().strip()
        desc_lower = desc_lower.replace('\u200c', ' ')
        desc_lower = re.sub(r'\s+', ' ', desc_lower)
        
        for section_type, keywords in self.description_keywords.items():
            for kw in keywords:
                kw_clean = kw.lower().replace('\u200c', ' ')
                if kw_clean in desc_lower:
                    return section_type
        
        return None
    
    def _detect_from_name(self, name: str) -> Optional[str]:
        """تشخیص از نام با regex و keyword"""
        if not name:
            return None
        
        name_lower = name.lower().strip()
        name_lower = name_lower.replace('\u200c', ' ')
        name_lower = re.sub(r'\s+', ' ', name_lower)
        
        # ============================================================
        # 1. الگوهای regex خاص
        # ============================================================
        regex_patterns = [
            # AHU با شماره
            (r'\bahu\s*[-\(]?\s*\d+', 'ahu'),
            (r'\bahu\b', 'ahu'),
            # ICU, NICU, CCU
            (r'\bicu\b', 'ahu'),
            (r'\bnicu\b', 'ahu'),
            (r'\bccu\b', 'ahu'),
            # Surgery Room
            (r'surgery\s*room', 'ahu'),
            (r'operating\s*room', 'ahu'),
            # Cath Lab
            (r'cath\s*lab', 'ahu'),
            (r'post\s*cath', 'ahu'),
            # Cardiac
            (r'cardiac', 'ahu'),
            # Floor
            (r'\bfloor\s*\d+', 'building'),
            (r'grand\s*floor', 'building'),
            # Mechanical Room
            (r'mechanical\s*room', 'mechanical_room'),
            # Exhaust Fan
            (r'exhaust\s*fan', 'exhaust_fan'),
            (r'exhuast\s*fan', 'exhaust_fan'),
            # Booster
            (r'booster\s*pump', 'booster_pump'),
            # Air Handling
            (r'air\s*handl', 'ahu'),
        ]
        
        for pattern, section_type in regex_patterns:
            if re.search(pattern, name_lower):
                return section_type
        
        # ============================================================
        # 2. Keyword matching
        # ============================================================
        for section_type, keywords in self.section_keywords.items():
            for keyword in keywords:
                kw_clean = keyword.lower().replace('\u200c', ' ').strip()
                
                if not kw_clean:
                    continue
                
                # کلمات کوتاه → word boundary
                if len(kw_clean) <= 3:
                    pattern = r'(?:^|[\s\-_\(])' + re.escape(kw_clean) + r'(?:$|[\s\-_\)])'
                    if re.search(pattern, name_lower):
                        return section_type
                # کلمات بلند → substring
                else:
                    if kw_clean in name_lower:
                        return section_type
        
        return None
    
    # ================================================================
    # DETECT FROM DEVICES (fallback)
    # ================================================================
    
    def detect_from_devices(self, devices: List) -> Optional[str]:
        """
        ✅ جدید: تشخیص نوع سکشن از روی دستگاه‌های داخل آن
        
        این متد زمانی استفاده می‌شود که نام و توضیحات کافی نباشند.
        
        Args:
            devices: لیست دستگاه‌های سکشن
        
        Returns:
            section_type یا None
        """
        if not devices:
            return None
        
        # ===== شمارش انواع تجهیزات =====
        equipment_counter = Counter()
        
        for device in devices:
            # ===== از SmartTag =====
            smart_tag = (getattr(device, 'SmartTag', '') or '').upper()
            name = (getattr(device, 'Name', '') or '').upper()
            desc = (getattr(device, 'Description', '') or '').upper()
            combined = f"{smart_tag} {name} {desc}"
            
            # تشخیص
            eq_type = self._guess_equipment_type(combined)
            if eq_type:
                equipment_counter[eq_type] += 1
        
        if not equipment_counter:
            return None
        
        # ===== نوع غالب =====
        most_common_type, count = equipment_counter.most_common(1)[0]
        
        # ===== نقشه‌برداری تجهیز → سکشن =====
        equipment_to_section = {
            'AHU': 'ahu',
            'CHILLER': 'chiller',
            'BOILER': 'boiler',
            'PUMP': 'pump',
            'FAN': 'fan',
            'FCU': 'fancoil',
            'COOLING_TOWER': 'cooling_tower',
            'DHW': 'dhw',
            'BOOSTER': 'booster_pump',
            'EXPANSION': 'expansion_tank',
            'VALVE': 'pump',  # شیر معمولاً در پمپ‌ها
            'VAV': 'ahu',
        }
        
        return equipment_to_section.get(most_common_type)
    
    def _guess_equipment_type(self, text: str) -> Optional[str]:
        """حدس نوع تجهیز از متن"""
        patterns = {
            'AHU': ['AHU', 'AIR HANDLING', 'AIR HANDELING', 'هواساز'],
            'CHILLER': ['CHILLER', 'CH-', 'چیلر'],
            'BOILER': ['BOILER', 'BLR', 'HWB', 'دیگ', 'بویلر'],
            'PUMP': ['PUMP', 'P-', 'PU-', 'CWP', 'HWP', 'پمپ'],
            'FAN': ['FAN', 'F-', 'SF-', 'EF-', 'RF-', 'فن'],
            'FCU': ['FCU', 'FANCOIL', 'فن کویل'],
            'COOLING_TOWER': ['COOLING TOWER', 'CT-', 'برج'],
            'DHW': ['DHW', 'آبگرم'],
            'BOOSTER': ['BOOSTER', 'BP-', 'بوستر'],
            'EXPANSION': ['EXPANSION', 'ET-', 'EX-', 'انبساط'],
            'VAV': ['VAV'],
            'VALVE': ['VALVE', 'VA-', 'VLV-', 'شیر'],
        }
        
        for eq_type, keywords in patterns.items():
            for kw in keywords:
                if kw in text:
                    return eq_type
        
        return None
    
    # ================================================================
    # DETECT WITH CONFIDENCE
    # ================================================================
    
    def detect_with_confidence(
        self,
        section_name: str,
        section_description: str = ''
    ) -> Tuple[Optional[str], float, str]:
        """
        تشخیص با درجه اطمینان
        
        Returns:
            (section_type, confidence, matched_keyword)
        """
        if not section_name:
            return (None, 0.0, '')
        
        # ===== روش ۱: توضیحات (بالاترین اطمینان) =====
        if section_description:
            desc_type = self._detect_from_description(section_description)
            if desc_type:
                return (desc_type, 0.95, 'description')
        
        # ===== روش ۲: نام =====
        name_type = self._detect_from_name(section_name)
        if name_type:
            return (name_type, 0.85, 'name')
        
        # ===== روش ۳: ترکیب =====
        combined = f"{section_name} {section_description}"
        combined_type = self._detect_from_name(combined)
        if combined_type:
            return (combined_type, 0.70, 'combined')
        
        return (None, 0.0, '')
    
    # ================================================================
    # GROUP SECTIONS BY TYPE
    # ================================================================
    
    def group_sections_by_type(self, sections: list) -> Dict[str, List]:
        """
        گروه‌بندی سکشن‌ها بر اساس نوع
        
        برای سکشن‌های نامشخص، از دستگاه‌های داخلشان استفاده می‌کند.
        """
        result = {}
        unknown = []
        
        for section in sections:
            name = getattr(section, 'name', '')
            desc = getattr(section, 'description', '')
            
            # ===== تشخیص =====
            section_type = self.detect(name, desc)
            
            # ===== fallback: از دستگاه‌ها =====
            if not section_type:
                devices = getattr(section, 'devices', [])
                if devices:
                    section_type = self.detect_from_devices(devices)
                    if section_type:
                        logger.info(
                            f"✅ Section '{name}' → '{section_type}' "
                            f"(from {len(devices)} devices)"
                        )
            
            # ===== اضافه به نتیجه =====
            if section_type:
                if section_type not in result:
                    result[section_type] = []
                result[section_type].append(section)
            else:
                unknown.append(section)
        
        # ===== سکشن‌های نامشخص =====
        if unknown:
            result['_unknown'] = unknown
            logger.warning(
                f"⚠️ {len(unknown)} unknown sections: "
                f"{[getattr(s, 'name', '?') for s in unknown]}"
            )
        
        return result
    
    # ================================================================
    # HELPERS
    # ================================================================
    
    def get_section_type_display_name(self, section_type: str) -> str:
        """نام نمایشی نوع سکشن"""
        names = {
            'boiler': 'بویلرها (Boiler)',
            'chiller': 'چیلرها (Chiller)',
            'primary_loop': 'مدار اولیه (Primary Loop)',
            'secondary_loop': 'مدار ثانویه (Secondary Loop)',
            'dhw': 'آبگرم مصرفی (DHW)',
            'expansion_tank': 'منبع انبساط (Expansion Tank)',
            'booster_pump': 'بوسترپمپ (Booster Pump)',
            'ahu': 'هواساز (AHU)',
            'fancoil': 'فن‌کویل (Fan Coil)',
            'cooling_tower': 'برج خنک‌کننده (Cooling Tower)',
            'heat_exchanger': 'مبدل حرارتی (Heat Exchanger)',
            'exhaust_fan': 'فن تخلیه (Exhaust Fan)',
            'supply_fan': 'فن تازه (Supply Fan)',
            'pump': 'پمپ‌ها (Pump)',
            'fan': 'فن‌ها (Fan)',
            'mechanical_room': 'موتورخانه (Mechanical Room)',
            'building': 'ساختمان (Building)',
            'panel': 'تابلو برق (Panel)',
            'hardware': 'سخت‌افزار (Hardware)',
            '_unknown': 'سایر (Other)',
        }
        return names.get(section_type, section_type)


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['ProposalSectionDetector', 'SECTION_KEYWORDS']