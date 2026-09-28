# gui/attachments_panel.py
"""
پنل مدیریت پیوست‌های پروژه (Attachments Panel)
با ساختار درختی و همگام‌سازی خودکار با فایل‌سیستم
"""

import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import os
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional

from core.attachments import AttachmentManager
from gui.theme import (
    get_color, font, sp, pad, h, w, ico,
)
from gui.components import (
    SearchInput, Separator,
    PrimaryButton, SecondaryButton, DangerButton,
    GhostButton, IconButton,
    ToastManager, confirm_dialog,
)


# ================================================================
# FILE TYPE ICONS
# ================================================================

FILE_TYPE_ICONS = {
    # Documents
    'pdf':  '📕',
    'doc':  '📘', 'docx': '📘',
    'xls':  '📗', 'xlsx': '📗', 'csv': '📗',
    'ppt':  '📙', 'pptx': '📙',
    'txt':  '📄',
    
    # Images
    'jpg':  '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 
    'gif':  '🖼️', 'bmp': '🖼️', 'svg': '🖼️',
    
    # CAD / Engineering
    'dwg':  '📐', 'dxf': '📐',
    
    # Archives
    'zip':  '📦', 'rar': '📦', '7z': '📦',
    
    # Other
    'default': '📎',
}


def get_file_icon(extension: str) -> str:
    """دریافت آیکون بر اساس پسوند فایل"""
    ext = extension.lower().lstrip('.')
    return FILE_TYPE_ICONS.get(ext, FILE_TYPE_ICONS['default'])


# ================================================================
# ATTACHMENTS PANEL
# ================================================================

class AttachmentsPanel(tk.Frame):
    """
    پنل پیوست‌ها - با ساختار درختی
    
    قابلیت‌ها:
    - نمایش درختی فایل‌ها و پوشه‌ها
    - باز/بسته کردن پوشه‌ها با دابل کلیک
    - افزودن فایل / پوشه
    - حذف (با Recycle Bin)
    - تغییر نام
    - باز کردن / نمایش در Explorer
    - Export (کپی به جای دیگر)
    - همگام‌سازی خودکار با فایل‌سیستم
    - جستجو
    """
    
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(parent, bg=get_color('bg_app'), **kwargs)
        
        self.app = app
        self.attachment_manager: Optional[AttachmentManager] = None
        self._all_files: List[Dict[str, Any]] = []
        self._filtered_files: List[Dict[str, Any]] = []
        self._current_project: Optional[str] = None
        
        self._build_ui()
    
    # ================================================================
    # INIT
    # ================================================================
    
    def set_attachment_manager(self, manager: AttachmentManager):
        """تنظیم AttachmentManager (بعد از ساخت)"""
        self.attachment_manager = manager
    
    def set_project(self, project_name: str):
        """تنظیم پروژه فعلی و بارگذاری پیوست‌ها"""
        self._current_project = project_name
        self.refresh()
    
    # ================================================================
    # UI
    # ================================================================
    
    def _build_ui(self):
        """ساخت UI"""
        
        # ===== Card =====
        card = tk.Frame(
            self,
            bg=get_color('bg_surface'),
            highlightthickness=1,
            highlightbackground=get_color('border_default'),
        )
        card.pack(fill=tk.BOTH, expand=True)
        
        # ============================================================
        # HEADER
        # ============================================================
        header = tk.Frame(
            card,
            bg=get_color('bg_surface_alt'),
            height=h('table_header'),
        )
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"  {ico('attachment')}  Project Attachments",
            font=font('h3'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_primary'),
        ).pack(side=tk.LEFT, padx=sp('md'))
        
        # Counter + Size
        self.counter_label = tk.Label(
            header,
            text="0 files (0 B)",
            font=font('small'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_secondary'),
        )
        self.counter_label.pack(side=tk.RIGHT, padx=sp('md'))
        
        # ============================================================
        # TOOLBAR
        # ============================================================
        toolbar = tk.Frame(card, bg=get_color('bg_surface'))
        toolbar.pack(fill=tk.X, padx=sp('md'), pady=sp('sm'))
        
        # ===== Add Buttons =====
        PrimaryButton(
            toolbar,
            text="Add Files",
            icon='add',
            command=self._add_files,
            tooltip="Add one or more files",
        ).pack(side=tk.LEFT, padx=(0, sp('xs')))
        
        SecondaryButton(
            toolbar,
            text="Add Folder",
            icon='folder',
            command=self._add_folder,
            tooltip="Add all files from a folder",
        ).pack(side=tk.LEFT, padx=(0, sp('sm')))
        
        # ===== Separator =====
        tk.Frame(toolbar, bg=get_color('border_default'), width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs')
        )
        
        # ===== Action Buttons =====
        self.open_btn = IconButton(
            toolbar, icon='folder_open',
            command=self._open_file,
            tooltip="Open File/Folder",
            size=32,
        )
        self.open_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        self.explorer_btn = IconButton(
            toolbar, icon='search',
            command=self._show_in_explorer,
            tooltip="Show in Explorer",
            size=32,
        )
        self.explorer_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        self.rename_btn = IconButton(
            toolbar, icon='edit',
            command=self._rename_file,
            tooltip="Rename",
            size=32,
        )
        self.rename_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        self.export_btn = IconButton(
            toolbar, icon='export',
            command=self._export_file,
            tooltip="Export (Copy to...)",
            size=32,
        )
        self.export_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        self.delete_btn = IconButton(
            toolbar, icon='delete',
            command=self._delete_file,
            tooltip="Delete",
            size=32,
        )
        self.delete_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ============================================================
        # Sync Button
        # ============================================================
        tk.Frame(toolbar, bg=get_color('border_default'), width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs')
        )
        
        self.sync_btn = IconButton(
            toolbar, icon='refresh',
            command=self._manual_sync,
            tooltip="Sync with filesystem (detect new files)",
            size=32,
        )
        self.sync_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ============================================================
        # Expand/Collapse All Buttons
        # ============================================================
        tk.Frame(toolbar, bg=get_color('border_default'), width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs')
        )
        
        self.expand_btn = IconButton(
            toolbar, icon='collapse',
            command=self._expand_all,
            tooltip="Expand All",
            size=32,
        )
        self.expand_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        self.collapse_btn = IconButton(
            toolbar, icon='expand',
            command=self._collapse_all,
            tooltip="Collapse All",
            size=32,
        )
        self.collapse_btn.pack(side=tk.LEFT, padx=sp('xxs'))
        
        # ===== Open Folder =====
        tk.Frame(toolbar, bg=get_color('border_default'), width=1).pack(
            side=tk.LEFT, fill=tk.Y, padx=sp('sm'), pady=sp('xs')
        )
        
        SecondaryButton(
            toolbar,
            text="Open Folder",
            icon='folder_open',
            command=self._open_project_folder,
            tooltip="Open attachments folder",
        ).pack(side=tk.LEFT)
        
        # ===== Search (Right) =====
        self.search = SearchInput(
            toolbar,
            placeholder="Search files...",
            on_change=self._on_search,
        )
        self.search.pack(side=tk.RIGHT, fill=tk.X, expand=False, ipadx=40)
        
        # ============================================================
        # TABLE
        # ============================================================
        table_container = tk.Frame(card, bg=get_color('bg_surface'))
        table_container.pack(
            fill=tk.BOTH, expand=True,
            padx=sp('md'), pady=(0, sp('md'))
        )
        
        columns = ('name', 'type', 'size', 'date', 'path')
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show='tree headings',
            selectmode='extended',
        )
        
        # ===== تنظیم ستون‌ها =====
        self.tree.heading('#0', text='')
        self.tree.column('#0', width=30, minwidth=30, stretch=False)
        
        column_configs = {
            'name': ('File Name',   300, 'w'),
            'type': ('Type',        90,  'center'),
            'size': ('Size',        90,  'e'),
            'date': ('Added',       140, 'center'),
            'path': ('Path',        250, 'w'),
        }
        
        for col, (title, width, align) in column_configs.items():
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor=align, minwidth=50)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_container, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(table_container, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # ===== رویدادها =====
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Delete>', lambda e: self._delete_file())
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Button-3>', self._show_context_menu)
        
        # ===== Context Menu =====
        self._build_context_menu()
        
        # ===== Empty State =====
        self.empty_label = tk.Label(
            table_container,
            text="📎  No attachments yet.\n\nClick 'Add Files' to attach documents.",
            font=font('body'),
            bg=get_color('bg_surface'),
            fg=get_color('text_muted'),
            justify='center',
        )
        
        # وضعیت اولیه دکمه‌ها
        self._update_buttons_state(False)
    
    # ================================================================
    # CONTEXT MENU
    # ================================================================
    
    def _build_context_menu(self):
        """ساخت منوی راست‌کلیک"""
        self.context_menu = tk.Menu(
            self,
            tearoff=0,
            bg=get_color('bg_surface_elevated'),
            fg=get_color('text_primary'),
            activebackground=get_color('primary'),
            activeforeground=get_color('text_inverse'),
            font=font('body'),
            borderwidth=1,
            relief='solid',
        )
    
    def _show_context_menu(self, event):
        """نمایش منوی راست‌کلیک"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        if item not in self.tree.selection():
            self.tree.selection_set(item)
        
        # ===== تشخیص نوع =====
        values = self.tree.item(item, 'values')
        is_folder = len(values) > 1 and 'Folder' in values[1]
        
        # ===== ساخت منو =====
        self.context_menu.delete(0, tk.END)
        
        if is_folder:
            self.context_menu.add_command(
                label=f"  {ico('folder_open')}  Open Folder",
                command=lambda: self._on_double_click_by_item(item),
            )
            self.context_menu.add_command(
                label=f"  {ico('search')}  Show in Explorer",
                command=self._show_in_explorer,
            )
            self.context_menu.add_separator()
            self.context_menu.add_command(
                label=f"  {ico('edit')}  Rename",
                command=self._rename_file,
            )
            self.context_menu.add_separator()
            self.context_menu.add_command(
                label=f"  {ico('delete')}  Delete",
                command=self._delete_file,
            )
        else:
            self.context_menu.add_command(
                label=f"  {ico('folder_open')}  Open File",
                command=self._open_file,
            )
            self.context_menu.add_command(
                label=f"  {ico('search')}  Show in Explorer",
                command=self._show_in_explorer,
            )
            self.context_menu.add_separator()
            self.context_menu.add_command(
                label=f"  {ico('edit')}  Rename",
                command=self._rename_file,
            )
            self.context_menu.add_command(
                label=f"  {ico('export')}  Export To...",
                command=self._export_file,
            )
            self.context_menu.add_separator()
            self.context_menu.add_command(
                label=f"  {ico('delete')}  Delete",
                command=self._delete_file,
            )
        
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    # ================================================================
    # REFRESH
    # ================================================================
    
    def refresh(self):
        """بارگذاری مجدد لیست پیوست‌ها (با همگام‌سازی خودکار)"""
        if not self.attachment_manager:
            return
        
        if not self._current_project:
            return
        
        try:
            # ============================================================
            # ✅ همگام‌سازی با فایل‌سیستم
            # ============================================================
            self.attachment_manager.sync_with_filesystem(self._current_project)
            
            # ============================================================
            # ✅ دریافت ساختار درختی
            # ============================================================
            self._all_files = self.attachment_manager.get_files_tree(self._current_project)
            self._apply_filter()
            self._update_counter()
        except Exception as e:
            ToastManager.error(f"Failed to load attachments: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_filter(self):
        """اعمال فیلتر جستجو (روی درخت)"""
        search_term = self.search.get().lower() if hasattr(self, 'search') else ''
        
        if search_term:
            # ===== فیلتر بازگشتی =====
            def filter_tree(items):
                result = []
                for item in items:
                    name_match = search_term in item['name'].lower()
                    filtered_children = filter_tree(item.get('children', []))
                    
                    if name_match or filtered_children:
                        new_item = item.copy()
                        new_item['children'] = filtered_children
                        result.append(new_item)
                return result
            
            self._filtered_files = filter_tree(self._all_files)
        else:
            self._filtered_files = self._all_files
        
        self._populate_tree()
    
    def _populate_tree(self):
        """پر کردن Treeview به صورت درخت سلسله‌مراتبی"""
        # ===== پاک کردن =====
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self._filtered_files:
            self.empty_label.place(relx=0.5, rely=0.5, anchor='center')
            return
        else:
            self.empty_label.place_forget()
        
        # ============================================================
        # ✅ بررسی وضعیت جستجو
        # ============================================================
        search_term = ''
        if hasattr(self, 'search'):
            try:
                search_term = self.search.get().strip()
            except Exception:
                pass
        
        is_searching = bool(search_term)
        
        # ============================================================
        # ✅ تابع کمکی: آیا این نود فرزند قابل نمایش دارد؟
        # ============================================================
        def has_visible_children(node) -> bool:
            """آیا این نود فرزندی دارد که باید نمایش داده شود؟"""
            children = node.get('children', [])
            
            if not children:
                return False
            
            # در حالت جستجو، فقط نودهایی که خودشان یا فرزندانشان مطابق هستند
            # در این تابع، فرض بر این است که _filtered_files قبلاً فیلتر شده
            # پس اگر فرزندی دارد، یعنی فرزند مطابق است
            return True
        
        # ============================================================
        # ✅ درج بازگشتی
        # ============================================================
        def insert_node(node: Dict, parent: str = '') -> str:
            node_type = node.get('type', 'file')
            
            # ===== تعیین آیکون و نوع =====
            if node_type == 'folder':
                icon = '📁'
                type_display = '📁 Folder'
                tag = 'folder'
            else:
                file_type = node.get('file_type', '')
                if not node.get('exists', True):
                    icon = '⚠️'
                    tag = 'missing'
                else:
                    icon = get_file_icon(file_type)
                    tag = 'normal'
                type_display = file_type.upper() if file_type else '—'
            
            # ============================================================
            # ✅ تصمیم‌گیری درباره open/close
            # ============================================================
            is_open = False
            
            if node_type == 'folder':
                if is_searching:
                    # در حالت جستجو: اگر پوشه فرزندی دارد → باز
                    is_open = bool(node.get('children'))
                else:
                    # بدون جستجو: پوشه‌ها بسته
                    is_open = False
            
            # ===== فرمت‌ها =====
            file_size_str = node.get('file_size_str', '—')
            date_str = self._format_date(node.get('added_at', ''))
            short_path = self._shorten_path(node.get('rel_path', node.get('path', '')))
            
            # ===== درج =====
            item_id = self.tree.insert(
                parent,
                'end',
                text=f"  {icon}",
                values=(
                    node['name'],
                    type_display,
                    file_size_str,
                    date_str,
                    short_path,
                ),
                tags=(tag,),
                open=is_open,
            )
            
            # ===== درج فرزندان =====
            for child in node.get('children', []):
                insert_node(child, item_id)
            
            return item_id
        
        # ===== شروع از ریشه =====
        for node in self._filtered_files:
            insert_node(node)
        
        # ============================================================
        # ✅ تنظیم رنگ‌ها
        # ============================================================
        self.tree.tag_configure('normal', foreground=get_color('text_primary'))
        self.tree.tag_configure('missing', foreground=get_color('danger'))
        self.tree.tag_configure(
            'folder',
            foreground=get_color('accent_orange'),
            font=('Segoe UI', 10, 'bold'),
        )
    
    def _update_counter(self):
        """به‌روزرسانی شمارنده"""
        if not self.attachment_manager or not self._current_project:
            return
        
        try:
            # ===== شمارش بازگشتی فایل‌ها و پوشه‌ها =====
            file_count = 0
            folder_count = 0
            total_bytes = 0
            
            def walk(items):
                nonlocal file_count, folder_count, total_bytes
                for item in items:
                    if item.get('type') == 'folder':
                        folder_count += 1
                    else:
                        file_count += 1
                        total_bytes += item.get('file_size', 0)
                    walk(item.get('children', []))
            
            walk(self._all_files)
            
            size_str = self.attachment_manager._format_size(total_bytes)
            
            text = f"{file_count} files, {folder_count} folders ({size_str})"
            self.counter_label.configure(text=text)
        except Exception:
            pass
    
    def _format_date(self, iso_str: str) -> str:
        """فرمت تاریخ"""
        if not iso_str:
            return '—'
        
        try:
            dt = datetime.fromisoformat(iso_str)
            return dt.strftime('%Y/%m/%d %H:%M')
        except Exception:
            return iso_str[:16] if len(iso_str) > 16 else iso_str
    
    def _shorten_path(self, path: str, max_len: int = 50) -> str:
        """کوتاه کردن مسیر"""
        if not path:
            return '—'
        
        if len(path) <= max_len:
            return path
        
        head = path[:20]
        tail = path[-(max_len - 23):]
        return f"{head}...{tail}"
    
    # ================================================================
    # SEARCH
    # ================================================================
    
    def _on_search(self, query: str):
        """جستجو"""
        self._apply_filter()
        self._update_counter()
    
    # ================================================================
    # SELECTION
    # ================================================================
    
    def _get_selected_files(self) -> List[Dict[str, Any]]:
        """دریافت فایل‌های انتخاب شده (فقط فایل‌ها، نه پوشه‌ها)"""
        selected = []
        
        for item in self.tree.selection():
            values = self.tree.item(item, 'values')
            if not values:
                continue
            
            file_name = values[0]
            type_display = values[1] if len(values) > 1 else ''
            
            # ✅ رد کردن پوشه‌ها
            if 'Folder' in type_display:
                continue
            
            # ===== پیدا کردن فایل در درخت =====
            def find_node(items, name):
                for node in items:
                    if node['name'] == name and node.get('type') == 'file':
                        return node
                    found = find_node(node.get('children', []), name)
                    if found:
                        return found
                return None
            
            node = find_node(self._all_files, file_name)
            if node:
                selected.append(node)
        
        return selected
    
    def _on_select(self, event=None):
        """رویداد انتخاب"""
        selected = self.tree.selection()
        
        if not selected:
            self._update_buttons_state(False)
            return
        
        # ===== بررسی: آیا انتخاب روی پوشه است؟ =====
        is_folder_selected = False
        for item in selected:
            values = self.tree.item(item, 'values')
            if len(values) > 1 and 'Folder' in values[1]:
                is_folder_selected = True
                break
        
        if is_folder_selected:
            # ===== پوشه: فقط دکمه‌های باز/نمایش/تغییرنام/حذف فعال =====
            try:
                self.open_btn.set_enabled(False)
                self.explorer_btn.set_enabled(True)
                self.rename_btn.set_enabled(True)
                self.export_btn.set_enabled(False)
                self.delete_btn.set_enabled(True)
            except:
                pass
        else:
            # ===== فایل: همه فعال =====
            has_selection = len(selected) > 0
            single_selection = len(selected) == 1
            self._update_buttons_state(has_selection, single_selection)
    
    def _update_buttons_state(self, has_selection: bool, single_selection: bool = False):
        """به‌روزرسانی وضعیت دکمه‌ها"""
        for btn in (self.open_btn, self.explorer_btn, self.export_btn, self.delete_btn):
            try:
                btn.set_enabled(has_selection)
            except:
                pass
        
        try:
            self.rename_btn.set_enabled(single_selection)
        except:
            pass
    
    # ================================================================
    # DOUBLE CLICK
    # ================================================================
    
    def _on_double_click(self, event):
        """رویداد دابل کلیک - پوشه باز/بسته یا فایل باز"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        self._on_double_click_by_item(item)
        return "break"
    
    def _on_double_click_by_item(self, item):
        """دابل کلیک روی item خاص"""
        values = self.tree.item(item, 'values')
        
        if len(values) > 1 and 'Folder' in values[1]:
            # ===== پوشه: باز/بسته کن =====
            current_open = self.tree.item(item, 'open')
            self.tree.item(item, open=not current_open)
        else:
            # ===== فایل: باز کن =====
            self._open_file()
    
    # ================================================================
    # EXPAND/COLLAPSE
    # ================================================================
    
    def _expand_all(self):
        """باز کردن همه پوشه‌ها"""
        def walk(item):
            try:
                self.tree.item(item, open=True)
                for child in self.tree.get_children(item):
                    walk(child)
            except:
                pass
        
        for item in self.tree.get_children():
            walk(item)
        
        ToastManager.info("All folders expanded")
    
    def _collapse_all(self):
        """بستن همه پوشه‌ها"""
        def walk(item):
            try:
                self.tree.item(item, open=False)
                for child in self.tree.get_children(item):
                    walk(child)
            except:
                pass
        
        for item in self.tree.get_children():
            walk(item)
        
        ToastManager.info("All folders collapsed")
    
    # ================================================================
    # ACTIONS - SYNC
    # ================================================================
    
    def _manual_sync(self):
        """همگام‌سازی دستی با فایل‌سیستم"""
        if not self._check_project():
            return
        
        try:
            # ===== نمایش حالت loading =====
            self.sync_btn.set_enabled(False)
            self.update_idletasks()
            
            # ===== اجرای sync =====
            result = self.attachment_manager.sync_with_filesystem(self._current_project)
            
            # ===== Refresh =====
            self._all_files = self.attachment_manager.get_files_tree(self._current_project)
            self._apply_filter()
            self._update_counter()
            
            # ===== نمایش نتیجه =====
            if result['added'] > 0 or result['removed'] > 0:
                parts = []
                if result['added'] > 0:
                    parts.append(f"{result['added']} added")
                if result['removed'] > 0:
                    parts.append(f"{result['removed']} removed")
                ToastManager.success(f"Synced: {', '.join(parts)}")
            else:
                ToastManager.info("Everything is up to date ✅")
        
        except Exception as e:
            ToastManager.error(f"Sync failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.sync_btn.set_enabled(True)
    
    # ================================================================
    # ACTIONS - ADD
    # ================================================================
    
    def _add_files(self):
        """افزودن فایل‌ها"""
        if not self._check_project():
            return
        
        file_paths = filedialog.askopenfilenames(
            title="Select Files to Attach",
            filetypes=[
                ("All files", "*.*"),
                ("Documents", "*.pdf *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.txt"),
                ("Images", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("CAD", "*.dwg *.dxf"),
                ("Archives", "*.zip *.rar *.7z"),
            ],
        )
        
        if not file_paths:
            return
        
        result = self.attachment_manager.add_files(
            self._current_project,
            list(file_paths)
        )
        
        self.refresh()
        
        if result['added'] > 0:
            ToastManager.success(f"Added {result['added']} file(s) successfully!")
        
        if result['failed'] > 0:
            error_msg = f"Failed to add {result['failed']} file(s)"
            if result['errors']:
                error_msg += f"\n\nFirst error: {result['errors'][0]}"
            ToastManager.warning(error_msg)
    
    def _add_folder(self):
        """افزودن پوشه"""
        if not self._check_project():
            return
        
        folder_path = filedialog.askdirectory(
            title="Select Folder to Attach",
        )
        
        if not folder_path:
            return
        
        recursive = messagebox.askyesno(
            "Include Subfolders?",
            "Do you want to include files from subfolders?",
            parent=self,
        )
        
        result = self.attachment_manager.add_folder(
            self._current_project,
            folder_path,
            recursive=recursive,
        )
        
        self.refresh()
        
        if result['added'] > 0:
            ToastManager.success(f"Added {result['added']} file(s) from folder!")
        
        if result['failed'] > 0:
            ToastManager.warning(f"Failed: {result['failed']} file(s)")
    
    # ================================================================
    # ACTIONS - OPEN
    # ================================================================
    
    def _open_file(self):
        """باز کردن فایل یا پوشه"""
        selected = self._get_selected_files()
        
        # ===== فایل انتخاب شده =====
        if selected:
            file_data = selected[0]
            result = self.attachment_manager.open_file(
                self._current_project,
                file_data['name']
            )
            
            if not result['success']:
                ToastManager.error(f"Failed to open: {result.get('error', 'Unknown error')}")
            return
        
        # ===== پوشه انتخاب شده =====
        tree_selection = self.tree.selection()
        if tree_selection:
            item = tree_selection[0]
            values = self.tree.item(item, 'values')
            if values and len(values) > 1 and 'Folder' in values[1]:
                folder_name = values[0]
                self._open_folder_by_name(folder_name)
    
    def _open_folder_by_name(self, folder_name: str):
        """باز کردن یک پوشه خاص در Explorer"""
        try:
            # ===== جستجوی پوشه در درخت =====
            def find_folder(items, name):
                for node in items:
                    if node.get('type') == 'folder' and node['name'] == name:
                        return node
                    found = find_folder(node.get('children', []), name)
                    if found:
                        return found
                return None
            
            folder_node = find_folder(self._all_files, folder_name)
            
            if folder_node and os.path.exists(folder_node['path']):
                if os.name == 'nt':
                    os.startfile(folder_node['path'])
                else:
                    subprocess.Popen(['xdg-open', folder_node['path']])
            else:
                ToastManager.error(f"Folder not found: {folder_name}")
        
        except Exception as e:
            ToastManager.error(f"Failed to open folder: {e}")
    
    def _show_in_explorer(self):
        """نمایش در Explorer"""
        # ===== بررسی: فایل یا پوشه؟ =====
        tree_selection = self.tree.selection()
        if not tree_selection:
            return
        
        item = tree_selection[0]
        values = self.tree.item(item, 'values')
        
        if len(values) > 1 and 'Folder' in values[1]:
            # ===== پوشه: باز کردن در Explorer =====
            folder_name = values[0]
            self._open_folder_by_name(folder_name)
            return
        
        # ===== فایل: انتخاب در Explorer =====
        selected = self._get_selected_files()
        if not selected:
            return
        
        for file_data in selected:
            result = self.attachment_manager.show_in_explorer(
                self._current_project,
                file_data['name']
            )
            
            if not result['success']:
                ToastManager.error(f"Failed: {result.get('error', 'Unknown')}")
    
    def _open_project_folder(self):
        """باز کردن پوشه پروژه"""
        if not self._check_project():
            return
        
        result = self.attachment_manager.open_folder(self._current_project)
        
        if not result['success']:
            ToastManager.error(f"Failed: {result.get('error', 'Unknown')}")
    
    # ================================================================
    # ACTIONS - RENAME
    # ================================================================
    
    def _rename_file(self):
        """تغییر نام فایل یا پوشه"""
        tree_selection = self.tree.selection()
        if len(tree_selection) != 1:
            ToastManager.warning("Please select exactly one item.")
            return
        
        item = tree_selection[0]
        values = self.tree.item(item, 'values')
        old_name = values[0]
        is_folder = len(values) > 1 and 'Folder' in values[1]
        
        # ===== جدا کردن نام و پسوند =====
        if is_folder:
            name_part = old_name
            ext_part = ''
        else:
            name_part, ext_part = os.path.splitext(old_name)
        
        # ===== دیالوگ =====
        new_name = simpledialog.askstring(
            "Rename Folder" if is_folder else "Rename File",
            f"New name for '{old_name}':",
            initialvalue=name_part,
            parent=self,
        )
        
        if not new_name or not new_name.strip():
            return
        
        new_name = new_name.strip()
        if ext_part and not new_name.lower().endswith(ext_part.lower()):
            new_name += ext_part
        
        if new_name == old_name:
            return
        
        # ===== فراخوانی rename =====
        result = self.attachment_manager.rename_file(
            self._current_project,
            old_name,
            new_name,
        )
        
        if result['success']:
            ToastManager.success(f"Renamed to '{result['new_name']}'")
            self.refresh()
        else:
            ToastManager.error(f"Failed: {result.get('error', 'Unknown')}")
    
    # ================================================================
    # ACTIONS - EXPORT
    # ================================================================
    
    def _export_file(self):
        """Export"""
        selected = self._get_selected_files()
        if not selected:
            ToastManager.warning("Please select file(s) to export.")
            return
        
        if len(selected) == 1:
            # ===== تک فایل =====
            file_data = selected[0]
            
            dest_path = filedialog.asksaveasfilename(
                title="Export File As...",
                initialfile=file_data['name'],
            )
            
            if not dest_path:
                return
            
            result = self.attachment_manager.export_file(
                self._current_project,
                file_data['name'],
                dest_path,
            )
            
            if result['success']:
                ToastManager.success(f"Exported to: {dest_path}")
            else:
                ToastManager.error(f"Failed: {result.get('error')}")
        else:
            # ===== چند فایل =====
            dest_dir = filedialog.askdirectory(
                title=f"Export {len(selected)} files to folder...",
            )
            
            if not dest_dir:
                return
            
            success_count = 0
            for file_data in selected:
                dest_path = os.path.join(dest_dir, file_data['name'])
                result = self.attachment_manager.export_file(
                    self._current_project,
                    file_data['name'],
                    dest_path,
                )
                if result['success']:
                    success_count += 1
            
            ToastManager.success(f"Exported {success_count}/{len(selected)} file(s)")
    
    # ================================================================
    # ACTIONS - DELETE
    # ================================================================
    
    def _delete_file(self):

        """حذف فایل یا پوشه (به Recycle Bin)"""
        tree_selection = self.tree.selection()
        if not tree_selection:
            return
        
        # ===== شمارش =====
        items_to_delete = []
        for item in tree_selection:
            values = self.tree.item(item, 'values')
            if not values:
                continue
            items_to_delete.append({
                'name': values[0],
                'is_folder': len(values) > 1 and 'Folder' in values[1],
            })
        
        if not items_to_delete:
            return
        
        # ===== تایید =====
        if len(items_to_delete) == 1:
            item = items_to_delete[0]
            type_str = "folder" if item['is_folder'] else "file"
            msg = f"Delete {type_str} '{item['name']}'?\n\nThe {type_str} will be moved to Recycle Bin."
        else:
            msg = f"Delete {len(items_to_delete)} item(s)?\n\nItems will be moved to Recycle Bin."
        
        if not confirm_dialog(
            self,
            msg,
            "Confirm Delete",
            'danger',
            "Delete",
            "Cancel",
        ):
            return
        
        # ===== حذف =====
        success_count = 0
        errors = []
        
        for item in items_to_delete:
            result = self.attachment_manager.remove_file(
                self._current_project,
                item['name'],
                to_recycle_bin=True,
            )
            
            if result['success']:
                success_count += 1
            else:
                errors.append(f"{item['name']}: {result.get('error')}")
        
        self.refresh()
        
        if success_count > 0:
            ToastManager.success(f"Deleted {success_count} item(s)")
        
        if errors:
            ToastManager.error(f"Failed: {len(errors)} item(s)")
    
    # ================================================================
    # HELPERS
    # ================================================================
    
    def _check_project(self) -> bool:
        """بررسی وجود پروژه"""
        if not self.attachment_manager:
            ToastManager.error("AttachmentManager not initialized!")
            return False
        
        if not self._current_project:
            ToastManager.warning("No project selected!")
            return False
        
        return True


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['AttachmentsPanel', 'get_file_icon']