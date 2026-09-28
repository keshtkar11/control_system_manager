# gui/layout/statusbar.py
"""
نوار وضعیت - Status Bar
با Project + Revision + Section + Stats + Save Status + تاریخ شمسی
"""

import tkinter as tk
from datetime import datetime
from typing import Optional

from gui.theme import (
    get_color, font, sp, pad, h, ico,
    create_tooltip,
)


# ================================================================
# 📅 تبدیل تاریخ میلادی به شمسی
# ================================================================

def gregorian_to_jalali(gy: int, gm: int, gd: int) -> tuple:
    """
    تبدیل تاریخ میلادی به شمسی
    
    Args:
        gy: سال میلادی
        gm: ماه میلادی (1-12)
        gd: روز میلادی (1-31)
    
    Returns:
        (سال شمسی, ماه شمسی, روز شمسی)
    """
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    
    if gm > 2:
        gy2 = gy + 1
    else:
        gy2 = gy
    
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + \
           ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    
    return jy, jm, jd


def get_jalali_date_str() -> str:
    """دریافت تاریخ شمسی به صورت رشته"""
    today = datetime.now()
    jy, jm, jd = gregorian_to_jalali(today.year, today.month, today.day)
    return f"{jy}/{jm:02d}/{jd:02d}"


# ================================================================
# STATUS BAR
# ================================================================

class StatusBar(tk.Frame):
    """
    نوار وضعیت پایین پنجره
    
    شامل:
    - وضعیت (Status)
    - پروژه + Revision + Section (Context)
    - آمار (Devices + I/O)
    - وضعیت ذخیره
    - تاریخ شمسی + ساعت
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=get_color('bg_surface'),
            height=h('statusbar'),
            **kwargs
        )
        
        self.pack_propagate(False)
        
        # ============================================================
        # متغیرهای داخلی
        # ============================================================
        self._is_saved = True
        self._save_time = datetime.now()
        self._device_count = 0
        self._active_count = 0
        self._io_stats = {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0, 'total': 0}
        
        # ============================================================
        # ساخت سه ناحیه
        # ============================================================
        self._build_left_section()
        self._build_center_section()
        self._build_right_section()
        
        # ============================================================
        # شروع به‌روزرسانی زمان
        # ============================================================
        self._update_time()
    
    # ================================================================
    # ساخت بخش‌ها
    # ================================================================
    
    def _build_left_section(self):
        """بخش چپ: وضعیت (Status)"""
        self.left_frame = tk.Frame(self, bg=get_color('bg_surface'))
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=sp('md'))
        
        # Status icon
        self.status_icon = tk.Label(
            self.left_frame,
            text=ico('check_circle'),
            font=font('small'),
            bg=get_color('bg_surface'),
            fg=get_color('success'),
        )
        self.status_icon.pack(side=tk.LEFT, padx=(0, sp('xs')))
        
        # Status text
        self.status_label = tk.Label(
            self.left_frame,
            text="Ready",
            font=font('small'),
            bg=get_color('bg_surface'),
            fg=get_color('text_secondary'),
        )
        self.status_label.pack(side=tk.LEFT)
    
    def _build_center_section(self):
        """بخش وسط: Context (پروژه + Revision + Section + Stats)"""
        self.center_frame = tk.Frame(self, bg=get_color('bg_surface'))
        self.center_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # ===== Placeholder =====
        self.center_label = tk.Label(
            self.center_frame,
            text="",
            font=font('small'),
            bg=get_color('bg_surface'),
            fg=get_color('text_muted'),
        )
        self.center_label.pack(side=tk.LEFT)
    
    def _build_right_section(self):
        """بخش راست: Save Status + تاریخ + ساعت"""
        self.right_frame = tk.Frame(self, bg=get_color('bg_surface'))
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=sp('md'))
        
        # ===== Time (ساعت) =====
        self.time_label = tk.Label(
            self.right_frame,
            text="",
            font=('Segoe UI', 10, 'bold'),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
        )
        self.time_label.pack(side=tk.RIGHT)
        
        tk.Label(
            self.right_frame,
            text="🕐",
            font=font('small'),
            bg=get_color('bg_surface'),
            fg=get_color('text_muted'),
        ).pack(side=tk.RIGHT, padx=(0, sp('xs')))
        
        # ===== Separator =====
        tk.Label(
            self.right_frame,
            text="│",
            font=font('small'),
            bg=get_color('bg_surface'),
            fg=get_color('border_default'),
        ).pack(side=tk.RIGHT, padx=sp('sm'))
        
        # ===== Date (تاریخ شمسی) =====
        self.date_label = tk.Label(
            self.right_frame,
            text=get_jalali_date_str(),
            font=font('small'),
            bg=get_color('bg_surface'),
            fg=get_color('text_secondary'),
        )
        self.date_label.pack(side=tk.RIGHT)
        
        tk.Label(
            self.right_frame,
            text="📅",
            font=font('small'),
            bg=get_color('bg_surface'),
            fg=get_color('text_muted'),
        ).pack(side=tk.RIGHT, padx=(0, sp('xs')))
        
        # ===== Separator =====
        tk.Label(
            self.right_frame,
            text="│",
            font=font('small'),
            bg=get_color('bg_surface'),
            fg=get_color('border_default'),
        ).pack(side=tk.RIGHT, padx=sp('sm'))
        
        # ===== Save Status =====
        self.save_label = tk.Label(
            self.right_frame,
            text="💾 Saved",
            font=font('small'),
            bg=get_color('bg_surface'),
            fg=get_color('success'),
        )
        self.save_label.pack(side=tk.RIGHT, padx=(0, sp('xs')))
    
    # ================================================================
    # زمان و تاریخ
    # ================================================================
    
    def _update_time(self):
        """به‌روزرسانی ساعت و تاریخ"""
        now = datetime.now()
        
        # ساعت
        self.time_label.configure(text=now.strftime("%H:%M:%S"))
        
        # تاریخ شمسی (هر دقیقه یکبار چک می‌کنه که تغییر روز رو بگیره)
        self.date_label.configure(text=get_jalali_date_str())
        
        # هر ثانیه
        self.after(1000, self._update_time)
    
    # ================================================================
    # متد اصلی: set_context
    # ================================================================
    
    def set_context(self, project: str = "", revision: str = "", section: str = ""):
        """
        تنظیم context (پروژه + Revision + Section)
        
        Args:
            project: نام پروژه
            revision: نام Revision (با "(Current)" اگر Current باشه)
            section: نام بخش
        """
        # ===== ذخیره برای استفاده بعدی =====
        self._current_project = project
        self._current_revision = revision
        self._current_section = section
        
        # ===== رندر مجدد =====
        self._render_center()
    
    def _render_center(self):
        """رندر ناحیه وسط با همه اطلاعات"""
        # ===== پاک کردن =====
        for widget in self.center_frame.winfo_children():
            widget.destroy()
        
        project = getattr(self, '_current_project', '')
        revision = getattr(self, '_current_revision', '')
        section = getattr(self, '_current_section', '')
        
        has_any = project or revision or section
        
        if not has_any:
            return
        
        # ============================================================
        # 🏗️ Project
        # ============================================================
        if project:
            self._add_item(
                text=f"{ico('project')}  {project}",
                color=get_color('text_primary'),
                font_style='body',
            )
        
        # ============================================================
        # 📌 Revision (برجسته)
        # ============================================================
        if revision:
            self._add_separator()
            
            is_current = '(Current)' in revision
            clean_name = revision.replace(' (Current)', '').replace('(Current)', '').strip()
            
            rev_icon = '📌' if is_current else '📎'
            rev_color = get_color('success') if is_current else get_color('accent_cyan')
            
            # آیکون
            tk.Label(
                self.center_frame,
                text=rev_icon,
                font=font('small'),
                bg=get_color('bg_surface'),
                fg=rev_color,
            ).pack(side=tk.LEFT)
            
            # نام Revision (Bold)
            tk.Label(
                self.center_frame,
                text=f" {clean_name}",
                font=('Segoe UI', 10, 'bold'),
                bg=get_color('bg_surface'),
                fg=rev_color,
            ).pack(side=tk.LEFT)
            
            # (Current) اگر Current باشه
            if is_current:
                tk.Label(
                    self.center_frame,
                    text=" (Current)",
                    font=font('caption'),
                    bg=get_color('bg_surface'),
                    fg=get_color('text_muted'),
                ).pack(side=tk.LEFT)
        
        # ============================================================
        # 📂 Section
        # ============================================================
        if section:
            self._add_separator()
            
            tk.Label(
                self.center_frame,
                text=f"{ico('section')}  {section}",
                font=font('small'),
                bg=get_color('bg_surface'),
                fg=get_color('text_secondary'),
            ).pack(side=tk.LEFT)
        
        # ============================================================
        # 🔧 Devices + 🔋 Active
        # ============================================================
        if self._device_count > 0:
            self._add_separator()
            
            tk.Label(
                self.center_frame,
                text=f"🔧 {self._device_count}",
                font=font('small'),
                bg=get_color('bg_surface'),
                fg=get_color('text_primary'),
            ).pack(side=tk.LEFT)
            
            tk.Label(
                self.center_frame,
                text=f"  🔋 {self._active_count}",
                font=font('small'),
                bg=get_color('bg_surface'),
                fg=get_color('success'),
            ).pack(side=tk.LEFT)
        
        # ============================================================
        # 📊 I/O (با Tooltip)
        # ============================================================
        if self._io_stats['total'] > 0:
            self._add_separator()
            
            io_total = self._io_stats['total']
            
            io_label = tk.Label(
                self.center_frame,
                text=f"📊 {io_total} I/O",
                font=('Segoe UI', 10, 'bold'),
                bg=get_color('bg_surface'),
                fg=get_color('primary'),
                cursor='hand2',
            )
            io_label.pack(side=tk.LEFT)
            
            # ✅ Tooltip با تفکیک I/O
            tooltip_text = (
                f"Total: {io_total} I/O\n"
                f"{'─' * 20}\n"
                f"DI: {self._io_stats['DI']}\n"
                f"DO: {self._io_stats['DO']}\n"
                f"AI: {self._io_stats['AI']}\n"
                f"AO: {self._io_stats['AO']}"
            )
            create_tooltip(io_label, tooltip_text, delay=300, duration=5000, position='above')
    
    def _add_item(self, text: str, color: str, font_style: str = 'small'):
        """افزودن یک آیتم به center"""
        tk.Label(
            self.center_frame,
            text=text,
            font=font(font_style),
            bg=get_color('bg_surface'),
            fg=color,
        ).pack(side=tk.LEFT)
    
    def _add_separator(self):
        """افزودن جداکننده"""
        tk.Label(
            self.center_frame,
            text="│",
            font=font('small'),
            bg=get_color('bg_surface'),
            fg=get_color('border_default'),
        ).pack(side=tk.LEFT, padx=sp('sm'))
    
    # ================================================================
    # آمار
    # ================================================================
    
    def update_stats(self, device_count: int = 0, active_count: int = 0,
                     io_stats: dict = None):
        """
        به‌روزرسانی آمار
        
        Args:
            device_count: تعداد کل Device ها
            active_count: تعداد Device های فعال
            io_stats: {'DI': ..., 'DO': ..., 'AI': ..., 'AO': ..., 'total': ...}
        """
        self._device_count = device_count
        self._active_count = active_count
        
        if io_stats:
            self._io_stats = io_stats
        else:
            self._io_stats = {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0, 'total': 0}
        
        # رندر مجدد
        self._render_center()
    
    # ================================================================
    # وضعیت ذخیره
    # ================================================================
    
    def set_save_status(self, saved: bool, save_time: datetime = None):
        """
        تنظیم وضعیت ذخیره
        
        Args:
            saved: آیا ذخیره شده؟
            save_time: زمان ذخیره
        """
        self._is_saved = saved
        if save_time:
            self._save_time = save_time
        
        if saved:
            self.save_label.configure(
                text="💾 Saved",
                fg=get_color('success'),
            )
            create_tooltip(
                self.save_label,
                f"Last saved: {self._save_time.strftime('%H:%M:%S')}",
                delay=300,
            )
        else:
            self.save_label.configure(
                text="● Unsaved",
                fg=get_color('warning'),
            )
            create_tooltip(
                self.save_label,
                "Changes not saved yet",
                delay=300,
            )
    
    # ================================================================
    # وضعیت (Status)
    # ================================================================
    
    def set_status(self, text: str, status_type: str = 'info'):
        """
        تنظیم وضعیت
        
        Args:
            text: متن وضعیت
            status_type: 'info', 'success', 'warning', 'error'
        """
        icons = {
            'info':    ('info_circle', 'info'),
            'success': ('check_circle', 'success'),
            'warning': ('warning_triangle', 'warning'),
            'error':   ('x_circle', 'danger'),
        }
        
        icon_name, color_key = icons.get(status_type, icons['info'])
        
        self.status_icon.configure(
            text=ico(icon_name),
            fg=get_color(color_key),
        )
        self.status_label.configure(text=text)
    
    # ================================================================
    # Legacy (سازگاری)
    # ================================================================
    
    def set_info(self, key: str, value: str):
        """Legacy: تنظیم اطلاعات"""
        # این متد دیگه استفاده نمی‌شه ولی برای سازگاری نگه داشته شده
        pass


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['StatusBar', 'get_jalali_date_str', 'gregorian_to_jalali']