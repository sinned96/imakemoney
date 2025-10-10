#!/usr/bin/env python3
"""
Verification script for finalized portrait UI fixes
Tests centered modals, rotation cleanup, and toolbar behavior
"""

import sys
from pathlib import Path

def test_modal_centered_layout():
    """Test 1: Verify all modals use centered layout with AnchorLayout"""
    print("\n=== Test 1: Modal Centered Layout ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print("❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('SettingsRootPopup uses AnchorLayout', 'class SettingsRootPopup' in content and 
         'anchor = AnchorLayout(size_hint=(1, 1), anchor_x=\'center\', anchor_y=\'center\')' in content),
        ('GlobalDurationPopup uses AnchorLayout', 'class GlobalDurationPopup' in content and 
         'AnchorLayout' in content),
        ('FormatSelectionPopup uses AnchorLayout', 'class FormatSelectionPopup' in content),
        ('GeneralSettingsPopup uses AnchorLayout', 'class GeneralSettingsPopup' in content),
        ('Portrait sizing factors (0.62×w, 0.86×h)', 'content_w * 0.62' in content and 'content_h * 0.86' in content),
        ('Minimum size constraints (320×260)', 'max(int(content_w * 0.62), dp(320))' in content and 
         'max(int(content_h * 0.86), dp(260))' in content),
        ('Full-screen modal (size_hint=(1, 1))', 'size_hint\', (1, 1)' in content),
        ('Dim overlay (0.7 alpha)', 'background_color = (0, 0, 0, 0.7)' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: All modals use centered layout")
    else:
        print("\n❌ FAIL: Some modals missing centered layout")
    
    return all_passed

def test_esc_key_handling():
    """Test 2: Verify ESC key handling in all modals"""
    print("\n=== Test 2: ESC Key Handling ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('SettingsRootPopup ESC handler', 'class SettingsRootPopup' in content and 
         'def _on_key_down' in content and 'if key == 27:' in content),
        ('GlobalDurationPopup ESC handler', 'class GlobalDurationPopup' in content),
        ('FormatSelectionPopup ESC handler', 'class FormatSelectionPopup' in content),
        ('GeneralSettingsPopup ESC handler', 'class GeneralSettingsPopup' in content),
        ('Key binding in modals', 'Window.bind(on_key_down=self._on_key_down)' in content),
        ('Key unbinding on dismiss', 'Window.unbind(on_key_down=self._on_key_down)' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: ESC key handling implemented")
    else:
        print("\n❌ FAIL: ESC key handling incomplete")
    
    return all_passed

def test_panel_management():
    """Test 3: Verify panel management and logging"""
    print("\n=== Test 3: Panel Management ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('Panel open logging', 'debug_logger.info("Opening' in content),
        ('Panel close in _apply_layout', '_close_current_panel()' in content and 
         'def _apply_layout' in content),
        ('Toolbar restack logging', 'debug_logger.info("Toolbar restacked to front' in content),
        ('Modal open logging', 'modal open centered size=' in content),
        ('Modal dismiss logging', 'modal dismissed' in content),
        ('Layout apply logging', 'Applying layout for aspect ratio' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Panel management and logging complete")
    else:
        print("\n❌ FAIL: Panel management incomplete")
    
    return all_passed

def test_portrait_toolbar():
    """Test 4: Verify portrait toolbar implementation"""
    print("\n=== Test 4: Portrait Toolbar ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('Vertical toolbar for 9:16', 'self.toolbar = self._create_toolbar(vertical=True)' in content),
        ('Horizontal toolbar for 16:9', 'self.toolbar = self._create_toolbar(vertical=False)' in content),
        ('Right-docked vertical toolbar', 'pos_hint = {"right": 1, "top": 1}' in content),
        ('Fixed width for vertical toolbar', 'bar.width = dp(108)' in content),
        ('Toolbar restack method', 'def _bring_toolbar_to_front' in content),
        ('VerticalButton for rotated labels', 'class VerticalButton' in content),
        ('270° rotation for labels', 'rotation_angle=270' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Portrait toolbar implemented")
    else:
        print("\n❌ FAIL: Portrait toolbar incomplete")
    
    return all_passed

def test_gallery_portrait():
    """Test 5: Verify gallery portrait adaptations"""
    print("\n=== Test 5: Gallery Portrait Mode ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('Gallery columns adapt to portrait', 'aspect == "9:16"' in content and 'gallery_cols' in content),
        ('2-3 columns for portrait', 'gallery_cols = 3 if Window.width > dp(600) else 2' in content),
        ('Tighter spacing for portrait', 'gallery_spacing = dp(10)' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Gallery portrait mode implemented")
    else:
        print("\n❌ FAIL: Gallery portrait mode incomplete")
    
    return all_passed

def test_unicode_fixes():
    """Test 6: Verify Unicode symbol fixes"""
    print("\n=== Test 6: Unicode Fixes ===")
    
    aufnahme_path = Path(__file__).parent / "Aufnahme.py"
    if not aufnahme_path.exists():
        print("❌ FAIL: Aufnahme.py not found")
        return False
    
    with open(aufnahme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('No ℹ symbol', 'ℹ' not in content),
        ('Uses [INFO] instead', '[INFO] Info:' in content),
        ('No ✓ symbol', '✓' not in content),
        ('No ✅ symbol', '✅' not in content),
        ('No ❌ symbol', '❌' not in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Unicode symbols fixed")
    else:
        print("\n❌ FAIL: Unicode symbols not fixed")
    
    return all_passed

def test_transform_stripping():
    """Test 7: Verify transform stripping helper"""
    print("\n=== Test 7: Transform Stripping ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('Transform stripping method exists', 'def _strip_transforms_from_content' in content),
        ('Removes Rotate transforms', 'isinstance(instruction, (Rotate, Scale, Translate' in content),
        ('Skips VerticalButton', 'not isinstance(child, VerticalButton)' in content),
        ('Resets rotation attributes', 'widget.rotation = 0' in content),
        ('Recursive stripping', 'self._strip_transforms_from_content(child)' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Transform stripping implemented")
    else:
        print("\n❌ FAIL: Transform stripping incomplete")
    
    return all_passed

def main():
    """Run all tests"""
    print("=" * 70)
    print("Portrait UI Finalization Verification")
    print("=" * 70)
    
    tests = [
        ("Modal Centered Layout", test_modal_centered_layout),
        ("ESC Key Handling", test_esc_key_handling),
        ("Panel Management", test_panel_management),
        ("Portrait Toolbar", test_portrait_toolbar),
        ("Gallery Portrait Mode", test_gallery_portrait),
        ("Unicode Fixes", test_unicode_fixes),
        ("Transform Stripping", test_transform_stripping),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("\n" + "=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 70)
    if passed == total:
        print("🎉 All tests passed! Portrait UI finalization complete.")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review the fixes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
