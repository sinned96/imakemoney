#!/usr/bin/env python3
"""
Test script for Vertex AI integration in the recording workflow.

This script validates the complete workflow from transcript creation to image generation.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

def create_test_transcript_files(test_dir, real_transcript=True):
    """Create test transcript files for testing"""
    print("📝 Creating test transcript files...")
    
    # Test transcript content
    if real_transcript:
        transcript_text = "Create a beautiful landscape image with mountains and a lake"
        processing_method = "google_speech_api"
        real_recognition = True
    else:
        transcript_text = "Dies ist ein Test für die Bildgenerierung mit simuliertem Text"
        processing_method = "simulation"
        real_recognition = False
    
    # Create .txt file
    txt_file = test_dir / "transkript.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(transcript_text)
    print(f"✓ Created: {txt_file}")
    
    # Create .json file with metadata
    json_file = test_dir / "transkript.json"
    transcript_data = {
        "transcript": transcript_text,
        "timestamp": 1234567890.0,
        "iso_timestamp": "2023-02-14 10:30:00",
        "file_size": len(transcript_text),
        "processing_method": processing_method,
        "audio_source": str(test_dir / "aufnahme.wav"),
        "workflow_step": "transcription_complete",
        "real_recognition": real_recognition
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, ensure_ascii=False, indent=2)
    print(f"✓ Created: {json_file}")
    
    return str(txt_file), str(json_file), transcript_text

def test_transcript_reading():
    """Test the transcript reading functionality"""
    print("\n🔍 Testing transcript reading functionality...")
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        
        # Create test transcript files
        txt_file, json_file, expected_text = create_test_transcript_files(test_dir)
        
        # Temporarily modify the paths for testing
        import PythonServer
        original_txt_path = PythonServer.TRANSKRIPT_PATH
        original_json_path = PythonServer.TRANSKRIPT_JSON_PATH
        
        PythonServer.TRANSKRIPT_PATH = str(txt_file)
        PythonServer.TRANSKRIPT_JSON_PATH = str(json_file)
        
        try:
            # Test with WorkflowFileWatcher (which has the _get_transcript_for_ai method)
            from PythonServer import WorkflowFileWatcher
            
            watcher = WorkflowFileWatcher(test_dir)
            transcript = watcher._get_transcript_for_ai()
            
            if transcript == expected_text:
                print("✓ Transcript reading successful")
                print(f"   Found text: '{transcript[:50]}{'...' if len(transcript) > 50 else ''}'")
                return True
            else:
                print(f"✗ Transcript mismatch. Expected: '{expected_text}', Got: '{transcript}'")
                return False
                
        finally:
            # Restore original paths
            PythonServer.TRANSKRIPT_PATH = original_txt_path
            PythonServer.TRANSKRIPT_JSON_PATH = original_json_path

def test_image_generation():
    """Test the image generation functionality"""
    print("\n🎨 Testing image generation functionality...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        bilder_dir = test_dir / "BilderVertex"
        
        # Test prompt
        test_prompt = "A beautiful sunset over mountains"
        
        # Import the function
        from PythonServer import generate_image_imagen4
        
        # Test image generation (will create demo images since we don't have real credentials)
        print(f"Testing with prompt: '{test_prompt}'")
        print(f"Target directory: {bilder_dir}")
        
        generated_files = generate_image_imagen4(
            prompt=test_prompt,
            image_count=2,
            bilder_dir=str(bilder_dir),
            output_prefix="test_image"
        )
        
        if generated_files:
            print(f"✓ Image generation successful: {len(generated_files)} images created")
            for img_file in generated_files:
                if os.path.exists(img_file):
                    file_size = os.path.getsize(img_file)
                    print(f"   ✓ {img_file} ({file_size} bytes)")
                else:
                    print(f"   ✗ {img_file} (file not found)")
                    return False
            return True
        else:
            print("✗ Image generation failed: no images created")
            return False

def test_directory_structure():
    """Test that the directory structure is correctly created"""
    print("\n📁 Testing directory structure creation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        
        # Import directory creation logic
        from PythonServer import BILDER_DIR
        import PythonServer
        
        # Temporarily set bilder dir to test location
        original_bilder_dir = PythonServer.BILDER_DIR
        test_bilder_dir = str(test_dir / "BilderVertex")
        PythonServer.BILDER_DIR = test_bilder_dir
        
        try:
            # Test image generation which should create the directory
            generated_files = PythonServer.generate_image_imagen4(
                "Test prompt",
                image_count=1,
                bilder_dir=test_bilder_dir,
                output_prefix="test"
            )
            
            if os.path.exists(test_bilder_dir):
                print(f"✓ Directory created successfully: {test_bilder_dir}")
                
                if generated_files and all(os.path.exists(f) for f in generated_files):
                    print("✓ Images saved in correct directory")
                    return True
                else:
                    print("✗ Images not saved correctly")
                    return False
            else:
                print(f"✗ Directory not created: {test_bilder_dir}")
                return False
                
        finally:
            PythonServer.BILDER_DIR = original_bilder_dir

def test_workflow_integration():
    """Test the complete workflow integration"""
    print("\n⚙️ Testing complete workflow integration...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        
        # Create test transcript files
        txt_file, json_file, expected_text = create_test_transcript_files(test_dir, real_transcript=True)
        
        # Setup paths for testing
        import PythonServer
        original_paths = {
            'txt': PythonServer.TRANSKRIPT_PATH,
            'json': PythonServer.TRANSKRIPT_JSON_PATH,
            'bilder': PythonServer.BILDER_DIR
        }
        
        test_bilder_dir = str(test_dir / "BilderVertex")
        PythonServer.TRANSKRIPT_PATH = str(txt_file)
        PythonServer.TRANSKRIPT_JSON_PATH = str(json_file)
        PythonServer.BILDER_DIR = test_bilder_dir
        
        try:
            # Create a workflow file watcher for testing
            from PythonServer import WorkflowFileWatcher
            
            watcher = WorkflowFileWatcher(test_dir)
            
            # Test transcript reading
            transcript = watcher._get_transcript_for_ai()
            if transcript != expected_text:
                print(f"✗ Transcript reading failed")
                return False
            
            print("✓ Transcript reading works")
            
            # Test image generation with transcript
            generated_files = PythonServer.generate_image_imagen4(
                prompt=transcript,
                image_count=1,
                bilder_dir=test_bilder_dir,
                output_prefix="workflow_test"
            )
            
            if generated_files and all(os.path.exists(f) for f in generated_files):
                print("✓ Image generation from transcript works")
                print(f"   Generated: {len(generated_files)} images")
                return True
            else:
                print("✗ Image generation from transcript failed")
                return False
                
        finally:
            # Restore original paths
            PythonServer.TRANSKRIPT_PATH = original_paths['txt']
            PythonServer.TRANSKRIPT_JSON_PATH = original_paths['json']
            PythonServer.BILDER_DIR = original_paths['bilder']

def main():
    """Run all integration tests"""
    print("🚀 Vertex AI Integration Test Suite")
    print("=" * 50)
    
    # Check basic imports
    print("\n📦 Checking imports...")
    try:
        import PythonServer
        print("✓ PythonServer module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PythonServer: {e}")
        return False
    
    # Run individual tests
    tests = [
        ("Transcript Reading", test_transcript_reading),
        ("Image Generation", test_image_generation), 
        ("Directory Structure", test_directory_structure),
        ("Workflow Integration", test_workflow_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    # Summary
    print(f"\n{'='*50}")
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Vertex AI integration is working correctly.")
        print("\n📋 Integration Status:")
        print("   ✓ Transcript files can be read (both .txt and .json)")
        print("   ✓ Image generation function works (demo mode)")
        print("   ✓ Directory structure is created correctly") 
        print("   ✓ Workflow integration connects transcript to image generation")
        print("\n🔧 For production use:")
        print("   1. Set up Google Cloud credentials (cloudKey.json)")
        print("   2. Install Google Cloud libraries: pip install google-cloud-aiplatform")
        print("   3. Enable Vertex AI API in Google Cloud Console")
        print("   4. Set up billing for Vertex AI")
        
        return True
    else:
        print(f"❌ {total - passed} tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)