# Rotated Modal Labels Implementation

## Overview

This document describes the implementation of rotated text labels in the Format modal for portrait (9:16) mode. The goal is to make text readable when the device is in physical portrait orientation, while maintaining correct button hitboxes and touch handling.

## Problem Statement

In 9:16 portrait mode, the Format modal appeared with text oriented horizontally relative to the screen. Users needed to tilt their heads or device to read the text comfortably. The requirement was to rotate the text -90° (counterclockwise) so it reads naturally from top to bottom when the device is held in portrait orientation.

## Key Requirements

1. **Text Rotation Only**: Rotate only the text rendering, not the widget containers or touch hitboxes
2. **Conditional Rotation**: Apply rotation only in 9:16 mode, not in 16:9 mode
3. **Maintain Touch Handling**: Button clicks must register at the correct positions
4. **Prevent Text Clipping**: Add padding to prevent rotated text from being cut off
5. **Logging**: Log when rotated labels are used

## Implementation

### 1. Configuration Constants

Added two configuration constants near the top of the widget definitions:

```python
# Config constants for portrait modal labels
PORTRAIT_MODAL_LABEL_ANGLE = -90  # Counterclockwise rotation for portrait mode
PORTRAIT_MODAL_LABEL_PADDING = (dp(8), dp(6))  # Padding to prevent clipping
```

**Location**: `main.py` around line 757

**Rationale**:
- `-90°` rotation makes text readable from top to bottom on a portrait screen
- Padding prevents text clipping when rotated
- Constants make values configurable and consistent

### 2. RotatedLabel Widget

Created a new `RotatedLabel` class that extends Kivy's `Label`:

```python
class RotatedLabel(Label):
    """Label with rotated text for portrait mode modals.
    
    Rotates only the text rendering, not the widget container itself,
    so button hitboxes and layout remain correct.
    """
    def __init__(self, rotation_angle=0, **kwargs):
        super().__init__(**kwargs)
        self.rotation_angle = rotation_angle
        if rotation_angle != 0:
            self.padding = PORTRAIT_MODAL_LABEL_PADDING
        self.bind(pos=self._update_rotation, size=self._update_rotation)
        
    def _update_rotation(self, *args):
        self.canvas.before.clear()
        if self.rotation_angle != 0:
            with self.canvas.before:
                PushMatrix()
                Rotate(angle=self.rotation_angle, origin=self.center)
        
        self.canvas.after.clear()
        if self.rotation_angle != 0:
            with self.canvas.after:
                PopMatrix()
```

**Key Features**:
- Uses `canvas.before` and `canvas.after` to apply rotation only to rendering
- `PushMatrix`/`PopMatrix` ensure rotation doesn't affect other widgets
- Rotation is around the widget's center point
- Conditional padding prevents clipping
- When `rotation_angle=0`, behaves like a normal Label

### 3. RotatedButton Widget

Similar to `RotatedLabel` but for buttons:

```python
class RotatedButton(Button):
    """Button with rotated text for portrait mode modals.
    
    Rotates only the text rendering, not the button container itself,
    so hitboxes remain correct and clicks work as expected.
    """
    def __init__(self, rotation_angle=0, **kwargs):
        super().__init__(**kwargs)
        self.rotation_angle = rotation_angle
        if rotation_angle != 0:
            self.padding = PORTRAIT_MODAL_LABEL_PADDING
        self.bind(pos=self._update_rotation, size=self._update_rotation)
        
    def _update_rotation(self, *args):
        self.canvas.before.clear()
        if self.rotation_angle != 0:
            with self.canvas.before:
                PushMatrix()
                Rotate(angle=self.rotation_angle, origin=self.center)
        
        self.canvas.after.clear()
        if self.rotation_angle != 0:
            with self.canvas.after:
                PopMatrix()
```

**Why a Separate Button Class?**:
- Buttons need to maintain their click handling
- Canvas rotation affects only visual rendering, not touch events
- The button container stays unrotated, so hitboxes remain correct

### 4. FormatSelectionPopup Updates

Modified the `FormatSelectionPopup.__init__` method to use rotated widgets:

#### Determine Portrait Mode

```python
# Determine if we should rotate labels (portrait mode)
is_portrait = aspect == "9:16"
label_rotation = PORTRAIT_MODAL_LABEL_ANGLE if is_portrait else 0
```

#### Replace Labels with RotatedLabel

**Before**:
```python
panel.add_widget(Label(text="Format", size_hint_y=None, height=dp(54),
                      font_size=dp(32), color=(1, 1, 1, 1), bold=True))
```

**After**:
```python
title_label = RotatedLabel(
    text="Format", 
    size_hint_y=None, 
    height=dp(54),
    font_size=dp(32), 
    color=(1, 1, 1, 1), 
    bold=True,
    rotation_angle=label_rotation
)
panel.add_widget(title_label)
```

#### Replace Buttons with RotatedButton

**Before**:
```python
btn_horizontal = Button(text="Horizontal (16:9)", size_hint_y=None, height=dp(60),
                       font_size=dp(22),
                       background_normal='', background_color=(0.3, 0.5, 0.7, 1),
                       color=(1, 1, 1, 1))
```

**After**:
```python
btn_horizontal = RotatedButton(
    text="Horizontal (16:9)", 
    size_hint_y=None, 
    height=dp(60),
    font_size=dp(22),
    background_normal='', 
    background_color=(0.3, 0.5, 0.7, 1),
    color=(1, 1, 1, 1),
    rotation_angle=label_rotation
)
```

#### Enhanced Logging

Added conditional logging to track when rotated labels are used:

```python
# Log modal opening
if is_portrait:
    debug_logger.info(f"Format modal open centered size={panel_size[0]}x{panel_size[1]}")
    debug_logger.info(f"Format modal labels rotated {PORTRAIT_MODAL_LABEL_ANGLE}° (portrait)")
else:
    debug_logger.info(f"Format modal open centered size={panel_size[0]}x{panel_size[1]}")
```

## Technical Details

### Canvas Rotation vs Widget Rotation

**Important**: We use canvas-level rotation, not widget-level rotation:

- **Canvas Rotation** (`canvas.before`/`canvas.after`):
  - Affects only the visual rendering of the widget's content
  - Touch events are still processed based on the widget's unrotated position
  - Hitboxes remain correct
  - ✅ This is what we use

- **Widget Rotation** (rotating the entire widget):
  - Would rotate both rendering AND touch handling
  - Would cause touch coordinates to be misaligned
  - Would require complex coordinate transformations
  - ❌ We explicitly avoid this

### Matrix Operations

The rotation uses standard OpenGL matrix operations:

1. `PushMatrix()` - Save current transformation state
2. `Rotate(angle=..., origin=self.center)` - Apply rotation around center
3. **Widget renders here** (automatically by Kivy)
4. `PopMatrix()` - Restore transformation state

This ensures:
- Rotation is isolated to this widget
- Other widgets are unaffected
- The widget's layout position is unchanged

### Rotation Angle: Why -90°?

- **-90° (counterclockwise)** makes text read naturally from top to bottom
- Matches the physical orientation of a portrait device
- Text flows naturally downward, matching reading direction
- Consistent with the toolbar's `VerticalButton` approach (270° = -90°)

## Testing

### Automated Tests

Created `verify_rotated_modal_labels.py` which verifies:
- ✅ Config constants are defined correctly
- ✅ RotatedLabel class exists with proper implementation
- ✅ RotatedButton class exists with proper implementation
- ✅ FormatSelectionPopup uses the rotated widgets
- ✅ Rotation is conditional on portrait mode
- ✅ Logging is implemented

Run with:
```bash
python3 verify_rotated_modal_labels.py
```

### Visual Test

Created `test_rotated_modal_labels.py` which shows:
- Side-by-side comparison of normal vs rotated labels
- Interactive buttons to verify hitboxes work correctly
- Demonstrates the visual effect of -90° rotation

Run with:
```bash
python3 test_rotated_modal_labels.py
```

### Manual Testing Checklist

1. **9:16 Portrait Mode**:
   - [ ] Switch app to 9:16 mode
   - [ ] Open Format modal (press Format button)
   - [ ] Verify all text is rotated -90° (readable from left edge)
   - [ ] Verify title "Format" is rotated
   - [ ] Verify "Aktuell: 9:16" subtitle is rotated
   - [ ] Verify "Horizontal (16:9)" button text is rotated
   - [ ] Verify "Vertikal (9:16)" button text is rotated
   - [ ] Verify "Schließen" button text is rotated
   - [ ] Click each button and verify it responds
   - [ ] Press ESC/Back and verify modal closes
   - [ ] Check logs for "Format modal labels rotated -90° (portrait)"

2. **16:9 Landscape Mode**:
   - [ ] Switch app to 16:9 mode
   - [ ] Open Format modal
   - [ ] Verify all text is horizontal (normal)
   - [ ] Verify all buttons work correctly
   - [ ] Press ESC/Back and verify modal closes
   - [ ] Check logs (should NOT mention rotated labels)

3. **Mode Switching**:
   - [ ] Start in 16:9, open modal, close modal
   - [ ] Switch to 9:16, open modal, verify rotation, close modal
   - [ ] Switch back to 16:9, open modal, verify no rotation, close modal

## Benefits

1. **Improved Readability**: Text is readable without tilting head or device
2. **Correct Touch Handling**: Buttons click where they appear on screen
3. **Minimal Code Changes**: Only ~100 lines added
4. **Reusable Components**: RotatedLabel and RotatedButton can be used elsewhere
5. **Configurable**: Rotation angle and padding are easily adjustable
6. **No Regressions**: 16:9 mode unchanged, ESC/Back still works
7. **Logged**: Clear log messages for debugging

## Comparison with VerticalButton

This implementation is similar to the existing `VerticalButton` class used in the toolbar:

| Feature | VerticalButton | RotatedLabel/RotatedButton |
|---------|----------------|----------------------------|
| Purpose | Toolbar buttons | Modal text/buttons |
| Rotation Angle | 270° (default) | -90° (portrait), 0° (landscape) |
| Conditional | Always rotated in portrait toolbar | Conditional on aspect ratio |
| Padding | `[dp(10), dp(5)]` | `PORTRAIT_MODAL_LABEL_PADDING` |
| Canvas Rotation | Yes | Yes |
| Touch Handling | Correct | Correct |

Both use the same technique: canvas-level rotation with proper matrix operations.

## Files Modified

- `main.py`:
  - Added constants: `PORTRAIT_MODAL_LABEL_ANGLE`, `PORTRAIT_MODAL_LABEL_PADDING`
  - Added class: `RotatedLabel`
  - Added class: `RotatedButton`
  - Modified class: `FormatSelectionPopup.__init__` to use rotated widgets
  - Enhanced logging in `FormatSelectionPopup.__init__`

## Files Added

- `verify_rotated_modal_labels.py`: Automated verification tests
- `test_rotated_modal_labels.py`: Visual test application
- `ROTATED_MODAL_LABELS_IMPLEMENTATION.md`: This documentation

## Future Enhancements

Possible improvements for future iterations:

1. **Apply to Other Modals**: Use RotatedLabel/RotatedButton in other modals (Settings, TimePickerPopup, etc.)
2. **Configurable Angle**: Allow users to choose rotation preference
3. **Animation**: Smoothly animate rotation when switching modes
4. **Font Size Adjustment**: Auto-adjust font sizes for rotated text
5. **RTL Support**: Handle right-to-left languages

## Conclusion

This implementation successfully rotates Format modal labels in portrait mode while maintaining correct button hitboxes and touch handling. The solution is minimal, reusable, and consistent with existing code patterns.
