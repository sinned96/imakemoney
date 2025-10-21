# Touch Diagnostics Feature

## Overview

This feature provides opt-in diagnostics for debugging touch input issues in portrait mode. It helps identify which widgets accept touch events, track focus changes, and visualize coordinate mapping.

## Features

1. **Touch Event Tracing**: Logs detailed information about each touch event (down/move/up)
2. **Focus Logging**: Tracks when TextInput widgets gain/lose focus
3. **Visual Overlay**: Optional red dot markers showing mapped touch coordinates
4. **Z-Order Diagnostics**: Logs widget hierarchy on startup
5. **Zero Impact When Disabled**: No performance overhead or behavioral changes

## Environment Flags

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `DIAG_TOUCH_TRACE` | `0`, `1`, `true`, `false` | `0` (off) | Enable touch tracing |
| `DIAG_TOUCH_TRACE_OVERLAY` | `0`, `1`, `true`, `false` | `0` (off) | Draw visual markers at touch points |
| `DIAG_TOUCH_TRACE_LEVEL` | `info`, `debug` | `info` | Log verbosity level |

## Usage Examples

### Basic Touch Tracing

```bash
DIAG_TOUCH_TRACE=1 PORTRAIT_PIPELINE=matrix python3 main.py
```

Expected log output:
```
[INFO   ] [diag] TouchTraceController enabled: overlay=False level=info
[INFO   ] [diag] Z-order summary (bottom to top):
[INFO   ] [diag]   [0] PortraitContainer(1920x1080@0,0)
[INFO   ] [diag]   [1] LoginScreen(480x560@720,260)
[INFO   ] [diag] touch down win=(850,640) norm=(0.442,0.593) accepted_by=TextInput#username path=[PortraitContainer(c=T,r=T), LoginScreen(c=T,r=T), TextInput#username(c=T,r=T)]
[INFO   ] [diag] focus TextInput#username=True cursor=(0, 0)
[INFO   ] [diag] touch up win=(850,640) norm=(0.442,0.593) accepted_by=TextInput#username path=[...]
```

### With Visual Overlay

```bash
DIAG_TOUCH_TRACE=1 DIAG_TOUCH_TRACE_OVERLAY=1 PORTRAIT_PIPELINE=matrix python3 main.py
```

This adds small red dots with white crosshairs at each touch point, helping visualize coordinate mapping.

### Debug Level Logging

```bash
DIAG_TOUCH_TRACE=1 DIAG_TOUCH_TRACE_LEVEL=debug PORTRAIT_PIPELINE=matrix python3 main.py
```

Provides more verbose diagnostic output for deep debugging.

## Log Format

### Touch Event Log

```
[diag] touch {phase} win=(x,y) norm=(sx,sy) accepted_by={widget} path=[{path}]
```

Where:
- `{phase}`: `down`, `move`, or `up`
- `win=(x,y)`: Window coordinates (pixels)
- `norm=(sx,sy)`: Normalized coordinates (0-1 range)
- `{widget}`: Widget that accepted the event (e.g., `TextInput#username`)
- `{path}`: List of widgets in dispatch path with collide/return info

Example:
```
[diag] touch down win=(500,600) accepted_by=Button#login path=[Root(c=T,r=T), Panel(c=T,r=F), Button#login(c=T,r=T)]
```

### Focus Change Log

```
[diag] focus {widget}={focused} cursor=(x,y)
```

Example:
```
[diag] focus TextInput#password=True cursor=(5, 0)
```

### Z-Order Summary

```
[diag] Z-order summary (bottom to top):
[diag]   [0] WidgetClass#id(WxH@X,Y)
[diag]   [1] WidgetClass#id(WxH@X,Y)
```

Example:
```
[diag] Z-order summary (bottom to top):
[diag]   [0] FloatLayout(1920x1080@0,0)
[diag]   [1] LoginScreen(480x560@720,260)
[diag]   [2] InputOverlay(1920x1080@0,0)
```

## Path Entry Format

Each path entry shows:
- Widget class name and ID (if available)
- `c=T/F`: Whether widget's `collide_point()` returned True/False
- `r=T/F`: Whether widget's touch handler returned True/False

Example: `TextInput#username(c=T,r=T)` means the username TextInput collided with the touch and accepted it.

## Implementation Details

### Files

1. **diag_touch.py**: Core diagnostics module with `TouchTraceController` class
2. **main.py**: Instrumented touch handlers in `PortraitContainer` and focus bindings in `LoginScreen`

### Integration Points

1. **PortraitContainer.on_touch_down/move/up**: Wraps touch handlers to collect dispatch path and log events
2. **LoginScreen.__init__**: Binds focus listeners to username/password TextInput widgets
3. **RotatingRoot.add_widget**: Logs z-order summary on first widget add

### Performance Considerations

- Touch move events are throttled (logged every 5th event) to prevent log spam
- All diagnostics are behind `if enabled()` checks for zero overhead when disabled
- Path collection is minimal and only done when diagnostics are active

## Troubleshooting

### No diagnostic logs appear

1. Verify `DIAG_TOUCH_TRACE=1` is set before running the app
2. Check that `PORTRAIT_PIPELINE=matrix` (diagnostics only work with matrix pipeline)
3. Look in the log file (`projekt.log`) for `[diag]` messages

### Visual markers don't appear

1. Verify both `DIAG_TOUCH_TRACE=1` and `DIAG_TOUCH_TRACE_OVERLAY=1` are set
2. Check that touches are actually being processed (check log output)

### Focus logging doesn't work

1. Verify you're clicking on the username or password fields
2. Check that the TextInput widgets have IDs set (`username`, `password`)
3. Look for `[diag] focus` messages in logs

## Testing

Run the manual testing guide:

```bash
python3 test_diag_touch.py
```

This displays comprehensive testing instructions for all features.

## Future Enhancements

Possible improvements:
- Add dispatch tree visualization
- Track gesture recognition (swipes, drags)
- Record and replay touch sequences
- Heatmap of touch distribution
- Performance metrics (dispatch time)

## Related Issues

This feature addresses the "ghost hit area" problem mentioned in the portrait rotation context, where touches seem to land in unexpected places despite correct visual rotation. The diagnostics help identify:

1. Which widget is actually receiving touches
2. Whether coordinate mapping is working correctly
3. If any overlay widgets are intercepting touches
4. The complete dispatch path from window to leaf widget
