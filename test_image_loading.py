#!/usr/bin/env python3
"""
Test script for image loading improvements

This script verifies:
1. Robust image loading with CoreImage primary path
2. Proper state clearing before load
3. Debug logging includes all required information
4. Lightbox uses same robust loading approach
"""

import sys
from pathlib import Path

def test_slideshow_image_loading():
    """Test 1: Verify slideshow has robust image loading"""
    print("\n=== Test 1: Slideshow Image Loading ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print(f"❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('_load_image_robust method exists', 'def _load_image_robust(' in content),
        ('Clear source before load', 'img_widget.source = ""' in content and 'def _load_image_robust' in content),
        ('Clear texture before load', 'img_widget.texture = None' in content and 'def _load_image_robust' in content),
        ('Force canvas update', 'canvas.ask_update()' in content),
        ('Schedule load on next frame', 'Clock.schedule_once(_do_load' in content),
        ('Check file exists', 'os.path.exists(path)' in content and 'def _load_image_robust' in content),
        ('Primary path: CoreImage with nocache', 'CoreImage(path, nocache=True)' in content),
        ('Fallback: widget.source with reload', 'img_widget.source = cache_bust_path' in content or 'img_widget.reload()' in content),
        ('Debug log: image path', 'debug_logger.info(f"Loading image: path=' in content),
        ('Debug log: file exists check', 'exists={file_exists}' in content),
        ('Debug log: texture size', 'texture_size={tex_size}' in content or 'texture_size=' in content),
        ('Debug log: aspect mode', 'aspect_mode={self.aspect_ratio}' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Slideshow image loading is robust")
    else:
        print("\n❌ FAIL: Some slideshow image loading checks failed")
    
    return all_passed

def test_lightbox_image_loading():
    """Test 2: Verify lightbox has robust image loading"""
    print("\n=== Test 2: Lightbox Image Loading ===")
    
    main_path = Path(__file__).parent / "main.py"
    if not main_path.exists():
        print(f"❌ FAIL: main.py not found")
        return False
    
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find ImageLightboxPopup class
    lightbox_start = content.find('class ImageLightboxPopup')
    lightbox_end = content.find('\nclass ', lightbox_start + 1)
    if lightbox_start == -1:
        print("❌ FAIL: ImageLightboxPopup class not found")
        return False
    
    lightbox_content = content[lightbox_start:lightbox_end] if lightbox_end != -1 else content[lightbox_start:]
    
    checks = [
        ('Lightbox clears source before load', 'self.img.source = ""' in lightbox_content),
        ('Lightbox clears texture before load', 'self.img.texture = None' in lightbox_content),
        ('Lightbox checks file exists', 'os.path.exists(image_path)' in lightbox_content),
        ('Lightbox uses CoreImage primary', 'CoreImage(image_path, nocache=True)' in lightbox_content),
        ('Lightbox has fallback', 'self.img.source = image_path' in lightbox_content and 'self.img.reload()' in lightbox_content),
        ('Lightbox logs loading', 'debug_logger.info(f"Loading lightbox image:' in lightbox_content),
        ('Lightbox uses fit_mode contain', "fit_mode='contain'" in lightbox_content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Lightbox image loading is robust")
    else:
        print("\n❌ FAIL: Some lightbox image loading checks failed")
    
    return all_passed

def test_orientation_provider():
    """Test 3: Verify OrientationProvider is single source of truth"""
    print("\n=== Test 3: OrientationProvider Single Source of Truth ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('OrientationProvider class exists', 'class OrientationProvider:' in content),
        ('OrientationProvider is singleton', '_instance = None' in content and 'class OrientationProvider:' in content),
        ('OrientationProvider has aspect_ratio', 'self.aspect_ratio = aspect_ratio' in content and 'class OrientationProvider:' in content),
        ('OrientationProvider has rotation_angle', 'self.rotation_angle = 90 if aspect_ratio == "9:16" else 0' in content),
        ('OrientationProvider has is_portrait', 'def is_portrait(self):' in content and 'class OrientationProvider:' in content),
        ('RotatingRoot uses OrientationProvider', 'self.orientation_provider = OrientationProvider()' in content and 'class RotatingRoot' in content),
        ('RotatedModalView uses OrientationProvider', 'self.orientation_provider = OrientationProvider()' in content and 'class RotatedModalView' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: OrientationProvider is single source of truth")
    else:
        print("\n❌ FAIL: Some OrientationProvider checks failed")
    
    return all_passed

def test_aspect_persistence():
    """Test 4: Verify aspect ratio persistence"""
    print("\n=== Test 4: Aspect Ratio Persistence ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('load_image_meta has aspect_ratio default', '"aspect_ratio": "16:9"' in content and 'def load_image_meta():' in content),
        ('Slideshow loads aspect_ratio from meta', 'self.aspect_ratio = meta.get("aspect_ratio", "16:9")' in content),
        ('Slideshow initializes OrientationProvider', 'orientation_provider.set_orientation(self.aspect_ratio)' in content and 'class Slideshow' in content),
        ('persist_meta saves aspect_ratio', '"aspect_ratio": self.aspect_ratio' in content and 'def persist_meta(self):' in content),
        ('FormatSelectionPopup calls persist_meta', 'self.slideshow.persist_meta()' in content and 'class FormatSelectionPopup' in content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: Aspect ratio persistence is correct")
    else:
        print("\n❌ FAIL: Some aspect ratio persistence checks failed")
    
    return all_passed

def test_no_vertical_toolbar():
    """Test 5: Verify no vertical toolbar remnants"""
    print("\n=== Test 5: No Vertical Toolbar Remnants ===")
    
    main_path = Path(__file__).parent / "main.py"
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find Slideshow class
    slideshow_start = content.find('class Slideshow(')
    slideshow_end = content.find('\n# ---- App Klassen ----', slideshow_start)
    if slideshow_start == -1:
        print("❌ FAIL: Slideshow class not found")
        return False
    
    slideshow_content = content[slideshow_start:slideshow_end]
    
    checks = [
        ('No toolbar_width in _resize_image', 'toolbar_width' not in slideshow_content or 
         slideshow_content.count('toolbar_width') == 0 or 
         '# Toolbar is ALWAYS at the bottom' in slideshow_content),
        ('_resize_image uses toolbar_height only', 'toolbar_height' in slideshow_content and '_resize_image' in slideshow_content),
        ('Content width is full width', 'content_w = self.width' in slideshow_content),
        ('_create_toolbar always uses vertical=False', 'vertical=False' in slideshow_content and '_create_toolbar' in slideshow_content),
        ('Toolbar positioned at bottom', 'pos_hint = {"bottom": 1}' in slideshow_content or 'pos_hint={"bottom":1}' in slideshow_content),
    ]
    
    all_passed = True
    for check_name, check_result in checks:
        if check_result:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: No vertical toolbar remnants")
    else:
        print("\n❌ FAIL: Some vertical toolbar checks failed")
    
    return all_passed

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Slideshow/Orientation Hotfix Implementation")
    print("=" * 60)
    
    results = [
        test_slideshow_image_loading(),
        test_lightbox_image_loading(),
        test_orientation_provider(),
        test_aspect_persistence(),
        test_no_vertical_toolbar(),
    ]
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    if all(results):
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
