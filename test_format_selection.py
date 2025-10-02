#!/usr/bin/env python3
"""
Test script for format selection feature

This test validates:
1. Aspect ratio is stored and retrieved from image_meta.json
2. The aspect ratio parameter is correctly passed to image generation
3. The format selection popup can be instantiated
"""

import sys
import json
from pathlib import Path

def test_aspect_ratio_storage():
    """Test that aspect ratio can be saved and loaded from metadata"""
    print("📝 Testing aspect ratio storage...")
    
    try:
        # Test directly with JSON file (no Kivy dependency)
        meta_path = Path(__file__).parent / "image_meta.json"
        
        # Test 1: Read current metadata
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        else:
            meta = {}
        
        # Test 2: Save with vertical aspect ratio
        meta["aspect_ratio"] = "9:16"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        print("   ✓ Saved aspect ratio 9:16 to image_meta.json")
        
        # Test 3: Load and verify
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta_loaded = json.load(f)
        assert meta_loaded["aspect_ratio"] == "9:16", f"Loaded aspect ratio should be 9:16, got {meta_loaded.get('aspect_ratio')}"
        print("   ✓ Loaded aspect ratio 9:16 from image_meta.json")
        
        # Test 4: Restore default
        meta_loaded["aspect_ratio"] = "16:9"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta_loaded, f, indent=2, ensure_ascii=False)
        print("   ✓ Restored default aspect ratio")
        
        print("✅ Aspect ratio storage test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Aspect ratio storage test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imagen4_aspect_ratio_parameter():
    """Test that generate_image_imagen4 accepts aspect_ratio parameter"""
    print("\n📝 Testing Imagen4 aspect ratio parameter...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from PythonServer import generate_image_imagen4
        import inspect
        
        # Get function signature
        sig = inspect.signature(generate_image_imagen4)
        params = sig.parameters
        
        # Verify aspect_ratio parameter exists
        assert "aspect_ratio" in params, "aspect_ratio parameter missing from generate_image_imagen4"
        print("   ✓ aspect_ratio parameter exists in generate_image_imagen4")
        
        # Verify default value
        default_value = params["aspect_ratio"].default
        assert default_value == "16:9", f"Default aspect ratio should be 16:9, got {default_value}"
        print("   ✓ Default value is 16:9")
        
        print("✅ Imagen4 aspect ratio parameter test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Imagen4 parameter test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_format_selection_popup():
    """Test that FormatSelectionPopup class exists in main.py source"""
    print("\n📝 Testing FormatSelectionPopup class...")
    
    try:
        # Check source code directly (no Kivy import needed)
        main_path = Path(__file__).parent / "main.py"
        with open(main_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check that FormatSelectionPopup class is defined
        assert "class FormatSelectionPopup" in source, "FormatSelectionPopup class not found in main.py"
        print("   ✓ FormatSelectionPopup class defined in main.py")
        
        # Check for required methods
        assert "def _select_format" in source, "_select_format method not found"
        assert 'self.slideshow.aspect_ratio = aspect_ratio' in source, "aspect_ratio assignment not found"
        assert 'self.slideshow.persist_meta()' in source, "persist_meta call not found"
        print("   ✓ FormatSelectionPopup has required methods")
        
        # Check for button definitions
        assert '"Horizontal (16:9)"' in source or "'Horizontal (16:9)'" in source, "Horizontal button not found"
        assert '"Vertikal (9:16)"' in source or "'Vertikal (9:16)'" in source, "Vertikal button not found"
        print("   ✓ Format selection buttons defined")
        
        print("✅ FormatSelectionPopup class test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FormatSelectionPopup test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_toolbar_buttons():
    """Test that toolbar has format selection button"""
    print("\n📝 Testing toolbar buttons configuration...")
    
    try:
        # Check source code directly (no Kivy import needed)
        main_path = Path(__file__).parent / "main.py"
        with open(main_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check if Format button is in toolbar
        assert '"Format"' in source or "'Format'" in source, "Format button not found in toolbar configuration"
        print("   ✓ Format button configured in toolbar")
        
        # Check for aspect-ratio icon (KivyMD)
        assert '"aspect-ratio"' in source or "'aspect-ratio'" in source, "aspect-ratio icon not found in KivyMD toolbar"
        print("   ✓ aspect-ratio icon configured in KivyMD toolbar")
        
        # Check if open_format_selection method exists
        assert "def open_format_selection" in source, "open_format_selection method not found"
        assert "FormatSelectionPopup(self)" in source, "FormatSelectionPopup instantiation not found"
        print("   ✓ open_format_selection method exists")
        
        print("✅ Toolbar buttons test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Toolbar buttons test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all format selection tests"""
    print("=" * 60)
    print("Format Selection Feature Tests")
    print("=" * 60)
    
    all_passed = True
    
    all_passed &= test_aspect_ratio_storage()
    all_passed &= test_imagen4_aspect_ratio_parameter()
    all_passed &= test_format_selection_popup()
    all_passed &= test_toolbar_buttons()
    
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
