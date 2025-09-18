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

import os
import sys
import signal
import time
import subprocess
from datetime import datetime
from pathlib import Path
from logging_config import setup_project_logging, log_function_entry, log_function_exit, log_exception

# Setup project logging
logger = setup_project_logging("Aufnahme")

class AudioRecorder:
    def __init__(self):
        log_function_entry(logger, "__init__")
        self.recording_process = None
        self.recording_started = False
        self.start_time = None
        self.output_file = None
        self.frame_count = 0
        self.setup_signal_handler()
        logger.info("AudioRecorder initialized successfully")
        log_function_exit(logger, "__init__")
        
    def setup_signal_handler(self):
        """Setup SIGTERM handler for clean shutdown"""
        logger.debug("Setting up signal handlers for SIGTERM and SIGINT")
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)  # Also handle Ctrl+C
        logger.info("Signal handlers configured successfully")
        
    def signal_handler(self, signum, frame):
        """Handle SIGTERM/SIGINT signals gracefully"""
        logger.warning(f"Received signal {signum}, stopping recording gracefully...")
        print(f"Received signal {signum}, stopping recording...")
        self.stop_recording()
        
    def start_recording(self):
        """Start audio recording using available tools"""
        log_function_entry(logger, "start_recording")
        
        if self.recording_started:
            logger.warning("Recording already started - ignoring duplicate start request")
            print("Warning: Recording already started")
            return
            
        try:
            # Create standardized output directory if it doesn't exist
            recordings_dir = Path("/home/pi/Desktop/v2_Tripple S")
            logger.debug(f"Creating recordings directory: {recordings_dir}")
            try:
                recordings_dir.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError):
                # Fallback to current directory for development/testing
                logger.warning(f"Cannot create target directory {recordings_dir}, falling back to current directory")
                recordings_dir = Path.cwd()
            
            # Use fixed filename in standardized location - always overwrite previous recording
            self.output_file = recordings_dir / "aufnahme.wav"
            logger.info(f"Output file set to: {self.output_file}")
            
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
            logger.debug("Searching for available recording tools...")
            for cmd in recording_commands:
                try:
                    # Test if command exists
                    logger.debug(f"Testing recording tool: {cmd[0]}")
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
                logger.info("Starting simulation mode for testing...")
                print("Warning: No audio recording tools found (arecord, parecord, ffmpeg)")
                print("Starting simulation mode for testing...")
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
            
            logger.info(f"Starting recording process with command: {' '.join(cmd_found[:2])}...")
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
            log_function_exit(logger, "start_recording", result=True)
            
        except Exception as e:
            error_msg = f"Error starting recording: {e}"
            logger.error(error_msg, exc_info=True)
            print(error_msg)
            log_function_exit(logger, "start_recording", error=e)
            sys.exit(1)
            
    def stop_recording(self):
        """Stop the recording and cleanup with improved error handling"""
        log_function_entry(logger, "stop_recording")
        
        if not self.recording_started or not self.recording_process:
            logger.warning("No recording to stop - recording not started or process not available")
            print("No recording to stop")
            log_function_exit(logger, "stop_recording", result=False)
            return
            
        process_exit_code = None
        try:
            # Terminate the recording process
            if self.recording_process.poll() is None:  # Process is still running
                logger.debug("Sending SIGINT to recording process for clean shutdown")
                # Send SIGINT to arecord for clean shutdown
                os.killpg(os.getpgid(self.recording_process.pid), signal.SIGINT)
                
                # Wait for process to finish
                logger.debug("Waiting for recording process to terminate...")
                stdout, stderr = self.recording_process.communicate(timeout=5)
                process_exit_code = self.recording_process.returncode
                logger.info(f"Recording process terminated with exit code: {process_exit_code}")
                
                if stderr:
                    # Handle stderr properly - it's already a string due to universal_newlines=True
                    stderr_text = stderr if isinstance(stderr, str) else stderr.decode('utf-8', errors='ignore')
                    if stderr_text.strip():
                        logger.warning(f"Recording warnings: {stderr_text}")
                        print(f"Recording warnings: {stderr_text}")
            else:
                process_exit_code = self.recording_process.returncode
                logger.debug(f"Recording process already terminated with exit code: {process_exit_code}")
                
        except subprocess.TimeoutExpired:
            logger.error("Recording process didn't terminate cleanly within timeout, forcing kill")
            print("Warning: Recording process didn't terminate cleanly, forcing kill")
            os.killpg(os.getpgid(self.recording_process.pid), signal.SIGKILL)
            self.recording_process.wait()
            process_exit_code = self.recording_process.returncode
            logger.warning(f"Forced kill completed, exit code: {process_exit_code}")
        except Exception as e:
            logger.error(f"Error stopping recording: {e}", exc_info=True)
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
            logger.debug(f"Estimated frame count: {self.frame_count:,} frames")
        
        # Improved error handling: Check file creation success first
        file_created_successfully = False
        file_size = 0
        
        if self.output_file and self.output_file.exists():
            file_size = self.output_file.stat().st_size
            # Consider file created successfully if it has reasonable size (at least 1KB for very short recordings)
            file_created_successfully = file_size > 1024
            
            logger.info(f"Recording file: {self.output_file}")
            logger.info(f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            logger.info(f"Estimated frames recorded: {self.frame_count:,}")
            
            print(f"Recording saved to: {self.output_file}")
            print(f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            print(f"Estimated frames recorded: {self.frame_count:,}")
            
            if file_created_successfully:
                logger.info("SUCCESS: Audio file successfully created")
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
                logger.debug("This is normal when stopping recording tools via signal")
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
        log_function_exit(logger, "stop_recording", result=file_created_successfully)
        
    def run(self):
        """Main recording loop"""
        log_function_entry(logger, "run")
        logger.info("Audio recorder starting...")
        print("Audio recorder starting...")
        
        # Start recording immediately
        self.start_recording()
        
        if not self.recording_started:
            logger.error("Failed to start recording, exiting")
            log_function_exit(logger, "run", error="Recording failed to start")
            sys.exit(1)
            
        try:
            logger.info("Entering recording loop, waiting for process to finish or signals...")
            # Wait for the recording process to finish or for signals
            while self.recording_process and self.recording_process.poll() is None:
                time.sleep(0.1)  # Small sleep to prevent busy waiting
                
            # If we get here, recording process ended naturally
            logger.info("Recording process ended naturally")
            # Note: We handle exit codes in stop_recording() method with file validation
                
        except KeyboardInterrupt:
            logger.warning("Recording interrupted by user (KeyboardInterrupt)")
            print("[INTERRUPT] Recording interrupted by user (KeyboardInterrupt)")
            print("[STATUS] Gracefully stopping recording process...")
        except Exception as e:
            logger.error(f"Unexpected error in recording loop: {e}", exc_info=True)
            print(f"[ERROR] Unexpected error in recording loop: {e}")
        finally:
            logger.info("Cleaning up recording resources...")
            self.stop_recording()
        
        logger.info("Recording session completed")
        log_function_exit(logger, "run", result=True)

def main():
    """Main entry point"""
    log_function_entry(logger, "main")
    logger.info("Aufnahme.py - Audio Recording Script starting")
    print("Aufnahme.py - Audio Recording Script")
    print("Press Ctrl+C or send SIGTERM to stop recording")
    
    try:
        recorder = AudioRecorder()
        recorder.run()
        logger.info("Recording session completed successfully")
        print("Recording session completed.")
        log_function_exit(logger, "main", result=True)
    except KeyboardInterrupt:
        logger.warning("Main process interrupted by KeyboardInterrupt")
        print("\n[INTERRUPT] Main process interrupted by KeyboardInterrupt")
        print("[STATUS] Audio recording script shutting down gracefully")
        log_function_exit(logger, "main", error="KeyboardInterrupt")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        try:
            print(f"[ERROR] Unexpected error in main: {e}")
        except Exception:
            logger.critical("Critical error: Could not even display error message due to encoding issues")
            print("[ERROR] Unexpected error occurred but could not be displayed due to encoding issues")
        log_function_exit(logger, "main", error=e)

if __name__ == "__main__":
    main()
