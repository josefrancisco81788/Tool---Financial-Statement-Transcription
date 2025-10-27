#!/usr/bin/env python3
"""
Progressive diagnostic script to find exactly where the hang occurs
"""

import os
import sys
import time
import threading
from pathlib import Path


def run_with_timeout(func, timeout_seconds=30, description="operation"):
    """Run a function with timeout protection using threading"""
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func()
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if thread.is_alive():
        print(f"   ❌ {description} TIMED OUT after {timeout_seconds}s")
        return None
    elif exception[0]:
        print(f"   ❌ {description} FAILED: {exception[0]}")
        return None
    else:
        print(f"   ✅ {description} SUCCEEDED")
        return result[0]


def test_basic_imports():
    """Test 1: Basic imports"""
    print("\n🔍 TEST 1: Basic imports")
    print("-" * 40)
    
    def test_os():
        import os
        return True
    
    def test_sys():
        import sys
        return True
    
    def test_json():
        import json
        return True
    
    def test_pathlib():
        from pathlib import Path
        return True
    
    def test_threading():
        import threading
        return True
    
    tests = [
        (test_os, "os import"),
        (test_sys, "sys import"),
        (test_json, "json import"),
        (test_pathlib, "pathlib import"),
        (test_threading, "threading import")
    ]
    
    for test_func, description in tests:
        run_with_timeout(test_func, 5, description)


def test_project_structure():
    """Test 2: Project structure"""
    print("\n🔍 TEST 2: Project structure")
    print("-" * 40)
    
    def check_core_dir():
        core_dir = Path("core")
        if core_dir.exists():
            return f"core/ exists: {list(core_dir.glob('*.py'))}"
        return "core/ does not exist"
    
    def check_tests_dir():
        tests_dir = Path("tests")
        if tests_dir.exists():
            return f"tests/ exists: {list(tests_dir.glob('*.py'))}"
        return "tests/ does not exist"
    
    result1 = run_with_timeout(check_core_dir, 5, "core directory check")
    if result1:
        print(f"   📁 {result1}")
    
    result2 = run_with_timeout(check_tests_dir, 5, "tests directory check")
    if result2:
        print(f"   📁 {result2}")


def test_core_package():
    """Test 3: Core package import"""
    print("\n🔍 TEST 3: Core package import")
    print("-" * 40)
    
    def import_core():
        import core
        return f"core module: {dir(core)}"
    
    result = run_with_timeout(import_core, 10, "core package import")
    if result:
        print(f"   📦 {result}")


def test_config_module():
    """Test 4: Config module import"""
    print("\n🔍 TEST 4: Config module import")
    print("-" * 40)
    
    def import_config_module():
        from core import config
        return f"config module: {dir(config)}"
    
    result = run_with_timeout(import_config_module, 10, "config module import")
    if result:
        print(f"   ⚙️ {result}")


def test_config_class():
    """Test 5: Config class import"""
    print("\n🔍 TEST 5: Config class import")
    print("-" * 40)
    
    def import_config_class():
        from core.config import Config
        return f"Config class: {Config.__name__}"
    
    result = run_with_timeout(import_config_class, 10, "Config class import")
    if result:
        print(f"   🏗️ {result}")


def test_config_instantiation():
    """Test 6: Config instantiation"""
    print("\n🔍 TEST 6: Config instantiation")
    print("-" * 40)
    
    def instantiate_config():
        from core.config import Config
        config = Config()
        return f"Config instance: {type(config).__name__}"
    
    result = run_with_timeout(instantiate_config, 30, "Config instantiation")
    if result:
        print(f"   🎯 {result}")


def test_extractor_import():
    """Test 7: Extractor import"""
    print("\n🔍 TEST 7: Extractor import")
    print("-" * 40)
    
    def import_extractor():
        from core.extractor import FinancialDataExtractor
        return f"FinancialDataExtractor class: {FinancialDataExtractor.__name__}"
    
    result = run_with_timeout(import_extractor, 30, "FinancialDataExtractor import")
    if result:
        print(f"   🤖 {result}")


def test_extractor_instantiation():
    """Test 8: Extractor instantiation"""
    print("\n🔍 TEST 8: Extractor instantiation")
    print("-" * 40)
    
    def instantiate_extractor():
        from core.extractor import FinancialDataExtractor
        extractor = FinancialDataExtractor()
        return f"Extractor instance: {type(extractor).__name__}"
    
    result = run_with_timeout(instantiate_extractor, 60, "FinancialDataExtractor instantiation")
    if result:
        print(f"   🎯 {result}")


def main():
    """Run all diagnostic tests"""
    print("🔍 PROGRESSIVE DIAGNOSTIC SCRIPT")
    print("=" * 60)
    print("Finding the exact line where the hang occurs...")
    
    try:
        test_basic_imports()
        test_project_structure()
        test_core_package()
        test_config_module()
        test_config_class()
        test_config_instantiation()
        test_extractor_import()
        test_extractor_instantiation()
        
        print("\n🎉 ALL TESTS COMPLETED")
        print("=" * 60)
        print("If you see this message, the hang was likely in a different area.")
        
    except KeyboardInterrupt:
        print("\n⚠️ DIAGNOSTIC INTERRUPTED")
        print("=" * 60)
        print("This indicates where the hang occurred.")
    except Exception as e:
        print(f"\n❌ DIAGNOSTIC FAILED: {e}")
        print("=" * 60)


if __name__ == "__main__":
    main()
