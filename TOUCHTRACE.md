# TouchTrace Diagnostics

This document describes the TouchTrace diagnostics system for identifying which widgets consume touch events in portrait mode.

## Overview

After PR #99, coordinate remapping is correct - logs show window→portrait values within [0..1080]x[0..1920] in both mapping modes. However, clicks on visible Login fields still don't focus, indicating a "ghost" hit area that consumes touches.

The TouchTrace diagnostics help identify which widget(s) are accepting touches without changing any layout or rendering behavior.

## Features

### 1. Touch Candidate Logging

When a touch event occurs on `PortraitContainer`, the system logs all direct children and whether they collide with the touch position.

**Example log output:**
```
[TouchTrace] phase=down at=(540.0,960.0)->(540.0,960.0) candidates=[{'cls':'LoginScreen','pos':(0.0,0.0),'size':(1080.0,1920.0),'collide':True,'opacity':1.0,'disabled':False}, {'cls':'Label','pos':(340.0,1060.0),'size':(400.0,100.0),'collide':False,'opacity':1.0}]
```

**Logged information for each candidate:**
- `cls`: Widget class name (e.g., 'LoginScreen', 'TextInput', 'Button')
- `id`: Widget ID or name if available
- `pos`: Widget position as (x, y) in portrait coordinates
- `size`: Widget size as (width, height)
- `collide`: Boolean indicating if the widget collides with the touch
- `opacity`: Widget opacity (0.0 to 1.0) if available
- `disabled`: Boolean indicating if the widget is disabled (if attribute exists)

### 2. Accepted-by Logging

After touch events are dispatched, the system logs which widget accepted/handled the touch.

**Example log output (with marker):**
```
[TouchTrace] phase=down accepted_by=LoginScreen path=RotatingRoot/PortraitContainer/LoginScreen
```

**Example log output (best-effort guess):**
```
[TouchTrace] phase=down accepted_by_guess=TextInput path=RotatingRoot/PortraitContainer/LoginScreen/BoxLayout/TextInput
```

**Example log output (not accepted):**
```
[TouchTrace] phase=down not_accepted (ret=False)
```

The system uses the following logic to determine accepted-by:
1. Check if `touch.ud['accepted_by']` is set (widgets that mark their acceptance)
2. If not set, make a best-effort guess based on:
   - Which collided child is likely to accept touches (TextInput, Button, MD* widgets, etc.)
   - The return value from the super() call
3. Log "not_accepted" if the touch was not handled

### 3. Focus Diagnostics for TextInput

The `LoginScreen` automatically binds to all `TextInput` widgets to log focus events.

**Example log output:**
```
[TouchTrace] Found 2 TextInput widgets in LoginScreen
[TouchTrace] focus widget=TextInput state=gained path=RotatingRoot/PortraitContainer/LoginScreen/BoxLayout/TextInput
[TouchTrace] focus widget=TextInput state=lost path=RotatingRoot/PortraitContainer/LoginScreen/BoxLayout/TextInput
```

This helps identify if TextInput widgets are receiving focus properly when touched.

## Implementation Details

### PortraitContainer Changes

The `PortraitContainer` class was enhanced with three new methods:

1. **`_log_touch_candidates(touch, orig_wx, orig_wy, phase)`**
   - Logs all direct children and their collision status
   - Called AFTER coordinate mapping but BEFORE dispatch
   - Includes both original window coordinates and mapped portrait coordinates

2. **`_log_accepted_by(touch, phase, ret_value)`**
   - Logs which widget accepted the touch
   - Called AFTER dispatch (super() call)
   - Checks touch.ud['accepted_by'] first, then makes best-effort guess

3. **`_get_widget_path(widget)`**
   - Returns a string representation of widget hierarchy
   - Example: "RotatingRoot/PortraitContainer/LoginScreen/BoxLayout/TextInput"
   - Limited to 5 levels to avoid excessive verbosity

### LoginScreen Changes

The `LoginScreen` class was enhanced with:

1. **`_setup_focus_diagnostics()`**
   - Scheduled 0.1 seconds after widget construction
   - Walks the widget tree to find all TextInput widgets
   - Binds to their focus events for logging

2. **`_on_textinput_focus(textinput, focused)`**
   - Logs focus state changes (gained/lost)
   - Includes widget path for easy identification

3. **Touch event handlers (`on_touch_down/move/up`)**
   - Set `touch.ud['accepted_by'] = self` when handling touches
   - Allows PortraitContainer to accurately identify which widget handled the touch

### No Behavior Changes

All changes are **logging-only**:
- Touch dispatch order is unchanged
- Return values from super() calls are preserved
- No widgets are added, removed, or modified (except for logging bindings)
- Layout and rendering are unaffected

## Usage

The TouchTrace diagnostics are **always active** - no configuration needed. Just run the app normally and check the logs when touching the screen in portrait mode.

### Reading the Logs

1. **Look for collision candidates** - which widgets are in the touch area?
   ```
   [TouchTrace] phase=down at=(540.0,960.0)->(540.0,960.0) candidates=[...]
   ```

2. **Check which widget accepted the touch**
   ```
   [TouchTrace] phase=down accepted_by=LoginScreen path=...
   ```

3. **Verify TextInput focus events**
   ```
   [TouchTrace] focus widget=TextInput state=gained path=...
   ```

### Identifying Ghost Hit Areas

If touches on a TextInput don't focus it, check for:

1. **A different widget accepting the touch before the TextInput**
   - Example: A parent container or overlay widget returning True and consuming the event

2. **TextInput showing as a collision candidate but not being the accepted_by widget**
   - This indicates something is blocking or consuming touches before they reach the TextInput

3. **No focus event logged when touching the TextInput**
   - Indicates the TextInput is not receiving the touch event at all

## Example Diagnostic Session

```
# User touches username field at window position (540, 960)

[Portrait] on_touch_down map inv=True from=(540.0,960.0) to=(540.0,960.0)

[TouchTrace] phase=down at=(540.0,960.0)->(540.0,960.0) candidates=[
  {'cls':'LoginScreen','pos':(0.0,0.0),'size':(1080.0,1920.0),'collide':True,'opacity':1.0},
  {'cls':'OverlayWidget','pos':(340.0,1000.0),'size':(400.0,200.0),'collide':True,'opacity':0.0}
]

[TouchTrace] phase=down accepted_by=OverlayWidget path=RotatingRoot/PortraitContainer/OverlayWidget

# ^ This reveals the problem: OverlayWidget (with opacity 0.0) is accepting touches
# even though it's invisible, blocking the LoginScreen underneath
```

## Related Files

- `main.py` - Contains PortraitContainer and LoginScreen implementations
- `test_touchtrace.py` - Static tests to verify TouchTrace implementation (not tracked in git due to .gitignore)
- `ENV_PORTRAIT_MAPPING.md` - Documentation for portrait coordinate mapping

## Testing

A static verification test script (`test_touchtrace.py`) is available to verify the implementation:

```bash
python test_touchtrace.py
```

This performs static code analysis to verify:
- TouchTrace methods exist in PortraitContainer
- LoginScreen schedules focus diagnostics
- Logging format matches requirements
- Original coordinates are preserved
- No behavior changes (dispatch order preserved)

Note: The test file is excluded from git by `.gitignore` (test_*.py pattern).

## Troubleshooting

### Logs Not Appearing

- Check that the app is running in portrait mode (aspect ratio 9:16)
- Verify that touches are being processed (existing [Portrait] logs should appear)
- Ensure logging level is set to INFO or DEBUG

### Too Much Log Noise

- The TouchTrace logs use the `[TouchTrace]` prefix for easy filtering
- You can grep for specific phases: `grep "TouchTrace.*phase=down"`
- Or filter for specific widgets: `grep "TouchTrace.*LoginScreen"`

### Understanding Widget Paths

Widget paths are shown in hierarchical order from root to leaf:
```
RotatingRoot/PortraitContainer/LoginScreen/BoxLayout/TextInput
└─ Root       └─ Container   └─ Screen   └─ Layout └─ Input field
```

Each component is either:
- Widget class name (if no id/name)
- Widget id (if set with `id='...'`)
- Widget name (if set with `name='...'`)
