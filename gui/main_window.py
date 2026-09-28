# gui/main_window.py
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox, scrolledtext
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import json
import math
import logging
from core.models import Valve                                    # ✅ اضافه کنید
from utils.paths import get_resource_path   # ← 🆕

# ===== Core =====
from core import (
    Project, ProjectSection, Motor,
    DatabaseManager, HistoryManager,
    COMPONENT_LABELS, LIMITS,
    validate_device_name, validate_io_value,
)
from core.component_manager import ComponentManager
from core.template_manager import TemplateManager

from gui.attachments_panel import AttachmentsPanel    
from gui.valves import ValvesPanel   
from core.attachments import AttachmentManager  

# ===== Theme & Components =====
from gui.theme import (
    get_theme_manager, apply_ttk_styles,
    get_color, font, sp, pad, h, w, ico,
)
from gui.components import (
    ToastManager,
    PrimaryButton, SecondaryButton, GhostButton,
    DangerButton, SuccessButton, IconButton,
    button, icon_button,
    confirm_dialog, message_dialog,
)
from gui.layout import (
    StatusBar, Toolbar, Sidebar, DeviceTable,
)

# ===== Dialogs =====
from gui.dialogs_new import DeviceDialog, ProjectManagerDialog
from gui.help import HelpDialog

# ===== Legacy Dialogs =====
from gui.dialogs import (
    SectionManagerDialog,
    LabelsManagerDialog,
    DeviceReorderDialog,
)

# ============================================================
# ✅ Logger Setup
# ============================================================
logger = logging.getLogger(__name__)


class MotorApp:
    """
    کلاس اصلی برنامه - Design System جدید
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Control System Devices Manager (Vahhaj Sanat Co.)")
        
        # ==================== تنظیمات اولیه ====================
        self._setup_window()
        
        # ==================== Theme ====================
        self.tm = get_theme_manager()
        apply_ttk_styles(root)
        ToastManager.set_parent(root)
        
        # ==================== هسته ====================
        self.db = DatabaseManager()
        self.component_manager = ComponentManager(self.db)
        self.template_manager = TemplateManager(self.db)
        self.history = HistoryManager()
        
        # ✅ Attachment Manager
        self.attachment_manager = AttachmentManager(self.db)
        
        # ==================== داده‌ها ====================
        self.projects: Dict[str, Project] = {}
        self.current_project_name: Optional[str] = None
        self.current_section_name: Optional[str] = None
        self.copied_motors: List[Motor] = []
        self.copied_valves: List[Any] = []  
        self.component_labels: Dict[str, Dict[str, str]] = {}
        
        # ==================== AI (Lazy Loading) ====================
        self._learning_engine = None
        self._ai_assistant = None
        
        # ==================== ساخت UI ====================
        self._create_widgets()
        
        # ==================== بارگذاری ====================
        self._load_initial_data()
        
        # ==================== میانبرهای صفحه کلید ====================
        self._setup_shortcuts()
        
        # ==================== Toast خوش‌آمد ====================
        self.root.after(500, lambda: ToastManager.success("Welcome to Control System Manager!"))
    
    # ================================================================
    # SETUP
    # ================================================================
    
    def _setup_window(self):
        """تنظیم اندازه پنجره"""
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        
        width = int(screen_w * 0.9)
        height = int(screen_h * 0.85)
        
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(1200, 700)
        self.root.configure(bg=get_color('bg_app'))
        
        # آیکون — با پشتیبانی از EXE
        try:
            from utils.paths import get_resource_path   # ← 🆕
            icon_path = get_resource_path("resources", "icons", "icon.ico")
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception as e:
            logger.debug(f"Failed to load icon: {e}")
    
    def _create_widgets(self):
        """ساخت همه ویجت‌ها"""

        # ===== 0. Menu =====
        self._create_menu()
        
        # ===== 1. Toolbar =====
        self._create_toolbar()
        
        # ===== 2. Main Content =====
        main = tk.Frame(self.root, bg=get_color('bg_app'))
        main.pack(fill=tk.BOTH, expand=True)
        
        # ---- Sidebar ----
        self._create_sidebar(main)
        
        # ---- Center ----
        center = tk.Frame(main, bg=get_color('bg_app'))
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=sp('md'), pady=sp('md'))
        
        # ============================================================
        # ✅ Notebook با سه Tab: Devices + Valves + Attachments
        # ============================================================
        self.notebook = ttk.Notebook(center)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # ===== Tab 1: Devices =====
        self.devices_tab = tk.Frame(self.notebook, bg=get_color('bg_app'))
        self.notebook.add(
            self.devices_tab,
            text=f"  {ico('device')}  Devices  "
        )
        
        self.table = DeviceTable(self.devices_tab, app=self)
        self.table.pack(fill=tk.BOTH, expand=True)
        
        # ===== Tab 2: Valves (جدید) =====
        self.valves_tab = tk.Frame(self.notebook, bg=get_color('bg_app'))
        self.notebook.add(
            self.valves_tab,
            text=f"  {ico('valve')}  Valves  "
        )
        
        self.valves_panel = ValvesPanel(self.valves_tab, app=self)
        self.valves_panel.pack(fill=tk.BOTH, expand=True)
        
        # ===== Tab 3: Attachments =====
        self.attachments_tab = tk.Frame(self.notebook, bg=get_color('bg_app'))
        self.notebook.add(
            self.attachments_tab,
            text=f"  {ico('attachment')}  Attachments  "
        )
        
        self.attachments_panel = AttachmentsPanel(self.attachments_tab, app=self)
        self.attachments_panel.pack(fill=tk.BOTH, expand=True)
        self.attachments_panel.set_attachment_manager(self.attachment_manager)
        
        # ===== 3. StatusBar =====
        self._create_status_bar()
    
    def _create_menu(self):
        """ایجاد منوی اصلی"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # ============================================================
        # FILE MENU
        # ============================================================
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # ===== Project =====
        file_menu.add_command(
            label="New Project",
            command=self._new_project,
            accelerator="Ctrl+N",
        )
        file_menu.add_command(
            label="Open Project Manager",
            command=self._open_project_manager,
            accelerator="Ctrl+O",
        )
        file_menu.add_separator()
        
        # ===== Export =====
        file_menu.add_command(
            label="📗  Export to Excel",
            command=self._export_excel,
            accelerator="Ctrl+E",
        )
        file_menu.add_command(
            label="📕  Export to PDF",
            command=self._export_pdf,
            accelerator="Ctrl+P",
        )
        file_menu.add_separator()
        
        # ===== Project Backup/Restore =====
        file_menu.add_command(
            label="📦  Backup Current Project",
            command=self._backup_current_project,
            accelerator="Ctrl+B",
        )
        file_menu.add_command(
            label="📥  Restore Project",
            command=self._restore_project,
            accelerator="Ctrl+R",
        )
        file_menu.add_separator()

        # ===== Full Project Backup (with Attachments) =====
        file_menu.add_command(
            label="📦  Backup Project (Full + Attachments)",
            command=self._backup_current_project_full,
            accelerator="Ctrl+Shift+B",
        )
        file_menu.add_command(
            label="📥  Restore Project (Full + Attachments)",
            command=self._restore_project_full,
            accelerator="Ctrl+Shift+R",
        )
        

        file_menu.add_separator()        
        # ===== Exit =====
        file_menu.add_command(
            label="Exit",
            command=self.root.quit,
            accelerator="Ctrl+Q",
        )
        
        # ============================================================
        # EDIT MENU
        # ============================================================
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        edit_menu.add_command(label="Add Device", command=self._add_device, accelerator="Ctrl+Shift+A")
        edit_menu.add_command(label="Edit Device", command=self._edit_device, accelerator="Ctrl+E")
        edit_menu.add_command(label="Delete Device", command=self._delete_device, accelerator="Delete")
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy Device", command=self._copy_device, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste Device", command=self._paste_device, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Manage Sections", command=self._manage_sections)
        edit_menu.add_command(label="Manage Labels", command=self._manage_labels)
        edit_menu.add_separator()
        edit_menu.add_command(
            label="🔍  Check Duplicate Device Names",
            command=self._check_duplicate_names,
            accelerator="Ctrl+D",
        )
        edit_menu.add_command(
            label="🔧  Fix Duplicate Device Names",
            command=self._fix_duplicate_names,
            accelerator="Ctrl+Shift+D",
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="🔍  Check Duplicate Valve Names",
            command=self._check_valve_duplicates,
        )
        edit_menu.add_command(
            label="🔧  Fix Duplicate Valve Names",
            command=self._fix_valve_duplicates,
        )

        edit_menu.add_command(
            label="⚠️  Validate Project",
            command=self._validate_project,
            accelerator="Ctrl+Shift+V",
        )

        edit_menu.add_separator()
        edit_menu.add_command(label="Undo", command=self._undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self._redo, accelerator="Ctrl+Y")
        
        # ============================================================
        # VIEW MENU
        # ============================================================
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        
        view_menu.add_command(label="Refresh", command=self._refresh_ui, accelerator="F5")
        view_menu.add_command(label="Project Summary", command=self._show_project_summary)
        
        # ============================================================
        # TOOLS MENU
        # ============================================================
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        tools_menu.add_command(
            label="🧩  Component Manager",
            command=self._open_component_manager,
        )
        tools_menu.add_command(
            label="🚰  Valve Statistics",
            command=self._show_valve_statistics,
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label="📥  Import Proposal from Word",
            command=self._import_proposal,
        )
        tools_menu.add_command(
            label="📋  Manage Proposal Templates",
            command=self._manage_proposal_templates,
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label="🔍  Global Search",
            command=self._open_global_search,
            accelerator="Ctrl+F",
        )

        tools_menu.add_separator()
        
        # ===== Database Backup/Restore =====
        tools_menu.add_command(
            label="💾  Backup Database",
            command=self._backup_database,
        )
        tools_menu.add_command(
            label="📂  Restore Database",
            command=self._restore_database,
        )
        tools_menu.add_command(
            label="📁  Open Backup Folder",
            command=self._open_backup_folder,
        )
        
        # ============================================================
        # AI MENU
        # ============================================================
        ai_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="AI", menu=ai_menu)
        
        ai_menu.add_command(
            label="🧠  Learn from Current Project (All Revisions)",
            command=self._learn_project,
            accelerator="Ctrl+L",
        )
        ai_menu.add_command(
            label="🌐  Learn from ALL Projects",       # ✅ جدید
            command=self._learn_all_projects,
            accelerator="Ctrl+Shift+L",
        )
        ai_menu.add_command(label="🔮  Predict Components", command=self._predict_components)
        ai_menu.add_command(label="⚡  Optimize I/O", command=self._optimize_io)
        ai_menu.add_separator()
        ai_menu.add_command(label="📊  Learning Statistics", command=self._show_learning_stats)
        ai_menu.add_command(label="🔗  Similar Projects", command=self._find_similar_projects)
        ai_menu.add_separator()
        ai_menu.add_command(label="🤖  AI Assistant", command=self._open_ai_assistant)
        ai_menu.add_command(label="💡  Recommendations", command=self._get_recommendations)
        
        # ============================================================
        # HELP MENU
        # ============================================================
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        help_menu.add_command(label="📖  Help Center", command=self._open_help, accelerator="F1")
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_toolbar(self):
        """ساخت Toolbar"""
        self.toolbar = Toolbar(self.root)
        self.toolbar.pack(fill=tk.X, side=tk.TOP)
        
        # ============================================================
        # ✅ Add/Edit/Delete منتقل شده‌اند به Device Table
        # ============================================================
                        
        # ===== Undo/Redo =====
        self.undo_btn = self.toolbar.add_icon_button(
            'undo',
            command=self._undo,
            tooltip="Undo (Ctrl+Z)",
        )
        self.redo_btn = self.toolbar.add_icon_button(
            'redo',
            command=self._redo,
            tooltip="Redo (Ctrl+Y)",
        )
        
        self.toolbar.add_separator()
        
        # ============================================================
        # Attachments
        # ============================================================
        self.toolbar.add_icon_button(
            'attachment',
            command=self._switch_to_attachments,
            tooltip="Attachments (Ctrl+Shift+P)",
        )
        
        self.toolbar.add_separator()
        
        # ============================================================
        # AI Buttons
        # ============================================================
        self.toolbar.add_icon_button(
            'brain',
            command=self._learn_project,
            tooltip="Learn from Project (Ctrl+L)",
            fg='#A855F7',
        )
        self.toolbar.add_icon_button(
            'predict',
            command=self._predict_components,
            tooltip="Predict Components",
        )
        self.toolbar.add_icon_button(
            'optimize',
            command=self._optimize_io,
            tooltip="Optimize I/O",
        )
        self.toolbar.add_icon_button(
            'ai',
            command=self._open_ai_assistant,
            tooltip="AI Assistant",
        )
        
        # ============================================================
        # RIGHT SECTION
        # ============================================================
        self.toolbar.add_icon_button(
            'search',
            side='right',
            command=self._open_global_search,
            tooltip="Search (Ctrl+F)",
        )
        self.toolbar.add_icon_button(
            'theme',
            side='right',
            command=self._toggle_theme,
            tooltip="Toggle Theme",
        )
        self.toolbar.add_icon_button(
            'help',
            side='right',
            command=self._open_help,
            tooltip="Help (F1)",
        )
        self.toolbar.add_icon_button(
            'settings',
            side='right',
            command=self._open_component_manager,
            tooltip="Component Manager",
        )
    
    def _create_sidebar(self, parent):
        """ساخت Sidebar"""
        self.sidebar = Sidebar(parent, app=self)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
    
    def _create_device_table(self, parent):
        """ساخت جدول دستگاه‌ها"""
        self.table = DeviceTable(parent, app=self)
        self.table.pack(fill=tk.BOTH, expand=True)
    
    def _create_status_bar(self):
        """ساخت StatusBar"""
        self.statusbar = StatusBar(self.root)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        self.statusbar.set_status("Ready", 'success')
    
    # ================================================================
    # LOAD DATA
    # ================================================================
    
    def _load_initial_data(self):
        """بارگذاری داده‌های اولیه"""
        try:
            self.projects = self.db.load_all_projects()
            
            if self.projects:
                # ============================================================
                # ✅ بازیابی آخرین پروژه فعال
                # ============================================================
                last_active = self.db.get_last_active_project()
                
                if last_active and last_active in self.projects:
                    # پروژه ذخیره‌شده هنوز وجود دارد
                    self.current_project_name = last_active
                    logger.info(f"Restored last active project: '{last_active}'")
                else:
                    # پروژه ذخیره‌شده وجود ندارد → اولین پروژه
                    self.current_project_name = next(iter(self.projects))
                    logger.info(f"Using first project: '{self.current_project_name}'")
                    
                    # اگر نام ذخیره‌شده معتبر نبود، پاکش کن
                    if last_active:
                        self.db.clear_last_active_project()
                
                # ===== انتخاب اولین Section از Revision فعلی =====
                project = self.projects[self.current_project_name]
                current_rev = project.get_current_revision()
                if current_rev and current_rev.sections:
                    self.current_section_name = current_rev.sections[0].name
                else:
                    self.current_section_name = None
            else:
                # ============================================================
                # ✅ دیتابیس خالی → ساخت پروژه پیش‌فرض با ساختار کامل
                # ============================================================
                project = Project("Project 1")
                
                # ساخت Revision پیش‌فرض
                default_revision = project.add_revision("Rev-0")
                project.current_revision_name = "Rev-0"
                
                # ساخت Section پیش‌فرض
                default_section = default_revision.add_section(
                    name="Section 1",
                    description="",
                )
                
                # ذخیره در حافظه
                self.projects["Project 1"] = project
                self.current_project_name = "Project 1"
                self.current_section_name = default_section.name
                
                # ذخیره در دیتابیس
                self.db.save_project(project)
                self.db.set_last_active_project("Project 1")
                
                logger.info("Created default project 'Project 1' (Rev-0, Section 1)")
            
            self._load_component_labels()
            self._refresh_ui()
            
        except Exception as e:
            logger.error(f"Failed to load initial data: {e}", exc_info=True)
            ToastManager.error(f"Failed to load data: {str(e)}")
    
    def _load_component_labels(self):
        try:
            if self.current_project_name:
                self.component_labels = self.db.load_component_labels(self.current_project_name)
            else:
                self.component_labels = COMPONENT_LABELS.copy()
        except Exception as e:
            logger.warning(f"Failed to load component labels: {e}")
            self.component_labels = COMPONENT_LABELS.copy()
    
    # ================================================================
    # REFRESH UI
    # ================================================================
    

    def _refresh_ui(self):
        """به‌روزرسانی کامل UI"""
        
        # ===== Sidebar =====
        self.sidebar.refresh_tree(self.projects)
        
        # ===== Stats =====
        self._update_stats()
        
        # ===== Device Table =====
        section = self.get_current_section()
        if section:
            self.table.load_data(section.devices)
        else:
            self.table.load_data([])

        # ===== ✅ Valves Panel (جدید) =====
        if hasattr(self, 'valves_panel'):
            if section:
                self.valves_panel.refresh()
            else:
                self.valves_panel.table.load_data([])
        
        # ✅ Attachments Panel
        if self.current_project_name:
            self.attachments_panel.set_project(self.current_project_name)
        
        # ============================================================
        # ✅ StatusBar (Context + آمار)
        # ============================================================
        self._update_statusbar()
        
        # ===== Undo/Redo Buttons =====
        self._update_undo_buttons()


    def _refresh_table_only(self):
        """به‌روزرسانی فقط Device Table و Stats (بدون Sidebar)"""
        
        # ===== Stats =====
        self._update_stats()
        
        # ===== Device Table =====
        section = self.get_current_section()
        if section:
            self.table.load_data(section.devices)
        else:
            self.table.load_data([])

        # ===== ✅ Valve Table (جدید) =====
        if hasattr(self, 'valves_panel'):
            if section:
                self.valves_panel.refresh()
            else:
                self.valves_panel.table.load_data([])
        
        # ===== StatusBar (Context + آمار) =====
        self._update_statusbar()
        
        # ===== Undo/Redo =====
        self._update_undo_buttons()

    def _update_statusbar(self):
        """
        به‌روزرسانی StatusBar با Context + آمار
        
        این متد رو در _refresh_ui، _refresh_ui_preserving_tree و 
        _refresh_table_only صدا بزنید تا کد تکرار نشه.
        """
        project = self.get_current_project()
        section = self.get_current_section()
        
        if not project:
            self.statusbar.set_context()
            self.statusbar.update_stats()
            return
        
        # ===== Revision فعلی =====
        current_rev = project.get_current_revision()
        revision_display = f"{current_rev.name} (Current)" if current_rev else "—"
        
        # ===== Context =====
        # ===== Context =====
        self.statusbar.set_context(
            project=project.name,
            revision=revision_display,
            section=section.name if section else "",
        )
        
        # ===== آمار =====
        if section:
            # آمار بخش فعلی
            devices = section.devices
            device_count = len(devices)
            active_count = sum(1 for d in devices if d.get_total_io() > 0)
            
            io_stats = {
                'DI': sum(d.DI for d in devices),
                'DO': sum(d.DO for d in devices),
                'AI': sum(d.AI for d in devices),
                'AO': sum(d.AO for d in devices),
            }
            io_stats['total'] = sum(io_stats.values())
            
            # ✅ آمار Valve ها (اختیاری)
            valves_count = len(getattr(section, 'valves', []))
            # اگر می‌خواهید در StatusBar نشان دهید، این را در آمار اضافه کنید
        else:
            # آمار کل پروژه
            stats = project.get_statistics()
            device_count = stats['total_devices']
            active_count = stats['active_devices']
            io_stats = {
                'DI': stats['total_di'],
                'DO': stats['total_do'],
                'AI': stats['total_ai'],
                'AO': stats['total_ao'],
                'total': stats['total_io'],
            }
        
        self.statusbar.update_stats(
            device_count=device_count,
            active_count=active_count,
            io_stats=io_stats,
        )
    
    def _update_stats(self):
        """به‌روزرسانی آمار"""
        project = self.get_current_project()
        if not project:
            return
        
        stats = project.get_statistics()
        
        self.sidebar.update_stats({
            'sections': stats['total_sections'],
            'devices': stats['total_devices'],
            'active': stats['active_devices'],
            'io': stats['total_io'],
        })
    
    def _update_undo_buttons(self):
        """به‌روزرسانی دکمه‌های Undo/Redo"""
        info = self.history.get_history_info()
        
        if hasattr(self.undo_btn, 'set_enabled'):
            self.undo_btn.set_enabled(info['can_undo'])
        if hasattr(self.redo_btn, 'set_enabled'):
            self.redo_btn.set_enabled(info['can_redo'])
    
    # ================================================================
    # SIDEBAR EVENTS
    # ================================================================
    
    def _on_sidebar_project_selected(self, project_name: str, item: str):
        """
        انتخاب پروژه از Sidebar
        
        ⚠️ نکته: اگر پروژه عوض نشده باشد، فقط toggle می‌کنیم (بدون refresh)
        """
        if not project_name:
            return
        
        # ===== بررسی تغییر واقعی پروژه =====
        if project_name != self.current_project_name:
            # پروژه عوض شده → refresh کامل
            self.switch_to_project(project_name)
            
            # ✅ باز کردن پروژه جدید
            if hasattr(self, 'sidebar') and self.sidebar.tree.exists(item):
                try:
                    self.sidebar.tree.item(item, open=True)
                except:
                    pass
        else:
            # ✅ همان پروژه → فقط toggle
            if hasattr(self, 'sidebar') and self.sidebar.tree.exists(item):
                try:
                    current_open = self.sidebar.tree.item(item, 'open')
                    self.sidebar.tree.item(item, open=not current_open)
                except:
                    pass


    def _on_sidebar_revision_selected(self, project_name: str, revision_name: str, item: str):
        """
        انتخاب Revision از Sidebar
        
        ⚠️ این متد فقط زمانی صدا زده می‌شود که کاربر روی خود Revision کلیک کند،
        نه روی Section یا Device.
        """
        if not project_name or not revision_name:
            return
        
        # ===== تغییر پروژه در صورت نیاز =====
        if project_name != self.current_project_name:
            self.switch_to_project(project_name)
            return  # switch_to_project خودش refresh می‌کند
        
        # ===== سوئیچ به Revision انتخاب شده =====
        project = self.projects.get(project_name)
        if project and project.current_revision_name != revision_name:
            project.current_revision_name = revision_name
            self.db.set_current_revision(project_name, revision_name)
            
            # انتخاب اولین Section از Revision جدید
            current_rev = project.get_current_revision()
            if current_rev and current_rev.sections:
                self.current_section_name = current_rev.sections[0].name
            else:
                self.current_section_name = None
            
            ToastManager.info(f"Switched to {revision_name}")
            
            # ✅ refresh با حفظ state
            self._refresh_ui_preserving_tree()
        
        # ============================================================
        # ✅ باز/بسته کردن خودِ Revision (toggle)
        # ============================================================
        if hasattr(self, 'sidebar') and self.sidebar.tree.exists(item):
            try:
                current_open = self.sidebar.tree.item(item, 'open')
                self.sidebar.tree.item(item, open=not current_open)
            except:
                pass

    def _refresh_ui_preserving_tree(self):
        """
        به‌روزرسانی UI با حفظ حالت باز/بسته درخت
        
        این متد زمانی استفاده می‌شود که نیاز به refresh کامل داریم
        اما نمی‌خواهیم حالت درخت از دست برود.
        """
        # ذخیره انتخاب فعلی
        current_selection = None
        if hasattr(self, 'sidebar') and self.sidebar.tree.selection():
            try:
                sel_item = self.sidebar.tree.selection()[0]
                if self.sidebar.tree.exists(sel_item):
                    current_selection = self.sidebar.tree.item(sel_item, 'values')
            except:
                pass
        
        # ✅ Sidebar با حفظ state
        self.sidebar.refresh_tree(self.projects, preserve_state=True)
        
        # ✅ بازیابی انتخاب
        if current_selection:
            self._restore_tree_selection(current_selection)
        
        # Stats
        self._update_stats()
        
        # Device Table
        section = self.get_current_section()
        if section:
            self.table.load_data(section.devices)
        else:
            self.table.load_data([])

        # ===== ✅ Valve Table (جدید) =====
        if hasattr(self, 'valves_panel'):
            if section:
                self.valves_panel.refresh()
            else:
                self.valves_panel.table.load_data([])
        
        # Attachments
        if self.current_project_name:
            self.attachments_panel.set_project(self.current_project_name)
        
        # StatusBar
        
        # Undo/Redo
        self._update_undo_buttons()
        self._update_statusbar()


    def _restore_tree_selection(self, values):
        """
        بازیابی انتخاب درخت بر اساس values
        """
        if not hasattr(self, 'sidebar') or not values:
            return
        
        values = tuple(values)
        
        def find_item(parent=''):
            for item in self.sidebar.tree.get_children(parent):
                try:
                    item_values = tuple(self.sidebar.tree.item(item, 'values'))
                    if item_values == values:
                        return item
                    
                    # جستجو در فرزندان
                    found = find_item(item)
                    if found:
                        return found
                except:
                    continue
            return None
        
        item = find_item()
        if item:
            try:
                self.sidebar.tree.selection_set(item)
                self.sidebar.tree.see(item)
            except Exception as e:
                logger.debug(f"Failed to restore tree selection: {e}")
            
    def _on_sidebar_section_selected(self, project_name: str, revision_name: str, 
                                    section_name: str, item: str):
        """
        انتخاب سکشن از Sidebar
        
        ⚠️ نکته مهم: از refresh کامل خودداری می‌کنیم تا حالت درخت حفظ شود
        """
        if not project_name or not revision_name or not section_name:
            return
        
        # ===== بررسی تغییر واقعی =====
        needs_table_refresh = False
        needs_full_refresh = False
        
        # ===== تغییر پروژه =====
        if project_name != self.current_project_name:
            self.current_project_name = project_name
            needs_full_refresh = True  # چون پروژه عوض شده، UI باید کامل آپدیت بشه
            needs_table_refresh = True
        
        # ===== تغییر Revision =====
        project = self.projects.get(project_name)
        revision_changed = False
        if project and project.current_revision_name != revision_name:
            project.current_revision_name = revision_name
            self.db.set_current_revision(project_name, revision_name)
            revision_changed = True
            needs_table_refresh = True
            needs_full_refresh = True  # چون Revision عوض شده
        
        # ===== تغییر سکشن =====
        section_changed = False
        if section_name != self.current_section_name:
            self.current_section_name = section_name
            section_changed = True
            needs_table_refresh = True
        
        # ============================================================
        # ✅ به‌روزرسانی هوشمند
        # ============================================================
        if needs_full_refresh:
            # پروژه یا Revision عوض شده → refresh کامل (اما با حفظ state)
            self._refresh_ui_preserving_tree()
        elif needs_table_refresh:
            # فقط سکشن عوض شده → فقط جدول رو آپدیت کن
            self._refresh_table_only()
        
        # باز کردن item (بدون بستن بقیه)
        if hasattr(self, 'sidebar') and self.sidebar.tree.exists(item):
            try:
                self.sidebar.tree.item(item, open=True)
            except:
                pass
    

    def _on_sidebar_device_selected(self, project_name: str, revision_name: str,
                                    section_name: str, device_index: int, item: str):
        """
        انتخاب دستگاه از Sidebar
        
        ⚠️ دستگاه تغییری در Sidebar ایجاد نمی‌کند → فقط انتخاب در جدول
        """
        if not project_name or not revision_name or not section_name:
            return
        
        # ===== تغییر پروژه =====
        if project_name != self.current_project_name:
            self.switch_to_project(project_name)
        
        # ===== تغییر Revision =====
        project = self.projects.get(project_name)
        if project and project.current_revision_name != revision_name:
            project.current_revision_name = revision_name
            self.db.set_current_revision(project_name, revision_name)
        
        # ===== تغییر سکشن =====
        if section_name != self.current_section_name:
            self.current_section_name = section_name
            self._refresh_table_only()  # ✅ فقط جدول
        
        # ===== انتخاب دستگاه در جدول =====
        self._select_device_in_table(device_index)
    
    def _select_device_in_table(self, index: int):
        try:
            children = self.table.tree.get_children()
            if 0 <= index < len(children):
                self.table.tree.selection_set(children[index])
                self.table.tree.focus(children[index])
                self.table.tree.see(children[index])
        except Exception as e:
            logger.debug(f"Failed to select device at index {index}: {e}")
    
    # ================================================================
    # PROJECT MANAGEMENT (از Sidebar)
    # ================================================================
    
    def _rename_project(self, old_name: str, new_name: str):
        """
        تغییر نام پروژه
        
        ⚠️ نکات:
        - اعتبارسنجی کامل
        - منطق دیتابیس در DatabaseManager.rename_project
        - مدیریت خطا با Rollback خودکار
        """
        # ============================================================
        # 1. اعتبارسنجی
        # ============================================================
        if not new_name or not new_name.strip():
            ToastManager.warning("Project name cannot be empty!")
            return
        
        new_name = new_name.strip()
        
        if new_name == old_name:
            return
        
        if old_name not in self.projects:
            ToastManager.error(f"Project '{old_name}' not found!")
            return
        
        if new_name in self.projects:
            ToastManager.warning(f"Project '{new_name}' already exists!")
            return
        
        if len(new_name) > 100:
            ToastManager.warning("Project name is too long (max 100 chars)!")
            return
        
        # ============================================================
        # 2. تغییر در دیتابیس
        # ============================================================
        try:
            success = self.db.rename_project(old_name, new_name)
            
            if not success:
                ToastManager.error("Failed to rename project in database!")
                return
            
            # ============================================================
            # 3. به‌روزرسانی Object در حافظه
            # ============================================================
            project = self.projects.pop(old_name)
            project.name = new_name
            project.updated_at = datetime.now()
            self.projects[new_name] = project
            
            # ============================================================
            # 4. اگر پروژه فعلی بود، نامش را عوض کن
            # ============================================================
            if self.current_project_name == old_name:
                self.current_project_name = new_name
                
                # برچسب‌های کامپوننت
                try:
                    self._load_component_labels()
                except Exception as e:
                    logger.warning(f"Failed to reload labels: {e}")
                
                # Attachments Panel
                try:
                    if hasattr(self, 'attachments_panel'):
                        self.attachments_panel.set_project(new_name)
                except Exception as e:
                    logger.warning(f"Failed to update attachments panel: {e}")
            
            # ============================================================
            # 5. History پاک شود
            # ============================================================
            try:
                self.history.clear_project(old_name)
            except Exception as e:
                logger.debug(f"Failed to clear history: {e}")
            
            # ============================================================
            # 6. Refresh UI
            # ============================================================
            self._refresh_ui_preserving_tree()
            
            ToastManager.success(f"Project renamed: '{old_name}' → '{new_name}'")
            logger.info(f"Project renamed: {old_name} → {new_name}")
            
        except Exception as e:
            logger.error(f"Failed to rename project: {e}", exc_info=True)
            ToastManager.error(f"Failed to rename project: {str(e)}")

    # ================================================================
    # REVISION OPERATIONS (جدید)
    # ================================================================
    
    def _new_revision_dialog(self, project_name: str, copy_from: str = None):
        """
        دیالوگ ساخت Revision جدید
        
        Args:
            project_name: نام پروژه
            copy_from: نام Revision مبدأ (اختیاری)
        """
        if project_name not in self.projects:
            ToastManager.error(f"Project '{project_name}' not found!")
            return
        
        project = self.projects[project_name]
        
        # ===== پیشنهاد نام =====
        existing_names = set(project.get_revision_names())
        counter = 0
        while f"Rev-{counter}" in existing_names:
            counter += 1
        suggested_name = f"Rev-{counter}"
        
        # ===== دیالوگ =====
        from tkinter import simpledialog
        
        title = "New Revision"
        prompt = f"New revision name for '{project_name}':"
        if copy_from:
            prompt += f"\n(Copy from '{copy_from}')"
        
        new_name = simpledialog.askstring(
            title,
            prompt,
            initialvalue=suggested_name,
            parent=self.root,
        )
        
        if not new_name or not new_name.strip():
            return
        
        new_name = new_name.strip()
        
        # ===== بررسی تکراری =====
        if project.get_revision_by_name(new_name):
            ToastManager.warning(f"Revision '{new_name}' already exists!")
            return
        
        # ===== ساخت Revision =====
        try:
            if copy_from:
                # کپی از Revision دیگر
                new_rev = project.copy_revision(copy_from, new_name)
                ToastManager.success(
                    f"Revision '{new_name}' created (copied from '{copy_from}')"
                )
            else:
                # Revision خالی
                new_rev = project.add_revision(new_name)
                ToastManager.success(f"Revision '{new_name}' created (empty)")
            
            # ===== ذخیره در دیتابیس =====
            self.db.save_project(project)
            
            # ===== به‌روزرسانی UI =====
            self._refresh_ui()
            
        except ValueError as e:
            ToastManager.error(str(e))
        except Exception as e:
            ToastManager.error(f"Failed to create revision: {str(e)}")
    
    def _switch_to_revision(self, project_name: str, revision_name: str):
        """سوئیچ به Revision دیگر"""
        if project_name not in self.projects:
            return
        
        project = self.projects[project_name]
        
        if not project.get_revision_by_name(revision_name):
            ToastManager.error(f"Revision '{revision_name}' not found!")
            return
        
        # سوئیچ
        if not project.switch_to_revision(revision_name):
            return
        
        # اگر پروژه فعلی است، UI را به‌روز کن
        if self.current_project_name == project_name:
            # انتخاب اولین Section از Revision جدید
            current_rev = project.get_current_revision()
            if current_rev and current_rev.sections:
                self.current_section_name = current_rev.sections[0].name
            else:
                self.current_section_name = None
            
            self._refresh_ui()
        
        # ذخیره در دیتابیس
        self.db.set_current_revision(project_name, revision_name)
        
        ToastManager.success(f"Switched to '{revision_name}'")
    
    def _delete_revision_with_confirm(self, project_name: str, 
                                       revision_name: str,
                                       force: bool = False):
        """
        حذف Revision (حتی اگر آخرین Revision باشد)
        
        ⚠️ قانون:
        - Revision باید خالی باشد (بدون Section)
        - اگر آخرین Revision باشد، پروژه خالی می‌ماند (راه‌حل B)
        - پروژه خالی قابل حذف است (با _delete_project_with_confirm)
        """
        if project_name not in self.projects:
            return
        
        project = self.projects[project_name]
        
        # ============================================================
        # دریافت Revision
        # ============================================================
        revision = project.get_revision_by_name(revision_name)
        if not revision:
            ToastManager.error(f"Revision '{revision_name}' not found!")
            return
        
        section_count = len(revision.sections)
        is_current = (project.current_revision_name == revision_name)
        
        # ============================================================
        # بررسی محتوا (فقط در حالت غیرآبشاری)
        # ============================================================
        if not force and section_count > 0:
            messagebox.showwarning(
                "Cannot Delete Revision",
                f"Cannot delete revision '{revision_name}'!\n\n"
                f"This revision contains {section_count} section(s).\n\n"
                f"Please delete all sections first.",
                parent=self.root,
            )
            return
        
        # ============================================================
        # تایید
        # ============================================================
        is_last_revision = (len(project.revisions) <= 1)
        
        if force:
            confirm_msg = (
                f"⚠️ DELETE REVISION WITH ALL CONTENT?\n\n"
                f"Revision: '{revision_name}'\n\n"
                f"This will permanently delete:\n"
                f"  • {section_count} section(s)\n\n"
                f"This action CANNOT be undone!"
            )
        elif is_current and is_last_revision:
            confirm_msg = (
                f"Delete last revision '{revision_name}'?\n\n"
                f"⚠️ This is the LAST revision in project '{project_name}'.\n"
                f"The project will become EMPTY.\n\n"
                f"You can delete the empty project later.\n\n"
                f"This action cannot be undone!"
            )
        elif is_current:
            confirm_msg = (
                f"Delete CURRENT revision '{revision_name}'?\n\n"
                f"⚠️ This is the CURRENT revision.\n"
                f"After deletion, another revision will be set as current.\n\n"
                f"This action cannot be undone!"
            )
        else:
            confirm_msg = (
                f"Delete revision '{revision_name}'?\n\n"
                f"This revision is empty (0 sections).\n\n"
                f"This action cannot be undone!"
            )
        
        if not confirm_dialog(
            self.root,
            confirm_msg,
            "Confirm Delete Revision",
            'danger',
            "Delete",
            "Cancel",
        ):
            return
        
        # ============================================================
        # حذف + سوئیچ خودکار
        # ============================================================
        try:
            was_current = is_current
            
            # ===== حذف از Model =====
            success = project.delete_revision(revision_name)
            
            if not success:
                ToastManager.error("Failed to delete revision!")
                return
            
            # ===== اگر Current بود، انتخاب یه Revision دیگه =====
            if was_current and project.revisions:
                new_current = project.revisions[0].name
                project.current_revision_name = new_current
                self.db.set_current_revision(project_name, new_current)
                
                new_rev = project.get_current_revision()
                if new_rev and new_rev.sections:
                    self.current_section_name = new_rev.sections[0].name
                else:
                    self.current_section_name = None
                
                ToastManager.info(f"Current revision switched to '{new_current}'")
            elif was_current and not project.revisions:
                # اگر آخرین Revision حذف شد، پروژه خالی می‌شود
                project.current_revision_name = None
                self.current_section_name = None
                self.db.set_current_revision(project_name, None)
                ToastManager.info("Project is now empty")
            
            # ===== حذف از دیتابیس =====
            self.db.delete_revision(project_name, revision_name)
            self.db.save_project(project)
            
            # ===== به‌روزرسانی UI =====
            if self.current_project_name == project_name:
                self._refresh_ui_preserving_tree()
            else:
                self._refresh_ui()
            
            ToastManager.success(f"Revision '{revision_name}' deleted!")
            
        except Exception as e:
            logger.error(f"Failed to delete revision: {e}", exc_info=True)
            ToastManager.error(f"Failed to delete revision: {str(e)}")
    
    def _copy_all_sections_to_current(self, project_name: str, source_revision: str):
        """کپی همه Section ها از یک Revision به Current"""
        if project_name not in self.projects:
            return
        
        project = self.projects[project_name]
        
        source_rev = project.get_revision_by_name(source_revision)
        if not source_rev:
            ToastManager.error(f"Source revision '{source_revision}' not found!")
            return
        
        current_rev = project.get_current_revision()
        if not current_rev:
            ToastManager.error("No current revision!")
            return
        
        if source_rev.name == current_rev.name:
            ToastManager.warning("Source and target are the same revision!")
            return
        
        if not source_rev.sections:
            ToastManager.info("Source revision has no sections!")
            return
        
        section_count = len(source_rev.sections)
        device_count = len(source_rev.get_all_devices())
        
        if not confirm_dialog(
            self.root,
            f"Copy all sections from '{source_revision}' to '{current_rev.name}'?\n\n"
            f"• Sections: {section_count}\n"
            f"• Devices: {device_count}\n\n"
            f"Existing sections in '{current_rev.name}' will NOT be deleted.",
            "Confirm Copy Sections",
            'question',
            "Copy",
            "Cancel",
        ):
            return
        
        # ذخیره Undo State
        self._save_state()
        
        # کپی Section ها
        copied_count = 0
        for source_section in source_rev.sections:
            # بررسی نام تکراری
            base_name = source_section.name
            new_name = base_name
            counter = 1
            while current_rev.get_section_by_name(new_name):
                new_name = f"{base_name}_Copy{counter}"
                counter += 1
            
            # کپی
            new_section = source_section.copy()
            new_section.name = new_name
            current_rev.sections.append(new_section)
            copied_count += 1
        
        # ذخیره
        self._save_project()
        self._refresh_ui()
        
        ToastManager.success(
            f"Copied {copied_count} section(s) from '{source_revision}' to '{current_rev.name}'!"
        )

    def _rename_revision(self, project_name: str, old_name: str, new_name: str):
        """تغییر نام Revision"""
        if project_name not in self.projects:
            return
        
        project = self.projects[project_name]
        
        if not project.rename_revision(old_name, new_name):
            ToastManager.error(f"Failed to rename revision (name may be duplicate or not found)")
            return
        
        # ذخیره در دیتابیس
        self.db.save_project(project)
        
        # به‌روزرسانی UI
        self._refresh_ui()
        
        ToastManager.success(f"Revision renamed: {old_name} → {new_name}")
    
    def _paste_section_to_revision(self, project_name: str, revision_name: str, section):
        """
        پیست یک Section کپی شده به Revision فعلی
        """
        if project_name not in self.projects:
            return
        
        project = self.projects[project_name]
        
        target_rev = project.get_revision_by_name(revision_name)
        if not target_rev:
            ToastManager.error(f"Target revision '{revision_name}' not found!")
            return
        
        # بررسی نام تکراری
        base_name = section.name
        new_name = base_name
        counter = 1
        while target_rev.get_section_by_name(new_name):
            new_name = f"{base_name}_Copy{counter}"
            counter += 1
        
        # ذخیره Undo State
        self._save_state()
        
        # کپی Section
        new_section = section.copy()
        new_section.name = new_name
        target_rev.sections.append(new_section)
        
        # ذخیره
        self._save_project()
        self._refresh_ui()
        
        ToastManager.success(
            f"Section '{new_name}' pasted to '{revision_name}'!"
        )
    

    def _delete_project_with_confirm(self, project_name: str):
        """
        حذف پروژه (حتی اگر آخرین پروژه باشد)
        
        ⚠️ قانون:
        - پروژه باید خالی باشد (بدون Revision یا Revision خالی)
        - اگر آخرین پروژه باشد، یک پروژه جدید خودکار ساخته می‌شود
        - برنامه هرگز بدون پروژه نمی‌ماند
        """
        if project_name not in self.projects:
            return
        
        project = self.projects[project_name]
        
        # ============================================================
        # بررسی: آیا پروژه واقعاً خالی است؟
        # ============================================================
        has_content = False
        for rev in project.revisions:
            if len(rev.sections) > 0:
                has_content = True
                break
        
        if has_content:
            # شمارش
            total_sections = sum(len(r.sections) for r in project.revisions)
            total_devices = sum(len(r.get_all_devices()) for r in project.revisions)
            
            messagebox.showwarning(
                "Cannot Delete Project",
                f"Cannot delete project '{project_name}'!\n\n"
                f"This project contains:\n"
                f"  • {len(project.revisions)} revision(s)\n"
                f"  • {total_sections} section(s)\n"
                f"  • {total_devices} device(s)\n\n"
                f"Please delete all content first.",
                parent=self.root,
            )
            return
        
        # ============================================================
        # بررسی: آخرین پروژه؟
        # ============================================================
        is_last_project = (len(self.projects) <= 1)
        
        if is_last_project:
            confirm_msg = (
                f"Delete project '{project_name}'?\n\n"
                f"⚠️ This is the LAST project in the application.\n\n"
                f"A new empty project will be created automatically.\n\n"
                f"This action cannot be undone!"
            )
        else:
            confirm_msg = (
                f"Delete empty project '{project_name}'?\n\n"
                f"This project has no content.\n\n"
                f"This action cannot be undone!"
            )
        
        if not confirm_dialog(
            self.root,
            confirm_msg,
            "Confirm Delete Project",
            'danger',
            "Delete",
            "Cancel",
        ):
            return
        
        # ============================================================
        # حذف
        # ============================================================
        try:
            # ===== حذف از دیتابیس =====
            self.db.delete_project(project_name)
            
            # ===== حذف از حافظه =====
            del self.projects[project_name]

            try:
                last_active = self.db.get_last_active_project()
                if last_active == project_name:
                    self.db.clear_last_active_project()
            except Exception as e:
                logger.warning(f"Failed to clear last active project: {e}")
            
            # ============================================================
            # اگر آخرین پروژه بود → ساخت پروژه جدید
            # ============================================================
            if is_last_project or not self.projects:
                new_project = Project("Project 1")
                self.projects["Project 1"] = new_project
                self.current_project_name = "Project 1"
                self.current_section_name = None
                self.db.save_project(new_project)
                
                ToastManager.info("New empty project 'Project 1' created")
            
            # ===== اگر پروژه فعلی حذف شد → سوئیچ =====
            if self.current_project_name == project_name:
                first_project = next(iter(self.projects))
                self.current_project_name = first_project
                project = self.projects[first_project]
                if project.sections:
                    self.current_section_name = project.sections[0].name
                else:
                    self.current_section_name = None
            
            # ===== Refresh UI =====
            self._refresh_ui_preserving_tree()
            
            ToastManager.success(f"Project '{project_name}' deleted!")
            logger.info(f"Project deleted: {project_name}")
            
        except Exception as e:
            logger.error(f"Failed to delete project: {e}", exc_info=True)
            ToastManager.error(f"Failed to delete project: {str(e)}")
    
    def _backup_project_by_name(self, project_name: str):
        """بکاپ پروژه با نام"""
        if project_name not in self.projects:
            ToastManager.error(f"Project '{project_name}' not found!")
            return
        
        original_project = self.current_project_name
        
        try:
            self.current_project_name = project_name
            self._backup_current_project()
        finally:
            self.current_project_name = original_project
    
    def _add_section_to_project(self, project_name: str):
        """افزودن سکشن به پروژه"""
        if project_name not in self.projects:
            ToastManager.error(f"Project '{project_name}' not found!")
            return
        
        name = simpledialog.askstring(
            "New Section",
            f"Section name for '{project_name}':",
            parent=self.root,
        )
        if not name or not name.strip():
            return
        
        name = name.strip()
        project = self.projects[project_name]
        
        if project.get_section_by_name(name):
            ToastManager.warning(f"Section '{name}' already exists!")
            return
        
        description = simpledialog.askstring(
            "Section Description",
            "Description (optional):",
            parent=self.root,
        )
        
        self._save_state()
        project.add_section(name, description or "")
        self._save_project()
        self._refresh_ui()
        
        ToastManager.success(f"Section '{name}' added!")
    
    # ================================================================
    # SECTION MANAGEMENT (از Sidebar)
    # ================================================================
    
    def _rename_section(self, project_name: str, revision_name: str, 
                        old_name: str, new_name: str):
        """تغییر نام سکشن"""
        if project_name not in self.projects:
            return
        
        project = self.projects[project_name]
        revision = project.get_revision_by_name(revision_name)
        
        if not revision:
            return
        
        if revision.get_section_by_name(new_name):
            ToastManager.warning(f"Section '{new_name}' already exists!")
            return
        
        section = revision.get_section_by_name(old_name)
        if not section:
            return
        
        self._save_state()
        section.name = new_name
        
        if (self.current_section_name == old_name and 
            project_name == self.current_project_name and
            revision_name == project.current_revision_name):
            self.current_section_name = new_name
        
        self._save_project()
        self._refresh_ui()
        
        ToastManager.success(f"Section renamed: {old_name} → {new_name}")
    

    def _delete_section_with_confirm(self, project_name: str, revision_name: str, 
                                    section_name: str):
        """
        حذف Section خالی (حتی اگر آخرین Section باشد)
        
        ⚠️ قانون:
        - Section باید خالی باشد (بدون Device)
        - اگر آخرین Section باشد، Revision خالی می‌ماند (راه‌حل B)
        - Revision خالی قابل حذف است (با _delete_revision_with_confirm)
        """
        if project_name not in self.projects:
            return
        
        project = self.projects[project_name]
        revision = project.get_revision_by_name(revision_name)
        
        if not revision:
            ToastManager.error(f"Revision '{revision_name}' not found!")
            return
        
        # ===== دریافت Section =====
        section = revision.get_section_by_name(section_name)
        if not section:
            ToastManager.error(f"Section '{section_name}' not found!")
            return
        
        device_count = len(section.devices)
        
        # ============================================================
        # بررسی: Section باید خالی باشد
        # ============================================================
        if device_count > 0:
            messagebox.showwarning(
                "Cannot Delete Section",
                f"Cannot delete section '{section_name}'!\n\n"
                f"This section contains {device_count} device(s).\n\n"
                f"Please delete all devices first.",
                parent=self.root,
            )
            return
        
        # ============================================================
        # بررسی: آخرین Section؟
        # ============================================================
        is_last_section = (len(revision.sections) <= 1)
        
        if is_last_section:
            # هشدار مخصوص
            confirm_msg = (
                f"Delete last section '{section_name}'?\n\n"
                f"⚠️ This is the LAST section in revision '{revision_name}'.\n"
                f"The revision will become EMPTY.\n\n"
                f"You can delete the empty revision later.\n\n"
                f"This action cannot be undone!"
            )
        else:
            confirm_msg = (
                f"Delete empty section '{section_name}'?\n\n"
                f"This section is empty (0 devices).\n\n"
                f"This action cannot be undone!"
            )
        
        if not confirm_dialog(
            self.root,
            confirm_msg,
            "Confirm Delete Section",
            'danger',
            "Delete",
            "Cancel",
        ):
            return
        
        # ===== حذف =====
        self._save_state()
        revision.delete_section(section_name)
        
        # اگر Section فعلی حذف شد
        if (self.current_section_name == section_name and 
            project_name == self.current_project_name and
            revision_name == project.current_revision_name):
            self.current_section_name = (
                revision.sections[0].name if revision.sections else None
            )
        
        self._save_project()
        
        # ===== به‌روزرسانی UI =====
        if self.current_project_name == project_name:
            self._refresh_ui_preserving_tree()
        else:
            self._refresh_ui()
        
        ToastManager.success(f"Section '{section_name}' deleted!")

    def _delete_last_section_with_revision(self, project_name: str, 
                                            revision_name: str, 
                                            section_name: str):
        """
        حذف آخرین Section + کل Revision (حذف آبشاری)
        
        ⚠️ منطق:
        - چون Revision بدون Section معنی ندارد،
          آخرین Section را نمی‌توان به تنهایی حذف کرد.
        - به‌جای آن، کل Revision با تمام محتوا حذف می‌شود.
        
        Args:
            project_name: نام پروژه
            revision_name: نام Revision
            section_name: نام آخرین Section (برای نمایش)
        """
        if project_name not in self.projects:
            return
        
        project = self.projects[project_name]
        
        # ============================================================
        # بررسی: آخرین Revision نباشد
        # ============================================================
        if len(project.revisions) <= 1:
            messagebox.showwarning(
                "Cannot Delete Last Revision",
                f"Cannot delete section '{section_name}'!\n\n"
                f"This is the last section in the last revision "
                f"of project '{project_name}'.\n\n"
                f"A project must have at least one revision.",
                parent=self.root,
            )
            return
        
        revision = project.get_revision_by_name(revision_name)
        if not revision:
            ToastManager.error(f"Revision '{revision_name}' not found!")
            return
        
        # ============================================================
        # بررسی: Section باید خالی باشد
        # ============================================================
        section = revision.get_section_by_name(section_name)
        if section and len(section.devices) > 0:
            messagebox.showwarning(
                "Cannot Delete Section",
                f"Cannot delete section '{section_name}'!\n\n"
                f"This section contains {len(section.devices)} device(s).\n\n"
                f"Please delete all devices first.",
                parent=self.root,
            )
            return
        
        # ============================================================
        # نمایش اطلاعات به کاربر
        # ============================================================
        section_count = len(revision.sections)
        device_count = len(revision.get_all_devices())
        is_current = (project.current_revision_name == revision_name)
        
        info_lines = [
            f"⚠️ DELETE LAST SECTION + REVISION",
            "",
            f"Section: '{section_name}'",
            f"Revision: '{revision_name}'",
            "",
            "Since a revision must have at least one section,",
            "the entire revision will be deleted.",
            "",
            f"This will permanently delete:",
            f"  • {section_count} section(s)",
            f"  • {device_count} device(s)",
        ]
        
        if is_current:
            info_lines.append("")
            info_lines.append("📌 This is the CURRENT revision.")
            info_lines.append("   Another revision will be set as current.")
        
        info_lines.append("")
        info_lines.append("This action CANNOT be undone!")
        
        if not confirm_dialog(
            self.root,
            "\n".join(info_lines),
            "Confirm Cascading Delete",
            'danger',
            "Delete Everything",
            "Cancel",
        ):
            return
        
        # ============================================================
        # فراخوانی حذف Revision با force=True
        # ============================================================
        self._delete_revision_with_confirm(
            project_name, 
            revision_name, 
            force=True
        )

    
    def _add_device_to_section(self, project_name: str, revision_name: str, section_name: str):
        """افزودن دستگاه به سکشن"""
        if project_name != self.current_project_name:
            self.switch_to_project(project_name)
        
        # سوئیچ به Revision
        project = self.projects.get(project_name)
        if project and project.current_revision_name != revision_name:
            project.current_revision_name = revision_name
            self.db.set_current_revision(project_name, revision_name)
        
        if section_name != self.current_section_name:
            self.current_section_name = section_name
            self._refresh_ui()
        
        self._add_device()
    # ================================================================
    # DEVICE MANAGEMENT (از Sidebar)
    # ================================================================
    
    def _edit_device_from_sidebar(self, project_name: str, revision_name: str, 
                                section_name: str, device_index: int):
        """ویرایش دستگاه از Sidebar"""
        if project_name != self.current_project_name:
            self.switch_to_project(project_name)
        
        project = self.projects.get(project_name)
        if project and project.current_revision_name != revision_name:
            project.current_revision_name = revision_name
            self.db.set_current_revision(project_name, revision_name)
        
        if section_name != self.current_section_name:
            self.current_section_name = section_name
            self._refresh_ui()
        
        self._select_device_in_table(device_index)
        self._edit_device()
    
    def _copy_device_from_sidebar(self, project_name: str, revision_name: str,
                                section_name: str, device_index: int):
        """کپی دستگاه از Sidebar"""
        if project_name != self.current_project_name:
            self.switch_to_project(project_name)
        
        project = self.projects.get(project_name)
        if project and project.current_revision_name != revision_name:
            project.current_revision_name = revision_name
            self.db.set_current_revision(project_name, revision_name)
        
        if section_name != self.current_section_name:
            self.current_section_name = section_name
            self._refresh_ui()
        
        section = self.get_current_section()
        if section and 0 <= device_index < len(section.devices):
            self.copied_motors = [section.devices[device_index].copy()]
            ToastManager.success("Device copied!")

    def _delete_device_from_sidebar(self, project_name: str, revision_name: str,
                                    section_name: str, device_index: int):
        """حذف دستگاه از Sidebar"""
        if project_name != self.current_project_name:
            self.switch_to_project(project_name)
        
        project = self.projects.get(project_name)
        if project and project.current_revision_name != revision_name:
            project.current_revision_name = revision_name
            self.db.set_current_revision(project_name, revision_name)
        
        if section_name != self.current_section_name:
            self.current_section_name = section_name
            self._refresh_ui()
        
        section = self.get_current_section()
        if not section or not (0 <= device_index < len(section.devices)):
            return
        
        device = section.devices[device_index]
        
        if not confirm_dialog(
            self.root,
            f"Delete device '{device.Name or 'Unnamed'}'?",
            "Confirm Delete",
            'danger',
            "Delete",
            "Cancel",
        ):
            return
        
        self._save_state()
        section.devices.pop(device_index)
        self._save_project()
        self._refresh_ui()
        
        ToastManager.success(f"Device deleted!")
    
    # ================================================================
    # HELPERS
    # ================================================================
    
    def get_current_project(self) -> Optional[Project]:
        """پروژه جاری"""
        if self.current_project_name and self.current_project_name in self.projects:
            return self.projects[self.current_project_name]
        return None
    
    def get_current_section(self) -> Optional[ProjectSection]:
        """بخش جاری"""
        project = self.get_current_project()
        if project and self.current_section_name:
            return project.get_section_by_name(self.current_section_name)
        return None
    
    def get_all_devices(self) -> List[Motor]:
        """همه دستگاه‌ها"""
        project = self.get_current_project()
        return project.get_all_devices() if project else []
    
    def get_current_component_labels(self):
        """برچسب‌های کامپوننت جاری"""
        if self.current_project_name and self.current_project_name in self.projects:
            project = self.projects[self.current_project_name]
            return project.get_component_labels(self.db)
        return COMPONENT_LABELS.copy()
    
    def _save_state(self):
        """ذخیره حالت برای Undo"""
        project = self.get_current_project()
        if project:
            current_rev = project.get_current_revision()
            if current_rev:
                self.history.push_state(
                    project.name, 
                    current_rev.sections,
                    revision_name=current_rev.name,  # ← اضافه
                )
            self._update_undo_buttons()
    
    def _save_project(self):
        """ذخیره پروژه"""
        project = self.get_current_project()
        if project:
            self.db.save_project(project)
    
    # ================================================================
    # PROJECT OPERATIONS
    # ================================================================
    
    def _new_project(self, name: str = None):
        """
        پروژه جدید با ساختار کامل
        
        ✅ ساختار خودکار:
            Project
              └── Rev-0 (Revision پیش‌فرض)
                    └── Section 1 (Section پیش‌فرض)
        """
        # ============================================================
        # 1. دریافت نام
        # ============================================================
        if not name:
            name = simpledialog.askstring(
                "New Project",
                "Enter project name:",
                parent=self.root,
            )
            if not name or not name.strip():
                return
            name = name.strip()
        
        # ============================================================
        # 2. بررسی تکراری
        # ============================================================
        if name in self.projects:
            ToastManager.warning(f"Project '{name}' already exists!")
            return
        
        # ============================================================
        # 3. ساخت پروژه
        # ============================================================
        try:
            project = Project(name)
            
            # ============================================================
            # ✅ 4. ساخت Revision پیش‌فرض
            # ============================================================
            default_revision = project.add_revision("Rev-0")
            project.current_revision_name = "Rev-0"
            
            # ============================================================
            # ✅ 5. ساخت Section پیش‌فرض
            # ============================================================
            default_section = default_revision.add_section(
                name="Section 1",
                description="",
            )
            
            # ============================================================
            # 6. تنظیم Project در حافظه
            # ============================================================
            self.projects[name] = project
            self.current_project_name = name
            self.current_section_name = default_section.name

            try:
                self.db.set_last_active_project(name)
            except Exception as e:
                logger.warning(f"Failed to save last active project: {e}")

            # ============================================================
            # 7. ذخیره در دیتابیس
            # ============================================================
            self.db.save_project(project)
            
            # ============================================================
            # 8. بارگذاری برچسب‌ها و به‌روزرسانی UI
            # ============================================================
            self._load_component_labels()
            self._refresh_ui()
            self._save_state()
            
            # ============================================================
            # 9. پیام موفقیت
            # ============================================================
            ToastManager.success(
                f"Project '{name}' created with Rev-0 and Section 1"
            )
            logger.info(f"New project created: '{name}' (Rev-0, Section 1)")
            
        except Exception as e:
            logger.error(f"Failed to create project: {e}", exc_info=True)
            ToastManager.error(f"Failed to create project: {str(e)}")
    
    def switch_to_project(self, name: str):
        """تغییر پروژه"""
        if name in self.projects:
            self.current_project_name = name
            project = self.projects[name]
            
            if project.sections:
                self.current_section_name = project.sections[0].name
            else:
                self.current_section_name = None
            
            # ============================================================
            # ✅ ذخیره آخرین پروژه فعال
            # ============================================================
            try:
                self.db.set_last_active_project(name)
                logger.debug(f"Saved last active project: '{name}'")
            except Exception as e:
                logger.warning(f"Failed to save last active project: {e}")
            
            self._load_component_labels()
            self._refresh_ui()
        else:
            ToastManager.error(f"Project '{name}' not found!")
    
    def _open_project_manager(self):
        """مدیریت پروژه‌ها"""
        dialog = ProjectManagerDialog(self.root, self)
        dialog.show()
    
    # ================================================================
    # SECTION OPERATIONS
    # ================================================================
    
    def _manage_sections(self):
        """مدیریت بخش‌ها"""
        SectionManagerDialog(self.root, self).show()
    
    def switch_to_section(self, name: str):
        """تغییر بخش"""
        self.current_section_name = name
        self._refresh_ui()
    
    # ================================================================
    # DEVICE OPERATIONS
    # ================================================================
    
    def _add_device(self):
        """افزودن دستگاه"""
        section = self.get_current_section()
        if not section:
            ToastManager.warning("Please select a section first!")
            return
        
        dialog = DeviceDialog(self.root, self, is_new=True, section=section)
        dialog.show()
        self._refresh_ui()
    
    def _edit_device(self):
        """ویرایش دستگاه"""
        indices = self.table.get_selected_indices()
        if not indices:
            ToastManager.warning("Please select a device to edit!")
            return
        
        if len(indices) > 1:
            ToastManager.warning("Please select only one device!")
            return
        
        section = self.get_current_section()
        if section and indices[0] < len(section.devices):
            dialog = DeviceDialog(
                self.root, self,
                motor=section.devices[indices[0]],
                is_new=False,
            )
            dialog.show()
            self._refresh_ui()
    
    def _delete_device(self):
        """حذف دستگاه"""
        indices = self.table.get_selected_indices()
        if not indices:
            ToastManager.warning("Please select a device to delete!")
            return
        
        if not confirm_dialog(
            self.root,
            f"Delete {len(indices)} device(s)?\n\nThis action can be undone.",
            "Confirm Delete",
            'danger',
            "Delete",
            "Cancel",
        ):
            return
        
        self._save_state()
        section = self.get_current_section()
        if section:
            for idx in sorted(indices, reverse=True):
                if idx < len(section.devices):
                    section.devices.pop(idx)
            
            self._save_project()
            self._refresh_ui()
            ToastManager.success(f"{len(indices)} device(s) deleted!")
    
    def _copy_device(self):
        """کپی دستگاه"""
        indices = self.table.get_selected_indices()
        if not indices:
            ToastManager.warning("Please select a device to copy!")
            return
        
        section = self.get_current_section()
        if section:
            self.copied_motors = []
            for idx in indices:
                if idx < len(section.devices):
                    self.copied_motors.append(section.devices[idx].copy())
            
            ToastManager.success(f"{len(self.copied_motors)} device(s) copied!")
    
    def _paste_device(self):
        """چسباندن دستگاه‌های کپی شده"""
        if not self.copied_motors:
            ToastManager.warning("No devices to paste!")
            return
        
        section = self.get_current_section()
        if not section:
            ToastManager.warning("No section selected!")
            return
        
        self._save_state()
        
        for motor in self.copied_motors:
            new_motor = motor.copy()
            # ✅ نام اصلی حفظ می‌شود - "(Copy)" اضافه نمی‌شود
            new_motor.recalculate_io()
            section.devices.append(new_motor)
        
        self._save_project()
        self._refresh_ui()
        ToastManager.success(f"{len(self.copied_motors)} device(s) pasted!")
    
    def _move_device_up(self):
        """جابجایی دستگاه به بالا"""
        indices = self.table.get_selected_indices()
        if not indices:
            return
        
        section = self.get_current_section()
        if not section:
            return
        
        idx = indices[0]
        if idx <= 0:
            return
        
        self._save_state()
        section.devices[idx], section.devices[idx-1] = section.devices[idx-1], section.devices[idx]
        self._save_project()
        self._refresh_ui()
        
        # انتخاب مجدد
        self._select_device_in_table(idx - 1)
    
    def _move_device_down(self):
        """جابجایی دستگاه به پایین"""
        indices = self.table.get_selected_indices()
        if not indices:
            return
        
        section = self.get_current_section()
        if not section:
            return
        
        idx = indices[0]
        if idx >= len(section.devices) - 1:
            return
        
        self._save_state()
        section.devices[idx], section.devices[idx+1] = section.devices[idx+1], section.devices[idx]
        self._save_project()
        self._refresh_ui()
        
        # انتخاب مجدد
        self._select_device_in_table(idx + 1)

    # ================================================================
    # ✅ VALVE OPERATIONS (Delegate to ValvesPanel)
    # ================================================================
    def _check_valve_duplicates(self):
        """بررسی نام‌های تکراری شیرها (Delegate)"""
        if hasattr(self, 'valves_panel'):
            self.valves_panel.check_duplicate_names()
    
    def _fix_valve_duplicates(self):
        """اصلاح نام‌های تکراری شیرها (Delegate)"""
        if hasattr(self, 'valves_panel'):
            self.valves_panel.fix_duplicate_names()

    def _copy_valve(self):
        """کپی شیرها (Delegate)"""
        if hasattr(self, 'valves_panel'):
            self.valves_panel.copy_valves()
    
    def _paste_valve(self):
        """چسباندن شیرها (Delegate)"""
        if hasattr(self, 'valves_panel'):
            self.valves_panel.paste_valves()
    
    def _add_valve(self):
        """افزودن شیر (Delegate)"""
        if hasattr(self, 'valves_panel'):
            self.valves_panel.add_valve()
    
    def _edit_valve(self):
        """ویرایش شیر (Delegate)"""
        if hasattr(self, 'valves_panel'):
            self.valves_panel.edit_valve()
    
    def _delete_valve(self):
        """حذف شیر (Delegate)"""
        if hasattr(self, 'valves_panel'):
            self.valves_panel.delete_valves()
    
    def _move_valve_up(self):
        """جابجایی شیر به بالا (Delegate)"""
        if hasattr(self, 'valves_panel'):
            self.valves_panel.move_valve_up()
    
    def _move_valve_down(self):
        """جابجایی شیر به پایین (Delegate)"""
        if hasattr(self, 'valves_panel'):
            self.valves_panel.move_valve_down()
    
    def _duplicate_valves(self):
        """کپی شیرها (Delegate)"""
        if hasattr(self, 'valves_panel'):
            self.valves_panel.duplicate_valves()

    def _show_valve_statistics(self):
        """نمایش آمار شیرها"""
        if not hasattr(self, 'valves_panel'):
            ToastManager.warning("Valves panel not available!")
            return
        
        stats = self.valves_panel.get_statistics()
        
        if stats['total'] == 0:
            ToastManager.info("No valves in current section.")
            return
        
        # ===== ساخت گزارش =====
        report = "🚰 VALVE STATISTICS\n"
        report += "=" * 60 + "\n\n"
        report += f"📊 Total Valves: {stats['total']}\n\n"
        
        # By Type
        if stats['by_type']:
            report += "📋 By Type:\n"
            for vt, count in sorted(stats['by_type'].items()):
                report += f"  • {vt}: {count}\n"
            report += "\n"
        
        # By Circuit
        if stats['by_circuit']:
            report += "🔌 By Circuit:\n"
            for circuit, count in sorted(stats['by_circuit'].items()):
                report += f"  • {circuit}: {count}\n"
            report += "\n"
        
        # Warnings
        if stats['with_warnings'] > 0:
            report += f"⚠️  Valves with Warnings: {stats['with_warnings']}\n"
        
        messagebox.showinfo("Valve Statistics", report)

    def _import_proposal(self):
        """Import پروپوزال از Word"""
        try:
            from gui.import_proposal_dialog import ImportProposalDialog
            dialog = ImportProposalDialog(self.root, self)
            dialog.show()
        except Exception as e:
            logger.error(f"Failed to open import dialog: {e}", exc_info=True)
            ToastManager.error(f"خطا در باز کردن دیالوگ: {e}")


    def _manage_proposal_templates(self):
        """مدیریت قالب‌های پروپوزال"""
        try:
            from gui.import_proposal_dialog import ImportProposalDialog
            dialog = ImportProposalDialog(self.root, self)
            # مستقیم به تب قالب‌ها برود
            dialog._show_templates()
            dialog.show()
        except Exception as e:
            logger.error(f"Failed to open templates dialog: {e}", exc_info=True)
            ToastManager.error(f"خطا: {e}")
    # ================================================================
    # ✅ VALVE OPERATIONS — Export (Delegate to ValvesPanel)
    # ================================================================
    
    def _export_valves_excel(self):
        """Export Valves به Excel (Delegate)"""
        if hasattr(self, 'valves_panel'):
            self.valves_panel.export_to_excel()
        else:
            ToastManager.warning("Valves panel not available!")
    
    def _reorder_devices(self):
        """مرتب‌سازی دستی دستگاه‌ها"""
        section = self.get_current_section()
        if not section:
            ToastManager.warning("No section selected!")
            return
        
        if len(section.devices) < 2:
            ToastManager.info("Need at least 2 devices to reorder.")
            return
        
        DeviceReorderDialog(self.root, self, section).show()

    def _check_duplicate_names(self):
        """
        بررسی نام‌های تکراری در بخش جاری و نمایش گزارش
        """
        from collections import defaultdict
        
        section = self.get_current_section()
        if not section:
            ToastManager.warning("Please select a section first!")
            return
        
        if not section.devices:
            ToastManager.info("No devices in this section!")
            return
        
        # ============================================================
        # پیدا کردن نام‌های تکراری
        # ============================================================
        name_groups = defaultdict(list)
        
        for idx, device in enumerate(section.devices):
            name = (device.Name or "Unnamed").strip() or "Unnamed"
            
            name_groups[name].append({
                'index': idx,
                'name': device.Name or "Unnamed",
                'description': device.Description or 'No description',
                'info': device.INFO or '',
                'di': device.DI,
                'do': device.DO,
                'ai': device.AI,
                'ao': device.AO,
                'total_io': device.get_total_io(),
            })
        
        # فیلتر: فقط نام‌های تکراری
        duplicates = {
            name: devices
            for name, devices in name_groups.items()
            if len(devices) > 1
        }
        
        # ============================================================
        # ساخت گزارش
        # ============================================================
        project = self.get_current_project()
        project_name = project.name if project else "Unknown"
        
        report = "🔍 DUPLICATE NAME REPORT\n"
        report += "=" * 70 + "\n\n"
        report += f"📁 Project: {project_name}\n"
        report += f"📂 Section: {section.name}\n"
        report += f"🔢 Total Devices: {len(section.devices)}\n"
        report += f"📝 Unique Names: {len(name_groups)}\n"
        report += "=" * 70 + "\n\n"
        
        if not duplicates:
            # ===== بدون تکراری =====
            report += "✅ NO DUPLICATES FOUND!\n\n"
            report += f"All {len(section.devices)} device(s) have unique names.\n"
            
            messagebox.showinfo(
                "🔍 Duplicate Names Check",
                report
            )
            ToastManager.success("No duplicates found!")
            return
        
        # ===== با تکراری =====
        total_duplicated_devices = sum(len(devices) for devices in duplicates.values())
        
        report += f"❌ FOUND {len(duplicates)} DUPLICATE GROUP(S)\n"
        report += f"⚠️  Affected Devices: {total_duplicated_devices}\n"
        report += "=" * 70 + "\n\n"
        
        for i, (name, devices) in enumerate(sorted(duplicates.items()), 1):
            report += f"┌─ [{i}] Name: \"{name}\"  ({len(devices)} devices)\n"
            report += "│\n"
            
            for j, device in enumerate(devices, 1):
                report += f"│  {j}. Row #{device['index'] + 1}\n"
                report += f"│     Description: {device['description']}\n"
                if device['info']:
                    report += f"│     INFO: {device['info']}\n"
                report += f"│     I/O: DI={device['di']}  DO={device['do']}  "
                report += f"AI={device['ai']}  AO={device['ao']}  "
                report += f"(Total: {device['total_io']})\n"
                report += "│\n"
            
            report += "└" + "─" * 68 + "\n\n"
        
        # ===== راهنما =====
        report += "=" * 70 + "\n"
        report += "💡 RECOMMENDATIONS:\n"
        report += "-" * 70 + "\n"
        report += "• Rename manually (Edit Device)\n"
        report += "• Use Ctrl+Shift+D for auto-fix\n"
        report += "• Use unique naming (P5a/P5b or P5/P6/P7)\n"
        report += "=" * 70 + "\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # ============================================================
        # نمایش گزارش
        # ============================================================
        self._show_duplicate_report_window(report, duplicates, section.name)
        
        ToastManager.warning(
            f"Found {len(duplicates)} duplicate group(s)!"
        )

    def _validate_project(self):
        """
        اعتبارسنجی پروژه و نمایش خطاها
        
        بررسی می‌کند:
        - تعداد کامپوننت‌های متصل به PU (FS, VSD) با PU برابر باشند
        - (در آینده: بررسی‌های بیشتر)
        """
        try:
            from core.validation_errors import validate_project_components
        except ImportError as e:
            ToastManager.error(
                f"Module 'validation_errors' not found!\n"
                f"Please create core/validation_errors.py first."
            )
           
            return
        
        project = self.get_current_project()
        if not project:
            ToastManager.warning("Please select a project first!")
            return
        
        if not project.sections:
            ToastManager.warning("Project has no sections!")
            return
        
        devices = project.get_all_devices()
        if not devices:
            ToastManager.warning("Project has no devices!")
            return
        
        # ============================================================
        # اعتبارسنجی
        # ============================================================
        collector = validate_project_components(project)
        
        # ============================================================
        # اگر خطایی نیست
        # ============================================================
        if collector.count() == 0:
            ToastManager.success("✅ No validation errors found!")
            
            report = "✅ VALIDATION PASSED\n"
            report += "=" * 75 + "\n\n"
            report += f"📁 Project: {project.name}\n"
            report += f"📂 Sections: {len(project.sections)}\n"
            report += f"🔢 Devices: {len(devices)}\n"
            report += f"📊 Total I/O: {project.get_total_io()}\n\n"
            report += "=" * 75 + "\n"
            report += "🎉 All validation checks passed!\n"
            report += "=" * 75 + "\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            self._show_text_report_window(
                report=report,
                title=f"Validation Report - {project.name}",
                section_name=f"Validation_{project.name}",
                icon='✅',
                header_color=get_color('success'),
            )
            return
        
        # ============================================================
        # ساخت گزارش
        # ============================================================
        report = "⚠️ VALIDATION REPORT\n"
        report += "=" * 75 + "\n\n"
        report += f"📁 Project: {project.name}\n"
        report += f"📂 Sections: {len(project.sections)}\n"
        report += f"🔢 Devices: {len(devices)}\n"
        report += f"📊 Total I/O: {project.get_total_io()}\n"
        report += f"❗ Total Issues: {collector.count()}\n"
        report += "=" * 75 + "\n\n"
        
        # ============================================================
        # گروه‌بندی بر اساس severity
        # ============================================================
        from core.validation_errors import ErrorSeverity
        
        severity_info = [
            (ErrorSeverity.CRITICAL, '🔴', 'CRITICAL'),
            (ErrorSeverity.ERROR,    '🟠', 'ERROR'),
            (ErrorSeverity.WARNING,  '🟡', 'WARNING'),
            (ErrorSeverity.INFO,     '🔵', 'INFO'),
        ]
        
        for severity, icon, label in severity_info:
            errors = collector.get_by_severity(severity)
            if not errors:
                continue
            
            report += f"{icon} {label} ({len(errors)})\n"
            report += "-" * 75 + "\n"
            
            for i, err in enumerate(errors, 1):
                report += f"  [{i}] {err.title}\n"
                report += f"      Code: {err.code}\n"
                
                # پیام چند خطی
                for line in err.message.split('\n'):
                    if line.strip():
                        report += f"      {line.strip()}\n"
                
                if err.suggestion:
                    report += f"      💡 {err.suggestion}\n"
                
                report += "\n"
            
            report += "\n"
        
        # ============================================================
        # خلاصه
        # ============================================================
        report += "=" * 75 + "\n"
        report += "📌 SUMMARY\n"
        report += "-" * 75 + "\n"
        
        critical_count = len(collector.get_by_severity(ErrorSeverity.CRITICAL))
        error_count = len(collector.get_by_severity(ErrorSeverity.ERROR))
        warning_count = len(collector.get_by_severity(ErrorSeverity.WARNING))
        info_count = len(collector.get_by_severity(ErrorSeverity.INFO))
        
        report += f"  🔴 Critical: {critical_count}\n"
        report += f"  🟠 Error:    {error_count}\n"
        report += f"  🟡 Warning:  {warning_count}\n"
        report += f"  🔵 Info:     {info_count}\n"
        report += f"  ─────────────────\n"
        report += f"  📊 Total:    {collector.count()}\n\n"
        
        report += "=" * 75 + "\n"
        report += "💡 TIP: Fix these issues before exporting reports\n"
        report += "         to ensure accuracy and consistency.\n"
        report += "=" * 75 + "\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # ============================================================
        # Toast
        # ============================================================
        if collector.has_errors():
            ToastManager.error(f"Found {collector.count()} validation issue(s)!")
        elif collector.has_warnings():
            ToastManager.warning(f"Found {collector.count()} warning(s)")
        else:
            ToastManager.info(f"Found {collector.count()} info message(s)")
        
        # ============================================================
        # نمایش گزارش
        # ============================================================
        header_color = get_color('danger') if collector.has_errors() else get_color('warning')
        
        self._show_text_report_window(
            report=report,
            title=f"Validation Report - {project.name}",
            section_name=f"Validation_{project.name}",
            icon='⚠️',
            header_color=header_color,
        )

    def _show_duplicate_report_window(self, report: str, duplicates: dict, section_name: str):
        """نمایش گزارش تکراری‌ها در یک پنجره اختصاصی با قابلیت کپی"""
        
        win = tk.Toplevel(self.root)
        win.title(f"🔍 Duplicate Names - {section_name}")
        win.geometry("800x600")
        win.transient(self.root)
        win.grab_set()
        win.configure(bg=get_color('bg_app'))
        
        # مرکز کردن
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
        y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")
        
        # ===== Header =====
        header = tk.Frame(win, bg=get_color('bg_surface'), height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        has_duplicates = len(duplicates) > 0
        header_color = get_color('danger') if has_duplicates else get_color('success')
        header_icon = '🔴' if has_duplicates else '✅'
        
        tk.Label(
            header,
            text=f"{header_icon} Duplicate Names Report",
            font=font('h2'),
            bg=get_color('bg_surface'),
            fg=header_color,
            anchor='w',
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=sp('lg'))
        
        # ===== Info Bar =====
        info_frame = tk.Frame(win, bg=get_color('bg_app'))
        info_frame.pack(fill=tk.X, padx=sp('lg'), pady=sp('md'))
        
        if has_duplicates:
            info_text = f"⚠️  Found {len(duplicates)} duplicate group(s) in section '{section_name}'"
            info_color = get_color('danger')
        else:
            info_text = f"✅ No duplicates found in section '{section_name}'"
            info_color = get_color('success')
        
        tk.Label(
            info_frame,
            text=info_text,
            font=font('body_bold'),
            bg=get_color('bg_app'),
            fg=info_color,
            anchor='w',
        ).pack(fill=tk.X)
        
        # ===== Separator =====
        separator = tk.Frame(win, bg=get_color('border_default'), height=1)
        separator.pack(fill=tk.X, padx=sp('lg'), pady=sp('sm'))
        
        # ===== Text Area =====
        text_frame = tk.Frame(win, bg=get_color('bg_surface'))
        text_frame.pack(fill=tk.BOTH, expand=True, padx=sp('lg'), pady=sp('md'))
        
        text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
            relief='flat',
            border=0,
            padx=sp('md'),
            pady=sp('md'),
        )
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert('1.0', report)
        text_area.config(state='disabled')
        
        # ===== Footer =====
        footer = tk.Frame(win, bg=get_color('bg_surface'), height=60)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        btn_frame = tk.Frame(footer, bg=get_color('bg_surface'))
        btn_frame.pack(side=tk.RIGHT, padx=sp('lg'), pady=sp('md'))
        
        # ===== Close =====
        PrimaryButton(
            btn_frame,
            text="Close",
            command=win.destroy,
        ).pack(side=tk.RIGHT)
        
        # ===== Copy to Clipboard =====
        def copy_to_clipboard():
            win.clipboard_clear()
            win.clipboard_append(report)
            ToastManager.success("Report copied to clipboard!")
        
        SecondaryButton(
            btn_frame,
            text="📋 Copy",
            command=copy_to_clipboard,
        ).pack(side=tk.RIGHT, padx=(0, sp('sm')))
        
        # ===== Save to File =====
        if has_duplicates:
            def save_to_file():
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                    title="Save Duplicate Report",
                    initialfile=f"Duplicates_{section_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                )
                
                if file_path:
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(report)
                        ToastManager.success(f"Report saved!")
                    except Exception as e:
                        ToastManager.error(f"Failed to save: {str(e)}")
            
            SecondaryButton(
                btn_frame,
                text="💾 Save",
                command=save_to_file,
            ).pack(side=tk.RIGHT, padx=(0, sp('sm')))

    def _show_text_report_window(
        self,
        report: str,
        title: str,
        section_name: str = "",
        icon: str = '📄',
        header_color: str = None,
    ):
        """
        نمایش گزارش متنی در پنجره اختصاصی با اسکرول عمودی و افقی
        
        Args:
            report: متن گزارش
            title: عنوان پنجره
            section_name: نام بخش (برای نام‌گذاری فایل ذخیره)
            icon: آیکون هدر
            header_color: رنگ هدر (اختیاری، پیش‌فرض primary)
        """
        
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("950x700")
        win.minsize(600, 400)
        win.transient(self.root)
        win.grab_set()
        win.configure(bg=get_color('bg_app'))
        
        # مرکز کردن
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
        y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")
        
        # ============================================================
        # Header
        # ============================================================
        header = tk.Frame(win, bg=get_color('bg_surface'), height=55)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        color = header_color or get_color('primary')
        
        tk.Label(
            header,
            text=f"{icon} {title}",
            font=font('h2'),
            bg=get_color('bg_surface'),
            fg=color,
            anchor='w',
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=sp('lg'))
        
        # ============================================================
        # Separator
        # ============================================================
        separator = tk.Frame(win, bg=get_color('border_default'), height=1)
        separator.pack(fill=tk.X, padx=sp('lg'), pady=sp('sm'))
        
        # ============================================================
        # Text Area با Scroll
        # ============================================================
        text_frame = tk.Frame(win, bg=get_color('bg_surface'))
        text_frame.pack(fill=tk.BOTH, expand=True, padx=sp('lg'), pady=(0, sp('md')))
        
        # ✅ Scroll عمودی
        v_scrollbar = ttk.Scrollbar(text_frame, orient='vertical')
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ✅ Scroll افقی
        h_scrollbar = ttk.Scrollbar(text_frame, orient='horizontal')
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # ✅ Text Widget
        text_area = tk.Text(
            text_frame,
            wrap=tk.NONE,
            font=('Consolas', 10),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
            relief='flat',
            border=0,
            padx=sp('md'),
            pady=sp('md'),
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            insertbackground=get_color('text_primary'),
            selectbackground=get_color('primary'),
            selectforeground='white',
        )
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=text_area.yview)
        h_scrollbar.config(command=text_area.xview)
        
        # درج محتوا
        text_area.insert('1.0', report)
        text_area.config(state='disabled')
        
        # ============================================================
        # Mouse Wheel Support
        # ============================================================
        def on_mousewheel(event):
            text_area.yview_scroll(int(-1 * (event.delta / 120)), 'units')
            return "break"
        
        def on_shift_mousewheel(event):
            text_area.xview_scroll(int(-1 * (event.delta / 120)), 'units')
            return "break"
        
        def on_linux_mousewheel(event):
            if event.num == 4:
                text_area.yview_scroll(-1, 'units')
            elif event.num == 5:
                text_area.yview_scroll(1, 'units')
            return "break"
        
        text_area.bind('<MouseWheel>', on_mousewheel)
        text_area.bind('<Shift-MouseWheel>', on_shift_mousewheel)
        text_area.bind('<Button-4>', on_linux_mousewheel)
        text_area.bind('<Button-5>', on_linux_mousewheel)
        
        # ============================================================
        # Keyboard Shortcuts
        # ============================================================
        def on_ctrl_a(event):
            text_area.tag_add('sel', '1.0', 'end')
            return "break"
        
        def on_ctrl_c(event):
            try:
                selected = text_area.get('sel.first', 'sel.last')
                win.clipboard_clear()
                win.clipboard_append(selected)
            except tk.TclError:
                pass
            return "break"
        
        text_area.bind('<Control-a>', on_ctrl_a)
        text_area.bind('<Control-c>', on_ctrl_c)
        
        # ============================================================
        # Footer
        # ============================================================
        footer = tk.Frame(win, bg=get_color('bg_surface'), height=60)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        btn_frame = tk.Frame(footer, bg=get_color('bg_surface'))
        btn_frame.pack(side=tk.RIGHT, padx=sp('lg'), pady=sp('md'))
        
        # ===== Close =====
        PrimaryButton(
            btn_frame,
            text="Close",
            command=win.destroy,
        ).pack(side=tk.RIGHT)
        
        # ===== Copy to Clipboard =====
        def copy_to_clipboard():
            win.clipboard_clear()
            win.clipboard_append(report)
            ToastManager.success("Report copied to clipboard!")
        
        SecondaryButton(
            btn_frame,
            text="📋 Copy",
            command=copy_to_clipboard,
        ).pack(side=tk.RIGHT, padx=(0, sp('sm')))
        
        # ===== Save to File =====
        def save_to_file():
            safe_name = "".join(
                c if c.isalnum() or c in " _-" else "_"
                for c in (section_name or title)
            ).strip() or "Report"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Report",
                initialfile=f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(report)
                    ToastManager.success(f"Report saved!")
                except Exception as e:
                    ToastManager.error(f"Failed to save: {str(e)}")
        
        SecondaryButton(
            btn_frame,
            text="💾 Save",
            command=save_to_file,
        ).pack(side=tk.RIGHT, padx=(0, sp('sm')))
        
        # ============================================================
        # Focus
        # ============================================================
        win.focus_set()

    
    def _fix_duplicate_names(self):
        """
        اصلاح نام‌های تکراری با پر کردن شماره‌های خالی
        
        مثال:
            ورودی: PT-1, PT-2, PT-5, PT, PT
            خروجی: PT-1, PT-2, PT-3, PT-4, PT-5
            
        توضیح:
            - شماره‌های 3 و 4 خالی هستند → استفاده می‌شوند
            - اگر شماره خالی کافی نبود → از max+1 ادامه می‌دهد
        """
        import re
        
        section = self.get_current_section()
        if not section:
            ToastManager.warning("No section selected!")
            return
        
        if not section.devices:
            ToastManager.info("No devices in this section!")
            return
        
        # ============================================================
        # 1. پیدا کردن نام‌های تکراری
        # ============================================================
        name_count = {}
        for device in section.devices:
            name = (device.Name or "Unnamed").strip() or "Unnamed"
            if name not in name_count:
                name_count[name] = []
            name_count[name].append(device)
        
        duplicates = {name: devices for name, devices in name_count.items() if len(devices) > 1}
        
        if not duplicates:
            ToastManager.success("All device names are unique!")
            return
        
        duplicate_count = sum(len(devices) for devices in duplicates.values())
        
        if not confirm_dialog(
            self.root,
            f"Found {len(duplicates)} duplicate name(s) affecting {duplicate_count} devices.\n\n"
            f"Fix automatically by filling gaps in numbering?",
            "Fix Duplicate Names",
            'warning',
            "Fix",
            "Cancel",
        ):
            return
        
        self._save_state()
        
        # ============================================================
        # 2. جمع‌آوری شماره‌های موجود برای هر prefix
        # ============================================================
        # مثال: prefix_numbers = {"PT": {1, 2, 5}, "DTS": {1, 3}}
        prefix_numbers = {}
        
        for device in section.devices:
            device_name = (device.Name or "").strip()
            if not device_name:
                continue
            
            match = re.match(r'^(.*?)-(\d+)$', device_name)
            if match:
                prefix = match.group(1).strip()
                num = int(match.group(2))
                
                if prefix not in prefix_numbers:
                    prefix_numbers[prefix] = set()
                prefix_numbers[prefix].add(num)
        
        # ============================================================
        # 3. مرتب‌سازی گروه‌های تکراری (برای پردازش قابل پیش‌بینی)
        # ============================================================
        # گروه‌هایی که name آنها "PREFIX-NUM" است، ابتدا پردازش شوند
        # تا شماره‌های موجود آنها در prefix_numbers ثبت شود
        sorted_duplicates = sorted(
            duplicates.items(),
            key=lambda x: (0 if '-' in x[0] else 1, x[0])
        )
        
        # ============================================================
        # 4. اصلاح تکراری‌ها
        # ============================================================
        fixed_count = 0
        fix_log = []
        
        for name, devices in sorted_duplicates:
            # ===== پیدا کردن base_prefix =====
            match = re.match(r'^(.*?)-(\d+)$', name)
            
            if match:
                # name مثل "PT-1" است
                base_prefix = match.group(1).strip()
                # شماره‌ای که در این گروه وجود دارد (مثلاً 1)
                original_num = int(match.group(2))
            else:
                # name فقط "PT" است (بدون شماره)
                base_prefix = name.strip()
                original_num = None
            
            # ===== دریافت شماره‌های موجود برای این prefix =====
            if base_prefix not in prefix_numbers:
                prefix_numbers[base_prefix] = set()
            
            existing_numbers = prefix_numbers[base_prefix]
            
            # ===== تعداد شماره‌های لازم =====
            needed = len(devices)
            
            # ===== پیدا کردن شماره‌های خالی =====
            # از 1 شروع کن و هر شماره‌ای که در existing_numbers نیست را بردار
            available_numbers = []
            candidate = 1
            max_search = 10000  # محدودیت برای جلوگیری از حلقه بی‌نهایت
            
            while len(available_numbers) < needed and candidate <= max_search:
                if candidate not in existing_numbers:
                    available_numbers.append(candidate)
                candidate += 1
            
            # ===== اگر شماره خالی کافی نبود، از max+1 ادامه بده =====
            if len(available_numbers) < needed:
                max_existing = max(existing_numbers) if existing_numbers else 0
                next_num = max_existing + 1
                
                while len(available_numbers) < needed:
                    if next_num not in existing_numbers:
                        available_numbers.append(next_num)
                    next_num += 1
            
            # ===== اصلاح نام‌ها =====
            for i, device in enumerate(devices):
                new_num = available_numbers[i]
                new_name = f"{base_prefix}-{new_num}"
                
                old_name = device.Name
                device.Name = new_name
                fixed_count += 1
                
                # ===== به‌روزرسانی شماره‌های موجود =====
                existing_numbers.add(new_num)
                
                fix_log.append(f"  • '{old_name}' → '{new_name}'")
        
        # ============================================================
        # 5. ذخیره و نمایش نتیجه
        # ============================================================
        self._save_project()
        self._refresh_ui()
        
        # ===== نمایش گزارش =====
        result_msg = f"✅ Fixed {fixed_count} device name(s)!\n\n"
        result_msg += "Changes:\n"
        result_msg += "\n".join(fix_log[:30])
        
        if len(fix_log) > 30:
            result_msg += f"\n\n... and {len(fix_log) - 30} more"
        
        messagebox.showinfo("✅ Fix Duplicate Names", result_msg)
        ToastManager.success(f"Fixed {fixed_count} device name(s)!")
    
    # ================================================================
    # UNDO / REDO
    # ================================================================
    
    def _undo(self):
        """Undo (پشتیبانی از Revision)"""
        state = self.history.undo()
        if not state:
            return
        
        project_name = state['project_name']
        revision_name = state.get('revision_name')      # ✅ جدید
        sections = state['sections']
        
        if project_name not in self.projects:
            return
        
        project = self.projects[project_name]
        
        # ============================================================
        # ✅ اعمال روی Revision درست
        # ============================================================
        if revision_name:
            # Undo روی یک Revision خاص
            revision = project.get_revision_by_name(revision_name)
            if revision:
                revision.sections = sections
                
                # بررسی: آیا در حال حاضر روی این Revision هستیم؟
                if (self.current_project_name == project_name and 
                    project.current_revision_name == revision_name):
                    # نیاز به refresh
                    self._refresh_ui()
                
                # ذخیره
                self.db.save_project(project)
                self._update_undo_buttons()
                ToastManager.info(f"Undo successful ({revision_name})")
            else:
                ToastManager.warning(f"Revision '{revision_name}' not found for undo")
        else:
            # Backward Compatibility (state قدیمی بدون revision_name)
            project.sections = sections
            
            if self.current_project_name == project_name:
                self._refresh_ui()
            
            self.db.save_project(project)
            self._update_undo_buttons()
            ToastManager.info("Undo successful")


    def _redo(self):
        """Redo (پشتیبانی از Revision)"""
        state = self.history.redo()
        if not state:
            return
        
        project_name = state['project_name']
        revision_name = state.get('revision_name')      # ✅ جدید
        sections = state['sections']
        
        if project_name not in self.projects:
            return
        
        project = self.projects[project_name]
        
        # ============================================================
        # ✅ اعمال روی Revision درست
        # ============================================================
        if revision_name:
            revision = project.get_revision_by_name(revision_name)
            if revision:
                revision.sections = sections
                
                if (self.current_project_name == project_name and 
                    project.current_revision_name == revision_name):
                    self._refresh_ui()
                
                self.db.save_project(project)
                self._update_undo_buttons()
                ToastManager.info(f"Redo successful ({revision_name})")
            else:
                ToastManager.warning(f"Revision '{revision_name}' not found for redo")
        else:
            # Backward Compatibility
            project.sections = sections
            
            if self.current_project_name == project_name:
                self._refresh_ui()
            
            self.db.save_project(project)
            self._update_undo_buttons()
            ToastManager.info("Redo successful")
    
    # ================================================================
    # TEMPLATE OPERATIONS
    # ================================================================
    
    def _create_template(self):
        """ذخیره به عنوان تمپلیت"""
        indices = self.table.get_selected_indices()
        if not indices:
            ToastManager.warning("Please select devices first!")
            return
        
        section = self.get_current_section()
        selected = [section.devices[i] for i in indices if i < len(section.devices)]
        
        name = simpledialog.askstring(
            "New Template",
            "Template name:",
            parent=self.root,
        )
        if not name or not name.strip():
            return
        
        project = self.get_current_project()
        success = self.template_manager.create_template_from_selected(
            name=name.strip(),
            devices=selected,
            source_project=project.name if project else '',
            source_section=section.name if section else '',
        )
        
        if success:
            ToastManager.success(f"Template '{name}' saved!")
        else:
            ToastManager.error("Failed to save template!")
    
    def _apply_template(self):
        """اعمال تمپلیت"""
        from gui.template_dialogs import TemplateManagerDialog
        
        dialog = TemplateManagerDialog(self.root, self)
        dialog.show()
    
    def _create_info_group_from_template(self, template_name: str):
        """ایجاد گروه INFO از قالب"""
        template = self.template_manager.get_template(template_name)
        if not template:
            ToastManager.error(f"Template '{template_name}' not found!")
            return
        
        group_name = simpledialog.askstring(
            "Create INFO Group",
            f"Enter group name for '{template_name}':",
            initialvalue=f"{template_name}-1",
            parent=self.root,
        )
        
        if not group_name or not group_name.strip():
            return
        
        group_name = group_name.strip()
        
        devices = self.template_manager.generate_devices(template_name, group_name)
        
        if not devices:
            ToastManager.error("Failed to generate devices from template!")
            return
        
        section = self.get_current_section()
        if not section:
            ToastManager.error("Please select a section first!")
            return
        
        self._save_state()
        
        for motor in devices:
            section.devices.append(motor)
        
        self._save_project()
        self._refresh_ui()
        
        ToastManager.success(f"Created {len(devices)} devices from template!")
    
    # ================================================================
    # AI & LEARNING
    # ================================================================
    
    def _get_learning_engine(self):
        """دریافت موتور یادگیری"""
        if self._learning_engine is None:
            try:
                from ai.learning_engine import LearningEngine
                self._learning_engine = LearningEngine(self.db, self)
            except ImportError:
                ToastManager.warning("AI module not available!")
                return None
        return self._learning_engine
    
    def _get_ai_assistant(self):
        """دریافت دستیار AI"""
        if self._ai_assistant is None:
            try:
                from ai.ai_assistant import AIProjectAssistant
                self._ai_assistant = AIProjectAssistant(self.db, self)
            except ImportError:
                ToastManager.warning("AI Assistant not available!")
                return None
        return self._ai_assistant
    

    def _learn_project(self):
        """یادگیری از پروژه فعلی (همه Revision ها)"""
        project = self.get_current_project()
        if not project:
            ToastManager.warning("Please select a project first!")
            return
        
        if not project.revisions:
            ToastManager.warning("Project has no revisions!")
            return
        
        # ===== شمارش Revision ها =====
        revision_count = len(project.revisions)
        total_devices = sum(len(r.get_all_devices()) for r in project.revisions)
        
        if total_devices == 0:
            ToastManager.warning("Project has no devices in any revision!")
            return
        
        # ===== تایید =====
        if not confirm_dialog(
            self.root,
            f"Learn from '{project.name}'?\n\n"
            f"This will analyze:\n"
            f"  • {revision_count} revision(s)\n"
            f"  • {total_devices} total device(s)",
            "Learn from Project",
            'question',
            "Learn",
            "Cancel",
        ):
            return
        
        try:
            engine = self._get_learning_engine()
            if not engine:
                return
            
            # ✅ یادگیری از همه Revision ها
            engine.learn_from_project(project, revision_name=None)
            
            # ===== تحلیل =====
            analysis = engine.analyze_project(project)
            
            # ===== نمایش نتیجه =====
            result = f"""
    📚 Learning Complete: {project.name}

    ✅ Analyzed {revision_count} revision(s)!

    Results:
    • Total Revisions: {revision_count}
    • Total Devices: {total_devices}
    • Total I/O: {analysis.get('total_io', 0)}
    • Avg I/O/Device: {analysis.get('avg_io_per_device', 0):.1f}

    Revisions Analyzed:
    """
            
            for rev in project.revisions:
                dev_count = len(rev.get_all_devices())
                io_count = rev.get_total_io()
                marker = "📌" if rev.name == project.current_revision_name else "📎"
                result += f"  {marker} {rev.name}: {dev_count} devices, {io_count} I/O\n"
            
            result += "\nTop Components:\n"
            for comp, count in sorted(analysis.get('component_usage', {}).items(), 
                                    key=lambda x: x[1], reverse=True)[:5]:
                label = COMPONENT_LABELS.get(comp, {}).get('fa', comp)
                result += f"• {label}: {count}\n"
            
            ToastManager.success(f"Learned from {project.name} ({revision_count} revisions)!")
            
            messagebox.showinfo("✅ Learning Success", result)
            
        except Exception as e:
            logger.error(f"Learning failed: {e}", exc_info=True)
            ToastManager.error(f"Learning failed: {str(e)}")


    def _learn_all_projects(self):
        """✅ یادگیری از همه پروژه‌ها و همه Revision ها"""
        if not self.projects:
            ToastManager.warning("No projects available!")
            return
        
        # ===== محاسبه آمار =====
        total_revisions = sum(len(p.revisions) for p in self.projects.values())
        total_devices = sum(
            len(r.get_all_devices()) 
            for p in self.projects.values() 
            for r in p.revisions
        )
        
        if total_devices == 0:
            ToastManager.warning("No devices found in any project!")
            return
        
        # ===== تایید =====
        if not confirm_dialog(
            self.root,
            f"Learn from ALL projects?\n\n"
            f"This will analyze:\n"
            f"  • {len(self.projects)} project(s)\n"
            f"  • {total_revisions} revision(s)\n"
            f"  • {total_devices} total device(s)\n\n"
            f"This may take a few moments.",
            "Learn from All Projects",
            'question',
            "Learn All",
            "Cancel",
        ):
            return
        
        try:
            engine = self._get_learning_engine()
            if not engine:
                return
            
            # ✅ یادگیری از همه
            stats = engine.learn_from_all_projects(self.projects)
            
            # ===== نمایش نتیجه =====
            result = f"""
    🧠 Learning Complete - ALL PROJECTS

    ✅ Analyzed {stats['successful']} revision(s)!
    ❌ Failed: {stats['failed']}

    Statistics:
    • Projects: {stats['total_projects']}
    • Revisions: {stats['total_revisions']}
    • Devices: {stats['total_devices']}
    • I/O: {stats['total_io']}
    """
            
            if stats['errors']:
                result += f"\n⚠️ Errors ({len(stats['errors'])}):\n"
                for err in stats['errors'][:5]:
                    result += f"  • {err}\n"
                if len(stats['errors']) > 5:
                    result += f"  ... and {len(stats['errors']) - 5} more\n"
            
            ToastManager.success(
                f"Learned from {stats['successful']} revisions across "
                f"{stats['total_projects']} projects!"
            )
            
            messagebox.showinfo("🧠 Learning All Complete", result)
            
        except Exception as e:
            logger.error(f"Learning all failed: {e}", exc_info=True)
            ToastManager.error(f"Learning failed: {str(e)}")
    
    def _predict_components(self):
        """پیش‌بینی کامپوننت‌ها"""
        project = self.get_current_project()
        if not project:
            ToastManager.warning("Please select a project first!")
            return
        
        devices = project.get_all_devices()
        
        try:
            engine = self._get_learning_engine()
            if not engine:
                return
            
            predictions = engine.predict_component_needs(devices)
            
            if not predictions:
                ToastManager.info("Not enough data for predictions. Run 'Learn' on more projects!")
                return
            
            result = f"🔮 Predictions for {project.name}\n\n"
            result += f"Devices: {len(devices)}\n\n"
            result += "Suggested Components:\n\n"
            
            for pred in predictions:
                emoji = "🔴" if pred['priority'] == 'high' else "🟡"
                result += f"{emoji} {pred['label']}\n"
                result += f"   Reason: {pred['reason']}\n\n"
            
            messagebox.showinfo("🔮 Predictions", result)
            
        except Exception as e:
            ToastManager.error(f"Prediction failed: {str(e)}")
    
    def _optimize_io(self):
        """بهینه‌سازی I/O - نسخه ساده (بدون LearningEngine)"""
        project = self.get_current_project()
        if not project:
            ToastManager.warning("Please select a project first!")
            return
        
        section = self.get_current_section()
        if not section:
            ToastManager.warning("Please select a section first!")
            return
        
        devices = section.devices
        if not devices:
            ToastManager.warning("Section has no devices!")
            return
        
        # ============================================================
        # محاسبه I/O
        # ============================================================
        current_io = {'DI': 0, 'DO': 0, 'AI': 0, 'AO': 0}
        for device in devices:
            current_io['DI'] += device.DI
            current_io['DO'] += device.DO
            current_io['AI'] += device.AI
            current_io['AO'] += device.AO
        
        total_io = sum(current_io.values())
        
        # ============================================================
        # پیشنهادات ساده (بدون AI)
        # ============================================================
        suggestions = []
        
        # ===== پیشنهاد ۱: تعادل I/O =====
        if current_io['DI'] > current_io['DO'] * 2:
            suggestions.append({
                'priority': 'medium',
                'message': f"DI ({current_io['DI']}) بسیار بیشتر از DO ({current_io['DO']}) است",
                'suggestion': "بررسی کنید آیا برخی DI ها قابل تبدیل به DO هستند",
            })
        
        if current_io['DO'] > current_io['DI'] * 2:
            suggestions.append({
                'priority': 'medium',
                'message': f"DO ({current_io['DO']}) بسیار بیشتر از DI ({current_io['DI']}) است",
                'suggestion': "بررسی کنید آیا برخی DO ها قابل تبدیل به DI هستند",
            })
        
        # ===== پیشنهاد ۲: نسبت AI/AO =====
        if current_io['AI'] + current_io['AO'] > 0:
            ratio = (current_io['AI'] + current_io['AO']) / total_io * 100
            if ratio > 50:
                suggestions.append({
                    'priority': 'high',
                    'message': f"نسبت I/O آنالوگ ({ratio:.1f}%) بالاست",
                    'suggestion': "بررسی کنید آیا می‌توان برخی سیگنال‌های آنالوگ را دیجیتال کرد",
                })
        
        # ===== پیشنهاد ۳: اگر تعداد Device زیاد است =====
        if len(devices) > 50:
            suggestions.append({
                'priority': 'info',
                'message': f"تعداد دستگاه‌ها ({len(devices)}) بالاست",
                'suggestion': "می‌توانید Section را به چند بخش تقسیم کنید",
            })
        
        # ===== اگر هیچ پیشنهادی نیست =====
        if not suggestions:
            suggestions.append({
                'priority': 'info',
                'message': "توزیع I/O در وضعیت متعادل است",
                'suggestion': "نیازی به بهینه‌سازی نیست",
            })
        
        # ============================================================
        # ساخت گزارش
        # ============================================================
        report = "⚡ I/O OPTIMIZATION REPORT\n"
        report += "=" * 75 + "\n\n"
        
        report += f"📂 Section: {section.name}\n"
        report += f"🔢 Devices: {len(devices)}\n\n"
        
        # ===== Current I/O =====
        report += "┌─ 📊 CURRENT I/O DISTRIBUTION\n"
        report += "│\n"
        report += f"│  • DI (Digital Input):   {current_io['DI']:>5}\n"
        report += f"│  • DO (Digital Output):  {current_io['DO']:>5}\n"
        report += f"│  • AI (Analog Input):    {current_io['AI']:>5}\n"
        report += f"│  • AO (Analog Output):   {current_io['AO']:>5}\n"
        report += f"│  ─────────────────────────────\n"
        report += f"│  • TOTAL:                {total_io:>5}\n"
        report += "│\n"
        report += "└" + "─" * 73 + "\n\n"
        
        # ===== Suggestions =====
        report += "┌─ 💡 SUGGESTIONS\n"
        report += "│\n"
        
        for i, suggestion in enumerate(suggestions, 1):
            priority = suggestion.get('priority', 'info')
            
            icon = {
                'high':   '🔴',
                'medium': '🟡',
                'low':    '🔵',
                'info':   '✅',
            }.get(priority, 'ℹ️')
            
            report += f"│  {icon} [{priority.upper()}] Suggestion #{i}\n"
            report += f"│     {suggestion['message']}\n"
            report += f"│     → {suggestion['suggestion']}\n"
            report += "│\n"
        
        report += "└" + "─" * 73 + "\n\n"
        
        report += "=" * 75 + "\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # ============================================================
        # نمایش
        # ============================================================
        self._show_text_report_window(
            report=report,
            title=f"Optimize I/O - {section.name}",
            section_name=f"I/O_{section.name}",
            icon='⚡',
            header_color=get_color('warning'),
        )
    
    def _show_learning_stats(self):
        """نمایش آمار یادگیری - با پنجره اختصاصی"""
        try:
            engine = self._get_learning_engine()
            if not engine:
                return
            
            stats = engine.get_statistics()
            
            # ============================================================
            # ساخت گزارش
            # ============================================================
            report = "📊 LEARNING STATISTICS\n"
            report += "=" * 75 + "\n\n"
            
            # ===== Overall Stats =====
            report += "┌─ 📈 OVERALL STATISTICS\n"
            report += "│\n"
            report += f"│  • Projects Analyzed:     {stats['total_projects_analyzed']}\n"
            report += f"│  • Components Learned:    {stats['total_components_learned']}\n"
            report += f"│  • I/O Patterns:          {stats['total_io_patterns']}\n"
            report += f"│  • Equipment Types:       {stats['total_equipment_types']}\n"
            report += "│\n"
            report += "└" + "─" * 73 + "\n\n"
            
            # ===== Most Common Components =====
            if stats['most_common_components']:
                report += "┌─ 🔧 MOST COMMON COMPONENTS\n"
                report += "│\n"
                
                for i, comp in enumerate(stats['most_common_components'], 1):
                    label = comp.get('label', comp.get('component', '?'))
                    count = comp.get('count', 0)
                    report += f"│  {i}. {label:<30} {count:>5} uses\n"
                
                report += "│\n"
                report += "└" + "─" * 73 + "\n\n"
            
            # ===== Top Equipment Types =====
            if stats.get('top_equipment_types'):
                report += "┌─ 🏗️ TOP EQUIPMENT TYPES\n"
                report += "│\n"
                
                for i, equip in enumerate(stats['top_equipment_types'], 1):
                    type_name = equip.get('type', '?')
                    count = equip.get('count', 0)
                    report += f"│  {i}. {type_name:<30} {count:>5} devices\n"
                
                report += "│\n"
                report += "└" + "─" * 73 + "\n\n"
            
            # ===== Most Common I/O Pattern =====
            if stats.get('most_common_io_pattern'):
                pattern = stats['most_common_io_pattern']
                report += "┌─ 📊 MOST COMMON I/O PATTERN\n"
                report += "│\n"
                report += f"│  Equipment Type:  {pattern.get('equipment_type', '?')}\n"
                report += f"│  I/O Pattern:     {pattern.get('pattern', '?')}\n"
                report += f"│  Count:           {pattern.get('count', 0)} uses\n"
                
                if pattern.get('components'):
                    comps = pattern['components'][:10]
                    report += f"│  Components:      {', '.join(comps)}\n"
                
                report += "│\n"
                report += "└" + "─" * 73 + "\n\n"
            
            # ===== No Data Case =====
            if stats['total_projects_analyzed'] == 0:
                report += "⚠️  NO LEARNING DATA YET\n\n"
                report += "To build learning data:\n"
                report += "  1. Open a project with devices\n"
                report += "  2. Go to AI → Learn from Project\n"
                report += "  3. Repeat with more projects\n"
                report += "  4. Come back here to see statistics\n\n"
            
            report += "=" * 75 + "\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # ============================================================
            # نمایش
            # ============================================================
            self._show_text_report_window(
                report=report,
                title="Learning Statistics",
                section_name="Learning_Stats",
                icon='📊',
                header_color=get_color('success'),
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Stats failed: {e}", exc_info=True)
            traceback.print_exc()
            ToastManager.error(f"Stats failed: {str(e)}")
    
    def _find_similar_projects(self):
        """پروژه‌های مشابه - با پنجره اختصاصی و اسکرول"""
        project = self.get_current_project()
        if not project:
            ToastManager.warning("Please select a project first!")
            return
        
        try:
            engine = self._get_learning_engine()
            if not engine:
                return
            
            similar = engine._find_similar_projects(project)
            
            if not similar:
                ToastManager.info("No similar projects found!")
                return
            
            # ============================================================
            # ساخت گزارش متنی
            # ============================================================
            report = "🔗 SIMILAR PROJECTS REPORT\n"
            report += "=" * 70 + "\n\n"
            
            report += f"📁 Current Project: {project.name}\n"
            report += f"🔢 Total Devices: {len(project.get_all_devices())}\n"
            report += f"📊 Total I/O: {project.get_total_io()}\n"
            report += f"📝 Found: {len(similar)} similar section(s)\n"
            report += "=" * 70 + "\n\n"
            
            for i, proj in enumerate(similar, 1):
                similarity = proj['similarity']
                
                # آیکون بر اساس شباهت
                if similarity >= 70:
                    icon = "🟢"
                    level = "HIGH"
                elif similarity >= 40:
                    icon = "🟡"
                    level = "MEDIUM"
                else:
                    icon = "🔵"
                    level = "LOW"
                
                report += f"┌─ [{i}] {icon} {proj['project_name']}  ({level}: {similarity}%)\n"
                report += "│\n"
                report += f"│  📊 Similarity Breakdown:\n"
                report += f"│     • Component Match: {proj['component_similarity']}%\n"
                report += f"│     • I/O Match:       {proj['io_similarity']}%\n"
                report += f"│\n"
                report += f"│  📈 Section Info:\n"
                report += f"│     • Total I/O:    {proj['io_total']}\n"
                report += f"│     • Devices:      {proj['devices_count']}\n"
                
                if proj.get('equipment_types'):
                    types = ', '.join(proj['equipment_types'][:5])
                    report += f"│     • Equipment:    {types}\n"
                
                report += "│\n"
                
                # کامپوننت‌های مشترک
                if proj.get('common_components'):
                    report += f"│  ✅ Common Components ({len(proj['common_components'])}):\n"
                    
                    # نمایش به صورت چند ستونی
                    common = proj['common_components']
                    for j in range(0, len(common), 8):
                        chunk = common[j:j+8]
                        report += f"│     {', '.join(chunk)}\n"
                    report += "│\n"
                
                # کامپوننت‌های اضافی
                if proj.get('unique_components'):
                    report += f"│  ➕ Unique to this Section ({len(proj['unique_components'])}):\n"
                    
                    unique = proj['unique_components']
                    for j in range(0, len(unique), 8):
                        chunk = unique[j:j+8]
                        report += f"│     {', '.join(chunk)}\n"
                    report += "│\n"
                
                report += "└" + "─" * 68 + "\n\n"
            
            report += "=" * 70 + "\n"
            report += "💡 TIP: Similar sections can be used as reference\n"
            report += "         for templates and component selection.\n"
            report += "=" * 70 + "\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # ============================================================
            # نمایش در پنجره اختصاصی
            # ============================================================
            self._show_text_report_window(
                report=report,
                title=f"🔗 Similar Projects - {project.name}",
                section_name=project.name,
                icon='🔗',
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Failed: {e}", exc_info=True)
            ToastManager.error(f"Failed: {str(e)}")
    
    def _get_recommendations(self):
        """توصیه‌های کلی - با پنجره اختصاصی"""
        project = self.get_current_project()
        
        try:
            engine = self._get_learning_engine()
            if not engine:
                return
            
            practices = engine._get_best_practices(project)
            
            # ============================================================
            # ساخت گزارش
            # ============================================================
            report = "💡 BEST PRACTICES & RECOMMENDATIONS\n"
            report += "=" * 75 + "\n\n"
            
            if project:
                report += f"📁 Project: {project.name}\n"
                report += f"🔢 Devices: {len(project.get_all_devices())}\n"
                report += f"📊 Total I/O: {project.get_total_io()}\n"
                report += "=" * 75 + "\n\n"
            
            for i, practice in enumerate(practices, 1):
                report += f"[{i:02d}] {practice}\n\n"
            
            report += "=" * 75 + "\n"
            report += "💡 TIP: These are general engineering best practices.\n"
            report += "         Apply them to improve your project quality.\n"
            report += "=" * 75 + "\n"
            report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # ============================================================
            # نمایش
            # ============================================================
            self._show_text_report_window(
                report=report,
                title="Recommendations",
                section_name="Recommendations",
                icon='💡',
                header_color=get_color('warning'),
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Failed: {e}", exc_info=True)
            traceback.print_exc()
            ToastManager.error(f"Failed: {str(e)}")
    
    def _open_ai_assistant(self):
        """باز کردن دستیار AI"""
        try:
            assistant = self._get_ai_assistant()
            if assistant:
                assistant.start_conversation()
        except Exception as e:
            ToastManager.error(f"AI Assistant failed: {str(e)}")
    
    # ================================================================
    # EXPORT
    # ================================================================
    
    def _export_excel(self):
        """خروجی Excel"""
        try:
            from export.excel_exporter import ExcelExporter
            exporter = ExcelExporter(self)
            result = exporter.export_full_report()
            logger.info(f"Excel export completed: {result}")
        except Exception as e:
            logger.error(f"Excel export failed: {e}", exc_info=True)
            messagebox.showerror(
                "Excel Export Error",
                f"Failed to export Excel:\n\n{str(e)}"
            )


    def _export_pdf(self):
        """خروجی PDF"""
        try:
            from export.pdf_exporter import PDFExporter
            exporter = PDFExporter(self)
            result = exporter.export_full_report()
            logger.info(f"PDF export completed: {result}")
        except Exception as e:
            logger.error(f"PDF export failed: {e}", exc_info=True)
            messagebox.showerror(
                "PDF Export Error",
                f"Failed to export PDF:\n\n{str(e)}"
            )

    def _switch_to_attachments(self):
        """سوئیچ به Tab پیوست‌ها"""
        try:
            if hasattr(self, 'notebook') and hasattr(self, 'attachments_tab'):
                self.notebook.select(self.attachments_tab)
                # Refresh پیوست‌ها
                if hasattr(self, 'attachments_panel'):
                    self.attachments_panel.refresh()
            else:
                ToastManager.warning("Attachments panel not available!")
        except Exception as e:
            logger.error(f"Failed to switch to attachments: {e}", exc_info=True)
            ToastManager.error(f"Failed to open attachments: {e}")
    
    # ================================================================
    # BACKUP
    # ================================================================
    
    def _backup_current_project(self):
        """بکاپ پروژه"""
        project = self.get_current_project()
        if not project:
            ToastManager.warning("No project selected!")
            return
        
        backup_dir = self.db.get_project_backup_path()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"Project_{project.name}_{timestamp}.json"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Project Backup", "*.json")],
            initialdir=backup_dir,
            initialfile=default_filename,
        )
        
        if file_path and self.db.backup_project(project.name, file_path):
            ToastManager.success(f"Project backed up!")
    
    def _restore_project(self):
        """بازیابی پروژه"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Project Backup", "*.json")],
            title="Select Project Backup",
        )
        
        if file_path and self.db.restore_project(file_path):
            self.projects = self.db.load_all_projects()
            self._refresh_ui()
            ToastManager.success("Project restored!")

    def _backup_current_project_full(self):
        """بکاپ کامل پروژه (دیتابیس + Attachments)"""
        project = self.get_current_project()
        if not project:
            ToastManager.warning("No project selected!")
            return
        
        # ===== مسیر پیش‌فرض =====
        backup_dir = self.db.get_project_backup_path()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"Project_{project.name}_{timestamp}_Full.zip"
        
        # ===== دیالوگ ذخیره =====
        file_path = filedialog.asksaveasfilename(
            title="Save Full Project Backup",
            defaultextension=".zip",
            filetypes=[("Zip files", "*.zip"), ("All files", "*.*")],
            initialdir=backup_dir,
            initialfile=default_filename,
        )
        
        if not file_path:
            return
        
        # ===== نمایش وضعیت =====
        ToastManager.info("Creating full backup...")
        
        # ===== بکاپ =====
        success = self.db.backup_project_full(
            project_name=project.name,
            backup_zip_path=file_path,
            attachment_manager=self.attachment_manager,
        )
        
        if success:
            ToastManager.success(f"Full backup created: {os.path.basename(file_path)}")
            logger.info(f"Full backup: {file_path}")
        else:
            ToastManager.error("Failed to create full backup!")


    def _restore_project_full(self):
        """بازیابی کامل پروژه (دیتابیس + Attachments)"""
        # ===== دیالوگ انتخاب فایل =====
        file_path = filedialog.askopenfilename(
            title="Select Full Project Backup",
            filetypes=[("Zip files", "*.zip"), ("All files", "*.*")],
        )
        
        if not file_path:
            return
        
        # ===== تایید =====
        if not confirm_dialog(
            self.root,
            f"Restore project from:\n{os.path.basename(file_path)}\n\n"
            f"This will restore the project AND its attachments.\n\n"
            f"A new project name will be used if the original exists.\n\n"
            f"Continue?",
            "Confirm Restore",
            'question',
            "Restore",
            "Cancel",
        ):
            return
        
        # ===== بازیابی =====
        ToastManager.info("Restoring project...")
        
        success = self.db.restore_project_full(
            backup_zip_path=file_path,
            attachment_manager=self.attachment_manager,
        )
        
        if success:
            # ===== بارگذاری مجدد =====
            self.projects = self.db.load_all_projects()
            self._refresh_ui()
            ToastManager.success("Project restored successfully!")
        else:
            ToastManager.error("Failed to restore project!")


    # ================================================================
    # DATABASE BACKUP / RESTORE
    # ================================================================

    def _backup_database(self):
        """بکاپ کل دیتابیس"""
        from tkinter import filedialog
        
        default_filename = f"IO_List_Generator_DB_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite Database", "*.db"), ("All files", "*.*")],
            title="Backup Database",
            initialfile=default_filename,
        )
        
        if not file_path:
            return
        
        if self.db.backup_database(file_path):
            ToastManager.success(f"Database backed up successfully!")
        else:
            ToastManager.error("Failed to backup database!")


    def _restore_database(self):
        """بازگردانی کل دیتابیس"""
        import shutil
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            filetypes=[("SQLite Database", "*.db"), ("All files", "*.*")],
            title="Select Database Backup",
        )
        
        if not file_path:
            return
        
        # تایید
        if not confirm_dialog(
            self.root,
            f"⚠️ WARNING: This will REPLACE the current database!\n\n"
            f"Backup file: {os.path.basename(file_path)}\n"
            f"Target: {self.db.db_path}\n\n"
            f"All current data will be LOST.\n\n"
            f"Continue?",
            "Confirm Restore Database",
            'danger',
            "Restore",
            "Cancel",
        ):
            return
        
        try:
            # بستن اتصال فعلی
            self.db.close_connection()
            
            # کپی فایل بکاپ
            shutil.copy2(file_path, self.db.db_path)
            
            # بازسازی اتصال
            from core import DatabaseManager
            self.db = DatabaseManager(self.db.db_path)
            
            # بارگذاری مجدد پروژه‌ها
            self.projects = self.db.load_all_projects()
            
            if self.projects:
                self.current_project_name = next(iter(self.projects))
                project = self.projects[self.current_project_name]
                if project.sections:
                    self.current_section_name = project.sections[0].name
            else:
                self.current_project_name = None
                self.current_section_name = None
            
            self._refresh_ui()
            
            ToastManager.success(
                f"Database restored! ({len(self.projects)} projects loaded)"
            )
            
        except Exception as e:
            ToastManager.error(f"Failed to restore database: {str(e)}")


    def _open_backup_folder(self):
        """باز کردن پوشه بکاپ در File Explorer"""
        import subprocess
        
        try:
            backup_dir = self.db.get_backup_path()
            
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            
            if os.name == 'nt':
                os.startfile(backup_dir)
            else:
                subprocess.Popen(['xdg-open', backup_dir])
            
            ToastManager.info(f"Opened backup folder: {backup_dir}")
            
        except Exception as e:
            ToastManager.error(f"Failed to open backup folder: {str(e)}")


    def _open_template_manager(self):
        """باز کردن Template Manager"""
        try:
            from gui.template_dialogs import TemplateManagerDialog
            dialog = TemplateManagerDialog(self.root, self)
            dialog.show()
        except Exception as e:
            ToastManager.error(f"Template Manager failed: {str(e)}")


    def _show_about(self):
        """نمایش درباره برنامه - با Dedication"""
        messagebox.showinfo(
            "About - درباره برنامه",
            "═══════════════════════════════════════════\n"
            "   CONTROL SYSTEM DEVICES MANAGER\n"
            "              Version 2.1\n"
            "═══════════════════════════════════════════\n\n"
            "🏢  Vahhaj Sanat Energy Co.\n"
            "    شرکت مهندسی وهاج صنعت انرژی\n\n"
            "👨‍💻  Developer: Mr. Keshtkar\n\n"
            "───────────────────────────────────────────\n"
            "          🛠️  Features\n"
            "───────────────────────────────────────────\n"
            "• Project Management\n"
            "• Device Tracking\n"
            "• Template System\n"
            "• Excel/PDF Export\n"
            "• Backup & Restore\n"
            "• AI Assistant\n\n"
            "───────────────────────────────────────────\n"
            "          📿  این برنامه هدیه می‌شود به:\n"
            "───────────────────────────────────────────\n\n"
            "        روح همه شهدای اسلام\n"
            "        بالاخص شهدای مبارزه با\n"
            "        آمریکا و اسرائیل\n"
            "        در سراسر جهان\n\n"
            "      🌹 روحشان شاد و یادشان گرامی 🌹\n\n"
            "───────────────────────────────────────────\n"
            "© 1403 Vahhaj Sanat Energy Co.\n"
            "All rights reserved.\n"
            "═══════════════════════════════════════════"
        )
    
    # ================================================================
    # TOOLS
    # ================================================================
    
    def _open_help(self):
        """باز کردن Help"""
        dialog = HelpDialog(self.root)
        dialog.show()
    
    def _open_component_manager(self):
        """باز کردن Component Manager"""
        from gui.component_dialogs import ComponentManagerDialog
        dialog = ComponentManagerDialog(self.root, self)
        dialog.show()
        self._refresh_ui()
    
    def _open_global_search(self):
        """جستجوی جهانی"""
        ToastManager.info("Search feature coming soon!")
    
    def _manage_labels(self):
        """مدیریت برچسب‌ها"""
        LabelsManagerDialog(self.root, self).show()
    
    def _show_project_summary(self):
        """خلاصه پروژه"""
        project = self.get_current_project()
        if not project:
            ToastManager.warning("No project selected!")
            return
        
        stats = project.get_statistics()
        msg = f"""
📊 Project Summary: {project.name}
{'='*40}

Sections: {stats['total_sections']}
Total Devices: {stats['total_devices']}
Active Devices: {stats['active_devices']}
Inactive Devices: {stats['inactive_devices']}

I/O Statistics:
- DI: {stats['total_di']}
- DO: {stats['total_do']}
- AI: {stats['total_ai']}
- AO: {stats['total_ao']}
- Total I/O: {stats['total_io']}
"""
        messagebox.showinfo("Project Summary", msg)
    
    def _edit_project_info(self):
        """ویرایش اطلاعات پروژه - با فیلد Description چندخطی"""
        project = self.get_current_project()
        if not project:
            ToastManager.warning("No project selected!")
            return
        
        # ============================================================
        # پنجره
        # ============================================================
        win = tk.Toplevel(self.root)
        win.title(f"Edit Project: {project.name}")
        win.geometry("600x750")
        win.transient(self.root)
        win.grab_set()
        win.configure(bg=get_color('bg_app'))
        
        # ============================================================
        # فیلدهای معمولی (Entry)
        # ============================================================
        entry_fields = [
            ("Project Name", "name"),
            ("Client Name", "client_name"),
            ("Client Phone", "client_phone"),
            ("Client Address", "client_address"),
            ("Consultant Name", "consultant_name"),
            ("Consultant Phone", "consultant_phone"),
            ("Consultant Address", "consultant_address"),
            ("Contractor Name", "contractor_name"),
            ("Contractor Phone", "contractor_phone"),
            ("Contractor Address", "contractor_address"),
            ("Designer Name", "designer_name"),
        ]
        
        entries = {}
        row_index = 0
        
        # ============================================================
        # ✅ فیلد Description (چندخطی)
        # ============================================================
        tk.Label(
            win,
            text="Description:",
            anchor="w",
            bg=get_color('bg_app'),
            fg=get_color('text_primary'),
            font=font('body'),
        ).grid(row=row_index, column=0, sticky="nw", padx=10, pady=(15, 3))
        
        desc_text = tk.Text(
            win,
            width=50,
            height=5,
            bg=get_color('input_bg'),
            fg=get_color('input_text'),
            font=font('input'),
            wrap=tk.WORD,
            relief='solid',
            borderwidth=1,
        )
        desc_text.insert('1.0', getattr(project, 'description', '') or "")
        desc_text.grid(row=row_index, column=1, padx=10, pady=(15, 3), sticky="ew")
        row_index += 1
        
        # ============================================================
        # فیلدهای Entry
        # ============================================================
        for label, attr in entry_fields:
            tk.Label(
                win,
                text=label + ":",
                anchor="w",
                bg=get_color('bg_app'),
                fg=get_color('text_primary'),
                font=font('body'),
            ).grid(row=row_index, column=0, sticky="w", padx=10, pady=3)
            
            entry = tk.Entry(
                win,
                width=50,
                bg=get_color('input_bg'),
                fg=get_color('input_text'),
                font=font('input'),
            )
            entry.insert(0, getattr(project, attr, '') or "")
            entry.grid(row=row_index, column=1, padx=10, pady=3, sticky="ew")
            entries[attr] = entry
            row_index += 1
        
        # ============================================================
        # تنظیم عرض ستون
        # ============================================================
        win.grid_columnconfigure(1, weight=1)
        
        # ============================================================
        # ذخیره
        # ============================================================
        def save():
            try:
                # ============================================================
                # 1. خواندن Description
                # ============================================================
                new_desc = desc_text.get('1.0', 'end-1c').strip()
                
                # اگر خالی بود، مقدار قبلی را نگه دار
                if not new_desc:
                    new_desc = getattr(project, 'description', '') or ""
                
                project.description = new_desc
                
                # ============================================================
                # 2. خواندن بقیه فیلدها
                # ============================================================
                for attr, entry in entries.items():
                    value = entry.get().strip()
                    
                    # اگر Entry خالی بود، مقدار قبلی را نگه دار
                    if not value:
                        value = getattr(project, attr, '') or ""
                    
                    setattr(project, attr, value)
                
                project.updated_at = datetime.now()
                
                # ============================================================
                # 3. ✅ فقط اطلاعات پایه را ذخیره کن (بدون دست زدن به Section ها)
                # ============================================================
                self.db.save_project_info(project)
                
                # ============================================================
                # 4. DEBUG
                # ============================================================
                
                win.destroy()
                ToastManager.success("Project information updated!")
                
                self._refresh_ui()
                logger.info(f"Project info updated: {project.name}")
            
            except Exception as e:
                logger.error(f"Failed to save project info: {e}", exc_info=True)
                ToastManager.error(f"Failed to save: {str(e)}")
        
        # ============================================================
        # دکمه Save
        # ============================================================
        btn_frame = tk.Frame(win, bg=get_color('bg_app'))
        btn_frame.grid(row=row_index, column=0, columnspan=2, pady=20)
        
        PrimaryButton(
            btn_frame,
            text="Save",
            command=save,
        ).pack(side=tk.LEFT, padx=5)
        
        SecondaryButton(
            btn_frame,
            text="Cancel",
            command=win.destroy,
        ).pack(side=tk.LEFT, padx=5)
        
        # ============================================================
        # Focus روی فیلد Project Name
        # ============================================================
        if entries.get('name'):
            entries['name'].focus_set()
    
    def _toggle_theme(self):
        """تغییر تم"""
        new_theme = self.tm.toggle_theme()
        ToastManager.info(f"Theme: {new_theme.capitalize()}")
        
        messagebox.showinfo(
            "Restart Required",
            "Theme changed.\n\nPlease restart the application to fully apply changes.",
        )
    
    # ================================================================
    # SHORTCUTS
    # ================================================================

    def _setup_shortcuts(self):
        """راه‌حل ترکیبی: keycode + bind معمولی"""
        from functools import partial
        
        # ===== روش 1: keycode (مستقل از زبان) =====
        self._setup_keycode_shortcuts()
        
        # ===== روش 2: bind معمولی (برای F1, F5) =====
        self.root.bind_all('<F1>', lambda e: self._open_help())
        self.root.bind_all('<F5>', lambda e: self._refresh_ui())


    def _setup_keycode_shortcuts(self):
        """shortcut ها بر اساس keycode"""
        
        # ============================================================
        # Virtual Key Codes (استاندارد ویندوز)
        # ============================================================
        VK = {
            'A': 65, 'B': 66, 'C': 67, 'D': 68, 'E': 69, 'F': 70,
            'G': 71, 'H': 72, 'I': 73, 'J': 74, 'K': 75, 'L': 76,
            'M': 77, 'N': 78, 'O': 79, 'P': 80, 'Q': 81, 'R': 82,
            'S': 83, 'T': 84, 'U': 85, 'V': 86, 'W': 87, 'X': 88,
            'Y': 89, 'Z': 90,
        }
        
        # ============================================================
        # تعریف shortcut ها
        # ============================================================
        # ('KEY', ctrl, shift): function
        SHORTCUTS = {
            # File
            ('N', 1, 0): self._new_project,
            ('O', 1, 0): self._open_project_manager,
            ('E', 1, 0): self._export_excel,
            ('P', 1, 0): self._export_pdf,
            ('Q', 1, 0): self.root.quit,
            # Duplicate
            ('D', 1, 0): self._check_duplicate_names,
            ('D', 1, 1): self._fix_duplicate_names,
            # ✅ Validate Project
            # Device
            ('A', 1, 1): self._add_device,
            ('C', 1, 0): self._copy_device,
            ('V', 1, 0): self._paste_device,
            ('C', 1, 1): self._copy_valve,           # Ctrl+Shift+C → Valves
            ('V', 1, 1): self._paste_valve,          # Ctrl+Shift+V → Valves
            # Edit
            ('Z', 1, 0): self._undo,
            ('Y', 1, 0): self._redo,
            ('F', 1, 0): self._open_global_search,
            # Backup
            ('B', 1, 0): self._backup_current_project,
            ('R', 1, 0): self._restore_project,
            # AI
            ('L', 1, 0): self._learn_project,   # Ctrl+L
            ('L', 1, 1): self._learn_all_projects,   # ✅ Ctrl+Shift+L
        }
        
        # ساخت map: (keycode, ctrl, shift) → function
        self._shortcut_map = {}
        for (key, ctrl, shift), func in SHORTCUTS.items():
            keycode = VK.get(key)
            if keycode:
                self._shortcut_map[(keycode, bool(ctrl), bool(shift))] = func
        
        # ============================================================
        # handler
        # ============================================================
        # keycode هایی که در Entry نباید اجرا شوند
        ENTRY_KEYS = {
            (VK['C'], True, False),   # Ctrl+C
            (VK['V'], True, False),   # Ctrl+V
            (VK['X'], True, False),   # Ctrl+X
            (VK['Z'], True, False),   # Ctrl+Z
            (VK['Y'], True, False),   # Ctrl+Y
            (VK['A'], True, True),    # Ctrl+Shift+A
        }
        
        def on_key_press(event):
            """
            پردازش کلیدهای فشرده شده
            
            ✅ جدید: 
            - چک می‌کند کدام Tab فعال است
            - Ctrl+C/V/X فقط در Device Tab کار می‌کنند
            """
            # ===== تشخیص state =====
            ctrl = bool(event.state & 0x4)
            shift = bool(event.state & 0x1)
            
            # ============================================================
            # ✅ ۱. اجازه بده Entry/Text همیشه کار کند
            # ============================================================
            widget = self.root.focus_get()
            is_in_entry = isinstance(widget, (tk.Entry, tk.Text, ttk.Entry))
            
            if is_in_entry:
                # در Entry → همه چیز رو بذار tkinter خودش انجام بده
                return None
            
            # ============================================================
            # ✅ ۲. چک: آیا Tab فعلی، "Devices" است؟
            # ============================================================
            def _is_devices_tab_active() -> bool:
                """آیا تب Devices فعال است؟"""
                try:
                    if not hasattr(self, 'notebook'):
                        return False
                    
                    current_tab = self.notebook.select()
                    current_widget = self.notebook.nametowidget(current_tab)
                    
                    return current_widget == self.devices_tab
                except Exception:
                    return False
            
            # ============================================================
            # ✅ ۳. Ctrl+C/V/X — فقط در Devices Tab
            # ============================================================
            if ctrl and not shift and event.keycode in (67, 86, 88):  # C, V, X
                if not _is_devices_tab_active():
                    logger.debug(
                        f"🚫 Blocked Ctrl+{event.keysym} — "
                        f"not in Devices tab"
                    )
                    return "break"   # ← نادیده بگیر
            
            # ============================================================
            # ✅ ۴. Ctrl+Shift+C/V — فقط در Valves Tab
            # ============================================================
            if ctrl and shift and event.keycode in (67, 86):  # Ctrl+Shift+C/V
                def _is_valves_tab_active() -> bool:
                    try:
                        if not hasattr(self, 'notebook'):
                            return False
                        current_tab = self.notebook.select()
                        current_widget = self.notebook.nametowidget(current_tab)
                        return current_widget == self.valves_tab
                    except Exception:
                        return False
                
                if not _is_valves_tab_active():
                    logger.debug(
                        f"🚫 Blocked Ctrl+Shift+{event.keysym} — "
                        f"not in Valves tab"
                    )
                    return "break"   # ← نادیده بگیر
            
            # ============================================================
            # ۵. جستجو در shortcut_map
            # ============================================================
            map_key = (event.keycode, ctrl, shift)
            
            if map_key not in self._shortcut_map:
                return None
            
            # ===== اجرا =====
            func = self._shortcut_map[map_key]
            try:
                func()
            except Exception as e:
                import traceback
                logger.error(f"Shortcut error: {e}", exc_info=True)
            
            return "break"
        
        # ===== اتصال =====
        self.root.bind_all('<KeyPress>', on_key_press)
        
        logger.debug(f"{len(self._shortcut_map)} shortcuts registered")

# ================================================================
# ENTRY POINT
# ================================================================

def run():
    """اجرای برنامه"""
    root = tk.Tk()
    app = MotorApp(root)
    root.mainloop()


if __name__ == '__main__':
    run()