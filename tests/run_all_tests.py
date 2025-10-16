#!/usr/bin/env python3
"""
Test runner for Moobot scraper tests

Runs key diagnostic and functional tests in order.
"""

import sys
import subprocess
from pathlib import Path

def run_test(test_name, description, *args):
    """Run a single test with nice formatting."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        cmd = [sys.executable, f"tests/{test_name}"] + list(args)
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {test_name} - PASSED")
            return True
        else:
            print(f"❌ {test_name} - FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_name} - TIMEOUT (5 minutes)")
        return False
    except Exception as e:
        print(f"💥 {test_name} - ERROR: {e}")
        return False

def main():
    """Run all tests in order."""
    print("🔧 Moobot Scraper Test Suite")
    print("Running diagnostic and functional tests...\n")
    
    tests_passed = 0
    total_tests = 0
    
    # Quick diagnostic tests (run first)
    quick_tests = [
        ("diagnose_webdriver.py", "WebDriver Compatibility Check"),
        ("test_filtering.py", "UI Text Filtering Test"),
        ("test_html_generation.py", "HTML Generation Test"),
    ]
    
    print("🚀 Running Quick Tests...")
    for test_name, description in quick_tests:
        total_tests += 1
        if run_test(test_name, description):
            tests_passed += 1
    
    # Integration tests (slower)
    integration_tests = [
        ("test_scraper.py", "Full Scraper Integration Test", "--streamer", "slimaera"),
    ]
    
    print("\n🧪 Running Integration Tests...")
    for test_data in integration_tests:
        test_name = test_data[0]
        description = test_data[1]
        args = test_data[2:] if len(test_data) > 2 else []
        
        total_tests += 1
        if run_test(test_name, description, *args):
            tests_passed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 Test Results Summary")
    print(f"{'='*60}")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {total_tests - tests_passed}")
    print(f"📊 Total:  {total_tests}")
    
    if tests_passed == total_tests:
        print(f"\n🎉 All tests passed! Your Moobot scraper is working correctly.")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())