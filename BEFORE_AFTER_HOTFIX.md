# Before/After: Critical Hotfix for Matrix Stack and Rotation

## 🚨 Critical Issue #1: Unbalanced PushMatrix/PopMatrix

### BEFORE (Crashed on startup)
```python
def _update_rotation(self, *args):
    angle = self.orientation_provider.get_rotation_angle()
    
    # Clear existing rotation instructions
    self.canvas.before.clear()  # ❌ Removes PushMatrix!
    
    if angle != 0:
        with self.canvas.before:
            PushMatrix()
            Translate(self.width, 0, 0)
            CanvasRotate(angle=angle, origin=(0, 0))
        
        with self.canvas.after:
            PopMatrix()  # ❌ No matching Push in landscape!
    else:
        # Landscape mode
        with self.canvas.before:
            PushMatrix()
        with self.canvas.after:
            PopMatrix()  # ❌ Gets called when before was cleared!
```

**Problem**: 
- `canvas.before.clear()` removes the PushMatrix
- Then `canvas.after` still has PopMatrix
- Results in: `IndexError: list index out of range` → **App crashes immediately**

### AFTER (Fixed)
```python
def _update_rotation(self, *args):
    angle = self.orientation_provider.get_rotation_angle()
    
    # Clear existing rotation instructions
    self.canvas.before.clear()
    self.canvas.after.clear()  # ✅ Clear both!
    
    # ALWAYS push/pop matrix in both portrait and landscape
    with self.canvas.before:
        PushMatrix()  # ✅ Always Push
        if angle != 0:
            Translate(self.width, 0, 0)
            CanvasRotate(angle=angle, origin=(0, 0))
    
    with self.canvas.after:
        PopMatrix()  # ✅ Always Pop (balanced)
```

**Solution**:
- Clear BOTH `canvas.before` AND `canvas.after`
- Always include balanced Push/Pop regardless of orientation
- Only add transforms conditionally in portrait mode

---

## 🔄 Issue #2: Dialogs Don't Rotate

### BEFORE (Dialogs stuck in landscape)
```python
class AufnahmePopup(FloatLayout):  # ❌ FloatLayout doesn't rotate
    def __init__(self, slideshow=None, **kwargs):
        super().__init__(**kwargs)
        # ... setup code ...
        
        # Background
        with self.canvas.before:
            Color(0, 0, 0, 0.7)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)
        # ... rest of popup ...
    
    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
    
    def close_popup(self, instance):
        if self.parent:
            self.parent.remove_widget(self)  # ❌ Manual removal

# Opening:
def open_aufnahme_popup(self):
    self.open_single(AufnahmePopup(slideshow=self))  # ❌ Added as widget
```

**Problem**:
- Inherits from FloatLayout, not RotatedModalView
- Doesn't participate in global rotation transform
- Manual background management
- Opened with `open_single()` / `add_widget()` instead of `.open()`

### AFTER (Dialogs rotate correctly)
```python
class AufnahmePopup(RotatedModalView):  # ✅ Inherits rotation
    def __init__(self, slideshow=None, **kwargs):
        # Set ModalView properties
        kw_copy = kwargs.copy()
        kw_copy.setdefault('size_hint', (None, None))
        kw_copy.setdefault('auto_dismiss', False)
        super().__init__(**kw_copy)  # ✅ RotatedModalView handles rotation
        # ... setup code ...
        
        # ModalView provides background
        self.background_color = (0, 0, 0, 0.7)  # ✅ Use ModalView API
        self.background = ''
        
        # Set size directly
        self.size = panel_size
        # ... rest of popup ...
    
    # ❌ No more _update_bg method needed
    
    def close_popup(self, instance):
        self.dismiss()  # ✅ ModalView API

# Opening:
def open_aufnahme_popup(self):
    popup = AufnahmePopup(slideshow=self)
    popup.open()  # ✅ ModalView API
```

**Solution**:
- Changed base class to `RotatedModalView`
- Uses ModalView's built-in background system
- Removed manual background rectangle management
- Uses `.open()` and `.dismiss()` ModalView APIs

---

## 🖼️ Issue #3: Lightbox Shows White Images

### BEFORE (Unreliable image loading)
```python
def load_image(dt):
    try:
        self.img.source = image_path
        self.img.reload()
        debug_logger.info(f"Lightbox image loaded: {image_path}")
    except Exception as e:
        debug_logger.error(f"Failed to load image: {e}")
        # Show error
```

**Problem**:
- No fallback if `source` + `reload()` produces no texture
- Some images would show as white rectangles
- No validation that texture actually loaded

### AFTER (Robust loading with fallback)
```python
def load_image(dt):
    try:
        self.img.source = image_path
        self.img.reload()
        
        # ✅ Check texture after reload and try fallback
        def check_texture(dt2):
            if self.img.texture is None:
                debug_logger.warning("Texture None, trying CoreImage fallback")
                try:
                    from kivy.core.image import Image as CoreImage
                    core_img = CoreImage(image_path, nocache=True)
                    if core_img and core_img.texture:
                        self.img.texture = core_img.texture  # ✅ Fallback
                        debug_logger.info("Loaded via CoreImage fallback")
                    else:
                        raise Exception("CoreImage returned no texture")
                except Exception as e2:
                    debug_logger.error(f"Fallback failed: {e2}")
                    # Show error message
            else:
                debug_logger.info("Image loaded successfully")
        
        Clock.schedule_once(check_texture, 0.1)  # ✅ Validate after delay
    except Exception as e:
        debug_logger.error(f"Failed to load: {e}")
        # Show error
```

**Solution**:
- Primary method: `source` + `reload()`
- Secondary fallback: `CoreImage(path, nocache=True)`
- Validation: Check if texture is None after 0.1s
- Error handling: Show user-friendly error if both fail

---

## 📋 Summary of All Popup Conversions

| Popup Class | Status |
|-------------|--------|
| ImageSettingsPopup | ✅ Converted to RotatedModalView |
| ImageLightboxPopup | ✅ Converted to RotatedModalView |
| SettingsRootPopup | ✅ Converted to RotatedModalView |
| AufnahmePopup | ✅ Converted to RotatedModalView |
| GeneralSettingsPopup | ✅ Converted to RotatedModalView |
| GlobalDurationPopup | ✅ Converted to RotatedModalView |
| TimePickerPopup | ✅ Converted to RotatedModalView |
| FormatSelectionPopup | ✅ Converted to RotatedModalView |

---

## 🎯 Expected Behavior After Hotfix

### Startup
✅ No crash due to matrix stack imbalance  
✅ App starts successfully in both 16:9 and 9:16 modes

### Orientation Switch
✅ Entire UI rotates (main content + all dialogs)  
✅ No matrix stack errors  
✅ Touch events work correctly in both orientations

### Dialogs in Portrait Mode
✅ Aufnahme window rotates and is usable  
✅ Settings dialogs rotate and are usable  
✅ Gallery lightbox rotates and shows images correctly  
✅ All dialogs properly positioned and interactive

### Image Loading
✅ Gallery lightbox shows actual images (no white screens)  
✅ CoreImage fallback triggers if needed  
✅ Error messages shown if image cannot load

---

## 🔧 Technical Details

### Matrix Stack Balance
- **Root cause**: Clearing `canvas.before` after adding instructions
- **Fix**: Always clear BOTH before/after, always Push/Pop
- **Impact**: Prevents IndexError crash on startup and orientation switch

### ModalView vs FloatLayout
- **ModalView benefits**:
  - Built-in rotation support via RotatedModalView
  - Auto-dismiss on background click
  - Proper z-ordering above other content
  - Built-in background overlay
  - `.open()` and `.dismiss()` API

### Rotation Architecture
```
RotatingRoot (applies transform)
  └── All content rotates
      ├── Main slideshow
      ├── Toolbar
      └── RotatedModalView popups (inherit rotation)
          ├── AufnahmePopup
          ├── SettingsRootPopup
          └── All other popups
```

---

## ✅ Verification Checklist

- [x] Python syntax validation passed
- [x] All popups converted to RotatedModalView
- [x] All popup opening uses `.open()`
- [x] All popup closing uses `.dismiss()`
- [x] Matrix Push/Pop balanced in RotatingRoot
- [x] Matrix Push/Pop balanced in RotatedModalView
- [x] CoreImage fallback implemented in lightbox
- [ ] Manual testing on device required
