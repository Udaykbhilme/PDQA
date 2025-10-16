#!/usr/bin/env python3
"""
Installation Test Script for Timetable Generator

This script tests if all required dependencies are properly installed
and the application can be imported correctly.
"""

import sys
import importlib

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        if package_name:
            module = importlib.import_module(f"{package_name}.{module_name}")
        else:
            module = importlib.import_module(module_name)
        print(f"✓ {module_name} - OK")
        return True
    except ImportError as e:
        print(f"✗ {module_name} - FAILED: {e}")
        return False

def main():
    """Run installation tests"""
    print("Timetable Generator - Installation Test")
    print("=" * 50)
    
    # Test Python version
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("⚠ Warning: Python 3.8 or higher is recommended")
    else:
        print("✓ Python version OK")
    
    print("\nTesting required packages:")
    
    # Test external dependencies
    external_deps = [
        "PyQt6",
        "sqlalchemy", 
        "reportlab"
    ]
    
    external_ok = True
    for dep in external_deps:
        if not test_import(dep):
            external_ok = False
    
    print("\nTesting application modules:")
    
    # Test application modules
    app_modules = [
        ("database_manager", "src.database"),
        ("db_models", "src.database"),
        ("timetable_scheduler", "src.scheduler"),
        ("pdf_exporter", "src.export"),
        ("main_window", "src.views"),
        ("data_management_tab", "src.views"),
        ("timetable_generation_tab", "src.views"),
        ("timetable_review_tab", "src.views"),
        ("export_tab", "src.views")
    ]
    
    app_ok = True
    for module, package in app_modules:
        if not test_import(module, package):
            app_ok = False
    
    print("\n" + "=" * 50)
    
    if external_ok and app_ok:
        print("✓ All tests passed! Installation is successful.")
        print("\nYou can now run the application with:")
        print("  python main.py")
        print("\nOr test the example usage with:")
        print("  python example_usage.py")
    else:
        print("✗ Some tests failed. Please check the installation.")
        print("\nTo install missing dependencies, run:")
        print("  pip install -r requirements.txt")
        
        if not external_ok:
            print("\nMissing external dependencies detected.")
            print("Make sure you have installed PyQt6, SQLAlchemy, and ReportLab.")
        
        if not app_ok:
            print("\nApplication modules not found.")
            print("Make sure you're running this script from the project root directory.")

if __name__ == "__main__":
    main()
