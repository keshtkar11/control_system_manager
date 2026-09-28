# 🏗️ Control System Manager

> نرم‌افزار دسکتاپ جامع برای طراحی، مدیریت و مستندسازی سیستم‌های کنترل BMS (Building Management System)

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green.svg)](https://docs.python.org/3/library/tkinter.html)
[![SQLite](https://img.shields.io/badge/Database-SQLite-blue.svg)](https://www.sqlite.org/)
[![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)]()
[![Status](https://img.shields.io/badge/Status-Ready%20for%20Delivery-brightgreen.svg)]()

---

## 📖 درباره پروژه

**Control System Manager** یک برنامه دسکتاپ حرفه‌ای برای مهندسین کنترل و فعالان حوزه BMS است که فرآیند طراحی، محاسبه، مستندسازی و تولید پروپوزال سیستم‌های کنترل را به طور کامل پوشش می‌دهد.

این نرم‌افزار با هدف جایگزینی روش‌های دستی و پراکنده در مدیریت پروژه‌های BMS طراحی شده و تمام چرخه کاری — از ورود اطلاعات تجهیزات تا تولید خروجی‌های نهایی PDF/Word/Excel — را در یک محیط یکپارچه فراهم می‌کند.

### 🎯 چرا Control System Manager؟

- ⚡ **صرفه‌جویی در زمان:** تولید خودکار IO List، پروپوزال و گزارش‌ها
- 🎯 **کاهش خطا:** محاسبات دقیق شیرها بر اساس استانداردهای بین‌المللی
- 🤖 **هوش مصنوعی یکپارچه:** دستیار هوشمند برای تحلیل پروژه و تولید پروپوزال
- 🌐 **پشتیبانی کامل فارسی:** خروجی PDF با رعایت کامل RTL
- 📦 **بدون نیاز به نصب:** خروجی EXE مستقل

---

## ✨ ویژگی‌های کلیدی

### 📋 مدیریت پروژه
- ایجاد، ویرایش و حذف پروژه‌ها با **Revisions** (نسخه‌بندی)
- مدیریت سکشن‌ها و دستگاه‌های هر پروژه
- جستجوی سریع و فیلتر پیشرفته
- سیستم Undo/Redo کامل

### ⚙️ مدیریت دستگاه‌ها
- محاسبه خودکار I/O (PU, DI, DO, AI, AO)
- پشتیبانی از برچسب‌های سفارشی (Smart Tags)
- اعتبارسنجی هوشمند داده‌ها
- مدیریت کامپوننت‌های سفارشی

### 🔧 محاسبات شیر (Valve)
- **PICV** — استاندارد Danfoss ABQM
- **3-Way** — استاندارد Danfoss VRG 3
- **Steam** — استاندارد IEC 60534-2-1
- جداول مرجع VFS 2 و VRG 3
- پیشنهاد خودکار سایز شیر بر اساس Kv

### 🤖 دستیار هوش مصنوعی
- چت هوشمند با AI (OpenAI SDK / CodeCraft API)
- پاسخ به سؤالات پروژه (تعداد کامپوننت، خلاصه پروژه، مقایسه)
- تولید خودکار **پروپوزال** بر اساس داده‌های پروژه
- **Learning Engine** — یادگیری از پروژه‌های قبلی
- وارد کردن پروپوزال‌های Word موجود

### 📤 خروجی‌های حرفه‌ای
- 📄 **Word** — پروپوزال کامل با تصاویر
- 📄 **PDF** — IO List و پروپوزال (با پشتیبانی کامل فارسی RTL)
- 📊 **Excel** — IO List، لیست شیرها با استایل حرفه‌ای

### 🗂️ ضمیمه‌ها
- مدیریت فایل‌های ضمیمه هر پروژه
- **Recycle Bin** داخلی (بازگردانی آسان)
- پشتیبانی از انواع فرمت‌ها

### 🛡️ امنیت و پشتیبان‌گیری
- **Backup خودکار** هر ۶ ساعت
- **Backup اتمیک** بدون ریسک کرش
- **Migration** خودکار دیتابیس
- **Safe ZIP Extraction** (محافظت از Zip Slip)

---

## 🛠️ تکنولوژی‌ها

| دسته | تکنولوژی |
|------|-----------|
| **زبان** | Python 3.14 |
| **رابط کاربری** | Tkinter |
| **دیتابیس** | SQLite |
| **هوش مصنوعی** | OpenAI SDK (CodeCraft API) |
| **PDF** | reportlab + arabic-reshaper + python-bidi |
| **Word** | python-docx |
| **Excel** | openpyxl |
| **تصاویر** | Pillow (PIL) |
| **Recycle Bin** | send2trash |
| **Build** | PyInstaller |

---

## 📦 نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.10 یا بالاتر (توصیه: 3.14)
- ویندوز 10/11

### نصب از منبع

```bash
# 1. کلون پروژه
git clone https://github.com/keshtkar11/control_system_manager.git
cd control_system_manager

# 2. نصب پکیج‌ها
python -m pip install -r requirements.txt

# 3. اجرا
python main.py