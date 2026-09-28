# 🏗️ Control System Manager — Context

> این فایل برای انتقال context پروژه به چت/توسعه‌دهنده جدید است.
> آخرین به‌روزرسانی: 1405/07/06 (2026/09/27)
> نسخه پروژه: 1.0

---

## 📌 اطلاعات پایه

| فیلد | مقدار |
|------|-------|
| **نام پروژه** | Control System Manager |
| **هدف** | برنامه طراحی سیستم کنترل BMS |
| **مسیر پروژه** | `D:\01-Projects\Control System Design\control_system_manager` |
| **مسیر داده‌ها** | `D:\BMS Projects\IO_List_Generator` |
| **سازنده** | Vahhaj Sanat Energy Co. |
| **طراح** | Mr. Keshtkar |

---

## 🛠️ تکنولوژی‌ها

### زبان و فریمورک:
- **Python 3.14**
- **Tkinter** — رابط کاربری
- **SQLite** — دیتابیس

### کتابخانه‌های کلیدی:
| کتابخانه | کاربرد |
|----------|--------|
| `openai` | اتصال به AI (CodeCraft API) |
| `httpx` | HTTP Client برای AI |
| `reportlab` | تولید PDF |
| `python-docx` | تولید Word |
| `openpyxl` | تولید Excel |
| `Pillow (PIL)` | پردازش تصویر |
| `arabic-reshaper` | آماده‌سازی متن فارسی |
| `python-bidi` | RTL برای فارسی |
| `send2trash` | حذف ایمن فایل‌ها |

### فونت‌های استفاده‌شده:
- `tahoma.ttf` — متن عمومی و PDF
- `BNazanin.ttf` — متن فارسی
- `BLotus.ttf` — تیتر فارسی
- `BMitra.ttf` — متن فارسی

---

## 🏛️ معماری لایه‌ها



---

## ✅ کارهای انجام‌شده (فاز ۱-۴)

### 🔹 فاز ۱: رفع باگ‌های Learning Engine
- ✅ `_extract_patterns` (الگوهای ترکیبی)
- ✅ `_suggest_io_optimization`
- ✅ `_detect_equipment_type_from_tag`
- ✅ `_get_project_templates`
- ✅ `get_statistics` با label
- ✅ `predict_component_needs` با label

### 🔹 فاز ۲: Local Proposal Generator
- ✅ `_importer` با lazy loading
- ✅ `_load_section_template` با fallback
- ✅ `_get_section_image_markdown`
- ✅ `getattr` امن در همه جا
- ✅ `_collect_project_data` چک دستگاه خالی

### 🔹 فاز ۳: DeepSeek Client + Config
- ✅ `utils/config_manager.py` (جدید)
- ✅ `gui/ai_settings_dialog.py` (جدید)
- ✅ خواندن API Key از `config.json`
- ✅ Test Connection با UI
- ✅ پشتیبانی از Environment Variables

### 🔹 فاز ۳.۵: Section Detector
- ✅ اولویت توضیحات
- ✅ Regex patterns
- ✅ تشخیص نام‌های بیمارستانی (ICU, NICU, CCU, ...)
- ✅ پشتیبانی از Floor, Mechanical Room, Exhaust Fan
- ✅ `detect_from_devices` (fallback)

### 🔹 فاز ۳.۶: Query Templates
- ✅ ترتیب: COUNT_COMPONENTS > LIST_SECTIONS > LIST_PROJECTS
- ✅ پشتیبانی از کلمات عامیانه فارسی (چیه، چی، کدام)
- ✅ `TOP_COMPONENTS` intent

### 🔹 فاز ۴: Steam Valve (IEC 60534-2-1)
- ✅ `core/steam_kv_calculator.py` (جدید)
- ✅ جدول خواص بخار (23 نقطه)
- ✅ `STEAM_CATEGORIES` (VACUUM, LPS, MPS, HPS, VHPS)
- ✅ `STEAM_APPLICATIONS` (10 کاربرد)
- ✅ `VFS2_INFO` (از کاتالوگ Danfoss)
- ✅ کارت Steam در UI
- ✅ Choked Flow detection
- ✅ تبدیل kg/h, lb/h, ton/h
- ✅ نمایش PN، TMax، Body Material

### 🔹 فاز ۴.۵: PDF فارسی
- ✅ `utils/pdf_helpers.py` (جدید)
- ✅ `fa()`, `fa_paragraph()`, `fa_mixed()`, `fa_bold()`
- ✅ `fa_safe()` برای متن‌های ترکیبی
- ✅ `_sanitize_cable_tag()` برای Cable Tag
- ✅ PDF IO List با RTL
- ✅ PDF Proposal با RTL

### 🔹 فاز ۵: EXE
- ✅ `main.spec` v2.2
- ✅ EXE یکپارچه ~65 مگابایت
- ✅ `arabic_reshaper` + `bidi` در hiddenimports
- ✅ `README.txt` (راهنمای نصب)
- ✅ `install.bat` (نصب خودکار)

### 🔹 فاز ۶: رفع باگ Backup & Migration (v1.1)
- ✅ `_init_db()` بازنویسی شد — چک نسخه Schema
- ✅ `pre_migration_*` فقط در صورت نیاز ساخته می‌شود
- ✅ `_create_auto_backup()` با `min_interval_hours=6`
- ✅ حذف ۲۱ فایل `pre_migration_*` اضافی
- ✅ سرعت startup بهبود یافت (~۱۰ برابر)

---

## ⚠️ کارهای باقی‌مانده (اختیاری)

### 🔸 کار ۱: یکسان‌سازی منطق انتخاب شیر

**مشکل:** در `select_vfs2` (بخار) از «بزرگ‌تر یا مساوی» استفاده می‌شود ولی در `select_vrg3` (سه راهه) از «نزدیک‌ترین».

**راه‌حل:** تابع `select_vfs2` را در `core/valve_calculator.py` طوری اصلاح کنید که از «نزدیک‌ترین» استفاده کند (مشابه `select_vrg3`).

**مثال:**
- `kvs = 0.5` → انتخاب `0.40` (نه `0.63`)

### 🔸 کار ۲: سری VFS 2 HP

اضافه کردن سری بخار پرفشار برای فشار بالاتر از 6 bar.

### 🔸 کار ۳: رفع باگ کوچک Query

«پرکاربردترین کامپوننت پروژه ربانی» → `project_summary` (نه `top_components`)

### 🔸 کار ۴: تصاویر جدید

افزودن:
- `mechanical_room.png`
- `exhaust_fan.png`
- `building.png`

به `ai/proposal_images/` و `section_images` در `local_proposal_generator.py`.

---

## 🗄️ مسیرهای داده (Runtime)

python test_full_system.py
python test_queries.py
python test_kvs_debug.py
python analyze_project.py

python -m pip install -r requirements.txt
python -m pip install arabic-reshaper python-bidi
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
python -m PyInstaller --clean main.spec


# 1. کلون پروژه
cd "D:\01-Projects\Control System Design\control_system_manager"

# 2. نصب کتابخانه‌ها
python -m pip install -r requirements.txt
python -m pip install arabic-reshaper python-bidi

# 3. تست اولیه
python test_full_system.py

# 4. اجرا
python main.py

# 5. Build
python -m PyInstaller --clean main.spec

# 6. EXE
.\dist\ControlSystemManager.exe