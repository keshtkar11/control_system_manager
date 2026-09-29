# core/valve_calculator.py
"""
توابع محاسباتی برای بخش Valves (شیرها)

نسخه 3.0 — اصلاح‌شده:
    - محاسبه Kv بخار با استاندارد IEC 60534-2-1
    - تشخیص Choked Flow
    - اطلاعات کامل Steam برای UI
"""

import math
import logging
from typing import Optional, Dict, Any, List

from core.valve_constants import (
    # جداول
    ABQM_TABLE,
    VRG3_TABLE,
    VFS2_TABLE,
    
    # ثابت‌ها
    FLOW_UNITS,
    PSI_TO_BAR,
    SG_WATER,
    KV_MAX_3WAY,
    KVS_MAX_STEAM,
    KV_MIN_3WAY,
    DEFAULT_PRESSURE_DROP_PSI,
    STEAM_V_SPECIFIC,
    STEAM_CATEGORIES,
    STEAM_APPLICATIONS,
    # ✅ جدید
    LB_TO_KG,
    KG_TO_LB,
    TON_TO_KG,
    
    # توابع کمکی
    get_steam_actuator,
    get_3way_actuator,
)

# ✅ جدید: ماژول محاسبه Kv بخار
from core.steam_kv_calculator import (
    calculate_kv_steam as calculate_kv_steam_iec,
    get_steam_properties,
    get_suggested_dp_limit,
    psi_to_bar,
    bar_to_psi,
)

logger = logging.getLogger(__name__)


# ================================================================
# ۱. تبدیل واحدها
# ================================================================


def _resolve_picv_actuator(signal: str, model: str = '',
                            default_actuator: str = '') -> str:
    """
    تعیین Actuator واقعی PICV بر اساس Signal و Model
    
    منطق (طبق کاتالوگ Danfoss):
    
    ┌──────────────────────┬─────────────────────────┬──────────────────┐
    │ Model Range          │ Signal                  │ Actuator         │
    ├──────────────────────┼─────────────────────────┼──────────────────┤
    │ ABQM15 → ABQM32HF    │ Modulating , 24Vac      │ AME110NLX        │
    │ ABQM15 → ABQM32HF    │ 220V On/Off             │ TWA-Q 230V NC    │
    │ ABQM40 → ABQM100HF   │ (هر سیگنالی)           │ AME435QM         │
    │ ABQM125 → ABQM200    │ (هر سیگنالی)           │ AME55QM          │
    └──────────────────────┴─────────────────────────┴──────────────────┘
    
    ⚠️ برای مدل‌های ABQM40 به بالا، Signal کاربر نادیده گرفته می‌شود
       چون این مدل‌ها فقط یک نوع Actuator دارند.
    """
    signal_lower = (signal or '').strip().lower()
    model_upper = (model or '').strip().upper()
    
    # ============================================================
    # Set های دقیق مدل‌ها (بدون substring problem)
    # ============================================================
    MODELS_AME55QM = {
        'ABQM125', 'ABQM125HF',
        'ABQM150', 'ABQM150HF',
        'ABQM200',
    }
    
    MODELS_AME435QM = {
        'ABQM40', 'ABQM50',
        'ABQM65', 'ABQM65HF',
        'ABQM80', 'ABQM80HF',
        'ABQM100', 'ABQM100HF',
    }
    
    MODELS_DUAL = {
        'ABQM15', 'ABQM15 HF',
        'ABQM20HF', 'ABQM25HF', 'ABQM32HF',
    }
    
    # ============================================================
    # ۱. مدل‌های ABQM125 → ABQM200: فقط AME55QM
    # ============================================================
    if model_upper in MODELS_AME55QM:
        return "AME55QM"
    
    # ============================================================
    # ۲. مدل‌های ABQM40 → ABQM100HF: فقط AME435QM
    # ============================================================
    if model_upper in MODELS_AME435QM:
        return "AME435QM"
    
    # ============================================================
    # ۳. مدل‌های ABQM15 → ABQM32HF: Actuator بر اساس Signal
    # ============================================================
    if model_upper in MODELS_DUAL:
        # Signal = Modulating → AME110NLX
        if 'modulating' in signal_lower:
            return "AME110NLX"
        # Signal = 220V On/Off → TWA-Q 230V NC
        if (
            '220v' in signal_lower
            or 'on/off' in signal_lower
            or 'on-off' in signal_lower
        ):
            return "TWA-Q 230V NC"
        # Signal ناشناخته → پیش‌فرض Modulating
        return "AME110NLX"
    
    # ============================================================
    # ۴. Model ناشناخته → مقدار پیش‌فرض
    # ============================================================
    return default_actuator or ''


def convert_flow_to_lph(flow: float, unit: str,
                        pressure_drop_psi: float = None) -> float:
    """
    تبدیل دبی از هر واحدی به L/HR
    
    برای بخار (Kg/h, lb/h, ton/h)، از چگالی استاندارد استفاده می‌کند.
    """
    try:
        flow = float(flow)
    except (ValueError, TypeError):
        return 0.0
    
    if flow <= 0:
        return 0.0
    
    # ============================================================
    # واحدهای خطی (مایعات)
    # ============================================================
    factor = FLOW_UNITS.get(unit)
    
    if factor is not None:
        return round(flow * factor, 2)
    
    # ============================================================
    # Kg/h (بخار)
    # ============================================================
    if unit == 'Kg/h':
        return round(flow * STEAM_V_SPECIFIC * 1000, 2)
    
    # ============================================================
    # ✅ lb/h (بخار) — اینجا اضافه شده
    # ============================================================
    if unit == 'lb/h':
        kg_h = flow * LB_TO_KG
        return round(kg_h * STEAM_V_SPECIFIC * 1000, 2)
    
    # ============================================================
    # ton/h (بخار)
    # ============================================================
    if unit == 'ton/h':
        kg_h = flow * TON_TO_KG
        return round(kg_h * STEAM_V_SPECIFIC * 1000, 2)
    
    return 0.0


def convert_pressure_to_bar(pressure_psi: float) -> float:
    """تبدیل psi به bar"""
    return psi_to_bar(pressure_psi)


# ================================================================
# ۲. محاسبه Kv برای 3Way
# ================================================================

def calculate_kv(flow_lph: float, pressure_drop_psi: float,
                 sg: float = SG_WATER) -> float:
    """
    محاسبه Kv برای شیر سه راهه (مایع)
    
    فرمول: Kv = Q(m³/h) / √(Δp(bar) / SG)
    """
    try:
        flow_lph = float(flow_lph)
        pressure_drop_psi = float(pressure_drop_psi)
        sg = float(sg)
    except (ValueError, TypeError):
        return 0.0
    
    if flow_lph <= 0 or pressure_drop_psi <= 0 or sg <= 0:
        return 0.0
    
    q_m3h = flow_lph / 1000.0
    dp_bar = pressure_drop_psi * PSI_TO_BAR
    
    if dp_bar <= 0:
        return 0.0
    
    kv = q_m3h / math.sqrt(dp_bar / sg)
    return round(kv, 4)


def select_vrg3(kv_calc: float) -> Dict[str, Any]:
    """
    انتخاب VRG 3 بر اساس نزدیک‌ترین Kv
    """
    result = {
        'dn': None,
        'kv': None,
        'actuator': None,
        'diff': None,
        'warning': None,
    }
    
    try:
        kv_calc = float(kv_calc)
    except (ValueError, TypeError):
        result['warning'] = "⚠️ Kv نامعتبر است"
        return result
    
    if kv_calc <= 0:
        result['warning'] = "⚠️ Kv محاسبه‌شده نامعتبر است"
        return result
    
    # ===== بررسی محدوده =====
    if kv_calc > KV_MAX_3WAY:
        result['warning'] = (
            f"⚠️ Kv محاسبه‌شده ({kv_calc:.2f}) از بزرگ‌ترین Kv جدول "
            f"VRG 3/VF 3 ({KV_MAX_3WAY}) بیشتر است."
        )
        kv_max, dn_max = VRG3_TABLE[-1]
        result['dn'] = dn_max
        result['kv'] = kv_max
        result['actuator'] = get_3way_actuator(dn_max)
        result['diff'] = round(abs(kv_max - kv_calc), 4)
        return result
    
    # ===== پیدا کردن نزدیک‌ترین =====
    best_match = None
    min_diff = float('inf')
    
    for kv, dn in VRG3_TABLE:
        diff = abs(kv - kv_calc)
        
        if diff < min_diff or (diff == min_diff and 
                                best_match and kv > best_match[0]):
            min_diff = diff
            best_match = (kv, dn)
    
    if best_match:
        kv_sel, dn_sel = best_match
        result['dn'] = dn_sel
        result['kv'] = kv_sel
        result['actuator'] = get_3way_actuator(dn_sel) or "AME 435 QM"
        result['diff'] = round(min_diff, 4)
        
        if kv_calc < KV_MIN_3WAY:
            result['warning'] = (
                f"⚠️ Kv محاسبه‌شده ({kv_calc:.2f}) کمتر از کوچک‌ترین Kv جدول "
                f"VRG 3 ({KV_MIN_3WAY}) است. DN 15 انتخاب شد."
            )
    
    return result


# ================================================================
# ۳. انتخاب ABQM برای PICV
# ================================================================

def select_picv(flow_lph: float) -> Dict[str, Any]:
    """انتخاب ABQM برای PICV"""
    result = {
        'model': None,
        'max_flow': None,
        'actuator': None,
        'signal': None,
        'percent': None,
        'warning': None,
    }
    
    try:
        flow_lph = float(flow_lph)
    except (ValueError, TypeError):
        result['warning'] = "⚠️ دبی نامعتبر است"
        return result
    
    if flow_lph <= 0:
        result['warning'] = "⚠️ دبی باید بزرگ‌تر از صفر باشد"
        return result
    
    max_flow_available = ABQM_TABLE[-1][0]
    
    if flow_lph > max_flow_available:
        result['warning'] = (
            f"⚠️ دبی ({flow_lph:.0f} L/HR) از بزرگ‌ترین ABQM "
            f"({max_flow_available} L/HR) بیشتر است."
        )
    
    for max_flow, model, actuator, signal in ABQM_TABLE:
        if max_flow >= flow_lph:
            result['model'] = model
            result['max_flow'] = max_flow
            result['actuator'] = actuator
            result['signal'] = signal
            break
    
    if result['model'] is None:
        max_flow, model, actuator, signal = ABQM_TABLE[-1]
        result['model'] = model
        result['max_flow'] = max_flow
        result['actuator'] = actuator
        result['signal'] = signal
    
    if result['max_flow'] and result['max_flow'] > 0:
        percent = (flow_lph / result['max_flow']) * 100
        result['percent'] = round(percent, 2)
    
    return result


def calculate_picv_percent(flow_lph: float, picv_max_flow: float) -> float:
    """محاسبه درصد تنظیم PICV"""
    try:
        flow_lph = float(flow_lph)
        picv_max_flow = float(picv_max_flow)
    except (ValueError, TypeError):
        return 0.0
    
    if picv_max_flow <= 0:
        return 0.0
    
    return round((flow_lph / picv_max_flow) * 100, 2)


# ================================================================
# ۴. محاسبه Kv و انتخاب VFS 2 برای Steam
# ================================================================

def calculate_kvs_steam(flow_kg_h: float, inlet_pressure_bar: float,
                        pressure_drop_psi: float) -> float:
    """
    محاسبه kvs برای شیر بخار — IEC 60534-2-1
    
    این تابع یک wrapper ساده روی steam_kv_calculator است.
    
    Args:
        flow_kg_h: دبی (kg/h)
        inlet_pressure_bar: فشار مطلق ورودی (bar abs)
        pressure_drop_psi: افت فشار (psi)
    
    Returns:
        kvs محاسبه‌شده
    """
    # ===== تبدیل psi به bar =====
    dp_bar = pressure_drop_psi * PSI_TO_BAR
    
    # ===== فراخوانی فرمول IEC =====
    result = calculate_kv_steam_iec(
        mass_flow_kg_h=flow_kg_h,
        inlet_pressure_bar_abs=inlet_pressure_bar,
        pressure_drop_bar=dp_bar,
    )
    
    # ===== چک خطا =====
    if result.get('error'):
        logger.warning(f"Steam Kv error: {result['error']}")
        return 0.0
    
    # ===== هشدار Choked Flow =====
    if result.get('is_choked'):
        logger.warning(
            f"⚠️ Choked flow detected: x={result['x']:.3f} > "
            f"x_critical={result['x_critical']:.3f}"
        )
    
    return result.get('kv', 0.0)


def select_vfs2(kvs_calc: float) -> Dict[str, Any]:
    """
    انتخاب VFS 2 بر اساس نزدیک‌ترین kvs
    در حالت تساوی، بزرگ‌تر انتخاب می‌شود
    """
    result = {
        'kvs_selected': None,
        'dn': None,
        'model': None,
        'actuator': None,
        'diff': None,
        'warning': None,
    }
    
    try:
        kvs_calc = float(kvs_calc)
    except (ValueError, TypeError):
        result['warning'] = "⚠️ kvs نامعتبر است"
        return result
    
    if kvs_calc <= 0:
        result['warning'] = "⚠️ kvs باید بزرگ‌تر از صفر باشد"
        return result
    
    # ============================================================
    # بررسی محدوده
    # ============================================================
    if kvs_calc > KVS_MAX_STEAM:
        result['warning'] = (
            f"⚠️ kvs محاسبه‌شده ({kvs_calc:.2f}) از بزرگ‌ترین kvs جدول "
            f"VFS 2 ({KVS_MAX_STEAM}) بیشتر است. لطفاً سیستم را بررسی کنید."
        )
        # بزرگ‌ترین انتخاب می‌شود
        kvs_max, dn_max = VFS2_TABLE[-1]
        result['kvs_selected'] = kvs_max
        result['dn'] = dn_max
        result['model'] = f"VFS 2 DN{dn_max}"
        result['actuator'] = get_steam_actuator(dn_max)
        result['diff'] = round(abs(kvs_max - kvs_calc), 4)
        return result
    
    # ============================================================
    # ✅ جدید: پیدا کردن نزدیک‌ترین (در تساوی، بزرگ‌تر)
    # ============================================================
    best_match = None
    min_diff = float('inf')
    
    for kvs, dn in VFS2_TABLE:
        diff = abs(kvs - kvs_calc)
        
        # شرط: نزدیک‌تر، یا در تساوی بزرگ‌تر
        if diff < min_diff or (diff == min_diff and
                                best_match and kvs > best_match[0]):
            min_diff = diff
            best_match = (kvs, dn)
    
    if best_match:
        kvs_sel, dn_sel = best_match
        result['kvs_selected'] = kvs_sel
        result['dn'] = dn_sel
        result['model'] = f"VFS 2 DN{dn_sel}"
        result['actuator'] = get_steam_actuator(dn_sel)
        result['diff'] = round(min_diff, 4)
        
        # ===== هشدار اگر kvs خیلی کم =====
        if kvs_calc < 0.4:  # کوچک‌ترین kvs جدول VFS 2
            result['warning'] = (
                f"⚠️ kvs محاسبه‌شده ({kvs_calc:.2f}) کمتر از کوچک‌ترین kvs جدول "
                f"VFS 2 (0.4) است. DN 15 انتخاب شد."
            )
    
    return result


# ================================================================
# ۵. اطلاعات کامل Steam (جدید)
# ================================================================

def get_steam_info(pressure_bar: float) -> Dict[str, Any]:
    """
    دریافت اطلاعات کامل Steam برای نمایش در UI
    
    Args:
        pressure_bar: فشار مطلق ورودی (bar)
    
    Returns:
        {
            'valid': bool,
            'temp_saturation': float,
            'rho': float,
            'category': dict یا None,
            'applications': list,
            'warnings': list,
        }
    """
    result = {
        'valid': False,
        'temp_saturation': 0.0,
        'rho': 0.0,
        'category': None,
        'applications': [],
        'warnings': [],
    }
    
    try:
        pressure_bar = float(pressure_bar)
    except (ValueError, TypeError):
        return result
    
    if pressure_bar <= 0:
        return result
    
    # ===== خواص بخار =====
    props = get_steam_properties(pressure_bar)
    result['temp_saturation'] = props.get('temp_sat', 0.0)
    result['rho'] = props.get('rho', 0.0)
    result['valid'] = props.get('valid', False)
    
    # ===== دسته‌بندی =====
    for cat in STEAM_CATEGORIES:
        if cat['bar_min'] <= pressure_bar <= cat['bar_max']:
            result['category'] = cat
            result['warnings'].extend(cat.get('warnings', []))
            break
    
    # ===== کاربردها =====
    for app in STEAM_APPLICATIONS:
        if app['bar_min'] <= pressure_bar <= app['bar_max']:
            result['applications'].append(app)
    
    return result


def check_choked_flow(p1_bar: float, dp_bar: float,
                      x_t: float = 0.43) -> Dict[str, Any]:
    """
    بررسی Choked Flow برای VFS 2 (کاتالوگ Danfoss)
    
    نسبت بحرانی = 40% فشار مطلق (از دیاگرام Danfoss)
    """
    result = {
        'is_choked': False,
        'x': 0.0,
        'x_critical': 0.0,
        'dp_max': 0.0,
    }
    
    try:
        p1_bar = float(p1_bar)
        dp_bar = float(dp_bar)
    except (ValueError, TypeError):
        return result
    
    if p1_bar <= 0 or dp_bar < 0:
        return result
    
    # ===== نسبت افت فشار =====
    x = dp_bar / p1_bar
    result['x'] = round(x, 4)
    
    # ===== نسبت بحرانی برای بخار (از کاتالوگ Danfoss) =====
    x_critical = 0.40    # 40% فشار مطلق
    result['x_critical'] = x_critical
    
    # ===== تشخیص =====
    result['is_choked'] = (x > x_critical)
    
    # ===== حداکثر افت فشار مجاز =====
    result['dp_max'] = round(p1_bar * x_critical, 4)
    
    return result


# ================================================================
# ۶. تابع جامع: enrich_valve
# ================================================================

def enrich_valve(valve) -> None:
    """
    پر کردن خودکار فیلدهای محاسبه‌شده شیر
    """
    # ============================================================
    # ۱. تبدیل دبی به L/HR
    # ============================================================
    valve.MaxFlowLPH = convert_flow_to_lph(
        valve.Flow, 
        valve.Unit or 'L/HR',
        valve.PressureDrop
    )
    
    # ============================================================
    # ۲. پاک کردن فیلدهای قبلی
    # ============================================================
    valve.Warning3Way = ''
    valve.WarningSteam = ''
    valve.WarningGeneral = ''
    
    # ============================================================
    # ۳. محاسبات بر اساس نوع شیر
    # ============================================================
    valve_type = valve.ValveType or ''
    
    # ─── PICV ───
    if valve_type in ('PICV', 'PICV+3Way'):
        _enrich_picv(valve)
    
    # ─── 3 Way ───
    if valve_type in ('3 Way', 'PICV+3Way'):
        _enrich_3way(valve)
    
    # ─── Steam ───
    if valve_type == 'Steam':
        _enrich_steam(valve)
    
    # ============================================================
    # ۴. هشدار کلی
    # ============================================================
    if valve.has_warning():
        warnings = []
        if valve.Warning3Way:
            warnings.append(valve.Warning3Way)
        if valve.WarningSteam:
            warnings.append(valve.WarningSteam)
        valve.WarningGeneral = ' | '.join(warnings)


def _enrich_picv(valve) -> None:
    """پر کردن فیلدهای PICV — با منطق Signal → Actuator"""
    if valve.MaxFlowLPH <= 0:
        valve.WarningGeneral = "⚠️ دبی برای محاسبه PICV نامعتبر است"
        return
    
    # ============================================================
    # ✅ ۱. ذخیره Signal کاربر (قبل از محاسبه)
    # ============================================================
    user_signal = (getattr(valve, 'PICVSignal', '') or '').strip()
    
    # ============================================================
    # ✅ ۲. محاسبه PICV
    # ============================================================
    picv_result = select_picv(valve.MaxFlowLPH)
    
    valve.PICVModel = picv_result['model'] or ''
    valve.PICVMaxFlow = picv_result['max_flow'] or 0
    valve.PICVPercent = picv_result['percent'] or 0
    
    # ============================================================
    # ✅ ۳. Signal و Actuator
    # ============================================================
    if valve.ValveType == 'PICV+3Way':
        # برای PICV+3Way: Signal کاربر حفظ می‌شود
        # ولی Actuator خالی می‌ماند (چون 3Way دارد)
        valve.PICVSignal = user_signal
        valve.PICVActuator = ''
    else:
        # برای PICV خالص:
        # ۱. Signal: اگر کاربر داده → حفظ، وگرنه از جدول
        valve.PICVSignal = user_signal or (picv_result['signal'] or '')
        
        # ۲. Actuator: از Signal استخراج می‌شود (نه از جدول!)
        valve.PICVActuator = _resolve_picv_actuator(
            signal=valve.PICVSignal,
            model=valve.PICVModel,
            default_actuator=picv_result['actuator'] or ''
        )
    
    # ============================================================
    # ✅ ۴. هشدارها
    # ============================================================
    if picv_result.get('warning'):
        valve.WarningGeneral = picv_result['warning']


def _enrich_3way(valve) -> None:
    """پر کردن فیلدهای 3Way"""
    if valve.MaxFlowLPH <= 0:
        valve.Warning3Way = "⚠️ دبی برای محاسبه 3Way نامعتبر است"
        return
    
    if valve.PressureDrop <= 0:
        valve.Warning3Way = "⚠️ Pressure Drop نامعتبر است"
        return
    
    kv_calc = calculate_kv(valve.MaxFlowLPH, valve.PressureDrop)
    valve.KvCalc = kv_calc
    
    if kv_calc <= 0:
        valve.Warning3Way = "⚠️ Kv محاسبه‌شده نامعتبر است"
        return
    
    vrg3_result = select_vrg3(kv_calc)
    
    valve.KvSelected = vrg3_result['kv'] or 0
    
    dn = vrg3_result['dn'] or 0
    valve.__dict__['3WayDN'] = dn
    
    if dn:
        series = "VRG 3" if dn <= 50 else "VF 3"
        valve.__dict__['3WayModel'] = f"{series} DN{dn}"
    else:
        valve.__dict__['3WayModel'] = ''
    
    valve.__dict__['3WayActuator'] = vrg3_result['actuator'] or ''
    
    if vrg3_result.get('warning'):
        valve.Warning3Way = vrg3_result['warning']


def _enrich_steam(valve) -> None:
    """
    پر کردن فیلدهای Steam — با فرمول IEC 60534-2-1
    
    ✅ اصلاح‌شده:
        - چک SteamPressure و PressureDrop اول
        - سپس تبدیل دبی به Kg/h
        - عدم نیاز به MaxFlowLPH برای بخار
    """
    # ============================================================
    # ۱. اعتبارسنجی اولیه
    # ============================================================
    if valve.SteamPressure <= 0:
        valve.WarningSteam = "⚠️ فشار ورودی بخار نامعتبر است"
        return
    
    if valve.PressureDrop <= 0:
        valve.WarningSteam = "⚠️ Pressure Drop نامعتبر است"
        return
    
    # ============================================================
    # ۲. تبدیل دبی به Kg/h (مستقل از MaxFlowLPH)
    # ============================================================
    try:
        flow_value = float(valve.Flow or 0)
    except (ValueError, TypeError):
        flow_value = 0.0
    
    if flow_value <= 0:
        valve.WarningSteam = "⚠️ دبی باید بزرگ‌تر از صفر باشد"
        return
    
    unit = valve.Unit or ''
    
    if unit == 'Kg/h':
        flow_kg_h = flow_value
    elif unit == 'lb/h':
        flow_kg_h = flow_value * LB_TO_KG
    elif unit == 'ton/h':
        flow_kg_h = flow_value * TON_TO_KG
    else:
        # واحد حجمی → تخمینی از MaxFlowLPH (اگر موجود باشد)
        if valve.MaxFlowLPH and valve.MaxFlowLPH > 0:
            flow_kg_h = valve.MaxFlowLPH / (STEAM_V_SPECIFIC * 1000)
        else:
            valve.WarningSteam = (
                f"⚠️ واحد '{unit}' برای بخار پشتیبانی نمی‌شود. "
                f"از Kg/h، lb/h یا ton/h استفاده کنید."
            )
            return
    
    if flow_kg_h <= 0:
        valve.WarningSteam = "⚠️ دبی محاسبه‌شده نامعتبر است"
        return
    
    # ============================================================
    # ۳. محاسبه kvs (IEC 60534)
    # ============================================================
    kvs_calc = calculate_kvs_steam(
        flow_kg_h,
        valve.SteamPressure,
        valve.PressureDrop
    )
    
    valve.KvsCalc = kvs_calc
    
    if kvs_calc <= 0:
        valve.WarningSteam = "⚠️ kvs محاسبه‌شده نامعتبر است"
        return
    
    # ============================================================
    # ۴. انتخاب VFS 2
    # ============================================================
    vfs2_result = select_vfs2(kvs_calc)
    
    valve.KvsSelected = vfs2_result['kvs_selected'] or 0
    valve.SteamDN = vfs2_result['dn'] or 0
    valve.SteamModel = vfs2_result['model'] or ''
    valve.SteamActuator = vfs2_result['actuator'] or ''

    # ============================================================
    # ✅ جدید: اطلاعات VFS 2 (از کاتالوگ Danfoss)
    # ============================================================
    from core.valve_constants import VFS2_INFO
    valve.__dict__['_vfs2_info'] = VFS2_INFO
    
    # ✅ جدید: هشدار ΔP > 6 bar (محدودیت فیزیکی VFS 2)
    dp_bar = valve.PressureDrop * PSI_TO_BAR
    if dp_bar > VFS2_INFO['steam_dp_max_physical']:
        valve.WarningSteam = (
            f"❌ افت فشار ({dp_bar:.2f} bar) بیشتر از "
            f"حد فیزیکی VFS 2 ({VFS2_INFO['steam_dp_max_physical']} bar) است."
        )
        valve.KvsCalc = 0
        valve.KvsSelected = 0
        valve.SteamDN = 0
        valve.SteamModel = ''
        valve.SteamActuator = ''
        valve.__dict__['_vfs2_info'] = VFS2_INFO
        return
    
    # ✅ جدید: هشدار ΔP > 4 bar (پیشنهادی)
    if dp_bar > VFS2_INFO['steam_dp_max_recommended']:
        # هشدار نرم — Kv محاسبه می‌شود
        pass
    # ============================================================
    # ۵. اطلاعات Steam
    # ============================================================
    steam_info = get_steam_info(valve.SteamPressure)
    valve.__dict__['_steam_info'] = steam_info
    
    # ============================================================
    # ۶. ذخیره تبدیل‌ها (برای UI)
    # ============================================================
    conversions = {
        'input_unit': unit,
        'input_value': flow_value,
        'kg_h': flow_kg_h,
        'lb_h': flow_kg_h * KG_TO_LB,
        'ton_h': flow_kg_h / 1000.0,
    }
    valve.__dict__['_steam_conversions'] = conversions
    
    # ============================================================
    # ۷. بررسی Choked Flow
    # ============================================================
    dp_bar = valve.PressureDrop * PSI_TO_BAR
    choked = check_choked_flow(valve.SteamPressure, dp_bar)
    valve.__dict__['_choked_info'] = choked
    
    # ============================================================
    # ۸. هشدارهای ترکیبی
    # ============================================================
    warnings = []
    
    if vfs2_result.get('warning'):
        warnings.append(vfs2_result['warning'])
    
    if choked.get('is_choked'):
        warnings.append(
            f"⚠️ جریان خفه (Choked Flow): ΔP = {dp_bar:.2f} bar "
            f"بیشتر از حد مجاز ({choked['dp_max']:.2f} bar) است."
        )
    
    if warnings:
        valve.WarningSteam = ' | '.join(warnings)

# ================================================================
# ۷. توابع کمکی برای UI
# ================================================================

def get_active_fields_for_type(valve_type: str) -> List[str]:
    """دریافت لیست فیلدهای فعال برای یک نوع شیر"""
    from core.valve_constants import VALVE_TYPE_FIELDS
    
    field_map = {
        'picv_model': 'PICVModel',
        'picv_max_flow': 'PICVMaxFlow',
        'picv_percent': 'PICVPercent',
        'picv_actuator': 'PICVActuator',
        'picv_signal': 'PICVSignal',
        'kv_calc': 'KvCalc',
        'kv_selected': 'KvSelected',
        '3way_dn': '3WayDN',
        '3way_model': '3WayModel',
        '3way_actuator': '3WayActuator',
        '3way_signal': '3WaySignal',
        'steam_pressure': 'SteamPressure',
        'steam_flow_kg_h': 'SteamFlowKgH',     # ✅ جدید
        'steam_flow_lb_h': 'SteamFlowLbH',     # ✅ جدید
        'kvs_calc': 'KvsCalc',
        'kvs_selected': 'KvsSelected',
        'steam_dn': 'SteamDN',
        'steam_model': 'SteamModel',
        'steam_actuator': 'SteamActuator',
        'steam_signal': 'SteamSignal',
        'warning_3way': 'Warning3Way',
        'warning_steam': 'WarningSteam',
        'warning_general': 'WarningGeneral',
    }
    
    snake_fields = VALVE_TYPE_FIELDS.get(valve_type, [])
    return [field_map.get(s, s) for s in snake_fields]


def get_all_base_fields() -> List[str]:
    """فیلدهای پایه (همیشه نمایش)"""
    return [
        'Equipment', 'Quantity', 'Circuit',
        'Flow', 'PressureDrop', 'Unit',
        'ValveType', 'MaxFlowLPH',
    ]


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    # تبدیل واحدها
    'convert_flow_to_lph',
    'convert_pressure_to_bar',
    
    # Kv و VRG 3
    'calculate_kv',
    'select_vrg3',
    
    # PICV
    'select_picv',
    'calculate_picv_percent',
    
    # Steam
    'calculate_kvs_steam',
    'select_vfs2',
    'get_steam_info',
    'check_choked_flow',
    
    # تابع جامع
    'enrich_valve',
    '_resolve_picv_actuator',
    
    # کمکی
    'get_active_fields_for_type',
    'get_all_base_fields',
]