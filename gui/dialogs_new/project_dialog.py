# gui/dialogs_new/project_dialog.py
"""
دیالوگ مدیریت پروژه‌ها - با جستجو در نام و توضیحات
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from gui.theme import (
    get_color, font, sp, w, ico,
)
from gui.components import (
    BaseDialog, PrimaryButton, SecondaryButton, DangerButton,
    ToastManager, confirm_dialog, SearchInput,
)


class ProjectManagerDialog(BaseDialog):
    """
    مدیر پروژه‌ها - با جستجو در نام و توضیحات
    """
    
    def __init__(self, parent, app):
        self.app = app
        
        super().__init__(
            parent,
            title="Project Manager",
            width=w('dialog_lg'),
            height=600,
        )
    
    # ================================================================
    # BUILD UI
    # ================================================================
    
    def build_body(self, parent):
        """محتوای دیالوگ"""
        
        # ===== Toolbar =====
        toolbar = tk.Frame(parent, bg=get_color('bg_app'))
        toolbar.pack(fill=tk.X, pady=(0, sp('md')))
        
        PrimaryButton(
            toolbar,
            text="New Project",
            icon='add',
            command=self._new_project,
        ).pack(side=tk.LEFT, padx=(0, sp('xs')))
        
        SecondaryButton(
            toolbar,
            text="Edit Info",
            icon='edit',
            command=self._edit_project,
        ).pack(side=tk.LEFT, padx=(0, sp('xs')))
        
        DangerButton(
            toolbar,
            text="Delete",
            icon='delete',
            command=self._delete_project,
        ).pack(side=tk.LEFT)
        
        # ===== Search =====
        search_frame = tk.Frame(parent, bg=get_color('bg_app'))
        search_frame.pack(fill=tk.X, pady=(0, sp('sm')))
        
        self.search = SearchInput(
            search_frame,
            placeholder="Search by name or description...",
            on_change=self._on_search,
        )
        self.search.pack(fill=tk.X)
        
        # ===== Table =====
        table_frame = tk.Frame(parent, bg=get_color('bg_app'))
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('name', 'description', 'sections', 'devices', 'io')
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            selectmode='browse',
        )
        
        column_configs = {
            'name':        ('Project Name', 220, 'w'),
            'description': ('Description',  250, 'w'),
            'sections':    ('Sections',     80,  'center'),
            'devices':     ('Devices',      80,  'center'),
            'io':          ('Total I/O',    90,  'center'),
        }
        
        for col, (title, width, align) in column_configs.items():
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor=align)
        
        # ===== Scrollbar =====
        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ===== رویدادها =====
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', lambda e: self._load_project())
        
        # ===== بارگذاری اولیه =====
        self._refresh_list()
    
    # ================================================================
    # REFRESH LIST
    # ================================================================
    
    def _refresh_list(self):
        """به‌روزرسانی لیست پروژه‌ها - با جستجو در نام و توضیحات"""
        
        # ===== پاک کردن Tree =====
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # ===== خواندن مقدار جستجو =====
        search_term = self.search.get().lower().strip() if hasattr(self, 'search') else ''
        
        # ===== مرتب‌سازی =====
        sorted_projects = sorted(
            self.app.projects.items(),
            key=lambda x: x[0].lower()
        )
        
        # ===== پر کردن Tree =====
        for name, project in sorted_projects:
            description = getattr(project, 'description', '') or ''
            
            # ===== جستجو در نام و توضیحات =====
            if search_term:
                name_match = search_term in name.lower()
                desc_match = search_term in description.lower()
                
                if not (name_match or desc_match):
                    continue
            
            # ===== آمار =====
            stats = project.get_statistics()
            
            values = (
                name,
                self._shorten_text(description, max_len=50),
                stats['total_sections'],
                stats['total_devices'],
                stats['total_io'],
            )
            
            item = self.tree.insert('', 'end', values=values)
            
            # ===== هایلایت پروژه جاری =====
            if name == self.app.current_project_name:
                self.tree.selection_set(item)
                self.tree.item(item, tags=('current',))
        
        self.tree.tag_configure('current', foreground=get_color('primary'))
    
    @staticmethod
    def _shorten_text(text: str, max_len: int = 50) -> str:
        """کوتاه کردن متن طولانی"""
        if not text:
            return '—'
        
        text = text.replace('\n', ' ').strip()
        
        if len(text) <= max_len:
            return text
        
        return text[:max_len - 3] + '...'
    
    # ================================================================
    # EVENTS
    # ================================================================
    
    def _on_search(self, query: str):
        """جستجو"""
        self._refresh_list()
    
    def _on_select(self, event=None):
        """انتخاب"""
        pass
    
    def _get_selected_name(self) -> Optional[str]:
        """نام پروژه انتخاب شده"""
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree.item(selection[0], 'values')[0]
    
    # ================================================================
    # ACTIONS
    # ================================================================
    
    def _new_project(self):
        """پروژه جدید"""
        self.destroy()
        self.app._new_project()
    
    def _edit_project(self):
        """ویرایش پروژه"""
        name = self._get_selected_name()
        if not name:
            ToastManager.warning("Please select a project.")
            return
        
        self.destroy()
        self.app.switch_to_project(name)
        self.app._edit_project_info()
    
    def _delete_project(self):
        """حذف پروژه"""
        name = self._get_selected_name()
        if not name:
            ToastManager.warning("Please select a project.")
            return
        
        if len(self.app.projects) <= 1:
            ToastManager.warning("Cannot delete the last project.")
            return
        
        if confirm_dialog(
            self,
            f"Are you sure you want to delete project '{name}'?\n\n"
            f"This action cannot be undone.",
            "Confirm Delete",
            'danger',
            "Delete",
            "Cancel",
        ):
            self.app.db.delete_project(name)
            del self.app.projects[name]
            
            if name == self.app.current_project_name:
                first = next(iter(self.app.projects))
                self.app.switch_to_project(first)
            
            ToastManager.success(f"Project '{name}' deleted.")
            self._refresh_list()
    
    def _load_project(self):
        """بارگذاری پروژه"""
        name = self._get_selected_name()
        if not name:
            return
        
        self.app.switch_to_project(name)
        ToastManager.success(f"Loaded project: {name}")
        self.destroy()
    
    # ================================================================
    # FOOTER
    # ================================================================
    
    def _build_footer(self):
        """Footer با دکمه Load"""
        footer = tk.Frame(self, bg=get_color('bg_surface'), height=60)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        btn_frame = tk.Frame(footer, bg=get_color('bg_surface'))
        btn_frame.pack(side=tk.RIGHT, padx=sp('lg'), pady=sp('md'))
        
        SecondaryButton(
            btn_frame,
            text="Cancel",
            command=self.on_cancel,
        ).pack(side=tk.RIGHT, padx=(sp('sm'), 0))
        
        PrimaryButton(
            btn_frame,
            text="Load",
            icon='folder_open',
            command=self._load_project,
        ).pack(side=tk.RIGHT)


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['ProjectManagerDialog']