# Visual Guide: Portrait UI Fixes

## Before vs After

### 🖼️ Aufnahme Panel Behavior

#### BEFORE (Broken)
```
┌────────────────────────────────┐
│                                │
│  ┌──────────┐                  │
│  │ Aufnahme │ ← Left-docked    │
│  │  Panel   │   overlay        │
│  │ (visible)│                  │
│  │          │                  │
│  └──────────┘                  │
│        ↓                       │
│  Invisible clickable area      │
│  in center (legacy behavior)   │
│                                │
└────────────────────────────────┘
Issue: Two overlapping implementations
```

#### AFTER (Fixed) ✅
```
┌────────────────────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ ← Semi-transparent
│ ░░┌──────────────────┐░░░░░░░ │   background (0.7 alpha)
│ ░░│                  │░░░░░░░ │
│ ░░│  Aufnahme Panel  │░░░░░░░ │ ← Centered modal
│ ░░│   (0.62w×0.86h)  │░░░░░░░ │   AnchorLayout
│ ░░│                  │░░░░░░░ │
│ ░░│     [Close]      │░░░░░░░ │
│ ░░└──────────────────┘░░░░░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
└────────────────────────────────┘
```

---

### 📱 Toolbar Layout Changes

#### 16:9 Mode (Landscape) - UNCHANGED
```
┌──────────────────────────────────┐
│                                  │
│         Content Area             │
│      (full width, reduced        │
│       height for toolbar)        │
│                                  │
├──────────────────────────────────┤
│ [Zeiten][Aufnahme][Format]...    │ ← Horizontal toolbar
└──────────────────────────────────┘   at bottom (60dp height)
```

#### 9:16 Mode (Portrait) - NEW VERTICAL TOOLBAR ✅
```
┌────────────────────────┬─────┐
│                        │  Z  │ ← Vertical toolbar
│                        │  e  │   on right side
│      Content Area      │  i  │   (108dp wide)
│   (reduced width for   │  t  │
│    toolbar, x=0)       │  e  │   Labels rotated
│                        │  n  │   -90° (270°)
│                        │     │
│                        │  A  │
│                        │  u  │
│                        │  f  │
│                        │  n  │
│                        │  .  │
│                        │     │
│                        │  F  │
│                        │  .  │
└────────────────────────┴─────┘
```

---

### 🎯 Panel Management Flow

#### BEFORE (Multiple panels could be open)
```
User clicks: Aufnahme → Opens
User clicks: Gallery  → Opens (now 2 panels!)
User clicks: Format   → Opens (now 3 panels!!)
                         ↑ confusing, z-order issues
```

#### AFTER (Single-open rule) ✅
```
User clicks: Aufnahme → Opens Aufnahme
                        (tracks: _open_panel = ("aufnahme", instance))

User clicks: Gallery  → Closes Aufnahme
                        Opens Gallery
                        (tracks: _open_panel = ("gallery", instance))

User clicks: Gallery  → Toggles closed
                        (same ID → close)
                        
User clicks: ESC      → Closes current panel
```

---

### 🔄 Aspect Ratio Switch Behavior

#### BEFORE
```
16:9 Mode → Open Aufnahme → Switch to 9:16
                              ↓
                        Aufnahme still open
                        Layout breaks
                        Toolbar misaligned
```

#### AFTER ✅
```
16:9 Mode → Open Aufnahme → Switch to 9:16
                              ↓
                        Auto-close Aufnahme
                        Rebuild toolbar (vertical)
                        Clean layout
```

---

## Key Technical Changes

### 1. AufnahmePopup Architecture
```python
# BEFORE
class AufnahmePopup(RotatedModalView):
    def __init__(...):
        super().__init__(**kwargs)
        self.size = (600, 500)  # Fixed size
        self.add_widget(self.panel)
        # No centering, no cleanup

# AFTER ✅
class AufnahmePopup(RotatedModalView):
    def __init__(...):
        self._cleanup_legacy_sheets()  # Remove old overlays
        
        kw_copy.setdefault('size_hint', (1, 1))  # Full screen
        super().__init__(**kw_copy)
        
        # Portrait sizing
        if aspect == "9:16":
            panel_w = max(int(content_w * 0.62), dp(320))
            panel_h = max(int(content_h * 0.86), dp(260))
        
        # Centered with AnchorLayout
        anchor = AnchorLayout(size_hint=(1, 1), 
                             anchor_x='center', 
                             anchor_y='center')
        anchor.add_widget(self.panel)
        self.add_widget(anchor)
        
        # ESC key
        Window.bind(on_key_down=self._on_key_down)
```

### 2. Toolbar Creation Logic
```python
# BEFORE (Always horizontal at bottom)
def _create_toolbar(self, vertical=False):
    bar = CustomAppBar(title="...", vertical=False)  # Always False!
    bar.pos_hint = {"bottom": 1}  # Always bottom
    return bar

# AFTER ✅ (Conditional based on aspect ratio)
def _create_toolbar(self, vertical=False):
    bar = CustomAppBar(title="...", vertical=vertical)  # Uses param
    
    if vertical:
        bar.pos_hint = {"right": 1, "top": 1}  # Right side
        bar.width = dp(108)  # Fixed width
    else:
        bar.pos_hint = {"bottom": 1}  # Bottom
    
    return bar
```

### 3. Content Area Calculation
```python
# BEFORE (Always subtract bottom toolbar)
def _resize_image(self, img_widget):
    content_h = self.height - toolbar_height
    content_y = toolbar_height
    img_widget.size = (self.width, content_h)
    img_widget.pos = (0, content_y)

# AFTER ✅ (Conditional based on orientation)
def _resize_image(self, img_widget):
    if self.aspect_ratio == "9:16":
        # Vertical toolbar on right
        toolbar_width = self.toolbar.width or dp(108)
        content_w = self.width - toolbar_width
        content_x = 0
    else:
        # Horizontal toolbar at bottom
        toolbar_height = self.toolbar.height or dp(60)
        content_h = self.height - toolbar_height
        content_y = toolbar_height
    
    img_widget.size = (content_w, content_h)
    img_widget.pos = (content_x, content_y)
```

---

## Testing Results

### Automated Tests ✅
```bash
$ python3 verify_portrait_fixes.py

✅ PASS: AufnahmePopup Modal Setup (7/7)
✅ PASS: Panel Tracking (7/7)
✅ PASS: Vertical Toolbar for 9:16 (7/7)
✅ PASS: Logging (5/5)
✅ PASS: ESC/Back Key Handling (5/5)

Results: 5/5 tests passed
```

### Expected Behavior
1. ✅ Aufnahme appears centered, not as left sheet
2. ✅ Only one panel open at a time
3. ✅ Clicking same toolbar button toggles panel
4. ✅ Format panel always visible (not hidden behind others)
5. ✅ 9:16 mode uses vertical toolbar on right
6. ✅ ESC key dismisses Aufnahme modal
7. ✅ Aspect ratio switch closes all panels

---

## Files Changed

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `main.py` | ~250 | Core implementation |
| `verify_portrait_fixes.py` | +251 (new) | Automated tests |
| `PORTRAIT_UI_FIXES.md` | +389 (new) | Documentation |
| `CHANGES_VISUAL_GUIDE.md` | +240 (new) | This visual guide |

---

## Summary

**Problem:** Overlapping UI, panels not closing, toolbar always horizontal

**Solution:** 
- Full-screen centered modals with AnchorLayout
- Single-open panel tracking with toggle behavior
- Vertical toolbar for portrait mode (9:16)
- ESC key support and comprehensive logging

**Result:** Clean, predictable UI behavior in both landscape and portrait modes ✅
