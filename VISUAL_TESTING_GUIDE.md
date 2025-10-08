# Visual Testing Guide - Portrait Toolbar Implementation

This guide helps you visually verify that the 9:16 portrait toolbar implementation is working correctly.

## Expected Visual States

### 16:9 Mode (Landscape) - Toolbar at Bottom

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                        SLIDESHOW                            │
│                     (Images displayed                       │
│                      with fit_mode='cover')                 │
│                                                             │
│                                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│ [Zeiten][Aufnahme][Format][Galerie][Einstellungen][Logout]...│ ← 60px height
└─────────────────────────────────────────────────────────────┘
   ↑ All buttons horizontal, text readable left-to-right
```

**What to check:**
- ✅ Toolbar spans full width at bottom
- ✅ Buttons arranged horizontally
- ✅ Text is horizontal and readable
- ✅ Content fills area above toolbar
- ✅ No vertical toolbar on right or left

---

### 9:16 Mode (Portrait) - Toolbar on Right

```
┌────────────────────────────────────────────────┬──────────┐
│                                                │    Z     │
│                                                │    e     │
│                                                │    i     │
│                                                │    t     │
│                                                │    e     │
│          SLIDESHOW                             │    n     │
│        (Images displayed                       │          │
│      with fit_mode='cover')                    │    A     │
│                                                │    u     │
│                                                │    f     │
│                                                │    n     │
│                                                │    a     │
│                                                │    h     │
│                                                │    m     │
│                                                │    e     │
│                                                │          │
│                                                │    F     │
│                                                │    o     │
│                                                │    r     │
│                                                │    m     │
│                                                │    a     │
│                                                │    t     │
└────────────────────────────────────────────────┴──────────┘
                                                      ↑
                                                  110px width
                                              Text rotated 270°
                                         (readable top-to-bottom)
```

**What to check:**
- ✅ Toolbar on RIGHT edge (not bottom)
- ✅ Toolbar width ~110 pixels
- ✅ Buttons stacked vertically
- ✅ Text rotated 270° (readable from top to bottom when looking at right edge)
- ✅ Text baseline parallel to device bottom edge
- ✅ Content fills area to LEFT of toolbar
- ✅ Content does NOT extend behind toolbar
- ✅ No horizontal toolbar at bottom

---

## Toggle Behavior Testing

### Scenario 1: Opening and Closing Same Item

1. **Start**: No panel open
2. **Click "Zeiten"**: Schedule editor opens as overlay
3. **Click "Zeiten" again**: Schedule editor closes
4. **Result**: ✅ Back to no panel open

### Scenario 2: Switching Between Items

1. **Start**: No panel open
2. **Click "Galerie"**: Gallery editor opens
3. **Click "Zeiten"**: Gallery closes, schedule editor opens
4. **Click "Zeiten" again**: Schedule editor closes
5. **Result**: ✅ Back to no panel open

### Scenario 3: Popup Modals

1. **Click "Aufnahme"**: Recording popup opens (modal with dark overlay)
2. **Verify "Schließen" button is visible and clickable**
3. **Click "Aufnahme" again**: Popup closes
4. **Click "Format"**: Format selection popup opens
5. **Click "Format" again**: Popup closes
6. **Result**: ✅ All popups toggle correctly

---

## Modal Positioning Tests

### In 16:9 Mode

**Expected**: Modals appear centered in viewport, NOT rotated

1. Open "Aufnahme" popup
   - Should be centered horizontally and vertically
   - "Schließen" button at bottom of popup
   - Text is horizontal and readable

2. Open "Format" popup
   - Should be centered
   - Buttons arranged vertically
   - Text is horizontal

3. Open "Einstellungen" popup
   - Should be centered
   - All controls visible and accessible

### In 9:16 Mode

**Expected**: Modals rotate 90° CW around their CENTER, positioned correctly

1. Open "Aufnahme" popup
   - Should appear in center of screen
   - Rotated 90° CW so it's readable in portrait
   - "Schließen" button visible and clickable
   - NOT positioned off-screen or clipped

2. Open "Format" popup
   - Should be centered and rotated
   - Both format buttons visible
   - "Schließen" button accessible

3. Open "Einstellungen" popup
   - Should be centered and rotated
   - All settings controls visible
   - Sliders functional

---

## Content Area Tests

### In 16:9 Mode

**Expected**: Content fills (width=1280, height=660) starting at y=60

1. Display an image
   - Image should fill from left edge to right edge
   - Image should fill from toolbar top to window top
   - No gap on right side
   - No gap above toolbar

### In 9:16 Mode

**Expected**: Content fills (width=610, height=1280) starting at x=0

1. Display an image
   - Image should fill from left edge to toolbar left edge
   - Image should fill from bottom to top
   - No gap on right side (toolbar occupies it)
   - No content bleeding behind toolbar

---

## Orientation Switching Test

### Test Sequence

1. **Start in 16:9**
   - Toolbar at bottom, horizontal
   - Content fills above toolbar
   
2. **Click "Format"**
   - Format selection popup opens centered
   
3. **Click "Vertikal (9:16)"**
   - Window changes to 720x1280 (if not fullscreen)
   - Toolbar moves to right side, becomes vertical
   - Content reflows to left of toolbar
   - Current image reloads with 9:16 filter
   
4. **Verify UI state**
   - Toolbar on right ✅
   - Buttons vertical with rotated text ✅
   - Content area correct ✅
   
5. **Click "Format" again**
   - Format popup opens (rotated, centered) ✅
   
6. **Click "Horizontal (16:9)"**
   - Window changes to 1280x720
   - Toolbar moves to bottom, becomes horizontal
   - Content reflows above toolbar
   - Current image reloads with 16:9 filter
   
7. **Verify UI state**
   - Toolbar at bottom ✅
   - Buttons horizontal ✅
   - Content area correct ✅

---

## Common Issues to Watch For

### ❌ Issue: Toolbar still at bottom in 9:16
**Expected**: Toolbar should be on RIGHT side in 9:16 mode
**Check**: Look at `_apply_layout()` - should create `vertical=True` toolbar for 9:16

### ❌ Issue: Text not rotated in vertical toolbar
**Expected**: Button text should be rotated 270° (top-to-bottom readable)
**Check**: VerticalButton should be used, rotation_angle=270

### ❌ Issue: Content extends behind toolbar in 9:16
**Expected**: Content width should be (window_width - toolbar_width)
**Check**: `_resize_image()` should subtract toolbar width in 9:16

### ❌ Issue: Modal positioned off-screen in 9:16
**Expected**: Modal should rotate around its center and be visible
**Check**: `RotatedModalView._update_rotation()` should use center-based transform

### ❌ Issue: Clicking toolbar item doesn't toggle
**Expected**: Second click should close the panel/popup
**Check**: `current_popup_type` should be set and checked in open methods

### ❌ Issue: "Schließen" button not clickable in Aufnahme
**Expected**: Button should always be on top and clickable
**Check**: Modal has proper `overlay_color` and Z-order

---

## Quick Visual Checklist

Use this checklist while testing:

### 16:9 Mode
- [ ] Toolbar at bottom (not right)
- [ ] Toolbar height ~60px
- [ ] Buttons horizontal with horizontal text
- [ ] Content fills above toolbar
- [ ] Clicking Zeiten opens/closes schedule editor
- [ ] Clicking Galerie opens/closes gallery editor
- [ ] All popups centered and readable

### 9:16 Mode
- [ ] Toolbar on right (not bottom)
- [ ] Toolbar width ~110px
- [ ] Buttons vertical with rotated text (top-to-bottom)
- [ ] Content fills to left of toolbar
- [ ] Clicking Aufnahme opens/closes popup
- [ ] "Schließen" button always clickable
- [ ] All popups rotated and centered
- [ ] No horizontal toolbar at bottom

### Toggle Behavior (both modes)
- [ ] Clicking same item twice opens then closes
- [ ] Switching items closes previous
- [ ] Works for all items: Zeiten, Aufnahme, Format, Galerie, Einstellungen

### Persistence (both modes)
- [ ] Switch to 9:16, restart app → starts in 9:16
- [ ] Switch to 16:9, restart app → starts in 16:9
- [ ] Aspect ratio saved in image_meta.json

---

## Screenshots Checklist

To fully verify the implementation, take screenshots of:

1. **16:9 with toolbar at bottom**
2. **9:16 with toolbar on right** (showing vertical rotated text)
3. **9:16 with Aufnahme popup open** (showing proper centering and rotation)
4. **9:16 with Galerie open** (showing overlay positioning)
5. **Toggle behavior** (before/after clicking same button)

---

## Performance Checks

- [ ] Images load quickly in both modes
- [ ] No lag when switching orientations
- [ ] Smooth transitions between images
- [ ] Toolbar buttons respond immediately
- [ ] No memory leaks with repeated toggle actions

---

This guide should help you systematically verify all aspects of the portrait toolbar implementation. If any item doesn't match the expected behavior, refer to the implementation details in `PORTRAIT_TOOLBAR_IMPLEMENTATION.md`.
