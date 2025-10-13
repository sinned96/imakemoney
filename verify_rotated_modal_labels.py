#!/usr/bin/env python3
"""
Test script to verify rotated modal labels implementation for portrait mode
"""
from pathlib import Path
import re

def test_rotated_label_class():
    """Test that RotatedLabel class exists and has proper implementation"""
    print("\n=== Test: RotatedLabel Class ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print("❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # Check RotatedLabel class exists
    has_rotated_label = 'class RotatedLabel(Label):' in content
    checks.append(('RotatedLabel class exists', has_rotated_label))
    
    if has_rotated_label:
        # Extract RotatedLabel class
        rotated_label_pattern = r'class RotatedLabel\(Label\):.*?(?=\nclass )'
        rotated_label_match = re.search(rotated_label_pattern, content, re.DOTALL)
        
        if rotated_label_match:
            rotated_label_code = rotated_label_match.group(0)
            
            # Check for rotation_angle parameter
            has_rotation_angle = 'rotation_angle' in rotated_label_code
            checks.append(('RotatedLabel has rotation_angle parameter', has_rotation_angle))
            
            # Check for PushMatrix/PopMatrix
            has_push = 'PushMatrix()' in rotated_label_code
            has_pop = 'PopMatrix()' in rotated_label_code
            checks.append(('RotatedLabel has PushMatrix', has_push))
            checks.append(('RotatedLabel has PopMatrix', has_pop))
            
            # Check for Rotate instruction
            has_rotate = 'Rotate(angle=self.rotation_angle' in rotated_label_code
            checks.append(('RotatedLabel rotates text', has_rotate))
            
            # Check for padding to prevent clipping
            has_padding = 'PORTRAIT_MODAL_LABEL_PADDING' in rotated_label_code or 'padding' in rotated_label_code
            checks.append(('RotatedLabel has padding to prevent clipping', has_padding))
    
    # Print results
    all_passed = all(result for _, result in checks)
    for check_name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    return all_passed

def test_rotated_button_class():
    """Test that RotatedButton class exists and has proper implementation"""
    print("\n=== Test: RotatedButton Class ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print("❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # Check RotatedButton class exists
    has_rotated_button = 'class RotatedButton(Button):' in content
    checks.append(('RotatedButton class exists', has_rotated_button))
    
    if has_rotated_button:
        # Extract RotatedButton class
        rotated_button_pattern = r'class RotatedButton\(Button\):.*?(?=\nclass )'
        rotated_button_match = re.search(rotated_button_pattern, content, re.DOTALL)
        
        if rotated_button_match:
            rotated_button_code = rotated_button_match.group(0)
            
            # Check for rotation_angle parameter
            has_rotation_angle = 'rotation_angle' in rotated_button_code
            checks.append(('RotatedButton has rotation_angle parameter', has_rotation_angle))
            
            # Check for PushMatrix/PopMatrix
            has_push = 'PushMatrix()' in rotated_button_code
            has_pop = 'PopMatrix()' in rotated_button_code
            checks.append(('RotatedButton has PushMatrix', has_push))
            checks.append(('RotatedButton has PopMatrix', has_pop))
            
            # Check for Rotate instruction
            has_rotate = 'Rotate(angle=self.rotation_angle' in rotated_button_code
            checks.append(('RotatedButton rotates text', has_rotate))
            
            # Check for padding to prevent clipping
            has_padding = 'PORTRAIT_MODAL_LABEL_PADDING' in rotated_button_code or 'padding' in rotated_button_code
            checks.append(('RotatedButton has padding to prevent clipping', has_padding))
    
    # Print results
    all_passed = all(result for _, result in checks)
    for check_name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    return all_passed

def test_config_constants():
    """Test that config constants are defined"""
    print("\n=== Test: Config Constants ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print("❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # Check for PORTRAIT_MODAL_LABEL_ANGLE constant
    has_angle_constant = 'PORTRAIT_MODAL_LABEL_ANGLE' in content
    checks.append(('PORTRAIT_MODAL_LABEL_ANGLE constant defined', has_angle_constant))
    
    # Check that it's set to -90
    if has_angle_constant:
        angle_match = re.search(r'PORTRAIT_MODAL_LABEL_ANGLE\s*=\s*(-?\d+)', content)
        if angle_match:
            angle_value = int(angle_match.group(1))
            is_correct_angle = angle_value == -90
            checks.append(('PORTRAIT_MODAL_LABEL_ANGLE is -90', is_correct_angle))
    
    # Check for PORTRAIT_MODAL_LABEL_PADDING constant
    has_padding_constant = 'PORTRAIT_MODAL_LABEL_PADDING' in content
    checks.append(('PORTRAIT_MODAL_LABEL_PADDING constant defined', has_padding_constant))
    
    # Print results
    all_passed = all(result for _, result in checks)
    for check_name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    return all_passed

def test_format_selection_popup():
    """Test that FormatSelectionPopup uses RotatedLabel and RotatedButton"""
    print("\n=== Test: FormatSelectionPopup Implementation ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print("❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # Extract FormatSelectionPopup class
    format_popup_pattern = r'class FormatSelectionPopup\(.*?\):.*?def _on_key_down'
    format_popup_match = re.search(format_popup_pattern, content, re.DOTALL)
    
    if format_popup_match:
        format_popup_code = format_popup_match.group(0)
        
        # Check that RotatedLabel is used
        uses_rotated_label = 'RotatedLabel(' in format_popup_code
        checks.append(('FormatSelectionPopup uses RotatedLabel', uses_rotated_label))
        
        # Check that RotatedButton is used
        uses_rotated_button = 'RotatedButton(' in format_popup_code
        checks.append(('FormatSelectionPopup uses RotatedButton', uses_rotated_button))
        
        # Check that rotation_angle is set based on portrait mode
        has_label_rotation = 'label_rotation' in format_popup_code
        checks.append(('FormatSelectionPopup calculates label_rotation', has_label_rotation))
        
        # Check that is_portrait is determined
        has_is_portrait = 'is_portrait' in format_popup_code
        checks.append(('FormatSelectionPopup determines is_portrait', has_is_portrait))
        
        # Check that rotation is conditional on portrait mode
        has_conditional = 'PORTRAIT_MODAL_LABEL_ANGLE if' in format_popup_code
        checks.append(('Rotation is conditional on portrait mode', has_conditional))
        
        # Check for logging of rotated labels
        has_logging = 'Format modal labels rotated' in format_popup_code
        checks.append(('FormatSelectionPopup logs rotated labels', has_logging))
    else:
        checks.append(('FormatSelectionPopup found', False))
    
    # Print results
    all_passed = all(result for _, result in checks)
    for check_name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    return all_passed

def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("Verifying Rotated Modal Labels Implementation")
    print("="*60)
    
    results = []
    results.append(test_config_constants())
    results.append(test_rotated_label_class())
    results.append(test_rotated_button_class())
    results.append(test_format_selection_popup())
    
    print("\n" + "="*60)
    if all(results):
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("="*60)
        return True
    else:
        print("✗✗✗ SOME TESTS FAILED ✗✗✗")
        print("="*60)
        return False

if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
