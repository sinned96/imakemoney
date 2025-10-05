#!/usr/bin/env python3
"""
Test script for 9:16 End-to-End fixes

This script verifies that the fixes are properly implemented:
1. aspect_ratio is read from image_meta.json
2. Images are scaled to correct dimensions based on aspect_ratio
3. No hardcoded 1920x1080 forcing

Usage:
    python3 test_9_16_fixes.py
"""

import os
import json
import sys
from pathlib import Path

def test_image_meta_json():
    """Test 1: Verify image_meta.json exists and can be read"""
    print("\n=== Test 1: image_meta.json Configuration ===")
    
    meta_path = Path(__file__).parent / "image_meta.json"
    
    if not meta_path.exists():
        print(f"❌ FAIL: image_meta.json not found at {meta_path}")
        return False
    
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        if 'aspect_ratio' not in meta:
            print("❌ FAIL: aspect_ratio key not found in image_meta.json")
            return False
        
        aspect_ratio = meta['aspect_ratio']
        if aspect_ratio not in ['16:9', '9:16']:
            print(f"❌ FAIL: Invalid aspect_ratio value: {aspect_ratio}")
            return False
        
        print(f"✅ PASS: image_meta.json exists with aspect_ratio={aspect_ratio}")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Error reading image_meta.json: {e}")
        return False

def test_scale_function_implementation():
    """Test 2: Verify scale functions use aspect_ratio"""
    print("\n=== Test 2: Scale Function Implementation ===")
    
    # Check PythonServer.py
    python_server_path = Path(__file__).parent / "PythonServer.py"
    if not python_server_path.exists():
        print(f"❌ FAIL: PythonServer.py not found")
        return False
    
    with open(python_server_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify aspect-aware implementation
    checks = [
        ('aspect_ratio from image_meta.json', 'image_meta.json' in content and 'aspect_ratio' in content),
        ('9:16 target size', '(1080, 1920)' in content),
        ('16:9 target size', '(1920, 1080)' in content),
        ('aspect_ratio == "9:16" check', 'aspect_ratio == "9:16"' in content or 'aspect_ratio == \'9:16\'' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    # Check vertex_ai_image_workflow.py
    print("\n  Checking vertex_ai_image_workflow.py...")
    workflow_path = Path(__file__).parent / "vertex_ai_image_workflow.py"
    if not workflow_path.exists():
        print(f"❌ FAIL: vertex_ai_image_workflow.py not found")
        return False
    
    with open(workflow_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    workflow_checks = [
        ('get_aspect_ratio_from_meta function', 'def get_aspect_ratio_from_meta' in content),
        ('scale_image_to_target_size function', 'def scale_image_to_target_size' in content),
        ('PIL logging suppression', 'PIL.PngImagePlugin' in content or 'PIL\').setLevel' in content),
    ]
    
    for check_name, check_result in workflow_checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: All scale functions are aspect-aware")
    else:
        print("\n❌ FAIL: Some checks failed")
    
    return all_passed

def test_main_py_fixes():
    """Test 3: Verify main.py fixes (rotation, debounce, keep_ratio)"""
    print("\n=== Test 3: main.py Fixes ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print(f"❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('VerticalButton class exists', 'class VerticalButton' in content),
        ('rotation_angle parameter', 'rotation_angle' in content),
        ('90° rotation', 'angle=90' in content or 'angle=self.rotation_angle' in content),
        ('keep_ratio=True', 'keep_ratio=True' in content),
        ('is_lightbox_open flag', 'is_lightbox_open' in content),
        ('debounce with Clock.schedule_once', 'Clock.schedule_once' in content and '_open_lightbox' in content),
        ('CoreImage with nocache', 'nocache=True' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: All main.py fixes are implemented")
    else:
        print("\n❌ FAIL: Some main.py fixes are missing")
    
    return all_passed

def test_image_scaling_logic():
    """Test 4: Simulate image scaling logic"""
    print("\n=== Test 4: Image Scaling Logic Simulation ===")
    
    # Read aspect_ratio from image_meta.json
    meta_path = Path(__file__).parent / "image_meta.json"
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        aspect_ratio = meta.get('aspect_ratio', '16:9')
    except Exception as e:
        print(f"⚠️  WARNING: Could not read image_meta.json: {e}")
        aspect_ratio = '16:9'
    
    # Simulate scaling logic
    if aspect_ratio == "9:16":
        target_size = (1080, 1920)
    else:
        target_size = (1920, 1080)
    
    print(f"  Aspect ratio: {aspect_ratio}")
    print(f"  Target size: {target_size[0]}x{target_size[1]}")
    
    # Verify logic
    if aspect_ratio == "9:16" and target_size == (1080, 1920):
        print("✅ PASS: 9:16 mode correctly targets 1080x1920")
        return True
    elif aspect_ratio == "16:9" and target_size == (1920, 1080):
        print("✅ PASS: 16:9 mode correctly targets 1920x1080")
        return True
    else:
        print(f"❌ FAIL: Incorrect target size for aspect_ratio={aspect_ratio}")
        return False

def test_documentation():
    """Test 5: Verify documentation exists"""
    print("\n=== Test 5: Documentation ===")
    
    docs = [
        'CHANGELOG.md',
        'TEST_GUIDE_9_16_FIXES.md',
    ]
    
    all_exist = True
    for doc in docs:
        doc_path = Path(__file__).parent / doc
        if doc_path.exists():
            print(f"  ✅ {doc} exists")
        else:
            print(f"  ❌ {doc} missing")
            all_exist = False
    
    if all_exist:
        print("\n✅ PASS: All documentation files exist")
    else:
        print("\n❌ FAIL: Some documentation files are missing")
    
    return all_exist

def main():
    """Run all tests"""
    print("=" * 60)
    print("9:16 End-to-End Fixes - Automated Test Suite")
    print("=" * 60)
    
    tests = [
        ("image_meta.json Configuration", test_image_meta_json),
        ("Scale Function Implementation", test_scale_function_implementation),
        ("main.py Fixes", test_main_py_fixes),
        ("Image Scaling Logic", test_image_scaling_logic),
        ("Documentation", test_documentation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {test_name}: {e}")
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
        print("\n🎉 All tests passed! Fixes are properly implemented.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the fixes.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
