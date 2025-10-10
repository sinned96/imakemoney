# Testing Instructions: Slideshow/Orientation Hotfix

## Quick Start

### Fetch and Checkout the PR

```bash
# Fetch the PR branch
git fetch origin pull/NUMBER/head:pr-followup

# Or directly checkout the branch
git fetch origin copilot/fix-slideshow-orientation-bugs
git checkout copilot/fix-slideshow-orientation-bugs
```

Replace `NUMBER` with the actual PR number when it's created.

### Run Automated Tests

```bash
python3 test_image_loading.py
```

Expected output: ✅ ALL TESTS PASSED (5/5)

## Manual Testing Scenarios

### Scenario 1: Portrait Image Display ✅ HIGH PRIORITY

**Objective**: Verify 9:16 portrait images are no longer white/invisible

**Steps**:
1. Start the app
2. Login
3. Click "Format" button in toolbar
4. Select "Vertikal (9:16)"
5. Add or select a portrait (9:16) image
6. **Expected**: Image displays correctly (not white frame)
7. **Check logs** for: `Loading image: path=..., exists=True, aspect_mode=9:16`

**Success Criteria**:
- Portrait image visible
- No white frames
- Logs show successful texture load

---

### Scenario 2: Mixed Format Slideshow ✅ HIGH PRIORITY

**Objective**: Verify both 16:9 and 9:16 images cycle correctly together

**Steps**:
1. Have both landscape (16:9) and portrait (9:16) images in slideshow
2. Select "Alle Bilder" mode
3. Switch format to "Horizontal (16:9)"
4. **Expected**: Only 16:9 images show
5. Switch format to "Vertikal (9:16)"
6. **Expected**: Only 9:16 images show
7. Let slideshow cycle through images
8. **Expected**: All images in selected format display correctly

**Success Criteria**:
- Images filtered by aspect ratio
- All images display (no white frames)
- Smooth transitions between images

---

### Scenario 3: Format Switching ✅ HIGH PRIORITY

**Objective**: Verify toolbar remains visible and clickable after format switch

**Steps**:
1. Start in "Horizontal (16:9)" mode
2. Click "Format" button
3. Select "Vertikal (9:16)"
4. **Expected**: 
   - Entire UI rotates 90° CW
   - Toolbar at bottom, horizontal text
   - Toolbar buttons clickable
5. Switch back to "Horizontal (16:9)"
6. **Expected**: UI rotates back, toolbar still visible

**Success Criteria**:
- Toolbar always visible
- Toolbar always at bottom
- All buttons clickable
- Content area correct size

---

### Scenario 4: Lightbox in Both Modes

**Objective**: Verify lightbox displays images correctly in both orientations

**Steps**:
1. In "Horizontal (16:9)" mode:
   - Click "Galerie" button
   - Click an image
   - **Expected**: Lightbox shows image, not rotated
2. Switch to "Vertikal (9:16)" mode:
   - Click "Galerie" button
   - Click an image
   - **Expected**: Lightbox shows image, rotated correctly

**Success Criteria**:
- Images visible in lightbox (not white)
- Correct rotation in each mode
- Close button works

---

### Scenario 5: Aspect Ratio Persistence

**Objective**: Verify last selected aspect ratio is restored on restart

**Steps**:
1. Select "Vertikal (9:16)" format
2. Wait 2 seconds (for save)
3. Exit app completely
4. Restart app
5. **Expected**: App starts in "Vertikal (9:16)" mode
6. Check `image_meta.json`: should contain `"aspect_ratio": "9:16"`

**Success Criteria**:
- Aspect ratio persists across restarts
- UI in correct mode on startup

---

### Scenario 6: Log Inspection

**Objective**: Verify logging is clean and informative

**Steps**:
1. Clear or archive old `projekt.log`
2. Start app and perform scenarios 1-3
3. Check `projekt.log`

**Look for**:
```
✅ Loading image: path=/path/to/image.png, exists=True, aspect_mode=9:16
✅ Image loaded via CoreImage: texture_size=(1080, 1920), widget_size=(720, 1220)
✅ Applying layout for aspect ratio: 9:16, window size: 720x1280
```

**Should NOT see**:
```
❌ "cover mode: ..." (removed)
❌ PIL.PngImagePlugin debug spam (suppressed)
❌ White images/texture errors
```

**Success Criteria**:
- Clean, informative logs
- No spam
- Image loading logs present

---

## Expected Behavior Summary

| Scenario | Before Fix | After Fix |
|----------|-----------|-----------|
| 9:16 image in slideshow | White frame | Image visible ✅ |
| Mixed 16:9 + 9:16 | Only 16:9 shows | Filtered by format ✅ |
| Format switch | Toolbar disappears | Toolbar stays visible ✅ |
| Lightbox 9:16 | White image | Image visible + rotated ✅ |
| Restart app | Random format | Last selected format ✅ |
| Logs | Spam + errors | Clean + informative ✅ |

## Troubleshooting

### Images Still White

**Check**:
1. Log shows: `exists=False` → File path incorrect
2. Log shows: `CoreImage failed` → Image format corrupted
3. No texture_size in logs → Loading failed completely

**Fix**: Check image file permissions and format

### Toolbar Disappears

**Check**:
1. Toolbar has `pos_hint = {"bottom": 1}`
2. No overlays covering toolbar
3. `_bring_toolbar_to_front()` called after layout

### Wrong Aspect on Startup

**Check**:
1. `image_meta.json` exists and has correct `"aspect_ratio"`
2. No errors in startup logs
3. OrientationProvider initialized correctly

## Performance Notes

- **CoreImage with nocache**: Fresh load every time, prevents stale textures
- **Schedule on next frame**: Avoids race conditions, smooth transitions
- **Clear state first**: Ensures clean slate for each image

## Success Indicators

✅ All automated tests pass
✅ Portrait images always visible
✅ Mixed formats cycle correctly
✅ Toolbar always visible and clickable
✅ Lightbox shows images in both modes
✅ Aspect ratio persists across restarts
✅ Logs clean and informative

## Questions?

See **HOTFIX_FOLLOWUP_SUMMARY.md** for detailed technical explanation.

## Branch Info

- **Branch**: `copilot/fix-slideshow-orientation-bugs`
- **Base**: `main` (after PR #60)
- **Commits**: 4 (including initial plan)
- **Files changed**: 3 (main.py, test_image_loading.py, docs)

## Checklist for User

Before merging:
- [ ] Run automated tests: `python3 test_image_loading.py`
- [ ] Test Scenario 1: Portrait images visible
- [ ] Test Scenario 2: Mixed formats work
- [ ] Test Scenario 3: Toolbar after format switch
- [ ] Test Scenario 4: Lightbox in both modes
- [ ] Test Scenario 5: Aspect persistence
- [ ] Test Scenario 6: Check logs
- [ ] Verify on actual hardware (if different from dev environment)
