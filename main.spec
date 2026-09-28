# -*- mode: python ; coding: utf-8 -*-

r"""
PyInstaller Spec File — Control System Manager
Version 2.2 — FIXED + Persian PDF

- Python 3.14
- One-File EXE
- بدون UPX
- بدون Console
- ✅ Config/Database/Logs در D:\ یا %APPDATA%
- ✅ منابع فقط-خواندنی در _MEIPASS
- ✅ tkinter + tcl/tk کامل
- ✅ همه فایل‌های AI + Templates
- ✅ arabic-reshaper + python-bidi برای PDF فارسی
"""

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, collect_data_files


# ================================================================
# PROJECT ROOT
# ================================================================

PROJECT_ROOT = Path(SPECPATH).resolve()

print("\n" + "=" * 70)
print("🔨 PyInstaller Build Configuration — v2.2")
print("=" * 70)
print(f"📁 Project Root: {PROJECT_ROOT}")
print("=" * 70 + "\n")


# ================================================================
# DATA FILES
# ================================================================

datas = []


# ================================================================
# 0. TKINTER + TCL/TK
# ================================================================

print("📦 [0/9] Collecting tkinter + tcl/tk...")

try:
    import tkinter
    tkinter_dir = Path(tkinter.__file__).parent
    datas.append((str(tkinter_dir), "tkinter"))
    print(f"   ✅ tkinter/ ({tkinter_dir})")
except Exception as e:
    print(f"   ❌ tkinter failed: {e}")

try:
    import _tkinter
    _tkinter_path = Path(_tkinter.__file__).parent
    print(f"   ℹ️  _tkinter: {_tkinter_path}")
except Exception as e:
    print(f"   ⚠️  _tkinter: {e}")

try:
    python_root = Path(sys.base_prefix)
    candidate_tcl_dirs = [
        python_root / "tcl",
        python_root / "Lib" / "tkinter",
        python_root / "DLLs",
    ]
    for tcl_dir in candidate_tcl_dirs:
        if tcl_dir.exists():
            if tcl_dir.name == "tcl":
                datas.append((str(tcl_dir), "tcl"))
                print(f"   ✅ tcl/ from {tcl_dir}")
            elif tcl_dir.name == "DLLs":
                for dll in tcl_dir.glob("tcl*"):
                    datas.append((str(dll), "."))
                for dll in tcl_dir.glob("tk*"):
                    datas.append((str(dll), "."))
                print(f"   ✅ DLLs/tcl*.dll + tk*.dll")
except Exception as e:
    print(f"   ⚠️  tcl/tk dirs: {e}")


# ================================================================
# 1. AI FILES
# ================================================================

print("📦 [1/9] Collecting AI files...")

AI_DIR = PROJECT_ROOT / "ai"

for txt_file in ["proposal_template.txt", "proposal_instructions.txt"]:
    src = AI_DIR / txt_file
    if src.exists() and src.is_file():
        datas.append((str(src), "ai"))
        print(f"   ✅ {txt_file}")

AI_IMAGES_DIR = AI_DIR / "proposal_images"
if AI_IMAGES_DIR.exists() and AI_IMAGES_DIR.is_dir():
    image_count = 0
    for img_file in AI_IMAGES_DIR.glob("*"):
        if img_file.is_file():
            datas.append((str(img_file), "ai/proposal_images"))
            image_count += 1
    print(f"   ✅ proposal_images/ ({image_count} files)")

AI_TEMPLATES_DIR = AI_DIR / "proposal_templates"
if AI_TEMPLATES_DIR.exists() and AI_TEMPLATES_DIR.is_dir():
    template_count = 0
    for tpl_file in AI_TEMPLATES_DIR.glob("*"):
        if tpl_file.is_file() and tpl_file.suffix in ['.txt', '.md']:
            datas.append((str(tpl_file), "ai/proposal_templates"))
            template_count += 1
    print(f"   ✅ proposal_templates/ ({template_count} files)")


# ================================================================
# 2. RESOURCES — Icons
# ================================================================

print("📦 [2/9] Collecting resources/icons...")

RESOURCES_DIR = PROJECT_ROOT / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"

if ICONS_DIR.exists() and ICONS_DIR.is_dir():
    icon_count = 0
    for icon_file in ICONS_DIR.glob("*"):
        if icon_file.is_file():
            datas.append((str(icon_file), "resources/icons"))
            icon_count += 1
    print(f"   ✅ icons/ ({icon_count} files)")


# ================================================================
# 3. RESOURCES — Fonts
# ================================================================

print("📦 [3/9] Collecting resources/fonts...")

FONTS_DIR = RESOURCES_DIR / "fonts"

ESSENTIAL_FONTS = [
    "BNazanin.ttf", "BLotus.ttf", "BMitra.ttf",
    "tahoma.ttf", "arial.ttf",
]

if FONTS_DIR.exists() and FONTS_DIR.is_dir():
    available_fonts = {
        f.name.lower(): f
        for f in FONTS_DIR.glob("*.ttf")
        if f.is_file()
    }
    font_count = 0
    for font_name in ESSENTIAL_FONTS:
        lower_name = font_name.lower()
        if lower_name in available_fonts:
            font_path = available_fonts[lower_name]
            datas.append((str(font_path), "resources/fonts"))
            font_count += 1
    print(f"   ✅ fonts/ ({font_count} fonts)")

    ESSENTIAL_DIR = FONTS_DIR / "essential"
    if ESSENTIAL_DIR.exists():
        for font_file in ESSENTIAL_DIR.glob("*.ttf"):
            datas.append((str(font_file), "resources/fonts/essential"))
        print(f"   ✅ fonts/essential/")


# ================================================================
# 4. RESOURCES — Translations
# ================================================================

print("📦 [4/9] Collecting translations...")

TRANSLATIONS_DIR = RESOURCES_DIR / "translations"
if TRANSLATIONS_DIR.exists() and TRANSLATIONS_DIR.is_dir():
    trans_count = 0
    for trans_file in TRANSLATIONS_DIR.glob("*"):
        if trans_file.is_file():
            datas.append((str(trans_file), "resources/translations"))
            trans_count += 1
    if trans_count:
        print(f"   ✅ translations/ ({trans_count} files)")
    else:
        print(f"   ℹ️  translations/ empty")


# ================================================================
# 5. GUI STYLES
# ================================================================

print("📦 [5/9] Collecting gui/styles...")

GUI_STYLES_DIR = PROJECT_ROOT / "gui" / "styles"
if GUI_STYLES_DIR.exists() and GUI_STYLES_DIR.is_dir():
    style_count = 0
    for style_file in GUI_STYLES_DIR.glob("*"):
        if style_file.is_file():
            datas.append((str(style_file), "gui/styles"))
            style_count += 1
    if style_count:
        print(f"   ✅ gui/styles/ ({style_count} files)")
    else:
        print(f"   ℹ️  gui/styles/ empty")


# ================================================================
# 6. ROOT FILES
# ================================================================

print("📦 [6/9] Collecting root files...")

for fname in ["Help.txt", "README.md", "requirements.txt"]:
    fpath = PROJECT_ROOT / fname
    if fpath.exists() and fpath.is_file():
        datas.append((str(fpath), "."))
        print(f"   ✅ {fname}")


# ================================================================
# 7. DATABASE SEED
# ================================================================

print("📦 [7/9] Collecting database seed...")

DATA_DIR = PROJECT_ROOT / "data"
if DATA_DIR.exists() and DATA_DIR.is_dir():
    for db_file in DATA_DIR.glob("*.db"):
        if db_file.is_file():
            datas.append((str(db_file), "data"))
            print(f"   ✅ {db_file.name} (seed)")


# ================================================================
# 8. PACKAGE DATA FILES
# ================================================================

print("📦 [8/9] Collecting package data files...")

try:
    openpyxl_datas = collect_data_files("openpyxl")
    datas += openpyxl_datas
    print(f"   ✅ openpyxl ({len(openpyxl_datas)} files)")
except Exception as e:
    print(f"   ⚠️  openpyxl: {e}")

try:
    docx_datas = collect_data_files("docx")
    datas += docx_datas
    print(f"   ✅ docx ({len(docx_datas)} files)")
except Exception as e:
    print(f"   ⚠️  docx: {e}")

try:
    reportlab_datas = collect_data_files("reportlab")
    datas += reportlab_datas
    print(f"   ✅ reportlab ({len(reportlab_datas)} files)")
except Exception as e:
    print(f"   ⚠️  reportlab: {e}")


# ================================================================
# 9. ARABIC RESHAPER + BIDI
# ================================================================

print("📦 [9/9] Collecting arabic-reshaper + bidi...")

try:
    arabic_reshaper_datas = collect_data_files("arabic_reshaper")
    datas += arabic_reshaper_datas
    print(f"   ✅ arabic_reshaper ({len(arabic_reshaper_datas)} files)")
except Exception as e:
    print(f"   ⚠️  arabic_reshaper: {e}")

try:
    bidi_datas = collect_data_files("bidi")
    datas += bidi_datas
    print(f"   ✅ bidi ({len(bidi_datas)} files)")
except Exception as e:
    print(f"   ⚠️  bidi: {e}")


# ================================================================
# HIDDEN IMPORTS
# ================================================================

print("\n🔗 Collecting hidden imports...")

hiddenimports = []

for package in ["core", "ai", "export", "gui", "utils"]:
    try:
        submodules = collect_submodules(package)
        hiddenimports += submodules
        print(f"   ✅ {package} ({len(submodules)} modules)")
    except Exception as e:
        print(f"   ⚠️  {package}: {e}")

hiddenimports += [
    # Tkinter
    "tkinter", "tkinter.ttk", "tkinter.messagebox",
    "tkinter.filedialog", "tkinter.scrolledtext",
    "tkinter.font", "tkinter.colorchooser",
    "tkinter.constants", "tkinter.simpledialog",

    # Excel
    "openpyxl", "openpyxl.styles", "openpyxl.utils",
    "openpyxl.worksheet", "openpyxl.workbook",

    # PDF
    "reportlab", "reportlab.pdfbase", "reportlab.pdfbase.ttfonts",
    "reportlab.pdfgen", "reportlab.platypus", "reportlab.lib",
    "reportlab.lib.pagesizes", "reportlab.lib.styles",
    "reportlab.lib.colors", "reportlab.lib.units", "reportlab.lib.enums",

    # Word
    "docx", "docx.shared", "docx.enum", "docx.oxml",
    "docx.oxml.ns", "docx.oxml.shape", "docx.enum.text",

    # Images
    "PIL", "PIL.Image", "PIL.ImageTk", "PIL._tkinter_finder",

    # AI
    "openai",
    "openai._client",
    "openai.resources",
    "openai.resources.chat",
    "openai.types",
    "openai.types.chat",

    # HTTP
    "httpx", "httpcore", "anyio",

    # ✅ جدید: فارسی برای PDF
    "arabic_reshaper",
    "bidi",
    "bidi.algorithm",
    "bidi.bidi",

    # Recycle Bin
    "send2trash",

    # Database
    "sqlite3", "sqlite3.dbapi2",
]


# ================================================================
# EXCLUDES
# ================================================================

excludes = [
    "pytest", "unittest", "_pytest", "nose", "doctest",
    "IPython", "jupyter", "notebook", "ipykernel",
    "matplotlib", "pandas", "scipy", "numpy",
    "plotly", "seaborn",
    "django", "flask", "fastapi", "starlette",
    "PyQt5", "PyQt6", "PySide2", "PySide6", "wx", "kivy",
    "black", "pylint", "flake8", "mypy",
    "setuptools", "pip", "wheel",
    "test", "tests", "examples",
]


# ================================================================
# ANALYSIS
# ================================================================

print("\n🔍 Running Analysis...")

a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)


pyz = PYZ(a.pure)


exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ControlSystemManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / "resources" / "icons" / "icon.ico"),
)


# ================================================================
# SUMMARY
# ================================================================

print("\n" + "=" * 70)
print("✅ Build Configuration Complete")
print("=" * 70)
print(f"📦 Data Files:      {len(datas)}")
print(f"🔗 Hidden Imports:  {len(hiddenimports)}")
print(f"⛔ Excludes:        {len(excludes)}")
print("=" * 70 + "\n")