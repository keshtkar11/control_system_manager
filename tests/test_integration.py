"""تست یکپارچه‌سازی همه ماژول‌ها"""

import unittest
import sys
import os
import tempfile
import shutil
import time

# اضافه کردن مسیر اصلی
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import (
    Motor, Project, ProjectSection,
    DatabaseManager, HistoryManager,
    COMPONENT_LABELS
)


class TestIntegration(unittest.TestCase):
    """تست یکپارچه‌سازی"""
    
    def setUp(self):
        """تنظیمات قبل از هر تست"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.db = DatabaseManager(self.db_path)
        self.history = HistoryManager()
    
    def tearDown(self):
        """پاکسازی بعد از هر تست"""
        try:
            if hasattr(self.db, 'conn'):
                self.db.conn.close()
        except:
            pass
        time.sleep(0.5)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """تست گردش کار کامل"""
        
        # ===== 1. ایجاد پروژه =====
        project = Project("Integration Project")
        project.client_name = "Test Client"
        project.client_phone = "09123456789"
        # حذف بخش‌های پیش‌فرض
        project.sections = []
        
        # ===== 2. اضافه کردن بخش =====
        section = project.add_section("Main Section", "Main equipment")
        
        # ===== 3. اضافه کردن دستگاه‌ها =====
        motor1 = Motor(
            Name="Pump 1",
            PU=1,
            VSD=1,
            FS=1,
            DTS=1
        )
        motor1.recalculate_io()
        section.add_device(motor1)
        
        motor2 = Motor(
            Name="AHU 1",
            PU=1,
            DTS=2,
            RTS=1,
            VA=2
        )
        motor2.recalculate_io()
        section.add_device(motor2)
        
        # ===== 4. ذخیره در دیتابیس =====
        self.db.save_project(project)
        
        # ===== 5. ذخیره تاریخچه - دو بار برای اطمینان =====
        self.history.push_state(project.name, project.sections)
        self.history.push_state(project.name, project.sections)  # <-- دوبار برای ایجاد تاریخچه
        
        # ===== 6. بارگذاری از دیتابیس =====
        projects = self.db.load_all_projects()
        self.assertIn("Integration Project", projects)
        loaded = projects["Integration Project"]
        
        # حذف بخش‌های پیش‌فرض
        loaded.sections = [s for s in loaded.sections if s.name == "Main Section"]
        
        # ===== 7. بررسی داده‌ها =====
        self.assertEqual(loaded.name, "Integration Project")
        self.assertEqual(loaded.client_name, "Test Client")
        self.assertEqual(loaded.client_phone, "09123456789")
        self.assertEqual(len(loaded.sections), 1)
        
        loaded_section = loaded.sections[0]
        self.assertEqual(loaded_section.name, "Main Section")
        self.assertEqual(len(loaded_section.devices), 2)
        
        # ===== 8. بررسی دستگاه‌ها =====
        devices = loaded.get_all_devices()
        self.assertEqual(len(devices), 2)
        
        # محاسبه I/O
        total_io = loaded.get_total_io()
        self.assertGreater(total_io, 0)
        
        # ===== 9. بررسی تاریخچه =====
        # اطمینان از اینکه تاریخچه حداقل یک آیتم دارد
        self.assertTrue(self.history.can_undo() or len(self.history.history) > 0)
        
        # ===== 10. ویرایش و ذخیره مجدد =====
        loaded_section.devices[0].Name = "Pump 1 (Updated)"
        self.db.save_project(loaded)
        
        # ===== 11. بارگذاری مجدد =====
        projects = self.db.load_all_projects()
        reloaded = projects["Integration Project"]
        reloaded.sections = [s for s in reloaded.sections if s.name == "Main Section"]
        
        self.assertEqual(
            reloaded.sections[0].devices[0].Name,
            "Pump 1 (Updated)"
        )
        
        print("✅ All integration tests passed!")
    
    def test_component_labels_workflow(self):
        """تست گردش کار برچسب‌ها"""
        
        # ===== 1. ایجاد پروژه =====
        project = Project("Label Project")
        project.sections = []  # حذف بخش‌های پیش‌فرض
        project.add_section("Test Section")
        self.db.save_project(project)
        
        # ===== 2. ذخیره برچسب‌های سفارشی =====
        custom_labels = {
            'PU': {'fa': 'موتور الکتریکی', 'en': 'Electric Motor'},
            'DTS': {'fa': 'سنسور دمای کانال', 'en': 'Duct Temp Sensor'},
        }
        self.db.save_component_labels("Label Project", custom_labels)
        
        # ===== 3. بارگذاری برچسب‌ها =====
        loaded = self.db.load_component_labels("Label Project")
        
        # ===== 4. بررسی برچسب‌ها =====
        self.assertEqual(loaded['PU']['fa'], 'موتور الکتریکی')
        self.assertEqual(loaded['DTS']['en'], 'Duct Temp Sensor')
        
        print("✅ Label workflow test passed!")
    
    def test_undo_redo_workflow(self):
        """تست گردش کار Undo/Redo"""
        
        # ===== 1. ایجاد پروژه =====
        project = Project("History Project")
        project.sections = []  # حذف بخش‌های پیش‌فرض
        section = project.add_section("Section 1")
        motor = Motor(Name="Motor 1", PU=1)
        section.add_device(motor)
        
        # ===== 2. ذخیره حالت اول =====
        self.history.push_state(project.name, project.sections)
        
        # ===== 3. تغییر =====
        motor.Name = "Motor 2"
        motor.PU = 2
        motor.recalculate_io()
        
        # ===== 4. ذخیره حالت دوم =====
        self.history.push_state(project.name, project.sections)
        
        # ===== 5. تست Undo =====
        state = self.history.undo()
        self.assertIsNotNone(state)
        self.assertEqual(state['project_name'], "History Project")
        
        # ===== 6. تست Redo =====
        state = self.history.redo()
        self.assertIsNotNone(state)
        self.assertEqual(state['project_name'], "History Project")
        
        print("✅ Undo/Redo workflow test passed!")


if __name__ == '__main__':
    unittest.main()