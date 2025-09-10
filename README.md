# IMA Workflow - Asynchronous Audio Recording & AI Processing

This project implements an asynchronous workflow for audio recording and AI-powered image generation with a **separated architecture (Variante 3)**.

## 🚀 Separated Workflow Architecture

The system is now divided into two independent components:

1. **GUI (main.py)** - Only starts/stops recording (Aufnahme.py)
2. **Workflow Manager (PythonServer.py)** - Background service that processes recordings

### Communication via Files
- **Trigger File**: `workflow_trigger.txt` - GUI → Workflow Manager
- **Status Log**: `workflow_status.log` - Workflow Manager → GUI

## 📋 Quick Start

### 1. Start Background Service
```bash
# Option A: Direct service
python3 PythonServer.py --service

# Option B: Using utility script  
python3 start_workflow_service.py
```

### 2. Start GUI
```bash
python3 main.py
```

### 3. Use the Workflow
1. Login to GUI
2. Click "Aufnahme" button
3. Start/Stop recording
4. Watch automatic workflow processing in real-time
5. Generated images appear in BilderVertex/

## 🧪 Testing & Demo

```bash
# Run comprehensive tests
python3 test_separated_workflow.py

# Interactive demonstration
python3 demo_separated_workflow.py
```

## 🔧 Legacy Modes

```bash
# Original synchronous workflow
python3 PythonServer.py --original

# Interactive async workflow
python3 PythonServer.py
```

## Key Features

### Asynchronous Recording
- **Non-blocking execution**: Recording runs in background subprocess
- **Flexible termination**: Stop recording via Enter key, signals, or GUI events
- **Output capture**: All subprocess stdout/stderr is collected and displayed
- **Clean shutdown**: Uses SIGTERM for graceful termination

### Separated Architecture
- **Independent Components**: GUI and workflow manager run separately
- **File-based Communication**: Robust trigger and status mechanism
- **Real-time Status**: GUI displays workflow progress from log files
- **Cross-platform**: Works on Raspberry Pi, Desktop, headless environments

## Usage

### Basic Workflow
```bash
# Run the new async workflow
python3 PythonServer.py

# Run the original synchronous workflow (backwards compatibility)
python3 PythonServer.py --original

# Run as background service (Variante 3)
python3 PythonServer.py --service
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

- `PythonServer.py` - Main workflow script with async support & background service
- `Aufnahme.py` - Audio recording script with SIGTERM handling
- `main.py` - GUI application with slideshow functionality and workflow integration
- `demo_async.py` - Demo of async functionality
- `demo_separated_workflow.py` - Demo of separated architecture
- `test_separated_workflow.py` - Comprehensive test suite
- `SEPARATED_WORKFLOW.md` - Detailed architecture documentation

## Requirements

```bash
pip install pyperclip requests google-auth google-cloud-aiplatform kivy kivymd
```

## Demo

Run the demo to see the separated workflow functionality:
```bash
python3 demo_separated_workflow.py
```

This shows how the GUI and workflow manager communicate via files and process recordings independently.

---

📖 **For detailed documentation of the separated architecture, see [SEPARATED_WORKFLOW.md](SEPARATED_WORKFLOW.md)**