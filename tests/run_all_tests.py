"""اجرای همه تست‌ها"""

import unittest
import sys
import os

# اضافه کردن مسیر اصلی پروژه
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def run_all_tests():
    """اجرای همه تست‌ها و نمایش نتایج"""
    
    print("=" * 70)
    print("🧪 RUNNING ALL TESTS")
    print("=" * 70)
    print()
    
    # بارگذاری همه تست‌ها
    test_loader = unittest.TestLoader()
    
    # پیدا کردن همه تست‌ها
    test_suite = test_loader.discover(
        start_dir=os.path.dirname(__file__),
        pattern="test_*.py",
        top_level_dir=project_root
    )
    
    # اجرا با نتیجه‌گیری
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # نمایش خلاصه
    print()
    print("=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️ Errors: {len(result.errors)}")
    print(f"📝 Total: {total}")
    print()
    
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        if result.failures:
            print("\n--- Failures ---")
            for failure in result.failures:
                print(f"\n{failure[0]}:")
                print(failure[1])
        if result.errors:
            print("\n--- Errors ---")
            for error in result.errors:
                print(f"\n{error[0]}:")
                print(error[1])
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())