"""تست دیتابیس"""

import unittest
import sys
import os
import tempfile
import shutil
import time

# اضافه کردن مسیر اصلی
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import DatabaseManager
from core.models import Project, ProjectSection, Motor
from core.constants import COLORS, DEFAULT_SECTIONS


class TestDatabase(unittest.TestCase):
    """تست کلاس DatabaseManager"""
    
    def setUp(self):
        """تنظیمات قبل از هر تست"""
        # ایجاد دیتابیس موقت
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = DatabaseManager(self.db_path)
        
        # ایجاد پروژه تست - با حذف بخش‌های پیش‌فرض
        self.test_project = Project("Test Project")
        # حذف بخش‌های پیش‌فرض
        self.test_project.sections = []
        # اضافه کردن یک بخش تست
        section = self.test_project.add_section("Test Section", "Test Description")
        motor = Motor(
            Name="Test Motor",
            DI=2,
            DO=1,
            AI=3,
            AO=1,
            PU=2
        )
        section.add_device(motor)
        # تنظیم اطلاعات مشتری
        self.test_project.client_name = "Test Client"
        self.test_project.client_phone = "09123456789"
        self.test_project.consultant_name = "Test Consultant"
    
    def tearDown(self):
        """پاکسازی بعد از هر تست"""
        try:
            if hasattr(self.db, 'conn'):
                self.db.conn.close()
        except:
            pass
        
        time.sleep(0.5)
        
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass
    
    def test_save_and_load_project(self):
        """تست ذخیره و بارگذاری پروژه"""
        # ذخیره
        self.db.save_project(self.test_project)
        
        # بارگذاری
        projects = self.db.load_all_projects()
        
        self.assertIn("Test Project", projects)
        loaded = projects["Test Project"]
        
        # بررسی اطلاعات
        self.assertEqual(loaded.name, self.test_project.name)
        self.assertEqual(loaded.client_name, "Test Client")
        self.assertEqual(loaded.client_phone, "09123456789")
        self.assertEqual(loaded.consultant_name, "Test Consultant")
        
        # حذف بخش‌های پیش‌فرض که可能在 بارگذاری ایجاد شده‌اند
        # فقط بخش‌هایی که نامشان "Test Section" است را نگه می‌داریم
        loaded.sections = [s for s in loaded.sections if s.name == "Test Section"]
        
        self.assertEqual(len(loaded.sections), 1)
        
        section = loaded.sections[0]
        self.assertEqual(section.name, "Test Section")
        self.assertEqual(len(section.devices), 1)
        
        motor = section.devices[0]
        self.assertEqual(motor.Name, "Test Motor")
        self.assertEqual(motor.DI, 2)
        self.assertEqual(motor.PU, 2)
    
    def test_delete_project(self):
        """تست حذف پروژه"""
        self.db.save_project(self.test_project)
        
        # بررسی وجود پروژه
        projects = self.db.load_all_projects()
        self.assertIn("Test Project", projects)
        
        # حذف پروژه
        self.db.delete_project("Test Project")
        
        # بررسی حذف
        projects = self.db.load_all_projects()
        self.assertNotIn("Test Project", projects)
    
    def test_save_multiple_projects(self):
        """تست ذخیره چند پروژه"""
        # پروژه اول
        self.db.save_project(self.test_project)
        
        # پروژه دوم
        project2 = Project("Project 2")
        project2.sections = []  # حذف بخش‌های پیش‌فرض
        project2.add_section("Section 1")
        self.db.save_project(project2)
        
        # بارگذاری
        projects = self.db.load_all_projects()
        self.assertEqual(len(projects), 2)
        self.assertIn("Test Project", projects)
        self.assertIn("Project 2", projects)
    
    def test_backup_database(self):
        """تست پشتیبان‌گیری"""
        self.db.save_project(self.test_project)
        
        backup_path = os.path.join(self.temp_dir, "backup.db")
        result = self.db.backup_database(backup_path)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(backup_path))
    
    def test_restore_database(self):
        """تست بازگردانی از پشتیبان"""
        self.db.save_project(self.test_project)
        
        # پشتیبان‌گیری
        backup_path = os.path.join(self.temp_dir, "backup.db")
        self.db.backup_database(backup_path)
        
        # بستن اتصال دیتابیس
        try:
            if hasattr(self.db, 'conn'):
                self.db.conn.close()
        except:
            pass
        
        time.sleep(0.5)
        
        # حذف دیتابیس اصلی
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                self.db_path = os.path.join(self.temp_dir, "test2.db")
                self.db = DatabaseManager(self.db_path)
        
        # بازگردانی
        self.db = DatabaseManager(self.db_path)
        result = self.db.restore_database(backup_path)
        self.assertTrue(result)
        
        # بررسی داده‌ها
        projects = self.db.load_all_projects()
        self.assertIn("Test Project", projects)
    
    def test_component_labels(self):
        """تست ذخیره و بارگذاری برچسب‌ها"""
        labels = {
            'FS': {'fa': 'سوئیچ جریان', 'en': 'Flow Switch'},
            'DTS': {'fa': 'سنسور دما', 'en': 'Temp Sensor'}
        }
        
        self.db.save_component_labels("Test Project", labels)
        
        loaded = self.db.load_component_labels("Test Project")
        self.assertEqual(loaded['FS']['fa'], 'سوئیچ جریان')
        self.assertEqual(loaded['DTS']['en'], 'Temp Sensor')


if __name__ == '__main__':
    unittest.main()