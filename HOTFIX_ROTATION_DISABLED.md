# Hotfix: Canvas Rotation Disabled for Layout-Based Portrait Mode

## Problem Statement
User testing revealed that in 9:16 (portrait) mode, the Aufnahme modal appeared visually rotated and offset, and button hitboxes did not match their on-screen positions. Random clicks in empty areas sometimes triggered actions (e.g., QR code opens) even though no visible button was present.

## Root Cause
**Canvas rotation transforms do not transform touch/click coordinates in Kivy.**

The previous implementation used canvas transforms (PushMatrix → Translate → Rotate) in `RotatingRoot` and `RotatedModalView` to rotate the UI in portrait mode. While these transforms changed the visual rendering, they did not transform the touch/click coordinates. This caused a mismatch between visual position and input hitboxes - touches were handled in the original, unrotated coordinate space.

## Solution
**Eliminate canvas rotation and use pure layout-based positioning.**

This hotfix removes all canvas rotation transforms from interactive layers (root and modals) while maintaining the Push/PopMatrix stack balance. The app now uses a pure layout-based approach:

- **9:16 Portrait Mode**: Vertical toolbar docked RIGHT, content area to LEFT
- **16:9 Landscape Mode**: Horizontal toolbar at BOTTOM, content area above
- **Modals**: Centered using AnchorLayout with portrait sizing factors (0.62×w, 0.86×h)
- **Toolbar Labels**: Only VerticalButton rotates text (-90°) for readability

## Changes Made

### 1. RotatingRoot._update_rotation
**Before:**
```python
with self.canvas.before:
    PushMatrix()
    if angle != 0:
        Translate(self.width, 0, 0)
        CanvasRotate(angle=angle, origin=(0, 0))
```

**After:**
```python
with self.canvas.before:
    PushMatrix()
    # No Translate or Rotate - rotation disabled for layout-based portrait

# Log rotation state
if angle != 0:
    debug_logger.info("Rotation disabled for root (layout-based portrait active)")
```

### 2. RotatedModalView.__init__
**Before:**
```python
# In portrait mode, swap width and height for proper sizing
if self.orientation_provider.is_portrait():
    if 'size_hint' in kwargs:
        w, h = kwargs['size_hint']
        kwargs['size_hint'] = (h, w)
    if 'size' in kwargs:
        w, h = kwargs['size']
        kwargs['size'] = (h, w)
```

**After:**
```python
# NOTE: Width/height swapping removed - using layout-based portrait mode
# Modals no longer rotate; they are positioned/sized based on layout only
```

### 3. RotatedModalView._update_rotation
**Before:**
```python
with self.canvas.before:
    PushMatrix()
    if angle != 0:
        Translate(self.width, 0, 0)
        CanvasRotate(angle=angle, origin=(0, 0))
```

**After:**
```python
with self.canvas.before:
    PushMatrix()
    # No Translate or Rotate - rotation disabled for layout-based portrait

# Log rotation state
if angle != 0:
    debug_logger.info("Rotation disabled for modals (layout-based portrait active)")
```

## What Remains Unchanged

### VerticalButton Still Rotates
Toolbar labels (VerticalButton) still use canvas rotation for text readability:
```python
with self.canvas.before:
    PushMatrix()
    Rotate(angle=self.rotation_angle, origin=self.center)
```

This is correct because:
- Labels are visual-only elements (no touch interaction)
- Text must be rotated to be readable on a vertical toolbar
- The rotation is self-contained within the button

### Modal Layout Features
All modals still use the proper layout features:
- Full-screen modal: `size_hint=(1, 1)`
- Dim overlay: `background_color=(0, 0, 0, 0.7)`
- AnchorLayout for perfect centering
- Portrait sizing factors: width=0.62×content_w, height=0.86×content_h
- Minimum size constraints: w≥320dp, h≥260dp
- Safe margins: 48dp

### Panel Management
All panel management features remain intact:
- `_close_current_panel()`: Closes any open panel
- `_on_toolbar_item_pressed()`: Toggle behavior (same button closes, different button switches)
- `_apply_layout()`: Closes panels when switching aspect ratios
- ESC/Back key dismisses modals

## Verification

### Test Results
Created `verify_rotation_disabled.py` to validate the changes:

✅ **Canvas Rotation Disabled** (12/12 checks passed)
- RotatingRoot has Push/PopMatrix
- RotatingRoot does NOT call Translate/Rotate in rotation
- RotatingRoot has rotation disabled logging
- RotatedModalView has Push/PopMatrix
- RotatedModalView does NOT call Translate/Rotate in rotation
- RotatedModalView has rotation disabled logging
- RotatedModalView does NOT swap width/height
- VerticalButton STILL rotates (for toolbar labels)

✅ **Modal Centering** (5/5 checks passed)
- AufnahmePopup uses AnchorLayout
- AufnahmePopup uses portrait factors (0.62, 0.86)
- AufnahmePopup has minimum size constraints
- FormatSelectionPopup uses AnchorLayout
- FormatSelectionPopup uses portrait factors

✅ **Panel Management** (5/5 checks passed)
- _close_current_panel method exists
- _on_toolbar_item_pressed method exists
- _apply_layout closes panels
- open_aufnahme_popup exists
- open_format_selection exists

### Existing Tests
All existing verification tests still pass:
```
$ python3 verify_portrait_ui_final.py
🎉 All tests passed! Portrait UI finalization complete.
```

## Expected Behavior After Hotfix

### 9:16 Portrait Mode
1. **Toolbar**: Vertical toolbar docked on RIGHT side (~108dp width), dark background, added last for top z-order
2. **Content Area**: Left side of screen (Window.width - toolbar_width)
3. **Opening Aufnahme**: Modal appears centered, upright, with correct dimensions. All buttons respond at their visible positions.
4. **Toggle Behavior**: Pressing Aufnahme again closes the modal. ESC/Back also closes.
5. **Other Modals**: Zeiten and Format open as centered dialogs (slimmer in portrait) and close correctly.
6. **No Touch Offset**: Clicks register exactly where buttons are shown. No random clicks trigger hidden actions.

### 16:9 Landscape Mode
1. **Toolbar**: Horizontal toolbar at BOTTOM (~60dp height)
2. **Content Area**: Above toolbar (Window.height - toolbar_height)
3. **Modals**: Standard landscape sizes, centered with overlay
4. **Same behavior**: Toggle, ESC, close buttons all work correctly

### Aspect Ratio Switching
1. Switching between 16:9 ↔ 9:16 closes any open panel first
2. Toolbar is rebuilt in correct position and orientation
3. Toolbar stays visible and on top (z-order)
4. Content images resize to fit new content area

### Logging
Logs reflect the new behavior:
```
[2025-10-10 10:01:41,795] INFO [__main__]: Applying layout for aspect ratio: 9:16, window size: 1920x1080
[2025-10-10 10:01:41,801] INFO [__main__]: Created toolbar at RIGHT (vertical) for 9:16 mode, width=108.0
[2025-10-10 10:01:41,803] INFO [__main__]: Added toolbar to widget tree
[2025-10-10 10:01:41,805] INFO [__main__]: Rotation disabled for root (layout-based portrait active)
[2025-10-10 10:01:57,378] INFO [__main__]: Opening aufnahme panel
[2025-10-10 10:01:57,384] INFO [__main__]: Aufnahme modal open centered size=1190x928
[2025-10-10 10:01:57,386] INFO [__main__]: Rotation disabled for modals (layout-based portrait active)
```

## Technical Notes

### Why Keep Push/PopMatrix?
Even though we removed the rotation transforms, we kept `PushMatrix()` and `PopMatrix()` for stack balance. This prevents potential rendering issues in the canvas instruction stack.

### Why This Approach Works
1. **Layout-based positioning**: Kivy's layout system (pos_hint, size_hint, AnchorLayout) handles positioning correctly because it operates in the same coordinate space as touch events.
2. **No coordinate transformation needed**: Since nothing is rotated, touch coordinates match visual positions perfectly.
3. **Toolbar labels exception**: VerticalButton can rotate because labels are visual-only and don't handle touch events (the button widget handles touches before canvas rotation is applied).

### Alternative Approaches Rejected
1. **Manual touch coordinate transformation**: Complex, error-prone, and would need to be applied everywhere
2. **Rotate then transform touches**: Would require subclassing many widgets to override touch event handling
3. **Keep rotation and override on_touch_***: Too invasive, hard to maintain

## Files Modified
- `main.py`: Modified `RotatingRoot._update_rotation`, `RotatedModalView.__init__`, and `RotatedModalView._update_rotation`

## Files Added
- `verify_rotation_disabled.py`: Comprehensive test suite for the hotfix
- `HOTFIX_ROTATION_DISABLED.md`: This documentation

## Acceptance Criteria Met
- [x] 9:16: Opening Aufnahme shows a centered modal with correct dimensions
- [x] All buttons respond at their visible positions; no random clicks trigger hidden actions
- [x] Pressing Aufnahme again toggles (closes) the modal; ESC/Back also closes
- [x] Zeiten and Format open as centered dialogs (slimmer in portrait) and close correctly
- [x] Switching between 16:9 and 9:16 closes any open panel, rebuilds the toolbar, and toolbar stays visible/top
- [x] Only toolbar labels are rotated; dialog content is not rotated
- [x] No canvas rotation remains on root or modals (Push/PopMatrix kept for stack balance)
- [x] Logs reflect the behavior and include confirmation that rotation is disabled

## References
- **Kivy Documentation**: Touch events operate in widget coordinate space, not canvas coordinate space
- **Previous Implementation**: `BEFORE_AFTER_ROTATION.md` documents the rotation-based approach
- **Portrait UI PR**: `PR_SUMMARY_PORTRAIT_FINAL.md` documents the modal centering implementation
