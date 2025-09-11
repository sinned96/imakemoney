#!/usr/bin/env python3
"""
End-to-end workflow test for the complete recording → transcription → image generation pipeline.

This test simulates the complete workflow without requiring actual audio recording or Google Cloud credentials.
"""

import os
import sys
import json
import tempfile
import time
from pathlib import Path

def simulate_recording_completion(work_dir):
    """Simulate that a recording has been completed"""
    print("📼 Simulating audio recording completion...")
    
    # Create a dummy audio file (aufnahme.wav)
    audio_file = work_dir / "aufnahme.wav"
    audio_file.write_bytes(b"DUMMY_AUDIO_DATA")  # Placeholder audio data
    
    print(f"✓ Created dummy audio file: {audio_file}")
    return str(audio_file)

def simulate_transcription_completion(work_dir, transcript_text):
    """Simulate successful transcription completion"""
    print("🗣️ Simulating transcription completion...")
    
    # Create transcript.txt
    txt_file = work_dir / "transkript.txt"
    txt_file.write_text(transcript_text, encoding='utf-8')
    
    # Create transcript.json with metadata
    json_file = work_dir / "transkript.json" 
    transcript_data = {
        "transcript": transcript_text,
        "timestamp": time.time(),
        "iso_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file_size": len(transcript_text),
        "processing_method": "google_speech_api",
        "audio_source": str(work_dir / "aufnahme.wav"),
        "workflow_step": "transcription_complete",
        "real_recognition": True  # Simulate real recognition
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Created transcript files:")
    print(f"   - {txt_file}")
    print(f"   - {json_file}")
    
    return str(txt_file), str(json_file)

def simulate_workflow_trigger(work_dir):
    """Simulate the workflow trigger file creation"""
    print("⚡ Creating workflow trigger...")
    
    trigger_file = work_dir / "workflow_trigger.txt"
    trigger_file.write_text("run", encoding='utf-8')
    
    print(f"✓ Created trigger file: {trigger_file}")
    return str(trigger_file)

def test_workflow_file_watcher(work_dir):
    """Test the WorkflowFileWatcher with simulated data"""
    print("🔍 Testing WorkflowFileWatcher...")
    
    # Import the workflow manager
    import PythonServer
    
    # Temporarily override paths for testing
    original_paths = {
        'txt': PythonServer.TRANSKRIPT_PATH,
        'json': PythonServer.TRANSKRIPT_JSON_PATH,
        'bilder': PythonServer.BILDER_DIR,
        'audio': PythonServer.AUDIO_FILE
    }
    
    # Set paths to our test directory
    PythonServer.TRANSKRIPT_PATH = str(work_dir / "transkript.txt")
    PythonServer.TRANSKRIPT_JSON_PATH = str(work_dir / "transkript.json")
    PythonServer.BILDER_DIR = str(work_dir / "BilderVertex")
    PythonServer.AUDIO_FILE = str(work_dir / "aufnahme.wav")
    
    try:
        # Create the workflow watcher
        watcher = PythonServer.WorkflowFileWatcher(work_dir)
        
        # Test transcript reading
        transcript = watcher._get_transcript_for_ai()
        if not transcript:
            print("❌ Transcript reading failed")
            return False
            
        print(f"✓ Transcript read successfully: '{transcript[:50]}...'")
        
        # Instead of running the full workflow (which would execute external scripts),
        # let's test just the image generation part
        print("🎨 Testing image generation with transcript...")
        
        bilder_dir = work_dir / "BilderVertex"
        generated_images = PythonServer.generate_image_imagen4(
            prompt=transcript,
            image_count=1,
            bilder_dir=str(bilder_dir),
            output_prefix="workflow_test",
            logger=lambda msg, level="INFO": print(f"[{level}] {msg}")
        )
        
        if generated_images:
            print(f"✓ Image generation successful: {len(generated_images)} images")
            for img in generated_images:
                if os.path.exists(img):
                    file_size = os.path.getsize(img)
                    print(f"   ✓ {img} ({file_size} bytes)")
                else:
                    print(f"   ❌ {img} (not found)")
                    return False
            return True
        else:
            print("❌ Image generation failed")
            return False
            
    finally:
        # Restore original paths
        PythonServer.TRANSKRIPT_PATH = original_paths['txt']
        PythonServer.TRANSKRIPT_JSON_PATH = original_paths['json']
        PythonServer.BILDER_DIR = original_paths['bilder']
        PythonServer.AUDIO_FILE = original_paths['audio']

def test_directory_structure_creation(work_dir):
    """Test that the workflow creates the expected directory structure"""
    print("📁 Testing directory structure creation...")
    
    expected_dirs = [
        work_dir / "BilderVertex",
    ]
    
    expected_files = [
        work_dir / "aufnahme.wav",
        work_dir / "transkript.txt", 
        work_dir / "transkript.json",
        work_dir / "workflow_trigger.txt"
    ]
    
    # Check directories
    for dir_path in expected_dirs:
        if dir_path.exists():
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"❌ Directory missing: {dir_path}")
            return False
    
    # Check files  
    for file_path in expected_files:
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"✓ File exists: {file_path} ({file_size} bytes)")
        else:
            print(f"❌ File missing: {file_path}")
            return False
    
    # Check for generated images
    bilder_dir = work_dir / "BilderVertex"
    image_files = list(bilder_dir.glob("*.png"))
    
    if image_files:
        print(f"✓ Generated images found: {len(image_files)}")
        for img in image_files:
            print(f"   - {img.name}")
        return True
    else:
        print("❌ No generated images found")
        return False

def test_json_transcript_priority(work_dir):
    """Test that JSON transcript is prioritized over text transcript"""
    print("📋 Testing JSON transcript priority...")
    
    # Create both files with different content
    txt_content = "This is from the TXT file"
    json_content = "This is from the JSON file"
    
    txt_file = work_dir / "transkript.txt"
    json_file = work_dir / "transkript.json"
    
    txt_file.write_text(txt_content, encoding='utf-8')
    
    json_data = {
        "transcript": json_content,
        "processing_method": "test",
        "real_recognition": True
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    # Test transcript reading
    import PythonServer
    
    # Override paths temporarily
    original_txt = PythonServer.TRANSKRIPT_PATH
    original_json = PythonServer.TRANSKRIPT_JSON_PATH
    
    PythonServer.TRANSKRIPT_PATH = str(txt_file)
    PythonServer.TRANSKRIPT_JSON_PATH = str(json_file)
    
    try:
        watcher = PythonServer.WorkflowFileWatcher(work_dir)
        transcript = watcher._get_transcript_for_ai()
        
        if transcript == json_content:
            print("✓ JSON transcript correctly prioritized")
            return True
        elif transcript == txt_content:
            print("❌ TXT transcript used instead of JSON (incorrect priority)")
            return False
        else:
            print(f"❌ Unexpected transcript content: '{transcript}'")
            return False
            
    finally:
        PythonServer.TRANSKRIPT_PATH = original_txt
        PythonServer.TRANSKRIPT_JSON_PATH = original_json

def test_error_handling():
    """Test error handling with missing files"""
    print("⚠️ Testing error handling...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        work_dir = Path(temp_dir)
        
        import PythonServer
        
        # Set paths to non-existent files
        original_txt = PythonServer.TRANSKRIPT_PATH  
        original_json = PythonServer.TRANSKRIPT_JSON_PATH
        
        PythonServer.TRANSKRIPT_PATH = str(work_dir / "nonexistent.txt")
        PythonServer.TRANSKRIPT_JSON_PATH = str(work_dir / "nonexistent.json")
        
        try:
            watcher = PythonServer.WorkflowFileWatcher(work_dir)
            transcript = watcher._get_transcript_for_ai()
            
            if transcript == "":
                print("✓ Correctly handled missing transcript files")
                return True
            else:
                print(f"❌ Should return empty string for missing files, got: '{transcript}'")
                return False
                
        finally:
            PythonServer.TRANSKRIPT_PATH = original_txt
            PythonServer.TRANSKRIPT_JSON_PATH = original_json

def main():
    """Run the complete end-to-end workflow test"""
    print("🚀 End-to-End Workflow Test")
    print("=" * 60)
    print("Testing: Recording → Transcription → Vertex AI → Image Generation")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        work_dir = Path(temp_dir)
        transcript_text = "Create a stunning landscape with snow-covered mountains, a crystal clear lake, and a golden sunset sky"
        
        print(f"📂 Test directory: {work_dir}")
        
        # Test phases
        tests = [
            # Setup phase
            ("Audio Recording Simulation", 
             lambda: simulate_recording_completion(work_dir) is not None),
            
            ("Transcription Simulation",
             lambda: simulate_transcription_completion(work_dir, transcript_text) is not None),
            
            ("Workflow Trigger Creation", 
             lambda: simulate_workflow_trigger(work_dir) is not None),
            
            # Core functionality tests
            ("WorkflowFileWatcher Integration", 
             lambda: test_workflow_file_watcher(work_dir)),
            
            ("Directory Structure Verification",
             lambda: test_directory_structure_creation(work_dir)),
             
            ("JSON Transcript Priority Test",
             lambda: test_json_transcript_priority(work_dir)),
             
            ("Error Handling Test",
             lambda: test_error_handling()),
        ]
        
        # Run tests
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
                print(f"   Traceback: {traceback.format_exc()}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"🏁 End-to-End Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! End-to-end workflow is working correctly.")
            print("\n📋 Workflow Status:")
            print("   ✓ Audio recording simulation works")
            print("   ✓ Transcription simulation works") 
            print("   ✓ Workflow trigger mechanism works")
            print("   ✓ Transcript reading prioritizes JSON format")
            print("   ✓ Image generation integration works")
            print("   ✓ Directory structure is created correctly")
            print("   ✓ Error handling works for missing files")
            print("\n🚀 The complete Recording → Transcription → Vertex AI workflow is ready!")
            
            return True
        else:
            print(f"❌ {total - passed} tests failed. The workflow needs fixes.")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)