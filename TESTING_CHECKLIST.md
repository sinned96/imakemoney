# Testing Checklist for Portrait Mode Fixes

## Pre-Test Setup

1. **Fetch and checkout the PR branch:**
   ```bash
   git fetch origin pull/<PR_NUMBER>/head:pr-portrait-textflip
   git checkout pr-portrait-textflip
   ```

2. **Verify code integrity:**
   ```bash
   python3 verify_portrait_fixes.py
   ```
   Expected: "✓ All checks passed!"

3. **Start the application:**
   ```bash
   python3 main.py
   ```

## Test Suite

### A. Toolbar Tests (16:9 Mode)

**Initial State:**
- [ ] Application starts in 16:9 mode (landscape)
- [ ] Toolbar visible at bottom of screen
- [ ] Toolbar is horizontal orientation
- [ ] All toolbar buttons visible: [Zeiten] [Aufnahme] [Format] [Galerie] [Einstellungen] [Logout] [Exit]
- [ ] Button text is horizontal and clearly readable
- [ ] Toolbar height approximately 60dp

**Button Interaction:**
- [ ] Click each button - all are responsive
- [ ] Hover over buttons shows proper hitbox (no offset)
- [ ] Buttons have visual feedback on press

### B. Toolbar Tests (9:16 Mode)

**Switch to Portrait:**
- [ ] Click toolbar button "Format"
- [ ] Select "Vertikal (9:16)"
- [ ] Toolbar moves from bottom to right side
- [ ] Toolbar orientation is now vertical

**Text Orientation (Critical Test):**
- [ ] Physically rotate the display/screen 90° clockwise
  - If testing on Pi with physical display: rotate the actual screen
  - If testing via remote desktop: note that this may not represent actual behavior
- [ ] After rotation, toolbar text should be readable from top to bottom
- [ ] Text should read in natural direction: "Zeiten" starts at top, ends at bottom
- [ ] Text should NOT be upside down or backwards
- [ ] Text should NOT require tilting head to read

**Toolbar Layout:**
- [ ] Toolbar appears on right edge of screen
- [ ] Toolbar width approximately 110dp
- [ ] All buttons visible and evenly spaced
- [ ] Content area uses full width minus toolbar width
- [ ] No overlap between content and toolbar

**Button Interaction:**
- [ ] Click each button - all are responsive
- [ ] Hitboxes match visual button appearance
- [ ] No offset between touch area and button graphics
- [ ] Buttons have visual feedback on press

### C. Content Area Tests

**16:9 Mode:**
- [ ] Images fill area above toolbar
- [ ] No white bars or gaps
- [ ] Images centered and scaled properly (fit_mode='cover')
- [ ] Content height = window height - 60dp

**9:16 Mode:**
- [ ] Images fill area to the left of toolbar
- [ ] No white bars or gaps
- [ ] Images centered and scaled properly
- [ ] Content width = window width - 110dp
- [ ] Full vertical height used

**Slideshow Functionality:**
- [ ] Images transition smoothly in both modes
- [ ] No white frames during transitions
- [ ] Image load logging is concise (no PIL spam)
- [ ] Effects work correctly (if enabled)

### D. Galerie View Tests

**Open Galerie (16:9):**
- [ ] Click "Galerie" button
- [ ] Panel opens in center
- [ ] Panel width approximately 95% of screen
- [ ] Modi list visible on left side
- [ ] Image grid has 8 columns
- [ ] All grid images visible (none cut off)
- [ ] Scroll works if many images
- [ ] Filter button visible and functional
- [ ] Close button works

**Open Galerie (9:16):**
- [ ] Click "Galerie" button
- [ ] Panel opens in center (not overlapping toolbar)
- [ ] Panel width approximately 85% of screen
- [ ] Modi list visible on left side (full height)
- [ ] Image grid has 4 columns
- [ ] All grid images visible (none cut off by toolbar)
- [ ] Grid fits within panel width
- [ ] Scroll works if many images
- [ ] Filter button visible and functional
- [ ] Close button works

**Galerie Functionality:**
- [ ] Click mode name in left list - images update for that mode
- [ ] Click image checkbox - toggles selection
- [ ] Click gear icon on image - opens image settings
- [ ] "Nur Modus-Bilder" filter button toggles correctly
- [ ] Changes trigger "Speichern" button to appear
- [ ] "Speichern" button saves changes successfully

### E. Zeiten (Schedule Editor) Tests

**Open Zeiten (16:9):**
- [ ] Click "Zeiten" button
- [ ] Panel opens in center
- [ ] Panel width approximately 70% of screen
- [ ] "Tag" and "Nacht" rows visible
- [ ] Time displays show current schedule
- [ ] "Bearbeiten" buttons functional
- [ ] "Speichern & Schließen" and "Abbrechen" buttons visible

**Open Zeiten (9:16):**
- [ ] Click "Zeiten" button
- [ ] Panel opens in center (not overlapping toolbar)
- [ ] Panel width approximately 85% of screen (narrower than 16:9)
- [ ] "Tag" and "Nacht" rows fully visible
- [ ] All text readable
- [ ] Time displays show current schedule
- [ ] "Bearbeiten" buttons functional
- [ ] Buttons not cut off

**Zeiten Functionality:**
- [ ] Click "Bearbeiten" for Tag - time picker opens
- [ ] Set start and end times - saves correctly
- [ ] Click "Bearbeiten" for Nacht - time picker opens
- [ ] Set times - saves correctly
- [ ] Click "Speichern & Schließen" - closes with confirmation
- [ ] Click "Abbrechen" - closes without saving

### F. Format Selection Tests

**Open Format (Both Modes):**
- [ ] Click "Format" button
- [ ] Popup opens in center
- [ ] Current format displayed
- [ ] Both buttons visible: "Horizontal (16:9)" and "Vertikal (9:16)"
- [ ] Popup sized appropriately:
  - 16:9 mode: 400×300dp
  - 9:16 mode: 360×320dp (narrower)

**Format Switching:**
- [ ] Click "Horizontal (16:9)" from 9:16 mode
  - [ ] Confirms switch with popup or logging
  - [ ] Toolbar moves to bottom (horizontal)
  - [ ] Content area recalculates
  - [ ] Images rescale properly
- [ ] Click "Vertikal (9:16)" from 16:9 mode
  - [ ] Confirms switch with popup or logging
  - [ ] Toolbar moves to right (vertical)
  - [ ] Content area recalculates
  - [ ] Images rescale properly

### G. Aufnahme (Recording) Tests

**Open Aufnahme (Both Modes):**
- [ ] Click "Aufnahme" button
- [ ] Popup opens in center
- [ ] Title "Audio-Aufnahme + Bild" visible
- [ ] Recording controls visible
- [ ] Image selection visible
- [ ] Popup sized appropriately:
  - 16:9 mode: 600×500dp (wider)
  - 9:16 mode: 500×600dp (narrower, taller)

**Aufnahme Functionality:**
- [ ] Record button starts recording
- [ ] Timer shows elapsed time
- [ ] Stop button ends recording
- [ ] Image selection works
- [ ] Close/cancel button works

### H. Einstellungen (Settings) Tests

**Open Einstellungen (Both Modes):**
- [ ] Click "Einstellungen" button
- [ ] Popup opens with menu
- [ ] "Allgemein" and "Bilddauer" buttons visible
- [ ] Popup sized appropriately:
  - 16:9 mode: 500×480dp
  - 9:16 mode: 450×520dp (narrower, taller)

**Settings Submenus:**
- [ ] Click "Allgemein"
  - [ ] Opens general settings popup
  - [ ] Brightness slider visible and functional
  - [ ] Popup sized appropriately (460×450 in portrait)
  - [ ] Save and back buttons work
- [ ] Click "Bilddauer"
  - [ ] Opens duration settings popup
  - [ ] Duration slider visible and functional
  - [ ] Popup sized appropriately (460×400 in portrait)
  - [ ] Save and back buttons work

### I. Toggle Functionality Tests

**Same Button Toggle (16:9 and 9:16):**
- [ ] Click "Galerie" → Gallery opens
- [ ] Click "Galerie" again → Gallery closes (toggle off)
- [ ] Click "Zeiten" → Schedule opens
- [ ] Click "Zeiten" again → Schedule closes (toggle off)
- [ ] Same for Einstellungen, Aufnahme, Format

**Different Button Switch (16:9 and 9:16):**
- [ ] Click "Galerie" → Gallery opens
- [ ] Click "Zeiten" → Gallery closes, Schedule opens (switch)
- [ ] Click "Einstellungen" → Schedule closes, Settings opens (switch)
- [ ] Click "Aufnahme" → Settings closes, Recording opens (switch)
- [ ] Click "Format" → Recording closes, Format opens (switch)

**Mixed Toggle and Switch:**
- [ ] Click "Galerie" → Gallery opens
- [ ] Click "Zeiten" → Switches to Schedule
- [ ] Click "Zeiten" again → Schedule closes (toggle)
- [ ] Click "Galerie" → Gallery opens
- [ ] Click "Galerie" again → Gallery closes (toggle)

### J. Logging Tests

**Check console/log output for:**
- [ ] Concise aspect ratio confirmation:
  ```
  Applying layout for aspect ratio: 9:16
  ```
- [ ] Toolbar placement logging:
  ```
  Created toolbar at RIGHT (vertical) for 9:16 mode
  ```
  or
  ```
  Created toolbar at BOTTOM (horizontal) for 16:9 mode
  ```
- [ ] Image load confirmations (should be concise)
- [ ] No excessive PIL debug spam
- [ ] Modal rotation state (if using RotatedModalView)

### K. Regression Tests

**Previous Fixes Should Still Work:**
- [ ] Double-click gallery thumbnail opens lightbox (no freeze)
- [ ] Lightbox image loads correctly (no white screen)
- [ ] Lightbox close button works
- [ ] Image fit_mode='cover' scaling correct
- [ ] No manual position calculations causing negative positions
- [ ] Brightness controls work
- [ ] Duration controls work
- [ ] Schedule controls work

### L. Edge Cases

**Rapid Clicking:**
- [ ] Click toolbar buttons rapidly - no duplicate panels
- [ ] Click same button many times - toggles correctly
- [ ] Click different buttons rapidly - switches smoothly

**Mode Switching:**
- [ ] Switch 16:9 → 9:16 → 16:9 multiple times
  - [ ] Toolbar moves correctly each time
  - [ ] Content scales correctly each time
  - [ ] No artifacts or glitches
  - [ ] Memory usage stable

**With Panels Open:**
- [ ] Open Gallery, then switch format → Gallery adapts to new layout
- [ ] Open Settings, then switch format → Settings adapts
- [ ] Open Schedule, then switch format → Schedule adapts

## Success Criteria

### Must Pass (Critical)
✓ All toolbar tests pass in both modes  
✓ Text is readable in portrait when screen is rotated  
✓ All modal views fit properly in both modes  
✓ Toggle functionality works correctly  
✓ No off-screen content in any view  
✓ Content area calculations correct in both modes  
✓ No regressions in slideshow functionality  

### Should Pass (Important)
✓ Logging is concise and informative  
✓ No PIL spam in logs  
✓ Smooth transitions between modes  
✓ Proper popup sizing in both orientations  
✓ All previous fixes still working  

### Nice to Have (Optional)
✓ Fast mode switching (no lag)  
✓ Smooth animations  
✓ Visual polish  

## Reporting Issues

If any test fails, please report:

1. **Which test failed:** (e.g., "Galerie View Tests - Open Galerie (9:16)")
2. **Expected behavior:** (e.g., "Grid should have 4 columns")
3. **Actual behavior:** (e.g., "Grid has 8 columns, images cut off")
4. **Mode:** (16:9 or 9:16)
5. **Steps to reproduce:**
   - List exact steps that cause the issue
6. **Screenshots:** (if possible, especially for layout issues)
7. **Logs:** (relevant console output or log file excerpts)

## Quick Test Summary

For a quick smoke test, verify these core behaviors:

**16:9 Mode:**
1. Toolbar at bottom (horizontal) ✓
2. Galerie opens with 8 columns ✓
3. Toggle closes same panel ✓

**9:16 Mode:**
1. Toolbar on right (vertical) ✓
2. Text readable when screen rotated ✓
3. Galerie opens with 4 columns ✓
4. Toggle closes same panel ✓

**Both Modes:**
1. Content fills available space ✓
2. No off-screen elements ✓
3. Smooth transitions ✓
4. All popups fit properly ✓
