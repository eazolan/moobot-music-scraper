#!/usr/bin/env python3
"""
Test the improved WebDriver setup
"""

import sys
from pathlib import Path

# Add parent directory to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent))

from moobot_scraper import MoobotScraper

def test_webdriver_initialization():
    """Test WebDriver initialization with improved setup."""
    print("🧪 Testing improved WebDriver setup...")
    
    try:
        # Create scraper instance
        scraper = MoobotScraper()
        
        print("📋 Attempting to initialize WebDriver...")
        scraper.setup_webdriver()
        
        if scraper.driver:
            print("✅ WebDriver initialized successfully!")
            
            # Test basic functionality
            print("🌐 Testing basic page load...")
            scraper.driver.get("https://www.google.com")
            title = scraper.driver.title
            print(f"✅ Page loaded successfully: {title}")
            
            # Clean up
            scraper.cleanup()
            print("✅ WebDriver cleaned up successfully")
            
            return True
            
        else:
            print("❌ WebDriver initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        # Attempt cleanup even if test failed
        try:
            if 'scraper' in locals() and scraper.driver:
                scraper.cleanup()
        except:
            pass
        return False

def test_scraper_with_slimaera():
    """Test the full scraper with slimaera streamer."""
    print("\n🎵 Testing scraper with slimaera...")
    
    try:
        # Temporarily change the streamer name
        import moobot_scraper
        original_streamer = moobot_scraper.STREAMER_NAME
        moobot_scraper.STREAMER_NAME = "slimaera"
        moobot_scraper.MOOBOT_URL = f"https://moo.bot/r/music#slimaera"
        
        scraper = MoobotScraper()
        
        print("🔍 Running a quick scan...")
        scraper.run_scan()
        
        print("✅ Scan completed successfully!")
        scraper.cleanup()
        
        # Restore original values
        moobot_scraper.STREAMER_NAME = original_streamer
        
        return True
        
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 WebDriver Setup Test")
    print("=" * 40)
    
    # Test 1: Basic WebDriver functionality
    webdriver_ok = test_webdriver_initialization()
    
    if webdriver_ok:
        # Test 2: Full scraper test
        scraper_ok = test_scraper_with_slimaera()
        
        if scraper_ok:
            print("\n🎉 All tests passed! WebDriver setup is working correctly.")
        else:
            print("\n⚠️ WebDriver works, but scraper had issues.")
    else:
        print("\n❌ WebDriver setup needs attention.")
        print("\nTry running: python diagnose_webdriver.py for more details")