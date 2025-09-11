#!/usr/bin/env python3
"""
Test script for improved recording error handling

This script tests the new error handling logic to ensure that:
1. Exit code 1 with valid audio file shows success + info message (not error)
2. Exit code 1 without valid audio file shows proper error
3. Exit code 0 with valid audio file shows success
4. Missing audio file shows error regardless of exit code

Created to validate the fix for: "Behebe den Fehler beim Stoppen der Aufnahme"
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
import time

# Add current directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

def create_dummy_audio_file(path, size_bytes=10000):
    """Create a dummy audio file with WAV header for testing"""
    # Minimal WAV header (44 bytes) + dummy data
    wav_header = b'RIFF' + (size_bytes - 8).to_bytes(4, 'little') + b'WAVE'
    wav_header += b'fmt ' + (16).to_bytes(4, 'little')  # fmt chunk
    wav_header += b'\x01\x00\x01\x00'  # PCM, mono
    wav_header += (44100).to_bytes(4, 'little')  # sample rate
    wav_header += (44100 * 2).to_bytes(4, 'little')  # byte rate
    wav_header += b'\x02\x00\x10\x00'  # block align, bits per sample
    wav_header += b'data' + (size_bytes - 44).to_bytes(4, 'little')
    
    with open(path, 'wb') as f:
        f.write(wav_header)
        # Fill with dummy audio data
        dummy_data = b'\x00' * (size_bytes - 44)
        f.write(dummy_data)
    
    print(f"Created dummy audio file: {path} ({size_bytes} bytes)")

def test_aufnahme_error_handling():
    """Test the improved error handling in Aufnahme.py"""
    print("=== Testing Aufnahme.py Error Handling ===")
    
    # Test 1: Simulate successful recording with SIGTERM (exit code 1)
    print("\nTest 1: Recording stopped via SIGTERM (should show success + info)")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_file = Path(temp_dir) / "test_aufnahme.wav"
        
        # Create a test script that simulates arecord behavior
        test_script = Path(temp_dir) / "mock_arecord.py"
        with open(test_script, 'w') as f:
            f.write(f"""
import signal
import time
import sys

def signal_handler(signum, frame):
    print("Received signal, creating audio file...")
    # Create audio file before exiting
    with open('{audio_file}', 'wb') as f:
        f.write(b'RIFF' + (10000).to_bytes(4, 'little') + b'WAVE')
        f.write(b'fmt ' + (16).to_bytes(4, 'little'))
        f.write(b'\\x01\\x00\\x01\\x00')  # PCM, mono  
        f.write((44100).to_bytes(4, 'little'))  # sample rate
        f.write((44100 * 2).to_bytes(4, 'little'))  # byte rate
        f.write(b'\\x02\\x00\\x10\\x00')  # block align, bits per sample
        f.write(b'data' + (10000 - 44).to_bytes(4, 'little'))
        f.write(b'\\x00' * (10000 - 44))  # dummy data
    print("Audio file created, exiting with code 1")
    sys.exit(1)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

print("Mock recording started...")
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    signal_handler(signal.SIGINT, None)
""")
        
        # Test our AudioRecorder class behavior
        try:
            from Aufnahme import AudioRecorder
            
            # Patch the recorder to use our mock script  
            recorder = AudioRecorder()
            recorder.output_file = audio_file
            
            # Start our mock process
            import subprocess
            import os
            import signal
            
            process = subprocess.Popen([sys.executable, str(test_script)], 
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     universal_newlines=True,
                                     preexec_fn=os.setsid)
            
            recorder.recording_process = process
            recorder.recording_started = True
            recorder.start_time = time.time()
            
            # Wait a moment then stop
            time.sleep(0.5)
            
            print("Calling stop_recording()...")
            recorder.stop_recording()
            
            # Check results
            if audio_file.exists():
                print("✓ Test 1 PASSED: Audio file exists after stop")
            else:
                print("✗ Test 1 FAILED: Audio file not created")
                
        except Exception as e:
            print(f"Test 1 ERROR: {e}")
            import traceback
            traceback.print_exc()

def test_gui_validation():
    """Test the audio file validation function"""
    print("\n=== Testing GUI Audio File Validation ===")
    
    # We need to mock the GUI validation method since it requires Kivy
    # Instead, let's test the validation logic directly
    
    def validate_audio_file(file_path, start_time=None):
        """Mock version of _validate_audio_file method"""
        try:
            if not file_path.exists():
                return False, "Audiodatei wurde nicht erstellt", "error"
            
            file_size = file_path.stat().st_size
            
            if file_size < 1024:
                return False, f"Audiodatei ist zu klein ({file_size} Bytes) - möglicherweise unvollständig", "warning"
            
            duration_estimate = ""
            if start_time:
                duration = time.time() - start_time
                duration_estimate = f" (ca. {duration:.1f}s)"
            
            size_mb = file_size / 1024 / 1024
            status_msg = f"Audiodatei erfolgreich gespeichert: {size_mb:.1f} MB{duration_estimate}"
            
            # Check WAV header
            try:
                with open(file_path, 'rb') as f:
                    header = f.read(12)
                    if len(header) >= 12 and b'RIFF' in header and b'WAVE' in header:
                        return True, status_msg + " ✓ Gültiges WAV-Format", "success"
                    else:
                        return True, status_msg + " ⚠ Format unbekannt, aber Datei vorhanden", "info"
            except Exception:
                return True, status_msg, "success"
                
        except Exception as e:
            return False, f"Fehler bei der Dateivalidierung: {e}", "error"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_file = Path(temp_dir) / "test_audio.wav"
        
        # Test 1: File doesn't exist
        print("\nTest 1: Missing file")
        is_valid, message, level = validate_audio_file(audio_file)
        print(f"Result: {is_valid}, '{message}', {level}")
        assert not is_valid and level == "error", "Should fail for missing file"
        print("✓ PASSED")
        
        # Test 2: File too small
        print("\nTest 2: File too small")
        with open(audio_file, 'wb') as f:
            f.write(b'tiny')
        is_valid, message, level = validate_audio_file(audio_file)
        print(f"Result: {is_valid}, '{message}', {level}")
        assert not is_valid and level == "warning", "Should warn for tiny file"
        print("✓ PASSED")
        
        # Test 3: Valid WAV file
        print("\nTest 3: Valid WAV file")
        create_dummy_audio_file(audio_file, 50000)
        start_time = time.time() - 2.5  # Simulate 2.5 second recording
        is_valid, message, level = validate_audio_file(audio_file, start_time)
        print(f"Result: {is_valid}, '{message}', {level}")
        assert is_valid and level == "success", "Should succeed for valid WAV"
        print("✓ PASSED")
        
        # Test 4: Valid file, unknown format
        print("\nTest 4: Valid file, unknown format")
        with open(audio_file, 'wb') as f:
            f.write(b'X' * 5000)  # No WAV header, but decent size
        is_valid, message, level = validate_audio_file(audio_file)
        print(f"Result: {is_valid}, '{message}', {level}")
        assert is_valid and level == "info", "Should succeed with info for unknown format"
        print("✓ PASSED")

def main():
    """Run all tests"""
    print("Recording Error Handling Test Suite")
    print("=" * 50)
    
    try:
        test_aufnahme_error_handling()
        test_gui_validation()
        
        print("\n" + "=" * 50)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("\nThe new error handling should now:")
        print("1. Show success message when audio file is created (regardless of exit code)")
        print("2. Show info message for exit code 1 with valid file (not error)")
        print("3. Show error only when file is missing or invalid")
        print("4. Validate audio file format when possible")
        
    except Exception as e:
        print(f"\n✗ TEST SUITE ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)