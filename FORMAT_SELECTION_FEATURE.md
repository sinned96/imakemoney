# Format Selection Feature

## Overview
A new format selection feature has been added to the application that allows users to choose between horizontal (16:9) and vertical (9:16) aspect ratios for AI-generated images.

## Features

### 1. Format Selection Button
- **Location**: Added to the toolbar between "Aufnahme" (Recording) and "Galerie" (Gallery)
- **Icon**: Uses `aspect-ratio` icon in KivyMD toolbar
- **Label**: "Format" in custom toolbar

### 2. Format Selection Popup
When clicking the "Format" button, a popup window appears with:
- Current aspect ratio display
- "Horizontal (16:9)" button
- "Vertikal (9:16)" button
- Close button

### 3. Aspect Ratio Configuration
- **Storage**: Aspect ratio preference is saved in `image_meta.json`
- **Default**: 16:9 (horizontal)
- **Persistence**: Selection is preserved across app restarts
- **Feedback**: Visual feedback when selecting a format (green highlight)

### 4. AI Image Generation Integration
- The selected aspect ratio is automatically applied to all new AI image generation requests
- Images generated via Vertex AI Imagen 4.0 API will use the selected aspect ratio
- The aspect ratio is read from `image_meta.json` during workflow execution

## Technical Implementation

### Changes to `main.py`

#### 1. Configuration Storage
```python
# Added aspect_ratio to metadata
def load_image_meta():
    base = {..., "aspect_ratio": "16:9"}
    ...

# Store aspect_ratio in Slideshow class
self.aspect_ratio = meta.get("aspect_ratio", "16:9")

# Persist aspect_ratio
def persist_meta(self):
    meta = {..., "aspect_ratio": self.aspect_ratio}
    ...
```

#### 2. FormatSelectionPopup Class
A new popup class with:
- Clean UI design matching existing popups
- Two main buttons for format selection
- Real-time feedback when selecting
- Automatic persistence of selection

#### 3. Toolbar Integration
```python
# Added Format button to both toolbar types
def _update_md_toolbar_buttons(self, bar):
    bar.right_action_items=[
        ...,
        ["aspect-ratio", lambda x: self.open_format_selection()],
        ...
    ]

def _update_toolbar_buttons(self, bar):
    bar.set_right_actions([
        ...,
        ("Format", self.open_format_selection),
        ...
    ])
```

### Changes to `PythonServer.py`

#### 1. Function Signature Update
```python
def generate_image_imagen4(prompt, image_count=1, bilder_dir=BILDER_DIR, 
                          output_prefix="bild", logger=None, aspect_ratio="16:9"):
    ...
```

#### 2. API Payload Update
```python
payload = {
    "instances": [{"prompt": prompt}],
    "parameters": {
        "sampleCount": image_count,
        "aspectRatio": aspect_ratio,  # Now uses the parameter
        "resolution": "2k"
    }
}
```

#### 3. Workflow Integration
```python
# In execute_workflow method
# Read aspect ratio from image_meta.json
aspect_ratio = "16:9"  # Default
try:
    meta_path = self.work_dir / "image_meta.json"
    if meta_path.exists():
        import json
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
            aspect_ratio = meta_data.get("aspect_ratio", "16:9")
except Exception as e:
    # Fall back to default
    ...

# Pass to image generation
image_paths = generate_image_imagen4(
    prompt_text, 
    image_count=1, 
    bilder_dir=str(bilder_dir_path), 
    output_prefix="bild",
    logger=self.log_status,
    aspect_ratio=aspect_ratio  # Applied here
)
```

## User Experience

### How to Use
1. Open the application
2. Click on the "Format" button in the toolbar (between "Aufnahme" and "Galerie")
3. Select either:
   - "Horizontal (16:9)" for landscape images
   - "Vertikal (9:16)" for portrait images
4. The selection is saved automatically
5. Close the popup
6. All new AI-generated images will use the selected aspect ratio

### Visual Feedback
- Current aspect ratio is displayed in the popup
- Selected format briefly highlights in green
- Selection persists across sessions

## Testing

A comprehensive test suite has been added in `test_format_selection.py`:

### Test Coverage
1. **Aspect Ratio Storage**: Verifies JSON persistence
2. **API Parameter**: Confirms aspect_ratio parameter in generate_image_imagen4
3. **Popup Class**: Validates FormatSelectionPopup structure
4. **Toolbar Integration**: Checks button configuration

### Running Tests
```bash
python3 test_format_selection.py
```

All tests pass successfully ✅

## Layout Consistency

### Design Principles
- Popup follows existing design patterns (ScheduleEditor, GeneralSettingsPopup)
- Button placement maintains existing toolbar order
- No changes to bottom menu structure
- Consistent with app color scheme and styling

### Menu Structure (After Changes)
```
[Zeiten] [Aufnahme] [Format] [Galerie] [Einstellungen] [Logout] [Exit]
```

## Configuration File

### image_meta.json Structure
```json
{
  "effects": {},
  "intervals": {},
  "weights": {},
  "brightness": {},
  "global_interval": null,
  "global_brightness": null,
  "aspect_ratio": "16:9"
}
```

## Compatibility

### Vertex AI API
- The Imagen 4.0 API supports both 16:9 and 9:16 aspect ratios
- No additional configuration needed on Google Cloud side
- Aspect ratio is specified in the API payload parameters

### Demo Mode
- Demo mode (when Google Cloud is unavailable) will also respect the aspect ratio setting
- Placeholder images maintain the selected aspect ratio

## Future Enhancements

Possible improvements:
- Add more aspect ratio options (1:1, 4:3, etc.)
- Preview of aspect ratio before selection
- Automatic aspect ratio detection based on content
- Per-mode aspect ratio settings

## Summary

This feature provides users with complete control over the aspect ratio of AI-generated images, with minimal code changes and seamless integration into the existing workflow. The implementation follows the app's architectural patterns and maintains consistency with the existing UI/UX design.
