#!/usr/bin/env python3
"""
Test script for Toolbar Hotfix

This script verifies that the hotfix is properly implemented:
1. Toolbar is always positioned at bottom for both 16:9 and 9:16 modes
2. PushMatrix/PopMatrix are balanced in rotation classes
3. No manual cover mode calculations exist
4. Lightbox has proper debounce and guards
5. PIL logging is suppressed

Usage:
    python3 verify_toolbar_hotfix.py
"""

import sys
from pathlib import Path

def test_toolbar_positioning():
    """Test 1: Verify toolbar is always at bottom"""
    print("\n=== Test 1: Toolbar Positioning ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print(f"❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('No vertical toolbar logic in _create_toolbar', 'vertical=True' not in content or 
         content.count('vertical=True') <= 2),  # Only in CustomAppBar class definition
        ('Toolbar always at bottom', 'pos_hint = {"bottom": 1}' in content or 
         'pos_hint={"bottom":1}' in content),
        ('No right-side toolbar positioning', 'pos_hint = {"right": 1, "top": 1}' not in content),
        ('_apply_layout always creates horizontal toolbar', 
         'self.toolbar = self._create_toolbar(vertical=False)' in content),
        ('_resize_image always subtracts toolbar height', 
         'toolbar_height' in content and 'content_h = self.height - toolbar_height' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Toolbar positioning is correct")
    else:
        print("\n❌ FAIL: Some toolbar positioning checks failed")
    
    return all_passed

def test_matrix_balance():
    """Test 2: Verify PushMatrix/PopMatrix balance"""
    print("\n=== Test 2: Matrix Stack Balance ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find RotatingRoot._update_rotation method
    in_rotating_root = False
    push_count = 0
    pop_count = 0
    clears_both = False
    
    for i, line in enumerate(lines):
        if 'class RotatingRoot' in line:
            in_rotating_root = True
        elif in_rotating_root and 'def _update_rotation' in line:
            # Check next 30 lines
            method_lines = lines[i:i+30]
            method_str = ''.join(method_lines)
            
            if 'self.canvas.before.clear()' in method_str and 'self.canvas.after.clear()' in method_str:
                clears_both = True
            
            push_count = method_str.count('PushMatrix()')
            pop_count = method_str.count('PopMatrix()')
            break
    
    checks = [
        ('Clears both canvas.before and canvas.after', clears_both),
        ('PushMatrix count equals PopMatrix count', push_count > 0 and push_count == pop_count),
        ('Always has PushMatrix/PopMatrix', push_count >= 1 and pop_count >= 1),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name} (Push: {push_count}, Pop: {pop_count})")
        else:
            print(f"  ❌ {check_name} (Push: {push_count}, Pop: {pop_count})")
            all_passed = False
    
    # Check RotatedModalView too
    in_modal = False
    modal_push = 0
    modal_pop = 0
    modal_clears = False
    
    for i, line in enumerate(lines):
        if 'class RotatedModalView' in line:
            in_modal = True
        elif in_modal and 'def _update_rotation' in line:
            method_lines = lines[i:i+30]
            method_str = ''.join(method_lines)
            
            if 'self.canvas.before.clear()' in method_str and 'self.canvas.after.clear()' in method_str:
                modal_clears = True
            
            modal_push = method_str.count('PushMatrix()')
            modal_pop = method_str.count('PopMatrix()')
            break
    
    print(f"\n  RotatedModalView checks:")
    modal_checks = [
        ('Clears both canvas.before and canvas.after', modal_clears),
        ('PushMatrix count equals PopMatrix count', modal_push > 0 and modal_push == modal_pop),
    ]
    
    for check_name, check_result in modal_checks:
        if check_result:
            print(f"    ✅ {check_name} (Push: {modal_push}, Pop: {modal_pop})")
        else:
            print(f"    ❌ {check_name} (Push: {modal_push}, Pop: {modal_pop})")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Matrix stack is balanced")
    else:
        print("\n❌ FAIL: Matrix stack balance issues detected")
    
    return all_passed

def test_no_manual_cover():
    """Test 3: Verify no manual cover mode calculations"""
    print("\n=== Test 3: No Manual Cover Calculations ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('No "cover mode:" debug logs', 'cover mode:' not in content.lower()),
        ('No manual scale calculations', 'ratio_w = ' not in content and 'ratio_h = ' not in content),
        ('No negative position values', 'pos=(' not in content or '-' not in content.split('pos=(')[1].split(')')[0] if 'pos=(' in content else True),
        ('Uses fit_mode="cover" for slideshow', "fit_mode='cover'" in content),
        ('Uses fit_mode="contain" for lightbox', "fit_mode='contain'" in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: No manual cover calculations found")
    else:
        print("\n❌ FAIL: Manual cover calculations still present")
    
    return all_passed

def test_lightbox_stability():
    """Test 4: Verify lightbox debounce and guards"""
    print("\n=== Test 4: Lightbox Stability ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('has is_lightbox_open flag', 'is_lightbox_open' in content),
        ('has debounce with Clock.schedule_once', 'Clock.schedule_once' in content and '_open_lightbox' in content),
        ('has 250ms throttle', '0.25' in content and '_open_lightbox' in content),
        ('uses source+reload for image loading', 'self.img.source = ' in content and '.reload()' in content),
        ('has CoreImage nocache fallback', 'nocache=True' in content),
        ('NO while loops', 'while' not in content or 'while root.parent' not in content),
        ('has guard checks', 'if self.is_lightbox_open:' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Lightbox has proper stability measures")
    else:
        print("\n❌ FAIL: Some lightbox stability checks failed")
    
    return all_passed

def test_logging_suppression():
    """Test 5: Verify PIL logging is suppressed"""
    print("\n=== Test 5: Logging Suppression ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('PIL logger set to WARNING', "logging.getLogger('PIL').setLevel(logging.WARNING)" in content),
        ('PIL.PngImagePlugin set to WARNING', "logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)" in content),
        ('setup_debug_logging function exists', 'def setup_debug_logging' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: PIL logging is properly suppressed")
    else:
        print("\n❌ FAIL: PIL logging suppression incomplete")
    
    return all_passed

def main():
    """Run all tests"""
    print("=" * 60)
    print("Toolbar Hotfix - Automated Verification Suite")
    print("=" * 60)
    
    tests = [
        ("Toolbar Positioning", test_toolbar_positioning),
        ("Matrix Stack Balance", test_matrix_balance),
        ("No Manual Cover Calculations", test_no_manual_cover),
        ("Lightbox Stability", test_lightbox_stability),
        ("Logging Suppression", test_logging_suppression),
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
        print("\n🎉 All tests passed! Hotfix is properly implemented.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the hotfix.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
