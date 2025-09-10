# IMA Workflow - Asynchronous Audio Recording & AI Processing

This project implements an asynchronous workflow for audio recording and AI-powered image generation.

## Key Features

### Asynchronous Recording
- **Non-blocking execution**: Recording runs in background subprocess
- **Flexible termination**: Stop recording via Enter key, signals, or GUI events
- **Output capture**: All subprocess stdout/stderr is collected and displayed
- **Clean shutdown**: Uses SIGTERM for graceful termination

## Usage

### Basic Workflow
```bash
# Run the new async workflow
python3 PythonServer.py

# Run the original synchronous workflow (backwards compatibility)
python3 PythonServer.py --original
```

### Programmatic Usage
```python
from PythonServer import AsyncWorkflowManager

# Create workflow manager
workflow = AsyncWorkflowManager()

# Start recording asynchronously  
success = workflow.start_recording_async("path/to/Aufnahme.py")

# Recording runs in background - you can now:
# - Wait for user input
# - Set timers
# - Handle GUI events
# - Process other tasks

# Stop recording when ready
workflow.stop_recording()

# Continue with rest of workflow
workflow.run_script_sync("voiceToGoogle.py", "Speech Recognition")
workflow.run_script_sync("dateiKopieren.py", "File Copy")
# ... generate images ...
```

## Workflow Steps

1. **Aufnahme.py** - Audio recording (asynchronous, stoppable)
2. **voiceToGoogle.py** - Speech-to-text processing
3. **dateiKopieren.py** - File management
4. **Image Generation** - AI-powered image creation

## Signal Handling

The recording can be stopped by:
- Pressing Enter in the console
- Sending SIGTERM to the process
- Pressing Ctrl+C (SIGINT)
- GUI callbacks or external events

## Files

- `PythonServer.py` - Main workflow script with async support
- `Aufnahme.py` - Audio recording script with SIGTERM handling
- `main.py` - GUI application with slideshow functionality
- `demo_async.py` - Demo of async functionality

## Requirements

```bash
pip install pyperclip requests google-auth google-cloud-aiplatform
```

## Demo

Run the demo to see the async functionality:
```bash
python3 demo_async.py
```

This shows how recording runs in the background and can be stopped flexibly.