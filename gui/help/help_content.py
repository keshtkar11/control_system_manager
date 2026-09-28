# gui/help/help_content.py
"""
محتوای Help Center - دوزبانه (فارسی + انگلیسی)
"""

# ================================================================
# HELP SECTIONS
# ================================================================

HELP_SECTIONS = {
    # ============================================================
    # 1. USER GUIDE
    # ============================================================
    'user_guide': {
        'title_en': 'User Guide',
        'title_fa': 'راهنمای کاربر',
        'icon': 'guide',
        'content': """
═══════════════════════════════════════════════════════
📖 USER GUIDE / راهنمای کاربر
═══════════════════════════════════════════════════════

🇬🇧 ENGLISH:
─────────────────────────────────────────────────────
Welcome to Control System Devices Manager!

This application helps you:
• Manage multiple projects
• Track device I/O points
• Create reusable templates
• Export professional reports
• Manage custom components

GETTING STARTED:
1. Create a new project from the File menu
2. Add sections to organize your devices
3. Add devices with their components
4. Export reports in Excel or PDF format

🇮🇷 فارسی:
─────────────────────────────────────────────────────
به نرم‌افزار مدیریت دستگاه‌های سیستم کنترل خوش آمدید!

این برنامه به شما کمک می‌کند:
• چندین پروژه را مدیریت کنید
• نقاط I/O دستگاه‌ها را پیگیری کنید
• قالب‌های قابل استفاده مجدد بسازید
• گزارش‌های حرفه‌ای تولید کنید
• کامپوننت‌های سفارشی مدیریت کنید

شروع به کار:
۱. از منوی File یک پروژه جدید بسازید
۲. برای سازماندهی دستگاه‌ها، بخش اضافه کنید
۳. دستگاه‌ها را با کامپوننت‌هایشان اضافه کنید
۴. گزارش‌ها را به صورت Excel یا PDF صادر کنید

═══════════════════════════════════════════════════════

📌 KEY CONCEPTS / مفاهیم کلیدی
─────────────────────────────────────────────────────

🇬🇧 
• Project: Top-level container for your work
• Section: Group of related devices (e.g., Mechanical Room)
• Device: Individual equipment (e.g., PU-1)
• Component: Parts of a device (e.g., Motor, Sensor)
• Template: Reusable pattern for devices

🇮🇷
• پروژه: ظرف اصلی کار شما
• بخش: گروهی از دستگاه‌های مرتبط (مثلاً موتورخانه)
• دستگاه: تجهیز منفرد (مثلاً PU-1)
• کامپوننت: اجزای دستگاه (مثلاً موتور، سنسور)
• قالب: الگوی قابل استفاده مجدد

═══════════════════════════════════════════════════════

📌 PROJECT MANAGEMENT / مدیریت پروژه
─────────────────────────────────────────────────────

🇬🇧
Create Project:
1. File → New Project (Ctrl+N)
2. Enter a unique name
3. Fill project information (Client, Consultant, etc.)

🇮🇷
ایجاد پروژه:
۱. File → New Project (Ctrl+N)
۲. یک نام یکتا وارد کنید
۳. اطلاعات پروژه را پر کنید

═══════════════════════════════════════════════════════

📌 DEVICE MANAGEMENT / مدیریت دستگاه
─────────────────────────────────────────────────────

🇬🇧
Add Device:
1. Select a section first
2. Click "Add" in toolbar or press Ctrl+Shift+A
3. Enter device details:
   • Name: Device identifier (e.g., PU-1)
   • Description: Device type (e.g., Boiler Pump)
   • INFO: Location or extra info
4. Set component quantities
5. Save

🇮🇷
افزودن دستگاه:
۱. ابتدا یک بخش انتخاب کنید
۲. روی "Add" در نوار ابزار کلیک کنید یا Ctrl+Shift+A
۳. اطلاعات دستگاه را وارد کنید:
   • Name: شناسه دستگاه (مثلاً PU-1)
   • Description: نوع دستگاه (مثلاً پمپ بویلر)
   • INFO: مکان یا اطلاعات اضافی
۴. تعداد کامپوننت‌ها را تنظیم کنید
۵. ذخیره کنید

═══════════════════════════════════════════════════════
""",
    },
    
    # ============================================================
    # 2. ABBREVIATION GUIDE
    # ============================================================
    'abbreviation': {
        'title_en': 'Abbreviation Guide',
        'title_fa': 'راهنمای اختصارات',
        'icon': 'info_circle',
        'content': """
═══════════════════════════════════════════════════════
🔤 ABBREVIATION GUIDE / راهنمای اختصارات
═══════════════════════════════════════════════════════

🔵 SENSORS / سنسورها
─────────────────────────────────────────────────────
Code      English                    فارسی
──────    ──────────────────────    ────────────────────
FS        Flow Switch                سوئیچ جریان
DTS       Duct Temp Sensor           سنسور دمای کانال
ITS       Immersion Temp Sensor      سنسور دمای غوطه‌وری
DTHS      Duct Temp & Humidity       سنسور دما و رطوبت کانال
FR        Freeze Protection          محافظ یخ‌زدگی
AQ        Air Quality                سنسور کیفیت هوا
RTS       Room Temp Sensor           سنسور دمای اتاق
RTHS      Room Temp & Humidity       سنسور دما و رطوبت اتاق
SD        Smoke Detector             آشکارساز دود
AVS       Air Velocity Sensor        سنسور سرعت هوا
LS        Level Switch               سوئیچ سطح
LT        Level Transmitter          ترانسمیتر سطح
PS        Pressure Switch            سوئیچ فشار
PT        Pressure Transmitter       ترانسمیتر فشار
DPT       Diff. Pressure Trans.      ترانسمیتر فشار تفاضلی
DPS       Diff. Pressure Switch      سوئیچ فشار تفاضلی
SOU       Sound Meter                صدا سنج
LUX       Lux Meter                  نور سنج
VIB       Vibration Sensor           لرزش سنج

🟢 ACTUATORS / اکچویتورها
─────────────────────────────────────────────────────
VA        Valve Actuator             اکچویتور شیر
DAM_T1,DAM_T2   Damper (0-1)        دمپر دیجیتال
DAM_T3,DAM_T4   Damper (0-10V)       دمپر آنالوگ
SV        Solenoid Valve             شیر برقی
MOV       Motorize Valve             شیر موتوری

🟡 EQUIPMENT / تجهیزات
─────────────────────────────────────────────────────
PU        Motor                      موتور
VSD       Variable Speed Drive       درایو سرعت متغیر
FC        Fancoil                    فن کویل
LIG       Lighting                   خط روشنایی
BUZ       Buzzer Alarm               زنگ خطر
MOD       Modbus                     مدباس

🔴 STATUS & COMMANDS / وضعیت و فرمان
─────────────────────────────────────────────────────
FA        Fault Status               وضعیت خطا
FE        Run Status                 وضعیت روشن
SLE       Local/Remote Status        وضعیت سلکتور
CMD       Start/Stop Command         فرمان شروع/توقف
Knob      Setpoint Knob              تنظیم دما دیواری
SPR       Reserve                    رزرو

═══════════════════════════════════════════════════════
""",
    },
    
    # ============================================================
    # 3. KEYBOARD SHORTCUTS
    # ============================================================
    'shortcuts': {
        'title_en': 'Keyboard Shortcuts',
        'title_fa': 'میانبرهای صفحه کلید',
        'icon': 'keyboard',
        'content': """
═══════════════════════════════════════════════════════
⌨️ KEYBOARD SHORTCUTS / میانبرهای صفحه کلید
═══════════════════════════════════════════════════════

📁 FILE OPERATIONS / عملیات فایل
─────────────────────────────────────────────────────
Shortcut          Action / عملکرد
─────────────     ───────────────────────────────────
Ctrl+N            New Project / پروژه جدید
Ctrl+O            Open Project Manager / مدیر پروژه
Ctrl+E            Export to Excel / خروجی Excel
Ctrl+P            Export to PDF / خروجی PDF
Ctrl+B            Backup Current Project / بکاپ پروژه
Ctrl+R            Restore Project / بازیابی پروژه
Ctrl+Q            Exit / خروج

📝 EDIT OPERATIONS / عملیات ویرایش
─────────────────────────────────────────────────────
Ctrl+Shift+A      Add Device / افزودن دستگاه
Ctrl+E            Edit Device / ویرایش دستگاه
Delete            Delete Device / حذف دستگاه
Ctrl+C            Copy Device / کپی دستگاه
Ctrl+V            Paste Device / چسباندن دستگاه
Ctrl+Z            Undo / بازگشت
Ctrl+Y            Redo / جلورفتن

🔍 VIEW & NAVIGATION / نمایش و ناوبری
─────────────────────────────────────────────────────
F5                Refresh / بروزرسانی
Ctrl+F            Global Search / جستجوی جهانی

🤖 AI & LEARNING / هوش مصنوعی و یادگیری
─────────────────────────────────────────────────────
Ctrl+L            Learn from Project / یادگیری
Ctrl+Shift+P      Predict Components / پیش‌بینی
Ctrl+Shift+O      Optimize I/O / بهینه‌سازی
Ctrl+Shift+S      Learning Statistics / آمار یادگیری
Ctrl+Shift+A      Open AI Assistant / دستیار AI

═══════════════════════════════════════════════════════
""",
    },
    
    # ============================================================
    # 4. FAQ
    # ============================================================
    'faq': {
        'title_en': 'FAQ',
        'title_fa': 'سوالات متداول',
        'icon': 'question',
        'content': """
═══════════════════════════════════════════════════════
❓ FREQUENTLY ASKED QUESTIONS / سوالات متداول
═══════════════════════════════════════════════════════

🔹 GENERAL / عمومی
─────────────────────────────────────────────────────

Q1: Does the program require internet?
    آیا برنامه به اینترنت نیاز دارد؟
─────────────────────────────────────────────────────
🇬🇧 No, the program works offline. Internet is only 
   needed for AI Assistant features.

🇮🇷 خیر، برنامه به صورت آفلاین کار می‌کند. فقط برای 
   استفاده از دستیار AI به اینترنت نیاز است.

─────────────────────────────────────────────────────

Q2: Where is the database stored?
    دیتابیس در کجا ذخیره می‌شود؟
─────────────────────────────────────────────────────
🇬🇧 Location: C:\\ProgramData\\IO_List_Generator\\

🇮🇷 مسیر: C:\\ProgramData\\IO_List_Generator\\

─────────────────────────────────────────────────────

🔹 PROJECT & DEVICE / پروژه و دستگاه
─────────────────────────────────────────────────────

Q3: What's the difference between INFO and Description?
    تفاوت INFO و Description چیست؟
─────────────────────────────────────────────────────
🇬🇧 Description: Device type (for grouping)
                Example: Boiler Pump
   INFO: Additional info (location, tag)
         Example: Mechanical Room

🇮🇷 Description: نوع دستگاه (برای گروه‌بندی)
                مثال: پمپ بویلر
   INFO: اطلاعات اضافی (مکان، تگ)
         مثال: موتورخانه

─────────────────────────────────────────────────────

Q4: Why is the device count different in reports?
    چرا تعداد دستگاه‌ها در گزارش متفاوت است؟
─────────────────────────────────────────────────────
🇬🇧 For Pumps and Drives, count is based on Quantity.
   Example: If PU=3, it counts as 3 devices.

🇮🇷 برای پمپ‌ها و درایوها، تعداد بر اساس Quantity است.
   مثال: اگر PU=3 باشد، 3 دستگاه حساب می‌شود.

─────────────────────────────────────────────────────

🔹 BACKUP / بکاپ
─────────────────────────────────────────────────────

Q5: Difference between "Backup Database" and "Backup Project"?
    تفاوت "Backup Database" و "Backup Project" چیست؟
─────────────────────────────────────────────────────
🇬🇧 Backup Database: Full backup (all projects + templates)
   Backup Project: Only current project (as JSON)

🇮🇷 Backup Database: بکاپ کامل (همه پروژه‌ها + تمپلیت‌ها)
   Backup Project: فقط پروژه جاری (به صورت JSON)

═══════════════════════════════════════════════════════
""",
    },
    
    # ============================================================
    # 5. TROUBLESHOOTING
    # ============================================================
    'troubleshooting': {
        'title_en': 'Troubleshooting',
        'title_fa': 'عیب‌یابی',
        'icon': 'warning_triangle',
        'content': """
═══════════════════════════════════════════════════════
🔧 TROUBLESHOOTING / عیب‌یابی
═══════════════════════════════════════════════════════

❌ Problem 1: Program doesn't open
   مشکل ۱: برنامه باز نمی‌شود
─────────────────────────────────────────────────────
🇬🇧 Solutions:
   1. Check if Python is installed
   2. Install required libraries:
      pip install -r requirements.txt
   3. Run the program:
      python main.py

🇮🇷 راه‌حل‌ها:
   1. بررسی کنید که Python نصب باشد
   2. کتابخانه‌های مورد نیاز را نصب کنید
   3. برنامه را اجرا کنید: python main.py

─────────────────────────────────────────────────────

❌ Problem 2: Database can't be opened
   مشکل ۲: دیتابیس باز نمی‌شود
─────────────────────────────────────────────────────
🇬🇧 Solutions:
   1. Check if folder exists:
      C:\\ProgramData\\IO_List_Generator\\
   2. Create it manually if missing
   3. Check write permissions

🇮🇷 راه‌حل‌ها:
   1. بررسی کنید که پوشه وجود داشته باشد
   2. اگر وجود ندارد، دستی بسازید
   3. دسترسی نوشتن را بررسی کنید

─────────────────────────────────────────────────────

❌ Problem 3: PDF export fails
   مشکل ۳: خروجی PDF تولید نمی‌شود
─────────────────────────────────────────────────────
🇬🇧 Solutions:
   1. Install reportlab:
      pip install reportlab
   2. Install openpyxl:
      pip install openpyxl
   3. Check Help → About for versions

🇮🇷 راه‌حل‌ها:
   1. نصب reportlab
   2. نصب openpyxl
   3. از Help → About نسخه‌ها را بررسی کنید

═══════════════════════════════════════════════════════
""",
    },
    
    # ============================================================
    # 6. CHANGELOG
    # ============================================================
    'changelog': {
        'title_en': 'Changelog',
        'title_fa': 'تاریخچه تغییرات',
        'icon': 'list',
        'content': """
═══════════════════════════════════════════════════════
📝 CHANGELOG / تاریخچه تغییرات
═══════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────┐
│ Version 2.1 (1403/07/01) - Design System Update     │
├─────────────────────────────────────────────────────┤
│ ✨ New Features / ویژگی‌های جدید:                    │
│ • Modern Professional Design System                 │
│ • Dark & Light themes                               │
│ • Sidebar with Project Explorer                     │
│ • Toast notifications                               │
│ • New custom components library                     │
│ • Bilingual Help Center                             │
│                                                     │
│ 🔧 Improvements / بهبودها:                          │
│ • Better performance                                │
│ • Improved UX/UI                                    │
│ • Native look & feel                                │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Version 2.0 (1403/01/01)                            │
├─────────────────────────────────────────────────────┤
│ ✨ New Features / ویژگی‌های جدید:                    │
│ • Component Manager                                 │
│ • Template Manager                                  │
│ • Project Backup/Restore (JSON)                     │
│ • Professional Excel reports                        │
│ • Professional PDF reports                          │
│                                                     │
│ 🐛 Bug Fixes / رفع باگ:                            │
│ • Fixed device info changing on template save       │
│ • Fixed device count in reports                     │
│ • Fixed Persian font in PDF                         │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Version 1.0 (1402/10/01)                            │
├─────────────────────────────────────────────────────┤
│ ✨ Initial Release / نسخه اولیه:                    │
│ • Project management                                │
│ • Section management                                │
│ • Device management                                 │
│ • I/O calculation                                   │
│ • Excel and PDF export                              │
└─────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════
""",
    },
    
    # ============================================================
    # 7. ABOUT
    # ============================================================
    'about': {
        'title_en': 'About',
        'title_fa': 'درباره برنامه',
        'icon': 'info_circle',
        'content': """
═══════════════════════════════════════════════════════
ℹ️ ABOUT / درباره برنامه
═══════════════════════════════════════════════════════

        CONTROL SYSTEM DEVICES MANAGER
        ────────────────────────────────
              Version 2.1
              Build: 1403/07/01

🏢 Company / شرکت
─────────────────────────────────────────────────────
🇬🇧 Vahhaj Sanat Energy Co.
🇮🇷 شرکت مهندسی وهاج صنعت انرژی

👨‍💻 Developer / توسعه‌دهنده
─────────────────────────────────────────────────────
Mr. Keshtkar

📧 Contact / تماس
─────────────────────────────────────────────────────
• Email: info@vahhajsanat.com
• Website: www.vahhajsanat.com

🛠️ Technologies / تکنولوژی‌ها
─────────────────────────────────────────────────────
• Python 3.14
• Tkinter (GUI Framework)
• SQLite (Database)
• ReportLab (PDF Generation)
• OpenPyXL (Excel Generation)

📄 License / مجوز
─────────────────────────────────────────────────────
🇬🇧 This software is proprietary and developed for 
   Vahhaj Sanat Energy Co.

🇮🇷 این نرم‌افزار اختصاصی بوده و برای شرکت وهاج صنعت 
   انرژی توسعه یافته است.

© 1403 Vahhaj Sanat Energy Co.
All rights reserved.

═══════════════════════════════════════════════════════
""",
    },
}


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def get_section(section_id: str) -> dict:
    """دریافت یک بخش"""
    return HELP_SECTIONS.get(section_id, {})


def get_all_sections() -> dict:
    """دریافت همه بخش‌ها"""
    return HELP_SECTIONS


def get_section_ids() -> list:
    """دریافت لیست کلیدها"""
    return list(HELP_SECTIONS.keys())


# ================================================================
# EXPORTS
# ================================================================

__all__ = [
    'HELP_SECTIONS',
    'get_section',
    'get_all_sections',
    'get_section_ids',
]