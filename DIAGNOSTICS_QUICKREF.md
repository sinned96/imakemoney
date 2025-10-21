# Touch Diagnostics Quick Reference

## 🚀 Quick Start

```bash
# Enable basic diagnostics
DIAG_TOUCH_TRACE=1 PORTRAIT_PIPELINE=matrix python3 main.py

# With visual markers
DIAG_TOUCH_TRACE=1 DIAG_TOUCH_TRACE_OVERLAY=1 PORTRAIT_PIPELINE=matrix python3 main.py
```

## 📊 What You'll See

### Touch Events
```
[diag] touch down win=(850,640) accepted_by=TextInput#username path=[...]
[diag] focus TextInput#username=True cursor=(0, 0)
[diag] touch up win=(850,640) accepted_by=TextInput#username path=[...]
```

### Z-Order (on startup)
```
[diag] Z-order summary (bottom to top):
[diag]   [0] PortraitContainer(1920x1080@0,0)
[diag]   [1] LoginScreen(480x560@720,260)
```

## 🎯 Common Use Cases

### Debug "Ghost" Touch Areas
**Problem**: Clicks don't work where you expect

**Solution**:
1. Enable diagnostics: `DIAG_TOUCH_TRACE=1`
2. Click the problematic area
3. Check the log: `accepted_by=` shows which widget handled it
4. Check the path: see if an overlay intercepted the touch

### Verify Focus Works
**Problem**: Login fields don't focus when clicked

**Solution**:
1. Enable diagnostics: `DIAG_TOUCH_TRACE=1`
2. Click username field
3. Look for: `[diag] focus TextInput#username=True`
4. If missing, the field isn't receiving the touch

### Visualize Coordinate Mapping
**Problem**: Touch coordinates seem wrong after rotation

**Solution**:
1. Enable overlay: `DIAG_TOUCH_TRACE=1 DIAG_TOUCH_TRACE_OVERLAY=1`
2. Click around the screen
3. Red dots show where touches land in transformed space
4. Dots should align with visible UI elements

### Identify Overlay Widgets
**Problem**: Something invisible is blocking touches

**Solution**:
1. Enable diagnostics: `DIAG_TOUCH_TRACE=1`
2. Check z-order summary at startup
3. Look for full-screen widgets (1920x1080@0,0)
4. Check if they appear in the dispatch path

## ⚙️ Environment Flags

| Flag | Values | Use When |
|------|--------|----------|
| `DIAG_TOUCH_TRACE` | `1` or `0` | Always needed for any diagnostics |
| `DIAG_TOUCH_TRACE_OVERLAY` | `1` or `0` | Want visual markers |
| `DIAG_TOUCH_TRACE_LEVEL` | `info` or `debug` | Need more details |

## 📖 Reading the Logs

### Path Format
```
path=[Widget1(c=T,r=T), Widget2(c=T,r=F), Widget3(c=T,r=T)]
```
- `c=T`: Widget's collide_point() returned True (touch is inside)
- `c=F`: Touch is outside widget bounds
- `r=T`: Widget's touch handler returned True (accepted event)
- `r=F`: Widget passed event to children

### Accepted By
```
accepted_by=TextInput#username
```
- Shows widget class and ID
- This is the widget that handled the touch
- If `None`, no widget accepted it

## 🔍 Troubleshooting

**No logs appear?**
- Check `DIAG_TOUCH_TRACE=1` is set
- Verify `PORTRAIT_PIPELINE=matrix` 
- Look in `projekt.log` file

**Visual markers don't show?**
- Need both `DIAG_TOUCH_TRACE=1` and `DIAG_TOUCH_TRACE_OVERLAY=1`
- Check that touches are being processed (check logs)

**Too many logs?**
- Move events are already throttled (every 5th)
- Focus on down/up events for debugging

## 📚 Full Documentation

- **DIAGNOSTICS_README.md**: Complete feature documentation
- **IMPLEMENTATION_SUMMARY.md**: Technical implementation details
- **test_diag_touch.py**: Comprehensive test scenarios

## 💡 Pro Tips

1. **Start Simple**: Use just `DIAG_TOUCH_TRACE=1` first
2. **Add Overlay**: If coordinates look wrong, enable overlay to visualize
3. **Check Z-Order**: First thing to check if touches don't work at all
4. **Focus Logs**: Great for debugging text input issues
5. **Disable in Prod**: Zero overhead, but disable for cleaner logs

## Example Debugging Session

```bash
# 1. Enable diagnostics
export DIAG_TOUCH_TRACE=1
export PORTRAIT_PIPELINE=matrix
python3 main.py

# 2. Click problem area, check log:
# [diag] touch down win=(500,600) accepted_by=Overlay#transparent

# 3. Identified: Overlay is intercepting touches!
# 4. Check z-order to confirm:
# [diag] Z-order summary (bottom to top):
# [diag]   [1] LoginScreen(480x560@720,260)  
# [diag]   [2] Overlay#transparent(1920x1080@0,0)  <-- This is on top!

# 5. Fix: Remove or reorder the overlay widget
```

---

Need help? Check the full documentation in DIAGNOSTICS_README.md
