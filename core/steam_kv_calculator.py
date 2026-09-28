# core/steam_kv_calculator.py
"""
محاسبه Kv برای شیر بخار بر اساس استاندارد IEC 60534-2-1

مراجع:
    - IEC 60534-2-1: Industrial-process control valves
    - ISA-75.01.01: Flow Equations for Sizing Control Valves

فرمول:
    Kv = ṁ / (31.6 × Y × √(x_s × P₁ × ρ₁))

که:
    ṁ  = دبی جرمی (kg/h)
    P₁ = فشار مطلق ورودی (bar abs)
    ρ₁ = چگالی بخار در ورودی (kg/m³)
    x  = ΔP / P₁  (نسبت افت فشار)
    x_T = ضریب هندسی شیر
    Y  = ضریب انبساط
"""

import math
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# ================================================================
# ثابت‌ها
# ================================================================

PSI_TO_BAR = 0.0689476
BAR_TO_PSI = 1 / PSI_TO_BAR

# ضریب آیزنتروپیک برای بخار اشباع
GAMMA_STEAM = 1.3

# ضریب هندسی شیر (Globe valve)
X_T_DEFAULT = 0.7
X_T_VFS2_STEAM = 0.43

# حداقل ضریب انبساط (استاندارد IEC)
Y_MIN = 0.667


# ================================================================
# جدول خواص بخار اشباع
# ================================================================
# (bar_abs, T_sat_C, rho_kg_m3)
# منبع: Steam Tables (IAPWS-97)

STEAM_PROPERTIES = [
    (0.10,  45.8,  0.0686),
    (0.20,  60.1,  0.131),
    (0.30,  69.1,  0.188),
    (0.50,  81.3,  0.321),
    (0.75,  91.8,  0.464),
    (1.00,  99.6,  0.590),
    (1.50, 111.4,  0.863),
    (2.00, 120.2,  1.129),
    (2.50, 127.4,  1.392),
    (3.00, 133.5,  1.651),
    (3.50, 138.9,  1.908),
    (4.00, 143.6,  2.163),
    (4.50, 147.9,  2.417),
    (5.00, 151.8,  2.669),
    (6.00, 158.8,  3.169),
    (7.00, 165.0,  3.667),
    (8.00, 170.4,  4.161),
    (9.00, 175.4,  4.652),
    (10.0, 179.9,  5.145),
    (12.0, 188.0,  6.123),
    (15.0, 198.3,  7.594),
    (20.0, 212.4, 10.05),
    (25.0, 224.0, 12.51),
    (30.0, 233.9, 14.99),
    (40.0, 250.4, 19.99),
    (50.0, 263.9, 25.03),
]


# ================================================================
# درون‌یابی خواص بخار
# ================================================================

def get_steam_properties(p1_bar: float) -> Dict[str, float]:
    """
    درون‌یابی خواص بخار اشباع از فشار
    
    Args:
        p1_bar: فشار مطلق (bar)
    
    Returns:
        {
            'temp_sat': دمای اشباع (°C),
            'rho': چگالی بخار اشباع (kg/m³),
            'valid': آیا در محدوده جدول است؟
        }
    """
    if p1_bar <= 0:
        return {'temp_sat': 0.0, 'rho': 0.0, 'valid': False}
    
    table = STEAM_PROPERTIES
    
    # کمتر از کوچک‌ترین
    if p1_bar <= table[0][0]:
        return {
            'temp_sat': table[0][1],
            'rho': table[0][2],
            'valid': False,
        }
    
    # بیشتر از بزرگ‌ترین
    if p1_bar >= table[-1][0]:
        return {
            'temp_sat': table[-1][1],
            'rho': table[-1][2],
            'valid': False,
        }
    
    # درون‌یابی خطی
    for i in range(len(table) - 1):
        p1, t1, r1 = table[i]
        p2, t2, r2 = table[i + 1]
        
        if p1 <= p1_bar <= p2:
            ratio = (p1_bar - p1) / (p2 - p1)
            return {
                'temp_sat': round(t1 + ratio * (t2 - t1), 2),
                'rho': round(r1 + ratio * (r2 - r1), 4),
                'valid': True,
            }
    
    return {'temp_sat': 0.0, 'rho': 0.0, 'valid': False}


# ================================================================
# محاسبه Kv اصلی (IEC 60534-2-1)
# ================================================================

def calculate_kv_steam(
    mass_flow_kg_h: float,
    inlet_pressure_bar_abs: float,
    pressure_drop_bar: float,
    rho_kg_m3: Optional[float] = None,
    gamma: float = GAMMA_STEAM,
    x_t: float = X_T_VFS2_STEAM,
) -> Dict:
    """
    محاسبه Kv برای شیر بخار با فرمول IEC 60534-2-1
    
    Args:
        mass_flow_kg_h: دبی جرمی (kg/h)
        inlet_pressure_bar_abs: فشار مطلق ورودی (bar)
        pressure_drop_bar: افت فشار (bar)
        rho_kg_m3: چگالی بخار (اگر None → از جدول)
        gamma: ضریب آیزنتروپیک (پیش‌فرض 1.3 برای بخار اشباع)
        x_t: ضریب هندسی شیر (پیش‌فرض 0.7 برای گلوب)
    
    Returns:
        {
            'kv': مقدار Kv,
            'x': نسبت افت فشار,
            'x_critical': نسبت بحرانی,
            'x_s': نسبت مؤثر,
            'F_gamma': تصحیح gamma,
            'Y': ضریب انبساط,
            'is_choked': آیا جریان خفه است,
            'rho': چگالی استفاده‌شده (kg/m³),
            'temp_sat': دمای اشباع (°C),
            'error': پیام خطا یا None,
            'warning': پیام هشدار یا None,
        }
    """
    
    # ============================================================
    # مقدار اولیه نتیجه
    # ============================================================
    result = {
        'kv': 0.0,
        'x': 0.0,
        'x_critical': 0.0,
        'x_s': 0.0,
        'F_gamma': 0.0,
        'Y': 0.0,
        'is_choked': False,
        'rho': 0.0,
        'temp_sat': 0.0,
        'error': None,
        'warning': None,
    }
    
    # ============================================================
    # اعتبارسنجی ورودی
    # ============================================================
    if mass_flow_kg_h <= 0:
        result['error'] = "دبی جرمی باید بزرگ‌تر از صفر باشد"
        return result
    
    if inlet_pressure_bar_abs <= 0:
        result['error'] = "فشار ورودی باید بزرگ‌تر از صفر باشد"
        return result
    
    if pressure_drop_bar <= 0:
        result['error'] = "افت فشار باید بزرگ‌تر از صفر باشد"
        return result
    
    if pressure_drop_bar >= inlet_pressure_bar_abs:
        result['error'] = "افت فشار نمی‌تواند از فشار ورودی بیشتر باشد"
        return result
    
    # ============================================================
    # چگالی و دمای اشباع
    # ============================================================
    if rho_kg_m3 is None or rho_kg_m3 <= 0:
        props = get_steam_properties(inlet_pressure_bar_abs)
        rho = props['rho']
        temp_sat = props['temp_sat']
        result['warning'] = (
            "چگالی از جدول بخار اشباع درآورده شد. "
            "اگر بخار سوپرهیت است، چگالی واقعی را وارد کنید."
        )
    else:
        rho = rho_kg_m3
        props = get_steam_properties(inlet_pressure_bar_abs)
        temp_sat = props['temp_sat']
    
    if rho <= 0:
        result['error'] = "چگالی محاسبه‌شده نامعتبر است"
        return result
    
    result['rho'] = rho
    result['temp_sat'] = temp_sat
    
    # ============================================================
    # نسبت افت فشار
    # ============================================================
    x = pressure_drop_bar / inlet_pressure_bar_abs
    result['x'] = round(x, 4)
    
    # ============================================================
    # تصحیح gamma
    # ============================================================
    F_gamma = gamma / 1.4
    result['F_gamma'] = round(F_gamma, 4)
    
    # ============================================================
    # نسبت بحرانی (Choked Flow Threshold)
    # ============================================================
    x_critical = F_gamma * x_t
    result['x_critical'] = round(x_critical, 4)
    
    # ============================================================
    # نسبت مؤثر
    # ============================================================
    x_s = min(x, x_critical)
    result['x_s'] = round(x_s, 4)
    
    # ============================================================
    # بررسی Choked Flow
    # ============================================================
    result['is_choked'] = (x > x_critical)
    
    if result['is_choked']:
        result['warning'] = (
            f"⚠️ جریان خفه (Choked Flow): افت فشار ({pressure_drop_bar:.2f} bar) "
            f"بیشتر از حد مجاز ({x_critical * inlet_pressure_bar_abs:.2f} bar) است."
        )
    
    # ============================================================
    # ضریب انبساط Y
    # ============================================================
    try:
        Y = 1 - x_s / (3 * F_gamma * x_t)
        Y = max(Y_MIN, Y)
        result['Y'] = round(Y, 4)
    except ZeroDivisionError:
        result['error'] = "خطا در محاسبه Y (تقسیم بر صفر)"
        return result
    
    # ============================================================
    # محاسبه Kv نهایی
    # ============================================================
    try:
        inner = x_s * inlet_pressure_bar_abs * rho
        
        if inner <= 0:
            result['error'] = "عبارت زیر رادیکال نامعتبر است"
            return result
        
        denominator = 31.6 * Y * math.sqrt(inner)
        
        if denominator <= 0:
            result['error'] = "مخرج فرمول صفر است"
            return result
        
        Kv = mass_flow_kg_h / denominator
        result['kv'] = round(Kv, 4)
    
    except (ValueError, ZeroDivisionError) as e:
        result['error'] = f"خطا در محاسبه Kv: {e}"
        return result
    
    return result


# ================================================================
# توابع کمکی
# ================================================================

def psi_to_bar(psi: float) -> float:
    """تبدیل psi به bar"""
    try:
        return round(float(psi) * PSI_TO_BAR, 4)
    except (ValueError, TypeError):
        return 0.0


def bar_to_psi(bar: float) -> float:
    """تبدیل bar به psi"""
    try:
        return round(float(bar) * BAR_TO_PSI, 4)
    except (ValueError, TypeError):
        return 0.0


def get_suggested_dp_limit(inlet_pressure_bar_abs: float) -> float:
    """
    حداکثر افت فشار مجاز (50% فشار ورودی)
    
    Args:
        inlet_pressure_bar_abs: فشار مطلق ورودی (bar)
    
    Returns:
        حداکثر افت فشار مجاز (bar)
    """
    return inlet_pressure_bar_abs * 0.5


# ================================================================
# تست داخلی
# ================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 تست فرمول IEC 60534-2-1 — شیر بخار")
    print("=" * 70)
    
    # ============================================================
    # تست ۱: داده‌های تصویر Sauter
    # ============================================================
    print("\n📊 تست ۱: داده‌های تصویر Sauter")
    print("-" * 70)
    
    m = 45.36       # kg/h
    P1 = 4.136      # bar abs
    dP = 2.068      # bar
    
    result = calculate_kv_steam(m, P1, dP)
    
    print(f"  ṁ  = {m} kg/h")
    print(f"  P₁ = {P1} bar abs")
    print(f"  ΔP = {dP} bar")
    print()
    print(f"  Kv         = {result['kv']:.4f}")
    print(f"  x          = {result['x']}")
    print(f"  x_critical = {result['x_critical']}")
    print(f"  x_s        = {result['x_s']}")
    print(f"  F_gamma    = {result['F_gamma']}")
    print(f"  Y          = {result['Y']}")
    print(f"  ρ          = {result['rho']:.4f} kg/m³")
    print(f"  T_sat      = {result['temp_sat']} °C")
    print(f"  Choked     = {result['is_choked']}")
    print()
    print(f"  🎯 Sauter: 0.96 | IEC: {result['kv']:.4f} | "
          f"خطا: {abs(result['kv'] - 0.96) / 0.96 * 100:.2f}%")
    
    # ============================================================
    # تست ۲: تست‌های قبلی
    # ============================================================
    print("\n📊 تست ۲: تست‌های قبلی (تغییر P₁)")
    print("-" * 70)
    
    test_cases = [
        (2.5, 1.65, 1.57),
        (3.0, 1.65, 1.30),
        (4.137, 1.65, 0.98),
        (5.0, 1.65, 0.86),
        (6.0, 1.65, 0.76),
        (8.0, 1.65, 0.63),
    ]
    
    print(f"  {'P₁':>6}  {'dP':>6}  {'Sauter':>8}  {'IEC':>8}  {'خطا':>8}")
    print("  " + "-" * 50)
    
    total_error = 0
    for p1, dp, kv_sauter in test_cases:
        r = calculate_kv_steam(45.36, p1, dp)
        kv_iec = r['kv']
        if kv_sauter > 0:
            error = abs(kv_iec - kv_sauter) / kv_sauter * 100
        else:
            error = 0
        total_error += error
        
        print(f"  {p1:>6.3f}  {dp:>6.2f}  {kv_sauter:>8.3f}  "
              f"{kv_iec:>8.3f}  {error:>7.2f}%")
    
    print("  " + "-" * 50)
    print(f"  {'':>6}  {'':>6}  {'':>8}  {'':>8}  "
          f"{total_error / len(test_cases):>7.2f}% (میانگین)")
    
    # ============================================================
    # تست ۳: Choked Flow
    # ============================================================
    print("\n📊 تست ۳: بررسی Choked Flow")
    print("-" * 70)
    
    r = calculate_kv_steam(45.36, 4.136, 3.0)
    print(f"  P₁ = 4.136 bar, ΔP = 3.0 bar")
    print(f"  x = {r['x']}, x_critical = {r['x_critical']}")
    print(f"  Choked: {r['is_choked']}")
    print(f"  Kv = {r['kv']:.4f}")
    if r['warning']:
        print(f"  ⚠️ {r['warning']}")
    
    print()
    print("=" * 70)
    print("🎉 تست کامل شد")
    print("=" * 70)