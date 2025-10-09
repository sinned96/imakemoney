#!/usr/bin/env python3
"""
Verification script for Portrait UI (9:16) Refinements

This script verifies that the portrait UI fixes are properly implemented:
1. Configuration constants are defined
2. Toolbar positioning logic is correct for 9:16 vs 16:9
3. VerticalButton supports configurable rotation and flip
4. Popup toggle behavior is implemented
5. Content views adjust for portrait mode

Usage:
    python3 verify_portrait_ui.py
"""

import sys
from pathlib import Path


def test_configuration_constants():
    """Test 1: Verify portrait configuration constants are defined"""
    print("\n=== Test 1: Configuration Constants ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print(f"❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('PORTRAIT_TOOLBAR_WIDTH is defined', 'PORTRAIT_TOOLBAR_WIDTH' in content),
        ('PORTRAIT_LABEL_ANGLE is defined', 'PORTRAIT_LABEL_ANGLE' in content),
        ('PORTRAIT_LABEL_FLIP is defined', 'PORTRAIT_LABEL_FLIP' in content),
        ('PORTRAIT_LABEL_ANGLE set to -90', 'PORTRAIT_LABEL_ANGLE = -90' in content),
    ]
    
    passed = True
    for desc, check in checks:
        status = "✅" if check else "❌"
        print(f"{status} {desc}")
        if not check:
            passed = False
    
    return passed


def test_toolbar_positioning():
    """Test 2: Verify toolbar positioning logic for 9:16 vs 16:9"""
    print("\n=== Test 2: Toolbar Positioning Logic ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('_apply_layout creates vertical toolbar for 9:16', 
         'if self.aspect_ratio == "9:16":' in content and 
         'self.toolbar = self._create_toolbar(vertical=True)' in content),
        ('_apply_layout creates horizontal toolbar for 16:9', 
         'else:' in content and 
         'self.toolbar = self._create_toolbar(vertical=False)' in content),
        ('Toolbar positioned at RIGHT for portrait', 
         'pos_hint = {"right": 1, "top": 1}' in content or 
         'pos_hint = {\'right\': 1, \'top\': 1}' in content),
        ('Toolbar positioned at BOTTOM for landscape', 
         'pos_hint = {"bottom": 1}' in content or 
         'pos_hint = {\'bottom\': 1}' in content),
        ('Log message for RIGHT toolbar in 9:16', 
         'Created toolbar at RIGHT' in content),
        ('Log message for BOTTOM toolbar in 16:9', 
         'Created toolbar at BOTTOM' in content),
    ]
    
    passed = True
    for desc, check in checks:
        status = "✅" if check else "❌"
        print(f"{status} {desc}")
        if not check:
            passed = False
    
    return passed


def test_vertical_button_rotation():
    """Test 3: Verify VerticalButton supports configurable rotation"""
    print("\n=== Test 3: VerticalButton Rotation Support ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('VerticalButton accepts rotation_angle parameter', 
         'def __init__(self, rotation_angle=' in content and 
         'class VerticalButton' in content),
        ('VerticalButton accepts flip_horizontal parameter', 
         'flip_horizontal' in content and 
         'class VerticalButton' in content),
        ('VerticalButton uses PORTRAIT_LABEL_ANGLE', 
         'PORTRAIT_LABEL_ANGLE' in content and 
         'self.rotation_angle' in content),
        ('VerticalButton uses PORTRAIT_LABEL_FLIP', 
         'PORTRAIT_LABEL_FLIP' in content and 
         'self.flip_horizontal' in content),
        ('VerticalButton applies Scale for flip', 
         'Scale(-1, 1' in content or 'Scale(x_scale' in content),
        ('VerticalButton uses PushMatrix/PopMatrix', 
         'PushMatrix()' in content and 'PopMatrix()' in content),
    ]
    
    passed = True
    for desc, check in checks:
        status = "✅" if check else "❌"
        print(f"{status} {desc}")
        if not check:
            passed = False
    
    return passed


def test_resize_image_logic():
    """Test 4: Verify _resize_image accounts for toolbar position"""
    print("\n=== Test 4: Image Resize Logic for Toolbar Position ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the _resize_image method
    resize_start = content.find('def _resize_image(')
    if resize_start == -1:
        print("❌ FAIL: _resize_image method not found")
        return False
    
    # Get the method content (roughly until next def)
    resize_end = content.find('\n    def ', resize_start + 1)
    resize_content = content[resize_start:resize_end] if resize_end != -1 else content[resize_start:]
    
    checks = [
        ('Checks for 9:16 aspect ratio', 
         'if self.aspect_ratio == "9:16"' in resize_content or 
         "if self.aspect_ratio == '9:16'" in resize_content),
        ('Calculates toolbar_width for portrait', 
         'toolbar_width' in resize_content and '9:16' in resize_content),
        ('Adjusts content_w for portrait', 
         'content_w = self.width - toolbar_width' in resize_content),
        ('Calculates toolbar_height for landscape', 
         'toolbar_height' in resize_content),
        ('Adjusts content_h for landscape', 
         'content_h = self.height - toolbar_height' in resize_content),
    ]
    
    passed = True
    for desc, check in checks:
        status = "✅" if check else "❌"
        print(f"{status} {desc}")
        if not check:
            passed = False
    
    return passed


def test_popup_toggle_behavior():
    """Test 5: Verify popup toggle behavior is implemented"""
    print("\n=== Test 5: Popup Toggle Behavior ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('current_popup tracking variable', 
         'self.current_popup' in content),
        ('current_popup_type tracking variable', 
         'self.current_popup_type' in content),
        ('_track_popup method exists', 
         'def _track_popup(' in content),
        ('_close_current_popup method exists', 
         'def _close_current_popup(' in content),
        ('_clear_popup_tracking method exists', 
         'def _clear_popup_tracking(' in content),
        ('Toggle check in open_aufnahme_popup', 
         'if self.current_popup_type == "aufnahme"' in content),
        ('Toggle check in open_format_selection', 
         'if self.current_popup_type == "format"' in content),
        ('Toggle check in open_settings_root', 
         'if self.current_popup_type == "settings"' in content),
        ('Clock.schedule_once for dismiss', 
         'Clock.schedule_once(lambda dt: self.dismiss()' in content),
    ]
    
    passed = True
    for desc, check in checks:
        status = "✅" if check else "❌"
        print(f"{status} {desc}")
        if not check:
            passed = False
    
    return passed


def test_gallery_portrait_columns():
    """Test 6: Verify gallery adjusts columns for portrait"""
    print("\n=== Test 6: Gallery Column Adjustment ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('Gallery checks aspect ratio for columns', 
         'grid_cols' in content and '9:16' in content),
        ('Gallery uses fewer columns in portrait', 
         '5 if slideshow.aspect_ratio == "9:16"' in content or
         '5 if' in content and '9:16' in content),
        ('Gallery uses more columns in landscape', 
         'else 8' in content or ': 8' in content),
    ]
    
    passed = True
    for desc, check in checks:
        status = "✅" if check else "❌"
        print(f"{status} {desc}")
        if not check:
            passed = False
    
    return passed


def test_customappbar_width():
    """Test 7: Verify CustomAppBar uses PORTRAIT_TOOLBAR_WIDTH"""
    print("\n=== Test 7: CustomAppBar Width Configuration ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find CustomAppBar class
    appbar_start = content.find('class CustomAppBar')
    if appbar_start == -1:
        print("❌ FAIL: CustomAppBar class not found")
        return False
    
    # Get the __init__ method (roughly)
    init_start = content.find('def __init__', appbar_start)
    init_end = content.find('\n    def ', init_start + 1)
    init_content = content[init_start:init_end] if init_end != -1 else content[init_start:init_start + 1000]
    
    checks = [
        ('CustomAppBar uses PORTRAIT_TOOLBAR_WIDTH', 
         'PORTRAIT_TOOLBAR_WIDTH' in init_content),
        ('Width set for vertical mode', 
         'if vertical:' in init_content and 'width =' in init_content),
    ]
    
    passed = True
    for desc, check in checks:
        status = "✅" if check else "❌"
        print(f"{status} {desc}")
        if not check:
            passed = False
    
    return passed


def main():
    """Run all tests"""
    print("=" * 60)
    print("Portrait UI Refinement - Verification Suite")
    print("=" * 60)
    
    tests = [
        ("Configuration Constants", test_configuration_constants),
        ("Toolbar Positioning Logic", test_toolbar_positioning),
        ("VerticalButton Rotation", test_vertical_button_rotation),
        ("Image Resize Logic", test_resize_image_logic),
        ("Popup Toggle Behavior", test_popup_toggle_behavior),
        ("Gallery Column Adjustment", test_gallery_portrait_columns),
        ("CustomAppBar Width", test_customappbar_width),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Portrait UI refinements are properly implemented.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
