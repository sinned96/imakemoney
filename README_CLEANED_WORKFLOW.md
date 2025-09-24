# Cleaned Workflow Documentation - ImakeMoney Project

## Overview

This project implements a streamlined workflow for **Audio Recording → Speech Recognition → Vertex AI Image Generation**. The workflow has been cleaned and optimized to provide a minimal, robust solution with automatic integration.

## Core Workflow

```
📼 Recording (Aufnahme.py)
    ↓ (creates aufnahme.wav)
🗣️ Speech Recognition (voiceToGoogle.py) 
    ↓ (creates transkript.txt)
🎨 Vertex AI (automatic) 
    ↓ (creates images in BilderVertex/)
🖼️ GUI Display (main.py)
```

## Architecture

### Core Components

1. **main.py** - GUI application with Kivy-based slideshow and recording controls
2. **Aufnahme.py** - Audio recording script with SIGTERM handling
3. **voiceToGoogle.py** - Google Speech-to-Text transcription
4. **PythonServer.py** - Background workflow manager with Vertex AI integration
5. **vertex_ai_image_workflow.py** - Standalone Vertex AI image generation
6. **start_workflow_service.py** - Service management utility

### Key Directories

- **BilderVertex/** - Generated images destination (automatically created)
- **transkript.txt** - Speech recognition output (text)
- **transkript.json** - Speech recognition output (JSON with metadata)

## Automatic Integration

### How Vertex AI Activation Works

1. **Recording Completion**: When `Aufnahme.py` finishes, the GUI creates a workflow trigger
2. **Service Activation**: `PythonServer.py` detects the trigger and starts the workflow
3. **Speech Recognition**: `voiceToGoogle.py` processes audio and creates `transkript.txt`
4. **Automatic Vertex AI**: Immediately after successful transcription, the text is sent to Vertex AI
5. **Image Storage**: Generated images are saved to `BilderVertex/` with automatic naming
6. **GUI Update**: The slideshow GUI automatically displays new images

### Workflow Trigger Mechanism

```python
# After recording stops, GUI creates:
workflow_trigger.txt  # Contains "run" 

# PythonServer.py monitors for this file and executes:
# 1. Speech Recognition
# 2. Vertex AI Image Generation (automatic)
# 3. Cleanup trigger file
```

## Error Handling & Logging

### Centralized Error Handling

The workflow includes robust error handling for:
- **Vertex API failures** - Falls back to demo images, logs specific error codes
- **Image storage errors** - Directory creation, file permissions, disk space
- **Speech recognition failures** - Google API issues, audio format problems
- **Network connectivity** - Timeout handling, retry logic

### Logging

```
workflow_status.log     # Main workflow status and errors
recording_debug.log     # Recording process details  
speech_recognition.log  # Speech-to-text processing
```

### Error Recovery

```python
# Vertex AI error handling example
try:
    # Real Vertex AI API call
    response = requests.post(ENDPOINT, ...)
    if response.status_code != 200:
        # Log specific error
        log(f"Vertex AI API error: HTTP {response.status_code}", "ERROR")
        # Fall back to demo images
        return _create_demo_images(...)
except Exception as e:
    log(f"Vertex AI integration failed: {e}", "ERROR")
    # Continue workflow with fallback
```

## File Integration Points

### Input Files
```
/home/pi/Desktop/v2_Tripple S/aufnahme.wav       # Audio recording
/home/pi/Desktop/v2_Tripple S/cloudKey.json      # Google Cloud credentials
```

### Output Files  
```
/home/pi/Desktop/v2_Tripple S/transkript.txt     # Transcribed text
/home/pi/Desktop/v2_Tripple S/BilderVertex/      # Generated images
    ├── bild_1.png
    ├── bild_2.png
    └── ...
```

### Configuration Files
```
image_meta.json         # Image metadata and settings
modes.json             # GUI slideshow modes
```

## Removed Legacy Components

The following files were removed during cleanup:

### Unused Scripts (Removed)
- `VideoPlayer.py` - Video playback unrelated to workflow
- `checkNewImageAvailable.py` - Old file monitoring
- `dateiKopieren.py` - Legacy file copying and clipboard operations  
- `programmSendFile.py` - Old SSH upload functionality
- `createImageAndSave.py` - Deprecated image creation
- `combine_audio_to_text.py` - Redundant audio processing
- `einfuegen.py`, `pixelZeiger.py` - Unclear legacy utilities

### Removed Files
- Chrome extension files (`.crx`, `.pem`)
- Desktop shortcut files (`_gitignore*.desktop`)
- Old log files and temporary data

### Removed Features
- Manual file copying operations
- SSH/server upload functionality  
- Simulation modes for file operations
- Legacy clipboard integration
- Deprecated KivyMD workflow remnants

## Dependencies

### Required Python Packages
```bash
pip install kivy kivymd google-cloud-speech google-cloud-aiplatform requests pyperclip
```

### System Requirements  
- Linux/Raspberry Pi OS
- Audio recording capability (ALSA/PulseAudio)
- Internet connection for Google Cloud APIs
- Google Cloud Project with Vertex AI API enabled

## Configuration

### Google Cloud Setup
1. Create Google Cloud Project
2. Enable Speech-to-Text and Vertex AI APIs
3. Create service account and download `cloudKey.json`  
4. Place `cloudKey.json` in `/home/pi/Desktop/v2_Tripple S/`

### Environment Variables
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/home/pi/Desktop/v2_Tripple S/cloudKey.json"
export PROJECT_ID="your-project-id"
```

## Usage

### GUI Mode
```bash
python3 main.py
```
- Click "Aufnahme" to start recording
- Recording automatically triggers speech recognition  
- Speech recognition automatically triggers Vertex AI
- Generated images appear in slideshow

### Service Mode  
```bash
python3 start_workflow_service.py
```
- Runs background workflow manager
- Monitors for trigger files from GUI
- Processes recordings automatically

### Testing
```bash
python3 test_end_to_end_workflow.py
```
- Tests complete workflow simulation
- Validates directory structure
- Checks error handling

## Troubleshooting

### Common Issues

1. **No images generated**
   - Check `cloudKey.json` exists and is valid
   - Verify Google Cloud billing is enabled
   - Check `workflow_status.log` for Vertex AI errors

2. **Speech recognition fails**  
   - Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set
   - Check audio file format (should be mono WAV)
   - Verify internet connectivity

3. **Recording not working**
   - Install audio tools: `apt-get install alsa-utils pulseaudio`
   - Check microphone permissions
   - Test with: `arecord -l`

### Log Analysis
```bash
# Check workflow status
tail -f workflow_status.log

# Check recording issues  
tail -f recording_debug.log

# Check speech recognition
tail -f speech_recognition.log
```

## API Integration Details

### Vertex AI Request Formats

#### Text-Only Request (Traditional)
```json
{
  "prompt": "transcript text from transkript.txt"
}
```

#### Multimodal Request (Text + Image)
When `image_base64` field is present in `transkript.json`, the system automatically builds a Gemini multimodal request:
```json
{
  "instances": [{
    "prompt": "transcript text from transkript.json",
    "image": {
      "inline_data": {
        "mime_type": "image/png",
        "data": "base64-encoded-image-data"
      }
    }
  }],
  "parameters": {
    "sampleCount": 1,
    "aspectRatio": "16:9", 
    "resolution": "2k"
  }
}
```

#### Transkript.json Format with Image Support
```json
{
  "transcript": "Your transcribed text or prompt here",
  "timestamp": 1234567890.123,
  "iso_timestamp": "2023-12-01 14:30:45",
  "processing_method": "google_speech_api",
  "audio_source": "/home/pi/Desktop/v2_Tripple S/aufnahme.wav",
  "workflow_step": "transcription_complete",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgA...",
  "image_filename": "selected_image.png",
  "image_timestamp": "20231201_143045"
}
```

**Requirements for Multimodal Support:**
- Vertex AI Generative AI API (Gemini) must be activated in Google Cloud
- Valid Google Cloud credentials with Vertex AI permissions
- Image files must be valid and under 10MB
- Supported formats: PNG, JPG, JPEG, GIF, BMP

### Response Handling
```python
# Success: Save base64 image data to BilderVertex/
# Error: Log specific error code and fall back to demo images
# Timeout: Retry with exponential backoff
# Invalid Image: Fall back to text-only request
```

## Development

### Adding New Features
1. Follow the existing error handling patterns
2. Add comprehensive logging for new components  
3. Update tests in `test_end_to_end_workflow.py`
4. Document new configuration requirements

### Code Style
- Use descriptive logging with appropriate levels (INFO, WARNING, ERROR)
- Handle exceptions gracefully with fallbacks
- Maintain backwards compatibility where possible
- Keep functions focused and testable

This cleaned workflow provides a robust, minimal foundation for audio-to-image generation with proper error handling and automatic integration.