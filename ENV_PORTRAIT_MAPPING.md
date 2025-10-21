# Portrait Mode Touch Mapping Environment Variables

This document describes the environment variables used to control touch input mapping in portrait mode (-90° rotation).

## Core Configuration

### INPUT_OVERLAY_REMAP
- **Default**: `0` (disabled)
- **Values**: `0` or `1`
- **Description**: When enabled, the input overlay intercepts and remaps touch coordinates before they reach the container. This is useful for testing overlay-based remapping vs container-based remapping.
- **Usage**: `INPUT_OVERLAY_REMAP=1 python main.py`

### INPUT_OVERLAY_ANALYTIC
- **Default**: `0` (use matrix)
- **Values**: `0` or `1`
- **Description**: When enabled with `INPUT_OVERLAY_REMAP=1`, uses analytical mapping instead of matrix-based inverse transform. The analytical mapping is mathematically equivalent but can be more robust.
- **Usage**: `INPUT_OVERLAY_REMAP=1 INPUT_OVERLAY_ANALYTIC=1 python main.py`

### INPUT_ANALYTIC_MAP
- **Default**: `0` (use matrix)
- **Values**: `0` or `1`
- **Description**: When enabled, the container's touch handlers use analytical mapping instead of matrix-based inverse transform. This is a fallback option if matrix inversion causes issues.
- **Usage**: `INPUT_ANALYTIC_MAP=1 python main.py`

## Testing Scenarios

### Scenario 1: Default (Matrix-based container mapping)
```bash
python main.py
```
- Overlay logs touches but doesn't remap (logging-only mode)
- Container uses matrix inverse to map touches
- Expected log: `[Portrait] on_touch_down map inv=True from=(x,y) to=(u,v)`

### Scenario 2: Overlay remap with matrix (REMAP=1)
```bash
INPUT_OVERLAY_REMAP=1 python main.py
```
- Overlay remaps using matrix inverse
- Container bypasses its own mapping (overlay already mapped)
- Expected log: `[InputOverlay] down mode=remap from=(x,y) to=(u,v) inv_present=True`
- Expected log: `[Portrait] Bypass mapping for overlay-remapped touch`

### Scenario 3: Overlay remap with analytical mapping
```bash
INPUT_OVERLAY_REMAP=1 INPUT_OVERLAY_ANALYTIC=1 python main.py
```
- Overlay remaps using analytical formulas
- Container bypasses its own mapping
- Expected log: `[InputOverlay] down mode=remap from=(x,y) to=(u,v) inv_present=True`

### Scenario 4: Container analytical mapping (fallback mode)
```bash
INPUT_ANALYTIC_MAP=1 python main.py
```
- Overlay logs only (no remap)
- Container uses analytical mapping instead of matrix
- Expected log: `[Portrait] on_touch_down analytic map from=(x,y) to=(u,v) s=... pos=(...) Pw=...`

## Expected Results

In all scenarios with correct mapping:
- Portrait coordinates `(u, v)` should be in range `[0..1080]` x `[0..1920]`
- No negative coordinates
- No coordinates exceeding portrait bounds
- Username and password fields on LoginScreen should be clickable
- No ghost touch areas

## Diagnostics

### Startup Logs
On startup, look for these diagnostic logs:
```
[Portrait matrix] Pipeline params: event=WxH s=... pos=(ox,oy) forced_size=(1080,1920) rot=-90
[Portrait matrix] Forward mapping (portrait→window):
  portrait (0,0) [bottom-left] → window (...)
  ...
[Portrait matrix] Inverse mapping (window→portrait):
  window (0,0) [bottom-left] → portrait (...)
  ...
[Portrait matrix] Analytical validation at window center: matrix=(...) analytical=(...) diff=(...)
```

The diff between matrix and analytical should be < 0.01 pixels.

### Runtime Logs
During touch events, look for:
```
[InputOverlay] down mode=remap from=(win) to=(u,v) inv_present=True
```
or
```
[Portrait] on_touch_down map inv=True from=(win) to=(u,v)
```

Values should show:
- `from=` coordinates in window space (e.g., 0..1920 x 0..1080 for 1920x1080 window)
- `to=` coordinates in portrait space (0..1080 x 0..1920)

## Mathematical Formulas

### Forward Mapping (Portrait → Window)
For -90° rotation with scale `s` and offset `(ox, oy)`:
```
xw = ox + s * v
yw = oy + s * (Pw - u)
```
Where `(u, v)` are portrait coordinates and `Pw = 1080`.

### Inverse Mapping (Window → Portrait)
```
u = Pw - (yw - oy) / s
v = (xw - ox) / s
```

### Matrix Form
Forward transform matrix:
```
M_fwd = T(ox, oy) · S(s) · T(0, Pw) · R(-90°)
```

Inverse transform:
```
M_inv = inverse(M_fwd)
```
