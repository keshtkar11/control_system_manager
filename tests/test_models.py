"""تست مدل‌های داده"""

import unittest
import sys
import os

# اضافه کردن مسیر اصلی پروژه
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import Motor, ProjectSection, Project
from core.constants import COMPONENT_LABELS


class TestModels(unittest.TestCase):
    """تست کلاس‌های مدل"""
    
    def setUp(self):
        """تنظیمات قبل از هر تست"""
        self.motor = Motor(
            Name="Test Motor",
            Description="Test Description",
            DI=2,
            DO=1,
            AI=3,
            AO=1,
            PU=2,
            DTS=1,
            VA=1
        )
        
        self.section = ProjectSection("Test Section", "Test Description")
        self.section.add_device(self.motor)
        
        self.project = Project("Test Project")
        self.project.add_section("Custom Section")
    
    # ===== تست Motor =====
    
    def test_motor_creation(self):
        """تست ایجاد Motor"""
        self.assertEqual(self.motor.Name, "Test Motor")
        self.assertEqual(self.motor.Description, "Test Description")
        self.assertEqual(self.motor.DI, 2)
        self.assertEqual(self.motor.DO, 1)
        self.assertEqual(self.motor.AI, 3)
        self.assertEqual(self.motor.AO, 1)
    
    def test_motor_copy(self):
        """تست کپی Motor"""
        copy = self.motor.copy()
        self.assertEqual(copy.Name, self.motor.Name)
        self.assertEqual(copy.DI, self.motor.DI)
        self.assertIsNot(copy, self.motor)  # شیء متفاوت
    
    def test_motor_to_dict(self):
        """تست تبدیل به دیکشنری"""
        data = self.motor.to_dict()
        self.assertEqual(data['Name'], "Test Motor")
        self.assertEqual(data['DI'], 2)
        self.assertEqual(data['PU'], 2)
    
    def test_motor_get_total_io(self):
        """تست محاسبه مجموع I/O"""
        # DI=2, DO=1, AI=3, AO=1 => Total=7
        self.assertEqual(self.motor.get_total_io(), 7)
    
    def test_motor_get_active_components(self):
        """تست دریافت کامپوننت‌های فعال"""
        components = self.motor.get_active_components()
        # PU=2, DTS=1, VA=1 => 3 کامپوننت فعال
        self.assertEqual(len(components), 3)
        
        # بررسی کامپوننت‌ها
        component_keys = [c['key'] for c in components]
        self.assertIn('PU', component_keys)
        self.assertIn('DTS', component_keys)
        self.assertIn('VA', component_keys)
    
    def test_motor_recalculate_io(self):
        """تست محاسبه مجدد I/O"""
        motor = Motor(Name="Test", PU=2, DTS=1, VA=1)
        motor.recalculate_io()
        
        # PU: DI=3*2=6, DO=1*2=2
        # DTS: AI=1
        # VA: AI=1, AO=1
        self.assertEqual(motor.DI, 6)
        self.assertEqual(motor.DO, 2)
        self.assertEqual(motor.AI, 2)
        self.assertEqual(motor.AO, 1)
    
    def test_motor_get_io_breakdown(self):
        """تست تفکیک I/O"""
        motor = Motor(Name="Test", PU=2, DTS=1)
        breakdown = motor.get_io_breakdown()
        
        self.assertIn('PU', breakdown)
        self.assertEqual(breakdown['PU']['quantity'], 2)
        self.assertEqual(breakdown['PU']['di'], 6)  # 3 * 2
        
        self.assertIn('DTS', breakdown)
        self.assertEqual(breakdown['DTS']['ai'], 1)
    
    def test_motor_get_cable_tags(self):
        """تست تولید برچسب کابل"""
        motor = Motor(Name="Motor1", PU=2, DTS=1)
        tags = motor.get_cable_tags()
        
        # PU=2, DTS=1 => 3 تگ
        self.assertEqual(len(tags), 3)
        
        # بررسی تگ‌ها
        tag_strings = [t['tag'] for t in tags]
        self.assertIn('Motor1-01', tag_strings)
        self.assertIn('Motor1-02', tag_strings)
        self.assertIn('Motor1-03', tag_strings)
    
    # ===== تست ProjectSection =====
    
    def test_section_creation(self):
        """تست ایجاد Section"""
        self.assertEqual(self.section.name, "Test Section")
        self.assertEqual(self.section.description, "Test Description")
        self.assertEqual(len(self.section.devices), 1)
    
    def test_section_copy(self):
        """تست کپی Section"""
        copy = self.section.copy()
        self.assertEqual(copy.name, self.section.name)
        self.assertEqual(len(copy.devices), len(self.section.devices))
        self.assertIsNot(copy, self.section)
    
    def test_section_get_total_io(self):
        """تست محاسبه I/O بخش"""
        self.assertEqual(self.section.get_total_io(), 7)  # از motor قبلی
    
    def test_section_get_statistics(self):
        """تست آمار بخش"""
        stats = self.section.get_statistics()
        self.assertEqual(stats['device_count'], 1)
        self.assertEqual(stats['total_io'], 7)
        self.assertEqual(stats['total_di'], 2)
        self.assertEqual(stats['total_do'], 1)
        self.assertEqual(stats['total_ai'], 3)
        self.assertEqual(stats['total_ao'], 1)
    
    def test_section_get_active_devices(self):
        """تست دستگاه‌های فعال"""
        active = self.section.get_active_devices()
        self.assertEqual(len(active), 1)  # یک دستگاه فعال
    
    def test_section_get_component_usage(self):
        """تست استفاده از کامپوننت‌ها"""
        usage = self.section.get_component_usage()
        self.assertEqual(usage.get('PU', 0), 2)
        self.assertEqual(usage.get('DTS', 0), 1)
        self.assertEqual(usage.get('VA', 0), 1)
    
    # ===== تست Project =====
    
    def test_project_creation(self):
        """تست ایجاد Project"""
        self.assertEqual(self.project.name, "Test Project")
        self.assertIsNotNone(self.project.sections)
        self.assertGreater(len(self.project.sections), 0)
    
    def test_project_get_all_devices(self):
        """تست دریافت تمام دستگاه‌ها"""
        # اضافه کردن دستگاه به بخش سفارشی
        custom_section = self.project.get_section_by_name("Custom Section")
        custom_section.add_device(self.motor)
        
        devices = self.project.get_all_devices()
        self.assertEqual(len(devices), 1)
    
    def test_project_add_section(self):
        """تست افزودن بخش"""
        self.project.add_section("New Section", "Description")
        section = self.project.get_section_by_name("New Section")
        self.assertIsNotNone(section)
        self.assertEqual(section.description, "Description")
    
    def test_project_delete_section(self):
        """تست حذف بخش"""
        # ایجاد پروژه با 2 بخش
        project = Project("Test Project 2")
        project.sections = []  # حذف بخش‌های پیش‌فرض
        project.add_section("Section 1")
        project.add_section("Section 2")
        
        # حذف بخش اول - باید موفق باشد چون 2 بخش وجود دارد
        result = project.delete_section("Section 1")
        self.assertTrue(result)
        self.assertEqual(len(project.sections), 1)
        
        # حذف آخرین بخش - باید ناموفق باشد
        result = project.delete_section("Section 2")
        self.assertFalse(result)  # نمی‌توان آخرین بخش را حذف کرد
        self.assertEqual(len(project.sections), 1)
    
    def test_project_get_statistics(self):
        """تست آمار پروژه"""
        stats = self.project.get_statistics()
        self.assertEqual(stats['total_sections'], len(self.project.sections))
        self.assertEqual(stats['total_devices'], 0)  # هنوز دستگاهی اضافه نشده
    
    def test_project_get_component_usage(self):
        """تست استفاده از کامپوننت‌ها در پروژه"""
        # اضافه کردن دستگاه به پروژه
        section = self.project.get_section_by_name("Custom Section")
        section.add_device(self.motor)
        
        usage = self.project.get_component_usage()
        self.assertEqual(usage.get('PU', 0), 2)
        self.assertEqual(usage.get('DTS', 0), 1)
    
    def test_project_get_controller_requirements(self):
        """تست محاسبه کنترلرها"""
        # اضافه کردن دستگاه با I/O بالا
        motor = Motor(Name="Big", PU=20, DTS=10, VA=5)
        section = self.project.get_section_by_name("Custom Section")
        section.add_device(motor)
        
        requirements = self.project.get_controller_requirements()
        self.assertIn('cbx_8r8', requirements)
        self.assertIn('fbx_8r8', requirements)
    
    def test_project_invalid_name(self):
        """تست نام نامعتبر پروژه"""
        project = Project("")
        self.assertEqual(project.name, "Untitled Project")
        
        project = Project("A" * 200)  # خیلی طولانی
        self.assertLessEqual(len(project.name), 100)


if __name__ == '__main__':
    unittest.main()