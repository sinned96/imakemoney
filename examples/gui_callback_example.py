#!/usr/bin/env python3
"""
Example: Stop recording via GUI callback/signal
This simulates how a GUI application could control the recording
"""

import sys
import os
import time
import threading

# Add parent directory to path  
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PythonServer import AsyncWorkflowManager

class MockGUI:
    """Mock GUI class to simulate GUI callbacks"""
    
    def __init__(self):
        self.workflow = None
        self.recording_active = False
        
    def start_recording_callback(self):
        """Simulate GUI button callback to start recording"""
        print("GUI: Start button clicked")
        
        aufnahme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Aufnahme.py')
        
        if not os.path.exists(aufnahme_path):
            print(f"GUI: Error - Aufnahme.py not found")
            return False
            
        self.workflow = AsyncWorkflowManager()
        
        if self.workflow.start_recording_async(aufnahme_path):
            self.recording_active = True
            print("GUI: Recording started successfully")
            return True
        else:
            print("GUI: Failed to start recording")
            return False
            
    def stop_recording_callback(self):
        """Simulate GUI button callback to stop recording"""
        print("GUI: Stop button clicked")
        
        if self.workflow and self.recording_active:
            self.workflow.stop_recording()
            self.recording_active = False
            print("GUI: Recording stopped")
            return True
        else:
            print("GUI: No recording to stop")
            return False

def gui_callback_example():
    """Example of GUI-controlled recording"""
    print("=== GUI Callback Example ===")
    print("Simulating GUI application controlling recording")
    
    gui = MockGUI()
    
    # Simulate user clicking start button
    print("\n1. User clicks 'Start Recording' button")
    if not gui.start_recording_callback():
        return False
    
    # Simulate recording running while user does other things
    print("\n2. Recording runs in background while GUI remains responsive")
    for i in range(3):
        print(f"   GUI: User can interact with interface... ({i+1}/3)")
        time.sleep(1)
    
    # Simulate user clicking stop button
    print("\n3. User clicks 'Stop Recording' button") 
    gui.stop_recording_callback()
    
    print("\nGUI remains responsive throughout the entire process!")
    return True

def signal_example():
    """Example of stopping via external signal"""
    print("\n=== Signal Example ===")
    print("Recording will be stopped by sending SIGTERM after 3 seconds")
    
    aufnahme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Aufnahme.py')
    
    if not os.path.exists(aufnahme_path):
        print(f"Aufnahme.py not found")
        return False
    
    workflow = AsyncWorkflowManager()
    
    if not workflow.start_recording_async(aufnahme_path):
        return False
        
    # Simulate external signal after delay
    def send_signal():
        print("External system: Sending SIGTERM signal...")
        import os, signal
        try:
            # In real scenario, this would come from external source
            os.kill(workflow.recording_process.pid, signal.SIGTERM)
        except:
            pass  # Process might already be stopped
    
    timer = threading.Timer(3, send_signal)
    timer.start()
    
    # Wait for recording to stop
    while workflow.is_recording:
        time.sleep(0.1)
    
    timer.cancel()
    print("Recording stopped by external signal!")
    return True

if __name__ == "__main__":
    try:
        gui_callback_example()
        signal_example()
        print("\n✅ All GUI examples completed!")
    except KeyboardInterrupt:
        print("\nStopped by Ctrl+C")