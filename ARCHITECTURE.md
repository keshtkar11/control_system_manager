# 🏗️ Control System Manager — Architecture Documentation

> مستندات معماری، ساختار، و راهنمای توسعه
> 
> **نسخه:** 1.0
> **آخرین به‌روزرسانی:** 1405/07/06 (2026/09/27)
> **وضعیت:** ✅ آماده تحویل

---

## 📑 فهرست مطالب

1. [نمای کلی](#1-نمای-کلی)
2. [معماری لایه‌ها](#2-معماری-لایهها)
3. [ساختار پوشه‌ها](#3-ساختار-پوشهها)
4. [جریان داده](#4-جریان-داده)
5. [فایل‌های کلیدی](#5-فایلهای-کلیدی)
6. [مسیرهای Runtime](#6-مسیرهای-runtime)
7. [پایگاه داده](#7-پایگاه-داده)
8. [سیستم لاگ](#8-سیستم-لاگ)
9. [Backup & Restore](#9-backup--restore)
10. [Migration & Schema Versioning](#10-migration--schema-versioning)
11. [AI System](#11-ai-system)
12. [Valve Calculations](#12-valve-calculations)
13. [PDF & Persian Support](#13-pdf--persian-support)
14. [راهنمای توسعه](#14-راهنمای-توسعه)
15. [۵ قانون طلایی](#15-۵-قانون-طلایی)
16. [چک‌لیست تغییرات](#16-چکلیست-تغییرات)

---

## 1. نمای کلی

### هدف پروژه

برنامه‌ی دسکتاپ برای طراحی، مدیریت، و مستندسازی سیستم‌های کنترل BMS (Building Management System).

### قابلیت‌های اصلی

| # | قابلیت | توضیح |
|---|--------|-------|
| 1 | **مدیریت پروژه‌ها** | CRUD کامل + Revisions |
| 2 | **مدیریت دستگاه‌ها** | با محاسبه I/O |
| 3 | **مدیریت شیرها** | PICV, 3Way, Steam |
| 4 | **AI Assistant** | چت، پروپوزال، سوال |
| 5 | **Learning Engine** | یادگیری از پروژه‌ها |
| 6 | **خروجی‌ها** | Word, PDF, Excel |
| 7 | **Attachments** | ضمیمه‌ها با Recycle Bin |
| 8 | **Backup/Restore** | Atomic + Safe |

### تکنولوژی‌ها

| دسته | تکنولوژی |
|------|-----------|
| **زبان** | Python 3.14 |
| **GUI** | Tkinter |
| **دیتابیس** | SQLite |
| **AI** | OpenAI SDK (CodeCraft API) |
| **PDF** | reportlab + arabic-reshaper + python-bidi |
| **Word** | python-docx |
| **Excel** | openpyxl |
| **تصاویر** | Pillow (PIL) |
| **Recycle Bin** | send2trash |

---

## 2. معماری لایه‌ها

### نمودار کلی

```
┌─────────────────────────────────────────────────────────────────┐
│                    main.py  (Entry Point)                       │
│                                                                 │
│  • Setup Logger  • Setup Paths  • Create Root Window           │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│               │    │               │    │               │
│    core/      │    │      ai/      │    │     gui/      │
│               │    │               │    │               │
│  منطق تجاری   │    │  هوش مصنوعی   │    │  رابط کاربری  │
│  Business     │    │  AI           │    │  UI           │
│  Logic        │    │               │    │               │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        │                    │                    │
        │                    ▼                    │
        │            ┌───────────────┐            │
        │            │               │            │
        │            │   export/     │◄───────────┘
        │            │               │
        │            │  خروجی‌ها     │
        │            └───────┬───────┘
        │                    │
        ▼                    ▼
┌─────────────────────────────────────┐
│   utils/     +     resources/       │
│                                     │
│   کمکی              منابع           │
└─────────────────────────────────────┘
```

### وابستگی‌ها

| لایه | وابسته به | توضیح |
|------|-----------|-------|
| `core/` | sqlite3, dataclasses | فقط استاندارد |
| `ai/` | `core/` + openai | منطق AI |
| `gui/` | `core/`, `ai/`, tkinter | UI |
| `export/` | `core/` + reportlab, docx | خروجی |
| `utils/` | استاندارد | کمکی |

**⚠️ قانون اصلی:** `core/` هرگز نباید به `gui/` و `ai/` وابسته باشد.

### قواعد Cross-Layer

**✅ مجاز:**
```
gui/ → core/  (خواندن داده)
gui/ → ai/    (استفاده از AI)
export/ → core/  (دریافت داده برای خروجی)
ai/ → core/   (تحلیل داده)
```

**❌ ممنوع:**
```
core/ → gui/  (هرگز!)
core/ → ai/
gui/ → sqlite3  (مستقیم)
```

---

## 3. ساختار پوشه‌ها

```
control_system_manager/
│
├── 🚀 main.py                       ← نقطه ورود
├── 📦 main.spec                     ← PyInstaller spec
├── 📄 requirements.txt              ← پکیج‌ها
├── 📄 README.md                     ← مستندات کاربر
├── 📄 ARCHITECTURE.md               ← این فایل
├── 📄 Help.txt                      ← راهنمای داخل برنامه
├── 📄 README.txt                    ← راهنمای نصب
├── 📄 CONTEXT.md                    ← انتقال context
│
├── 📁 ai/                           ← هوش مصنوعی
│   ├── ai_assistant.py              ← دستیار گفتگو
│   ├── deepseek_client.py           ← کلاینت API
│   ├── learning_engine.py           ← یادگیری
│   ├── local_proposal_generator.py  ← پروپوزال محلی
│   ├── project_query_engine.py      ← پاسخ به سوال
│   ├── query_templates.py           ← الگوهای intent
│   ├── proposal_section_detector.py ← تشخیص سکشن
│   ├── proposal_importer.py         ← import Word
│   ├── pattern_extractor.py         ← استخراج الگو
│   ├── pattern_matcher.py           ← تطبیق الگو
│   ├── project_matcher.py           ← تطبیق نام پروژه
│   ├── proposal_template.txt        ← قالب پروپوزال
│   ├── proposal_instructions.txt    ← دستورالعمل
│   ├── 📁 proposal_images/          ← 15 تصویر
│   └── 📁 proposal_templates/       ← 13 قالب
│
├── 📁 core/                         ← منطق تجاری
│   ├── models.py                    ← مدل‌های داده
│   ├── database.py                  ← DatabaseManager
│   ├── constants.py                 ← ثابت‌ها
│   ├── attachments.py               ← AttachmentManager
│   ├── component_manager.py         ← کامپوننت سفارشی
│   ├── template_manager.py          ← قالب‌ها
│   ├── history.py                   ← Undo/Redo
│   ├── validators.py                ← اعتبارسنجی
│   ├── validation_errors.py         ← خطاها
│   ├── valve_constants.py           ← جداول شیرها
│   ├── valve_calculator.py          ← محاسبات شیر
│   └── steam_kv_calculator.py       ← Kv بخار
│
├── 📁 gui/                          ← رابط کاربری
│   ├── main_window.py               ← پنجره اصلی
│   ├── sidebar.py                   ← نوار کناری
│   ├── ai_settings_dialog.py        ← تنظیمات AI
│   ├── dialogs.py                   ← دیالوگ‌ها
│   ├── attachments_panel.py         ← پنل ضمیمه‌ها
│   ├── component_dialogs.py         ← دیالوگ کامپوننت
│   ├── import_proposal_dialog.py    ← import
│   ├── template_dialogs.py          ← دیالوگ قالب
│   ├── 📁 components/               ← کامپوننت‌های UI
│   ├── 📁 dialogs_new/              ← دیالوگ‌های مدل
│   ├── 📁 help/                     ← راهنما
│   ├── 📁 layout/                   ← چیدمان
│   ├── 📁 theme/                    ← ظاهر
│   ├── 📁 valves/                   ← پنل شیرها
│   └── 📁 styles/                   ← استایل‌ها
│
├── 📁 export/                       ← خروجی‌ها
│   ├── excel_exporter.py            ← Excel
│   ├── excel_styles.py              ← استایل Excel
│   ├── excel_utils.py               ← توابع Excel
│   ├── valves_excel_exporter.py     ← Excel شیرها
│   ├── pdf_exporter.py              ← PDF IO List
│   ├── pdf_proposal_exporter.py     ← PDF پروپوزال
│   ├── word_proposal_exporter.py    ← Word پروپوزال
│   └── report_generator.py          ← گزارش
│
├── 📁 utils/                        ← توابع کمکی
│   ├── config_manager.py            ← مدیریت config
│   ├── pdf_helpers.py               ← PDF فارسی
│   ├── paths.py                     ← مسیرها (منبع واحد)
│   ├── helpers.py                   ← توابع عمومی
│   └── logger.py                    ← تنظیمات log
│
├── 📁 resources/                    ← منابع
│   ├── 📁 fonts/                    ← 5 فونت
│   ├── 📁 icons/                    ← 2 آیکون
│   └── 📁 translations/             ← ترجمه‌ها
│
├── 📁 data/                         ← دیتابیس seed
│   └── IO_List_Generator.db
│
├── 📁 tests/                        ← تست‌ها
│
├── 📁 build/                        ← (خودکار)
├── 📁 dist/                         ← (خودکار) EXE
├── 📁 logs/                         ← (خودکار) لاگ‌ها
└── 📁 __pycache__/                  ← (خودکار)
```

---

## 4. جریان داده

### جریان کلی

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         gui/main_window.py          │
│      (MotorApp - پنجره اصلی)         │
└──────┬──────────────────────────────┘
       │
       ├──────────────────┬──────────────────┐
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Valves     │    │     AI      │    │   Export    │
│   Panel     │    │  Assistant  │    │   Menu      │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ core/       │    │ ai/         │    │ export/     │
│ - models    │    │ - query     │    │ - pdf       │
│ - database  │    │ - learning  │    │ - word      │
│ - calc      │    │ - proposal  │    │ - excel     │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┴──────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  SQLite DB      │
                 │  (D:\BMS...)    │
                 └─────────────────┘
```

### جریان یک درخواست نمونه

**مثال: کاربر یک Valve اضافه می‌کند:**

```
1. User → gui/valves/valves_panel.py
2. کلیک "Add Valve" → gui/valves/valve_dialog.py
3. کاربر فرم را پر می‌کند (ValveType=Steam)
4. _on_field_change() → _recalculate()
5. _recalculate() → core/valve_calculator.enrich_valve()
6. enrich_valve() → core/steam_kv_calculator.calculate_kv_steam()
7. نتیجه برمی‌گردد → valve.KvsCalc
8. UI به‌روز می‌شود
9. کاربر Save می‌زند → on_ok()
10. on_ok() → app._save_project()
11. app._save_project() → core/database.save_project()
12. Save در SQLite
```

---

## 5. فایل‌های کلیدی

### 🔴 حیاتی (Core)

| فایل | کاربرد | پیچیدگی |
|------|--------|---------|
| `core/models.py` | مدل‌ها | 🔴 بالا |
| `core/database.py` | Database | 🔴 بالا |
| `core/constants.py` | ثابت‌ها | 🟡 متوسط |
| `utils/paths.py` | مسیرها | 🟡 متوسط |
| `utils/logger.py` | لاگ | 🟡 متوسط |

### 🟡 مهم (AI + UI)

| فایل | کاربرد | پیچیدگی |
|------|--------|---------|
| `ai/learning_engine.py` | یادگیری | 🔴 بالا |
| `ai/local_proposal_generator.py` | پروپوزال | 🟡 متوسط |
| `ai/query_templates.py` | Intent | 🟡 متوسط |
| `gui/valves/valve_dialog.py` | UI Valve | 🟡 متوسط |
| `gui/ai_settings_dialog.py` | UI Settings | 🟢 پایین |

### 🟢 کمکی

| فایل | کاربرد |
|------|--------|
| `utils/config_manager.py` | Config |
| `utils/pdf_helpers.py` | PDF فارسی |
| `core/attachments.py` | ضمیمه‌ها |
| `core/steam_kv_calculator.py` | Kv بخار |

### 🔧 Export

| فایل | خروجی |
|------|--------|
| `export/word_proposal_exporter.py` | `.docx` |
| `export/pdf_exporter.py` | `.pdf` (IO List) |
| `export/pdf_proposal_exporter.py` | `.pdf` (Proposal) |
| `export/excel_exporter.py` | `.xlsx` |

---

## 6. مسیرهای Runtime

### نمای کلی

```
┌──────────────────────────────────────────────────────────────┐
│  Data Directory (اولویت‌بندی)                                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Environment Variable: CSM_DATA_DIR                       │
│  2. app_config.json → data_dir                               │
│  3. D:\BMS Projects\IO_List_Generator  (اگر D: موجود)        │
│  4. %APPDATA%\ControlSystemManager  (EXE)                    │
│  5. <project_root>/data  (Development)                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│  ساختار پوشه‌ها در Data Directory                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  D:\BMS Projects\IO_List_Generator\                          │
│  ├── IO_List_Generator.db          ← دیتابیس اصلی            │
│  ├── 📁 Backups\                    ← پشتیبان‌ها              │
│  │   ├── IO_List_Generator_Backup_*.db                       │
│  │   └── pre_migration_*.db                                  │
│  ├── 📁 config\                     ← تنظیمات                 │
│  │   └── config.json                ← API Key                │
│  ├── 📁 logs\                       ← لاگ‌ها                  │
│  │   ├── control_system.log                                  │
│  │   └── control_system_error.log                            │
│  ├── 📁 Attachments\                ← ضمیمه‌ها                │
│  │   └── {ProjectName}\                                       │
│  ├── 📁 Project_Backups\            ← بکاپ پروژه‌ها          │
│  └── 📁 output\                     ← خروجی‌های موقت          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### API توابع `utils/paths.py`

```python
# ===== منابع فقط-خواندنی =====
get_bundle_root()         # ریشه منابع
get_resource_path(*parts) # مسیر منابع

# ===== داده‌های کاربر =====
get_user_data_dir()       # پوشه داده
get_database_path()       # مسیر دیتابیس
get_logs_dir()            # پوشه لاگ
get_config_dir()          # پوشه config
get_output_dir()          # پوشه output
get_backups_dir()         # پوشه بکاپ
get_project_backups_dir() # پوشه بکاپ پروژه
get_attachments_dir()     # پوشه ضمیمه‌ها

# ===== اطلاعات =====
get_data_dir_info()       # اطلاعات کامل
is_frozen()               # آیا EXE است؟
get_app_root()            # ریشه برنامه
```

### نمونه استفاده

```python
from utils.paths import get_database_path, get_logs_dir

db_path = get_database_path()
logger.info(f"Database: {db_path}")

log_dir = get_logs_dir()
print(f"Logs at: {log_dir}")
```

---

## 7. پایگاه داده

### ساختار جداول

```
┌─────────────────────────────────────────────────────────────┐
│                       SQLite Database                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📋 projects                ← پروژه‌ها                      │
│  📋 revisions               ← رویژن‌ها                       │
│  📋 sections                ← سکشن‌ها                        │
│  📋 devices                 ← دستگاه‌ها (JSON)               │
│  📋 valves                  ← شیرها (JSON)                   │
│  📋 attachments             ← ضمیمه‌ها                       │
│  📋 component_labels        ← برچسب‌های کامپوننت             │
│  📋 templates               ← قالب‌ها                        │
│  📋 custom_components       ← کامپوننت سفارشی                │
│  📋 app_state               ← وضعیت (last active)           │
│  📋 learning_smart_tags     ← یادگیری SmartTag              │
│  📋 learning_models         ← یادگیری مدل                   │
│  📋 schema_migrations       ← نسخه Schema                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### روابط (Relationships)

```
projects (1) ───< (∞) revisions
                      │
                      ├──< sections
                      │       │
                      │       ├──< devices
                      │       └──< valves
                      │
                      └──< attachments
                      
projects (1) ───< (∞) component_labels
```

### اطلاعات کلیدی

| جدول | کلید اصلی | Foreign Keys | Index |
|------|-----------|--------------|-------|
| `projects` | `name` (TEXT) | - | PK |
| `revisions` | `id` | `project_name` | `idx_revisions_current` (partial unique) |
| `sections` | `id` | `project_name` | - |
| `devices` | `id` | `project_name` | - |
| `valves` | `id` | `project_name` | - |
| `attachments` | `id` | `project_name` | UNIQUE(project_name, file_name) |
| `schema_migrations` | `version` | - | PK |

### Partial Unique Index

```sql
-- فقط یک revision می‌تواند is_current=1 باشد
CREATE UNIQUE INDEX idx_revisions_current
ON revisions(project_name)
WHERE is_current = 1;
```

### مدل‌های داده

**`core/models.py`:**

```python
class Project:
    name: str
    description: str
    client_name: str
    ...
    revisions: List[Revision]
    current_revision_name: str

class Revision:
    name: str
    description: str
    sections: List[ProjectSection]

class ProjectSection:
    name: str
    description: str
    order_index: int
    devices: List[Motor]
    valves: List[Valve]

class Motor:
    Name: str
    Description: str
    SmartTag: str
    PU: int  # و سایر کامپوننت‌ها
    DI: int
    DO: int
    AI: int
    AO: int
    UseIndexNaming: bool

class Valve:
    Equipment: str
    ValveType: str  # 'PICV', '3 Way', 'Steam'
    Flow: float
    Unit: str
    PressureDrop: float
    SteamPressure: float
    ...
```

---

## 8. سیستم لاگ

### معماری

```
┌──────────────────────────────────────────────────────────────┐
│                    Root Logger                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ├── 📁 FileHandler → control_system.log                    │
│  ├── 📁 ErrorHandler → control_system_error.log             │
│  └── 🖥️ ConsoleHandler → stdout                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                          ▲
                          │ propagate=True
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   control_system    core.database    gui.main_window
   core.attachments  ai.learning      export.pdf
```

### استفاده

```python
# در هر ماژول:
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
logger.critical("Critical message")
```

### سطح‌های لاگ

| سطح | کاربرد |
|-----|--------|
| **DEBUG** | اطلاعات دقیق برای دیباگ |
| **INFO** | اطلاعات عمومی (پیش‌فرض) |
| **WARNING** | هشدارها |
| **ERROR** | خطاها |
| **CRITICAL** | خطاهای بحرانی |

### فایل‌های لاگ

| فایل | محتوا | Rotate |
|------|--------|---------|
| `control_system.log` | همه لاگ‌ها | 10 MB × 5 |
| `control_system_error.log` | فقط Error+ | 10 MB × 5 |

### تنظیم سطح لاگ

```python
from utils.logger import set_global_log_level

set_global_log_level('DEBUG')  # یا 'INFO', 'WARNING'
```

---

## 9. Backup & Restore

### انواع Backup

| نوع | مسیر | زمان ساخت | تعداد نگهداری |
|-----|------|-----------|---------------|
| **Auto** | `Backups/IO_List_Generator_Backup_*.db` | هر **۶ ساعت** (اولین اجرا بعد از این بازه) | ۳۰ نسخه آخر |
| **Pre-Migration** | `Backups/pre_migration_*.db` | **فقط وقتی** `current_schema < CURRENT_SCHEMA_VERSION` | همه (بی‌نهایت) |
| **Pre-Restore** | `Backups/pre_restore_*.db` | قبل Restore | همه |
| **Project** | `Project_Backups/` | دستی | همه |
| **Full** (ZIP) | — | دستی | همه |

### 🆕 Auto Backup با Interval

برای جلوگیری از تولید بی‌رویه فایل، Auto Backup فقط **هر 4 ساعت** یک بار ساخته می‌شود:

```python
def _create_auto_backup(self, min_interval_hours: int = 6):
    # چک آخرین بکاپ
    existing = sorted(
        Path(backup_dir).glob("IO_List_Generator_Backup_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if existing:
        last_mtime = datetime.fromtimestamp(existing[0].stat().st_mtime)
        elapsed = datetime.now() - last_mtime
        if elapsed.total_seconds() < min_interval_hours * 3600:
            logger.info(f"⏭️ Skipping auto-backup (last was {elapsed...:.1f}h ago)")
            return None
    
    # ... ساخت بکاپ
### Backup اتمیک

**استفاده از `sqlite3.Connection.backup()`:**

```python
src = sqlite3.connect(source_db)
dst = sqlite3.connect(backup_path)

with dst:
    src.backup(dst)

src.close()
dst.close()
```

**مزیت:** Atomic + Consistency

### Restore امن

**مراحل:**

```
1. Validate: فایل موجود است؟
2. Validate: SQLite integrity_check
3. Safety Backup: کپی از DB فعلی
4. Copy to temp: در همان درایو
5. os.replace() — اتمیک
6. Reopen DB
```

### Safe ZIP Extraction

**جلوگیری از Zip Slip:**

```python
def _safe_extract_zip(zip_path, extract_to):
    extract_to_resolved = Path(extract_to).resolve()
    
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            member_path = (extract_to_resolved / member).resolve()
            
            # چک: باید داخل extract_to باشد
            try:
                member_path.relative_to(extract_to_resolved)
            except ValueError:
                raise ValueError(f"Zip Slip: {member}")
        
        zf.extractall(extract_to)
```

### نگهداری Backup

- **۳۰ نسخه آخر** از Auto Backup نگه داشته می‌شود
- نسخه‌های قدیمی **خودکار پاک** می‌شوند

---

## 10. Migration & Schema Versioning

### Schema Versioning

**جدول `schema_migrations`:**

| version | applied_at | description |
|---------|-----------|-------------|
| 1 | `2026-09-27T...` | Initial schema with revisions, valves, attachments |
| 2 | (آینده) | ... |

**ثابت در `core/database.py`:**

```python
CURRENT_SCHEMA_VERSION = 1
```

**⚠️ هر بار تغییر ساختاری، این عدد را +۱ کنید.**
### Migration Flow — نسخه بهینه‌شده

┌─────────────────────────────────────────────────────────────┐
│ _init_db() │
├─────────────────────────────────────────────────────────────┤
│ │
│ 1. جدول projects وجود دارد؟ │
│ │ │
│ ├── خیر (نصب اول) → │
│ │ _create_all_tables() │
│ │ _ensure_schema_version_table() │
│ │ _record_schema_version(CURRENT) │
│ │ RETURN │
│ │ │
│ └── بله → │
│ current = _get_current_schema_version() │
│ │ │
│ ├── current >= CURRENT → RETURN (سریع!) ✅ │
│ │ هیچ بکاپی گرفته نمی‌شود │
│ │ هیچ migration ای اجرا نمی‌شود │
│ │ │
│ └── current < CURRENT → │
│ 1. _create_pre_migration_backup() (فقط الان) │
│ 2. _migrate_database() │
│ 3. _check_and_apply_migrations() │
│ │
└─────────────────────────────────────────────────────────────┘

### افزودن Migration جدید

**مثال: افزودن جدول جدید در نسخه 2:**

```python
# 1. در core/database.py، ثابت را افزایش دهید
CURRENT_SCHEMA_VERSION = 2

# 2. در _check_and_apply_migrations، بلاک جدید اضافه کنید:
if current_version < 2:
    logger.info("🔄 Applying migration v1 → v2...")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS new_table (
            id INTEGER PRIMARY KEY,
            ...
        )
    ''')
    
    self._record_schema_version(cursor, 2, "Added new_table")
```

---

## 11. AI System

### معماری AI

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Assistant                             │
│                (ai/ai_assistant.py)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┐
        ▼             ▼             ▼             ▼
┌─────────────┐ ┌───────────┐ ┌──────────┐ ┌────────────┐
│ DeepSeek    │ │ Query     │ │ Learning │ │ Local      │
│ Client      │ │ Engine    │ │ Engine   │ │ Proposal   │
└──────┬──────┘ └─────┬─────┘ └────┬─────┘ └─────┬──────┘
       │              │            │             │
       │              │            │             │
       ▼              ▼            ▼             ▼
┌─────────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐
│ OpenAI API  │ │ Templates │ │ Patterns │ │ Sections │
│ (CodeCraft) │ │ (Intent)  │ │ (DB)     │ │ Images   │
└─────────────┘ └───────────┘ └──────────┘ └──────────┘
```

### DeepSeek Client

**مسیر:** `ai/deepseek_client.py`

**مسئول:**
- اتصال به CodeCraft API
- مدیریت API Key
- تولید پروپوزال

**استفاده:**

```python
from ai.deepseek_client import DeepSeekClient

client = DeepSeekClient()

if client.is_configured():
    response = client.chat("سلام")
    print(response)
```

### Query Engine

**مسیر:** `ai/project_query_engine.py`

**Intent های پشتیبانی‌شده:**

| Intent | مثال |
|--------|------|
| `count_projects` | «چند پروژه دارم؟» |
| `count_components` | «چند PU در پروژه ربانی دارم؟» |
| `list_sections` | «سکشن‌های پروژه ربانی چیه؟» |
| `list_devices` | «دستگاه‌های سکشن AHU-1 چیه؟» |
| `project_summary` | «خلاصه پروژه ربانی» |
| `compare_projects` | «مقایسه ربانی و صادرات» |
| `total_io` | «کل I/O پروژه ربانی» |
| `list_projects` | «چه پروژه‌هایی دارم؟» |

### Learning Engine

**مسیر:** `ai/learning_engine.py`

**جداول:**

| جدول | کاربرد |
|------|--------|
| `learning_patterns` | الگوهای کامپوننت |
| `learning_project_analysis` | تحلیل پروژه‌ها |
| `learning_equipment_patterns` | الگوهای تجهیزات |

**استفاده:**

```python
engine.learn_from_project(project)
analysis = engine.analyze_project(project)
predictions = engine.predict_component_needs(devices)
```

### Local Proposal Generator

**مسیر:** `ai/local_proposal_generator.py`

**منابع:**
- دیتابیس (سکشن‌ها + دستگاه‌ها)
- `ai/proposal_template.txt`
- `ai/proposal_images/`
- `ai/proposal_templates/`

**استفاده:**

```python
gen = LocalProposalGenerator(db, app)
proposal = gen.generate(project, revision_name)
```

---

## 12. Valve Calculations

### انواع شیر

| نوع | استاندارد | فرمول |
|-----|-----------|--------|
| **PICV** | Danfoss ABQM | جدول lookup |
| **3-Way** | Danfoss VRG 3 | `Kv = Q / √(Δp/SG)` |
| **Steam** | IEC 60534-2-1 | `Kv = ṁ / (31.6·Y·√(x_s·P₁·ρ₁))` |

### Steam Kv Calculator

**مسیر:** `core/steam_kv_calculator.py`

**فرمول IEC 60534-2-1:**

```
Kv = ṁ / (31.6 × Y × √(x_s × P₁ × ρ₁))
```

**که:**

| پارامتر | توضیح | واحد |
|---------|-------|------|
| `ṁ` | دبی جرمی | kg/h |
| `P₁` | فشار مطلق ورودی | bar abs |
| `ρ₁` | چگالی بخار | kg/m³ |
| `x` | `ΔP / P₁` | — |
| `x_T` | ضریب هندسی شیر | — |
| `x_critical` | `F_γ × x_T` | — |
| `Y` | ضریب انبساط | — |

**برای VFS 2 Danfoss:**

```python
X_T_VFS2_STEAM = 0.43     # → x_critical ≈ 0.40
```

**جدول خواص بخار (23 نقطه):**

```python
STEAM_PROPERTIES = [
    (0.5, 81.3, 0.321),   # (bar, °C, kg/m³)
    (1.0, 99.6, 0.590),
    ...
]
```

### VFS 2 Valve (Danfoss)

**مسیر:** `core/valve_constants.py`

**جدول VFS 2:**

| kvs (m³/h) | DN |
|------------|-----|
| 0.40 | 15 |
| 0.63 | 15 |
| 1.00 | 15 |
| 1.60 | 15 |
| 2.50 | 15 |
| 4.00 | 20 |
| ... | ... |
| 145 | 100 |

**مشخصات VFS 2:**

| ویژگی | مقدار |
|--------|--------|
| **PN** | 25 bar |
| **T max** | 200°C |
| **Body** | Ductile Iron |
| **Connection** | Flange ISO 7005-2 |
| **ΔP max** | 6 bar |

### جدول VRG 3 (3-Way)

**Kv → DN:**

| Kv | DN |
|----|-----|
| 4 | 15 |
| 6.3 | 20 |
| ... | ... |
| 1350 | 300 |

---

## 13. PDF & Persian Support

### چالش: RTL در reportlab

reportlab از **RTL** پشتیبانی نمی‌کند → متن فارسی **معکوس** نمایش داده می‌شود.

### راه‌حل: arabic-reshaper + python-bidi

**مسیر:** `utils/pdf_helpers.py`

**توابع:**

```python
from utils.pdf_helpers import fa, fa_paragraph, fa_mixed, fa_bold

text = fa("سلام")               # reshape + RTL
text = fa_paragraph("پروژه")    # برای Paragraph
text = fa_mixed("پروژه ABC")    # ترکیبی
text = fa_bold("مهم")           # bold
```

### Pipeline

```
متن فارسی
    │
    ▼
arabic_reshaper.reshape()    ← چسباندن حروف
    │
    ▼
bidi.algorithm.get_display() ← RTL
    │
    ▼
Paragraph(text, style)
    │
    ▼
PDF با متن درست
```

### استفاده در PDF Exporter

```python
from utils.pdf_helpers import fa

# در ساخت ردیف جدول:
row = [
    str(idx),
    _fa_safe(cable['device_name']),   # ← reshape اگر فارسی است
    cable['tag'],                      # ← Cable Tag خالص ASCII
    ...
]
```

### Cable Tag Sanitization

**مسئله:** اگر نام دستگاه فارسی باشد، Cable Tag به‌هم‌ریخته می‌شود.

**راه‌حل:** فقط کاراکترهای ASCII:

```python
@staticmethod
def _sanitize_cable_tag(text) -> str:
    if not text:
        return ''
    
    result = ''.join(
        c for c in str(text)
        if ord(c) < 128 and (c.isalnum() or c in '-_.')
    )
    
    return result or 'TAG'
```

### فونت‌های فارسی

| فونت | کاربرد |
|-------|--------|
| `tahoma.ttf` | متن عمومی |
| `BNazanin.ttf` | متن فارسی |
| `BLotus.ttf` | تیتر |
| `BMitra.ttf` | متن |

**ثبت فونت در reportlab:**

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('Persian', str(font_path)))
```

---

## 14. راهنمای توسعه

### راه‌اندازی محیط

```powershell
# 1. کلون پروژه
cd "D:\01-Projects\Control System Design\control_system_manager"

# 2. نصب پکیج‌ها
python -m pip install -r requirements.txt
python -m pip install arabic-reshaper python-bidi

# 3. تست اولیه
python test_full_system.py

# 4. اجرا
python main.py
```

### ساختار workflow

```
1. کد را تغییر بده
2. تست کن: python main.py
3. اگر خطا بود: logs/control_system_error.log را ببین
4. اگر OK بود: 
   - Build: python -m PyInstaller --clean main.spec
   - تست EXE: .\dist\ControlSystemManager.exe
```

### افزودن قابلیت جدید

**مثال: افزودن کامپوننت جدید:**

```
1. core/constants.py
   COMPONENT_LABELS['NEW'] = {'fa': '...', 'en': '...'}
   IO_CALCULATION['NEW'] = {'DI': 0, 'DO': 1, 'AI': 0, 'AO': 0}
   
2. core/models.py
   Motor.NUMERIC_FIELDS.append('NEW')
   
3. تست: python -c "from core.constants import COMPONENT_LABELS; print(COMPONENT_LABELS['NEW'])"
```

**مثال: افزودن سکشن به پروپوزال:**

```
1. ai/proposal_images/new.png  ← تصویر
2. ai/proposal_templates/new.txt  ← قالب
3. ai/local_proposal_generator.py
   section_images['new'] = 'new.png'
4. export/word_proposal_exporter.py
   SECTION_IMAGES['new'] = 'new.png'
   SECTION_KEYWORDS['new'] = ['keyword']
```

### اشکال‌زدایی

**در Development:**

```python
# فایل logs/control_system_error.log را ببین
# یا در کنسول با set_global_log_level('DEBUG')
from utils.logger import set_global_log_level
set_global_log_level('DEBUG')
```

**در EXE:**

```
1. فایل D:\BMS Projects\IO_List_Generator\logs\control_system_error.log
2. از cmd اجرا کن:
   .\ControlSystemManager.exe 2>&1 | Tee-Object error.txt
```

---

## 15. ۵ قانون طلایی

### قانون ۱: جدا نگه داشتن لایه‌ها

```
✅ core/ → فقط sqlite3, dataclasses
✅ ai/ → core + openai
✅ gui/ → core + ai + tkinter
✅ export/ → core + reportlab + docx
✅ utils/ → استاندارد

❌ core/ → gui/  (هرگز!)
❌ core/ → ai/
❌ gui/ → sqlite3  (مستقیم)
```

### قانون ۲: استفاده از logger

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Message")
logger.error("Error", exc_info=True)
```

**نه:**
```python
print("...")  # ❌
```

### قانون ۳: Exception Handling

```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Error: {e}", exc_info=True)
    return default_value
except Exception as e:
    logger.error(f"Unexpected: {e}", exc_info=True)
    return default_value
```

### قانون ۴: Type Hints

```python
from typing import Optional, List, Dict, Any

def func(
    a: int,
    b: Optional[str] = None,
) -> List[Dict[str, Any]]:
    ...
```

### قانون ۵: تست قبل از Build

```powershell
# 1. تست
python main.py

# 2. پاک کردن build قبلی
Remove-Item -Recurse -Force build, dist

# 3. Build
python -m PyInstaller --clean main.spec

# 4. تست EXE
.\dist\ControlSystemManager.exe
```

---

## 16. چک‌لیست تغییرات

### قبل از هر تغییر:

- [ ] پشتیبان گرفتن
- [ ] در Git commit (اگر استفاده می‌کنید)
- [ ] فایل `control_system_error.log` را ببینید (خطاهای قبلی)

### برای تغییر منطق (core):

- [ ] `core/models.py` → تغییر مدل
- [ ] `core/database.py` → Migration
- [ ] `core/constants.py` → کامپوننت
- [ ] `core/validators.py` → اعتبارسنجی
- [ ] تست کنید

### برای تغییر AI:

- [ ] `ai/ai_assistant.py` → دستور جدید
- [ ] `ai/query_templates.py` → Intent جدید
- [ ] `ai/learning_engine.py` → الگوریتم

### برای تغییر UI:

- [ ] `gui/main_window.py` → منو
- [ ] `gui/dialogs.py` → دیالوگ
- [ ] `gui/theme/colors.py` → رنگ

### برای تغییر Export:

- [ ] `export/new_exporter.py` → ساخت
- [ ] `gui/` → دکمه
- [ ] `main.spec` → اگر کتابخانه جدید

### قبل از Build:

- [ ] همه تست‌ها اجرا شد
- [ ] `main.spec` به‌روز است
- [ ] `requirements.txt` به‌روز است
- [ ] `ARCHITECTURE.md` به‌روز است (این فایل)

### بعد از Build:

- [ ] EXE در `dist/` ساخته شد
- [ ] حجم EXE: ~۶۵-۷۲ MB
- [ ] EXE باز می‌شود
- [ ] ۸ پروژه بارگذاری می‌شوند
- [ ] PDF فارسی کار می‌کند
- [ ] AI Assistant کار می‌کند
- [ ] Attachments کار می‌کنند

---

## 📚 منابع

| موضوع | مرجع |
|--------|------|
| **Python** | https://docs.python.org/3/ |
| **Tkinter** | https://docs.python.org/3/library/tkinter.html |
| **PyInstaller** | https://pyinstaller.org/ |
| **python-docx** | https://python-docx.readthedocs.io/ |
| **reportlab** | https://docs.reportlab.com/ |
| **openpyxl** | https://openpyxl.readthedocs.io/ |
| **IEC 60534** | https://webstore.iec.ch/publication/26624 |
| **Danfoss VFS 2** | https://www.danfoss.com/ |

---

## 📝 تاریخچه تغییرات

| نسخه | تاریخ | تغییرات |
|------|-------|---------|
| 1.0 | 1405/07/06 | نسخه اولیه — همه قابلیت‌ها |

---

**نویسنده:** Mr. Keshtkar  
**شرکت:** Vahhaj Sanat Energy Co.  
**لایسنس:** Private

---

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║            ✅ پایان مستندات معماری                           ║
║                                                              ║
║                  Control System Manager v1.0                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```