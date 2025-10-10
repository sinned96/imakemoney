# Portrait UI Finalization - Testing Guide

This document describes the changes made to finalize the portrait (9:16) UI behavior and provides testing instructions.

## Changes Summary

This PR consolidates and finalizes portrait UI features, superseding PRs #62–#64 and referencing #65.

### 1. Centered Modals with Overlay ✅

**All modals now use centered ModalView with proper sizing:**
- SettingsRootPopup
- GlobalDurationPopup
- FormatSelectionPopup
- GeneralSettingsPopup
- AufnahmePopup (already implemented)

**Implementation:**
- Full-screen modal with `size_hint=(1, 1)`
- Semi-transparent background (0.7 alpha) for dim overlay
- AnchorLayout centers the content panel
- Portrait sizing factors: width = 0.62 × content width, height = 0.86 × content height
- Minimum constraints: width ≥ 320dp, height ≥ 260dp
- Safe margins respected (48dp implicit in factor calculations)

**Changes:**
- All modals updated from fixed-size `size_hint=(None, None)` to full-screen
- Added AnchorLayout wrapper for centered content
- Applied portrait sizing factors for 9:16 mode
- Increased background alpha from 0.55 to 0.7 for better contrast

### 2. Transform Stripping from Modal Contents ✅

**Helper method added to RotatedModalView:**
- `_strip_transforms_from_content()` removes any accidental rotation/scale/translate transforms
- Recursively processes widget tree
- Preserves VerticalButton rotations (toolbar labels only)
- Resets angle/rotation attributes
- Only modal itself rotates; content does not

**Why this matters:**
- Ensures dialog content is never rotated
- Only toolbar labels should be rotated (-90° for vertical orientation)
- Prevents double-rotation issues

### 3. Global Single-Open Panel Management ✅

**Existing implementation verified:**
- `_close_current_panel()` method closes any open panel
- `_on_toolbar_item_pressed()` handles toggle and single-open logic
- Pressing same item twice toggles off
- Opening different item closes previous then opens new
- All toolbar items use this helper

**Enhancement:**
- Added `_close_current_panel()` call at start of `_apply_layout()`
- Ensures panels close on aspect switch (16:9 ↔ 9:16)

### 4. Portrait Toolbar and Restack ✅

**Toolbar behavior:**
- 9:16 mode: Vertical toolbar docked on RIGHT, width ~108dp
- 16:9 mode: Horizontal toolbar at bottom
- Toolbar always added last via `_bring_toolbar_to_front()`
- Content area width adjusted: `Window.width - toolbar_width` in 9:16

**Implementation:**
- `_create_toolbar(vertical=False)` parameter
- `VerticalButton` class for rotated labels (270° = -90°)
- Toolbar positioned with `pos_hint = {"right": 1, "top": 1}` for portrait
- Z-order maintained by re-adding toolbar as last child

### 5. Portrait Gallery Tweaks ✅

**Gallery adaptations for 9:16:**
- Columns: 2–3 depending on width
  - 3 columns if `Window.width > 600dp`
  - 2 columns otherwise
- Tighter spacing: `dp(10)` instead of `dp(14)`
- Maintains 8 columns in 16:9 mode

### 6. Logging Hygiene ✅

**Added concise logs:**
- Layout apply: "Applying layout for aspect ratio: {ratio}, window size: {w}x{h}"
- Panel open: "Opening {panel_name} panel"
- Panel close: "Closed panel: {panel_id}"
- Toolbar restack: "Toolbar restacked to front (z-order)"
- Modal lifecycle: "modal open centered size=", "modal dismissed"

**Unicode fixes in Aufnahme.py:**
- Replaced `ℹ` with `[INFO]` for latin-1 terminal compatibility
- Prevents `UnicodeEncodeError` on non-UTF-8 terminals

### 7. ESC/Back Key Support ✅

**All modals now handle ESC key:**
- Key code 27 (ESC/Back) dismisses modal
- `_on_key_down()` handler added to all modal classes
- Proper binding on modal open
- Proper unbinding on modal dismiss
- Works for: Settings, Duration, Format, General Settings, Aufnahme

## Testing Instructions

### Manual Testing

#### Test 1: Modal Appearance in Portrait (9:16)

1. Set application to portrait mode (9:16)
2. Open each modal:
   - Press "Aufnahme" → Should show centered modal with dim overlay
   - Press "Einstellungen" → Should show centered settings modal
   - From Settings, press "Bilddauer" → Should show centered duration modal
   - From Settings, press "Allgemein" → Should show centered general settings modal
   - Press "Format" → Should show centered format selection modal

**Expected:**
- Each modal is centered on screen
- Background is semi-transparent (0.7 alpha)
- Modal size is proportional: ~62% width, ~86% height
- Content is not rotated (text reads normally)
- Close button is visible and accessible

#### Test 2: Modal Toggle Behavior

1. Press "Aufnahme" → Modal opens
2. Press "Aufnahme" again → Modal closes (toggle)
3. Press "Aufnahme" → Modal opens
4. Press "Format" → Aufnahme closes, Format opens
5. Press "Format" again → Format closes

**Expected:**
- Only one panel/modal open at a time
- Pressing same button toggles the panel
- Opening different panel closes previous one

#### Test 3: ESC Key Dismissal

1. Open any modal (Aufnahme, Settings, Format, etc.)
2. Press ESC key

**Expected:**
- Modal immediately dismisses
- No errors in console

#### Test 4: Aspect Ratio Switch

1. Open "Aufnahme" modal
2. Close it
3. Press "Format" button
4. Select "Vertikal (9:16)" or "Horizontal (16:9)" to switch

**Expected:**
- Any open panel closes before switch
- Toolbar rebuilds with correct orientation
- Toolbar is visible (top of z-order)
- No overlapping UI elements

#### Test 5: Portrait Toolbar

**In 9:16 mode:**
1. Check toolbar position: Should be on RIGHT edge
2. Check toolbar width: Should be ~108dp
3. Check button text: Should be rotated -90° (readable from top to bottom)
4. Check content area: Should not overlap toolbar

**In 16:9 mode:**
1. Check toolbar position: Should be at BOTTOM
2. Check button text: Should be horizontal

**Expected:**
- Toolbar always visible in both modes
- Content area properly sized to avoid overlap
- Button labels correctly oriented

#### Test 6: Gallery in Portrait

1. Set to portrait mode (9:16)
2. Press "Galerie" button
3. Select a mode (e.g., "Tag" or "Nacht")

**Expected:**
- Gallery shows 2-3 columns (depending on width)
- Spacing is tighter than landscape
- Image tiles are visible and clickable

#### Test 7: No Double Rotation

1. Set to portrait mode (9:16)
2. Open any modal
3. Check that dialog content (text, buttons) is NOT rotated
4. Only toolbar labels should be rotated

**Expected:**
- Modal content reads normally (not rotated)
- Only toolbar button labels are rotated
- No double-rotation artifacts

### Automated Testing

Run the verification script:

```bash
python3 verify_portrait_ui_final.py
```

**Expected output:**
```
======================================================================
Results: 7/7 tests passed
======================================================================
✅ PASS: Modal Centered Layout
✅ PASS: ESC Key Handling
✅ PASS: Panel Management
✅ PASS: Portrait Toolbar
✅ PASS: Gallery Portrait Mode
✅ PASS: Unicode Fixes
✅ PASS: Transform Stripping
======================================================================
🎉 All tests passed! Portrait UI finalization complete.
```

### Log Verification

Check projekt.log for proper logging:

```bash
tail -f /home/pi/Desktop/v2_Tripple\ S/projekt.log
```

**Expected log entries:**
- "Applying layout for aspect ratio: 9:16, window size: ..."
- "Opening {panel_name} panel"
- "Settings modal open centered size=..."
- "Modal dismissed"
- "Closed panel: {panel_id}"
- "Toolbar restacked to front (z-order)"
- "Removed old toolbar before rebuild"

## Acceptance Criteria

✅ **1. Centered Modals**
- In 9:16, all modals (Aufnahme, Zeiten, Format, Einstellungen) open as centered overlays
- Correct dimensions: 0.62×w, 0.86×h with minimums
- Dim background (0.7 alpha)
- Close button and ESC work

✅ **2. Toggle Behavior**
- Pressing Aufnahme opens modal
- Pressing again closes it (toggle)
- Same for all toolbar items

✅ **3. Single-Open Panel**
- Only one panel open at a time
- Opening different panel closes previous

✅ **4. Aspect Switch**
- Switching 16:9 ↔ 9:16 closes any open panel
- Toolbar cleanly rebuilds
- Toolbar visible (correct Z-order)

✅ **5. Portrait Toolbar**
- In 9:16: vertical toolbar on RIGHT (~108dp wide)
- In 16:9: horizontal toolbar at BOTTOM
- Labels rotated -90° in portrait only

✅ **6. No Content Rotation**
- Only toolbar labels are rotated
- Dialog content is NOT rotated

✅ **7. Gallery Adaptation**
- 2-3 columns in portrait
- Tighter spacing

✅ **8. Logging**
- Logs reflect behavior
- No Unicode symbol issues in Aufnahme.py

## Regression Testing

Verify no regressions in 16:9 mode:
- [ ] Toolbar at bottom, horizontal
- [ ] All panels open and close correctly
- [ ] Gallery shows 8 columns
- [ ] No rotation artifacts

## Files Changed

| File | Purpose |
|------|---------|
| `main.py` | Core implementation: modals, toolbar, gallery, logging |
| `Aufnahme.py` | Unicode symbol fix (ℹ → [INFO]) |
| `verify_portrait_ui_final.py` | Automated verification script |
| `PORTRAIT_UI_FINAL_TESTING.md` | This testing guide |

## Related PRs

- Supersedes: #62, #63, #64 (older portrait PRs)
- References: #65 (portrait layout and popup management)
- Builds on: #61 (slideshow 9:16 image loading fix)

## Summary

This PR provides a consolidated, final implementation of portrait UI behavior with:
- Proper centered modals using AnchorLayout
- Correct sizing factors for portrait mode
- ESC key support throughout
- Single-open panel management
- Portrait toolbar on the right
- Gallery adaptation for portrait
- Comprehensive logging
- No Unicode terminal issues
- Transform cleanup to prevent double rotation

All automated tests pass. Ready for manual testing and merge.
