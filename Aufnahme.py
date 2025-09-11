#!/usr/bin/env python3
"""
Aufnahme.py - Audio recording script with SIGTERM handling

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

class AudioRecorder:
    def __init__(self):
        self.recording_process = None
        self.recording_started = False
        self.start_time = None
        self.output_file = None
        self.frame_count = 0
        self.setup_signal_handler()
        
    def setup_signal_handler(self):
        """Setup SIGTERM handler for clean shutdown"""
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)  # Also handle Ctrl+C
        
    def signal_handler(self, signum, frame):
        """Handle SIGTERM/SIGINT signals gracefully"""
        print(f"Received signal {signum}, stopping recording...")
        self.stop_recording()
        
    def start_recording(self):
        """Start audio recording using available tools"""
        if self.recording_started:
            print("Warning: Recording already started")
            return
            
        # Create output directory if it doesn't exist
        recordings_dir = Path.home() / "Desktop" / "v2_Tripple S" / "Aufnahmen"
        recordings_dir.mkdir(parents=True, exist_ok=True)
        
        # Use fixed filename - always overwrite previous recording
        self.output_file = recordings_dir / "aufnahme.wav"
        
        print(f"Starting recording to: {self.output_file}")
        
        # Try different recording tools in order of preference
        recording_commands = [
            # ALSA tools (most common on Linux)
            ['arecord', '-f', 'cd', '-t', 'wav', str(self.output_file)],
            # PulseAudio tools
            ['parecord', '--format=s16le', '--rate=44100', '--channels=2', str(self.output_file)],
            # FFmpeg (fallback)
            ['ffmpeg', '-f', 'alsa', '-i', 'default', '-ac', '2', '-ar', '44100', str(self.output_file)]
        ]
        
        cmd_found = None
        for cmd in recording_commands:
            try:
                # Test if command exists
                subprocess.run([cmd[0], '--help'], capture_output=True, timeout=2)
                cmd_found = cmd
                break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        if not cmd_found:
            # Create a mock recording process for testing/demo purposes
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
        frame_count += 44100 * 2  # Simulate 1 second of 44.1kHz stereo audio
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
            print(f"Recording started successfully (PID: {self.recording_process.pid})")
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            sys.exit(1)
            
    def stop_recording(self):
        """Stop the recording and cleanup"""
        if not self.recording_started or not self.recording_process:
            print("No recording to stop")
            return
            
        try:
            # Terminate the recording process
            if self.recording_process.poll() is None:  # Process is still running
                # Send SIGINT to arecord for clean shutdown
                os.killpg(os.getpgid(self.recording_process.pid), signal.SIGINT)
                
                # Wait for process to finish
                stdout, stderr = self.recording_process.communicate(timeout=5)
                
                if stderr:
                    stderr_text = stderr.decode('utf-8', errors='ignore')
                    if stderr_text.strip():
                        print(f"Recording warnings: {stderr_text}")
                
        except subprocess.TimeoutExpired:
            print("Warning: Recording process didn't terminate cleanly, forcing kill")
            os.killpg(os.getpgid(self.recording_process.pid), signal.SIGKILL)
            self.recording_process.wait()
        except Exception as e:
            print(f"Error stopping recording: {e}")
            
        # Calculate recording statistics
        if self.start_time:
            duration = time.time() - self.start_time
            print(f"Recording duration: {duration:.2f} seconds")
            
            # Estimate frame count (44.1kHz * channels * duration)
            sample_rate = 44100
            channels = 2  # Stereo for CD format
            self.frame_count = int(sample_rate * channels * duration)
            
        # Check if file was created and get size
        if self.output_file and self.output_file.exists():
            file_size = self.output_file.stat().st_size
            print(f"Recording saved to: {self.output_file}")
            print(f"File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            print(f"Estimated frames recorded: {self.frame_count:,}")
        else:
            print("Warning: Recording file was not created or is missing")
            
        self.recording_started = False
        
    def run(self):
        """Main recording loop"""
        print("Audio recorder starting...")
        
        # Start recording immediately
        self.start_recording()
        
        if not self.recording_started:
            sys.exit(1)
            
        try:
            # Wait for the recording process to finish or for signals
            while self.recording_process and self.recording_process.poll() is None:
                time.sleep(0.1)  # Small sleep to prevent busy waiting
                
            # If we get here, recording process ended naturally
            if self.recording_process and self.recording_process.returncode != 0:
                print(f"Recording process ended with error code: {self.recording_process.returncode}")
                
        except KeyboardInterrupt:
            print("Interrupted by user")
        finally:
            self.stop_recording()

def main():
    """Main entry point"""
    print("Aufnahme.py - Audio Recording Script")
    print("Press Ctrl+C or send SIGTERM to stop recording")
    
    recorder = AudioRecorder()
    recorder.run()
    
    print("Recording session completed.")

if __name__ == "__main__":
    main()