# gui/layout/sidebar.py
"""
سایدبار - Sidebar
با Project Explorer + Context Menu
(Statistics و Quick Actions حذف شدند — آمار به StatusBar منتقل شد)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Callable, Dict, List, Optional

from gui.theme import (
    get_color, font, sp, pad, h, w, ico,
)
from gui.components import (
    SearchInput, Separator, Card,
    PrimaryButton, SecondaryButton, GhostButton,
    IconButton, ToastManager,
)


class Sidebar(tk.Frame):
    """
    سایدبار با:
    1. Project Explorer (تمام ارتفاع)
    2. Context Menu (راست کلیک)
    """
    
    def __init__(self, parent, app=None, **kwargs):
        super().__init__(
            parent,
            bg=get_color('sidebar_bg'),
            width=w('sidebar'),
            **kwargs
        )
        
        self.app = app
        self.pack_propagate(False)
        
        # ===== Border راست =====
        border = tk.Frame(self, bg=get_color('sidebar_border'), width=1)
        border.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ===== Container =====
        self.container = tk.Frame(self, bg=get_color('sidebar_bg'))
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # ===== ساخت Explorer (تمام ارتفاع) =====
        self._build_explorer()
        
        # ===== Context Menu =====
        self._build_context_menu()
    
    # ================================================================
    # EXPLORER
    # ================================================================
    
    def _build_explorer(self):
        """ساخت بخش Project Explorer - تمام ارتفاع"""
        # ===== Header =====
        header = tk.Frame(self.container, bg=get_color('sidebar_bg'))
        header.pack(fill=tk.X, padx=sp('md'), pady=(sp('md'), sp('sm')))
        
        tk.Label(
            header,
            text=f"{ico('folder_open')}  Explorer",
            font=font('h3'),
            bg=get_color('sidebar_bg'),
            fg=get_color('sidebar_text'),
            anchor='w',
        ).pack(side=tk.LEFT)
        
        # ===== Search =====
        search_frame = tk.Frame(self.container, bg=get_color('sidebar_bg'))
        search_frame.pack(fill=tk.X, padx=sp('md'), pady=(0, sp('sm')))
        
        self.search = SearchInput(
            search_frame,
            placeholder="Search...",
            on_change=self._on_search,
        )
        self.search.pack(fill=tk.X)
        
        # ===== Tree (با ارتفاع بیشتر) =====
        tree_frame = tk.Frame(self.container, bg=get_color('sidebar_bg'))
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=sp('md'))
        
        # استایل Treeview
        style = ttk.Style()
        style.configure(
            'Sidebar.Treeview',
            background=get_color('sidebar_bg'),
            foreground=get_color('sidebar_text'),
            fieldbackground=get_color('sidebar_bg'),
            font=font('body'),
            rowheight=26,
            borderwidth=0,
            relief='flat',
        )
        style.map(
            'Sidebar.Treeview',
            background=[
                ('selected', get_color('sidebar_active')),
            ],
            foreground=[
                ('selected', get_color('primary')),
            ],
        )
        
        self.tree = ttk.Treeview(
            tree_frame,
            style='Sidebar.Treeview',
            selectmode='browse',
            show='tree',
        )
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient='vertical',
            command=self.tree.yview,
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # ===== رویدادها =====
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
        self.tree.bind('<Double-1>', self._on_tree_double_click)
        self.tree.bind('<Button-3>', self._show_context_menu)
        self.tree.bind('<Delete>', lambda e: self._delete_selected())
        self.tree.bind('<F2>', lambda e: self._rename_selected())
        
        # ===== Quick New Button (پایین Sidebar) =====
        new_btn_frame = tk.Frame(self.container, bg=get_color('sidebar_bg'))
        new_btn_frame.pack(fill=tk.X, padx=sp('md'), pady=sp('sm'), side=tk.BOTTOM)
        
        PrimaryButton(
            new_btn_frame,
            text="New Project",
            icon='add',
            command=self._on_new_project,
        ).pack(fill=tk.X)
    
    
    
    # ================================================================
    # CONTEXT MENU
    # ================================================================
    
    def _build_context_menu(self):
        """ساخت Context Menu"""
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
        """
        نمایش Context Menu (سه‌سطحی: Project → Revision → Section → Device)
        
        ✅ راه‌حل B - حذف مرحله‌به‌مرحله:
        - Section خالی → قابل حذف (حتی اگر آخرین باشد)
        - Revision خالی → قابل حذف (حتی اگر آخرین باشد)
        - Project خالی → قابل حذف (حتی اگر آخرین باشد + ساخت خودکار)
        """
        item = self.tree.identify_row(event.y)
        if not item:
            return

        if not self.tree.exists(item):
            return
        
        self.tree.selection_set(item)
        tags = self.tree.item(item, 'tags')
        values = self.tree.item(item, 'values')
        
        self.context_menu.delete(0, tk.END)
        
        # ============================================================
        # PROJECT MENU
        # ============================================================
        if self._is_project(tags):
            proj_name = values[0] if values else None
            if not proj_name:
                return
            
            project = self.app.projects.get(proj_name) if self.app else None
            
            # ===== بررسی وضعیت =====
            total_sections = 0
            total_devices = 0
            revision_count = 0
            is_only_project = (len(self.app.projects) <= 1) if self.app else False
            
            if project:
                stats = project.get_statistics()
                total_sections = stats['total_sections']
                total_devices = stats['total_devices']
                revision_count = len(project.revisions)
            
            # ✅ راه‌حل B: پروژه خالی قابل حذف است (حتی اگر آخرین باشد)
            is_empty = (total_sections == 0 and total_devices == 0)
            
            # ===== آیتم‌های منو =====
            self.context_menu.add_command(
                label=f"  {ico('open')}  Open Project",
                command=self._open_selected_project,
            )
            self.context_menu.add_command(
                label=f"  {ico('edit')}  Rename Project",
                command=self._rename_selected,
            )
            self.context_menu.add_separator()
            
            self.context_menu.add_command(
                label="  📌  New Revision (Empty)",
                command=self._add_new_revision_to_project,
            )
            self.context_menu.add_command(
                label="  📋  Copy Current Revision → New",
                command=self._copy_current_revision,
            )
            self.context_menu.add_separator()
            
            self.context_menu.add_command(
                label=f"  {ico('add')}  New Section",
                command=self._add_section_to_project,
            )
            # ✅ Paste Section (به Revision فعلی این Project)
            if hasattr(self, '_copied_section') and self._copied_section:
                current_rev = project.current_revision_name if project else None
                if current_rev:
                    self.context_menu.add_command(
                        label=f"  📌  Paste Section '{self._copied_section.name}' to '{current_rev}'",
                        command=lambda p=proj_name, r=current_rev: 
                            self._paste_section(p, r),
                    )
                    self.context_menu.add_separator()

            self.context_menu.add_separator()
            self.context_menu.add_command(
                label=f"  {ico('backup')}  Backup Project",
                command=self._backup_selected_project,
            )
            self.context_menu.add_separator()
            
            # ============================================================
            # ✅ DELETE PROJECT - منطق جدید (راه‌حل B)
            # ============================================================
            if is_empty:
                # ─── پروژه خالی → قابل حذف ───
                if is_only_project:
                    # تنها پروژه → با هشدار
                    self.context_menu.add_command(
                        label=f"  {ico('delete')}  Delete Project (Last)",
                        command=self._delete_selected,
                    )
                    self.context_menu.add_command(
                        label="       ℹ️ A new empty project will be created",
                        state='disabled',
                        foreground=get_color('accent_cyan'),
                    )
                else:
                    # چند پروژه → ساده
                    self.context_menu.add_command(
                        label=f"  {ico('delete')}  Delete Project",
                        command=self._delete_selected,
                    )
            else:
                # ─── پروژه غیرخالی → غیرفعال ───
                info_parts = []
                if revision_count > 0:
                    info_parts.append(f"{revision_count} Rev")
                if total_sections > 0:
                    info_parts.append(f"{total_sections} Sec")
                if total_devices > 0:
                    info_parts.append(f"{total_devices} Dev")
                
                info_text = ", ".join(info_parts)
                
                self.context_menu.add_command(
                    label=f"  🔒  Delete Project ({info_text})",
                    state='disabled',
                )
                self.context_menu.add_command(
                    label="       ⚠️ Delete all content first",
                    state='disabled',
                    foreground=get_color('text_muted'),
                )
        
        
        # ============================================================
        # REVISION MENU
        # ============================================================
        elif 'revision' in tags and len(values) >= 2:
            proj_name = values[0]
            rev_name = values[1]
            
            project = self.app.projects.get(proj_name) if self.app else None
            revision = project.get_revision_by_name(rev_name) if project else None
            
            # ===== اگر revision پیدا نشد =====
            if not project or not revision:
                self.context_menu.add_command(
                    label="  ⚠️  Revision data not found",
                    state='disabled',
                )
                try:
                    self.context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    self.context_menu.grab_release()
                return
            
            # ===== محاسبه شرایط =====
            is_current = (project.current_revision_name == rev_name)
            section_count = len(revision.sections)
            device_count = len(revision.get_all_devices())
            
            # ✅ راه‌حل B: Revision خالی قابل حذف است (حتی اگر آخرین باشد)
            is_empty = (section_count == 0)
            
            # ===== Set as Current (فقط اگر Current نباشه) =====
            if not is_current:
                self.context_menu.add_command(
                    label="  ✅  Set as Current",
                    command=lambda: self._set_current_revision(proj_name, rev_name),
                )
                self.context_menu.add_separator()
            
            # ===== Copy This Revision =====
            self.context_menu.add_command(
                label="  📋  Copy This Revision → New",
                command=lambda: self._copy_revision_dialog(proj_name, rev_name),
            )
            # ✅ Paste Section (به این Revision)
            if hasattr(self, '_copied_section') and self._copied_section:
                self.context_menu.add_command(
                    label=f"  📌  Paste Section '{self._copied_section.name}'",
                    command=lambda p=proj_name, r=rev_name: 
                        self._paste_section(p, r),
                )
            
            # ===== Copy All Sections to Current =====
            if not is_current and section_count > 0:
                self.context_menu.add_command(
                    label="  📑  Copy All Sections to Current",
                    command=lambda: self._copy_all_sections_from_revision(proj_name, rev_name),
                )
            
            self.context_menu.add_separator()
            
            # ===== Rename =====
            self.context_menu.add_command(
                label=f"  {ico('edit')}  Rename Revision",
                command=self._rename_selected,
            )
            
            self.context_menu.add_separator()
            
            # ============================================================
            # ✅ DELETE REVISION - منطق جدید (راه‌حل B)
            # ============================================================
            if is_empty:
                # ─── Revision خالی → قابل حذف ───
                if is_current:
                    # Current Revision → با هشدار
                    self.context_menu.add_command(
                        label=f"  {ico('delete')}  Delete Revision (Current)",
                        command=lambda: self._delete_revision(proj_name, rev_name),
                    )
                    self.context_menu.add_command(
                        label="       ℹ️ Current will switch automatically",
                        state='disabled',
                        foreground=get_color('accent_cyan'),
                    )
                else:
                    # غیر Current → ساده
                    self.context_menu.add_command(
                        label=f"  {ico('delete')}  Delete Revision",
                        command=lambda: self._delete_revision(proj_name, rev_name),
                    )
            else:
                # ─── Revision غیرخالی → غیرفعال ───
                info_parts = [f"{section_count} Sec"]
                if device_count > 0:
                    info_parts.append(f"{device_count} Dev")
                info_text = ", ".join(info_parts)
                
                self.context_menu.add_command(
                    label=f"  🔒  Delete Revision ({info_text})",
                    state='disabled',
                )
                self.context_menu.add_command(
                    label="       ⚠️ Delete all sections first",
                    state='disabled',
                    foreground=get_color('text_muted'),
                )
        
        # ============================================================
        # SECTION MENU
        # ============================================================
        elif 'section' in tags and len(values) >= 3:
            proj_name = values[0]
            rev_name = values[1]
            sec_name = values[2]
            
            # ===== دریافت Section و Revision =====
            project = self.app.projects.get(proj_name) if self.app else None
            revision = project.get_revision_by_name(rev_name) if project else None
            section = revision.get_section_by_name(sec_name) if revision else None
            
            # ===== محاسبه شرایط =====
            device_count = len(section.devices) if section else 0
            
            # ===== آیتم‌های پایه منو =====
            self.context_menu.add_command(
                label=f"  {ico('open')}  Go to Section",
                command=self._open_selected_section,
            )
            self.context_menu.add_command(
                label=f"  {ico('edit')}  Rename Section",
                command=self._rename_selected,
            )
            self.context_menu.add_separator()
            self.context_menu.add_command(
                label=f"  {ico('add')}  Add Device",
                command=self._add_device_to_section,
            )
            self.context_menu.add_separator()
            
            self.context_menu.add_command(
                label="  📋  Copy Section",
                command=lambda: self._copy_section(proj_name, rev_name, sec_name),
            )
            
            
            # ===== Paste Section (به همان Revision) =====
            if hasattr(self, '_copied_section') and self._copied_section:
                self.context_menu.add_command(
                    label=f"  📌  Paste Section '{self._copied_section.name}'",
                    command=lambda p=proj_name, r=rev_name: 
                        self._paste_section(p, r),
                )
            
            self.context_menu.add_separator()
            
            # ============================================================
            # ✅ DELETE SECTION - منطق جدید (راه‌حل B)
            # ============================================================
            # حالت ۱: Section غیرخالی → غیرفعال
            # حالت ۲: Section خالی → قابل حذف (حتی اگر آخرین باشد)
            # ============================================================

            if device_count > 0:
                # ─── حالت ۱: Section غیرخالی ───
                self.context_menu.add_command(
                    label=f"  🔒  Delete Section ({device_count} Device)",
                    state='disabled',
                )
                self.context_menu.add_command(
                    label="       ⚠️ Delete all devices first",
                    state='disabled',
                    foreground=get_color('text_muted'),
                )
            else:
                # ─── حالت ۲: Section خالی → قابل حذف ───
                self.context_menu.add_command(
                    label=f"  {ico('delete')}  Delete Section",
                    command=self._delete_selected,
                )
        
        # ============================================================
        # DEVICE MENU
        # ============================================================
        elif 'device' in tags and len(values) >= 4:
            # Device همیشه قابل حذف است
            self.context_menu.add_command(
                label=f"  {ico('edit')}  Edit Device",
                command=self._edit_selected_device,
            )
            self.context_menu.add_separator()
            self.context_menu.add_command(
                label=f"  {ico('copy')}  Copy Device",
                command=self._copy_selected_device,
            )
            self.context_menu.add_separator()
            self.context_menu.add_command(
                label=f"  {ico('delete')}  Delete Device",
                command=self._delete_selected,
            )
        
        # ============================================================
        # نمایش منو
        # ============================================================
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    # ================================================================
    # CONTEXT MENU ACTIONS
    # ================================================================
    
    def _open_selected_project(self):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return
        values = self.tree.item(item, 'values')
        if values and self.app:
            self.app.switch_to_project(values[0])
    
    def _open_selected_section(self):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return
        values = self.tree.item(item, 'values')
        if len(values) >= 3 and self.app:
            project_name = values[0]
            revision_name = values[1]
            section_name = values[2]
            
            if project_name != self.app.current_project_name:
                self.app.switch_to_project(project_name)
            
            project = self.app.projects.get(project_name)
            if project and project.current_revision_name != revision_name:
                project.current_revision_name = revision_name
                self.app.db.set_current_revision(project_name, revision_name)
            
            self.app.current_section_name = section_name
            self.app._refresh_table_only()
    
    def _rename_selected(self):
        """تغییر نام آیتم انتخاب شده (Project / Revision / Section)"""
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item or not self.app:
            return
        values = self.tree.item(item, 'values')
        tags = self.tree.item(item, 'tags')
        
        # ============================================================
        # PROJECT RENAME
        # ============================================================
        if self._is_project(tags):
            old_name = values[0]
            
            new_name = simpledialog.askstring(
                "Rename Project",
                f"New name for project '{old_name}':",
                initialvalue=old_name,
                parent=self,
            )
            
            # کاربر Cancel کرد
            if new_name is None:
                return
            
            # خالی بود
            if not new_name.strip():
                ToastManager.warning("Project name cannot be empty!")
                return
            
            new_name = new_name.strip()
            
            # همان نام قبلی
            if new_name == old_name:
                return
            
            # تغییر نام
            self.app._rename_project(old_name, new_name)
        
        # ============================================================
        # REVISION RENAME
        # ============================================================
        elif 'revision' in tags:
            project_name = values[0]
            revision_name = values[1]
            
            new_name = simpledialog.askstring(
                "Rename Revision",
                f"New name for revision '{revision_name}':",
                initialvalue=revision_name,
                parent=self,
            )
            
            if new_name is None:
                return
            
            if not new_name.strip():
                ToastManager.warning("Revision name cannot be empty!")
                return
            
            new_name = new_name.strip()
            
            if new_name == revision_name:
                return
            
            self.app._rename_revision(project_name, revision_name, new_name)
        
        # ============================================================
        # SECTION RENAME
        # ============================================================
        elif 'section' in tags:
            project_name = values[0]
            revision_name = values[1]
            section_name = values[2]
            
            new_name = simpledialog.askstring(
                "Rename Section",
                f"New name for section '{section_name}':",
                initialvalue=section_name,
                parent=self,
            )
            
            if new_name is None:
                return
            
            if not new_name.strip():
                ToastManager.warning("Section name cannot be empty!")
                return
            
            new_name = new_name.strip()
            
            if new_name == section_name:
                return
            
            self.app._rename_section(
                project_name, revision_name, section_name, new_name
            )
    
    def _delete_selected(self):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item or not self.app:
            return
        values = self.tree.item(item, 'values')
        tags = self.tree.item(item, 'tags')
        
        if self._is_project(tags):
            self.app._delete_project_with_confirm(values[0])
        elif 'revision' in tags:
            self.app._delete_revision_with_confirm(values[0], values[1])
        elif 'section' in tags:
            self.app._delete_section_with_confirm(values[0], values[1], values[2])
        elif 'device' in tags:
            self.app._delete_device_from_sidebar(values[0], values[1], values[2], int(values[3]))

    def _add_section_to_project(self):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item or not self.app:
            return
        values = self.tree.item(item, 'values')
        if values:
            self.app._add_section_to_project(values[0])
    
    def _add_device_to_section(self):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item or not self.app:
            return
        values = self.tree.item(item, 'values')
        if len(values) >= 3:
            self.app._add_device_to_section(values[0], values[1], values[2])
    
    def _edit_selected_device(self):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item or not self.app:
            return
        values = self.tree.item(item, 'values')
        if len(values) >= 4:
            self.app._edit_device_from_sidebar(values[0], values[1], values[2], int(values[3]))
    
    def _copy_selected_device(self):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item or not self.app:
            return
        values = self.tree.item(item, 'values')
        if len(values) >= 4:
            self.app._copy_device_from_sidebar(values[0], values[1], values[2], int(values[3]))
    
    def _backup_selected_project(self):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item or not self.app:
            return
        tags = self.tree.item(item, 'tags')
        values = self.tree.item(item, 'values')
        if self._is_project(tags) and values:
            self.app._backup_project_by_name(values[0])

    def _is_project(self, tags) -> bool:
        """بررسی اینکه tag مربوط به پروژه است (فعال یا غیرفعال)"""
        return 'project' in tags or 'current_project' in tags
    
    # ================================================================
    # TREE EVENTS
    # ================================================================
    
    def _on_tree_select(self, event=None):
        selection = self.tree.selection()
        if not selection or not self.app:
            return
        item = selection[0]
        if not self.tree.exists(item):
            return
        tags = self.tree.item(item, 'tags')
        values = self.tree.item(item, 'values')
        
        if self._is_project(tags) and values:
            self.app._on_sidebar_project_selected(values[0], item)
        elif 'revision' in tags and len(values) >= 2:
            self.app._on_sidebar_revision_selected(values[0], values[1], item)
        elif 'section' in tags and len(values) >= 3:
            self.app._on_sidebar_section_selected(values[0], values[1], values[2], item)
        elif 'device' in tags and len(values) >= 4:
            self.app._on_sidebar_device_selected(
                values[0], values[1], values[2], int(values[3]), item
            )
    
    def _on_tree_double_click(self, event=None):
        self._on_tree_select(event)
    
    def _on_search(self, query: str):
        """جستجو در درخت پروژه‌ها — با پشتیبانی از Description"""
        
        # ============================================================
        # حالت ۱: query خالی → همه چیز را نشان بده
        # ============================================================
        if not query or not query.strip():
            if self.app:
                self.refresh_tree(self.app.projects, preserve_state=False)
            return
        
        query_lower = query.lower().strip()
        
        # ============================================================
        # حالت ۲: query دارد → فیلتر کن
        # ============================================================
        if self.app:
            self.refresh_tree(self.app.projects, preserve_state=False)
        
        # ============================================================
        # پیدا کردن نودهای مرتبط
        # ============================================================
        visible_items = set()
        
        for proj_item in self.tree.get_children(''):
            proj_text = self.tree.item(proj_item, 'text').lower()
            proj_values = self.tree.item(proj_item, 'values')
            
            # ============================================================
            # ✅ جستجو در نام پروژه
            # ============================================================
            proj_match = query_lower in proj_text
            
            # ============================================================
            # ✅ جستجو در Description پروژه (جدید)
            # ============================================================
            if not proj_match and proj_values and self.app:
                proj_name = proj_values[0] if proj_values else None
                
                if proj_name and proj_name in self.app.projects:
                    project = self.app.projects[proj_name]
                    description = getattr(project, 'description', '') or ''
                    
                    if query_lower in description.lower():
                        proj_match = True
            # ============================================================
            
            rev_matches = []
            
            for rev_item in self.tree.get_children(proj_item):
                rev_text = self.tree.item(rev_item, 'text').lower()
                rev_match = query_lower in rev_text
                
                sec_matches = []
                
                for sec_item in self.tree.get_children(rev_item):
                    sec_text = self.tree.item(sec_item, 'text').lower()
                    sec_match = query_lower in sec_text
                    
                    dev_matches = []
                    
                    for dev_item in self.tree.get_children(sec_item):
                        dev_text = self.tree.item(dev_item, 'text').lower()
                        if query_lower in dev_text:
                            dev_matches.append(dev_item)
                    
                    if sec_match or dev_matches:
                        sec_matches.append((sec_item, dev_matches))
                
                if rev_match or sec_matches:
                    rev_matches.append((rev_item, sec_matches))
            
            if proj_match or rev_matches:
                visible_items.add(proj_item)
                
                if proj_match and not rev_matches:
                    for rev_item in self.tree.get_children(proj_item):
                        visible_items.add(rev_item)
                        for sec_item in self.tree.get_children(rev_item):
                            visible_items.add(sec_item)
                            for dev_item in self.tree.get_children(sec_item):
                                visible_items.add(dev_item)
                else:
                    for rev_item, sec_matches in rev_matches:
                        visible_items.add(rev_item)
                        
                        if rev_match and not sec_matches:
                            for sec_item in self.tree.get_children(rev_item):
                                visible_items.add(sec_item)
                                for dev_item in self.tree.get_children(sec_item):
                                    visible_items.add(dev_item)
                        else:
                            for sec_item, dev_matches in sec_matches:
                                visible_items.add(sec_item)
                                
                                if not dev_matches:
                                    for dev_item in self.tree.get_children(sec_item):
                                        visible_items.add(dev_item)
                                else:
                                    for dev_item in dev_matches:
                                        visible_items.add(dev_item)
        
        # ============================================================
        # ✅ حذف نودهای غیرمرتبط
        # ============================================================
        self._filter_tree_by_visible(visible_items)
    
    def _on_new_project(self):
        if self.app:
            self.app._new_project()

    # ================================================================
    # REVISION ACTIONS
    # ================================================================

    def _filter_tree_by_visible(self, visible_items: set):
        """
        حذف نودهای غیرمرتبط از درخت
        
        Args:
            visible_items: set از item_id هایی که باید باقی بمانند
        """
        # ============================================================
        # پیدا کردن والدین نودهای visible
        # ============================================================
        all_visible = set(visible_items)
        
        def find_parent(item):
            """پیدا کردن والد یک نود"""
            return self.tree.parent(item)
        
        for item in list(visible_items):
            parent = find_parent(item)
            while parent:
                all_visible.add(parent)
                parent = find_parent(parent)
        
        # ============================================================
        # حذف نودهای غیرمرتبط (از پایین به بالا)
        # ============================================================
        def delete_unvisible(parent=''):
            """حذف بازگشتی نودهای غیرمرتبط"""
            for item in list(self.tree.get_children(parent)):
                # ===== ابتدا فرزندان را پردازش کن =====
                delete_unvisible(item)
                
                # ===== اگر نود visible نیست، حذفش کن =====
                if item not in all_visible:
                    try:
                        self.tree.delete(item)
                    except Exception:
                        pass
        
        # شروع از root ها
        delete_unvisible('')
        
        # ============================================================
        # ============================================================
        # ✅ بستن همه نودها (کاربر خودش باز می‌کند)
        # ============================================================
        for item in all_visible:
            if self.tree.exists(item):
                try:
                    self.tree.item(item, open=False)
                except Exception:
                    pass

    
    def _add_new_revision_to_project(self):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item or not self.app:
            return
        values = self.tree.item(item, 'values')
        if values:
            self.app._new_revision_dialog(values[0], copy_from=None)
    
    def _copy_current_revision(self):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item or not self.app:
            return
        values = self.tree.item(item, 'values')
        if values:
            proj_name = values[0]
            project = self.app.projects.get(proj_name)
            if project and project.current_revision_name:
                self.app._new_revision_dialog(
                    proj_name, 
                    copy_from=project.current_revision_name
                )
    
    def _set_current_revision(self, project_name: str, revision_name: str):
        if self.app:
            self.app._switch_to_revision(project_name, revision_name)
    
    def _copy_revision_dialog(self, project_name: str, source_revision: str):
        if self.app:
            self.app._new_revision_dialog(project_name, copy_from=source_revision)
    
    def _copy_all_sections_from_revision(self, project_name: str, source_revision: str):
        if self.app:
            self.app._copy_all_sections_to_current(project_name, source_revision)
    
    def _delete_revision(self, project_name: str, revision_name: str):
        if self.app:
            self.app._delete_revision_with_confirm(project_name, revision_name)

    def _delete_last_section_with_revision(self, project_name: str, 
                                            revision_name: str, 
                                            section_name: str):
        """
        حذف آخرین Section + کل Revision (آبشاری)
        
        این متد فقط یک Wrapper است که درخواست را به main_window می‌فرستد.
        منطق واقعی در MotorApp._delete_last_section_with_revision است.
        """
        if not self.app:
            return
        
        self.app._delete_last_section_with_revision(
            project_name, 
            revision_name, 
            section_name
        )
    
    def _copy_section(self, project_name: str, revision_name: str, section_name: str):
        if not self.app:
            return
        project = self.app.projects.get(project_name)
        if not project:
            return
        revision = project.get_revision_by_name(revision_name)
        if not revision:
            return
        section = revision.get_section_by_name(section_name)
        if not section:
            return
        
        self._copied_section = section.copy()
        self._copied_section_source = f"{project_name} / {revision_name} / {section_name}"
        
        ToastManager.success(f"Section '{section_name}' copied to clipboard!")
    
    def _paste_section(self, project_name: str, revision_name: str):
        if not hasattr(self, '_copied_section') or not self._copied_section:
            return
        if self.app:
            self.app._paste_section_to_revision(
                project_name, 
                revision_name, 
                self._copied_section
            )
    
    # ================================================================
    # STATS (برای StatusBar)
    # ================================================================
    
    def update_stats(self, stats: Dict):
        """
        به‌روزرسانی آمار - حالا در StatusBar استفاده می‌شود
        این متد برای سازگاری نگه داشته شده است.
        """
        # ✅ آمار در StatusBar نمایش داده می‌شود
        if self.app and hasattr(self.app, 'statusbar'):
            try:
                sections = stats.get('sections', 0)
                devices = stats.get('devices', 0)
                active = stats.get('active', 0)
                io = stats.get('io', 0)
                
                stats_text = (
                    f"{ico('section')} {sections}  |  "
                    f"{ico('device')} {devices}  |  "
                    f"{ico('check_circle')} {active}  |  "
                    f"{ico('chart')} I/O: {io}"
                )
                
                if hasattr(self.app.statusbar, 'set_stats'):
                    self.app.statusbar.set_stats(stats_text)
            except:
                pass

    # ================================================================
    # TREE STATE PERSISTENCE
    # ================================================================
    
    def _save_tree_state(self) -> set:
        """
        ذخیره حالت باز/بسته نودها
        
        Returns:
            set از (tags_tuple, values_tuple) که open هستن
        """
        open_items = set()
        
        def walk(item):
            try:
                tags = tuple(self.tree.item(item, 'tags'))
                values = tuple(self.tree.item(item, 'values'))
                is_open = bool(self.tree.item(item, 'open'))
                
                if is_open:
                    open_items.add((tags, values))
                
                for child in self.tree.get_children(item):
                    walk(child)
            except Exception:
                pass
        
        for item in self.tree.get_children():
            walk(item)
        
        return open_items
    
    def _restore_tree_state(self, open_items: set):
        """
        بازیابی حالت باز/بسته نودها
        
        Args:
            open_items: set از (tags_tuple, values_tuple)
        """
        def walk(item):
            try:
                tags = tuple(self.tree.item(item, 'tags'))
                values = tuple(self.tree.item(item, 'values'))
                key = (tags, values)
                
                if key in open_items:
                    self.tree.item(item, open=True)
                else:
                    # اگر قبلاً بسته بود، بسته نگه دار
                    # ولی اگر state ذخیره شده نداشتیم، از پیش‌فرض استفاده کن
                    if not open_items:  # فقط اگه state ذخیره شده خالی باشه
                        pass  # پیش‌فرض رو حفظ کن
                    else:
                        self.tree.item(item, open=False)
                
                for child in self.tree.get_children(item):
                    walk(child)
            except Exception:
                pass
        
        for item in self.tree.get_children():
            walk(item)
    
    def refresh_tree(self, projects: Dict, preserve_state: bool = True):
        """
        به‌روزرسانی درخت پروژه‌ها - با حفظ حالت باز/بسته
        
        Args:
            projects: دیکشنری پروژه‌ها
            preserve_state: اگر True، حالت باز/بسته حفظ می‌شود
        """
        # ✅ ذخیره حالت قبل از پاک کردن
        saved_state = None
        if preserve_state:
            saved_state = self._save_tree_state()
        
        # پاک کردن
        for item in self.tree.get_children():
            self.tree.delete(item)
        # ✅ پاک کردن cache جستجو
        
        if not projects:
            return
        
        # ... ساخت درخت (بدون تغییر) ...
        sorted_projects = sorted(projects.items(), key=lambda x: x[0].lower())
        
        for proj_name, project in sorted_projects:
            # ============================================================
            # ✅ تشخیص پروژه فعال
            # ============================================================
            is_current_project = (proj_name == self.app.current_project_name) if self.app else False
            
            # ============================================================
            # سطح 1: Project
            # ============================================================
            project_tag = 'current_project' if is_current_project else 'project'
            
            proj_item = self.tree.insert(
                '',
                'end',
                text=f"  🏗️  {proj_name}",
                open=False,   # ✅ پروژه فعال باز باشه
                tags=(project_tag,),
                values=(proj_name,),
            )
            
            sorted_revisions = sorted(project.revisions, key=lambda r: r.name.lower())
            
            for revision in sorted_revisions:
                is_current = (revision.name == project.current_revision_name)
                rev_icon = '📌' if is_current else '📎'
                current_marker = ' (Current)' if is_current else ''
                
                section_count = len(revision.sections)
                device_count = len(revision.get_all_devices())
                
                rev_text = f"  {rev_icon}  {revision.name}{current_marker}"
                if section_count > 0:
                    rev_text += f"  [{section_count}S / {device_count}D]"
                
                rev_item = self.tree.insert(
                    proj_item,
                    'end',
                    text=rev_text,
                    open=is_current,
                    tags=('revision', 'current_revision' if is_current else 'other_revision'),
                    values=(proj_name, revision.name),
                )
                
                sorted_sections = sorted(revision.sections, key=lambda s: s.name.lower())
                
                for section in sorted_sections:
                    device_count_sec = len(section.devices)
                    sec_text = f"  📂  {section.name}"
                    if device_count_sec > 0:
                        sec_text += f"  ({device_count_sec})"
                    
                    sec_item = self.tree.insert(
                        rev_item,
                        'end',
                        text=sec_text,
                        open=False,
                        tags=('section',),
                        values=(proj_name, revision.name, section.name),
                    )
                    
                    sorted_devices = sorted(
                        section.devices,
                        key=lambda d: (d.Name or '').lower()
                    )
                    
                    for i, device in enumerate(sorted_devices):
                        device_name = device.Name or "Unnamed"
                        device_io = device.get_total_io()
                        
                        if device_io > 20:
                            status_icon = '🔴'
                        elif device_io > 10:
                            status_icon = '🟡'
                        else:
                            status_icon = '🟢'
                        
                        device_text = f"    {status_icon}  {device_name}  ({device_io})"
                        
                        self.tree.insert(
                            sec_item,
                            'end',
                            text=device_text,
                            tags=('device',),
                            values=(proj_name, revision.name, section.name, i),
                        )
        
        # تنظیم رنگ‌ها
        # ============================================================
        # ✅ تنظیم رنگ‌ها
        # ============================================================
        # پروژه معمولی
        self.tree.tag_configure(
            'project',
            foreground=get_color('text_primary'),
            font=(None, 10, 'normal'),
        )

        # ✅ پروژه فعال - سبز تیره + Bold
        self.tree.tag_configure(
            'current_project',
            foreground=get_color('success'),      # رنگ سبز
            font=(None, 10, 'bold'),              # Bold
        )

        # Revision ها
        self.tree.tag_configure('revision', foreground=get_color('accent_cyan'))
        self.tree.tag_configure('current_revision', foreground=get_color('success'))
        self.tree.tag_configure('other_revision', foreground=get_color('text_secondary'))

        # Section و Device
        self.tree.tag_configure('section', foreground=get_color('text_secondary'))
        self.tree.tag_configure('device', foreground=get_color('text_muted'))
        
        # ✅ بازیابی حالت
        if preserve_state and saved_state is not None:
            self._restore_tree_state(saved_state)

    # ================================================================
    # SEARCH HELPERS
    # ================================================================
    
    
    
    def _restore_all_tree_items(self):
        """
        بازگرداندن همه نودها
        
        ✅ به‌جای استفاده از cache، درخت را از app.projects بازسازی می‌کند
        (ساده‌تر و مطمئن‌تر)
        """
        if not self.app:
            return
        
        self.refresh_tree(self.app.projects, preserve_state=False)
        
        # ============================================================
        # بازگرداندن نودها از cache
        # ============================================================
        def restore_children(parent=''):
            children = [
                (item, data) 
                for item, data in cache.items() 
                if data['parent'] == parent
            ]
            
            children.sort(key=lambda x: x[1]['index'])
            
            for item, data in children:
                if not self.tree.exists(item):
                    self.tree.move(item, parent, 'end')
                
                self.tree.item(item, open=data['open'])
                restore_children(item)
        
        roots = [
            (item, data) 
            for item, data in cache.items() 
            if data['parent'] == ''
        ]
        roots.sort(key=lambda x: x[1]['index'])
        
        for item, data in roots:
            if not self.tree.exists(item):
                self.tree.move(item, '', 'end')
            self.tree.item(item, open=data['open'])
            restore_children(item)
    


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['Sidebar']