# Google Speech-to-Text Setup and Workflow Documentation

## Complete Workflow Overview

This document describes the overhaul of the speech recording and Google Speech-to-Text integration workflow, with consistent path management and proper sequencing.

### Workflow Path Logic

**Base Directory**: All relevant files are now standardized to `/home/pi/Desktop/v2_Tripple S/`

**File Structure**:
```
/home/pi/Desktop/v2_Tripple S/
├── aufnahme.wav          # Audio recording (fixed filename, always overwritten)
├── transkript.txt        # Text transcript output
├── transkript.json       # JSON transcript with metadata (AI-ready)
├── cloudKey.json         # Google service account credentials
├── upload.log            # Upload operation logs
├── speech_recognition.log # Speech processing logs
└── BilderVertex/         # Generated images directory
```

### Workflow Sequence

The integration follows this exact sequence:

1. **Recording Phase** (`Aufnahme.py`)
   - Records audio to `/home/pi/Desktop/v2_Tripple S/aufnahme.wav`
   - Uses fixed filename, always overwrites previous recording
   - Stops cleanly on SIGTERM signal

2. **Transcription Phase** (`voiceToGoogle.py`) 
   - Processes `/home/pi/Desktop/v2_Tripple S/aufnahme.wav`
   - Uses Google Speech-to-Text API with credentials from `cloudKey.json`
   - Creates `transkript.txt` and `transkript.json` in same directory
   - Falls back to simulation mode if Google API unavailable

3. **Upload Phase** (`programmSendFile.py`)
   - Uploads `aufnahme.wav` to target server at `/home/server/XYZ/aufnahme.wav`  
   - Supports multiple transfer methods (SCP, rsync, SFTP)
   - Includes upload verification and comprehensive logging
   - Runs AFTER transcription is complete

4. **Processing Phase** (Optional)
   - File operations via `dateiKopieren.py`
   - AI image generation using transcript data
   - Additional processing workflows

## Requirements

### Google Cloud Setup

1. Create a Google Cloud Project or use an existing one
2. Enable the Speech-to-Text API in the Google Cloud Console
3. Create a Service Account with Speech-to-Text permissions:
   - Role: `roles/speechtotext.user` or `Speech-to-Text User`
4. Download the service account key as JSON file
5. Place the key file at `/home/pi/Desktop/v2_Tripple S/cloudKey.json`

### Environment Configuration

**Google Credentials**:
The system automatically uses the standardized path for credentials:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/home/pi/Desktop/v2_Tripple S/cloudKey.json"
```

**Server Upload Configuration**:
```bash
export UPLOAD_SERVER_HOST="your-server.example.com"
export UPLOAD_SERVER_USER="pi" 
export SSH_KEY_PATH="~/.ssh/id_rsa"
```

### Dependencies

Install required packages:
```bash
pip install google-cloud-speech
```

## Script Integration

### Main Integration Script (`PythonServer.py`)

The workflow manager ensures proper sequencing:

1. **Transcription First**: `voiceToGoogle.py` processes audio and creates transcript
2. **Upload Second**: `programmSendFile.py` transfers file to server
3. **Processing Last**: Additional operations and AI processing

### Error Handling

Each phase includes comprehensive error handling:

- **Missing Credentials**: Clear setup instructions
- **Network Issues**: Detailed connectivity diagnostics  
- **Invalid Audio**: File validation and format checking
- **Upload Failures**: Multiple transfer methods with fallback

## AI Integration Notes

### Transcript Export for Further Processing

The `transkript.json` file is structured for easy integration with AI services:

```json
{
  "transcript": "Your transcribed text here",
  "timestamp": 1234567890.123,
  "iso_timestamp": "2023-12-01 14:30:45",
  "processing_method": "google_speech_api",
  "audio_source": "/home/pi/Desktop/v2_Tripple S/aufnahme.wav",
  "workflow_step": "transcription_complete"
}
```

**Vertex AI Integration**: The transcript data is ready for:
- Content analysis and sentiment detection
- Text summarization and keyword extraction  
- Automated content generation workflows
- Multi-modal AI processing (text + audio analysis)

### Image Generation Pipeline

The workflow integrates with Vertex AI's Imagen model:
- Uses transcript text as generation prompt
- Saves generated images to `BilderVertex/` directory
- Supports batch processing and custom prompts

## Testing and Validation

### File Path Validation

All scripts validate the standardized file paths:
```bash
python3 -c "from pathlib import Path; print('✓ Path accessible' if Path('/home/pi/Desktop/v2_Tripple S').exists() else '✗ Path not found')"
```

### Workflow Testing

Test individual components:
```bash
# Test transcription (simulation mode)
python3 voiceToGoogle.py

# Test upload configuration  
python3 programmSendFile.py

# Test complete workflow
python3 PythonServer.py --service
```

## Troubleshooting

### Common Issues

1. **Path Not Found**: Ensure `/home/pi/Desktop/v2_Tripple S/` directory exists
2. **Credentials Error**: Verify `cloudKey.json` is present and valid
3. **Upload Failures**: Check SSH key configuration and server connectivity
4. **Audio Processing**: Ensure audio file is valid WAV format

### Log Files

Monitor workflow progress via log files:
- `speech_recognition.log` - Transcription process
- `upload.log` - Server upload operations  
- `workflow_status.log` - Overall workflow status

## Security Considerations

- Google credentials stored locally in `cloudKey.json`
- SSH key authentication for server uploads
- No sensitive data transmitted in logs
- Secure handling of audio content throughout workflow