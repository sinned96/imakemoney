# TouchTrace Example Log Output

This file shows example log output from the TouchTrace diagnostics to help understand what to expect.

## Scenario: User Taps Username Field in Portrait Mode

### Step 1: Touch Down Event

```
[2025-10-21 15:45:23] INFO [Portrait] on_touch_down map inv=True from=(540.0,960.0) to=(540.0,960.0)

[2025-10-21 15:45:23] INFO [TouchTrace] phase=down at=(540.0,960.0)->(540.0,960.0) candidates=[
  {'cls':'LoginScreen','id':None,'pos':(0.0,0.0),'size':(1080.0,1920.0),'collide':True,'opacity':1.0},
  {'cls':'Label','id':'debug_paint_label','pos':(10.0,1850.0),'size':(300.0,60.0),'collide':False,'opacity':1.0}
]

[2025-10-21 15:45:23] INFO [TouchTrace] phase=down accepted_by=LoginScreen path=RotatingRoot/PortraitContainer/LoginScreen

[2025-10-21 15:45:23] INFO [TouchTrace] focus widget=TextInput state=gained path=RotatingRoot/PortraitContainer/LoginScreen/BoxLayout/TextInput
```

**Analysis:**
- Touch at window position (540, 960) maps to same portrait position (coordinate mapping is working)
- Two candidates found: LoginScreen (collides) and debug Label (doesn't collide)
- LoginScreen accepts the touch
- TextInput gains focus (expected behavior - field works correctly)

---

## Scenario: User Taps Login Field but Ghost Widget Blocks It

### Step 1: Touch Down Event

```
[2025-10-21 15:46:12] INFO [Portrait] on_touch_down map inv=True from=(540.0,1060.0) to=(540.0,1060.0)

[2025-10-21 15:46:12] INFO [TouchTrace] phase=down at=(540.0,1060.0)->(540.0,1060.0) candidates=[
  {'cls':'LoginScreen','id':None,'pos':(0.0,0.0),'size':(1080.0,1920.0),'collide':True,'opacity':1.0},
  {'cls':'FloatLayout','id':'ghost_overlay','pos':(340.0,1000.0),'size':(400.0,200.0),'collide':True,'opacity':0.0},
  {'cls':'Label','id':'debug_paint_label','pos':(10.0,1850.0),'size':(300.0,60.0),'collide':False,'opacity':1.0}
]

[2025-10-21 15:46:12] INFO [TouchTrace] phase=down accepted_by=FloatLayout path=RotatingRoot/PortraitContainer/FloatLayout
```

**Analysis:**
- Touch at (540, 1060) is in the login field area
- Three candidates found, including a FloatLayout with opacity=0.0 (invisible!)
- The ghost FloatLayout collides with touch position AND accepts it
- No focus event logged (TextInput never receives the touch)
- **Problem identified:** The invisible FloatLayout at position (340, 1000) with size (400, 200) is blocking touches

**Solution:**
- Remove the ghost FloatLayout, OR
- Set its `disabled=True`, OR
- Override its `on_touch_down` to return False (don't consume)

---

## Scenario: Multiple Colliding Widgets

### Step 1: Touch Down Event

```
[2025-10-21 15:47:30] INFO [Portrait] on_touch_down map inv=True from=(640.0,1400.0) to=(640.0,1400.0)

[2025-10-21 15:47:30] INFO [TouchTrace] phase=down at=(640.0,1400.0)->(640.0,1400.0) candidates=[
  {'cls':'LoginScreen','id':None,'pos':(0.0,0.0),'size':(1080.0,1920.0),'collide':True,'opacity':1.0},
  {'cls':'BoxLayout','id':'card','pos':(300.0,1080.0),'size':(480.0,560.0),'collide':True,'opacity':1.0},
  {'cls':'TextInput','id':None,'pos':(328.0,1360.0),'size':(424.0,48.0),'collide':True,'opacity':1.0,'disabled':False},
  {'cls':'Label','id':'debug_paint_label','pos':(10.0,1850.0),'size':(300.0,60.0),'collide':False,'opacity':1.0}
]

[2025-10-21 15:47:30] INFO [TouchTrace] phase=down accepted_by_guess=TextInput path=RotatingRoot/PortraitContainer/LoginScreen/BoxLayout/TextInput

[2025-10-21 15:47:30] INFO [TouchTrace] focus widget=TextInput state=gained path=RotatingRoot/PortraitContainer/LoginScreen/BoxLayout/TextInput
```

**Analysis:**
- Touch collides with LoginScreen, BoxLayout (card), and TextInput
- All three are visible and enabled
- Best-effort guess identifies TextInput as the accepting widget
- Focus event confirms TextInput received and handled the touch correctly

---

## Scenario: Touch Outside All Widgets

### Step 1: Touch Down Event

```
[2025-10-21 15:48:15] INFO [Portrait] on_touch_down map inv=True from=(100.0,100.0) to=(100.0,100.0)

[2025-10-21 15:48:15] INFO [TouchTrace] phase=down at=(100.0,100.0)->(100.0,100.0) candidates=[
  {'cls':'LoginScreen','id':None,'pos':(0.0,0.0),'size':(1080.0,1920.0),'collide':True,'opacity':1.0},
  {'cls':'Label','id':'debug_paint_label','pos':(10.0,1850.0),'size':(300.0,60.0),'collide':False,'opacity':1.0}
]

[2025-10-21 15:48:15] INFO [TouchTrace] phase=down accepted_by=LoginScreen path=RotatingRoot/PortraitContainer/LoginScreen
```

**Analysis:**
- Touch at bottom-left corner (100, 100)
- LoginScreen collides (it fills the entire screen)
- Debug label doesn't collide
- LoginScreen accepts but likely just returns True without doing anything
- No focus change (no TextInput at that position)

---

## Using Grep to Filter Logs

### Find all touch down events
```bash
grep "TouchTrace.*phase=down" projekt.log
```

### Find which widget accepted a touch at specific coordinate
```bash
grep "TouchTrace.*at=(540" projekt.log | grep accepted_by
```

### Find all focus events
```bash
grep "TouchTrace.*focus" projekt.log
```

### Find touches handled by a specific widget
```bash
grep "TouchTrace.*accepted_by=FloatLayout" projekt.log
```

### Find invisible widgets that accept touches
```bash
grep "TouchTrace.*'opacity':0.0.*'collide':True" projekt.log
```
