#!/usr/bin/env python3
"""
Test script for Portrait (9:16) UI Fixes

This script verifies that the portrait mode fixes are properly implemented:
1. AufnahmePopup uses full-screen ModalView with AnchorLayout
2. Panel tracking is implemented for single-open behavior
3. Vertical toolbar for 9:16 mode with proper positioning
4. ESC/Back key handling for modals
5. Proper logging for modal operations

Usage:
    python3 verify_portrait_fixes.py
"""

import sys
from pathlib import Path

def test_aufnahme_modal_setup():
    """Test 1: Verify AufnahmePopup uses full-screen ModalView with AnchorLayout"""
    print("\n=== Test 1: AufnahmePopup Modal Setup ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print(f"❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find AufnahmePopup class
    aufnahme_start = content.find("class AufnahmePopup(RotatedModalView):")
    if aufnahme_start == -1:
        print("  ❌ AufnahmePopup class not found")
        return False
    
    # Find the next class to get the entire AufnahmePopup class
    next_class = content.find("\nclass ", aufnahme_start + 10)
    if next_class == -1:
        next_class = len(content)
    
    aufnahme_section = content[aufnahme_start:next_class]
    
    checks = [
        ('Uses full-screen ModalView', "'size_hint', (1, 1)" in aufnahme_section or 
         "size_hint': (1, 1)" in aufnahme_section),
        ('Uses AnchorLayout for centering', 'AnchorLayout' in aufnahme_section),
        ('Has legacy cleanup method', '_cleanup_legacy_sheets' in aufnahme_section),
        ('Has ESC/Back key handler', '_on_key_down' in aufnahme_section),
        ('Semi-transparent background', 'background_color = (0, 0, 0, 0.7)' in aufnahme_section or
         'background_color=(0,0,0,0.7)' in aufnahme_section),
        ('Portrait sizing logic', 'aspect_ratio if slideshow else' in aufnahme_section and
         '0.62' in aufnahme_section and '0.86' in aufnahme_section),
        ('Binds Window key handler', 'Window.bind(on_key_down=' in aufnahme_section),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed

def test_panel_tracking():
    """Test 2: Verify panel tracking is implemented"""
    print("\n=== Test 2: Panel Tracking ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('App has _open_panel attribute', "self._open_panel = None" in content),
        ('Has _close_current_panel method', 'def _close_current_panel(self):' in content),
        ('Has _on_toolbar_item_pressed helper', 'def _on_toolbar_item_pressed(self, item_id, open_fn):' in content),
        ('Toolbar buttons use helper', '_on_toolbar_item_pressed("aufnahme"' in content or
         '_on_toolbar_item_pressed("schedule"' in content),
        ('open_aufnahme_popup tracks panel', 'app._open_panel = ("aufnahme", popup)' in content),
        ('open_gallery tracks panel', 'app._open_panel = ("gallery"' in content),
        ('Format switch closes panels', 'self.slideshow._close_current_panel()' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed

def test_vertical_toolbar():
    """Test 3: Verify vertical toolbar for 9:16 mode"""
    print("\n=== Test 3: Vertical Toolbar for 9:16 ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find _apply_layout method
    apply_layout_start = content.find("def _apply_layout(self):")
    if apply_layout_start == -1:
        print("  ❌ _apply_layout method not found")
        return False
    
    apply_layout_section = content[apply_layout_start:apply_layout_start + 2000]
    
    checks = [
        ('Creates vertical toolbar for 9:16', 
         'if self.aspect_ratio == "9:16":' in apply_layout_section and
         '_create_toolbar(vertical=True)' in apply_layout_section),
        ('Creates horizontal toolbar for 16:9',
         'vertical=False' in apply_layout_section),
        ('Logs toolbar creation for 9:16',
         'Created toolbar at RIGHT (vertical) for 9:16 mode' in apply_layout_section),
        ('CustomAppBar supports vertical mode',
         'CustomAppBar(title=' in content and 'vertical=vertical)' in content),
        ('Vertical toolbar positioned right',
         'pos_hint = {"right": 1, "top": 1}' in content),
        ('Vertical toolbar has fixed width',
         'bar.width = dp(108)' in content or 'width = dp(110)' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    # Check _resize_image accounts for vertical toolbar
    resize_start = content.find("def _resize_image(self,img_widget):")
    if resize_start != -1:
        resize_section = content[resize_start:resize_start + 1500]
        if 'self.aspect_ratio == "9:16"' in resize_section and 'toolbar_width' in resize_section:
            print(f"  ✅ _resize_image accounts for vertical toolbar width")
        else:
            print(f"  ❌ _resize_image doesn't account for vertical toolbar width")
            all_passed = False
    
    return all_passed

def test_logging():
    """Test 4: Verify proper logging is in place"""
    print("\n=== Test 4: Logging ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('Logs removed legacy sheets',
         'Removed {removed_count} legacy Aufnahme sheet(s)' in content or
         'f"Removed {removed_count} legacy Aufnahme sheet(s)"' in content),
        ('Logs modal open with size',
         'Aufnahme modal open centered size=' in content),
        ('Logs modal dismissed',
         'Aufnahme modal dismissed' in content),
        ('Logs toolbar creation for 9:16',
         'Created toolbar at RIGHT (vertical) for 9:16 mode' in content),
        ('Logs closed panel',
         'Closed panel:' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed

def test_key_handling():
    """Test 5: Verify ESC/Back key handling"""
    print("\n=== Test 5: ESC/Back Key Handling ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find _on_key_down method in AufnahmePopup
    checks = [
        ('Has _on_key_down method', 'def _on_key_down(self, window, key,' in content),
        ('Checks for ESC key (27)', 'if key == 27:' in content),
        ('Calls close_popup on ESC', 'self.close_popup(None)' in content),
        ('Binds key handler in __init__', 'Window.bind(on_key_down=self._on_key_down)' in content),
        ('Unbinds key handler in close', 'Window.unbind(on_key_down=self._on_key_down)' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("=" * 60)
    print("Portrait (9:16) UI Fixes - Automated Verification Suite")
    print("=" * 60)
    
    tests = [
        ("AufnahmePopup Modal Setup", test_aufnahme_modal_setup),
        ("Panel Tracking", test_panel_tracking),
        ("Vertical Toolbar for 9:16", test_vertical_toolbar),
        ("Logging", test_logging),
        ("ESC/Back Key Handling", test_key_handling),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print("=" * 60)
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Portrait fixes are properly implemented.")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
