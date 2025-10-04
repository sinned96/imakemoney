# Visual Guide: 9:16 Mode Fixes

## Button Text Rotation

### Before Fix (Text was sideways):
```
┌────┐
│    │
│ Z  │
│ e  │
│ i  │   -90° rotation
│ t  │   Text reads right-to-left
│ e  │   (sideways)
│ n  │
│    │
└────┘
```

### After Fix (Text reads bottom-to-top):
```
┌────┐
│    │
│ n  │
│ e  │
│ t  │   180° rotation
│ i  │   Text reads bottom-to-top
│ e  │   (upside down but readable
│ Z  │    when viewing from bottom)
│    │
└────┘
```

## Layout Comparison

### 9:16 Mode (Portrait)

#### Before Fix:
```
┌──────────────────┐
│                  │
│  Image overlaps  │ ← Image used full width
│  with toolbar!   │   including toolbar area
│                  │
│  WHITE BARS  ┌─┐ │
│  VISIBLE     │T│ │ ← Toolbar 110px
│              │o│ │
│              │o│ │
└──────────────┴─┘─┘
     Issue: White background visible
     Issue: Image not centered properly
```

#### After Fix:
```
┌──────────────┬───┐
│              │   │
│   IMAGE      │ Z │ ← Toolbar 110px
│   FILLS      │ e │   (text rotated 180°)
│   CONTENT    │ i │
│   AREA       │ t │
│   PERFECTLY  │ e │
│              │ n │
└──────────────┴───┘
Content area: width - 110px
Image: Centered in content area
No white bars, no overlap
```

### 16:9 Mode (Landscape)

#### Layout (Unchanged):
```
┌─────────────────────────────┐
│                             │
│   IMAGE FILLS UPPER AREA    │
│   (height - 60px)           │
│                             │
├─────────────────────────────┤
│ [Zeiten] [Aufnahme] [Exit]  │ ← Toolbar 60px
└─────────────────────────────┘
Content area: height - 60px
Toolbar: Bottom, horizontal text
```

## Content Area Calculation

### 9:16 Mode:
```python
# Available space for image
content_x = 0                    # Start at left edge
content_y = 0                    # Start at bottom
content_w = window_width - 110   # Subtract toolbar width
content_h = window_height        # Full height

# Example with 720x1280 window:
# content_area = (0, 0, 610, 1280)
# toolbar_area = (610, 0, 110, 1280)
```

### 16:9 Mode:
```python
# Available space for image
content_x = 0                    # Start at left edge
content_y = 60                   # Start above toolbar
content_w = window_width         # Full width
content_h = window_height - 60   # Subtract toolbar height

# Example with 1280x720 window:
# content_area = (0, 60, 1280, 660)
# toolbar_area = (0, 0, 1280, 60)
```

## Image Scaling

### Cover Mode (Default):
```
Texture: 1080 x 1920 (9:16 image)
Content: 610 x 1280 (9:16 mode content area)

ratio_w = 610 / 1080 = 0.565
ratio_h = 1280 / 1920 = 0.667

scale = max(0.565, 0.667) = 0.667  ← Use height ratio

final_width = 1080 * 0.667 = 720px
final_height = 1920 * 0.667 = 1280px

Position: Center horizontally
x = (610 - 720) / 2 = -55  ← Image extends beyond left/right
y = (1280 - 1280) / 2 = 0

Result: Image fills height perfectly,
        sides are cropped (no white bars)
```

## Toolbar Button Structure

### Horizontal (16:9 Mode):
```
┌───────────────────────────────────────────────┐
│ [Button 1] [Button 2] [Button 3] ... [Exit]  │
│  110px       110px       110px        110px   │
└───────────────────────────────────────────────┘
     60px height
```

### Vertical (9:16 Mode):
```
┌─────┐
│  n  │ ← 180° rotated
│  e  │
│  t  │
│  i  │
│  e  │
│  Z  │
├─────┤ 60px per button
│  e  │
│  m  │
│  h  │
│  a  │
│  n  │
│  f  │
│  u  │
│  A  │
├─────┤
│ ... │
└─────┘
 110px
 width
```

## Image Widget Configuration

### Before:
```python
Image(opacity=1, color=(1,1,1,1))
```
- allow_stretch: False (default) → Image won't scale
- keep_ratio: True (default) → Aspect ratio preserved
- Result: White background visible when image smaller than widget

### After:
```python
Image(opacity=1, color=(1,1,1,1), 
      allow_stretch=True,    # Allow scaling
      keep_ratio=False)      # Manual control in _resize_image
```
- Image fills the size we set in _resize_image
- No white background visible
- Manual aspect ratio control for "cover" mode

## Debug Output Example

### 9:16 Mode:
```
[INFO] Applying layout for aspect ratio: 9:16, window size: 720x1280
[INFO] Created vertical toolbar for 9:16 mode
[DEBUG] 9:16 mode: window=720x1280, toolbar_width=110, content=610x1280
[DEBUG] cover mode: texture=1080x1920, scale=0.67, 
        img size=720x1280, pos=(-55,0)
```

### 16:9 Mode:
```
[INFO] Applying layout for aspect ratio: 16:9, window size: 1280x720
[INFO] Created horizontal toolbar for 16:9 mode
[DEBUG] 16:9 mode: window=1280x720, toolbar_height=60, content=1280x660
[DEBUG] cover mode: texture=1920x1080, scale=0.67, 
        img size=1280x720, pos=(0,-30)
```

## Key Points

### ✅ What Was Fixed:
1. **Text Rotation**: 180° instead of -90° for bottom-to-top readability
2. **Content Area**: Properly calculated excluding toolbar
3. **Image Positioning**: Centered in content area, not full window
4. **Image Stretching**: Enabled to prevent white backgrounds
5. **Layout Updates**: Images repositioned when switching modes

### ✅ What Stayed the Same:
1. **16:9 Mode**: Toolbar at bottom, horizontal text
2. **Image Scale Mode**: "cover" (fills content area)
3. **Background Color**: Dark (0.02, 0.02, 0.03)
4. **Toolbar Positioning**: FloatLayout with pos_hint
5. **Image Generation**: Already correct in vertex_ai_image_workflow.py

### 🔍 How to Verify:
1. Switch to 9:16 mode
2. Read button text from bottom to top ✓
3. Verify no white bars around images ✓
4. Check image is centered in left area ✓
5. Verify toolbar doesn't overlap image ✓
6. Switch to 16:9 mode
7. Verify toolbar at bottom, text normal ✓
8. Check images fill upper area correctly ✓

## Testing Commands

### Check syntax:
```bash
python3 -m py_compile main.py
```

### View logs:
```bash
tail -f /home/pi/Desktop/v2_Tripple\ S/projekt.log
```

### Filter image resize logs:
```bash
grep "mode:" /home/pi/Desktop/v2_Tripple\ S/projekt.log
```

### Check layout changes:
```bash
grep "Applying layout" /home/pi/Desktop/v2_Tripple\ S/projekt.log
```
