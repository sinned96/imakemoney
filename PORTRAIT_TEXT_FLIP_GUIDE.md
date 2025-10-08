# Portrait Text Flip & Layout Guide

This document describes the changes made to fix 9:16 portrait mode UI issues.

## Overview

The previous implementation had the toolbar at the bottom for both 16:9 and 9:16 modes. This PR restores the proper vertical toolbar on the right side for 9:16 mode with correctly oriented text.

## Changes Summary

### 1. Toolbar Text Orientation (9:16 Portrait Mode)

**Problem:** Text needs to be readable when the physical screen is rotated to portrait orientation.

**Solution:** Applied 90° rotation + vertical mirror (Scale 1,-1) transformation:
- Text rotates 90° clockwise
- Vertical mirror flips it to be readable from top to bottom
- Rotation center is the button's center point
- Hitboxes remain aligned with visual appearance

**Configuration:**
```python
PORTRAIT_LABEL_ANGLE = 90  # Will be mirrored with Scale(1, -1)
```

**Implementation in VerticalButton class:**
```python
def _update_rotation(self, *args):
    self.canvas.before.clear()
    with self.canvas.before:
        PushMatrix()
        # Translate to center for pivot point
        Translate(self.center_x, self.center_y, 0)
        # Apply vertical mirror if requested (flips text upside down)
        if self.use_mirror:
            Scale(1, -1, 1)
        # Rotate around the center point
        Rotate(angle=self.rotation_angle, origin=(0, 0))
        # Translate back
        Translate(-self.center_x, -self.center_y, 0)
    
    self.canvas.after.clear()
    with self.canvas.after:
        PopMatrix()
```

### 2. Vertical Toolbar Layout (9:16 Mode)

**16:9 Mode (Landscape):**
```
┌──────────────────────────────────┐
│                                  │
│        Content Area              │
│      (Full Width)                │
│                                  │
├──────────────────────────────────┤
│ [Zeiten] [Aufnahme] [Format] ... │ ← Toolbar at bottom
└──────────────────────────────────┘
```

**9:16 Mode (Portrait):**
```
┌───────────────────────┬────┐
│                       │ Z  │
│                       │ e  │
│                       │ i  │
│   Content Area        │ t  │
│   (Width - 110dp)     │ e  │
│                       │ n  │
│                       ├────┤
│                       │ A  │
│                       │ u  │
│                       │ f  │
│                       │ n  │
│                       │ a  │
└───────────────────────┴────┘
                          ↑
                    Vertical toolbar
                    on right side
                    Text is mirrored
                    for readability
```

### 3. Galerie View Adaptation

**Landscape (16:9):**
- Panel width: 95% of screen
- Grid columns: 8
- Spacing: 18dp
- Modi list: 22% width on left

**Portrait (9:16):**
- Panel width: 85% of screen (narrower to account for right toolbar)
- Grid columns: 4 (fewer for narrower width)
- Spacing: 12dp (tighter)
- Modi list: 22% width on left (same proportion)
- No off-screen content

### 4. Other Modal Views Adaptation

All popups/overlays now check `slideshow.aspect_ratio` and adapt:

**GalleryEditor:**
- size_hint: (0.85, 0.92) in portrait vs (0.95, 0.92) in landscape
- grid_cols: 4 in portrait vs 8 in landscape

**ScheduleEditor:**
- size_hint: (0.85, 0.6) in portrait vs (0.7, 0.6) in landscape

**FormatSelectionPopup:**
- size: (360dp, 320dp) in portrait vs (400dp, 300dp) in landscape

**AufnahmePopup, SettingsRootPopup, GeneralSettingsPopup, GlobalDurationPopup:**
- Already had portrait adaptation in previous PRs

### 5. Toolbar Toggle Functionality

**New State Tracking:**
```python
self.current_popup = None         # Currently open popup reference
self.current_popup_name = None    # Which toolbar item opened it
```

**Toggle Methods:**
```python
def _toggle_overlay(name, widget_factory):
    """For FloatLayout overlays (Galerie, Zeiten)"""
    if current_popup_name == name:
        # Same item clicked - close it
        _close_current_overlay()
    else:
        # Different item or nothing open - switch
        _close_current_popup()
        _close_current_overlay()
        # Open new overlay

def _toggle_popup(name, popup_factory):
    """For ModalView popups (Settings, Aufnahme, Format)"""
    if current_popup_name == name:
        # Same item clicked - close it
        _close_current_popup()
    else:
        # Different item or nothing open - switch
        _close_current_popup()
        _close_current_overlay()
        # Open new popup
```

**Behavior:**
1. First click on toolbar item → Opens panel/popup
2. Click same item again → Closes panel/popup (toggle off)
3. Click different item → Closes current, opens new

### 6. Image Content Area Calculation

**Updated _resize_image method:**

```python
def _resize_image(self, img_widget):
    content_x = 0
    content_y = 0
    content_w = self.width
    content_h = self.height
    
    if self.aspect_ratio == "9:16":
        # Portrait: vertical toolbar on right side
        toolbar_width = self.toolbar.width or dp(110)
        content_w = self.width - toolbar_width
        # Content uses full width minus toolbar width
    else:
        # Landscape: horizontal toolbar at bottom
        toolbar_height = self.toolbar.height or dp(60)
        content_h = self.height - toolbar_height
        content_y = toolbar_height
        # Content starts above the toolbar
    
    # fit_mode='cover' handles scaling automatically
    img_widget.size = (content_w, content_h)
    img_widget.pos = (content_x, content_y)
```

## Testing Checklist

### Visual Tests (9:16 Mode)
- [ ] Toolbar appears on right side (not bottom)
- [ ] Toolbar has vertical orientation
- [ ] Toolbar text is readable when screen is physically rotated to portrait
- [ ] Toolbar button hitboxes match visual labels (no offset)
- [ ] Toolbar width is ~110dp

### Visual Tests (16:9 Mode)
- [ ] Toolbar appears at bottom (horizontal)
- [ ] Toolbar text is horizontal and readable
- [ ] Toolbar height is ~60dp
- [ ] Content fills area above toolbar

### Modal View Tests (Both Modes)
- [ ] Galerie opens and displays correctly
  - [ ] Modi list visible on left
  - [ ] Image grid fills available space (no off-screen)
  - [ ] Grid has 4 columns in portrait, 8 in landscape
  - [ ] Filter button and close button work
  
- [ ] Zeiten (Schedule Editor) opens and displays correctly
  - [ ] Panel is narrower in portrait mode
  - [ ] All buttons and labels visible
  
- [ ] Format popup opens and displays correctly
  - [ ] Panel sized appropriately for mode
  - [ ] Both format options visible
  
- [ ] Aufnahme popup opens and displays correctly
  - [ ] Panel sized appropriately for mode
  - [ ] All controls visible
  
- [ ] Einstellungen (Settings) opens and displays correctly
  - [ ] All sub-menus accessible
  - [ ] Panel sized appropriately for mode

### Toggle Functionality Tests
- [ ] Click "Galerie" → Opens gallery
- [ ] Click "Galerie" again → Closes gallery (toggle off)
- [ ] Click "Galerie" then "Zeiten" → Switches from gallery to schedule
- [ ] Click "Zeiten" again → Closes schedule
- [ ] Same behavior for all toolbar items

### Slideshow Tests
- [ ] Images display correctly in both modes
- [ ] No white frames or artifacts
- [ ] Images fill content area (not covered by toolbar)
- [ ] Transitions work smoothly
- [ ] fit_mode='cover' scaling is correct

### Log Verification
Check logs for:
- [ ] Aspect ratio confirmation: "Applying layout for aspect ratio: 9:16"
- [ ] Toolbar placement: "Created toolbar at RIGHT (vertical)" or "BOTTOM (horizontal)"
- [ ] Modal rotation state (if applicable)
- [ ] Image load results (should be concise, no PIL spam)

## Configuration Quick Reference

To adjust text orientation if needed, modify this constant in main.py:

```python
PORTRAIT_LABEL_ANGLE = 90  # Try 270 to flip orientation direction
```

Or disable mirroring in VerticalButton instantiation:
```python
btn = VerticalButton(text=text, rotation_angle=270, use_mirror=False, ...)
```

## Architecture Notes

1. **OrientationProvider**: Singleton that tracks current aspect_ratio and rotation_angle
2. **RotatingRoot**: Applies canvas rotation for portrait mode (still in place for modal views)
3. **VerticalButton**: Custom button class with configurable rotation and mirror
4. **CustomAppBar**: Supports both vertical and horizontal modes
5. **All modal views**: Check aspect_ratio and adapt sizing/layout

## Files Modified

1. **main.py**
   - Added PORTRAIT_LABEL_ANGLE constant
   - Updated VerticalButton with mirror support
   - Modified _create_toolbar to use vertical mode in portrait
   - Updated _resize_image to account for right-side toolbar
   - Added toggle functionality (_toggle_overlay, _toggle_popup)
   - Updated all toolbar button methods
   - Adapted GalleryEditor for portrait layout
   - Adapted ScheduleEditor for portrait layout
   - Adapted FormatSelectionPopup for portrait layout
   - Updated _apply_layout for proper toolbar recreation

## Compatibility

- Works with Kivy 2.3+ (fit_mode='cover')
- Backward compatible with older Kivy (keep_ratio/allow_stretch)
- No breaking changes to existing functionality
- Previous slideshow robustness maintained

## Future Improvements

If text orientation needs further adjustment:
1. Try different PORTRAIT_LABEL_ANGLE values (90, 270, -90)
2. Toggle use_mirror parameter
3. Adjust padding in VerticalButton if text is clipped
4. Consider font size adjustment for narrow vertical buttons
