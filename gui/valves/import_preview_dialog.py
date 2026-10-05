# gui/valves/import_preview_dialog.py
"""
دیالوگ Preview برای Import شیرها از Excel

نمایش:
- تعداد شیرهای آماده Import
- تفکیک بر اساس نوع (PICV, 3 Way, Steam, PICV+3Way)
- هشدارها (ردیف‌های نامعتبر)
- جدول Preview با اولین N ردیف
- دکمه‌های Confirm / Cancel
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, List

from gui.theme import (
    get_color, font, sp, pad, h, w, ico,
)
from gui.components import (
    BaseDialog, PrimaryButton, SecondaryButton,
    GhostButton, ToastManager, Separator,
)


class ImportPreviewDialog(BaseDialog):
    """
    دیالوگ Preview برای Import شیرها
    
    Attributes:
        result: bool — آیا کاربر تایید کرد؟
    """
    
    # ============================================================
    # Colors
    # ============================================================
    PRIMARY = "#1F4E79"
    SUCCESS = "#27AE60"
    WARNING = "#F39C12"
    DANGER = "#E74C3C"
    LIGHT = "#F8F9FA"
    WHITE = "#FFFFFF"
    
    # ============================================================
    # Init
    # ============================================================
    
    def __init__(
        self,
        parent,
        app,
        import_result: Dict[str, Any],
        section,
    ):
        """
        Args:
            parent: والد
            app: MotorApp
            import_result: نتیجه read_and_validate() از ValvesExcelImporter
            section: Section هدف
        """
        self.app = app
        self.import_result = import_result
        self.section = section
        self.result = False   # خروجی — تا زمانی که تایید نشود False
        
        # ===== استخراج داده =====
        self.valves = import_result.get('valves', [])
        self.warnings = import_result.get('warnings', [])
        self.stats = import_result.get('stats', {})
        
        super().__init__(
            parent,
            title="📥  Valves Import Preview",
            width=1100,
            height=750,
            resizable=True,
        )
    
    # ============================================================
    # Build Body
    # ============================================================
    
    def build_body(self, parent):
        """ساخت بدنه دیالوگ"""
        
        container = tk.Frame(parent, bg=get_color('bg_app'))
        container.pack(fill=tk.BOTH, expand=True)
        
        # ===== Header =====
        self._build_preview_header(container)
        
        # ===== Stats Cards =====
        self._build_preview_stats(container)
        
        # ===== Preview Table =====
        self._build_preview_table(container)
        
        # ===== Warnings =====
        if self.warnings:
            self._build_preview_warnings(container)
    
    # ============================================================
    # Header
    # ============================================================
    
    def _build_preview_header(self, parent):
        """ساخت Header با نام Section"""
        
        header = tk.Frame(
            parent,
            bg=self.PRIMARY,
            height=60,
        )
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # ===== Title =====
        tk.Label(
            header,
            text="📥  Valves Import Preview",
            font=font('h3'),
            bg=self.PRIMARY,
            fg=self.WHITE,
            anchor='w',
        ).pack(side=tk.LEFT, padx=sp('lg'), pady=sp('md'))
        
        # ===== Target Section =====
        section_name = (
            getattr(self.section, 'display_name', None)
            or getattr(self.section, 'name', None)
            or '—'
        )
        
        tk.Label(
            header,
            text=f"→ Section: {section_name}",
            font=font('body_bold'),
            bg=self.PRIMARY,
            fg=self.WHITE,
            anchor='e',
        ).pack(side=tk.RIGHT, padx=sp('lg'))
    
    # ============================================================
    # Stats Cards
    # ============================================================
    
    def _build_preview_stats(self, parent):
        """ساخت کارت‌های آماری"""
        
        cards_frame = tk.Frame(parent, bg=get_color('bg_app'))
        cards_frame.pack(fill=tk.X, padx=sp('lg'), pady=sp('md'))
        
        # ===== Card 1: Total =====
        self._create_preview_stat_card(
            cards_frame,
            title="Total Valves",
            value=str(self.stats.get('total', 0)),
            icon="📊",
            color=self.PRIMARY,
        )
        
        # ===== Cards by Type =====
        by_type = self.stats.get('by_type', {})
        
        type_icons = {
            'PICV':      ('🔵', '#0A84FF'),
            '3 Way':     ('🟠', '#FF9F0A'),
            'Steam':     ('🔴', '#FF453A'),
            'PICV+3Way': ('🟣', '#A855F7'),
        }
        
        for vt, count in sorted(by_type.items()):
            icon, color = type_icons.get(vt, ('⚪', '#7F8C8D'))
            
            self._create_preview_stat_card(
                cards_frame,
                title=vt,
                value=str(count),
                icon=icon,
                color=color,
            )
        
        # ===== Card: Warnings =====
        if self.warnings:
            self._create_preview_stat_card(
                cards_frame,
                title="Warnings",
                value=str(len(self.warnings)),
                icon="⚠️",
                color=self.WARNING,
            )
    
    def _create_preview_stat_card(
        self, parent, title: str, value: str, icon: str, color: str
    ):
        """ساخت یک کارت آماری"""
        
        card = tk.Frame(
            parent,
            bg=get_color('bg_surface'),
            highlightthickness=2,
            highlightbackground=color,
        )
        card.pack(side=tk.LEFT, padx=sp('sm'), pady=sp('xs'))
        
        # ===== Icon + Value =====
        inner = tk.Frame(card, bg=get_color('bg_surface'))
        inner.pack(padx=sp('md'), pady=sp('sm'))
        
        tk.Label(
            inner,
            text=icon,
            font=('Segoe UI Emoji', 18),
            bg=get_color('bg_surface'),
            fg=color,
        ).pack(side=tk.LEFT, padx=(0, sp('sm')))
        
        tk.Label(
            inner,
            text=value,
            font=('Calibri', 22, 'bold'),
            bg=get_color('bg_surface'),
            fg=color,
        ).pack(side=tk.LEFT)
        
        # ===== Title =====
        tk.Label(
            card,
            text=title,
            font=font('caption'),
            bg=get_color('bg_surface'),
            fg=get_color('text_secondary'),
            anchor='w',
        ).pack(fill=tk.X, padx=sp('md'), pady=(0, sp('sm')))
    
    # ============================================================
    # Preview Table
    # ============================================================
    
    def _build_preview_table(self, parent):
        """ساخت جدول Preview"""
        
        # ===== Section Title =====
        title_frame = tk.Frame(parent, bg=get_color('bg_app'))
        title_frame.pack(fill=tk.X, padx=sp('lg'), pady=(sp('md'), sp('xs')))
        
        tk.Label(
            title_frame,
            text="📋  Preview (اولین ۲۰ ردیف)",
            font=font('h4'),
            bg=get_color('bg_app'),
            fg=get_color('text_primary'),
            anchor='w',
        ).pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text=f"نمایش ۲۰ از {len(self.valves)} شیر",
            font=font('caption'),
            bg=get_color('bg_app'),
            fg=get_color('text_muted'),
            anchor='e',
        ).pack(side=tk.RIGHT)
        
        # ===== Table Frame =====
        table_frame = tk.Frame(
            parent,
            bg=get_color('bg_surface'),
            highlightthickness=1,
            highlightbackground=get_color('border_default'),
        )
        table_frame.pack(
            fill=tk.BOTH, expand=True,
            padx=sp('lg'), pady=sp('xs')
        )
        
        # ===== Columns =====
        columns = [
            ('no', '#', 40),
            ('equipment', 'Equipment', 180),
            ('valve_type', 'ValveType', 100),
            ('flow', 'Flow', 80),
            ('unit', 'Unit', 70),
            ('pressure_drop', 'PD (psi)', 80),
            ('circuit', 'Circuit', 130),
            ('qty', 'Qty', 50),
            ('model', 'Model', 130),
            ('actuator', 'Actuator', 140),
            ('signal', 'Signal', 130),
        ]
        
        # ===== Treeview =====
        tree = ttk.Treeview(
            table_frame,
            columns=[c[0] for c in columns],
            show='headings',
            height=10,
        )
        
        # ===== Heading + Column =====
        for col_id, label, width in columns:
            tree.heading(col_id, text=label, anchor='center')
            tree.column(col_id, width=width, anchor='center', minwidth=40)
        
        # ===== Style =====
        style = ttk.Style()
        style.configure(
            'Preview.Treeview',
            font=('Calibri', 9),
            rowheight=24,
            background=self.WHITE,
            fieldbackground=self.WHITE,
        )
        style.configure(
            'Preview.Treeview.Heading',
            font=('Calibri', 9, 'bold'),
        )
        tree.configure(style='Preview.Treeview')
        
        # ===== Data (اولین ۲۰) =====
        preview_valves = self.valves[:20]
        
        for i, valve in enumerate(preview_valves, 1):
            row_values = self._get_preview_row_values(valve, i)
            
            # رنگ بر اساس نوع
            tag = self._get_tag_for_valve(valve)
            
            tree.insert('', 'end', values=row_values, tags=(tag,))
        
        # ===== Tag Colors =====
        tree.tag_configure('picv', background='#E8F4FD')
        tree.tag_configure('3way', background='#FFF8E1')
        tree.tag_configure('steam', background='#FFEBEE')
        tree.tag_configure('picv_3way', background='#F3E5F5')
        
        # ===== Scrollbars =====
        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
    
    def _get_preview_row_values(self, valve, idx: int) -> tuple:
        """مقادیر یک ردیف Preview"""
        try:
            # ===== Model =====
            if valve.ValveType == 'PICV':
                model = getattr(valve, 'PICVModel', '') or '—'
                actuator = getattr(valve, 'PICVActuator', '') or '—'
                signal = getattr(valve, 'PICVSignal', '') or '—'
            elif valve.ValveType == '3 Way':
                model = valve.__dict__.get('3WayModel', '') or '—'
                actuator = valve.__dict__.get('3WayActuator', '') or '—'
                signal = valve.__dict__.get('3WaySignal', '') or '—'
            elif valve.ValveType == 'Steam':
                model = getattr(valve, 'SteamModel', '') or '—'
                actuator = getattr(valve, 'SteamActuator', '') or '—'
                signal = getattr(valve, 'SteamSignal', '') or '—'
            elif valve.ValveType == 'PICV+3Way':
                picv_model = getattr(valve, 'PICVModel', '') or '—'
                model_3w = valve.__dict__.get('3WayModel', '') or '—'
                model = f"{picv_model} / {model_3w}"
                actuator = valve.__dict__.get('3WayActuator', '') or '—'
                signal = valve.__dict__.get('3WaySignal', '') or '—'
            else:
                model = '—'
                actuator = '—'
                signal = '—'
            
            return (
                str(idx),
                valve.Equipment or '—',
                valve.ValveType or '—',
                f"{valve.Flow:.2f}" if valve.Flow else '—',
                valve.Unit or '—',
                f"{valve.PressureDrop:.2f}" if valve.PressureDrop else '—',
                valve.Circuit or '—',
                str(valve.Quantity or 1),
                str(model)[:30],
                str(actuator)[:30],
                str(signal)[:30],
            )
        
        except Exception as e:
            return (
                str(idx), '—', '—', '—', '—', '—', '—', '—', '—', '—', '—'
            )
    
    def _get_tag_for_valve(self, valve) -> str:
        """تعیین tag رنگ"""
        if valve.ValveType == 'PICV':
            return 'picv'
        elif valve.ValveType == '3 Way':
            return '3way'
        elif valve.ValveType == 'Steam':
            return 'steam'
        elif valve.ValveType == 'PICV+3Way':
            return 'picv_3way'
        return ''
    
    # ============================================================
    # Warnings
    # ============================================================
    
    def _build_preview_warnings(self, parent):
        """ساخت بخش هشدارها"""
        
        warn_frame = tk.Frame(
            parent,
            bg='#FFF3CD',
            highlightthickness=2,
            highlightbackground=self.WARNING,
        )
        warn_frame.pack(
            fill=tk.X,
            padx=sp('lg'),
            pady=(sp('xs'), sp('md')),
        )
        
        # ===== Header =====
        header = tk.Frame(warn_frame, bg='#FFF3CD')
        header.pack(fill=tk.X, padx=sp('md'), pady=(sp('sm'), sp('xs')))
        
        tk.Label(
            header,
            text=f"⚠️  {len(self.warnings)} هشدار",
            font=font('body_bold'),
            bg='#FFF3CD',
            fg='#856404',
            anchor='w',
        ).pack(side=tk.LEFT)
        
        # ===== Toggle Button =====
        self._warnings_visible = tk.BooleanVar(value=False)
        
        toggle_btn = tk.Label(
            header,
            text="نمایش ▼",
            font=font('caption'),
            bg='#FFF3CD',
            fg='#856404',
            cursor='hand2',
        )
        toggle_btn.pack(side=tk.RIGHT)
        
        # ===== List (Hidden by default) =====
        list_frame = tk.Frame(warn_frame, bg='#FFF3CD')
        
        text_widget = tk.Text(
            list_frame,
            height=6,
            font=('Consolas', 9),
            bg='#FFFBF0',
            fg='#856404',
            wrap=tk.WORD,
            relief='flat',
            padx=sp('sm'),
            pady=sp('sm'),
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        for i, w in enumerate(self.warnings[:50], 1):
            text_widget.insert('end', f"{i}. {w}\n")
        
        if len(self.warnings) > 50:
            text_widget.insert(
                'end',
                f"\n... و {len(self.warnings) - 50} هشدار دیگر"
            )
        
        text_widget.config(state='disabled')
        
        # ===== Toggle Function =====
        def toggle():
            if self._warnings_visible.get():
                list_frame.pack_forget()
                toggle_btn.configure(text="نمایش ▼")
                self._warnings_visible.set(False)
            else:
                list_frame.pack(
                    fill=tk.X, padx=sp('md'), pady=(0, sp('sm'))
                )
                toggle_btn.configure(text="پنهان ▲")
                self._warnings_visible.set(True)
        
        toggle_btn.bind('<Button-1>', lambda e: toggle())
    
    # ============================================================
    # on_ok
    # ============================================================
    
    def on_ok(self):
        """تایید و بستن"""
        # ===== تایید نهایی =====
        count = len(self.valves)
        section_name = (
            getattr(self.section, 'display_name', None)
            or getattr(self.section, 'name', None)
            or '—'
        )
        
        # ✅ استفاده از _root به جای root
        if not messagebox.askyesno(
            "Confirm Import",
            f"افزودن {count} شیر به Section '{section_name}'؟\n\n"
            f"در صورت تکراری بودن Equipment، "
            f"پسوند (2), (3) اضافه می‌شود.",
            parent=self,   # ✅ استفاده از خود دیالوگ به عنوان parent
        ):
            return
        
        self.result = True
        self._close_dialog()
    
    def on_cancel(self):
        """لغو"""
        self.result = False
        self._close_dialog()
    
    # ============================================================
    # Footer Buttons (Override)
    # ============================================================
    
    def build_footer(self, parent):
        """ساخت فوتر با دکمه‌های Cancel / Import"""
        
        footer = tk.Frame(parent, bg=get_color('bg_surface'), height=70)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        btn_frame = tk.Frame(footer, bg=get_color('bg_surface'))
        btn_frame.pack(side=tk.RIGHT, padx=sp('lg'), pady=sp('md'))
        
        # ===== Info =====
        tk.Label(
            footer,
            text=f"📊 آماده Import: {len(self.valves)} شیر",
            font=font('body_bold'),
            bg=get_color('bg_surface'),
            fg=self.SUCCESS,
            anchor='w',
        ).pack(side=tk.LEFT, padx=sp('lg'))
        
        # ===== Import Button =====
        PrimaryButton(
            btn_frame,
            text=f"✅  Import {len(self.valves)} Valves",
            command=self.on_ok,
        ).pack(side=tk.RIGHT)
        
        # ===== Cancel =====
        SecondaryButton(
            btn_frame,
            text="Cancel",
            command=self.on_cancel,
        ).pack(side=tk.RIGHT, padx=(0, sp('sm')))


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['ImportPreviewDialog']