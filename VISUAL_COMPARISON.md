# Visual Comparison: Before vs After

## Toolbar Layout Changes

### Before (PR #60 - Hotfix)
Both 16:9 and 9:16 had horizontal toolbar at bottom:

```
16:9 Mode (Landscape):              9:16 Mode (Portrait):
┌─────────────────────────┐         ┌──────────────────┐
│                         │         │                  │
│    Content Area         │         │  Content Area    │
│    (Full Width)         │         │  (Full Width)    │
│                         │         │                  │
│                         │         │                  │
├─────────────────────────┤         ├──────────────────┤
│ [Zeit] [Aufn] [Form]... │         │ [Zeit] [Auf]...  │
└─────────────────────────┘         └──────────────────┘
     Horizontal toolbar               Horizontal toolbar
     ✓ Text readable                  ✗ Text horizontal
                                        (awkward when
                                         screen rotated)
```

**Problem:** In 9:16 mode, when user physically rotates the screen to portrait orientation, the horizontal toolbar text becomes sideways and hard to read.

### After (This PR)
Adaptive toolbar placement based on aspect ratio:

```
16:9 Mode (Landscape):              9:16 Mode (Portrait):
┌─────────────────────────┐         ┌──────────────────┬───┐
│                         │         │                  │ Z │
│    Content Area         │         │                  │ e │
│    (Full Width)         │         │                  │ i │
│                         │         │  Content Area    │ t │
│                         │         │  (Width - 110dp) │ e │
├─────────────────────────┤         │                  │ n │
│ [Zeit] [Aufn] [Form]... │         │                  ├───┤
└─────────────────────────┘         │                  │ A │
     Horizontal toolbar             │                  │ u │
     ✓ Text horizontal              │                  │ f │
     ✓ Easy to read                 └──────────────────┴───┘
                                         Vertical toolbar
                                         ✓ Text vertical
                                         ✓ Readable when
                                           screen rotated
```

## Text Orientation Detail

### Text Transformation (VerticalButton)

**Step-by-step transformation:**

```
1. Original text: "Zeiten"
   ┌─────────┐
   │ Zeiten  │
   └─────────┘

2. Rotate 90° clockwise:
   ┌───┐
   │ n │
   │ e │
   │ t │
   │ i │
   │ e │
   │ Z │
   └───┘
   (Reads bottom-to-top)

3. Apply vertical mirror (Scale 1,-1):
   ┌───┐
   │ Z │  ← Top
   │ e │
   │ i │
   │ t │
   │ e │
   │ n │  ← Bottom
   └───┘
   (Reads top-to-bottom - CORRECT!)
```

**Why this works:**
When the physical screen is rotated 90° clockwise (landscape → portrait), the already-rotated text appears upright and readable from top to bottom.

**Configuration:**
```python
PORTRAIT_LABEL_ANGLE = 90      # Rotation angle
use_mirror = True              # Apply vertical flip
```

**Alternative approaches tested:**
- 270° rotation alone: Text reads top-to-bottom but from wrong edge
- 90° rotation alone: Text reads bottom-to-top (incorrect)
- 90° + mirror: Text reads top-to-bottom (CORRECT) ✓

## Galerie View Adaptation

### Before (Fixed width for both modes)

```
16:9 Landscape:                     9:16 Portrait:
┌─────────────────────────────┐     ┌──────────────┬───┐
│ Modi │ [Grid: 8 columns]    │     │ Modi │ [Grid │ T │
│ ───  │  ┌──┬──┬──┬──┬──┬──┐ │     │ ───  │  ┌──┬ │ o │
│ [x]  │  │  │  │  │  │  │  │ │     │ [x]  │  │  │ │ o │
│ [x]  │  ├──┼──┼──┼──┼──┼──┤ │     │ [x]  │  ├──┼ │ l │
│ [x]  │  │  │  │  │  │  │  │ │     │ [x]  │  │  │ │ b │
└─────────────────────────────┘     └──────────────┴───┘
     95% width, 8 columns               95% width, 8 cols
     ✓ Fits well                         ✗ Too wide!
                                         Grid cut off →
```

### After (Adaptive width and columns)

```
16:9 Landscape:                     9:16 Portrait:
┌─────────────────────────────┐     ┌────────────┬───┐
│ Modi │ [Grid: 8 columns]    │     │ Modi │Grid │ T │
│ ───  │  ┌──┬──┬──┬──┬──┬──┐ │     │ ───  │┌──┬─┤ o │
│ [x]  │  │  │  │  │  │  │  │ │     │ [x]  ││  │ │ o │
│ [x]  │  ├──┼──┼──┼──┼──┼──┤ │     │ [x]  │├──┼─┤ l │
│ [x]  │  │  │  │  │  │  │  │ │     │ [x]  ││  │ │ b │
└─────────────────────────────┘     └────────────┴───┘
     95% width, 8 columns           85% width, 4 cols
     ✓ Fits well                    ✓ Fits well
                                    ✓ All visible
```

**Key changes:**
- Panel width: 95% → 85% (leaves room for toolbar)
- Grid columns: 8 → 4 (fits narrower width)
- Spacing: 18dp → 12dp (tighter for portrait)

## Toggle Functionality

### Before (No toggle)
```
Action:                Result:
Click "Galerie"   →   Opens gallery
Click "Galerie"   →   Opens gallery (again, duplicate)
Click "Zeiten"    →   Opens schedule (gallery still open)
```

### After (With toggle)
```
Action:                Result:
Click "Galerie"   →   Opens gallery
Click "Galerie"   →   Closes gallery (toggle off)
Click "Galerie"   →   Opens gallery again

Click "Galerie"   →   Opens gallery
Click "Zeiten"    →   Closes gallery, opens schedule (switch)
Click "Zeiten"    →   Closes schedule (toggle off)
```

**Implementation:**
```python
# Track state
self.current_popup = popup_instance
self.current_popup_name = "Galerie"  # or "Zeiten", etc.

# Toggle logic
if current_popup_name == clicked_name:
    close_popup()  # Same button - toggle off
else:
    close_current()  # Different button - switch
    open_new()
```

## Content Area Calculation

### Image Resize Logic

**Before:**
```python
# Always subtract toolbar from bottom
content_h = self.height - toolbar_height
content_y = toolbar_height
```

**After:**
```python
if aspect_ratio == "9:16":
    # Portrait: subtract toolbar from right
    content_w = self.width - toolbar_width
    content_x = 0
else:
    # Landscape: subtract toolbar from bottom
    content_h = self.height - toolbar_height
    content_y = toolbar_height
```

**Visual result:**

```
16:9 Mode:                          9:16 Mode:
┌─────────────────────────┐         ┌──────────────────┬───┐
│                         │         │                  │   │
│  Image fills this       │         │  Image fills     │ T │
│  content area           │         │  this content    │ o │
│  (width × height-60dp)  │         │  area            │ o │
│                         │         │  (width-110dp    │ l │
├─────────────────────────┤         │   × height)      │ b │
│    [Toolbar]            │         │                  │ a │
└─────────────────────────┘         └──────────────────┴───┘
```

## Modal View Sizing

### Popup Adaptation Examples

**GeneralSettingsPopup:**
```
Landscape (16:9):               Portrait (9:16):
┌────────────────┐              ┌──────────────┐
│  Einstellungen │              │ Einstellung  │
│                │              │              │
│  [Slider...]   │              │ [Slider...]  │
│  [Slider...]   │              │ [Slider...]  │
│                │              │              │
│  [Speichern]   │              │ [Speichern]  │
└────────────────┘              └──────────────┘
   520dp × 420dp                  460dp × 450dp
   (Wider, shorter)               (Narrower, taller)
```

**All adapted popups:**
- GeneralSettingsPopup: 520×420 → 460×450
- GlobalDurationPopup: 520×380 → 460×400
- FormatSelectionPopup: 400×300 → 360×320
- AufnahmePopup: 600×500 → 500×600
- SettingsRootPopup: 500×480 → 450×520

## User Experience Flow

### Typical Usage Scenario

**16:9 Landscape Mode:**
1. User sees slideshow with horizontal toolbar at bottom
2. Clicks "Galerie" → Panel opens (95% width, 8 columns)
3. Clicks "Galerie" again → Panel closes (toggle)
4. Switches format to "9:16" → Screen rotates

**9:16 Portrait Mode:**
1. User rotates device 90° clockwise (landscape → portrait)
2. Vertical toolbar now appears on right with readable text
3. Clicks "Galerie" → Panel opens (85% width, 4 columns)
4. Modi list fully visible, grid fits width perfectly
5. Clicks "Zeiten" → Switches to schedule editor
6. Clicks "Zeiten" again → Closes (toggle off)

## Browser/Testing View

Since the app runs on a Raspberry Pi with physical screen rotation, the behavior is:

**In landscape orientation (16:9):**
- Horizontal toolbar at bottom
- Text horizontal

**After changing to 9:16 and physically rotating screen:**
- User rotates screen 90° CW
- Vertical toolbar on right (user's perspective: bottom-right edge)
- Text appears upright and readable
- All buttons aligned and clickable

## Summary of Benefits

### 1. Better UX in Portrait Mode
- ✓ Text readable without tilting head
- ✓ Natural toolbar placement (side, not bottom)
- ✓ More vertical space for content

### 2. Proper Layout Adaptation
- ✓ All views fit their aspect ratio
- ✓ No off-screen content
- ✓ Optimal column counts for width

### 3. Improved Interaction
- ✓ Toggle closes same panel
- ✓ Switch closes current, opens new
- ✓ No duplicate panels

### 4. Maintainable Configuration
- ✓ PORTRAIT_LABEL_ANGLE constant
- ✓ Clear aspect ratio checks
- ✓ Consistent pattern across views

### 5. Backward Compatible
- ✓ No breaking changes
- ✓ Works with both Kivy 2.3+ and older versions
- ✓ Previous fixes maintained
