#!/usr/bin/env python3
"""
Aufnahme.py - Audio recording script with SIGTERM handling

Path Logic and Workflow Integration:
- Base directory: /home/pi/Desktop/v2_Tripple S/
- Output file: /home/pi/Desktop/v2_Tripple S/aufnahme.wav (fixed filename, always overwrite)
- This script starts the workflow by creating the audio recording
- After recording completes, voiceToGoogle.py processes the audio
- Finally, the processed files are available for AI integration
- Workflow sequence: Recording (this script) → Transcription → Upload

This script starts recording immediately when launched and stops cleanly
when receiving SIGTERM. It outputs frame count and file location when stopping.
"""

def setup_projekt_logging():
    """Setup unified logging for projekt.log and console output"""
    import logging
    from pathlib import Path
    # Use standardized base directory, but fall back to current directory if not accessible
    try:
        log_dir = Path("/home/pi/Desktop/v2_Tripple S")
        log_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        # Fallback to current working directory for testing/development
        log_dir = Path.cwd()
        
    log_file = log_dir / "projekt.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s [%(name)s]: %(message)s',
        handlers=[
            logging.FileHandler(str(log_file), mode='a', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Initialize logger
logger = setup_projekt_logging()

import os
import sys
import signal
import time
import subprocess
from datetime import datetime
from pathlib import Path
import logging

class AudioRecorder:
    def __init__(self):
        self.recording_process = None
        self.recording_started = False
        self.start_time = None
        self.output_file = None
        self.frame_count = 0
        self.setup_signal_handler()
        logger.info("AudioRecorder initialized")
        
    def setup_signal_handler(self):
        """Setup SIGTERM handler for clean shutdown"""
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)  # Also handle Ctrl+C
        logger.info("Signal handlers configured for clean shutdown")
        
    def signal_handler(self, signum, frame):
        """Handle SIGTERM/SIGINT signals gracefully"""
        logger.info(f"Received signal {signum}, stopping recording...")
        print(f"Received signal {signum}, stopping recording...")
        self.stop_recording()
        
    def start_recording(self):
        """Start audio recording using available tools"""
        if self.recording_started:
            logger.warning("Recording already started")
            print("Warning: Recording already started")
            return
            
        # Create standardized output directory if it doesn't exist
        recordings_dir = Path("/home/pi/Desktop/v2_Tripple S")
        try:
            recordings_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Recording directory ensured: {recordings_dir}")
        except Exception as e:
            logger.error(f"Failed to create recording directory: {e}")
            print(f"Error creating recording directory: {e}")
            return
        
        # Use fixed filename in standardized location - always overwrite previous recording
        self.output_file = recordings_dir / "aufnahme.wav"
        
        logger.info(f"Starting recording to: {self.output_file}")
        print(f"Starting recording to: {self.output_file}")
        print(f"Using standardized path: /home/pi/Desktop/v2_Tripple S/aufnahme.wav")
        
        # Try different recording tools in order of preference - MODIFIED FOR MONO RECORDING
        recording_commands = [
            # ALSA tools (most common on Linux) - use mono format (-c 1) for Google Speech-to-Text compatibility
            ['arecord', '-f', 'S16_LE', '-c', '1', '-r', '44100', '-t', 'wav', str(self.output_file)],
            # PulseAudio tools - use mono (--channels=1) for Google Speech-to-Text compatibility
            ['parecord', '--format=s16le', '--rate=44100', '--channels=1', str(self.output_file)],
            # FFmpeg (fallback) - use mono (-ac 1) for Google Speech-to-Text compatibility
            ['ffmpeg', '-f', 'alsa', '-i', 'default', '-ac', '1', '-ar', '44100', str(self.output_file)]
        ]
        
        cmd_found = None
        for cmd in recording_commands:
            try:
                # Test if command exists
                subprocess.run([cmd[0], '--help'], capture_output=True, timeout=2)
                cmd_found = cmd
                logger.info(f"Found recording tool: {cmd[0]}")
                break
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                logger.debug(f"Recording tool {cmd[0]} not available: {e}")
                continue
        
        if not cmd_found:
            # Create a mock recording process for testing/demo purposes
            logger.warning("No audio recording tools found (arecord, parecord, ffmpeg)")
            print("Warning: No audio recording tools found (arecord, parecord, ffmpeg)")
            print("Starting simulation mode for testing...")
            logger.info("Starting mock recording simulation mode")
            cmd_found = ['python3', '-c', f"""
import time
import os
import signal

# Create empty file to simulate recording
with open('{self.output_file}', 'wb') as f:
    pass

print("Mock recording started - generating frames...")
frame_count = 0
try:
    while True:
        time.sleep(1)
        frame_count += 44100 * 1  # Simulate 1 second of 44.1kHz mono audio
        print(f"Frames processed: {{frame_count}}")
        # Simulate file growth
        with open('{self.output_file}', 'ab') as f:
            f.write(b'\\x00' * 1000)  # Add some dummy data
except KeyboardInterrupt:
    print(f"Recording stopped. Total frames: {{frame_count}}")
"""]
        
        try:
            self.recording_process = subprocess.Popen(
                cmd_found,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                preexec_fn=os.setsid  # Create new process group
            )
            self.recording_started = True
            self.start_time = time.time()
            logger.info(f"Recording started successfully (PID: {self.recording_process.pid})")
            print(f"Recording started successfully (PID: {self.recording_process.pid})")
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            print(f"Error starting recording: {e}")
            sys.exit(1)
            
    def stop_recording(self):
        """Stop the recording and cleanup with improved error handling"""
        if not self.recording_started or not self.recording_process:
            logger.warning("No recording to stop")
            print("No recording to stop")
            return
            
        logger.info("Stopping recording process...")
        process_exit_code = None
        try:
            # Terminate the recording process
            if self.recording_process.poll() is None:  # Process is still running
                # Send SIGINT to arecord for clean shutdown
                os.killpg(os.getpgid(self.recording_process.pid), signal.SIGINT)
                logger.info("Sent SIGINT to recording process")
                
                # Wait for process to finish
                stdout, stderr = self.recording_process.communicate(timeout=5)
                process_exit_code = self.recording_process.returncode
                
                if stderr:
                    # Handle stderr properly - it's already a string due to universal_newlines=True
                    stderr_text = stderr if isinstance(stderr, str) else stderr.decode('utf-8', errors='ignore')
                    if stderr_text.strip():
                        logger.warning(f"Recording warnings: {stderr_text}")
                        print(f"Recording warnings: {stderr_text}")
            else:
                process_exit_code = self.recording_process.returncode
                
        except subprocess.TimeoutExpired:
            logger.error("Recording process didn't terminate cleanly, forcing kill")
            print("Warning: Recording process didn't terminate cleanly, forcing kill")
            os.killpg(os.getpgid(self.recording_process.pid), signal.SIGKILL)
            self.recording_process.wait()
            process_exit_code = self.recording_process.returncode
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            print(f"Error stopping recording: {e}")
            
        # Calculate recording statistics
        if self.start_time:
            duration = time.time() - self.start_time
            logger.info(f"Recording duration: {duration:.2f} seconds")
            print(f"Recording duration: {duration:.2f} seconds")
            
            # Estimate frame count (44.1kHz * channels * duration) - using MONO (1 channel)
            sample_rate = 44100
            channels = 1  # Mono for Google Speech-to-Text compatibility
            self.frame_count = int(sample_rate * channels * duration)
        
        # Improved error handling: Check file creation success first
        file_created_successfully = False
        file_size = 0
        
        if self.output_file and self.output_file.exists():
            file_size = self.output_file.stat().st_size
            # Consider file created successfully if it has reasonable size (at least 1KB for very short recordings)
            file_created_successfully = file_size > 1024
            
            logger.info(f"Recording saved to: {self.output_file}")
            logger.info(f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            logger.info(f"Estimated frames recorded: {self.frame_count:,}")
            
            print(f"Recording saved to: {self.output_file}")
            print(f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            print(f"Estimated frames recorded: {self.frame_count:,}")
            
            if file_created_successfully:
                logger.info("Audio file successfully created")
                print("[SUCCESS] Audio file successfully created")
            else:
                logger.warning("Audio file is very small, may be incomplete")
                print("[WARNING] Warning: Audio file is very small, may be incomplete")
        else:
            logger.error("Recording file was not created or is missing")
            print("[ERROR] Error: Recording file was not created or is missing")
            
        # Enhanced error reporting based on file creation success
        if process_exit_code is not None and process_exit_code != 0:
            if file_created_successfully:
                # Exit code != 0 but file was created successfully
                # This is common when stopping recording tools with SIGTERM/SIGINT
                logger.info(f"Recording process ended with exit code {process_exit_code}, but audio file was saved successfully")
                print(f"ℹ Info: Recording process ended with exit code {process_exit_code}, but audio file was saved successfully")
                print("This is normal when stopping recording tools via signal")
            else:
                # Exit code != 0 AND no valid file created - this is a real error
                logger.error(f"Recording process ended with error code {process_exit_code} and no valid audio file was created")
                print(f"[ERROR] Error: Recording process ended with error code {process_exit_code} and no valid audio file was created")
        elif file_created_successfully:
            logger.info("Recording completed successfully")
            print("[SUCCESS] Recording completed successfully")
            
        self.recording_started = False
        
    def run(self):
        """Main recording loop"""
        logger.info("Audio recorder starting...")
        print("Audio recorder starting...")
        
        # Start recording immediately
        self.start_recording()
        
        if not self.recording_started:
            logger.error("Failed to start recording")
            sys.exit(1)
            
        try:
            # Wait for the recording process to finish or for signals
            while self.recording_process and self.recording_process.poll() is None:
                time.sleep(0.1)  # Small sleep to prevent busy waiting
                
            # If we get here, recording process ended naturally
            # Note: We handle exit codes in stop_recording() method with file validation
                
        except KeyboardInterrupt:
            logger.info("Recording interrupted by user (KeyboardInterrupt)")
            print("[INTERRUPT] Recording interrupted by user (KeyboardInterrupt)")
            print("[STATUS] Gracefully stopping recording process...")
        finally:
            self.stop_recording()

def main():
    """Main entry point"""
    logger.info("=== Aufnahme.py - Audio Recording Script Started ===")
    print("Aufnahme.py - Audio Recording Script")
    print("Press Ctrl+C or send SIGTERM to stop recording")
    
    try:
        recorder = AudioRecorder()
        recorder.run()
        logger.info("Recording session completed")
        print("Recording session completed.")
    except KeyboardInterrupt:
        logger.info("Main process interrupted by KeyboardInterrupt")
        print("\n[INTERRUPT] Main process interrupted by KeyboardInterrupt")
        print("[STATUS] Audio recording script shutting down gracefully")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        try:
            print(f"[ERROR] Unexpected error in main: {e}")
        except Exception:
            print("[ERROR] Unexpected error occurred but could not be displayed due to encoding issues")

if __name__ == "__main__":
    main()
