# ai/proposal_importer.py
"""
Import پروپوزال از فایل Word

قابلیت‌ها:
- استخراج متن از .docx
- تشخیص نوع سکشن بر اساس کلیدواژه
- ذخیره در دیتابیس به عنوان قالب جدید
- پشتیبانی از چند قالب برای هر نوع سکشن
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from docx import Document

from ai.proposal_section_detector import ProposalSectionDetector

logger = logging.getLogger(__name__)


class ProposalImporter:
    """
    Import پروپوزال از فایل Word
    """
    
    def __init__(self, db_manager, app):
        self.db = db_manager
        self.app = app
        self.detector = ProposalSectionDetector()
        
        self._ensure_db_table()
    
    # ================================================================
    # DB SETUP
    # ================================================================
    
    def _ensure_db_table(self):
        """ایجاد جدول proposal_templates در دیتابیس"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proposal_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section_type TEXT NOT NULL,
                    template_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT DEFAULT 'imported',
                    usage_count INTEGER DEFAULT 0,
                    last_used TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            conn.commit()
            logger.info("✅ proposal_templates table ensured")
        
        except Exception as e:
            logger.error(f"❌ Could not create proposal_templates table: {e}")
    
    # ================================================================
    # EXTRACT FROM DOCX
    # ================================================================
    
    def extract_from_docx(self, docx_path: str) -> Optional[str]:
        """
        استخراج متن از فایل Word
        
        Args:
            docx_path: مسیر فایل .docx
        
        Returns:
            متن استخراج‌شده یا None
        """
        try:
            if not os.path.exists(docx_path):
                logger.error(f"❌ File not found: {docx_path}")
                return None
            
            doc = Document(docx_path)
            
            # ===== استخراج پاراگراف‌ها =====
            lines = []
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    lines.append(text)
            
            content = "\n".join(lines)
            
            logger.info(f"✅ Extracted {len(content)} chars from {os.path.basename(docx_path)}")
            return content
        
        except Exception as e:
            logger.error(f"❌ Error extracting from docx: {e}", exc_info=True)
            return None
    
    # ================================================================
    # SPLIT INTO SECTIONS
    # ================================================================
    
    def split_into_sections(self, content: str) -> Dict[str, str]:
        """
        تقسیم پروپوزال به بخش‌های تخصصی
        
        تشخیص بر اساس عناوین:
        - "سناریوی کنترلی سیستم X"
        - "X SYSTEM CONTROL SCENARIO"
        - "بخش X"
        
        Returns:
            dict: {section_type: text}
        """
        sections = {}
        
        # ===== الگوهای عنوان =====
        header_patterns = [
            r'سناریو(?:ی)?\s+کنترل(?:ی)?\s+(?:سیستم\s+)?(.+?)(?:\n|$)',
            r'بخش\s+(.+?)(?:\n|$)',
            r'(.+?)\s+SYSTEM\s+CONTROL',
            r'###\s+(.+?)(?:\n|$)',
            r'##\s+(.+?)(?:\n|$)',
        ]
        
        lines = content.split('\n')
        
        current_section_type = None
        current_section_name = None
        current_content = []
        
        for line in lines:
            # ===== چک: آیا خط یک عنوان است؟ =====
            detected_type = None
            detected_name = None
            
            for pattern in header_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    header_text = match.group(1).strip()
                    # تشخیص نوع سکشن
                    detected_type = self.detector.detect(header_text, "")
                    if detected_type:
                        detected_name = header_text
                        break
            
            if detected_type:
                # ===== ذخیره سکشن قبلی =====
                if current_section_type and current_content:
                    sections[current_section_type] = "\n".join(current_content).strip()
                
                # ===== شروع سکشن جدید =====
                current_section_type = detected_type
                current_section_name = detected_name
                current_content = [line]
            elif current_section_type:
                current_content.append(line)
        
        # ===== ذخیره آخرین سکشن =====
        if current_section_type and current_content:
            sections[current_section_type] = "\n".join(current_content).strip()
        
        logger.info(f"✅ Split into {len(sections)} sections: {list(sections.keys())}")
        
        return sections
    
    # ================================================================
    # SAVE TEMPLATE
    # ================================================================
    
    def save_template(
        self,
        section_type: str,
        template_name: str,
        content: str,
        source: str = 'imported',
    ) -> bool:
        """
        ذخیره قالب در دیتابیس — بدون تکرار
        
        اگر قالب با همین نام و نوع قبلاً ذخیره شده:
        - content را به‌روزرسانی می‌کند
        - usage_count را حفظ می‌کند
        
        Returns:
            True اگر موفق باشد
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            # ===== چک وجود =====
            cursor.execute('''
                SELECT id FROM proposal_templates
                WHERE section_type = ? AND template_name = ?
            ''', (section_type, template_name))
            
            existing = cursor.fetchone()
            
            if existing:
                # ===== به‌روزرسانی =====
                cursor.execute('''
                    UPDATE proposal_templates
                    SET content = ?, source = ?, updated_at = ?
                    WHERE id = ?
                ''', (content, source, now, existing[0]))
                
                logger.info(f"✅ Template updated: {section_type}/{template_name}")
            else:
                # ===== درج جدید =====
                cursor.execute('''
                    INSERT INTO proposal_templates
                    (section_type, template_name, content, source,
                    usage_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 0, ?, ?)
                ''', (section_type, template_name, content, source, now, now))
                
                logger.info(f"✅ Template saved: {section_type}/{template_name}")
            
            conn.commit()
            return True
        
        except Exception as e:
            logger.error(f"❌ Error saving template: {e}", exc_info=True)
            return False
    
    # ================================================================
    # MAIN IMPORT
    # ================================================================
    
    def import_from_docx(
        self,
        docx_path: str,
        auto_detect: bool = True,
    ) -> Dict[str, Any]:
        """
        Import کامل یک فایل Word
        
        Args:
            docx_path: مسیر فایل
            auto_detect: تشخیص خودکار سکشن‌ها
        
        Returns:
            dict: {
                'success': bool,
                'sections_found': list,
                'sections_saved': list,
                'errors': list,
            }
        """
        result = {
            'success': False,
            'sections_found': [],
            'sections_saved': [],
            'errors': [],
        }
        
        try:
            # ===== ۱. استخراج =====
            content = self.extract_from_docx(docx_path)
            if not content:
                result['errors'].append("استخراج متن ناموفق بود")
                return result
            
            # ===== ۲. تقسیم به بخش‌ها =====
            sections = self.split_into_sections(content)
            result['sections_found'] = list(sections.keys())
            
            if not sections:
                result['errors'].append("هیچ سکشن تخصصی در پروپوزال یافت نشد")
                return result
            
            # ===== ۳. ذخیره در دیتابیس =====
            file_name = Path(docx_path).stem
            
            for section_type, section_content in sections.items():
                template_name = f"{section_type}_{file_name}"
                
                success = self.save_template(
                    section_type=section_type,
                    template_name=template_name,
                    content=section_content,
                    source='imported',
                )
                
                if success:
                    result['sections_saved'].append({
                        'type': section_type,
                        'name': template_name,
                        'length': len(section_content),
                    })
                else:
                    result['errors'].append(f"ذخیره {section_type} ناموفق")
            
            result['success'] = len(result['sections_saved']) > 0
            return result
        
        except Exception as e:
            logger.error(f"❌ Error importing docx: {e}", exc_info=True)
            result['errors'].append(str(e))
            return result
    
    # ================================================================
    # GET TEMPLATES
    # ================================================================
    
    def get_templates_for_section(self, section_type: str) -> List[Dict]:
        """دریافت همه قالب‌های یک نوع سکشن"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, section_type, template_name, content,
                       source, usage_count, last_used, created_at
                FROM proposal_templates
                WHERE section_type = ?
                ORDER BY usage_count DESC, updated_at DESC
            ''', (section_type,))
            
            result = []
            for row in cursor.fetchall():
                result.append({
                    'id': row[0],
                    'section_type': row[1],
                    'template_name': row[2],
                    'content': row[3],
                    'source': row[4],
                    'usage_count': row[5],
                    'last_used': row[6],
                    'created_at': row[7],
                })
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Error getting templates: {e}")
            return []
    
    def get_best_template(self, section_type: str) -> Optional[str]:
        """
        دریافت بهترین قالب برای یک نوع سکشن
        
        اولویت:
        1. بیشترین usage_count
        2. جدیدترین updated_at
        """
        templates = self.get_templates_for_section(section_type)
        
        if templates:
            return templates[0]['content']
        
        return None
    
    def get_all_templates_summary(self) -> Dict[str, List[Dict]]:
        """دریافت خلاصه‌ی همه قالب‌ها"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, section_type, template_name, source,
                       usage_count, LENGTH(content), created_at
                FROM proposal_templates
                ORDER BY section_type, usage_count DESC
            ''')
            
            result = {}
            for row in cursor.fetchall():
                section_type = row[1]
                if section_type not in result:
                    result[section_type] = []
                
                result[section_type].append({
                    'id': row[0],
                    'template_name': row[2],
                    'source': row[3],
                    'usage_count': row[4],
                    'length': row[5],
                    'created_at': row[6],
                })
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Error getting summary: {e}")
            return {}
    
    # ================================================================
    # DELETE
    # ================================================================
    
    def delete_template(self, template_id: int) -> bool:
        """حذف قالب"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM proposal_templates WHERE id = ?", (template_id,))
            conn.commit()
            
            return cursor.rowcount > 0
        
        except Exception as e:
            logger.error(f"❌ Error deleting template: {e}")
            return False


# ================================================================
# EXPORTS
# ================================================================

__all__ = ['ProposalImporter']