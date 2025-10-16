#!/usr/bin/env python3
"""
Test the improved filtering of UI text and non-song elements
"""

import sys
from pathlib import Path

# Add parent directory to path for imports  
sys.path.insert(0, str(Path(__file__).parent.parent))

from domains.music_queue.services import SongMatchingService
from domains.content_publishing.services import HtmlGenerator

def test_ui_filtering():
    """Test UI text filtering with examples from the problematic output."""
    
    song_matcher = SongMatchingService()
    html_generator = HtmlGenerator(None)  # Config not needed for this test
    
    # Test cases from the problematic HTML
    test_cases = [
        # Good songs (should NOT be filtered)
        ("You Should Be Dancing", False),
        ("Yeah Yeah Yeahs - Heads Will Roll (Official Music Video)", False),
        ("Ooze on the Move - A D&D Gelatinous Cube Didgeridoo Song #sunoai", False),
        ("Conga", False),
        
        # Bad UI text (should be filtered)
        ("Song Requests", True),
        ("Moobot", True),
        ("Refresh", True),
        ("04:17", True),
        ("By Hell_wing2 9 hours ago", True),
        ("03:41", True),
        ("By Doom_bringer007 9 hours ago", True),
        ("Song queue", True),
        ("Song history", True),
        ("Requested by Hell_wing2", True),
        ("Played 9 hours ago", True),
    ]
    
    print("🧪 Testing UI text filtering...")
    print("=" * 50)
    
    all_correct = True
    
    for text, should_be_filtered in test_cases:
        # Test both filtering methods
        is_ui_song_matcher = song_matcher.is_ui_text(text)
        is_ui_html_generator = html_generator._is_ui_text(text)
        
        # Check if both methods agree and match expected result
        methods_agree = is_ui_song_matcher == is_ui_html_generator
        correct_result = is_ui_song_matcher == should_be_filtered
        
        status = "✅" if correct_result and methods_agree else "❌"
        filter_status = "FILTERED" if is_ui_song_matcher else "KEPT"
        expected = "SHOULD FILTER" if should_be_filtered else "SHOULD KEEP"
        
        print(f"{status} '{text}' -> {filter_status} ({expected})")
        
        if not correct_result:
            all_correct = False
            print(f"   ⚠️  Expected {'FILTER' if should_be_filtered else 'KEEP'}, got {'FILTER' if is_ui_song_matcher else 'KEEP'}")
        
        if not methods_agree:
            all_correct = False
            print(f"   ⚠️  Methods disagree: SongMatcher={is_ui_song_matcher}, HtmlGenerator={is_ui_html_generator}")
    
    print("\n" + "=" * 50)
    if all_correct:
        print("🎉 All filtering tests passed!")
    else:
        print("⚠️  Some filtering tests failed - need adjustments")
    
    return all_correct

if __name__ == "__main__":
    test_ui_filtering()