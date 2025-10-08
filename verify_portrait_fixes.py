#!/usr/bin/env python3
"""
Verification script for portrait mode fixes.
Checks that all required changes are present in main.py.
"""

import re
import sys
from pathlib import Path

def check_file_contains(filepath, patterns, description):
    """Check if file contains all patterns"""
    print(f"\n{'='*60}")
    print(f"Checking: {description}")
    print(f"{'='*60}")
    
    content = Path(filepath).read_text()
    all_found = True
    
    for pattern_desc, pattern in patterns:
        if isinstance(pattern, str):
            # Simple string search
            found = pattern in content
        else:
            # Regular expression search (pattern is already compiled)
            found = pattern.search(content) is not None
        
        status = "✓" if found else "✗"
        print(f"{status} {pattern_desc}")
        if not found:
            all_found = False
    
    return all_found

def main():
    main_py = Path(__file__).parent / "main.py"
    
    if not main_py.exists():
        print(f"Error: {main_py} not found!")
        return False
    
    all_checks_passed = True
    
    # Check 1: PORTRAIT_LABEL_ANGLE constant
    checks = [
        ("PORTRAIT_LABEL_ANGLE constant defined", 
         re.compile(r"PORTRAIT_LABEL_ANGLE\s*=\s*\d+")),
        ("PORTRAIT_LABEL_ANGLE comment explaining purpose",
         "Portrait mode (9:16) toolbar label orientation"),
    ]
    all_checks_passed &= check_file_contains(main_py, checks, 
                                              "1. PORTRAIT_LABEL_ANGLE Configuration")
    
    # Check 2: VerticalButton with mirror support
    checks = [
        ("VerticalButton class exists", 
         "class VerticalButton(Button):"),
        ("VerticalButton __init__ with use_mirror parameter",
         re.compile(r"def __init__\(self.*use_mirror")),
        ("Scale import for mirror transform",
         re.compile(r"from kivy.graphics import.*Scale")),
        ("Scale(1, -1, 1) applied in _update_rotation",
         re.compile(r"Scale\(1,\s*-1,\s*1\)")),
    ]
    all_checks_passed &= check_file_contains(main_py, checks,
                                              "2. VerticalButton Mirror Support")
    
    # Check 3: Toolbar creation with vertical mode
    checks = [
        ("_create_toolbar checks aspect_ratio",
         re.compile(r"is_portrait\s*=\s*self\.aspect_ratio\s*==\s*[\"']9:16[\"']")),
        ("CustomAppBar created with vertical parameter",
         re.compile(r"CustomAppBar\(.*vertical=is_portrait")),
        ("Toolbar pos_hint set to right for portrait",
         re.compile(r'pos_hint\s*=\s*\{.*["\']right["\']\s*:\s*1')),
    ]
    all_checks_passed &= check_file_contains(main_py, checks,
                                              "3. Vertical Toolbar Creation")
    
    # Check 4: Image resize for vertical toolbar
    checks = [
        ("_resize_image checks aspect_ratio for toolbar position",
         re.compile(r'if self\.aspect_ratio\s*==\s*["\']9:16["\']')),
        ("Content width adjusted for vertical toolbar",
         re.compile(r"content_w\s*=\s*self\.width\s*-\s*toolbar_width")),
    ]
    all_checks_passed &= check_file_contains(main_py, checks,
                                              "4. Image Resize for Vertical Toolbar")
    
    # Check 5: Toggle functionality
    checks = [
        ("current_popup tracking variable",
         re.compile(r"self\.current_popup\s*=\s*None")),
        ("current_popup_name tracking variable",
         re.compile(r"self\.current_popup_name\s*=\s*None")),
        ("_toggle_overlay method defined",
         re.compile(r"def _toggle_overlay\(self")),
        ("_toggle_popup method defined",
         re.compile(r"def _toggle_popup\(self")),
        ("open_gallery uses _toggle_overlay",
         re.compile(r"def open_gallery\(self\):.*_toggle_overlay", re.DOTALL)),
    ]
    all_checks_passed &= check_file_contains(main_py, checks,
                                              "5. Toggle Functionality")
    
    # Check 6: GalleryEditor portrait adaptation
    checks = [
        ("GalleryEditor checks aspect_ratio",
         re.compile(r"is_portrait\s*=\s*slideshow\.aspect_ratio\s*==\s*[\"']9:16[\"']")),
        ("GalleryEditor adjusts grid_cols for portrait",
         re.compile(r"grid_cols\s*=\s*4")),
        ("GalleryEditor adjusts panel_size_hint for portrait",
         re.compile(r"panel_size_hint\s*=\s*\(0\.85")),
    ]
    all_checks_passed &= check_file_contains(main_py, checks,
                                              "6. GalleryEditor Portrait Adaptation")
    
    # Check 7: ScheduleEditor portrait adaptation
    checks = [
        ("ScheduleEditor checks aspect_ratio",
         re.compile(r"is_portrait\s*=\s*slideshow\.aspect_ratio\s*==\s*[\"']9:16[\"']")),
        ("ScheduleEditor adjusts panel_size_hint for portrait",
         re.compile(r"panel_size_hint\s*=\s*\(0\.85.*portrait")),
    ]
    all_checks_passed &= check_file_contains(main_py, checks,
                                              "7. ScheduleEditor Portrait Adaptation")
    
    # Check 8: FormatSelectionPopup portrait adaptation
    checks = [
        ("FormatSelectionPopup checks aspect_ratio",
         re.compile(r"aspect\s*=\s*slideshow\.aspect_ratio.*[\"']16:9[\"']")),
        ("FormatSelectionPopup sets panel_size for portrait",
         re.compile(r"panel_size\s*=\s*\(dp\(360\).*Portrait")),
    ]
    all_checks_passed &= check_file_contains(main_py, checks,
                                              "8. FormatSelectionPopup Portrait Adaptation")
    
    # Check 9: _apply_layout updates OrientationProvider
    checks = [
        ("_apply_layout updates OrientationProvider",
         re.compile(r"orientation_provider\.set_orientation\(self\.aspect_ratio\)")),
        ("_apply_layout logs toolbar placement",
         re.compile(r'toolbar_placement.*RIGHT.*vertical.*BOTTOM')),
    ]
    all_checks_passed &= check_file_contains(main_py, checks,
                                              "9. Layout Application")
    
    # Summary
    print(f"\n{'='*60}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*60}")
    
    if all_checks_passed:
        print("✓ All checks passed!")
        print("\nThe portrait mode fixes are correctly implemented.")
        print("\nNext steps:")
        print("1. Test the application in both 9:16 and 16:9 modes")
        print("2. Verify toolbar text is readable when screen is rotated")
        print("3. Check all modal views (Galerie, Zeiten, etc.) display correctly")
        print("4. Test toolbar toggle functionality")
        return True
    else:
        print("✗ Some checks failed!")
        print("\nPlease review the failed checks above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
