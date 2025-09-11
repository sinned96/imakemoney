# Google Speech-to-Text Setup

## Requirements

This application uses Google Cloud Speech-to-Text API for converting audio recordings to text. Follow these steps to set up the integration:

### 1. Google Cloud Setup

1. Create a Google Cloud Project or use an existing one
2. Enable the Speech-to-Text API in the Google Cloud Console
3. Create a Service Account with Speech-to-Text permissions
4. Download the service account key as JSON file

### 2. Environment Setup

**Required Environment Variable:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/home/pi/meinprojekt-venv/cloudKey.json"
```

The application will automatically set this when running the workflow, but you can also set it manually for testing.

### 3. Install Dependencies

Install the Google Cloud Speech library:
```bash
pip install google-cloud-speech
```

### 4. Service Account Permissions

Your service account needs the following IAM roles:
- `roles/speechtotext.user` or `Speech-to-Text User`

### 5. Audio File Requirements

- **Location**: Audio files should be saved as `aufnahme.wav` in one of these locations:
  - `/home/pi/Desktop/v2_Tripple S/Aufnahmen/aufnahme.wav` (primary)
  - `Aufnahmen/aufnahme.wav` (local directory)
  - `aufnahme.wav` (current directory)
  
- **Format**: WAV format recommended (16-bit PCM, 44.1kHz sample rate)
- **Size**: Files up to 10MB for synchronous processing

## How It Works

1. **Audio Recording**: `Aufnahme.py` creates the audio file
2. **Speech Processing**: `voiceToGoogle.py` processes the audio:
   - Checks for Google credentials
   - Validates audio file
   - Sends to Google Speech-to-Text API
   - Falls back to simulation mode if API unavailable
3. **Output**: Creates `transkript.txt` and `transkript.json` with results

## Error Handling

The system includes comprehensive error logging:

- **Missing Credentials**: Clear instructions about setting `GOOGLE_APPLICATION_CREDENTIALS`
- **Network Issues**: Detailed error messages for API connectivity problems
- **Invalid Audio**: File validation and format checking
- **Library Missing**: Automatic fallback to simulation mode

## Logs

Speech recognition activity is logged to:
- `speech_recognition.log` - Detailed processing logs
- Console output - Real-time status updates

## Testing

The system will work in simulation mode even without Google Cloud setup, making it suitable for development and testing.

For production use with real speech recognition, ensure all requirements above are met.