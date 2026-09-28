# ai/query_templates.py
"""
قالب‌های تشخیص intent از سوال کاربر

⚠️ نسخه 3.0 — با رفع باگ‌ها
- ترتیب صحیح: COUNT_COMPONENTS > LIST_SECTIONS > LIST_PROJECTS
- اولویت count_components بر count_projects
- نگه‌داشتن case اصلی برای نام پروژه
- پشتیبانی از کلمات عامیانه فارسی (چیه، چی، کدام، ...)
"""

import re
from typing import Dict, List, Optional, Any


# ================================================================
# COMPONENT ALIASES
# ================================================================

COMPONENT_ALIASES = {
    'PU': ['pu', 'pump', 'motor', 'موتور', 'پمپ', 'پمپ‌ها', 'موتورها'],
    'DTS': ['dts', 'duct temp', 'duct temperature', 'سنسور دمای کانال'],
    'ITS': ['its', 'immersion', 'immersion temp', 'سنسور مستغرق', 'سنسور دمای غوطه'],
    'RTS': ['rts', 'room temp', 'room temperature', 'سنسور دمای اتاق'],
    'DTHS': ['dths', 'duct temp humidity', 'دما و رطوبت کانال'],
    'RTHS': ['rths', 'room temp humidity', 'دما و رطوبت اتاق'],
    'AVS': ['avs', 'air velocity', 'سرعت هوا'],
    'PT': ['pt', 'pressure transmitter', 'ترانسمیتر فشار', 'سنسور فشار'],
    'PS': ['ps', 'pressure switch', 'سوئیچ فشار'],
    'DPT': ['dpt', 'diff pressure', 'differential pressure', 'فشار تفاضلی'],
    'DPS': ['dps', 'diff pressure switch', 'سوئیچ فشار تفاضلی'],
    'FS': ['fs', 'flow switch', 'فلوسوئیچ', 'سوئیچ جریان'],
    'VA': ['va', 'valve actuator', 'actuator', 'اکچویتور', 'شیر'],
    'SV': ['sv', 'solenoid', 'solenoid valve', 'شیر برقی'],
    'MOV': ['mov', 'motorized valve', 'شیر موتوری'],
    'DAM_T1': ['dam_t1', 'damper with spring', 'دمپر با فنر'],
    'DAM_T2': ['dam_t2', 'damper without spring', 'دمپر بدون فنر'],
    'DAM_T3': ['dam_t3', 'modulating damper with spring'],
    'DAM_T4': ['dam_t4', 'modulating damper without spring'],
    'VSD': ['vsd', 'vfd', 'variable speed', 'درایو', 'اینورتر'],
    'FC': ['fc', 'fancoil', 'fan coil', 'فن کویل', 'فن‌کویل'],
    'LIG': ['lig', 'lighting', 'روشنایی'],
    'FR': ['fr', 'freeze', 'freeze protection', 'محافظ یخ‌زدگی'],
    'AQ': ['aq', 'air quality', 'کیفیت هوا'],
    'SD': ['sd', 'smoke', 'smoke detector', 'دتکتور دود'],
    'LS': ['ls', 'level switch', 'سوئیچ سطح'],
    'LT': ['lt', 'level transmitter', 'ترانسمیتر سطح'],
    'Knob': ['knob', 'setpoint knob', 'تنظیم دما'],
    'SOU': ['sou', 'sound', 'صدا سنج'],
    'LUX': ['lux', 'نورسنج'],
    'VIB': ['vib', 'vibration', 'لرزش سنج'],
    'BUZ': ['buz', 'buzzer', 'زنگ خطر'],
    'HMI': ['hmi', 'panel', 'پنل'],
    'FCV': ['fcv', 'fancoil valve', 'شیر فن کویل'],
}

# ================================================================
# PROJECT NAME ALIASES (فارسی/انگلیسی)
# ================================================================

PROJECT_ALIASES = {
    'Rabbani': ['ربانی', 'ربانى', 'rabbani', 'rbani', 'rabany'],
    'Abadrahan': ['ابادراهان', 'آبادرهان', 'abadrahan', 'abadrhan'],
    '01-Typical': ['تیپیکال', 'typical', '01typical', '01 typical'],
    'Data Center Saderat': [
        'دیتاسنتر صادرات', 'دیتا سنتر صادرات', 'صادرات',
        'saderat', 'datacenter saderat', 'saderat dc', 'dc saderat'
    ],
    'Data Center Tejarat': [
        'دیتاسنتر تجارت', 'دیتا سنتر تجارت', 'تجارت',
        'tejarat', 'datacenter tejarat', 'tejarat dc', 'dc tejarat'
    ],
    'Haspital Nikan Gharb': [
        'بیمارستان نیکان غرب', 'نیکان غرب', 'hospital nikan',
        'nikan gharb', 'nikan'
    ],
    'Mall Sam Shariati': [
        'مال سام شریعتی', 'سام شریعتی', 'sam shariati', 'mall sam'
    ],
    'Nikan Gharb AHU': [
        'نیکان غرب ahu', 'ahu نیکان', 'nikan gharb ahu', 'ahu nikan'
    ],
}

# ================================================================
# NORMALIZE
# ================================================================

def _clean(text: str) -> str:
    """نرمال‌سازی متن — lowercase + حذف نیم‌فاصله"""
    if not text:
        return ''
    text = text.lower()
    text = text.replace('\u200c', ' ')
    text = text.replace('\u200f', ' ')
    text = text.replace('\u200e', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _extract_project_name(text: str, project_names: List[str]) -> Optional[str]:
    """
    استخراج نام پروژه از متن — با پشتیبانی از aliases فارسی/انگلیسی
    """
    text_lower = text.lower().strip()
    
    # ===== ۱. تطبیق دقیق با نام واقعی =====
    for name in project_names:
        if name.lower() == text_lower:
            return name
    
    # ===== ۲. تطبیق با aliases =====
    for name, aliases in PROJECT_ALIASES.items():
        if name not in project_names:
            continue
        for alias in aliases:
            if alias.lower() in text_lower:
                return name
    
    # ===== ۳. اگر نام پروژه در متن باشد =====
    matches = []
    for name in project_names:
        if name.lower() in text_lower:
            matches.append((name, len(name)))
    
    if matches:
        matches.sort(key=lambda x: -x[1])
        return matches[0][0]
    
    # ===== ۴. اگر بخشی از نام پروژه در متن باشد =====
    words = text_lower.split()
    for word in words:
        if len(word) < 4:
            continue
        for name in project_names:
            name_words = name.lower().split()
            if word in name_words:
                return name
    
    return None


# ================================================================
# کامپوننت معتبر
# ================================================================

ALL_COMPONENT_CODES = set(COMPONENT_ALIASES.keys())

PERSIAN_COMPONENT_WORDS = {
    'پمپ': 'PU', 'موتور': 'PU', 'فن': 'FC',
    'سنسور': None,
    'شیر': 'VA', 'دمپر': 'DAM_T1', 'درایو': 'VSD', 'اینورتر': 'VSD',
    'فلوسوئیچ': 'FS', 'ترانسمیتر': 'PT',
}


def _is_valid_component(text: str) -> bool:
    """بررسی آیا متن یک کامپوننت معتبر است"""
    if not text:
        return False
    
    text_clean = _clean(text).replace(' ', '').strip()
    text_upper = text_clean.upper()
    
    if text_upper in ALL_COMPONENT_CODES:
        return True
    
    for key, aliases in COMPONENT_ALIASES.items():
        for alias in aliases:
            alias_clean = _clean(alias).replace(' ', '').strip()
            if alias_clean == text_clean:
                return True
    
    return False


# ============================================================
# INTENT DETECTION
# ============================================================

def detect_intent(question: str, project_names: List[str] = None) -> Dict[str, Any]:
    if project_names is None:
        project_names = []
    
    original = question.strip()
    q = _clean(question)
    
    if not q:
        return {'intent': 'unknown', 'groups': (), 'raw': question}
    
    # ============================================================
    # HELP
    # ============================================================
    if q in ['help', 'راهنما', 'کمک', '؟', '?']:
        return {'intent': 'help', 'groups': (), 'raw': question}
    
    # ============================================================
    # کلمات کلیدی مشترک
    # ============================================================
    has_project = any(w in q for w in ['پروژه', 'project'])
    has_count = any(w in q for w in ['چند', 'تعداد', 'چندتا', 'چند تا', 'count'])
    has_list = any(w in q for w in [
        'لیست', 'چه', 'چی', 'چیه', 'چیست', 'کدام', 'کدامند',
        'همه', 'بگو', 'نشان', 'نمایش', 'معرفی',
        'list', 'show', 'what', 'which',
    ])
    has_summary = any(w in q for w in [
        'خلاصه', 'اطلاعات', 'گزارش', 'معرفی',
        'summary', 'info',
    ])
    has_compare = 'مقایسه' in q or 'compare' in q
    has_section = any(w in q for w in ['سکشن', 'بخش', 'section'])
    has_device = any(w in q for w in ['دستگاه', 'تجهیز', 'device', 'equipment'])
    has_total = any(w in q for w in ['کل', 'مجموع', 'total'])
    has_io = any(w in q for w in ['i/o', 'io ', 'آی او', 'آی‌او', 'i o'])
    has_top = any(w in q for w in ['پرکاربرد', 'بیشترین', 'top', 'most'])
    
    # ============================================================
    # 🎯 PRIORITY 1: TOP_COMPONENTS  ← ✅ اول از همه!
    # ============================================================
    if has_top:
        proj = _extract_project_name(q, project_names)
        if proj:
            return {
                'intent': 'top_components',
                'groups': (proj,),
                'raw': question,
            }
        else:
            return {
                'intent': 'top_components',
                'groups': (),
                'raw': question,
            }
    
    # ============================================================
    # 🎯 PRIORITY 2: COUNT_COMPONENTS
    # ============================================================
    if has_count:
        q_upper = q.upper()
        found_component = None
        
        for comp_code in ALL_COMPONENT_CODES:
            if re.search(rf'\b{comp_code}\b', q_upper):
                found_component = comp_code
                break
        
        if found_component:
            proj = _extract_project_name(q, project_names)
            if proj:
                return {
                    'intent': 'count_components',
                    'groups': (found_component, proj),
                    'raw': question,
                }
            else:
                return {
                    'intent': 'count_components',
                    'groups': (found_component,),
                    'raw': question,
                }
    
    # ============================================================
    # 🎯 PRIORITY 3: COUNT_PROJECTS
    # ============================================================
    if has_project and has_count:
        return {'intent': 'count_projects', 'groups': (), 'raw': question}
    
    # ============================================================
    # 🎯 PRIORITY 4: LIST_SECTIONS
    # ============================================================
    if has_section:
        proj_raw = _extract_project_name(q, project_names) or ''
        
        if not proj_raw:
            match = re.search(
                r'(?:سکشن|بخش|section)'
                r'(?:\s*[های]*\s*)*'
                r'(?:\s+پروژه\s+)?'
                r'([^?؟]+?)'
                r'(?:\s+(?:را|چیه|چیست|چی|کدامند|کدام|بگو|نشان|list|show|هست|دارم|دارد))?'
                r'\s*[?؟]?\s*$',
                q
            )
            if match:
                proj_raw = match.group(1).strip()
                proj_raw = re.sub(
                    r'\s+(را|چیه|چیست|چی|کدامند|کدام|بگو|نشان|list|show|هست|دارم|دارد).*$',
                    '',
                    proj_raw
                ).strip()
        
        proj = _extract_project_name(proj_raw, project_names) or proj_raw
        
        return {
            'intent': 'list_sections',
            'groups': (proj,),
            'raw': question,
        }
    
    # ============================================================
    # 🎯 PRIORITY 5: LIST_DEVICES
    # ============================================================
    if has_device and has_list:
        match = re.search(
            r'(?:دستگاه|device)\S*\s+(?:سکشن\s+)?(.+?)'
            r'(?:\s+(?:را|چیه|چیست|بگو|list))?$',
            q
        )
        sec = match.group(1).strip() if match else ''
        sec = re.sub(r'\s+(را|چیه|چیست|بگو|list|show).*$', '', sec).strip()
        
        return {
            'intent': 'list_devices',
            'groups': (sec,),
            'raw': question,
        }
    
    # ============================================================
    # 🎯 PRIORITY 6: LIST_PROJECTS
    # ============================================================
    if has_project and has_list:
        return {'intent': 'list_projects', 'groups': (), 'raw': question}
    
    # ============================================================
    # 🎯 PRIORITY 7: COMPARE_PROJECTS
    # ============================================================
    if has_compare:
        match = re.search(
            r'(?:مقایسه|compare)\s+(?:پروژه\s+)?(.+?)\s+(?:و|با|and|vs)\s+(.+)',
            q
        )
        if match:
            proj_a_raw = match.group(1).strip()
            proj_b_raw = match.group(2).strip()
            
            proj_a = _extract_project_name(proj_a_raw, project_names) or proj_a_raw
            proj_b = _extract_project_name(proj_b_raw, project_names) or proj_b_raw
            
            return {
                'intent': 'compare_projects',
                'groups': (proj_a, proj_b),
                'raw': question,
            }
    
    # ============================================================
    # 🎯 PRIORITY 8: PROJECT_SUMMARY
    # ============================================================
    if has_summary:
        match = re.search(
            r'(?:خلاصه|اطلاعات|گزارش|summary)\s+(?:پروژه\s+)?(.+)',
            q
        )
        proj_raw = match.group(1).strip() if match else ''
        proj_raw = re.sub(r'\s*\?+$', '', proj_raw).strip()
        
        proj = _extract_project_name(proj_raw, project_names) or proj_raw
        
        return {
            'intent': 'project_summary',
            'groups': (proj,),
            'raw': question,
        }
    
    # ============================================================
    # 🎯 PRIORITY 9: TOTAL_IO
    # ============================================================
    if (has_io and has_total) or ('total io' in q) or ('total i/o' in q):
        match = re.search(
            r'(?:کل|مجموع|total)\s+(?:i/?o|آی\s*او|io)\s+(?:پروژه\s+)?(.+)',
            q
        )
        proj_raw = match.group(1).strip() if match else ''
        proj_raw = re.sub(r'\s*\?+$', '', proj_raw).strip()
        
        proj = _extract_project_name(proj_raw, project_names) or proj_raw
        
        return {
            'intent': 'total_io',
            'groups': (proj,),
            'raw': question,
        }
    
    # ============================================================
    # UNKNOWN
    # ============================================================
    return {'intent': 'unknown', 'groups': (), 'raw': question}


# ================================================================
# COMPONENT NORMALIZE
# ================================================================

def normalize_component(text: str) -> Optional[str]:
    """تبدیل نام کامپوننت از فارسی/انگلیسی به کد استاندارد"""
    if not text:
        return None
    
    text_clean = _clean(text).replace(' ', '').strip()
    
    # ===== ۱. چک کد مستقیم =====
    if text.upper() in COMPONENT_ALIASES:
        return text.upper()
    
    # ===== ۲. چک aliases دقیق =====
    for key, aliases in COMPONENT_ALIASES.items():
        for alias in aliases:
            alias_clean = _clean(alias).replace(' ', '').strip()
            if alias_clean == text_clean:
                return key
    
    return None