"""
مدیریت پیوست‌های پروژه (Attachments)

قابلیت‌ها:
- افزودن فایل به پوشه پیوست پروژه
- حذف فایل (Recycle Bin)
- باز کردن فایل با برنامه پیش‌فرض
- نمایش در File Explorer
- تغییر نام
- لیست فایل‌های پیوست
"""

import os
import shutil
import subprocess
import re
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AttachmentManager:
    """
    مدیریت پیوست‌های پروژه
    
    ساختار پوشه:
        <APP_DATA_PATH>/
        └── Attachments/
            ├── Project A/
            │   ├── drawing.dwg
            │   ├── contract.pdf
            │   └── BOQ.xlsx
            └── Project B/
                └── ...
    """
    
    def __init__(self, db_manager):
        """
        Args:
            db_manager: نمونه DatabaseManager
        """
        self.db = db_manager
        self._base_dir = None  # Lazy Loading
        logger.info("AttachmentManager initialized")
    
    # ================================================================
    # مسیرها
    # ================================================================
    
    @property
    def base_dir(self) -> str:
        """مسیر پایه پوشه پیوست‌ها (Lazy)"""
        if self._base_dir is None:
            from core.constants import APP_DATA_PATH
            self._base_dir = os.path.join(APP_DATA_PATH, 'Attachments')
            os.makedirs(self._base_dir, exist_ok=True)
        return self._base_dir
    
    def _sanitize_name(self, name: str) -> str:
        """پاکسازی نام برای استفاده در مسیر فایل"""
        safe = "".join(
            c if c.isalnum() or c in " _-" else "_"
            for c in name
        ).strip()
        return safe or "Project"
    
    def get_project_dir(self, project_name: str) -> str:
        """
        مسیر پوشه پیوست یک پروژه
        
        Args:
            project_name: نام پروژه
        
        Returns:
            مسیر کامل پوشه
        """
        safe_name = self._sanitize_name(project_name)
        return os.path.join(self.base_dir, safe_name)
    
    def ensure_project_dir(self, project_name: str) -> str:
        """اطمینان از وجود پوشه پیوست پروژه"""
        project_dir = self.get_project_dir(project_name)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir
    
    # ================================================================
    # افزودن فایل
    # ================================================================
    
    def _get_unique_filename(self, folder: str, filename: str) -> str:
        """
        اگر فایل تکراری بود، نام یکتا بساز
        
        Args:
            folder: پوشه مقصد
            filename: نام فایل
        
        Returns:
            نام یکتا (drawing.dwg / drawing_Copy1.dwg / ...)
        """
        dest_path = os.path.join(folder, filename)
        
        if not os.path.exists(dest_path):
            return filename
        
        # جدا کردن نام و پسوند
        name, ext = os.path.splitext(filename)
        counter = 1
        
        while True:
            new_name = f"{name}_Copy{counter}{ext}"
            new_path = os.path.join(folder, new_name)
            if not os.path.exists(new_path):
                return new_name
            counter += 1
            
            # حداکثر 10000 تلاش
            if counter > 10000:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                return f"{name}_{timestamp}{ext}"
    
    def add_file(self, project_name: str, source_path: str) -> Dict[str, Any]:
        """
        افزودن یک فایل به پیوست‌های پروژه
        
        Args:
            project_name: نام پروژه
            source_path: مسیر فایل مبدأ
        
        Returns:
            دیکشنری نتیجه: {'success': bool, 'file_name': str, 'error': str}
        """
        result = {'success': False, 'file_name': None, 'error': None}
        
        # ===== بررسی وجود فایل مبدأ =====
        if not os.path.exists(source_path):
            result['error'] = f"Source file not found: {source_path}"
            logger.warning(result['error'])
            return result
        
        if not os.path.isfile(source_path):
            result['error'] = f"Not a file: {source_path}"
            return result
        
        try:
            # ===== اطمینان از وجود پوشه =====
            project_dir = self.ensure_project_dir(project_name)
            
            # ===== نام فایل مبدأ =====
            original_name = os.path.basename(source_path)
            
            # ===== اگر تکراری بود، نام یکتا بساز =====
            unique_name = self._get_unique_filename(project_dir, original_name)
            
            # ===== مقصد =====
            dest_path = os.path.join(project_dir, unique_name)
            
            # ===== کپی فایل =====
            shutil.copy2(source_path, dest_path)
            
            # ===== اطلاعات فایل =====
            file_size = os.path.getsize(dest_path)
            file_ext = os.path.splitext(unique_name)[1].lower().replace('.', '')
            
            # ===== ذخیره در دیتابیس =====
            attachment_data = {
                'project_name': project_name,
                'file_name': unique_name,
                'file_path': dest_path,
                'file_size': file_size,
                'file_type': file_ext,
                'description': '',
            }
            
            success = self.db.add_attachment(attachment_data)
            
            if success:
                result['success'] = True
                result['file_name'] = unique_name
                logger.info(f"✅ Attachment added: {unique_name} → {project_name}")
            else:
                # اگر دیتابیس خطا داد، فایل کپی شده را حذف کن
                try:
                    os.remove(dest_path)
                except:
                    pass
                result['error'] = "Failed to save attachment to database"
            
            return result
        
        except PermissionError as e:
            result['error'] = f"Permission denied: {e}"
            logger.error(result['error'])
            return result
        except OSError as e:
            result['error'] = f"File error: {e}"
            logger.error(result['error'])
            return result
        except Exception as e:
            result['error'] = f"Unexpected error: {e}"
            logger.error(f"❌ Error adding attachment: {e}", exc_info=True)
            return result
    
    def add_files(self, project_name: str, source_paths: List[str]) -> Dict[str, Any]:
        """
        افزودن چند فایل به پیوست‌های پروژه
        
        Returns:
            دیکشنری: {
                'added': int,
                'failed': int,
                'skipped': int,
                'errors': List[str],
                'added_files': List[str]
            }
        """
        result = {
            'added': 0,
            'failed': 0,
            'skipped': 0,
            'errors': [],
            'added_files': []
        }
        
        for source_path in source_paths:
            res = self.add_file(project_name, source_path)
            
            if res['success']:
                result['added'] += 1
                result['added_files'].append(res['file_name'])
            else:
                result['failed'] += 1
                if res['error']:
                    result['errors'].append(
                        f"{os.path.basename(source_path)}: {res['error']}"
                    )
        
        logger.info(
            f"📎 Add files result: "
            f"{result['added']} added, {result['failed']} failed"
        )
        return result
    
    def add_folder(self, project_name: str, folder_path: str,
                   recursive: bool = False) -> Dict[str, Any]:
        """
        افزودن تمام فایل‌های یک پوشه
        
        Args:
            project_name: نام پروژه
            folder_path: مسیر پوشه
            recursive: شامل زیرپوشه‌ها
        
        Returns:
            مثل add_files
        """
        if not os.path.isdir(folder_path):
            return {
                'added': 0, 'failed': 0, 'skipped': 0,
                'errors': [f"Not a folder: {folder_path}"],
                'added_files': []
            }
        
        file_paths = []
        
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_paths.append(os.path.join(root, file))
        else:
            for entry in os.listdir(folder_path):
                full_path = os.path.join(folder_path, entry)
                if os.path.isfile(full_path):
                    file_paths.append(full_path)
        
        return self.add_files(project_name, file_paths)
    
    # ================================================================
    # لیست فایل‌ها
    # ================================================================
    
    def get_files(self, project_name: str) -> List[Dict[str, Any]]:
        """
        دریافت لیست فایل‌های پیوست یک پروژه
        
        Returns:
            لیست دیکشنری‌ها با اطلاعات فایل
        """
        try:
            files = self.db.get_attachments(project_name)
            
            # بررسی وجود فیزیکی + دریافت اطلاعات به‌روز
            valid_files = []
            for f in files:
                file_path = f.get('file_path', '')
                
                if os.path.exists(file_path):
                    # به‌روزرسانی size
                    f['file_size'] = os.path.getsize(file_path)
                    f['file_size_str'] = self._format_size(f['file_size'])
                    f['exists'] = True
                    valid_files.append(f)
                else:
                    f['exists'] = False
                    f['file_size_str'] = "N/A"
                    valid_files.append(f)
                    logger.warning(f"⚠️ Missing file: {file_path}")
            
            # مرتب‌سازی بر اساس نام (الفبایی)
            valid_files.sort(key=lambda x: x.get('file_name', '').lower())
            
            return valid_files
        
        except Exception as e:
            logger.error(f"Error getting attachments: {e}")
            return []
    
    def get_file_count(self, project_name: str) -> int:
        """تعداد فایل‌های پیوست"""
        return len(self.get_files(project_name))
    
    def get_total_size(self, project_name: str) -> int:
        """مجموع حجم فایل‌های پیوست (bytes)"""
        files = self.get_files(project_name)
        return sum(f.get('file_size', 0) for f in files if f.get('exists'))
    
    def _format_size(self, size: int) -> str:
        """تبدیل حجم به فرمت خوانا"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"
    
    # ================================================================
    # حذف فایل
    # ================================================================
    
    def remove_file(self, project_name: str, file_name: str,
                    to_recycle_bin: bool = True) -> Dict[str, Any]:
        """
        حذف یک فایل یا فولدر پیوست
        
        Args:
            project_name: نام پروژه
            file_name: نام فایل/فولدر (نه مسیر کامل)
            to_recycle_bin: اگر True، به Recycle Bin برود
        
        Returns:
            {'success': bool, 'error': str}
        """
        result = {'success': False, 'error': None}
        
        try:
            # ===== دریافت اطلاعات از دیتابیس =====
            files = self.db.get_attachments(project_name)
            target_file = None
            
            for f in files:
                if f.get('file_name') == file_name:
                    target_file = f
                    break
            
            if not target_file:
                result['error'] = f"File not found: {file_name}"
                return result
            
            file_path = target_file.get('file_path')
            is_folder = target_file.get('file_type') == 'folder'
            
            # ============================================================
            # ✅ حذف فیزیکی (فایل یا فولدر)
            # ============================================================
            if file_path and os.path.exists(file_path):
                if to_recycle_bin:
                    # ===== به Recycle Bin =====
                    success = self._send_to_recycle_bin(file_path)
                    if not success:
                        # اگر نشد، مستقیم حذف کن
                        logger.warning(f"Recycle Bin failed, deleting directly: {file_path}")
                        self._delete_physical(file_path)
                else:
                    # ===== حذف مستقیم =====
                    self._delete_physical(file_path)
                
                logger.info(f"🗑️ Removed {'folder' if is_folder else 'file'}: {file_path}")
            
            # ============================================================
            # ✅ حذف از دیتابیس
            # ============================================================
            db_success = self.db.delete_attachment(
                project_name=project_name,
                file_name=file_name
            )
            
            if db_success:
                result['success'] = True
                logger.info(f"✅ Attachment removed: {file_name}")
            else:
                result['error'] = "Failed to delete from database"
            
            return result
        
        except Exception as e:
            result['error'] = f"Error: {e}"
            logger.error(f"❌ Error removing attachment: {e}", exc_info=True)
            return result
    
    def _send_to_recycle_bin(self, file_path: str) -> bool:
        """
        ارسال فایل یا فولدر به Recycle Bin
        
        Args:
            file_path: مسیر فایل یا فولدر
        
        Returns:
            True اگر موفق باشد
        """
        # ============================================================
        # غیر ویندوز → حذف مستقیم
        # ============================================================
        if os.name != 'nt':
            return self._delete_physical(file_path)
        
        # ============================================================
        # ویندوز → تلاش با send2trash
        # ============================================================
        try:
            from send2trash import send2trash
            send2trash(file_path)
            logger.debug(f"Sent to Recycle Bin: {file_path}")
            return True
        except ImportError:
            # send2trash نصب نیست → استفاده از PowerShell
            pass
        except Exception as e:
            logger.warning(f"send2trash failed: {e}")
            return False
        
        # ============================================================
        # ✅ Fallback: PowerShell (با تفکیک فایل و فولدر)
        # ============================================================
        try:
            is_folder = os.path.isdir(file_path)
            
            # فرار از کاراکتر ' در مسیر
            safe_path = file_path.replace("'", "''")
            
            if is_folder:
                # ✅ فولدر → DeleteDirectory
                ps_command = f'''
Add-Type -AssemblyName Microsoft.VisualBasic
[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory(
    '{safe_path}',
    'OnlyErrorDialogs',
    'SendToRecycleBin'
)
'''
            else:
                # ✅ فایل → DeleteFile
                ps_command = f'''
Add-Type -AssemblyName Microsoft.VisualBasic
[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(
    '{safe_path}',
    'OnlyErrorDialogs',
    'SendToRecycleBin'
)
'''
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=15,
                check=False
            )
            
            # ===== بررسی موفقیت =====
            if result.returncode == 0 and not os.path.exists(file_path):
                logger.debug(f"Sent to Recycle Bin via PowerShell: {file_path}")
                return True
            else:
                if result.stderr:
                    logger.warning(f"PowerShell error: {result.stderr.strip()}")
                return False
        
        except Exception as e:
            logger.warning(f"PowerShell recycle bin failed: {e}")
            return False

    def _delete_physical(self, path: str) -> bool:
        """
        حذف فیزیکی یک فایل یا فولدر (بدون Recycle Bin)
        
        Args:
            path: مسیر فایل یا فولدر
        
        Returns:
            True اگر موفق باشد
        """
        try:
            if os.path.isdir(path):
                # ===== فولدر → shutil.rmtree =====
                shutil.rmtree(path, ignore_errors=False)
                logger.debug(f"Deleted folder: {path}")
            else:
                # ===== فایل → os.remove =====
                os.remove(path)
                logger.debug(f"Deleted file: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {path}: {e}", exc_info=True)
            return False
    
    # ================================================================
    # تغییر نام
    # ================================================================
    
    def rename_file(self, project_name: str, old_name: str,
                    new_name: str) -> Dict[str, Any]:
        """
        تغییر نام یک فایل پیوست
        
        Args:
            project_name: نام پروژه
            old_name: نام فعلی
            new_name: نام جدید
        
        Returns:
            {'success': bool, 'new_name': str, 'error': str}
        """
        result = {'success': False, 'new_name': None, 'error': None}
        
        # ===== اعتبارسنجی =====
        if not new_name or not new_name.strip():
            result['error'] = "New name cannot be empty"
            return result
        
        new_name = new_name.strip()
        
        # حذف کاراکترهای غیرمجاز
        new_name = re.sub(r'[<>:"/\\|?*]', '_', new_name)
        
        if new_name == old_name:
            result['success'] = True
            result['new_name'] = new_name
            return result
        
        try:
            # ===== دریافت اطلاعات فایل =====
            files = self.db.get_attachments(project_name)
            target_file = None
            
            for f in files:
                if f.get('file_name') == old_name:
                    target_file = f
                    break
            
            if not target_file:
                result['error'] = f"File not found: {old_name}"
                return result
            
            old_path = target_file.get('file_path')
            
            if not old_path or not os.path.exists(old_path):
                result['error'] = "Physical file not found"
                return result
            
            # ===== بررسی تکراری نبودن نام جدید =====
            project_dir = os.path.dirname(old_path)
            new_path_check = os.path.join(project_dir, new_name)
            
            if os.path.exists(new_path_check) and new_path_check != old_path:
                result['error'] = f"File '{new_name}' already exists"
                return result
            
            # ===== تغییر نام فیزیکی =====
            new_path = os.path.join(project_dir, new_name)
            os.rename(old_path, new_path)
            
            # ===== به‌روزرسانی دیتابیس =====
            db_success = self.db.rename_attachment(
                project_name=project_name,
                old_name=old_name,
                new_name=new_name,
                new_path=new_path
            )
            
            if db_success:
                result['success'] = True
                result['new_name'] = new_name
                logger.info(f"✏️ Renamed: {old_name} → {new_name}")
            else:
                # برگرداندن نام فایل
                try:
                    os.rename(new_path, old_path)
                except:
                    pass
                result['error'] = "Failed to update database"
            
            return result
        
        except Exception as e:
            result['error'] = f"Error: {e}"
            logger.error(f"❌ Error renaming: {e}", exc_info=True)
            return result
    
    # ================================================================
    # باز کردن فایل / پوشه
    # ================================================================
    
    def open_file(self, project_name: str, file_name: str) -> Dict[str, Any]:
        """
        باز کردن فایل با برنامه پیش‌فرض
        
        Returns:
            {'success': bool, 'error': str}
        """
        result = {'success': False, 'error': None}
        
        try:
            # ===== دریافت مسیر =====
            files = self.db.get_attachments(project_name)
            target_file = None
            
            for f in files:
                if f.get('file_name') == file_name:
                    target_file = f
                    break
            
            if not target_file:
                result['error'] = f"File not found: {file_name}"
                return result
            
            file_path = target_file.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                result['error'] = "Physical file not found"
                return result
            
            # ===== باز کردن =====
            if os.name == 'nt':
                os.startfile(file_path)
            elif os.name == 'posix':
                subprocess.Popen(['xdg-open', file_path])
            else:
                result['error'] = "Unsupported OS"
                return result
            
            result['success'] = True
            return result
        
        except Exception as e:
            result['error'] = f"Error: {e}"
            logger.error(f"❌ Error opening file: {e}")
            return result
    
    def open_folder(self, project_name: str) -> Dict[str, Any]:
        """
        باز کردن پوشه پیوست‌های پروژه در File Explorer
        
        Returns:
            {'success': bool, 'error': str}
        """
        result = {'success': False, 'error': None}
        
        try:
            project_dir = self.ensure_project_dir(project_name)
            
            if os.name == 'nt':
                os.startfile(project_dir)
            elif os.name == 'posix':
                subprocess.Popen(['xdg-open', project_dir])
            else:
                result['error'] = "Unsupported OS"
                return result
            
            result['success'] = True
            logger.info(f"📁 Opened folder: {project_dir}")
            return result
        
        except Exception as e:
            result['error'] = f"Error: {e}"
            logger.error(f"❌ Error opening folder: {e}")
            return result
    
    def show_in_explorer(self, project_name: str, file_name: str) -> Dict[str, Any]:
        """
        نمایش فایل در File Explorer (انتخاب شده)
        
        Returns:
            {'success': bool, 'error': str}
        """
        result = {'success': False, 'error': None}
        
        try:
            files = self.db.get_attachments(project_name)
            target_file = None
            
            for f in files:
                if f.get('file_name') == file_name:
                    target_file = f
                    break
            
            if not target_file:
                result['error'] = f"File not found: {file_name}"
                return result
            
            file_path = target_file.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                result['error'] = "Physical file not found"
                return result
            
            # ===== نمایش در Explorer =====
            if os.name == 'nt':
                subprocess.Popen(['explorer', '/select,', os.path.normpath(file_path)])
            elif os.name == 'posix':
                # Linux: open parent folder
                parent_dir = os.path.dirname(file_path)
                subprocess.Popen(['xdg-open', parent_dir])
            else:
                result['error'] = "Unsupported OS"
                return result
            
            result['success'] = True
            return result
        
        except Exception as e:
            result['error'] = f"Error: {e}"
            logger.error(f"❌ Error showing in explorer: {e}")
            return result
    
    def export_file(self, project_name: str, file_name: str,
                    dest_path: str) -> Dict[str, Any]:
        """
        کپی فایل پیوست به مسیر دیگر (Export)
        
        Returns:
            {'success': bool, 'error': str}
        """
        result = {'success': False, 'error': None}
        
        try:
            files = self.db.get_attachments(project_name)
            target_file = None
            
            for f in files:
                if f.get('file_name') == file_name:
                    target_file = f
                    break
            
            if not target_file:
                result['error'] = f"File not found: {file_name}"
                return result
            
            file_path = target_file.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                result['error'] = "Physical file not found"
                return result
            
            # ===== کپی =====
            shutil.copy2(file_path, dest_path)
            result['success'] = True
            logger.info(f"📤 Exported: {file_name} → {dest_path}")
            return result
        
        except Exception as e:
            result['error'] = f"Error: {e}"
            return result
    
    # ================================================================
    # پاکسازی
    # ================================================================
    
    def cleanup_missing_files(self, project_name: str) -> Dict[str, Any]:
        """
        حذف رکوردهای دیتابیس که فایل فیزیکی ندارند
        
        Returns:
            {'removed': int}
        """
        result = {'removed': 0}
        
        try:
            files = self.db.get_attachments(project_name)
            
            for f in files:
                file_path = f.get('file_path')
                if not file_path or not os.path.exists(file_path):
                    self.db.delete_attachment(
                        project_name=project_name,
                        file_name=f['file_name']
                    )
                    result['removed'] += 1
                    logger.info(f"🗑️ Removed missing file record: {f['file_name']}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error cleaning missing files: {e}")
            return result
    
    def delete_all_files(self, project_name: str) -> Dict[str, Any]:
        """
        حذف تمام فایل‌های پیوست یک پروژه
        
        Returns:
            {'success': bool, 'count': int, 'error': str}
        """
        result = {'success': False, 'count': 0, 'error': None}
        
        try:
            # حذف پوشه فیزیکی
            project_dir = self.get_project_dir(project_name)
            
            if os.path.exists(project_dir):
                if os.name == 'nt':
                    try:
                        from send2trash import send2trash
                        send2trash(project_dir)
                    except ImportError:
                        shutil.rmtree(project_dir, ignore_errors=True)
                else:
                    shutil.rmtree(project_dir, ignore_errors=True)
            
            # حذف رکوردهای دیتابیس
            count = self.db.delete_all_attachments(project_name)
            result['success'] = True
            result['count'] = count
            
            logger.info(f"🗑️ Deleted all attachments for '{project_name}' ({count} files)")
            return result
        
        except Exception as e:
            result['error'] = f"Error: {e}"
            logger.error(f"❌ Error deleting all attachments: {e}")
            return result

    # ================================================================
    # ✅ همگام‌سازی با فایل‌سیستم
    # ================================================================

    def sync_with_filesystem(self, project_name: str) -> Dict[str, Any]:
        """
        اسکن پوشه پروژه و همگام‌سازی با دیتابیس
        
        فایل‌های موجود در پوشه که در DB نیستن → اضافه می‌شن
        رکوردهای DB که فایل فیزیکی ندارن → حذف می‌شن
        
        Args:
            project_name: نام پروژه
        
        Returns:
            {
                'added': int,      # تعداد فایل/پوشه اضافه شده به DB
                'removed': int,    # تعداد رکورد حذف شده از DB
                'skipped': int,    # تعداد فایل‌های رد شده
            }
        """
        result = {'added': 0, 'removed': 0, 'skipped': 0}
        
        try:
            project_dir = self.ensure_project_dir(project_name)
            
            # ============================================================
            # 1. دریافت فایل‌های فعلی DB
            # ============================================================
            db_files = self.db.get_attachments(project_name)
            db_file_names = {f['file_name'] for f in db_files}
            
            # ============================================================
            # 2. اسکن پوشه (شامل زیرپوشه‌ها)
            # ============================================================
            disk_items = []
            
            for root, dirs, files in os.walk(project_dir):
                # ===== پوشه‌ها =====
                for dirname in dirs:
                    full_path = os.path.join(root, dirname)
                    rel_path = os.path.relpath(full_path, project_dir)
                    disk_items.append({
                        'name': dirname,
                        'path': full_path,
                        'rel_path': rel_path,
                        'size': 0,
                        'ext': 'folder',
                        'is_folder': True,
                    })
                
                # ===== فایل‌ها =====
                for filename in files:
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, project_dir)
                    disk_items.append({
                        'name': filename,
                        'path': full_path,
                        'rel_path': rel_path,
                        'size': os.path.getsize(full_path),
                        'ext': os.path.splitext(filename)[1].lower().replace('.', ''),
                        'is_folder': False,
                    })
            
            disk_item_names = {item['name'] for item in disk_items}
            
            # ============================================================
            # 3. حذف رکوردهایی که فایل فیزیکی ندارن
            # ============================================================
            for db_file in db_files:
                file_path = db_file.get('file_path', '')
                if not file_path or not os.path.exists(file_path):
                    self.db.delete_attachment(project_name, db_file['file_name'])
                    result['removed'] += 1
                    logger.info(f"🗑️ Removed missing record: {db_file['file_name']}")
            
            # ============================================================
            # 4. اضافه کردن آیتم‌های جدید به DB
            # ============================================================
            for item in disk_items:
                if item['name'] in db_file_names:
                    result['skipped'] += 1
                    continue
                
                # ===== تعیین نوع =====
                if item['is_folder']:
                    file_type = 'folder'
                    description = f"[Folder] {item['rel_path']}"
                else:
                    file_type = item['ext']
                    description = f"[Auto-sync] {item['rel_path']}"
                
                # ===== اضافه به DB =====
                attachment_data = {
                    'project_name': project_name,
                    'file_name': item['name'],
                    'file_path': item['path'],
                    'file_size': item['size'],
                    'file_type': file_type,
                    'description': description,
                }
                
                if self.db.add_attachment(attachment_data):
                    result['added'] += 1
                    logger.info(f"✅ Auto-synced: {item['name']}")
                else:
                    result['skipped'] += 1
            
            # ===== لاگ نهایی =====
            if result['added'] > 0 or result['removed'] > 0:
                logger.info(
                    f"🔄 Sync '{project_name}': "
                    f"{result['added']} added, "
                    f"{result['removed']} removed, "
                    f"{result['skipped']} skipped"
                )
            else:
                logger.debug(
                    f"Sync '{project_name}': no changes "
                    f"({result['skipped']} skipped)"
                )
            
            return result
        
        except Exception as e:
            logger.error(f"Error syncing with filesystem: {e}", exc_info=True)
            return result

    def get_files_tree(self, project_name: str) -> List[Dict[str, Any]]:
        """
        دریافت فایل‌های پیوست به صورت ساختار درختی
        
        Returns:
            لیست از node ها. هر node:
            {
                'type': 'folder' | 'file',
                'name': str,
                'path': str,          # مسیر کامل
                'rel_path': str,      # مسیر نسبی
                'file_size': int,
                'file_size_str': str,
                'file_type': str,
                'exists': bool,
                'children': List[Dict],  # فقط برای پوشه‌ها
            }
        """
        try:
            project_dir = self.ensure_project_dir(project_name)
            
            # ============================================================
            # ساخت درخت از روی فایل‌سیستم
            # ============================================================
            def scan_directory(path: str, rel_path: str = "") -> List[Dict]:
                """اسکن بازگشتی یک پوشه"""
                items = []
                
                try:
                    entries = sorted(os.listdir(path))
                except PermissionError:
                    return items
                
                for entry in entries:
                    full_path = os.path.join(path, entry)
                    entry_rel = os.path.join(rel_path, entry) if rel_path else entry
                    
                    if os.path.isdir(full_path):
                        # ===== پوشه =====
                        folder_node = {
                            'type': 'folder',
                            'name': entry,
                            'path': full_path,
                            'rel_path': entry_rel,
                            'file_size': 0,
                            'file_size_str': '—',
                            'file_type': 'folder',
                            'exists': True,
                            'children': scan_directory(full_path, entry_rel),
                        }
                        items.append(folder_node)
                    
                    elif os.path.isfile(full_path):
                        # ===== فایل =====
                        try:
                            size = os.path.getsize(full_path)
                        except:
                            size = 0
                        
                        ext = os.path.splitext(entry)[1].lower().replace('.', '')
                        
                        file_node = {
                            'type': 'file',
                            'name': entry,
                            'path': full_path,
                            'rel_path': entry_rel,
                            'file_size': size,
                            'file_size_str': self._format_size(size),
                            'file_type': ext,
                            'exists': True,
                            'children': [],
                        }
                        items.append(file_node)
                
                return items
            
            # ============================================================
            # مرتب‌سازی: پوشه‌ها اول، بعد فایل‌ها
            # ============================================================
            def sort_tree(items: List[Dict]) -> List[Dict]:
                """مرتب‌سازی بازگشتی: پوشه‌ها اول، بعد فایل‌ها"""
                folders = [i for i in items if i['type'] == 'folder']
                files = [i for i in items if i['type'] == 'file']
                
                # مرتب‌سازی الفبایی
                folders.sort(key=lambda x: x['name'].lower())
                files.sort(key=lambda x: x['name'].lower())
                
                # مرتب‌سازی بازگشتی
                for folder in folders:
                    folder['children'] = sort_tree(folder['children'])
                
                return folders + files
            
            tree = scan_directory(project_dir)
            tree = sort_tree(tree)
            
            return tree
        
        except Exception as e:
            logger.error(f"Error getting files tree: {e}", exc_info=True)
            return []


__all__ = ['AttachmentManager']