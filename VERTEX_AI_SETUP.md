# Vertex AI Integration Setup Guide

This document explains how to set up and configure the Vertex AI image generation feature in the recording workflow.

## Overview

The workflow now includes automatic image generation using Google's Vertex AI Imagen API:

1. **Recording** → `Aufnahme.py` creates audio file
2. **Transcription** → `voiceToGoogle.py` converts speech to text
3. **Upload** → `programmSendFile.py` uploads audio to server
4. **File Operations** → `dateiKopieren.py` organizes files
5. **Image Generation** → Transcript is sent to Vertex AI for image creation ✨

## Current Status: ✅ WORKING

The integration has been fixed and tested. It will work in **demo mode** without Google Cloud setup, or in **production mode** with proper credentials.

## Quick Test

Run the integration test to verify everything works:

```bash
python3 test_vertex_ai_integration.py
```

This will test the complete workflow including transcript reading and image generation (in demo mode).

## Production Setup (Optional)

To use real Vertex AI instead of demo mode, follow these steps:

### 1. Google Cloud Prerequisites

- Google Cloud Project with billing enabled
- Vertex AI API enabled
- Service account with appropriate permissions

### 2. Enable Vertex AI API

```bash
# Using gcloud CLI
gcloud services enable aiplatform.googleapis.com
```

Or via [Google Cloud Console](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com).

### 3. Create Service Account

1. Go to [Google Cloud Console → IAM & Admin → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Create a service account with the following roles:
   - **Vertex AI User** (`roles/aiplatform.user`)
   - **Storage Object Admin** (if using Cloud Storage)

### 4. Download Credentials

1. Create a JSON key for your service account
2. Save it as `/home/pi/Desktop/v2_Tripple S/cloudKey.json`
3. Verify the file path in `PythonServer.py` (variable `GOOGLE_CREDENTIALS`)

### 5. Install Dependencies

```bash
# Required for Vertex AI
pip install google-cloud-aiplatform google-auth

# Optional (already handled gracefully if missing)
pip install pyperclip requests
```

### 6. Set Environment Variables

```bash
# For speech recognition (if different from cloudKey.json)
export GOOGLE_APPLICATION_CREDENTIALS="/home/pi/Desktop/v2_Tripple S/cloudKey.json"

# Optional: Override project ID
export PROJECT_ID="your-project-id"
```

## Configuration

### File Paths

The workflow uses standardized paths in `/home/pi/Desktop/v2_Tripple S/`:

- `aufnahme.wav` - Audio recording
- `transkript.txt` - Plain text transcript  
- `transkript.json` - JSON transcript with metadata
- `cloudKey.json` - Google Cloud credentials
- `BilderVertex/` - Generated images directory

### Vertex AI Settings

Edit `PythonServer.py` to customize image generation:

```python
# In generate_image_imagen4 function
payload = {
    "instances": [{"prompt": prompt}],
    "parameters": {
        "sampleCount": 1,           # Number of images
        "aspectRatio": "16:9",      # Aspect ratio
        "resolution": "2k"          # Resolution
    }
}
```

## Workflow Integration

### Automatic Mode (Recommended)

The image generation happens automatically after recording:

1. Start recording via GUI (main.py)
2. Stop recording 
3. Workflow automatically processes: Transcription → Upload → Image Generation
4. Check `BilderVertex/` directory for generated images

### Manual Mode

You can also generate images manually:

```python
from PythonServer import generate_image_imagen4

# Generate image from text
image_paths = generate_image_imagen4(
    prompt="A beautiful landscape with mountains",
    image_count=2,
    bilder_dir="/path/to/BilderVertex",
    output_prefix="manual"
)

print(f"Generated images: {image_paths}")
```

## Troubleshooting

### Demo Mode (Expected in Test Environment)

If you see messages like:
```
Google Cloud libraries not available - using demo mode
Creating demo images as fallback...
```

This is normal and expected when:
- Google Cloud libraries are not installed
- Credentials are not configured
- Running in test/development environment

Demo mode creates placeholder images to test the workflow.

### Common Issues

#### Authentication Error
```
Authentication failed - check service account permissions
```
**Solution:** Verify your service account has the "Vertex AI User" role.

#### Permission Denied  
```
Permission denied - ensure Vertex AI API is enabled and billing is set up
```
**Solution:** 
1. Enable Vertex AI API in Google Cloud Console
2. Set up billing for your project
3. Verify service account permissions

#### Rate Limited
```
Rate limit exceeded - try again later
```
**Solution:** Vertex AI has usage quotas. Wait and try again, or request quota increase.

#### Network Error
```
Network error - check internet connection
```
**Solution:** Verify internet connectivity and firewall settings.

## Testing

### Integration Tests

```bash
# Full integration test
python3 test_vertex_ai_integration.py

# Test transcript reading only
python3 -c "from test_vertex_ai_integration import test_transcript_reading; test_transcript_reading()"

# Test image generation only  
python3 -c "from test_vertex_ai_integration import test_image_generation; test_image_generation()"
```

### Manual Verification

1. Create a test transcript:
   ```bash
   echo "Create a beautiful sunset landscape" > /tmp/transkript.txt
   ```

2. Run image generation:
   ```bash
   python3 -c "from PythonServer import generate_image_imagen4; generate_image_imagen4('Test prompt', bilder_dir='/tmp/test_images')"
   ```

3. Check results:
   ```bash
   ls -la /tmp/test_images/
   ```

## Monitoring

### Workflow Logs

The workflow creates detailed logs:
- `workflow_status.log` - Service status and progress
- `speech_recognition.log` - Transcription details
- Console output during execution

### Example Log Output

```
[INFO] === Vertex AI Image Generation ===
[INFO] Prompt: 'Create a beautiful landscape with mountains and a lake'
[INFO] Target directory: /home/pi/Desktop/v2_Tripple S/BilderVertex
[INFO] ✓ Authentication successful
[INFO] Sending request to Vertex AI Imagen API...
[INFO] ✓ Received response from Vertex AI API
[INFO] ✓ Image 1 saved: /home/pi/Desktop/v2_Tripple S/BilderVertex/bild_1.png (1,234,567 bytes)
[INFO] ✓ Vertex AI image generation completed: 1 images saved
```

## Cost Considerations

- **Vertex AI Imagen** charges per generated image
- **Typical cost:** ~$0.040 per image (check current pricing)
- **Free tier:** Limited credits for new Google Cloud accounts
- **Budget alerts:** Set up billing alerts to monitor usage

## API Limits

- **Rate limits:** ~10 requests per minute (varies by project)
- **Image size limits:** Managed automatically by the service
- **Prompt length:** Up to ~2000 characters

## Support

If you encounter issues:

1. Check the integration test: `python3 test_vertex_ai_integration.py`
2. Review logs for specific error messages
3. Verify Google Cloud setup (billing, API enabled, permissions)
4. Test with a simple prompt first

The integration is designed to be robust - if Vertex AI is not available, it will gracefully fall back to demo mode and continue the workflow.