# Fix Summary: 9:16 Mode Display Issues

## Overview
This fix addresses multiple display and layout issues in the 9:16 (portrait) mode while maintaining the existing 16:9 (landscape) mode functionality.

## Problem Statement (German)
1. Im 9:16-Modus wird das Google-Bild zwar hochkant erzeugt, aber nicht korrekt als 9:16 angezeigt
2. Im 9:16-Modus ist nach Aufnahme/Einfügen immer noch ein weißer Hintergrund
3. Die Menüleiste im 9:16-Modus: Drehe den Text der Buttons um 180°, damit alles von unten nach oben (richtig lesbar) angezeigt wird
4. Im 16:9-Modus bleibt alles wie gehabt, Menüleiste immer unten
5. Fixe das Layout und die Bilddarstellung

## Solutions Implemented

### 1. Button Text Rotation (VerticalButton class)
**File:** `main.py` line 612
**Change:** Rotation angle changed from `-90°` to `180°`

**Why:** 
- `-90°` rotates text 90° clockwise, making it read sideways (right to left)
- `180°` rotates text upside down, making it readable from bottom to top

**Code:**
```python
# Before:
Rotate(angle=-90, origin=self.center)  # 90° clockwise

# After:
Rotate(angle=180, origin=self.center)  # 180° - readable from bottom to top
```

### 2. Image Widget Configuration
**File:** `main.py` lines 2983-2984
**Change:** Added `allow_stretch=True` and `keep_ratio=False` to Image widgets

**Why:**
- Default Image widget behavior doesn't stretch textures
- Without stretching, images may show background (white) when smaller than widget
- `allow_stretch=True` allows image to fill widget size
- `keep_ratio=False` allows manual control of sizing in `_resize_image`

**Code:**
```python
# Before:
self.img_a = Image(opacity=1, color=(1,1,1,1))
self.img_b = Image(opacity=0, color=(1,1,1,1))

# After:
self.img_a = Image(opacity=1, color=(1,1,1,1), allow_stretch=True, keep_ratio=False)
self.img_b = Image(opacity=0, color=(1,1,1,1), allow_stretch=True, keep_ratio=False)
```

### 3. Content Area Calculation (_resize_image method)
**File:** `main.py` lines 3092-3142
**Change:** Complete rewrite to account for toolbar space

**Why:**
- Original code used full window dimensions
- Toolbar overlaps with content in FloatLayout
- Images need to be positioned in the remaining space

**Logic:**

#### 9:16 Mode (Portrait):
```
┌──────────────┬────┐
│              │ T  │
│   Content    │ o  │  Toolbar on right side (110px wide)
│   Area       │ o  │  Content uses remaining width
│              │ l  │
└──────────────┴────┘
```
- Content area: `(0, 0, width - toolbar_width, height)`
- Toolbar width: 110px (dp)
- Images centered horizontally in remaining space

#### 16:9 Mode (Landscape):
```
┌─────────────────────┐
│                     │
│   Content Area      │  Content uses upper area
│                     │
├─────────────────────┤
│     Toolbar         │  Toolbar at bottom (60px high)
└─────────────────────┘
```
- Content area: `(0, toolbar_height, width, height - toolbar_height)`
- Toolbar height: 60px (dp)
- Images centered vertically in remaining space

**Key Code Changes:**
```python
# Calculate content area
content_x = 0
content_y = 0
content_w = self.width
content_h = self.height

if self.aspect_ratio == "9:16":
    toolbar_width = self.toolbar.width or dp(110)
    content_w = self.width - toolbar_width
    # Content starts at x=0, toolbar on right
    
elif self.aspect_ratio == "16:9":
    toolbar_height = self.toolbar.height or dp(60)
    content_h = self.height - toolbar_height
    content_y = toolbar_height
    # Content starts above toolbar

# Scale and position image in content area
ratio_w = content_w / tex_w
ratio_h = content_h / tex_h
scale = max(ratio_w, ratio_h)  # Cover mode
new_w = tex_w * scale
new_h = tex_h * scale
img_widget.size = (new_w, new_h)
img_widget.pos = (content_x + (content_w - new_w) / 2, 
                  content_y + (content_h - new_h) / 2)
```

### 4. Layout Application Enhancement (_apply_layout method)
**File:** `main.py` lines 3044-3078
**Change:** Added image resize trigger and debug logging

**Why:**
- When switching modes, images need to be repositioned
- Debug logging helps identify layout issues

**Code:**
```python
def _apply_layout(self):
    debug_logger.info(f"Applying layout for aspect ratio: {self.aspect_ratio}")
    
    # ... create toolbar for current mode ...
    
    # Force resize of current images after layout change
    if hasattr(self, 'img_a') and self.img_a:
        self._resize_image(self.img_a)
    if hasattr(self, 'img_b') and self.img_b:
        self._resize_image(self.img_b)
```

## Debug Logging
All changes include comprehensive debug logging to `projekt.log`:

- Window dimensions
- Content area calculations
- Toolbar dimensions
- Image texture size
- Scale factors
- Final image size and position
- Layout application events

## Testing Checklist

### Visual Tests:
- [ ] 9:16 mode: Button text reads from bottom to top
- [ ] 9:16 mode: Images fill content area (left side) without white borders
- [ ] 9:16 mode: Images are centered in content area
- [ ] 9:16 mode: No overlap between images and toolbar
- [ ] 16:9 mode: Button text reads normally (left to right)
- [ ] 16:9 mode: Images fill content area (upper area) without white borders
- [ ] 16:9 mode: Images are centered in content area
- [ ] 16:9 mode: No overlap between images and toolbar

### Functional Tests:
- [ ] Switch from 16:9 to 9:16: Images reposition correctly
- [ ] Switch from 9:16 to 16:9: Images reposition correctly
- [ ] Load new image in 9:16 mode: Displays correctly
- [ ] Load new image in 16:9 mode: Displays correctly
- [ ] Google-generated images: Display correctly in both modes
- [ ] Imported images: Display correctly in both modes

### Log Tests:
- [ ] Check projekt.log for dimension calculations
- [ ] Verify content area calculations are correct
- [ ] Verify no error messages related to image display

## Background Information

### Image Scale Modes
The application uses `IMAGE_SCALE_MODE = "cover"` which means:
- Images are scaled to fill the entire content area
- Aspect ratio is preserved
- Parts of the image may be cropped if aspect ratios don't match
- No white/black borders appear

Alternative would be "contain" mode:
- Images fit entirely within content area
- Aspect ratio preserved
- No cropping
- Black bars may appear

### Window Sizes
Default window sizes when not in fullscreen:
- 16:9 mode: 1280 x 720 pixels
- 9:16 mode: 720 x 1280 pixels

### Toolbar Dimensions
- Horizontal toolbar (16:9 mode): 60px height
- Vertical toolbar (9:16 mode): 110px width

### Image Generation
The vertex_ai_image_workflow.py already handles aspect ratio correctly:
- Reads aspect_ratio from image_meta.json
- Generates 1920x1080 for 16:9
- Generates 1080x1920 for 9:16
- Uses ImageOps.fit to maintain aspect ratio

## Files Modified
1. `main.py` - All display and layout fixes

## Files Not Modified (but relevant)
- `vertex_ai_image_workflow.py` - Image generation already correct
- `image_meta.json` - Stores current aspect_ratio setting
- `modes.json` - Mode configuration

## Commits
1. Initial plan
2. Fix 9:16 mode: rotate text 180°, adjust image resize for toolbar, enable image stretching
3. Fix image positioning to account for toolbar location in both 9:16 and 16:9 modes
4. Add debug logging for image resize and layout changes

## Author
GitHub Copilot Agent
Co-authored-by: sinned96
