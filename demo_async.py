#!/usr/bin/env python3
"""
Demo script showing the new asynchronous workflow functionality
"""

import os
import time
from PythonServer import AsyncWorkflowManager

def demo_async_recording():
    """Demo the new async recording functionality"""
    print("=== Demo: Asynchronous Recording Workflow ===")
    print()
    
    # Check if Aufnahme.py exists locally
    aufnahme_path = os.path.abspath('Aufnahme.py')
    if not os.path.exists(aufnahme_path):
        print(f"Aufnahme.py not found at {aufnahme_path}")
        print("This demo requires Aufnahme.py to be in the same directory")
        return False
    
    # Create workflow manager
    manager = AsyncWorkflowManager()
    
    print("1. Starting recording asynchronously...")
    success = manager.start_recording_async(aufnahme_path)
    
    if not success:
        print("Failed to start recording")
        return False
    
    print("2. Recording is running in background...")
    print("   In a real scenario, you can now:")
    print("   - Wait for user input (Enter key)")
    print("   - Set up a timer")
    print("   - Wait for GUI callbacks")
    print("   - Handle external signals")
    print()
    
    # Demo: let it run for a few seconds
    print("3. Letting recording run for 3 seconds...")
    for i in range(3):
        print(f"   ...{3-i} seconds remaining")
        time.sleep(1)
    
    print("4. Stopping recording with SIGTERM...")
    manager.stop_recording()
    
    print()
    print("5. Now you can continue with the rest of the workflow:")
    print("   - voiceToGoogle.py (speech recognition)")
    print("   - dateiKopieren.py (file copying)")  
    print("   - Image generation with AI")
    print()
    print("✅ Demo completed successfully!")
    print()
    print("Key benefits of the new async approach:")
    print("- Recording can be stopped flexibly by external events")
    print("- Workflow doesn't block while recording")
    print("- All subprocess output is captured and displayed") 
    print("- Clean SIGTERM handling for graceful shutdown")
    
    return True

if __name__ == "__main__":
    try:
        demo_async_recording()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\nDemo error: {e}")