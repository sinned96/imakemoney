#!/usr/bin/env python3
"""
Example: Stop recording after a timer expires
"""

import sys
import os
import time
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PythonServer import AsyncWorkflowManager

def timer_stop_example(recording_duration=5):
    """Example of stopping recording after a timer"""
    print(f"=== Timer Stop Example (Recording for {recording_duration} seconds) ===")
    
    aufnahme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Aufnahme.py')
    
    if not os.path.exists(aufnahme_path):
        print(f"Aufnahme.py not found at {aufnahme_path}")
        return False
    
    workflow = AsyncWorkflowManager()
    
    # Start recording
    print("Starting recording...")
    if not workflow.start_recording_async(aufnahme_path):
        return False
    
    # Set up timer to stop recording
    def stop_after_timer():
        print(f"Timer expired after {recording_duration} seconds, stopping recording...")
        workflow.stop_recording()
    
    timer = threading.Timer(recording_duration, stop_after_timer)
    timer.start()
    
    # Wait for recording to finish
    print(f"Recording will automatically stop after {recording_duration} seconds...")
    while workflow.is_recording:
        time.sleep(0.1)
    
    timer.cancel()  # In case recording stopped early
    print("Recording finished!")
    return True

if __name__ == "__main__":
    timer_stop_example()