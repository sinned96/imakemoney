# PR Testing Guide - Portrait UI Refinements

## Quick Start

This PR is available on the branch: `copilot/fix-portrait-ui-toolbar-issues`

### Option 1: Test via Branch Name
```bash
# Fetch the branch
git fetch origin copilot/fix-portrait-ui-toolbar-issues

# Check it out
git checkout copilot/fix-portrait-ui-toolbar-issues
```

### Option 2: Test via PR Number (if PR is created)
```bash
# Replace <PR_NUMBER> with actual PR number from GitHub
git fetch origin pull/<PR_NUMBER>/head:pr-portrait-finetune
git checkout pr-portrait-finetune
```

## What's Been Fixed

### 1. Toolbar Positioning ✅
- **9:16 (Portrait)**: Vertical toolbar on RIGHT edge, flush alignment, 100dp width
- **16:9 (Landscape)**: Horizontal toolbar at BOTTOM (no changes)

### 2. Toolbar Text Orientation ✅
- **Rotation**: -90° counterclockwise (configurable)
- **Reading**: Top-to-bottom when toolbar is on right
- **Physical rotation**: Text reads left-to-right when screen held in portrait

### 3. Popup Toggle Behavior ✅
- Click toolbar item once: Opens popup
- Click same toolbar item again: Closes popup (toggle!)
- Click different toolbar item: Closes previous, opens new
- Close button always works (no freeze)

### 4. Portrait Content Layout ✅
- Gallery: 5 columns instead of 8 (fits narrower width)
- Images: Adjusted for right-side toolbar
- All popups: Adapt size for portrait dimensions

### 5. Configuration Constants ✅
Easy adjustment without code changes (main.py lines 301-304):
```python
PORTRAIT_TOOLBAR_WIDTH = dp(100)  # Toolbar width
PORTRAIT_LABEL_ANGLE = -90        # Text rotation
PORTRAIT_LABEL_FLIP = False       # Horizontal flip
```

## Testing Steps

### Quick Verification (Automated)
```bash
python3 verify_portrait_ui.py
```
Should show: "🎉 All tests passed! Portrait UI refinements are properly implemented."

### Manual Testing

#### A. Test 16:9 Mode (Ensure No Regression)
1. Start app (should default to 16:9)
2. Check toolbar at bottom with horizontal text
3. Click each toolbar button:
   - ✓ Zeiten (Schedule)
   - ✓ Aufnahme (Recording)
   - ✓ Format (Aspect ratio)
   - ✓ Galerie (Gallery - 8 columns)
   - ✓ Einstellungen (Settings)
4. Verify all popups open and close correctly
5. Check images display correctly (no white/black borders)

#### B. Switch to 9:16 Mode
1. Click **Format** toolbar button
2. Click **Vertikal (9:16)**
3. Popup closes, app switches to portrait layout

#### C. Test 9:16 Portrait Mode

**Toolbar:**
- [ ] Toolbar appears on RIGHT edge of screen
- [ ] Toolbar is flush (no gap between toolbar and screen edge)
- [ ] Toolbar width is consistent (100dp)
- [ ] Text orientation readable (see "Text Orientation Check" below)
- [ ] All buttons clickable and responsive

**Text Orientation Check:**
- Physically rotate your display 90° clockwise (to portrait orientation)
- Toolbar text should now read naturally left-to-right
- OR: If text is wrong, adjust `PORTRAIT_LABEL_ANGLE` (see Configuration below)

**Toggle Behavior:**
1. Click **Aufnahme** → popup opens
2. Click **Aufnahme** again → popup closes (toggle!)
3. Click **Aufnahme** → popup opens
4. Click **Schließen** button → popup closes
5. Repeat for Format, Einstellungen

**Popup Switching:**
1. Click **Aufnahme** → opens
2. Click **Format** → Aufnahme closes, Format opens
3. Click **Einstellungen** → Format closes, Settings opens
4. Only one popup open at a time ✓

**Gallery:**
- [ ] Gallery shows 5 columns (not 8)
- [ ] All thumbnails visible
- [ ] Scrolling works smoothly
- [ ] No horizontal overflow

**Content Area:**
- [ ] Images fill space to left of toolbar
- [ ] No overlap with toolbar
- [ ] Images scale correctly (cover mode)
- [ ] Transitions work smoothly

#### D. Test All Popups in 9:16

**Aufnahme Popup:**
- [ ] Opens centered
- [ ] All controls visible (Start button, image selection, close)
- [ ] "Schließen" button closes popup
- [ ] Recording works (if audio available)
- [ ] No freeze or stuck state

**Zeiten (Schedule) Popup:**
- [ ] Opens centered
- [ ] Time sliders visible and draggable
- [ ] "Speichern & Schließen" saves and closes
- [ ] "Abbrechen" cancels and closes

**Format Popup:**
- [ ] Shows current format
- [ ] Can switch between 16:9 and 9:16
- [ ] "Schließen" closes popup

**Galerie (Gallery) Overlay:**
- [ ] Shows 5 columns of thumbnails
- [ ] Can scroll through images
- [ ] Can select mode
- [ ] "Schließen" closes gallery

**Einstellungen (Settings) Popups:**
- [ ] Main settings menu opens
- [ ] "Allgemein" (General) opens sub-popup
- [ ] "Bilddauer" (Duration) opens sub-popup
- [ ] Sliders work
- [ ] "Speichern" saves changes
- [ ] "Zurück" / "Schließen" closes

## Configuration Adjustments

If text orientation isn't perfect, adjust these constants in `main.py` (lines 301-304):

### Scenario 1: Text Upside Down
```python
PORTRAIT_LABEL_ANGLE = 90  # Change from -90 to 90
```

### Scenario 2: Text Reads Bottom-to-Top
```python
PORTRAIT_LABEL_ANGLE = -90  # Keep current
PORTRAIT_LABEL_FLIP = True  # Add horizontal flip
```

### Scenario 3: Text Mirrored (Glyphs Reversed)
```python
PORTRAIT_LABEL_FLIP = False  # Set back to False
```

### Scenario 4: Toolbar Too Wide/Narrow
```python
PORTRAIT_TOOLBAR_WIDTH = dp(110)  # Increase from 100
# or
PORTRAIT_TOOLBAR_WIDTH = dp(90)   # Decrease from 100
```

After adjusting constants, restart the app to see changes.

## Expected Behavior Summary

| Mode  | Toolbar Position | Toolbar Size | Text Orientation | Content Area |
|-------|------------------|--------------|------------------|--------------|
| 16:9  | Bottom           | Full width × 60dp | Horizontal | Above toolbar |
| 9:16  | Right edge       | 100dp × Full height | -90° rotated | Left of toolbar |

## Troubleshooting

### Issue: Toolbar not on right edge in 9:16
**Check:**
- Switch to 9:16 via Format dialog
- Check logs for: "Created toolbar at RIGHT (vertical) for 9:16 mode"
- If shows BOTTOM, revert and report

### Issue: Text orientation wrong
**Solution:**
- Adjust `PORTRAIT_LABEL_ANGLE` in main.py
- Try values: -90, 90, -270, 270
- Restart app after each change

### Issue: Popup doesn't close
**Check:**
- Click "Schließen" button
- Or click same toolbar item again (toggle)
- Check logs for: "Scheduled popup dismiss"

### Issue: Multiple popups open
**Solution:**
- This should not happen (fixed in PR)
- If occurs, report with reproduction steps

### Issue: Gallery shows 8 columns in 9:16
**Check:**
- Verify you're in 9:16 mode (Format dialog)
- Check logs for aspect ratio
- Should show 5 columns in 9:16

## Files Changed
- `main.py` (~135 lines changed)
- `verify_portrait_ui.py` (new verification script)
- `PORTRAIT_UI_REFINEMENT_SUMMARY.md` (new documentation)
- `PR_TESTING_GUIDE.md` (this file)

## Rollback
If issues occur, rollback to main branch:
```bash
git checkout main
```

## Reporting Issues
When reporting issues, please include:
1. Mode (16:9 or 9:16)
2. Issue description
3. Screenshot if possible
4. Log output (projekt.log)
5. Configuration values (PORTRAIT_LABEL_ANGLE, etc.)

## Success Criteria
All these should work:
- ✅ 16:9 mode: No regressions, toolbar at bottom
- ✅ 9:16 mode: Toolbar on right edge, flush, 100dp width
- ✅ Text readable when screen physically rotated to portrait
- ✅ All toolbar buttons work
- ✅ Popup toggle behavior (click same item to close)
- ✅ Popup switching (opening new closes previous)
- ✅ All close buttons work (no freeze)
- ✅ Gallery shows 5 columns in portrait
- ✅ Images fill correct content area
- ✅ All transitions smooth

## Questions?
See `PORTRAIT_UI_REFINEMENT_SUMMARY.md` for detailed implementation notes.

---
**Branch**: `copilot/fix-portrait-ui-toolbar-issues`  
**Author**: GitHub Copilot Agent  
**Co-authored-by**: sinned96
