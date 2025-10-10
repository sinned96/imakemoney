# Portrait (9:16) Toolbar Layout Fixes

## Summary
This document describes the fixes implemented to address UI issues in portrait (9:16) layout mode.

## Problem Statement
In 9:16 (portrait) layout, the current UI had several problems:
1. Toolbar was horizontal at bottom (same as landscape), but should be vertical on right
2. Overlay panels appeared at wrong positions and sometimes were not closable
3. Multiple panels could be opened at once
4. The "Format wechseln" panel was sometimes not visible
5. Dialogs retained 16:9 proportions instead of being slimmer for portrait
6. Toolbar visibility and z-order issues

## Solutions Implemented

### 1. Vertical Toolbar for Portrait Mode
**Files Modified:** `main.py`

#### Changes in `_apply_layout()` (lines ~3310-3333)
- Removed hardcoded horizontal toolbar for all modes
- Now detects aspect ratio and creates appropriate toolbar:
  - `9:16` → vertical toolbar on RIGHT
  - `16:9` → horizontal toolbar at BOTTOM
- Code:
  ```python
  vertical = (self.aspect_ratio == "9:16")
  self.toolbar = self._create_toolbar(vertical=vertical)
  ```

#### Changes in `_create_toolbar()` (lines ~3378-3415)
- Now respects the `vertical` parameter instead of ignoring it
- For vertical mode (9:16):
  - Creates `CustomAppBar` with `vertical=True`
  - Positions at `pos_hint={'right': 1, 'top': 1}`
  - Logs: `"Created toolbar at RIGHT (vertical) for 9:16 mode, width=XXX"`
- For horizontal mode (16:9):
  - Creates `CustomAppBar` with `vertical=False`
  - Positions at `pos_hint={'bottom': 1}`
  - Logs: `"Created toolbar at BOTTOM (horizontal) for 16:9 mode, height=XXX"`

#### Changes in `CustomAppBar` (line ~753)
- Updated vertical toolbar width from `dp(110)` to `dp(108)` (per requirements: 100-108dp)
- Already has dark background via `Color(0.12, 0.12, 0.14, 1)` in canvas.before
- Already uses `VerticalButton` with 270° rotation for readable vertical text

### 2. Content Area Adjustment
**Files Modified:** `main.py`

#### Changes in `_resize_image()` (lines ~3356-3377)
- Now detects aspect ratio and adjusts content area accordingly:
  - **9:16 mode (portrait):**
    - Subtracts toolbar width from right: `content_w = self.width - toolbar_width`
    - Content starts at `x=0` (full left)
    - Toolbar width defaults to `dp(108)`
  - **16:9 mode (landscape):**
    - Subtracts toolbar height from bottom: `content_h = self.height - toolbar_height`
    - Content starts at `y=toolbar_height` (above toolbar)
    - Toolbar height defaults to `dp(60)`

### 3. Popup Management (Prevent Multiple Opens)
**Files Modified:** `main.py`

#### New Instance Variable (line ~3226)
- Added `self.current_popup = None` to track currently open popup

#### New Method `_toggle_popup()` (lines ~3436-3456)
- Centralized popup management
- Behavior:
  - If same popup type already open → close it (toggle off)
  - If different popup type open → close old, open new
  - If no popup open → open new popup
- Automatically binds to `on_dismiss` to clear reference when popup closed

#### Updated Methods
- `open_settings_root()`: Now uses `_toggle_popup(SettingsRootPopup, self)`
- `open_aufnahme_popup()`: Now uses `_toggle_popup(AufnahmePopup, slideshow=self)`
- `open_format_selection()`: Now uses `_toggle_popup(FormatSelectionPopup, self)`

### 4. Popup Sizing for Portrait Mode
**Files Modified:** `main.py`

#### FormatSelectionPopup (lines ~3068-3083)
- Now adapts size based on aspect ratio:
  - **9:16 mode:** `(dp(350), dp(400))` - narrower and taller
  - **16:9 mode:** `(dp(400), dp(300))` - wider and shorter

#### Other Popups Already Adapted
- `AufnahmePopup` (lines ~1270-1279): Already adapts sizing
- `SettingsRootPopup` (lines ~1158-1166): Already adapts sizing

### 5. Toolbar Text Rotation
**Already Implemented**

The `VerticalButton` class (lines 718-745) already implements:
- 270° rotation (equivalent to -90°) for top-to-bottom readable text
- Used automatically by `CustomAppBar` when in vertical mode
- Only rotates button labels, NOT panel contents

## Technical Details

### Toolbar Dimensions
- **Portrait (9:16):** 108dp width, full height
- **Landscape (16:9):** 60dp height, full width

### Toolbar Background
- Color: `rgba(0.12, 0.12, 0.14, 1)` - dark gray/black
- Applied via `canvas.before` in `CustomAppBar.__init__()`

### Z-Order
- Toolbar: Added last to parent via `_bring_toolbar_to_front()`
- Popups: `ModalView` automatically renders on top of all other widgets

### Content Area Calculation
Portrait mode (9:16):
```
┌────────────┬───┐
│            │ T │
│  Content   │ o │
│  Area      │ o │
│  (images)  │ l │
│            │ b │
│            │ a │
│            │ r │
└────────────┴───┘
 ←content_w→
```

Landscape mode (16:9):
```
┌───────────────┐
│               │
│   Content     │
│   Area        │
│   (images)    │
├───────────────┤
│   Toolbar     │
└───────────────┘
      ↑
  content_y
```

## Testing Recommendations

1. **Switch to 9:16 mode:**
   - Click "Format" button
   - Select "Vertikal (9:16)"
   - Verify toolbar appears on right side
   - Verify toolbar has vertical buttons with readable text

2. **Test popup toggling:**
   - Click "Aufnahme" button → popup opens
   - Click "Aufnahme" button again → popup closes
   - Click "Format" button → Format popup opens
   - Click "Aufnahme" button → Format closes, Aufnahme opens

3. **Test popup sizing:**
   - Open various popups in both 9:16 and 16:9 modes
   - Verify they are properly sized and centered
   - Verify they don't overlap with toolbar

4. **Test content area:**
   - Switch between 9:16 and 16:9 modes
   - Verify images fill the available space without overlapping toolbar
   - Verify no white/black bars appear unexpectedly

## Files Changed
- `main.py` (only file modified)

## Commits
1. Initial plan
2. Implement vertical toolbar for 9:16 portrait mode with proper positioning
3. Adapt FormatSelectionPopup sizing for portrait mode
