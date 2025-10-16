#!/usr/bin/env python3
"""
WebDriver diagnostic script to check Chrome and ChromeDriver compatibility
"""

import subprocess
import sys
from pathlib import Path
import re

def check_chrome_version():
    """Check installed Chrome version."""
    try:
        if sys.platform == "win32":
            # Windows Chrome paths
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                # Add more possible paths
            ]
            
            for chrome_path in chrome_paths:
                if Path(chrome_path).exists():
                    result = subprocess.run([chrome_path, "--version"], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        return result.stdout.strip()
        
        # Try generic chrome command
        result = subprocess.run(["chrome", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
            
        # Try google-chrome command (Linux)
        result = subprocess.run(["google-chrome", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
            
    except Exception as e:
        return f"Error checking Chrome version: {e}"
    
    return "Chrome not found or not accessible"

def check_chromedriver_version():
    """Check ChromeDriver version."""
    try:
        result = subprocess.run(["chromedriver", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        return f"ChromeDriver not found in PATH: {e}"
    
    return "ChromeDriver not found"

def extract_version_number(version_string):
    """Extract version number from version string."""
    try:
        match = re.search(r'(\d+)\.(\d+)\.(\d+)', version_string)
        if match:
            return match.group(1)  # Return major version
        return None
    except:
        return None

def check_selenium_version():
    """Check Selenium version."""
    try:
        import selenium
        return selenium.__version__
    except Exception as e:
        return f"Error: {e}"

def test_basic_webdriver():
    """Test basic WebDriver functionality."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        print("Testing basic WebDriver initialization...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Test with Selenium Manager (automatic driver management)
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(10)
        
        # Simple test
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        return f"✅ WebDriver test successful! Page title: {title}"
        
    except Exception as e:
        return f"❌ WebDriver test failed: {e}"

def main():
    """Run diagnostics."""
    print("🔧 WebDriver Diagnostic Tool")
    print("=" * 50)
    
    # Check Selenium version
    print(f"📦 Selenium version: {check_selenium_version()}")
    
    # Check Chrome version
    chrome_version = check_chrome_version()
    print(f"🌐 Chrome version: {chrome_version}")
    chrome_major = extract_version_number(chrome_version)
    
    # Check ChromeDriver version
    chromedriver_version = check_chromedriver_version()
    print(f"🚗 ChromeDriver version: {chromedriver_version}")
    chromedriver_major = extract_version_number(chromedriver_version)
    
    # Check compatibility
    print(f"\n📊 Compatibility Check:")
    if chrome_major and chromedriver_major:
        if chrome_major == chromedriver_major:
            print(f"✅ Chrome ({chrome_major}) and ChromeDriver ({chromedriver_major}) major versions match")
        else:
            print(f"⚠️  Version mismatch: Chrome major version {chrome_major} vs ChromeDriver {chromedriver_major}")
            print(f"   Consider downloading ChromeDriver {chrome_major}.x.x from:")
            print(f"   https://chromedriver.chromium.org/downloads")
    else:
        print("❌ Could not determine version compatibility")
    
    # Test basic WebDriver functionality
    print(f"\n🧪 WebDriver Test:")
    test_result = test_basic_webdriver()
    print(f"   {test_result}")
    
    # Provide recommendations
    print(f"\n💡 Recommendations:")
    if "not found" in chrome_version.lower():
        print("   - Install Google Chrome browser")
    if "not found" in chromedriver_version.lower():
        print("   - ChromeDriver will be auto-managed by Selenium 4+")
        print("   - Or manually download from https://chromedriver.chromium.org/")
    if chrome_major and chromedriver_major and chrome_major != chromedriver_major:
        print(f"   - Update ChromeDriver to match Chrome version {chrome_major}")
    
    print(f"\n🔗 Helpful Links:")
    print(f"   - Chrome version check: chrome://version/")
    print(f"   - ChromeDriver downloads: https://chromedriver.chromium.org/downloads")
    print(f"   - Selenium docs: https://selenium-python.readthedocs.io/")

if __name__ == "__main__":
    main()