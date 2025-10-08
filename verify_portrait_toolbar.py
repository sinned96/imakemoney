#!/usr/bin/env python3
"""
Verification script for 9:16 Portrait Toolbar and UI Consistency

This script verifies that the following fixes are properly implemented:
1. Toolbar positioning: vertical on right for 9:16, horizontal at bottom for 16:9
2. Toggle behavior for toolbar items
3. Content area calculation accounts for toolbar position
4. Modal rotation uses center-based transform
5. VerticalButton text rotation is correct

Usage:
    python3 verify_portrait_toolbar.py
"""

import os
import json
import sys
from pathlib import Path

def test_toolbar_positioning():
    """Test 1: Verify toolbar positioning logic"""
    print("\n=== Test 1: Toolbar Positioning Logic ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print(f"❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('9:16 creates vertical toolbar', 'self.aspect_ratio == "9:16"' in content and 'vertical=True' in content),
        ('16:9 creates horizontal toolbar', 'vertical=False' in content),
        ('Vertical toolbar positioned right', 'pos_hint={"right":1}' in content or 'pos_hint = {"right": 1}' in content),
        ('Horizontal toolbar positioned bottom', 'pos_hint={"bottom":1}' in content or 'pos_hint = {"bottom": 1}' in content),
        ('Debug log for vertical toolbar', '"Created vertical toolbar on RIGHT for 9:16 mode"' in content),
        ('Debug log for horizontal toolbar', '"Created horizontal toolbar at bottom for 16:9 mode"' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Toolbar positioning logic is correct")
    else:
        print("\n❌ FAIL: Some toolbar positioning checks failed")
    
    return all_passed

def test_toggle_behavior():
    """Test 2: Verify toolbar toggle behavior"""
    print("\n=== Test 2: Toolbar Toggle Behavior ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print(f"❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('current_popup tracking', 'self.current_popup=' in content),
        ('current_popup_type tracking', 'self.current_popup_type=' in content),
        ('_close_current_popup_or_overlay method', 'def _close_current_popup_or_overlay' in content),
        ('Gallery toggle check', 'if self.current_popup_type == "gallery"' in content),
        ('Zeiten toggle check', 'if self.current_popup_type == "zeiten"' in content),
        ('Settings toggle check', 'if self.current_popup_type == "settings"' in content),
        ('Aufnahme toggle check', 'if self.current_popup_type == "aufnahme"' in content),
        ('Format toggle check', 'if self.current_popup_type == "format"' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Toggle behavior is implemented")
    else:
        print("\n❌ FAIL: Some toggle behavior checks failed")
    
    return all_passed

def test_content_area_calculation():
    """Test 3: Verify content area calculation"""
    print("\n=== Test 3: Content Area Calculation ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print(f"❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('Content area check for 9:16', 'if self.aspect_ratio == "9:16"' in content),
        ('Toolbar width subtraction in 9:16', 'content_w = self.width - toolbar_width' in content),
        ('Toolbar height subtraction in 16:9', 'content_h = self.height - toolbar_height' in content),
        ('Portrait toolbar width default', 'dp(110)' in content),
        ('Landscape toolbar height default', 'dp(60)' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Content area calculation is correct")
    else:
        print("\n❌ FAIL: Some content area checks failed")
    
    return all_passed

def test_modal_rotation():
    """Test 4: Verify modal rotation is center-based"""
    print("\n=== Test 4: Modal Rotation ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print(f"❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('RotatedModalView class exists', 'class RotatedModalView(ModalView):' in content),
        ('Center-based rotation comment', 'center-based rotation' in content.lower() or 'translate to center' in content.lower()),
        ('center_x and center_y variables', 'center_x' in content and 'center_y' in content),
        ('Translate to origin', 'Translate(-center_x, -center_y' in content),
        ('Translate back', 'Translate(center_x, center_y' in content),
        ('PushMatrix/PopMatrix pairing', 'PushMatrix()' in content and 'PopMatrix()' in content),
        ('overlay_color set', 'overlay_color' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Modal rotation is center-based")
    else:
        print("\n❌ FAIL: Some modal rotation checks failed")
    
    return all_passed

def test_vertical_button():
    """Test 5: Verify VerticalButton implementation"""
    print("\n=== Test 5: VerticalButton Implementation ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print(f"❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('VerticalButton class exists', 'class VerticalButton(Button):' in content),
        ('rotation_angle parameter', 'rotation_angle' in content),
        ('270 degree rotation comment', '270' in content and 'rotation_angle=270' in content),
        ('Rotation around button center', 'origin=self.center' in content),
        ('Padding for text clipping', 'self.padding' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: VerticalButton is correctly implemented")
    else:
        print("\n❌ FAIL: Some VerticalButton checks failed")
    
    return all_passed

def test_aspect_ratio_persistence():
    """Test 6: Verify aspect ratio persistence"""
    print("\n=== Test 6: Aspect Ratio Persistence ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print(f"❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('persist_meta method exists', 'def persist_meta(self):' in content),
        ('aspect_ratio in meta', '"aspect_ratio": self.aspect_ratio' in content),
        ('load_image_meta function', 'def load_image_meta():' in content),
        ('aspect_ratio loaded from meta', 'self.aspect_ratio = meta.get("aspect_ratio"' in content),
        ('OrientationProvider updated', 'orientation_provider.set_orientation' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Aspect ratio persistence is implemented")
    else:
        print("\n❌ FAIL: Some persistence checks failed")
    
    return all_passed

def main():
    """Run all tests"""
    print("=" * 60)
    print("Portrait Toolbar & UI Consistency - Verification Suite")
    print("=" * 60)
    
    tests = [
        ("Toolbar Positioning Logic", test_toolbar_positioning),
        ("Toolbar Toggle Behavior", test_toggle_behavior),
        ("Content Area Calculation", test_content_area_calculation),
        ("Modal Rotation", test_modal_rotation),
        ("VerticalButton Implementation", test_vertical_button),
        ("Aspect Ratio Persistence", test_aspect_ratio_persistence),
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
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Portrait toolbar fixes are properly implemented.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
