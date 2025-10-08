# PR: 9:16 Portrait Layout Refinements and UI Consistency

## Summary

This PR implements the user's clarified requirements for 9:16 portrait mode UI:

- **9:16 mode**: Vertical toolbar on the RIGHT side with properly rotated labels (text baseline parallel to device bottom edge)
- **16:9 mode**: Horizontal toolbar at BOTTOM (unchanged from current implementation)
- **Toggle behavior**: Clicking the same toolbar item again closes its panel/popup
- **Center-based modal rotation**: Modals rotate around their center in portrait mode for proper positioning
- **Consistent layout**: All UI elements (Zeiten, Aufnahme, Format, Galerie, Einstellungen) adapt correctly to both aspect ratios

## Problem Statement

Previously, the toolbar was positioned horizontally at the bottom for **both** 16:9 and 9:16 modes. However, the user clarified that:

1. In 9:16 portrait mode, the toolbar should be **vertical on the RIGHT** with text rotated so it's readable when the physical screen is rotated
2. Clicking the same toolbar item should close its panel (toggle behavior)
3. Modals were not rotating correctly around their center in portrait mode
4. Content area calculations were not accounting for the right-side toolbar in 9:16

## Changes Overview

### Core Changes (main.py)

1. **`_apply_layout()` (lines 3310-3345)**
   - Creates vertical toolbar for 9:16, horizontal for 16:9
   - Logs which toolbar type was created

2. **`_create_toolbar()` (lines 3402-3443)**
   - Respects `vertical` parameter instead of ignoring it
   - Positions toolbar on right (`pos_hint={"right": 1}`) for 9:16
   - Positions toolbar at bottom (`pos_hint={"bottom": 1}`) for 16:9

3. **`_resize_image()` (lines 3375-3402)**
   - Subtracts toolbar width from right in 9:16 mode
   - Subtracts toolbar height from bottom in 16:9 mode
   - Content fills correctly in both orientations

4. **Toggle Behavior (lines 3223-3540)**
   - Added `current_popup` and `current_popup_type` tracking
   - New `_close_current_popup_or_overlay()` helper method
   - Updated all `open_*` methods to implement toggle behavior

5. **Modal Rotation (lines 239-267)**
   - `RotatedModalView._update_rotation()` now uses center-based transform
   - Transform sequence: translate to center → rotate → translate back
   - Ensures modals are properly positioned in portrait mode

6. **VerticalButton (lines 718-750)**
   - Updated documentation to clarify 270° rotation
   - Text baseline parallel to device bottom edge for natural readability

7. **Modal Visibility (line 224)**
   - Added `overlay_color` to ensure proper modal visibility

### New Files

1. **`verify_portrait_toolbar.py`**
   - Automated verification script with 6 test suites
   - Verifies toolbar positioning, toggle behavior, content area, modal rotation, VerticalButton, and persistence
   - All tests pass ✅

2. **`PORTRAIT_TOOLBAR_IMPLEMENTATION.md`**
   - Comprehensive documentation with before/after code samples
   - Architecture diagrams for both orientations
   - Manual testing checklist
   - Benefits and breaking changes summary

### Modified Files

1. **`image_meta.json`**
   - Changed to 9:16 for testing purposes
   - Can be changed via UI (Format selection)

## Testing

### Automated Tests

Run the verification script:

```bash
python3 verify_portrait_toolbar.py
```

**Expected Result**: All 6 tests pass ✅

```
============================================================
Test Summary
============================================================
✅ PASS: Toolbar Positioning Logic
✅ PASS: Toolbar Toggle Behavior
✅ PASS: Content Area Calculation
✅ PASS: Modal Rotation
✅ PASS: VerticalButton Implementation
✅ PASS: Aspect Ratio Persistence

Results: 6/6 tests passed
```

### Manual Testing Checklist

#### Testing 16:9 Mode

1. Start the app (or switch to 16:9 via Format selection)
2. Verify toolbar appears at bottom (horizontal)
3. Click "Zeiten" - schedule editor should open
4. Click "Zeiten" again - schedule editor should close (toggle)
5. Click "Galerie" - gallery editor should open (and Zeiten closes if open)
6. Click "Galerie" again - gallery editor should close
7. Repeat for Aufnahme, Format, Einstellungen
8. Verify content fills area above toolbar
9. Verify all modals appear centered and readable

#### Testing 9:16 Mode

1. Click "Format" in toolbar
2. Select "Vertikal (9:16)"
3. Verify toolbar appears on right side (vertical)
4. Verify button labels are rotated and readable (text parallel to device bottom)
5. Click each toolbar button - verify all are clickable with proper ripple effects
6. Click "Aufnahme" - recording popup should open
7. Verify "Schließen" button is visible and clickable (not covered/rotated out)
8. Click "Aufnahme" again - popup should close (toggle)
9. Click "Zeiten" - schedule editor should open
10. Click "Zeiten" again - should close
11. Verify content fills area to left of toolbar (not full width)
12. Verify no leftover horizontal toolbar at bottom
13. Open each modal/popup and verify they rotate properly around center
14. Verify modals are readable and positioned correctly

#### Slideshow Functionality

1. In both 16:9 and 9:16 modes:
   - Verify images load reliably
   - Verify no white frames
   - Verify transitions work smoothly
   - Open Lightbox - verify it uses fit_mode='contain'
   - Verify Lightbox opens/closes without hangs

#### Persistence

1. Switch to 9:16 mode
2. Close and restart the app
3. Verify app starts in 9:16 mode with vertical toolbar on right
4. Switch to 16:9 mode
5. Close and restart the app
6. Verify app starts in 16:9 mode with horizontal toolbar at bottom

## How to Test This PR

### Option 1: Fetch and Test Locally

```bash
# Fetch the PR branch
git fetch origin pull/<PR_NUMBER>/head:pr-portrait-toolbar

# Checkout the branch
git checkout pr-portrait-toolbar

# Run verification
python3 verify_portrait_toolbar.py

# Run the app
python3 main.py
```

### Option 2: Direct Branch Checkout

```bash
# Fetch the branch
git fetch origin copilot/refactor-portrait-layout-ui-consistency

# Checkout the branch
git checkout copilot/refactor-portrait-layout-ui-consistency

# Run verification
python3 verify_portrait_toolbar.py

# Run the app
python3 main.py
```

## Architecture Diagrams

### 16:9 Mode (Landscape)
```
┌─────────────────────────────────────────────┐
│                                             │
│                                             │
│            Content Area (1280x660)          │
│          Images + Overlays/Modals           │
│                                             │
│                                             │
└─────────────────────────────────────────────┘
┌─────────────────────────────────────────────┐
│  Zeiten | Aufnahme | Format | Galerie | ... │ ← Toolbar (60px height)
└─────────────────────────────────────────────┘
```

### 9:16 Mode (Portrait)
```
┌────────────────────────┬──┐
│                        │Z │
│                        │e │
│   Content Area         │i │
│   (610x1280)           │t │
│                        │e │
│   Images +             │n │
│   Overlays/Modals      │  │
│                        │A │
│                        │u │
│                        │f │
│                        │n │
│                        │. │
│                        │  │
│                        │F │
│                        │o │
│                        │r │
│                        │m │
│                        │. │
│                        │  │
│                        │G │
│                        │a │
│                        │l │
│                        │. │
└────────────────────────┴──┘
                          ↑
                    Toolbar (110px width)
                    Text rotated 270°
```

## Breaking Changes

**None.** This implementation maintains full backward compatibility with 16:9 mode while adding proper 9:16 support.

## Benefits

1. ✅ **Correct Portrait Layout**: 9:16 mode has vertical toolbar on right as requested by user
2. ✅ **Intuitive Toggle**: Users can close panels by clicking toolbar items again
3. ✅ **Proper Content Area**: Images fill available space correctly in both modes
4. ✅ **Better Modal Positioning**: Center-based rotation ensures modals are always visible
5. ✅ **Natural Text Orientation**: Labels are readable when device is physically rotated
6. ✅ **Consistent UX**: All UI elements adapt properly to aspect ratio changes
7. ✅ **No Toolbar at Bottom in 9:16**: Fixed the issue where horizontal toolbar appeared in portrait mode

## Related Issues

This PR addresses the user's clarified requirements that differ from the previous implementation where toolbar was always at bottom for both modes. The new implementation provides:

- Vertical toolbar on right for 9:16 (not horizontal at bottom)
- Proper label rotation for readability in portrait orientation
- Toggle behavior for all toolbar items
- Center-based modal rotation for proper positioning

## Files Changed

- `main.py` - Core implementation (132 insertions, 34 deletions)
- `verify_portrait_toolbar.py` - NEW automated verification script
- `PORTRAIT_TOOLBAR_IMPLEMENTATION.md` - NEW comprehensive documentation
- `image_meta.json` - Set to 9:16 for testing (can be changed via UI)

## Commits

1. `808a554` - Initial plan for 9:16 portrait layout refinements
2. `e5e16e5` - Implement 9:16 vertical toolbar on right with toggle behavior
3. `397e72b` - Add verification script and documentation for portrait toolbar

## Next Steps After Merge

1. User testing with physical portrait display
2. Screenshot verification of UI states in both orientations
3. Performance testing with large image sets
4. Accessibility review for button hit areas in portrait mode

## Questions for Reviewer

1. Should we add screenshots to this PR showing the toolbar in both orientations?
2. Are there any other UI elements that need 9:16-specific adaptations?
3. Should we add a visual indicator in the UI showing which orientation mode is active?

---

**Ready for Review** ✅

All automated tests pass, code is syntactically correct, and implementation follows the user's clarified requirements.
