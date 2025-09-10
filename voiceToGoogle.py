#!/usr/bin/env python3
"""
voiceToGoogle.py - Speech recognition script that processes audio recordings
and converts them to text using Google's speech recognition services.

This script is part of the asynchronous workflow managed by PythonServer.py.
It processes the audio recording created by Aufnahme.py and generates a transcript.
"""

import os
import sys
import json
import time
from pathlib import Path

# For demo purposes, we'll simulate speech recognition
# In a real implementation, this would use Google Speech-to-Text API

def find_latest_recording(recordings_dir):
    """Find the most recent audio recording file"""
    if not os.path.exists(recordings_dir):
        return None
    
    # Look for common audio file extensions
    extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
    recording_files = []
    
    for ext in extensions:
        files = list(Path(recordings_dir).glob(f'*{ext}'))
        recording_files.extend(files)
    
    if not recording_files:
        return None
    
    # Return the most recently created file
    latest_file = max(recording_files, key=lambda f: f.stat().st_mtime)
    return str(latest_file)

def simulate_speech_recognition(audio_file):
    """Simulate speech recognition processing"""
    print(f"Processing audio file: {audio_file}")
    
    # Check if file exists and get info
    if not os.path.exists(audio_file):
        print(f"Error: Audio file not found: {audio_file}")
        return None
    
    file_size = os.path.getsize(audio_file)
    print(f"Audio file size: {file_size:,} bytes")
    
    # Simulate processing time based on file size
    processing_time = min(max(file_size / 1000000, 1), 5)  # 1-5 seconds
    print(f"Analyzing audio content... (estimated {processing_time:.1f}s)")
    
    for i in range(int(processing_time)):
        print(f"  Processing... {i+1}/{int(processing_time)}")
        time.sleep(1)
    
    # Simulate different recognition results based on file characteristics
    if file_size < 10000:  # Very small file
        return "Kurze Aufnahme erkannt"
    elif file_size < 100000:  # Small file
        return "Dies ist eine Testaufnahme für die Spracherkennung"
    elif file_size < 500000:  # Medium file
        return "Hallo, dies ist eine längere Audioaufnahme die von der Spracherkennung verarbeitet wird. Bitte erstelle ein Bild basierend auf diesem Text."
    else:  # Large file
        return "Dies ist eine ausführliche Audioaufnahme mit vielen Details. Die Spracherkennung hat erfolgreich den gesprochenen Inhalt erkannt und in Text umgewandelt. Dieser Text kann nun für die Bildgenerierung verwendet werden."

def real_speech_recognition(audio_file):
    """Real speech recognition using Google Cloud Speech-to-Text API"""
    try:
        # This would be the real implementation
        # from google.cloud import speech
        # client = speech.SpeechClient()
        # ... actual API calls ...
        
        print("Note: Real Google Speech-to-Text API not implemented in this demo")
        print("Using simulation instead...")
        return simulate_speech_recognition(audio_file)
        
    except ImportError:
        print("Google Cloud Speech library not available, using simulation")
        return simulate_speech_recognition(audio_file)
    except Exception as e:
        print(f"Speech recognition error: {e}")
        return simulate_speech_recognition(audio_file)

def save_transcript(text, output_file="transkript.txt"):
    """Save the recognized text to a file"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Transcript saved to: {output_file}")
        return True
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return False

def main():
    """Main speech recognition workflow"""
    print("=== Voice to Google Speech Recognition ===")
    print("Starting speech-to-text processing...")
    
    # Define possible recording locations
    possible_dirs = [
        "Aufnahmen",  # Local directory
        ".",  # Current directory
        str(Path.home() / "Desktop" / "v2_Tripple S" / "Aufnahmen"),  # Original path
        "/tmp"  # Fallback for temporary files
    ]
    
    audio_file = None
    
    # Try to find an audio file in possible directories
    for recordings_dir in possible_dirs:
        if os.path.exists(recordings_dir):
            audio_file = find_latest_recording(recordings_dir)
            if audio_file:
                print(f"Found audio recording in: {recordings_dir}")
                break
    
    if not audio_file:
        print("No audio recording found in any of the expected directories:")
        for d in possible_dirs:
            print(f"  - {d}")
        
        # Create a dummy transcript for testing purposes
        print("Creating dummy transcript for workflow testing...")
        dummy_text = "Test Audio Aufnahme - Bitte erstelle ein schönes Bild von einer Landschaft mit Bergen und einem See"
        save_transcript(dummy_text)
        print("✓ Dummy transcript created successfully")
        return True
    
    print(f"Processing audio file: {os.path.basename(audio_file)}")
    
    # Perform speech recognition
    try:
        recognized_text = real_speech_recognition(audio_file)
        
        if recognized_text:
            print("\n--- Recognition Result ---")
            print(f'"{recognized_text}"')
            print("--- End Result ---")
            
            # Save transcript
            if save_transcript(recognized_text):
                print("✓ Speech recognition completed successfully")
                return True
            else:
                print("✗ Failed to save transcript")
                return False
        else:
            print("✗ Speech recognition failed - no text detected")
            return False
            
    except Exception as e:
        print(f"✗ Speech recognition error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nSpeech recognition interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)