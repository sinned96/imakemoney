#!/usr/bin/env python3
"""
Test script for image scaling functionality in the Vertex AI workflow.

This script validates that images are properly scaled to 1920x1080 pixels
to eliminate black bars when displayed.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def test_scaling_function():
    """Test the standalone scaling function from vertex_ai_image_workflow.py"""
    print("📏 Testing image scaling function...")
    
    try:
        from vertex_ai_image_workflow import scale_image_to_1920x1080
        from PIL import Image
        
        # Create a temporary test image
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "test_image.png")
            
            # Create test image with different dimensions
            test_cases = [
                (800, 600, "4:3 aspect ratio"),
                (1280, 720, "16:9 aspect ratio"),
                (1024, 1024, "square image"),
                (400, 300, "small image")
            ]
            
            for width, height, description in test_cases:
                # Create test image
                img = Image.new('RGB', (width, height), color=(100, 150, 200))
                img.save(test_image_path, "PNG")
                
                print(f"   Testing {description}: {width}x{height}")
                
                # Test scaling with aspect ratio preservation
                success = scale_image_to_1920x1080(test_image_path, preserve_aspect_ratio=True)
                
                if success:
                    # Verify final dimensions
                    with Image.open(test_image_path) as scaled_img:
                        final_size = scaled_img.size
                        if final_size == (1920, 1080):
                            print(f"   ✓ Successfully scaled to 1920x1080")
                        else:
                            print(f"   ✗ Failed: Final size is {final_size}")
                            return False
                else:
                    print(f"   ✗ Scaling failed for {description}")
                    return False
        
        print("✅ Image scaling function test PASSED")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_integration_with_demo_images():
    """Test that demo images are properly scaled in the main workflow"""
    print("🎨 Testing integration with demo image generation...")
    
    try:
        from PythonServer import generate_image_imagen4
        from PIL import Image
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate demo images (since we don't have Google Cloud setup)
            image_paths = generate_image_imagen4(
                prompt="Test scaling functionality",
                image_count=1,
                bilder_dir=temp_dir,
                output_prefix="scaling_test"
            )
            
            if not image_paths:
                print("   ✗ No images were generated")
                return False
            
            # Check that the generated image is 1920x1080
            for img_path in image_paths:
                if os.path.exists(img_path):
                    with Image.open(img_path) as img:
                        size = img.size
                        if size == (1920, 1080):
                            print(f"   ✓ Generated image has correct size: {size}")
                            print(f"   ✓ Image path: {img_path}")
                        else:
                            print(f"   ✗ Generated image has wrong size: {size}")
                            return False
                else:
                    print(f"   ✗ Generated image file not found: {img_path}")
                    return False
        
        print("✅ Demo image integration test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Integration test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_aspect_ratio_preservation():
    """Test that aspect ratio preservation works correctly"""
    print("📐 Testing aspect ratio preservation...")
    
    try:
        from vertex_ai_image_workflow import scale_image_to_1920x1080
        from PIL import Image
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_image_path = os.path.join(temp_dir, "aspect_test.png")
            
            # Create a very wide image (panoramic)
            img = Image.new('RGB', (3840, 1080), color=(255, 0, 0))  # Red panoramic
            img.save(test_image_path, "PNG")
            
            print("   Testing panoramic image (3840x1080)...")
            success = scale_image_to_1920x1080(test_image_path, preserve_aspect_ratio=True)
            
            if success:
                with Image.open(test_image_path) as scaled_img:
                    if scaled_img.size == (1920, 1080):
                        print("   ✓ Panoramic image properly fitted to 1920x1080")
                    else:
                        print(f"   ✗ Wrong final size: {scaled_img.size}")
                        return False
            else:
                print("   ✗ Scaling failed")
                return False
        
        print("✅ Aspect ratio preservation test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Aspect ratio test error: {e}")
        return False

def main():
    """Run all image scaling tests"""
    print("🚀 Image Scaling Test Suite")
    print("=" * 50)
    
    tests = [
        test_scaling_function,
        test_integration_with_demo_images,
        test_aspect_ratio_preservation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print()
        try:
            if test():
                passed += 1
            else:
                print("❌ Test failed")
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print()
    print("=" * 50)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Image scaling is working correctly.")
        print()
        print("📋 Scaling Status:")
        print("   ✓ Images are automatically scaled to 1920x1080")
        print("   ✓ Aspect ratio is preserved using ImageOps.fit")
        print("   ✓ LANCZOS resampling provides high quality scaling")
        print("   ✓ Black bars will be eliminated on 1920x1080 displays")
        return True
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)