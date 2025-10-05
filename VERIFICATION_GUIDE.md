# Verification Guide for 9:16 Fixes

## Quick Reference for Testing the Fixes

### Prerequisites
1. Set aspect ratio in `image_meta.json`:
   ```json
   {
     "aspect_ratio": "9:16"
   }
   ```

2. Ensure Vertex AI workflow is configured and working

---

## Test 1: Image Scaling (9:16 → No Forced Scaling)

### Steps
1. Trigger image generation workflow with 9:16 aspect ratio set
2. Check `projekt.log` for scaling information

### Expected Results

#### For 9:16 Images (e.g., 768x1408 from Vertex AI)
```log
Image analysis: aspect_ratio_request=9:16, raw_output_size=(768, 1408), 
                current_ratio=0.545, target_ratio=0.562, ratio_diff=3.0%
Aspect ratio already correct (3.0% difference), 
                final_saved_size=(768, 1408), scaling_applied=False
```

**Key Points**:
- ✅ `ratio_diff` should be < 5%
- ✅ `scaling_applied=False` means original size preserved
- ✅ `raw_output_size` == `final_saved_size`

#### For 16:9 Images
```log
Image analysis: aspect_ratio_request=16:9, raw_output_size=(1920, 1080), 
                current_ratio=1.778, target_ratio=1.778, ratio_diff=0.0%
Aspect ratio already correct (0.0% difference), 
                final_saved_size=(1920, 1080), scaling_applied=False
```

#### For Wrong Aspect Ratio (e.g., 16:9 image when 9:16 requested)
```log
Image analysis: aspect_ratio_request=9:16, raw_output_size=(1920, 1080), 
                current_ratio=1.778, target_ratio=0.562, ratio_diff=216.0%
Aspect ratio mismatch (216.0% difference), scaling to (1080, 1920)
Image scaled: aspect_ratio_request=9:16, 
              raw_output_size=(1920, 1080), final_saved_size=(1080, 1920), 
              scaling_applied=True
```

**Key Points**:
- ✅ `ratio_diff` should be > 5%
- ✅ `scaling_applied=True` means image was scaled
- ✅ `raw_output_size` != `final_saved_size`

---

## Test 2: Menu Rotation (270° for Natural Reading)

### Steps
1. Switch application to 9:16 mode
2. Observe the menu on the right side
3. Read the button text

### Expected Results

#### Visual Check
```
Menu Position: Right side ✅
Text Direction: Top to bottom ✅
Reading Flow: Natural (downward) ✅
Clipping: None (padding prevents) ✅
```

#### Code Verification
In `main.py`, look for:
```python
class VerticalButton(Button):
    def __init__(self, rotation_angle=270, **kwargs):  # ✅ Should be 270
```

And in `CustomAppBar.set_right_actions()`:
```python
btn=VerticalButton(text=text, ...,
                   rotation_angle=270,  # ✅ Should be 270 (not 90)
```

### Reading Direction Visual
```
┌─────┐
│  Z  │  ← Top (start reading here)
│  e  │
│  i  │
│  t  │
│  e  │
│  n  │  ← Bottom (end reading here)
└─────┘

Direction: ↓ Downward (natural)
```

---

## Test 3: Double-Click in Gallery (No Freeze)

### Steps
1. Open application
2. Navigate to gallery view
3. Find any image thumbnail
4. Double-click (or double-tap) the thumbnail rapidly
5. Try triple-clicking or multiple rapid clicks

### Expected Results

#### First Double-Click
```
✅ Lightbox opens once
✅ No duplicate lightboxes
✅ Application remains responsive
```

#### Subsequent Clicks While Lightbox Open
```
✅ Additional clicks are ignored
✅ No freeze
✅ Lightbox remains stable
```

#### After Closing Lightbox
```
✅ Can open lightbox again with double-click
✅ is_lightbox_open flag resets properly
```

#### Log Messages (in debug mode)
```log
Scheduled lightbox open for: /path/to/image.png
Lightbox opened for: /path/to/image.png
Lightbox already open, ignoring double-click for: /path/to/image.png  ← Subsequent clicks
Lightbox closed, flag reset for: /path/to/image.png  ← After closing
```

---

## Common Issues and Solutions

### Issue: Images still being scaled to 1920x1080

**Possible Causes**:
1. `image_meta.json` not in correct location (should be in app directory)
2. Aspect ratio not set to "9:16" in `image_meta.json`
3. Old Python processes still running (need restart)

**Solutions**:
```bash
# Check image_meta.json location
ls -la /path/to/app/image_meta.json

# Verify content
cat /path/to/app/image_meta.json | grep aspect_ratio

# Restart workflow service
pkill -f "python.*workflow"
python3 start_workflow_service.py
```

### Issue: Menu text not reading correctly

**Possible Causes**:
1. Old code still cached (Python bytecode)
2. Application not restarted after code update

**Solutions**:
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Restart application
pkill -f "python.*main.py"
python3 main.py
```

### Issue: Double-click still causes freeze

**Check These**:
1. Verify `is_lightbox_open` flag is being set/reset
2. Check for exceptions in logs
3. Verify `Clock.schedule_once` is working

**Debug Logging**:
```python
# Add to _open_lightbox_debounced() method
debug_logger.debug(f"Lightbox open flag: {self.is_lightbox_open}")
debug_logger.debug(f"Scheduled: {self._scheduled_lightbox}")
```

---

## Performance Verification

### Aspect Ratio Check Performance
```python
# This is very fast - just one division and comparison
current_ratio = width / height  # ~1 CPU cycle
ratio_diff = abs(current_ratio - target_ratio) / target_ratio  # ~3 CPU cycles
if ratio_diff < 0.05:  # ~1 CPU cycle
    return True  # Total: ~5 CPU cycles
```

**Expected**: < 1 microsecond per image

### Rotation Performance
```python
# Canvas rotation is GPU-accelerated in Kivy
Rotate(angle=270, origin=self.center)  # Handled by GPU
```

**Expected**: No measurable performance impact

---

## Success Criteria Checklist

### 9:16 Workflow
- [ ] image_meta.json has "aspect_ratio": "9:16"
- [ ] Generated image keeps original size if ratio correct
- [ ] Log shows `scaling_applied=False` for correct ratio
- [ ] Log shows `scaling_applied=True` only for wrong ratio
- [ ] Image displays correctly in 9:16 UI mode

### Menu Rotation
- [ ] Menu is on right side in 9:16 mode
- [ ] Text reads naturally top-to-bottom
- [ ] No text clipping visible
- [ ] Text is parallel to screen edge

### Gallery Double-Click
- [ ] Single lightbox opens on double-click
- [ ] No freeze on rapid clicks
- [ ] Additional clicks ignored when lightbox open
- [ ] Can open lightbox again after closing

### Code Quality
- [ ] No Python syntax errors (`python3 -m py_compile`)
- [ ] No breaking changes to existing functionality
- [ ] Backwards compatible (16:9 still works)
- [ ] Enhanced logging provides useful debug info

---

## Rollback Instructions

If issues occur, revert changes:

```bash
# View recent commits
git log --oneline -5

# Revert to previous commit
git revert HEAD

# Or reset to specific commit
git reset --hard <commit-hash>

# Force push (if needed)
git push --force origin <branch-name>
```

---

## Contact for Issues

If verification fails or unexpected behavior occurs:
1. Check `projekt.log` for detailed error messages
2. Verify all changes were applied correctly
3. Ensure no conflicting changes from other sources
4. Review FIX_IMPLEMENTATION_SUMMARY.md for detailed technical info
