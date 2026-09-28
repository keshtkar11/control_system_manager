# main.py
"""نقطه ورود اصلی برنامه - Design System جدید"""

import tkinter as tk
import sys
import os
import logging
from pathlib import Path

# ================================================================
# LOGGING SETUP — منبع واحد
# ================================================================

# ✅ استفاده از logger جدید (قبل از هر import دیگر)
from utils.logger import get_logger

logger = get_logger("control_system", level="INFO")

# ================================================================
# PROJECT PATHS
# ================================================================

if getattr(sys, "frozen", False):
    # در EXE، مسیر main.py در sys._MEIPASS است
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ================================================================
# آماده‌سازی پوشه‌های کاربر
# ================================================================

try:
    from utils.paths import get_output_dir, get_logs_dir
    get_output_dir()      # ← ساخت پوشه output
    get_logs_dir()        # ← ساخت پوشه logs
    logger.debug("✅ User directories ready")
except Exception as e:
    logger.error(f"⚠️ Could not prepare user directories: {e}")


# ================================================================
# IMPORTS
# ================================================================

from gui.theme import (
    get_theme_manager,
    apply_ttk_styles,
    get_color,
)
from gui.components import ToastManager


# ================================================================
# MAIN FUNCTION
# ================================================================

def main():
    """تابع اصلی برنامه"""
    
    # ===== 1. ساخت پنجره اصلی =====
    root = tk.Tk()
    root.title("Control System Devices Manager")
    
    # ===== 2. تنظیم آیکون — با پشتیبانی از EXE =====
    try:
        from utils.paths import get_resource_path
        
        icon_path = get_resource_path("resources", "icons", "icon.ico")
        
        if icon_path.exists():
            root.iconbitmap(str(icon_path))
        else:
            logger.warning(f"⚠️ Icon file not found: {icon_path}")
    except Exception as e:
        logger.warning(f"⚠️ Could not load icon: {e}")
    
    # ===== 3. اعمال تم جدید =====
    try:
        theme_manager = get_theme_manager()
        logger.info(f"Theme loaded: {theme_manager.current_theme}")
        
        apply_ttk_styles(root)
        root.configure(bg=get_color('bg_app'))
        
    except Exception as e:
        logger.error(f"Failed to apply theme: {e}", exc_info=True)
    
    # ===== 4. راه‌اندازی ToastManager =====
    ToastManager.set_parent(root)
    
    # ===== 5. ایجاد پنجره اصلی =====
    try:
        from gui.main_window import MotorApp
        app = MotorApp(root)
        logger.info("Application started successfully")
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        from tkinter import messagebox
        messagebox.showerror(
            "Critical Error",
            f"Failed to start application:\n\n{str(e)}"
        )
        root.destroy()
        sys.exit(1)
    
    # ===== 6. اجرای برنامه =====
    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        root.destroy()
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        from tkinter import messagebox
        messagebox.showerror(
            "Critical Error",
            f"Unexpected error:\n\n{str(e)}"
        )
        root.destroy()
        sys.exit(1)


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    main()