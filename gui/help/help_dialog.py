# gui/help/help_dialog.py
"""
دیالوگ Help Center - Design System جدید
با Sidebar + Search + Bilingual Content
"""

import tkinter as tk
from tkinter import ttk
import re
from typing import Optional, List, Dict

from gui.theme import (
    get_color, font, sp, pad, h, w, ico,
)
from gui.components import (
    BaseDialog, PrimaryButton, SecondaryButton, GhostButton,
    IconButton, SearchInput, Separator, ToastManager,
)
from .help_content import HELP_SECTIONS, get_section


class HelpDialog(BaseDialog):
    """
    Help Center با Sidebar + Search
    """
    
    def __init__(self, parent):
        self.current_section = 'user_guide'
        self.section_buttons = {}
        
        super().__init__(
            parent,
            title="Help Center",
            width=1100,
            height=700,
            resizable=True,
        )
    
    def build_body(self, parent):
        """ساخت محتوای دیالوگ"""
        
        # ===== Main Container =====
        main = tk.Frame(parent, bg=get_color('bg_app'))
        main.pack(fill=tk.BOTH, expand=True)
        
        # ===== Sidebar =====
        self._build_sidebar(main)
        
        # ===== Content =====
        self._build_content(main)
        
        # ===== نمایش بخش اول =====
        self._show_section('user_guide')
    
    # ================================================================
    # SIDEBAR
    # ================================================================
    
    def _build_sidebar(self, parent):
        """ساخت Sidebar"""
        sidebar = tk.Frame(
            parent,
            bg=get_color('bg_surface'),
            width=250,
        )
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # ===== Header =====
        header = tk.Frame(sidebar, bg=get_color('bg_surface_alt'), height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=f"  {ico('book_open')}  Help Topics",
            font=font('h3'),
            bg=get_color('bg_surface_alt'),
            fg=get_color('text_primary'),
        ).pack(side=tk.LEFT, padx=sp('sm'), pady=sp('md'))
        
        # ===== Sections List =====
        sections_frame = tk.Frame(sidebar, bg=get_color('bg_surface'))
        sections_frame.pack(fill=tk.BOTH, expand=True, padx=sp('sm'), pady=sp('sm'))
        
        for section_id, section_data in HELP_SECTIONS.items():
            self._create_section_button(sections_frame, section_id, section_data)
    
    def _create_section_button(self, parent, section_id: str, section_data: dict):
        """ساخت دکمه بخش"""
        # ===== Frame برای هر دکمه =====
        btn_frame = tk.Frame(
            parent,
            bg=get_color('bg_surface'),
            height=40,
        )
        btn_frame.pack(fill=tk.X, pady=1)
        btn_frame.pack_propagate(False)
        
        # ===== Icon =====
        icon_label = tk.Label(
            btn_frame,
            text=ico(section_data.get('icon', 'info_circle')),
            font=('Segoe UI', 12),
            bg=get_color('bg_surface'),
            fg=get_color('text_secondary'),
        )
        icon_label.pack(side=tk.LEFT, padx=(sp('md'), sp('sm')))
        
        # ===== Text =====
        text_label = tk.Label(
            btn_frame,
            text=section_data['title_en'],
            font=font('body'),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
            anchor='w',
        )
        text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # ===== رویدادها =====
        widgets = [btn_frame, icon_label, text_label]
        
        for widget in widgets:
            widget.configure(cursor='hand2')
            widget.bind(
                '<Button-1>',
                lambda e, sid=section_id: self._show_section(sid)
            )
            widget.bind(
                '<Enter>',
                lambda e, w=widgets, sid=section_id: self._on_hover(w, sid, True)
            )
            widget.bind(
                '<Leave>',
                lambda e, w=widgets, sid=section_id: self._on_hover(w, sid, False)
            )
        
        # ===== ذخیره =====
        self.section_buttons[section_id] = {
            'frame': btn_frame,
            'icon': icon_label,
            'text': text_label,
            'widgets': widgets,
        }
    
    def _on_hover(self, widgets, section_id: str, hover: bool):
        """افکت hover"""
        # فقط اگر section جاری نباشد
        if section_id == self.current_section:
            return
        
        bg = get_color('bg_hover') if hover else get_color('bg_surface')
        
        for widget in widgets:
            widget.configure(bg=bg)
    
    def _highlight_section(self, section_id: str):
        """هایلایت بخش فعال"""
        for sid, btn in self.section_buttons.items():
            if sid == section_id:
                # فعال
                color = get_color('primary')
                bg = get_color('bg_selected')
            else:
                # غیرفعال
                color = get_color('text_secondary')
                bg = get_color('bg_surface')
            
            btn['frame'].configure(bg=bg)
            btn['icon'].configure(bg=bg, fg=color)
            btn['text'].configure(bg=bg, fg=get_color('text_primary') if sid == section_id else get_color('text_secondary'))
    
    # ================================================================
    # CONTENT
    # ================================================================
    
    def _build_content(self, parent):
        """ساخت ناحیه محتوا"""
        content = tk.Frame(parent, bg=get_color('bg_app'))
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # ===== Search Bar =====
        search_frame = tk.Frame(content, bg=get_color('bg_app'))
        search_frame.pack(fill=tk.X, padx=sp('lg'), pady=sp('md'))
        
        self.search = SearchInput(
            search_frame,
            placeholder="Search in help...",
            on_change=self._on_search,
        )
        self.search.pack(fill=tk.X)
        
        # ===== Content Area =====
        content_area = tk.Frame(content, bg=get_color('bg_app'))
        content_area.pack(fill=tk.BOTH, expand=True, padx=sp('lg'), pady=(0, sp('md')))
        
        # ===== Title =====
        self.title_label = tk.Label(
            content_area,
            text="",
            font=font('h1'),
            bg=get_color('bg_app'),
            fg=get_color('text_primary'),
            anchor='w',
        )
        self.title_label.pack(fill=tk.X, pady=(0, sp('sm')))
        
        # ===== Separator =====
        Separator(content_area, spacing=sp('sm'))
        
        # ===== Text =====
        text_frame = tk.Frame(content_area, bg=get_color('bg_surface'))
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_area = tk.Text(
            text_frame,
            font=font('mono'),
            bg=get_color('bg_surface'),
            fg=get_color('text_primary'),
            insertbackground=get_color('text_primary'),
            relief='flat',
            border=0,
            wrap=tk.WORD,
            padx=sp('lg'),
            pady=sp('md'),
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # ===== Scrollbar =====
        scrollbar = ttk.Scrollbar(
            text_frame,
            orient='vertical',
            command=self.text_area.yview,
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.configure(yscrollcommand=scrollbar.set)
        
        # ===== Read-Only =====
        self.text_area.configure(state='disabled')
    
    def _show_section(self, section_id: str):
        """نمایش یک بخش"""
        section = get_section(section_id)
        if not section:
            return
        
        self.current_section = section_id
        
        # ===== Title =====
        title = f"{section['title_en']}  |  {section['title_fa']}"
        self.title_label.configure(text=title)
        
        # ===== Content =====
        content = section.get('content', '')
        self._set_text(content)
        
        # ===== Highlight =====
        self._highlight_section(section_id)
    
    def _set_text(self, text: str):
        """تنظیم متن"""
        self.text_area.configure(state='normal')
        self.text_area.delete('1.0', tk.END)
        self.text_area.insert('1.0', text)
        self.text_area.configure(state='disabled')
    
    # ================================================================
    # SEARCH
    # ================================================================
    
    def _on_search(self, query: str):
        """جستجو در Help"""
        if not query or not query.strip():
            self._show_section(self.current_section)
            return
        
        query = query.lower().strip()
        results = []
        
        # جستجو در همه بخش‌ها
        for section_id, section_data in HELP_SECTIONS.items():
            content = section_data.get('content', '').lower()
            title_en = section_data.get('title_en', '').lower()
            title_fa = section_data.get('title_fa', '')
            
            # اگر در عنوان یا محتوا پیدا شد
            if query in content or query in title_en or query in title_fa:
                results.append({
                    'section_id': section_id,
                    'title_en': section_data.get('title_en', ''),
                    'title_fa': section_data.get('title_fa', ''),
                    'content': section_data.get('content', ''),
                })
        
        # نمایش نتایج
        if results:
            self._show_search_results(query, results)
        else:
            self._show_no_results(query)
    
    def _show_search_results(self, query: str, results: List[Dict]):
        """نمایش نتایج جستجو"""
        self.title_label.configure(text=f"Search results for: '{query}'")
        
        text = f"Found {len(results)} result(s):\n"
        text += "=" * 60 + "\n\n"
        
        for i, result in enumerate(results, 1):
            text += f"{i}. {result['title_en']} / {result['title_fa']}\n"
            
            # نمایش بخشی از محتوا
            content = result['content'].lower()
            idx = content.find(query.lower())
            
            if idx >= 0:
                start = max(0, idx - 50)
                end = min(len(content), idx + 100)
                snippet = result['content'][start:end]
                text += f"   ...{snippet}...\n"
            
            text += "\n" + "-" * 60 + "\n\n"
        
        text += "\nClick on a section in the sidebar to view full content.\n"
        
        self._set_text(text)
    
    def _show_no_results(self, query: str):
        """نمایش عدم نتیجه"""
        self.title_label.configure(text=f"No results for: '{query}'")
        
        text = f"No results found for: '{query}'\n"
        text += "=" * 60 + "\n\n"
        text += "Try different keywords or browse the sections in the sidebar.\n"
        
        self._set_text(text)
    
    def _build_footer(self):
        """Footer"""
        footer = tk.Frame(self, bg=get_color('bg_surface'), height=60)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        btn_frame = tk.Frame(footer, bg=get_color('bg_surface'))
        btn_frame.pack(side=tk.RIGHT, padx=sp('lg'), pady=sp('md'))
        
        PrimaryButton(
            btn_frame,
            text="Close",
            command=self.on_cancel,
        ).pack()


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['HelpDialog']