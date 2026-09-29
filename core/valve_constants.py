# core/valve_constants.py
"""
ثابت‌ها و جداول مرجع برای بخش Valves (شیرها)
"""

# ============================================================
# ۱. انواع شیر (ستون ۸)
# ============================================================
VALVE_TYPES = [
    "PICV",
    "3 Way",
    "Steam",
    "Butterfly",     # ⏸️ فاز ۲
    "Motorized",     # ⏸️ فاز ۲
    "PICV+3Way",
]

# ============================================================
# ۲. مدار (ستون ۴)
# ============================================================
CIRCUIT_TYPES = [
    "گرمایش",
    "سرمایش",
    "بخار",
    "غیره",
]

# ============================================================
# ۳. واحدهای دبی (ستون ۷)
# ============================================================
# ضریب تبدیل به L/HR
FLOW_UNITS = {
    # ===== مایعات =====
    "L/HR":    1,
    "L/min":   60,
    "L/s":     3600,
    "m³/h":    1000,
    "m³/min":  60000,
    "GPM":     227.1247,
    "GPH":     3.7854,
    "CFM":     1699.01,
    
    # ===== بخار (دینامیک) =====
    "Kg/h":    None,      # دینامیک — بسته به چگالی بخار
    "lb/h":    None,      # ✅ جدید — دینامیک
    "ton/h":   None,      # دینامیک
}
# ============================================================
# ۳.۱: ثابت‌های تبدیل جرم (جدید)
# ============================================================
LB_TO_KG = 0.45359237       # 1 lb = 0.4536 kg
KG_TO_LB = 1 / LB_TO_KG     # 1 kg = 2.2046 lb
TON_TO_KG = 1000            # 1 ton = 1000 kg

# ============================================================
# ۴. نوع سیگنال موتور (ستون‌های ۱۴، ۲۰، ۲۷)
# ============================================================
SIGNAL_TYPES = [
    "Modulating , 24Vac , 0-10V",
    "Modulating , 4-20mA",
    "220V On/Off",
    "24V On/Off",
    "3-Point",
    "Modbus",
]
# ============================================================
# ۵. جدول ABQM (برای PICV)
# ============================================================
# (max_flow_LPH, model, actuator, signal)

ABQM_TABLE = [
    (700,   "ABQM15",     "AME110NLX (or TWA-Q 230V NC)", "Modulating , 24Vac , 0-10V"),
    (1200,  "ABQM15 HF",  "AME110NLX (or TWA-Q 230V NC)", "Modulating , 24Vac , 0-10V"),
    (1900,  "ABQM20HF",   "AME110NLX (or TWA-Q 230V NC)", "Modulating , 24Vac , 0-10V"),
    (3800,  "ABQM25HF",   "AME110NLX (or TWA-Q 230V NC)", "Modulating , 24Vac , 0-10V"),
    (5000,  "ABQM32HF",   "AME110NLX (or TWA-Q 230V NC)", "Modulating , 24Vac , 0-10V"),
    (7500,  "ABQM40",     "AME435QM",                     "Modulating , 24Vac , 0-10V"),
    (12500, "ABQM50",     "AME435QM",                     "Modulating , 24Vac , 0-10V"),
    (20000, "ABQM65",     "AME435QM",                     "Modulating , 24Vac , 0-10V"),
    (25000, "ABQM65HF",   "AME435QM",                     "Modulating , 24Vac , 0-10V"),
    (28000, "ABQM80",     "AME435QM",                     "Modulating , 24Vac , 0-10V"),
    (38000, "ABQM100",    "AME435QM",                     "Modulating , 24Vac , 0-10V"),
    (40000, "ABQM80HF",   "AME435QM",                      "Modulating , 24Vac , 0-10V"),
    (59000, "ABQM100HF",  "AME435QM",                      "Modulating , 24Vac , 0-10V"),
    (115000, "ABQM125",  "AME55QM",                      "Modulating , 24Vac , 0-10V"),
    (140000, "ABQM125HF",  "AME55QM",                      "Modulating , 24Vac , 0-10V"),
    (155000, "ABQM150",  "AME55QM",                      "Modulating , 24Vac , 0-10V"),
    (200000, "ABQM150HF",  "AME55QM",                      "Modulating , 24Vac , 0-10V"),
    (320000, "ABQM200",  "AME55QM",                      "Modulating , 24Vac , 0-10V"),
]

# ============================================================
# ۶. جدول VRG 3 (برای شیر سه راهه)
# ============================================================
# (kv, DN)
VRG3_TABLE = [
    # (kv, DN)
    # ===== بخش ۱: VRG 3 (تا DN 50) =====
    (4,     15),
    (6.3,   20),
    (10,    25),
    (16,    32),
    (25,    40),
    (40,    50),
    
    # ===== بخش ۲: VF 3 (DN 65 تا DN 300) =====
    (63,    65),
    (100,   80),
    (145,   100),
    (220,   125),
    (320,   150),
    (630,   200),
    (1000,  250),
    (1350,  300),
]

VRG3_ACTUATOR = "AME 435 QM"

# ============================================================
# ۷. جدول VFS 2 (برای شیر بخار)
# ============================================================
# (kvs, DN)
VFS2_TABLE = [
    (0.4,   15),
    (0.63,  15),
    (1.0,   15),
    (1.6,   15),
    (2.5,   15),
    (4.0,   15),
    (6.3,   20),
    (10,    25),
    (16,    32),
    (25,    40),
    (40,    50),
    (63,    65),
    (100,   80),
    (145,   100),
]
# ============================================================
# ۸. Actuator برای شیر بخار (بر اساس DN)
# ============================================================
def get_steam_actuator(dn):
    """دریافت Actuator برای شیر بخار بر اساس DN"""
    if dn is None:
        return None
    if 15 <= dn <= 50:
        return "AMV(E) 25"
    elif 65 <= dn <= 100:
        return "AMV(E) 55" 
    return None

def get_3way_actuator(dn):
    """دریافت Actuator پیشنهادی برای شیر سه راهه"""
    if dn is None:
        return None
    
    if 15 <= dn <= 80:
        return "AME 435 QM"
    elif dn == 100:
        return "AME 55"
    elif 100 < dn <= 150:
        return "AME 85"
    elif 150 < dn <= 300:
        return "AME 685"
    
    return None
# ============================================================
# ۹. ثابت‌های محاسباتی
# ============================================================
PSI_TO_BAR = 0.0689476
SG_WATER = 1.0

# برای محاسبه چگالی بخار
STEAM_TEMP_C = 140
STEAM_PRESSURE_PSI = 52.4      # فشار اشباع در 140°C
STEAM_Z_FACTOR = 0.95
STEAM_V_SPECIFIC = 0.5086      # m³/kg در 140°C

# ============================================================
# ۱۰. محدودیت‌ها و پیش‌فرض‌ها
# ============================================================
DEFAULT_PRESSURE_DROP_PSI = 5
DEFAULT_FLOW_UNIT = "L/HR"

KV_MAX_3WAY = 1350                # بزرگ‌ترین Kv جدول VRG 3
KVS_MAX_STEAM = 145             # بزرگ‌ترین kvs جدول VFS 2
KV_MIN_3WAY = 4                 # کوچک‌ترین Kv جدول VRG 3

# ============================================================
# ۱۱. برچسب‌های ستون‌ها (برای UI و گزارش)
# ============================================================
VALVE_COLUMNS = [
    # (شماره، کلید، برچسب انگلیسی، برچسب فارسی، گروه)
    (1,  "no",              "No",                    "ردیف",                     "base"),
    (2,  "equipment",       "Equipment",             "مشخصات تجهیز",             "base"),
    (3,  "quantity",        "Qty",                   "تعداد",                    "base"),
    (4,  "circuit",         "Circuit",               "مدار",                     "base"),
    (5,  "flow",            "Flow",                  "دبی",                      "base"),
    (6,  "pressure_drop",   "Pressure Drop (psi)",   "افت فشار (psi)",           "base"),
    (7,  "unit",            "Unit",                  "واحد",                     "base"),
    (8,  "valve_type",      "Valve Type",            "نوع شیر",                  "base"),
    (9,  "max_flow_lph",    "Max Flow (L/HR)",       "حداکثر دبی (L/HR)",        "base"),
    (10, "picv_model",      "PICV Model",            "مدل شیر PICV",             "picv"),
    (11, "picv_max_flow",   "PICV Max Flow (L/HR)",  "حداکثر دبی PICV (L/HR)",   "picv"),
    (12, "picv_percent",    "PICV %",                "درصد تنظیم PICV",          "picv"),
    (13, "picv_actuator",   "PICV Actuator",         "مدل موتور PICV",           "picv"),
    (14, "picv_signal",     "PICV Signal",           "نوع سیگنال موتور PICV",    "picv"),
    (15, "kv_calc",         "Kv Calculated",         "Kv محاسبه‌شده",            "3way"),
    (16, "kv_selected",     "Kv Selected",           "Kv انتخاب‌شده",            "3way"),
    (17, "3way_dn",         "3-Way DN",              "DN شیر سه راهه",           "3way"),
    (18, "3way_model",      "3-Way Model",           "مدل شیر سه راهه",          "3way"),
    (19, "3way_actuator",   "3-Way Actuator",        "مدل موتور سه راهه",        "3way"),
    (20, "3way_signal",     "3-Way Signal",          "نوع سیگنال موتور سه راهه", "3way"),
    (21, "steam_pressure",  "Steam Inlet (bar)",     "فشار ورودی بخار (bar)",    "steam"),
    (22, "kvs_calc",        "kvs Calculated",        "kvs محاسبه‌شده",           "steam"),
    (23, "kvs_selected",    "kvs Selected",          "kvs انتخاب‌شده",           "steam"),
    (24, "steam_dn",        "Steam DN",              "DN شیر بخار",              "steam"),
    (25, "steam_model",     "Steam Model",           "مدل شیر بخار",             "steam"),
    (26, "steam_actuator",  "Steam Actuator",        "مدل موتور شیر بخار",       "steam"),
    (27, "steam_signal",    "Steam Signal",          "نوع سیگنال موتور بخار",    "steam"),
    (28, "warning_3way",    "3-Way Warning",         "هشدار VRG 3",              "warning"),
    (29, "warning_steam",   "Steam Warning",         "هشدار Steam",              "warning"),
    (30, "warning_general", "Warning",               "هشدار کلی",                "warning"),
]

# ============================================================
# ۱۲. گروه‌ها (برای نمایش شرطی)
# ============================================================
VALVE_TYPE_FIELDS = {
    "PICV": [
        "picv_model", "picv_max_flow", "picv_percent",
        "picv_actuator", "picv_signal",
    ],
    "3 Way": [
        "kv_calc", "kv_selected", "3way_dn", "3way_model",
        "3way_actuator", "3way_signal", "warning_3way",
    ],
    "Steam": [
        "steam_pressure",
        "steam_flow_kg_h",     # ✅ جدید
        "steam_flow_lb_h",     # ✅ جدید
        "kvs_calc",
        "kvs_selected",
        "steam_dn",
        "steam_model",
        "steam_actuator",
        "steam_signal",
        "warning_steam",
    ],
    
    "PICV+3Way": [
        "picv_model", "picv_max_flow", "picv_percent",
        # بدون موتور PICV
        "kv_calc", "kv_selected", "3way_dn", "3way_model",
        "3way_actuator", "3way_signal", "warning_3way",
    ],

}

# ============================================================
# ۱۳. STEAM DATA (جدید — نسخه نهایی)
# ============================================================
# 
# ⚠️ توجه:
#   - جدول خواص بخار (فشار → دما و چگالی) در 
#     core/steam_kv_calculator.py قرار دارد.
#   - این فایل فقط دسته‌بندی و کاربردها را نگه می‌دارد.

# ===== ۱۳.۱: دسته‌بندی فشار بخار =====
STEAM_CATEGORIES = [
    {
        'code': 'VACUUM',
        'name_fa': 'بخار در خلأ',
        'name_en': 'Vacuum Steam',
        'bar_min': 0.0,
        'bar_max': 0.5,
        'temp_min': 0.0,
        'temp_max': 111.4,
        'color': '#95A5A6',
        'icon': '⬇️',
        'warnings': ['فشار کمتر از اتمسفر — نیاز به سیستم خلأ'],
    },
    {
        'code': 'LPS',
        'name_fa': 'بخار کم‌فشار',
        'name_en': 'Low Pressure Steam',
        'bar_min': 1.0,
        'bar_max': 3.0,
        'temp_min': 120.0,
        'temp_max': 143.6,
        'color': '#3498DB',
        'icon': '🔵',
        'warnings': [],
    },
    {
        'code': 'MPS',
        'name_fa': 'بخار متوسط',
        'name_en': 'Medium Pressure Steam',
        'bar_min': 4.0,
        'bar_max': 10.0,
        'temp_min': 151.8,
        'temp_max': 184.1,
        'color': '#F39C12',
        'icon': '🟡',
        'warnings': [
            'نیاز به تجهیزات PN16 به بالا',
            'بازرسی دوره‌ای الزامی است',
        ],
    },
    {
        'code': 'HPS',
        'name_fa': 'بخار پرفشار',
        'name_en': 'High Pressure Steam',
        'bar_min': 11.0,
        'bar_max': 25.0,
        'temp_min': 190.0,
        'temp_max': 226.0,
        'color': '#E67E22',
        'icon': '🟠',
        'warnings': [
            'نیاز به تجهیزات PN25+',
            'دریچه اطمینان (Safety Valve) الزامی است',
            'بازرسی دوره‌ای ۶ ماه',
            'رعایت استاندارد ASME B31.1',
        ],
    },
    {
        'code': 'VHPS',
        'name_fa': 'بخار فوق‌پرفشار',
        'name_en': 'Very High Pressure Steam',
        'bar_min': 25.0,
        'bar_max': 100.0,
        'temp_min': 226.0,
        'temp_max': 311.0,
        'color': '#C0392B',
        'icon': '🔴',
        'warnings': [
            'نیاز به تجهیزات PN40+ و آلیاژهای خاص',
            'بازرسی دوره‌ای ۳ ماه',
            'مدارک تست سالانه',
            'رعایت استاندارد ASME Section I',
            'خطرات جدی — مهندس مجرب الزامی',
        ],
    },
]


# ===== ۱۳.۲: کاربردهای متداول بخار =====
STEAM_APPLICATIONS = [
    {
        'name_fa': 'گرمایش ساختمان',
        'name_en': 'Building Heating',
        'bar_min': 0.5,
        'bar_max': 1.5,
        'temp_min': 110.0,
        'temp_max': 127.4,
        'icon': '🔥',
        'category': 'HVAC',
    },
    {
        'name_fa': 'رطوبت‌ساز HVAC',
        'name_en': 'HVAC Humidifier',
        'bar_min': 1.0,
        'bar_max': 3.0,
        'temp_min': 120.0,
        'temp_max': 143.6,
        'icon': '💧',
        'category': 'HVAC',
    },
    {
        'name_fa': 'کویل گرمایش/سرمایش',
        'name_en': 'Heating/Cooling Coil',
        'bar_min': 0.5,
        'bar_max': 2.0,
        'temp_min': 110.0,
        'temp_max': 133.5,
        'icon': '♨️',
        'category': 'HVAC',
    },
    {
        'name_fa': 'اتوکلاو / استریلایزر',
        'name_en': 'Autoclave / Sterilizer',
        'bar_min': 2.0,
        'bar_max': 4.0,
        'temp_min': 133.5,
        'temp_max': 151.8,
        'icon': '🏥',
        'category': 'Medical',
    },
    {
        'name_fa': 'شست‌وشوی صنعتی',
        'name_en': 'Industrial Washing',
        'bar_min': 3.0,
        'bar_max': 6.0,
        'temp_min': 143.6,
        'temp_max': 165.0,
        'icon': '🧼',
        'category': 'Industrial',
    },
    {
        'name_fa': 'صنایع غذایی',
        'name_en': 'Food Processing',
        'bar_min': 3.0,
        'bar_max': 8.0,
        'temp_min': 143.6,
        'temp_max': 175.4,
        'icon': '🍽️',
        'category': 'Food',
    },
    {
        'name_fa': 'خشکشویی صنعتی',
        'name_en': 'Industrial Laundry',
        'bar_min': 4.0,
        'bar_max': 8.0,
        'temp_min': 151.8,
        'temp_max': 175.4,
        'icon': '👔',
        'category': 'Industrial',
    },
    {
        'name_fa': 'فرآیندهای شیمیایی',
        'name_en': 'Chemical Processing',
        'bar_min': 6.0,
        'bar_max': 20.0,
        'temp_min': 165.0,
        'temp_max': 215.0,
        'icon': '⚗️',
        'category': 'Chemical',
    },
    {
        'name_fa': 'پالایشگاه',
        'name_en': 'Oil Refinery',
        'bar_min': 10.0,
        'bar_max': 40.0,
        'temp_min': 184.1,
        'temp_max': 250.0,
        'icon': '🛢️',
        'category': 'Petrochemical',
    },
    {
        'name_fa': 'نیروگاه / توربین بخار',
        'name_en': 'Power Plant / Steam Turbine',
        'bar_min': 25.0,
        'bar_max': 100.0,
        'temp_min': 226.0,
        'temp_max': 311.0,
        'icon': '⚡',
        'category': 'Power',
    },
]
# ============================================================
# ۱۴. VFS 2 VALVE INFO (از کاتالوگ Danfoss)
# ============================================================

VFS2_INFO = {
    'name': 'VFS 2',
    'manufacturer': 'Danfoss',
    'type': '2-way seated valve for steam',
    'type_fa': 'شیر دو راهه نشیمن‌دار برای بخار',
    
    # ===== Pressure / Temperature =====
    'pn': 25,                              # PN 25
    't_max': 200,                          # 200°C
    't_min': 2,                            # 2°C (یا -10 با stem heater)
    't_min_with_heater': -10,              # -10°C با stem heater
    
    # ===== Connection =====
    'connection': 'Flange ISO 7005-2',
    'connection_fa': 'فلنجی ISO 7005-2',
    
    # ===== Characteristics =====
    'characteristic': 'Logarithmic',
    'control_range': '30:1 / 50:1 / 100:1',
    'leakage': 'max. 0.05% of kvs',
    
    # ===== Materials =====
    'body_material': 'Ductile Iron EN-GJS-400-18-LT',
    'body_material_short': 'Ductile Iron',
    'trim_material': 'Stainless Steel',
    'gland_seal': 'Replaceable PTFE rings',
    
    # ===== Steam Limits =====
    'steam_dp_max_physical': 6.0,          # 6 bar — حداکثر فیزیکی
    'steam_dp_max_recommended': 4.0,       # 4 bar — پیشنهادی
    'steam_dp_ratio_max': 0.40,            # 40% فشار مطلق (از دیاگرام)
    
    # ===== Ranges =====
    'dn_range': (15, 100),
    'kvs_range': (0.4, 145),
    
    # ===== Medium =====
    'medium': 'Circulation water/glycolic water up to 50% / steam',
    'medium_fa': 'آب / آب‌گلیکول تا 50% / بخار',
    'medium_ph_min': 7,
    'medium_ph_max': 10,
}


# ============================================================
# ۱۵. VFS 2 STEAM CRITICAL RATIO (از کاتالوگ)
# ============================================================
# 
# کاتالوگ می‌گوید:
#   "Steam valve sizing is based on 40% of the absolute steam pressure
#    (immediately upstream of the valve), being dropped across the valve 
#    when fully open."
#
# پس نسبت بحرانی برای بخار 0.40 است (نه 0.65 که از فرمول IEC می‌آید).
#

STEAM_X_CRITICAL_VFS2 = 0.40

# ===== ۱۳.۳: محدودیت‌های محاسبه Kv بخار =====
STEAM_X_T_DEFAULT = 0.4          # ضریب هندسی شیر (Globe valve)
STEAM_GAMMA = 1.3                # ضریب آیزنتروپیک بخار اشباع
STEAM_DP_RATIO_MAX = 0.5         # حداکثر نسبت ΔP/P₁ (توصیه Sauter)