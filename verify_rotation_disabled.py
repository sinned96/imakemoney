#!/usr/bin/env python3
"""
Test script to verify canvas rotation has been properly disabled
"""
from pathlib import Path
import re

def test_rotation_disabled():
    """Test that canvas rotation is disabled in RotatingRoot and RotatedModalView"""
    print("\n=== Test: Canvas Rotation Disabled ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print("❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # Check RotatingRoot._update_rotation
    rotating_root_pattern = r'class RotatingRoot.*?def _update_rotation\(self.*?\):.*?(?=\n    def |\nclass )'
    rotating_root_match = re.search(rotating_root_pattern, content, re.DOTALL)
    
    if rotating_root_match:
        rotating_root_code = rotating_root_match.group(0)
        
        # Check that Translate is NOT called with non-zero values in portrait mode
        has_translate = 'Translate(self.width, 0, 0)' in rotating_root_code and 'if angle != 0:' not in rotating_root_code.split('Translate(self.width, 0, 0)')[0].split('\n')[-5:]
        
        # Check that CanvasRotate is NOT called in portrait mode
        has_canvas_rotate = 'CanvasRotate(angle=angle' in rotating_root_code and 'if angle != 0:' not in rotating_root_code.split('CanvasRotate')[0].split('\n')[-5:]
        
        # Check that Push/PopMatrix are still present
        has_push = 'PushMatrix()' in rotating_root_code
        has_pop = 'PopMatrix()' in rotating_root_code
        
        # Check for logging
        has_logging = 'Rotation disabled for root' in rotating_root_code or 'layout-based portrait' in rotating_root_code
        
        checks.append(('RotatingRoot has PushMatrix', has_push))
        checks.append(('RotatingRoot has PopMatrix', has_pop))
        checks.append(('RotatingRoot does NOT call Translate in rotation', not has_translate))
        checks.append(('RotatingRoot does NOT call CanvasRotate in rotation', not has_canvas_rotate))
        checks.append(('RotatingRoot has rotation disabled logging', has_logging))
    else:
        checks.append(('RotatingRoot._update_rotation found', False))
    
    # Check RotatedModalView._update_rotation
    modal_view_pattern = r'class RotatedModalView.*?def _update_rotation\(self.*?\):.*?(?=\n    def |\nclass )'
    modal_view_match = re.search(modal_view_pattern, content, re.DOTALL)
    
    if modal_view_match:
        modal_view_code = modal_view_match.group(0)
        
        # Check that Translate is NOT called with non-zero values in portrait mode
        has_translate = 'Translate(self.width, 0, 0)' in modal_view_code and 'if angle != 0:' not in modal_view_code.split('Translate(self.width, 0, 0)')[0].split('\n')[-5:]
        
        # Check that CanvasRotate is NOT called in portrait mode
        has_canvas_rotate = 'CanvasRotate(angle=angle' in modal_view_code and 'if angle != 0:' not in modal_view_code.split('CanvasRotate')[0].split('\n')[-5:]
        
        # Check that Push/PopMatrix are still present
        has_push = 'PushMatrix()' in modal_view_code
        has_pop = 'PopMatrix()' in modal_view_code
        
        # Check for logging
        has_logging = 'Rotation disabled for modals' in modal_view_code or 'layout-based portrait' in modal_view_code
        
        checks.append(('RotatedModalView has PushMatrix', has_push))
        checks.append(('RotatedModalView has PopMatrix', has_pop))
        checks.append(('RotatedModalView does NOT call Translate in rotation', not has_translate))
        checks.append(('RotatedModalView does NOT call CanvasRotate in rotation', not has_canvas_rotate))
        checks.append(('RotatedModalView has rotation disabled logging', has_logging))
    else:
        checks.append(('RotatedModalView._update_rotation found', False))
    
    # Check that width/height swapping is removed from RotatedModalView.__init__
    modal_init_pattern = r'class RotatedModalView.*?def __init__\(self.*?\):.*?super\(\).__init__'
    modal_init_match = re.search(modal_init_pattern, content, re.DOTALL)
    
    if modal_init_match:
        modal_init_code = modal_init_match.group(0)
        has_swap = "kwargs['size_hint'] = (h, w)" in modal_init_code or "kwargs['size'] = (h, w)" in modal_init_code
        checks.append(('RotatedModalView does NOT swap width/height', not has_swap))
    else:
        checks.append(('RotatedModalView.__init__ found', False))
    
    # Check that VerticalButton still rotates (toolbar labels)
    vertical_button_pattern = r'class VerticalButton.*?def _update_rotation\(self.*?\):.*?(?=\n    def |\nclass )'
    vertical_button_match = re.search(vertical_button_pattern, content, re.DOTALL)
    
    if vertical_button_match:
        vertical_button_code = vertical_button_match.group(0)
        has_rotate = 'Rotate(angle=' in vertical_button_code
        checks.append(('VerticalButton STILL rotates (for toolbar labels)', has_rotate))
    else:
        checks.append(('VerticalButton found', False))
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Canvas rotation properly disabled")
    else:
        print("\n❌ FAIL: Some checks failed")
    
    return all_passed


def test_modal_centering():
    """Test that modals still use proper centering with AnchorLayout"""
    print("\n=== Test: Modal Centering ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print("❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # Check AufnahmePopup
    aufnahme_pattern = r'class AufnahmePopup.*?(?=\nclass )'
    aufnahme_match = re.search(aufnahme_pattern, content, re.DOTALL)
    
    if aufnahme_match:
        aufnahme_code = aufnahme_match.group(0)
        has_anchor = 'AnchorLayout' in aufnahme_code
        has_portrait_factors = '0.62' in aufnahme_code and '0.86' in aufnahme_code
        has_min_size = 'dp(320)' in aufnahme_code and 'dp(260)' in aufnahme_code
        checks.append(('AufnahmePopup uses AnchorLayout', has_anchor))
        checks.append(('AufnahmePopup uses portrait factors (0.62, 0.86)', has_portrait_factors))
        checks.append(('AufnahmePopup has minimum size constraints', has_min_size))
    
    # Check FormatSelectionPopup
    format_pattern = r'class FormatSelectionPopup.*?(?=\nclass )'
    format_match = re.search(format_pattern, content, re.DOTALL)
    
    if format_match:
        format_code = format_match.group(0)
        has_anchor = 'AnchorLayout' in format_code
        has_portrait_factors = '0.62' in format_code and '0.86' in format_code
        checks.append(('FormatSelectionPopup uses AnchorLayout', has_anchor))
        checks.append(('FormatSelectionPopup uses portrait factors', has_portrait_factors))
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Modal centering verified")
    else:
        print("\n❌ FAIL: Some modal centering checks failed")
    
    return all_passed


def test_panel_management():
    """Test that panel management functions are present"""
    print("\n=== Test: Panel Management ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print("❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('_close_current_panel method exists', 'def _close_current_panel(self):' in content),
        ('_on_toolbar_item_pressed method exists', 'def _on_toolbar_item_pressed(self, item_id, open_fn):' in content),
        ('_apply_layout closes panels', '_close_current_panel()' in content and 'def _apply_layout(self):' in content),
        ('open_aufnahme_popup exists', 'def open_aufnahme_popup(self):' in content),
        ('open_format_selection exists', 'def open_format_selection(self):' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Panel management verified")
    else:
        print("\n❌ FAIL: Some panel management checks failed")
    
    return all_passed


if __name__ == '__main__':
    test1 = test_rotation_disabled()
    test2 = test_modal_centering()
    test3 = test_panel_management()
    
    if test1 and test2 and test3:
        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED")
        print("="*50)
        exit(0)
    else:
        print("\n" + "="*50)
        print("❌ SOME TESTS FAILED")
        print("="*50)
        exit(1)
