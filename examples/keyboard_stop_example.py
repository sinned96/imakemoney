#!/usr/bin/env python3
"""
Example: Stop recording by keyboard input (Enter key)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PythonServer import AsyncWorkflowManager

def keyboard_stop_example():
    """Example of stopping recording via keyboard input"""
    print("=== Keyboard Stop Example ===")
    print("Recording will start and can be stopped by pressing Enter")
    
    aufnahme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Aufnahme.py')
    
    if not os.path.exists(aufnahme_path):
        print(f"Aufnahme.py not found at {aufnahme_path}")
        return False
    
    workflow = AsyncWorkflowManager()
    
    # Start recording
    print("Starting recording...")
    if not workflow.start_recording_async(aufnahme_path):
        return False
    
    # Wait for user to stop recording
    print("\n*** Recording is active ***")
    print("Press Enter to stop recording...")
    
    # Use the built-in wait functionality
    workflow.wait_for_stop_signal()
    
    # Stop recording if still running
    if workflow.is_recording:
        workflow.stop_recording()
    
    print("Recording stopped by user input!")
    return True

if __name__ == "__main__":
    try:
        keyboard_stop_example()
    except KeyboardInterrupt:
        print("\nStopped by Ctrl+C")