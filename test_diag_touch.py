#!/usr/bin/env python3
"""
Manual Testing Guide for Touch Diagnostics Feature

This document provides manual testing instructions for the touch diagnostics feature.
The feature is designed to help debug touch input issues in portrait mode.

ENVIRONMENT FLAGS:
==================
- DIAG_TOUCH_TRACE=1          Enable touch tracing (default: 0/off)
- DIAG_TOUCH_TRACE_OVERLAY=1  Enable visual overlay markers (default: 0/off)
- DIAG_TOUCH_TRACE_LEVEL=debug   Set log level (default: info)

TEST SCENARIOS:
===============

Test 1: Basic Touch Tracing
----------------------------
Run with:
    DIAG_TOUCH_TRACE=1 PORTRAIT_PIPELINE=matrix python3 main.py

Expected behavior:
- On app start, you should see "[diag] TouchTraceController enabled" in logs
- On app start, you should see z-order summary showing widget hierarchy
- When clicking on login screen, you should see:
  [diag] touch down win=(x,y) accepted_by=... path=[...]
  [diag] touch up win=(x,y) accepted_by=... path=[...]
- Each log line should show:
  * Window coordinates (win=)
  * Widget that accepted the event (accepted_by=)
  * Dispatch path with collide and return info (path=)

Test 2: Visual Overlay Markers
-------------------------------
Run with:
    DIAG_TOUCH_TRACE=1 DIAG_TOUCH_TRACE_OVERLAY=1 PORTRAIT_PIPELINE=matrix python3 main.py

Expected behavior:
- Same as Test 1, plus:
- Small red dots with white crosshairs appear at touch coordinates
- Dots appear at the mapped (transformed) coordinates, not raw window coords
- This visually confirms the coordinate transformation is working correctly

Test 3: Focus Logging on Login Fields
--------------------------------------
Run with:
    DIAG_TOUCH_TRACE=1 PORTRAIT_PIPELINE=matrix python3 main.py

Expected behavior:
- Click on username field, you should see:
  [diag] focus TextInput#username=True cursor=(...)
- Click on password field, you should see:
  [diag] focus TextInput#password=True cursor=(...)
  [diag] focus TextInput#username=False cursor=(...)
- Focus logs include widget ID and cursor position

Test 4: Disabled Diagnostics (Default)
---------------------------------------
Run without flags:
    PORTRAIT_PIPELINE=matrix python3 main.py

Expected behavior:
- No "[diag]" log messages appear
- No visual overlay markers
- No performance impact
- Application behaves exactly as before

Test 5: Z-Order Diagnostics
----------------------------
Run with:
    DIAG_TOUCH_TRACE=1 PORTRAIT_PIPELINE=matrix python3 main.py

Expected behavior:
- On first widget add, you should see:
  [diag] Z-order summary (bottom to top):
  [diag]   [0] WidgetName(WxH@X,Y)
  [diag]   [1] WidgetName(WxH@X,Y)
  ...
- This shows the stacking order of widgets (helps identify overlays)

Test 6: Touch Move Event Throttling
------------------------------------
Run with:
    DIAG_TOUCH_TRACE=1 PORTRAIT_PIPELINE=matrix python3 main.py

Expected behavior:
- Drag/swipe on the screen
- Touch move events are logged but throttled (every 5th event)
- This prevents log spam while still providing useful info

Test 7: Debug Level Logging
----------------------------
Run with:
    DIAG_TOUCH_TRACE=1 DIAG_TOUCH_TRACE_LEVEL=debug PORTRAIT_PIPELINE=matrix python3 main.py

Expected behavior:
- More verbose diagnostic output
- Additional debug-level messages appear

VERIFICATION CHECKLIST:
=======================
[ ] Test 1: Basic touch tracing works (logs appear)
[ ] Test 2: Visual overlay markers appear at correct positions
[ ] Test 3: Focus logging works for username/password fields
[ ] Test 4: Disabled mode has zero impact (no logs, normal behavior)
[ ] Test 5: Z-order summary logged on startup
[ ] Test 6: Touch move events are throttled appropriately
[ ] Test 7: Debug level produces more verbose output

TROUBLESHOOTING:
================
If diagnostics don't work:
1. Check that DIAG_TOUCH_TRACE=1 is set before running the app
2. Check that PORTRAIT_PIPELINE=matrix (diagnostics only work with matrix pipeline)
3. Check the log file (projekt.log) for [diag] messages
4. Verify diag_touch.py was imported correctly (check import errors)

Example log output for successful touch event:
[INFO   ] [diag] touch down win=(500,600) norm=(0.260,0.556) accepted_by=TextInput#username path=[PortraitContainer(c=T,r=T), LoginScreen(c=T,r=T), TextInput#username(c=T,r=T)]
"""

print(__doc__)
print("\nThis file contains manual testing instructions.")
print("To run tests, follow the instructions above with the actual main.py application.")
print("\nNote: Automated unit tests require Kivy to be installed.")
