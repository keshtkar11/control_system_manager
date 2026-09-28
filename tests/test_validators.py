"""تست اعتبارسنجی‌ها"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.validators import (
    validate_device_name,
    validate_io_value,
    validate_phone_number,
    validate_email,
    validate_section_name,
    validate_project_name,
    validate_system_type
)


class TestValidators(unittest.TestCase):
    """تست توابع اعتبارسنجی"""
    
    def test_validate_device_name(self):
        """تست اعتبارسنجی نام دستگاه"""
        # نام معتبر
        valid, msg = validate_device_name("Motor 1")
        self.assertTrue(valid)
        
        valid, msg = validate_device_name("پمپ آب")
        self.assertTrue(valid)
        
        # نام خالی
        valid, msg = validate_device_name("")
        self.assertFalse(valid)
        
        # نام None
        valid, msg = validate_device_name(None)
        self.assertTrue(valid)
        
        # نام با کاراکترهای غیرمجاز
        valid, msg = validate_device_name("Motor/1")
        self.assertFalse(valid)
        
        # نام خیلی طولانی
        valid, msg = validate_device_name("A" * 150)
        self.assertFalse(valid)
    
    def test_validate_io_value(self):
        """تست اعتبارسنجی مقدار I/O"""
        # مقدار صحیح
        valid, value, msg = validate_io_value(5)
        self.assertTrue(valid)
        self.assertEqual(value, 5)
        
        # مقدار رشته‌ای صحیح
        valid, value, msg = validate_io_value("10")
        self.assertTrue(valid)
        self.assertEqual(value, 10)
        
        # مقدار منفی
        valid, value, msg = validate_io_value(-5)
        self.assertFalse(valid)
        
        # مقدار غیرعددی
        valid, value, msg = validate_io_value("abc")
        self.assertFalse(valid)
        
        # مقدار خالی
        valid, value, msg = validate_io_value("")
        self.assertTrue(valid)
        self.assertEqual(value, 0)
        
        # مقدار خیلی بزرگ
        valid, value, msg = validate_io_value(100000)
        self.assertFalse(valid)
    
    def test_validate_phone_number(self):
        """تست اعتبارسنجی شماره تلفن"""
        
        # ===== شماره‌های صحیح =====
        valid_phones = [
            "09123456789",      # موبایل با صفر
            "9123456789",       # موبایل بدون صفر
            "02112345678",      # تهران با صفر
            "+989123456789",    # بین‌المللی
            "00989123456789",   # بین‌المللی با 00
            "03112345678",      # اصفهان با صفر
            "05112345678",      # مشهد با صفر
            "0912 345 6789",    # با فاصله
            "(021)12345678",    # با پرانتز
            "021-12345678",     # با خط تیره
        ]
        
        for phone in valid_phones:
            valid, msg = validate_phone_number(phone)
            self.assertTrue(valid, f"Expected valid for '{phone}' but got: {msg}")
        
        # ===== شماره‌های نادرست =====
        invalid_phones = [
            "12345",            # خیلی کوتاه
            "091234567",        # 9 رقم
            "1234567890",       # 10 رقم ولی با 1 شروع شده
            "5123456789",       # 10 رقم ولی با 5 شروع شده (کد شهر 51 بدون صفر)
            "2112345678",       # 10 رقم ولی با 2 شروع شده (کد شهر 21 بدون صفر)
            "091234567890",     # 12 رقم
            "021123456",        # 9 رقم
            "912345678",        # 9 رقم
            "abc123",           # دارای حروف
            "+98123456789",     # +98 با 9 رقم
            "0098123456789",    # 0098 با 9 رقم
            "",                 # خالی
            "   ",              # فقط فاصله
            "123-456-7890",     # فرمت نامناسب
            "0",                # یک رقم
            "09123",            # 5 رقم
        ]
        
        for phone in invalid_phones:
            valid, msg = validate_phone_number(phone)
            self.assertFalse(valid, f"Expected invalid for '{phone}' but got valid with: {msg}")
    
    def test_validate_email(self):
        """تست اعتبارسنجی ایمیل"""
        # ایمیل صحیح
        valid, msg = validate_email("test@example.com")
        self.assertTrue(valid)
        
        valid, msg = validate_email("user.name@domain.co")
        self.assertTrue(valid)
        
        valid, msg = validate_email("user+tag@domain.com")
        self.assertTrue(valid)
        
        # ایمیل نادرست
        valid, msg = validate_email("test@")
        self.assertFalse(valid)
        
        valid, msg = validate_email("test@domain")
        self.assertFalse(valid)
        
        valid, msg = validate_email("test")
        self.assertFalse(valid)
        
        # خالی
        valid, msg = validate_email("")
        self.assertTrue(valid)
        
        valid, msg = validate_email("   ")
        self.assertTrue(valid)
    
    def test_validate_section_name(self):
        """تست اعتبارسنجی نام بخش"""
        # نام صحیح
        valid, msg = validate_section_name("Motor Room")
        self.assertTrue(valid)
        
        valid, msg = validate_section_name("اتاق موتور")
        self.assertTrue(valid)
        
        # نام خالی
        valid, msg = validate_section_name("")
        self.assertFalse(valid)
        
        # نام با فاصله
        valid, msg = validate_section_name("  Section 1  ")
        self.assertTrue(valid)
        self.assertEqual(msg, "Section 1")  # trimmed
        
        # نام خیلی طولانی
        valid, msg = validate_section_name("A" * 60)
        self.assertFalse(valid)
    
    def test_validate_project_name(self):
        """تست اعتبارسنجی نام پروژه"""
        # نام صحیح
        valid, msg = validate_project_name("Project 2024")
        self.assertTrue(valid)
        
        valid, msg = validate_project_name("پروژه نمونه")
        self.assertTrue(valid)
        
        # نام خالی
        valid, msg = validate_project_name("")
        self.assertFalse(valid)
        
        # نام با کاراکترهای غیرمجاز
        valid, msg = validate_project_name("Project/2024")
        self.assertFalse(valid)
        
        valid, msg = validate_project_name("Project:2024")
        self.assertFalse(valid)
        
        valid, msg = validate_project_name('Project"2024"')
        self.assertFalse(valid)
        
        # نام خیلی طولانی
        valid, msg = validate_project_name("A" * 150)
        self.assertFalse(valid)
        
        # نام با فاصله
        valid, msg = validate_project_name("  Project 1  ")
        self.assertTrue(valid)
        self.assertEqual(msg, "Project 1")
    
    def test_validate_system_type(self):
        """تست اعتبارسنجی نوع سیستم"""
        # انواع صحیح
        valid, msg = validate_system_type("HVAC")
        self.assertTrue(valid)
        
        valid, msg = validate_system_type("Chiller")
        self.assertTrue(valid)
        
        valid, msg = validate_system_type("BMS")
        self.assertTrue(valid)
        
        # انواع نادرست
        valid, msg = validate_system_type("Invalid")
        self.assertFalse(valid)
        
        valid, msg = validate_system_type("")
        self.assertFalse(valid)
        
        valid, msg = validate_system_type("   ")
        self.assertFalse(valid)


if __name__ == '__main__':
    unittest.main()