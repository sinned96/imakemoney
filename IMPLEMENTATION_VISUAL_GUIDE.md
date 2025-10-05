# Visual Guide: Portrait/Landscape Implementation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Slideshow (FloatLayout)                  │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │              Orientation Detection                 │   │
│  │   aspect_ratio = image_meta.json["aspect_ratio"]   │   │
│  │         (User-selectable: "16:9" or "9:16")        │   │
│  └────────────────────────────────────────────────────┘   │
│                         │                                   │
│                         ├──────────────┬────────────────┐  │
│                         │              │                │  │
│                  ┌──────▼─────┐ ┌─────▼────┐  ┌───────▼──┐│
│                  │  16:9 Mode │ │ 9:16 Mode│  │ Popups  ││
│                  │ (Landscape)│ │(Portrait)│  │(Both OK)││
│                  └────────────┘ └──────────┘  └─────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Layout Comparison

### 16:9 Mode (Landscape)
```
┌─────────────────────────────────────────────┐
│                                             │
│                                             │
│           Content Area                      │
│        (Images displayed here)              │
│                                             │
│                                             │
│                                             │
├─────────────────────────────────────────────┤
│  [Zeiten] [Aufnahme] [Format] [Galerie]... │ ← Toolbar (60dp height)
└─────────────────────────────────────────────┘
   ↑
   └─ Horizontal buttons, normal text orientation
```

**Characteristics:**
- Toolbar: `pos_hint={"bottom": 1}`, horizontal orientation
- Content area: Full width, `height - toolbar_height`
- Images: Centered, scaled to 1920×1080
- Text: Normal horizontal orientation

### 9:16 Mode (Portrait)
```
┌──────────────────────────┬───┐
│                          │ Z │
│                          │ e │
│                          │ i │
│      Content Area        │ t │
│   (Images displayed)     │ e │
│                          │ n │
│                          ├───┤
│                          │ A │
│                          │ u │
│                          │ f │
│                          │ n │
│                          │ a │
│                          │ h │
└──────────────────────────┴───┘
                             ↑
                             └─ Toolbar (110dp width)
                                VerticalButton with 270° rotation
                                Text readable top-to-bottom
```

**Characteristics:**
- Toolbar: `pos_hint={"right": 1, "top": 1}`, vertical orientation
- Content area: `width - toolbar_width`, full height
- Images: Centered, scaled to 1080×1920
- Text: Rotated 270° (clockwise 90°) for natural top-to-bottom reading

## Component Deep Dive

### VerticalButton Class

```python
class VerticalButton(Button):
    def __init__(self, rotation_angle=270, **kwargs):
        super().__init__(**kwargs)
        self.rotation_angle = rotation_angle
        self.padding = [dp(10), dp(5)]  # Prevent clipping
        
    def _update_rotation(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            PushMatrix()
            Rotate(angle=self.rotation_angle, origin=self.center)
        
        self.canvas.after.clear()
        with self.canvas.after:
            PopMatrix()
```

**Rotation Angle Explained:**
```
       0° (Normal)          90° (Right)         180° (Upside)       270° (Left)
     ┌──────────┐         ┌──────┐            ┌──────────┐         ┌──────┐
     │  Button  │         │      │            │  nottᴜB  │         │      │
     │  Text    │         │Text B│            │  txeT    │         │B txeT│
     └──────────┘         │      │            └──────────┘         │      │
                          │utton │                                 │      │
                          └──────┘                                 │nottuB│
                                                                   └──────┘
                          ↑ Natural reading                        ↑ Natural reading
                            from bottom                              from top
```

We use **270°** for portrait mode because:
- Text flows naturally from TOP to BOTTOM
- Matches natural reading direction when screen is vertical
- Text is parallel to screen edge
- With toolbar on right, text reads down the right side

### Image Widget Configuration

```python
# Kivy 2.3+ aware implementation
import kivy
kivy_version = tuple(map(int, kivy.__version__.split('.')[:2]))

if kivy_version >= (2, 3):
    # Modern API: fit_mode replaces deprecated properties
    self.img_a = Image(opacity=1, color=(1,1,1,1), fit_mode='cover')
    self.img_b = Image(opacity=0, color=(1,1,1,1), fit_mode='cover')
else:
    # Legacy API: for older Kivy versions
    self.img_a = Image(opacity=1, color=(1,1,1,1), 
                       allow_stretch=True, keep_ratio=True)
    self.img_b = Image(opacity=0, color=(1,1,1,1), 
                       allow_stretch=True, keep_ratio=True)
```

**Benefits of fit_mode='cover':**
- ✅ No white backgrounds
- ✅ Proper aspect ratio preservation
- ✅ Automatic centering
- ✅ Future-proof for Kivy updates

### Content Area Calculation

```python
def _resize_image(self, img_widget):
    # Start with full window size
    content_w = self.width
    content_h = self.height
    content_x = 0
    content_y = 0
    
    if self.aspect_ratio == "9:16":
        # Portrait: subtract toolbar width from right
        toolbar_width = self.toolbar.width or dp(110)
        content_w = self.width - toolbar_width
        # Content starts at x=0, toolbar is on the right
        
    elif self.aspect_ratio == "16:9":
        # Landscape: subtract toolbar height from bottom
        toolbar_height = self.toolbar.height or dp(60)
        content_h = self.height - toolbar_height
        content_y = toolbar_height
        # Content starts above the toolbar
    
    # Calculate scaling and position image in center of content area
    # ...
```

**Visual:**
```
9:16 Mode:                    16:9 Mode:
┌────────────┬───┐           ┌───────────────┐
│            │ T │           │               │
│  Content   │ o │           │   Content     │
│  Area      │ o │           │   Area        │
│  (calc)    │ l │           │   (calc)      │
│            │ b │           ├───────────────┤
│            │ a │           │   Toolbar     │
└────────────┴─r─┘           └───────────────┘
 ←content_w→                  ←─content_w──→
                              ↑content_y
```

## Gallery Double-Click Prevention

```python
class ImageTile(BoxLayout):
    def __init__(self, ...):
        self.is_lightbox_open = False
        self._scheduled_lightbox = None
        
    def on_touch_down(self, touch):
        if double_click_detected:
            self._open_lightbox_debounced()  # 250ms delay
    
    def _open_lightbox_debounced(self):
        # Cancel any pending opens
        if self._scheduled_lightbox:
            Clock.unschedule(self._scheduled_lightbox)
        
        # Check if already open
        if self.is_lightbox_open:
            return  # Ignore
        
        # Schedule with 250ms throttle
        self._scheduled_lightbox = Clock.schedule_once(
            lambda dt: self._open_lightbox(), 0.25
        )
    
    def _open_lightbox(self):
        self.is_lightbox_open = True
        # Create lightbox...
        # Bind to reset flag when closed
```

**Timeline:**
```
User Action:    [Click] [Click] [Click] [Click] [Click]
                  ↓       ↓       ↓       ↓       ↓
Detection:      Single  Double  Triple  Quad    Quint
                        ✓                         
                        │                         
Debounce:               └─ Schedule (250ms)      
                              ↓                   
Flag Check:                   is_open? No → Open 
                                       Yes → Ignore
                        
Result:         One lightbox opens, others ignored ✅
```

## 9:16 Pipeline Flow

```
User Action              File/Process              Result
───────────────────────────────────────────────────────────
                                                    
[Format Button]  →  FormatSelectionPopup    →  User selects "9:16"
                         │
                         ├──→ image_meta.json  →  {"aspect_ratio": "9:16"}
                         │
                         └──→ _apply_layout()  →  Toolbar moves to right
                                                   VerticalButton created
                                                   Content area recalculated
                                                    
[Record/Generate] → Aufnahme workflow      →  Creates transcript
                         │
                         └──→ vertex_ai_...  →  Reads image_meta.json ✅
                              workflow.py        aspect_ratio = "9:16"
                                 │
                                 └──→ Vertex AI  →  Generates 768×1408
                                      API           (portrait image)
                                        │
                                        └──→ scale_image_to  →  Input: 768×1408
                                             _target_size()     aspect_ratio: 9:16
                                                │               Target: 1080×1920
                                                │
                                                └──→ Image scaled to 1080×1920 ✅
                                                     (NOT 1920×1080!)
                                                     
[Display in App]  →  Slideshow loads       →  Image displays correctly
                     9:16 mode layout          in portrait orientation ✅
```

## Key Fixes Applied

### 1. JSON Import Fix (PythonServer.py)
**Before:**
```python
# Missing import
def scale_image_to_1920x1080(...):
    with open(meta_path, 'r') as f:
        meta = json.load(f)  # ❌ NameError: name 'json' is not defined
```

**After:**
```python
import json  # ✅ Added at top of file

def scale_image_to_1920x1080(...):
    with open(meta_path, 'r') as f:
        meta = json.load(f)  # ✅ Works correctly
```

### 2. PIL Debug Noise Suppression
**Before:**
```
[DEBUG] PIL.PngImagePlugin: Reading PNG chunk...
[DEBUG] PIL.PngImagePlugin: Chunk type...
[DEBUG] PIL.PngImagePlugin: ... (hundreds of lines)
```

**After:**
```python
# In setup_projekt_logging()
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)
```
Result: Clean logs with only important messages ✅

### 3. Kivy 2.3+ Compatibility
**Before:**
```python
# Using deprecated properties
self.img_a = Image(opacity=1, allow_stretch=True, keep_ratio=True)
# Works but deprecated in Kivy 2.3+
```

**After:**
```python
# Version-aware implementation
if kivy_version >= (2, 3):
    self.img_a = Image(opacity=1, fit_mode='cover')  # ✅ Modern API
else:
    self.img_a = Image(opacity=1, allow_stretch=True, keep_ratio=True)  # ✅ Legacy support
```

## Testing Matrix

| Feature | 16:9 Mode | 9:16 Mode | Status |
|---------|-----------|-----------|--------|
| Toolbar position | Bottom | Right | ✅ |
| Button orientation | Horizontal | Vertical (270°) | ✅ |
| Text readability | Normal | Top-to-bottom | ✅ |
| Content area calc | height - 60dp | width - 110dp | ✅ |
| Image scaling | 1920×1080 | 1080×1920 | ✅ |
| JSON reading | Works | Works | ✅ |
| PIL noise | Suppressed | Suppressed | ✅ |
| Popup centering | Centered | Centered | ✅ |
| Lightbox | No freeze | No freeze | ✅ |
| fit_mode support | Kivy 2.3+ | Kivy 2.3+ | ✅ |

## Conclusion

The implementation provides complete portrait/landscape support through:
1. ✅ Layout-based orientation (not root canvas rotation)
2. ✅ Proper component positioning for both modes
3. ✅ Readable text in portrait mode (VerticalButton)
4. ✅ Correct image scaling (9:16 → 1080×1920, 16:9 → 1920×1080)
5. ✅ Modern Kivy API support (fit_mode='cover')
6. ✅ Responsive gallery (no freeze on double-click)

All achieved with minimal code changes following best practices! 🎉
