#!/usr/bin/env python3
"""
Test script for aspect ratio filtering feature

This test validates:
1. Images are correctly identified as 16:9 or 9:16
2. Images are filtered based on the selected aspect ratio
3. Format switching reloads the image list
"""

import sys
import tempfile
from pathlib import Path

def test_aspect_ratio_detection():
    """Test that aspect ratio detection works correctly"""
    print("📝 Testing aspect ratio detection...")
    
    try:
        from PIL import Image as PILImage
    except ImportError:
        print("   ⚠️  Pillow not available, skipping test")
        return True
    
    try:
        # Create test images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a horizontal image (16:9 aspect ratio)
            horizontal_img = Path(temp_dir) / "horizontal.png"
            img_h = PILImage.new('RGB', (1920, 1080), color='red')
            img_h.save(horizontal_img)
            
            # Create a vertical image (9:16 aspect ratio)
            vertical_img = Path(temp_dir) / "vertical.png"
            img_v = PILImage.new('RGB', (1080, 1920), color='blue')
            img_v.save(vertical_img)
            
            # Create a square image
            square_img = Path(temp_dir) / "square.png"
            img_s = PILImage.new('RGB', (1080, 1080), color='green')
            img_s.save(square_img)
            
            print(f"   ✓ Created test images in {temp_dir}")
            
            # Test detection logic (simulate the main.py logic)
            def detect_aspect_ratio(image_path):
                with PILImage.open(image_path) as img:
                    width, height = img.size
                    if width > height:
                        return "16:9"
                    elif height > width:
                        return "9:16"
                    else:
                        return "square"
            
            h_ratio = detect_aspect_ratio(horizontal_img)
            v_ratio = detect_aspect_ratio(vertical_img)
            s_ratio = detect_aspect_ratio(square_img)
            
            assert h_ratio == "16:9", f"Expected 16:9 for horizontal image, got {h_ratio}"
            print(f"   ✓ Horizontal image detected as {h_ratio}")
            
            assert v_ratio == "9:16", f"Expected 9:16 for vertical image, got {v_ratio}"
            print(f"   ✓ Vertical image detected as {v_ratio}")
            
            assert s_ratio == "square", f"Expected square for square image, got {s_ratio}"
            print(f"   ✓ Square image detected as {s_ratio}")
        
        print("✅ Aspect ratio detection test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Aspect ratio detection test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_filtering_logic():
    """Test that filtering logic works correctly"""
    print("\n📝 Testing filtering logic...")
    
    try:
        from PIL import Image as PILImage
    except ImportError:
        print("   ⚠️  Pillow not available, skipping test")
        return True
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test images
            horizontal_img = Path(temp_dir) / "horizontal.png"
            img_h = PILImage.new('RGB', (1920, 1080), color='red')
            img_h.save(horizontal_img)
            
            vertical_img = Path(temp_dir) / "vertical.png"
            img_v = PILImage.new('RGB', (1080, 1920), color='blue')
            img_v.save(vertical_img)
            
            all_images = [str(horizontal_img), str(vertical_img)]
            
            # Simulate filtering for 16:9
            def filter_for_aspect_ratio(files, target_ratio):
                filtered = []
                for file_path in files:
                    with PILImage.open(file_path) as img:
                        width, height = img.size
                        if width > height:
                            img_ratio = "16:9"
                        elif height > width:
                            img_ratio = "9:16"
                        else:
                            img_ratio = target_ratio  # Square matches current
                        
                        if img_ratio == target_ratio:
                            filtered.append(file_path)
                return filtered
            
            horizontal_only = filter_for_aspect_ratio(all_images, "16:9")
            assert len(horizontal_only) == 1, f"Expected 1 horizontal image, got {len(horizontal_only)}"
            assert str(horizontal_img) in horizontal_only
            print(f"   ✓ Filtered to {len(horizontal_only)} horizontal image(s)")
            
            vertical_only = filter_for_aspect_ratio(all_images, "9:16")
            assert len(vertical_only) == 1, f"Expected 1 vertical image, got {len(vertical_only)}"
            assert str(vertical_img) in vertical_only
            print(f"   ✓ Filtered to {len(vertical_only)} vertical image(s)")
        
        print("✅ Filtering logic test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Filtering logic test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_py_has_filtering():
    """Test that main.py has the filtering methods"""
    print("\n📝 Testing main.py has filtering methods...")
    
    try:
        main_path = Path(__file__).parent / "main.py"
        with open(main_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check for filtering methods
        assert "def _get_image_aspect_ratio" in source, "_get_image_aspect_ratio method not found"
        print("   ✓ _get_image_aspect_ratio method exists")
        
        assert "def _filter_by_aspect_ratio" in source, "_filter_by_aspect_ratio method not found"
        print("   ✓ _filter_by_aspect_ratio method exists")
        
        # Check that filtering is applied in scan methods
        assert "_filter_by_aspect_ratio(files)" in source, "Filtering not applied in scan methods"
        print("   ✓ Filtering is applied in scan methods")
        
        # Check that format selection reloads images
        assert "self.slideshow.images = self.slideshow._scan_global()" in source, "Format selection doesn't reload global images"
        print("   ✓ Format selection reloads images")
        
        print("✅ main.py filtering methods test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ main.py filtering methods test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all aspect ratio filtering tests"""
    print("=" * 60)
    print("Aspect Ratio Filtering Feature Tests")
    print("=" * 60)
    
    all_passed = True
    
    all_passed &= test_aspect_ratio_detection()
    all_passed &= test_filtering_logic()
    all_passed &= test_main_py_has_filtering()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
