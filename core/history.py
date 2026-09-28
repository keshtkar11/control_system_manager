"""مدیریت تاریخچه عملیات برای Undo/Redo"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import copy

from .models import ProjectSection
import logging
logger = logging.getLogger(__name__)

class HistoryManager:
    """مدیریت تاریخچه عملیات (پشتیبانی از Revision)"""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.current_state: Optional[Dict[str, Any]] = None
        self._initial_state_saved = False
    
    def push_state(self, project_name: str, sections: List[ProjectSection],
                   revision_name: str = None):
        """
        ذخیره حالت فعلی در تاریخچه
        
        Args:
            project_name: نام پروژه
            sections: لیست بخش‌های پروژه
            revision_name: نام رویژن (اختیاری - جدید)
        """
        # ایجاد کپی عمیق از بخش‌ها
        sections_copy = [section.copy() for section in sections]
        
        state = {
            'project_name': project_name,
            'revision_name': revision_name,      # ✅ جدید
            'sections': sections_copy,
            'timestamp': datetime.now()
        }
        
        # اگر حالت جاری وجود دارد، آن را به تاریخچه اضافه کن
        if self.current_state:
            self.history.append(self.current_state)
        elif not self._initial_state_saved:
            # اگر اولین حالت است، آن را هم ذخیره کن
            self._initial_state_saved = True
        
        # تنظیم حالت جاری
        self.current_state = state
        
        # پاک کردن stack Redo
        self.redo_stack.clear()
        
        # محدود کردن اندازه تاریخچه
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    def undo(self) -> Optional[Dict[str, Any]]:
        """
        بازگشت به حالت قبلی
        
        Returns:
            حالت قبلی یا None اگر وجود نداشته باشد
        """
        if not self.history:
            return None
        
        # ذخیره حالت فعلی در Redo
        if self.current_state:
            self.redo_stack.append(self.current_state)
        
        # بازیابی حالت قبلی
        self.current_state = self.history.pop()
        return self.current_state
    
    def redo(self) -> Optional[Dict[str, Any]]:
        """
        بازگشت به حالت بعدی
        
        Returns:
            حالت بعدی یا None اگر وجود نداشته باشد
        """
        if not self.redo_stack:
            return None
        
        # ذخیره حالت فعلی در تاریخچه
        if self.current_state:
            self.history.append(self.current_state)
        
        # بازیابی حالت بعدی
        self.current_state = self.redo_stack.pop()
        return self.current_state
    
    def can_undo(self) -> bool:
        """بررسی امکان Undo"""
        return len(self.history) > 0
    
    def can_redo(self) -> bool:
        """بررسی امکان Redo"""
        return len(self.redo_stack) > 0
    
    def get_history_info(self) -> Dict[str, Any]:
        """دریافت اطلاعات تاریخچه"""
        return {
            'undo_count': len(self.history),
            'redo_count': len(self.redo_stack),
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo(),
            'current_project': self.current_state.get('project_name') if self.current_state else None,
            'current_revision': self.current_state.get('revision_name') if self.current_state else None,  # ✅ جدید
        }
    
    def clear(self):
        """پاک کردن کامل تاریخچه"""
        self.history.clear()
        self.redo_stack.clear()
        self.current_state = None
        self._initial_state_saved = False
    
    def get_last_state(self) -> Optional[Dict[str, Any]]:
        """دریافت آخرین حالت ذخیره شده"""
        if self.history:
            return self.history[-1]
        return self.current_state

    def clear_project(self, project_name: str):
        """
        پاک کردن History برای یک پروژه خاص
        
        زمانی استفاده می‌شود که پروژه Rename می‌شود
        (چون نام قدیمی دیگر معتبر نیست)
        
        Args:
            project_name: نام پروژه‌ای که History آن پاک می‌شود
        """
        # ===== فیلتر History =====
        self.history = [
            state for state in self.history
            if state.get('project_name') != project_name
        ]
        
        # ===== فیلتر Redo Stack =====
        self.redo_stack = [
            state for state in self.redo_stack
            if state.get('project_name') != project_name
        ]
        
        # ===== پاک کردن Current State =====
        if (self.current_state and 
            self.current_state.get('project_name') == project_name):
            self.current_state = None
            self._initial_state_saved = False
        
        logger.debug(f"History cleared for project '{project_name}'")