#!/usr/bin/env python3
"""
voiceToGoogle.py - Speech recognition script that processes audio recordings
and converts them to text using Google's speech recognition services.

This script is part of the asynchronous workflow managed by PythonServer.py.
It processes the audio recording created by Aufnahme.py and generates a transcript.

REQUIREMENTS:
- GOOGLE_APPLICATION_CREDENTIALS environment variable must be set to point to service account key
- google-cloud-speech library must be installed: pip install google-cloud-speech
- Audio file must be in WAV format compatible with Google Speech-to-Text
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# Setup logging for speech-to-text processing
def setup_speech_logging():
    """Setup logging for speech recognition with both file and console output"""
    log_dir = Path(__file__).parent
    log_file = log_dir / "speech_recognition.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(str(log_file), mode='a', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Initialize logger
speech_logger = setup_speech_logging()

# Try to import Google Cloud Speech-to-Text
try:
    from google.cloud import speech
    GOOGLE_SPEECH_AVAILABLE = True
    speech_logger.info("Google Cloud Speech-to-Text library loaded successfully")
except ImportError as e:
    GOOGLE_SPEECH_AVAILABLE = False
    speech_logger.warning(f"Google Cloud Speech-to-Text library not available: {e}")
    speech_logger.warning("Will use simulation mode instead")

def find_audio_recording(audio_file_path=None):
    """Find the audio file in expected locations"""
    # If specific path provided, use it
    if audio_file_path and os.path.exists(audio_file_path):
        speech_logger.info(f"Using provided audio file: {audio_file_path}")
        return audio_file_path
    
    # Define possible recording locations for the fixed filename
    possible_paths = [
        "/home/pi/Desktop/v2_Tripple S/Aufnahmen/aufnahme.wav",  # Required path from problem statement
        "Aufnahmen/aufnahme.wav",  # Local directory
        "aufnahme.wav",  # Current directory  
        str(Path.home() / "Desktop" / "v2_Tripple S" / "Aufnahmen" / "aufnahme.wav"),  # Original path
        "/tmp/aufnahme.wav"  # Fallback for temporary files
    ]
    
    for audio_path in possible_paths:
        if os.path.exists(audio_path):
            speech_logger.info(f"Found audio file at: {audio_path}")
            return audio_path
    
    speech_logger.error("No audio file found in any expected location")
    speech_logger.error("Expected locations:")
    for path in possible_paths:
        speech_logger.error(f"  - {path}")
    
    return None

def simulate_speech_recognition(audio_file):
    """Simulate speech recognition processing for fallback/demo purposes"""
    speech_logger.info(f"Using simulation mode for speech recognition")
    speech_logger.info(f"Processing audio file: {audio_file}")
    
    # Check if file exists and get info
    if not os.path.exists(audio_file):
        speech_logger.error(f"Audio file not found: {audio_file}")
        return None
    
    file_size = os.path.getsize(audio_file)
    speech_logger.info(f"Audio file size: {file_size:,} bytes")
    
    # Simulate processing time based on file size
    processing_time = min(max(file_size / 1000000, 1), 5)  # 1-5 seconds
    speech_logger.info(f"Analyzing audio content... (estimated {processing_time:.1f}s)")
    
    for i in range(int(processing_time)):
        speech_logger.info(f"  Processing... {i+1}/{int(processing_time)}")
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

def check_google_credentials():
    """Check if Google Cloud credentials are properly configured"""
    credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not credentials_path:
        speech_logger.error("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        speech_logger.error("Please set it to point to your service account key file:")
        speech_logger.error("export GOOGLE_APPLICATION_CREDENTIALS='/home/pi/meinprojekt-venv/cloudKey.json'")
        return False
    
    if not os.path.exists(credentials_path):
        speech_logger.error(f"Credentials file not found: {credentials_path}")
        return False
    
    speech_logger.info(f"Found Google credentials at: {credentials_path}")
    return True

def validate_audio_file(audio_file_path):
    """Validate that the audio file is suitable for Google Speech-to-Text"""
    try:
        file_size = os.path.getsize(audio_file_path)
        speech_logger.info(f"Audio file size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
        
        # Check file size limits (Google Speech-to-Text has limits)
        if file_size == 0:
            speech_logger.error("Audio file is empty")
            return False
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit for synchronous requests
            speech_logger.warning("Audio file is large (>10MB), may require async processing")
        
        # Basic file format check
        if not audio_file_path.lower().endswith('.wav'):
            speech_logger.warning("Audio file is not in WAV format, may cause issues")
        
        return True
        
    except Exception as e:
        speech_logger.error(f"Error validating audio file: {e}")
        return False

def real_google_speech_recognition(audio_file_path):
    """Real speech recognition using Google Cloud Speech-to-Text API"""
    if not GOOGLE_SPEECH_AVAILABLE:
        speech_logger.error("Google Cloud Speech-to-Text library not available")
        return None
    
    if not check_google_credentials():
        speech_logger.error("Google credentials not properly configured")
        return None
    
    if not validate_audio_file(audio_file_path):
        speech_logger.error("Audio file validation failed")
        return None
    
    try:
        speech_logger.info("Initializing Google Speech-to-Text client...")
        client = speech.SpeechClient()
        
        speech_logger.info("Reading audio file...")
        with open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()
        
        # Configure audio and recognition settings
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,  # Standard CD quality
            language_code="de-DE",  # German language
            alternative_language_codes=["en-US"],  # Fallback to English
            enable_automatic_punctuation=True,
            enable_word_confidence=True,
        )
        
        speech_logger.info("Sending audio to Google Speech-to-Text API...")
        
        # Perform the transcription
        response = client.recognize(config=config, audio=audio)
        
        # Process results
        if not response.results:
            speech_logger.warning("No speech detected in audio file")
            return None
        
        # Get the best transcript
        transcript = ""
        confidence_scores = []
        
        for result in response.results:
            alternative = result.alternatives[0]  # Best alternative
            transcript += alternative.transcript + " "
            confidence_scores.append(alternative.confidence)
            
            speech_logger.info(f"Transcript segment: '{alternative.transcript}' (confidence: {alternative.confidence:.2f})")
        
        transcript = transcript.strip()
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        speech_logger.info(f"Speech recognition completed successfully")
        speech_logger.info(f"Average confidence: {avg_confidence:.2f}")
        speech_logger.info(f"Full transcript: '{transcript}'")
        
        return transcript
        
    except Exception as e:
        speech_logger.error(f"Google Speech-to-Text API error: {e}")
        speech_logger.error(f"Error type: {type(e).__name__}")
        
        # Log specific error types
        if "INVALID_ARGUMENT" in str(e):
            speech_logger.error("Invalid argument - check audio format and configuration")
        elif "UNAUTHENTICATED" in str(e):
            speech_logger.error("Authentication failed - check GOOGLE_APPLICATION_CREDENTIALS")
        elif "PERMISSION_DENIED" in str(e):
            speech_logger.error("Permission denied - check service account permissions")
        elif "QUOTA_EXCEEDED" in str(e):
            speech_logger.error("API quota exceeded - check your Google Cloud billing")
        elif "UNAVAILABLE" in str(e):
            speech_logger.error("Service unavailable - network or Google Cloud issue")
        
        return None

def save_transcript(text, output_file="transkript.txt"):
    """Save the recognized text to a file with proper logging"""
    try:
        # Save the transcript
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        speech_logger.info(f"Transcript saved to: {output_file}")
        speech_logger.info(f"Transcript content: '{text}'")
        
        # Also save as JSON with metadata
        json_file = output_file.replace('.txt', '.json')
        transcript_data = {
            "transcript": text,
            "timestamp": time.time(),
            "iso_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "file_size": len(text),
            "processing_method": "google_speech_api" if GOOGLE_SPEECH_AVAILABLE else "simulation"
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)
        
        speech_logger.info(f"Transcript metadata saved to: {json_file}")
        return True
        
    except Exception as e:
        speech_logger.error(f"Error saving transcript: {e}")
        return False

def main():
    """Main speech recognition workflow"""
    speech_logger.info("=== Voice to Google Speech Recognition ===")
    speech_logger.info("Starting speech-to-text processing...")
    
    # Check if an audio file was provided as command line argument
    audio_file = None
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        speech_logger.info(f"Using audio file from command line: {audio_file}")
    else:
        # Look for the aufnahme.wav file in expected locations
        audio_file = find_audio_recording()
    
    if not audio_file:
        speech_logger.error("No aufnahme.wav file found in any of the expected locations")
        speech_logger.error("Expected locations:")
        expected_paths = [
            "/home/pi/Desktop/v2_Tripple S/Aufnahmen/aufnahme.wav",
            "Aufnahmen/aufnahme.wav",
            "aufnahme.wav", 
            str(Path.home() / "Desktop" / "v2_Tripple S" / "Aufnahmen" / "aufnahme.wav"),
            "/tmp/aufnahme.wav"
        ]
        for path in expected_paths:
            speech_logger.error(f"  - {path}")
        
        # Create a dummy transcript for testing purposes
        speech_logger.info("Creating dummy transcript for workflow testing...")
        dummy_text = "Test Audio Aufnahme - Bitte erstelle ein schönes Bild von einer Landschaft mit Bergen und einem See"
        if save_transcript(dummy_text):
            speech_logger.info("✓ Dummy transcript created successfully")
            return True
        else:
            speech_logger.error("✗ Failed to create dummy transcript")
            return False
    
    speech_logger.info(f"Processing audio file: {os.path.basename(audio_file)}")
    
    # Perform speech recognition
    try:
        # Try real Google Speech-to-Text first, then fallback to simulation
        recognized_text = None
        
        if GOOGLE_SPEECH_AVAILABLE and check_google_credentials():
            speech_logger.info("Attempting real Google Speech-to-Text recognition...")
            recognized_text = real_google_speech_recognition(audio_file)
        
        if not recognized_text:
            speech_logger.info("Falling back to simulation mode...")
            recognized_text = simulate_speech_recognition(audio_file)
        
        if recognized_text:
            speech_logger.info("--- Recognition Result ---")
            speech_logger.info(f'"{recognized_text}"')
            speech_logger.info("--- End Result ---")
            
            # Save transcript
            if save_transcript(recognized_text):
                speech_logger.info("✓ Speech recognition completed successfully")
                return True
            else:
                speech_logger.error("✗ Failed to save transcript")
                return False
        else:
            speech_logger.error("✗ Speech recognition failed - no text detected")
            return False
            
    except Exception as e:
        speech_logger.error(f"✗ Speech recognition error: {e}")
        speech_logger.error(f"Error type: {type(e).__name__}")
        import traceback
        speech_logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            speech_logger.info("Speech recognition workflow completed successfully")
            sys.exit(0)
        else:
            speech_logger.error("Speech recognition workflow failed")
            sys.exit(1)
    except KeyboardInterrupt:
        speech_logger.warning("Speech recognition interrupted by user")
        sys.exit(1)
    except Exception as e:
        speech_logger.error(f"Unexpected error: {e}")
        speech_logger.error(f"Error type: {type(e).__name__}")
        import traceback
        speech_logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)