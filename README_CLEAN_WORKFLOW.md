# Clean Vertex AI Integration Workflow

## Overview

This project now provides a clean, minimal, and robust integration between speech recognition and Vertex AI image generation. The workflow has been streamlined to remove unnecessary external dependencies and focus on the core functionality.

## Streamlined Workflow

The clean workflow consists of only 3 essential steps:

1. **Audio Recording** → `Aufnahme.py` creates audio file
2. **Speech Recognition** → `voiceToGoogle.py` converts speech to text  
3. **File Operations** → `dateiKopieren.py` manages local files
4. **AI Image Generation** → Vertex AI automatically generates images from transcript

## Key Improvements

### ✅ Removed Deprecated Components
- **SSH Upload Scripts**: Removed `programmSendFile.py` and all server upload functionality
- **External Dependencies**: No more SSH keys, server configurations, or external uploads needed
- **Simulation Mode Warnings**: Cleaned up fallback messaging to be more professional
- **Deprecated References**: Updated all documentation to reflect the clean workflow

### ✅ Enhanced Vertex AI Integration
- **Transparent Configuration**: Clear documentation of API keys, prompts, and error handling
- **Robust Error Handling**: Graceful fallback to demo mode when Google Cloud unavailable
- **Professional Logging**: Clean, informative status messages and workflow tracking
- **Minimal Dependencies**: Only essential packages required for core functionality

### ✅ Consistent File Structure
All files are now centralized in `/home/pi/Desktop/v2_Tripple S/`:
```
├── aufnahme.wav          # Audio recording
├── transkript.txt        # Text transcript
├── transkript.json       # JSON transcript with metadata (AI-ready)
├── cloudKey.json         # Google Cloud credentials
├── speech_recognition.log # Processing logs
└── BilderVertex/         # Generated images directory
```

## Usage

### Quick Start (Service Mode)
```bash
python3 start_workflow_service.py
```

### Manual Execution
```bash
python3 Aufnahme.py        # Record audio
python3 voiceToGoogle.py   # Speech to text
python3 dateiKopieren.py   # File operations
# Image generation happens automatically in workflow
```

### Testing
```bash
python3 test_vertex_ai_integration.py  # Test Vertex AI integration
python3 test_end_to_end_workflow.py    # Test complete workflow
```

## Production Setup (Optional)

For real Vertex AI (instead of demo mode):

1. **Install Dependencies**:
   ```bash
   pip install google-cloud-aiplatform google-auth requests
   pip install google-cloud-speech  # For speech recognition
   ```

2. **Google Cloud Setup**:
   - Create Google Cloud Project with billing enabled
   - Enable Vertex AI API and Speech-to-Text API  
   - Create service account with "Vertex AI User" role
   - Download JSON key to `/home/pi/Desktop/v2_Tripple S/cloudKey.json`

3. **Configuration**:
   ```bash
   export PROJECT_ID="your-project-id"
   export GOOGLE_APPLICATION_CREDENTIALS="/home/pi/Desktop/v2_Tripple S/cloudKey.json"
   ```

## Demo Mode

When Google Cloud is not configured, the system automatically runs in demo mode:
- **Speech Recognition**: Uses fallback processing for transcript generation
- **Image Generation**: Creates placeholder images to test the workflow
- **Full Functionality**: All components work end-to-end for development/testing

## Vertex AI Configuration

The image generation is transparently configured:
- **Model**: Imagen 4.0 (latest)
- **Resolution**: 2k
- **Aspect Ratio**: 16:9
- **Region**: us-central1
- **Error Handling**: Automatic fallback to demo images

## Key Features

- ✅ **Minimal Setup**: Works out-of-the-box in demo mode
- ✅ **No External Servers**: All processing happens locally
- ✅ **Robust Fallbacks**: Graceful degradation when APIs unavailable  
- ✅ **Clear Logging**: Transparent workflow status and error messages
- ✅ **Professional Output**: Clean generated images saved to `BilderVertex/`
- ✅ **Test Coverage**: Comprehensive test suite validates all components

This clean implementation focuses solely on the core workflow: Speech → AI → Images, with no unnecessary complexity or external dependencies.