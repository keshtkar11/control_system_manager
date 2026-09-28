"""تست خروجی‌ها"""

import unittest
import sys
import os
import tempfile
import shutil

# اضافه کردن مسیر اصلی
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import Motor, Project, ProjectSection
from core.database import DatabaseManager


class TestExporters(unittest.TestCase):
    """تست خروجی‌های Excel و PDF"""
    
    def setUp(self):
        """تنظیمات قبل از هر تست"""
        self.temp_dir = tempfile.mkdtemp()
        
        # ایجاد پروژه تست
        self.project = Project("Test Project")
        section = self.project.add_section("Test Section")
        
        # اضافه کردن دستگاه‌های تست
        motor1 = Motor(
            Name="Motor 1",
            DI=2,
            DO=1,
            AI=3,
            AO=1,
            PU=2,
            DTS=1
        )
        section.add_device(motor1)
        
        motor2 = Motor(
            Name="Motor 2",
            DI=0,
            DO=2,
            AI=1,
            AO=0,
            VSD=1,
            VA=1
        )
        section.add_device(motor2)
    
    def tearDown(self):
        """پاکسازی بعد از هر تست"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_excel_export_basic(self):
        """تست خروجی Excel پایه"""
        try:
            from export.excel_exporter import ExcelExporter
            
            # ایجاد Mock App
            class MockApp:
                def get_current_project(self):
                    return self.project
            
            mock_app = MockApp()
            mock_app.project = self.project
            
            exporter = ExcelExporter(mock_app)
            file_path = os.path.join(self.temp_dir, "test.xlsx")
            
            devices = self.project.get_all_devices()
            result = exporter.export_full_report(devices, file_path)
            
            # بررسی وجود فایل
            self.assertIsNotNone(result)
            self.assertTrue(os.path.exists(file_path))
            self.assertGreater(os.path.getsize(file_path), 0)
            
        except ImportError as e:
            self.skipTest(f"Excel exporter not available: {e}")
    
    def test_pdf_export_basic(self):
        """تست خروجی PDF پایه"""
        try:
            from export.pdf_exporter import PDFExporter
            
            # ایجاد Mock App
            class MockApp:
                def get_current_project(self):
                    return self.project
            
            mock_app = MockApp()
            mock_app.project = self.project
            
            exporter = PDFExporter(mock_app)
            file_path = os.path.join(self.temp_dir, "test.pdf")
            
            devices = self.project.get_all_devices()
            result = exporter.export_full_report(devices, file_path)
            
            # بررسی وجود فایل
            self.assertIsNotNone(result)
            self.assertTrue(os.path.exists(file_path))
            self.assertGreater(os.path.getsize(file_path), 0)
            
        except ImportError as e:
            self.skipTest(f"PDF exporter not available: {e}")


if __name__ == '__main__':
    unittest.main()