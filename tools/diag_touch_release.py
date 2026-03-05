#!/usr/bin/env python3
"""
diag_touch_release.py – Minimal standalone diagnostic for Button on_release
under the PortraitContainer matrix-pipeline touch mapping.

Purpose
-------
Reproduces and verifies the fix for the Kivy portrait-mode touch bug where
Login/Register buttons appeared to do nothing.

Root cause
----------
PortraitContainer.on_touch_down applied an inverse-matrix transform to put
touch coordinates into virtual portrait space (1080×1920) and then called
touch.pop() unconditionally after the dispatch.  When a Button called
touch.grab(self) during on_touch_down, Kivy's grab-dispatch phase later
called Button.on_touch_up directly with the *window* coordinates (not
portrait).  ButtonBehavior's on_touch_up checks collide_point when
always_release=False (the default), so the position check failed and
on_release never fired.

Fix
---
After on_touch_down dispatch, if touch.grab_list is non-empty, the container
now skips touch.pop() and records touch.ud['_portrait_transformed'] = True.
The touch stays in portrait space for the entire gesture lifecycle.
on_touch_move/up detect the flag and skip re-applying the transform.
on_touch_up pops the touch (restoring window coords) and clears the flag.

How to run
----------
This script works in two modes:

1. Pure-Python simulation (no Kivy required) – run directly:

       python3 tools/diag_touch_release.py

   The mock Kivy classes simulate the grab mechanism and verify that
   on_release fires for a simulated down→up sequence.

2. Live app – set env var before launching main.py:

       DIAG_TOUCH_TRACE=1 PORTRAIT_PIPELINE=matrix python3 main.py

   Then tap the Login button.  The log (projekt.log) should contain lines
   like::

       [Portrait] on_touch_down matrix map pos=(...)
       [Portrait] on_touch_down grab detected – keeping touch in portrait space
       [diag] touch up win=(...) accepted_by=Button path=[...]
       try_login called

   If the fix is NOT present the log would NOT contain "try_login called".
"""

import sys
import traceback

# ---------------------------------------------------------------------------
# Minimal mock classes – no real Kivy import needed
# ---------------------------------------------------------------------------

class MockMatrix:
    """
    Inverse matrix that maps (x_win, y_win) → (x_portrait, y_portrait).

    Forward transform (portrait → window) for -90° rotation:
        xw = ox + s * v
        yw = oy + s * (Pw - u)
    Inverse (window → portrait):
        u  = Pw - (yw - oy) / s       ← portrait x, range [0, virtual_w]
        v  = (xw - ox) / s            ← portrait y, range [0, virtual_h]
    """
    def __init__(self, virtual_w=1080, virtual_h=1920, win_w=1920, win_h=1080):
        # After -90° rotation the rotated frame is virtual_h wide × virtual_w tall
        rot_w = virtual_h   # 1920 for default values
        rot_h = virtual_w   # 1080
        scale = min(win_w / rot_w, win_h / rot_h)
        blit_w = rot_w * scale
        blit_h = rot_h * scale
        self._ox = (win_w - blit_w) / 2
        self._oy = (win_h - blit_h) / 2
        self._scale = scale
        self._Pw = virtual_w   # portrait width (1080)

    def transform_point(self, x, y, z=0):
        # Correct inverse of the -90° portrait pipeline
        u = self._Pw - (y - self._oy) / self._scale   # portrait x
        v = (x - self._ox) / self._scale               # portrait y
        return (u, v, z)


class MockClock:
    """
    Minimal stand-in for kivy.clock.Clock.

    Use only as a class-level utility (never instantiate it).  Collects
    callbacks registered with schedule_once() and executes them when
    flush() is called, simulating "next frame" behaviour without a real
    Kivy event loop.
    """
    _pending: list = []

    @classmethod
    def schedule_once(cls, callback, delay):
        cls._pending.append(callback)

    @classmethod
    def flush(cls):
        """Run all pending callbacks (in registration order) and clear the queue."""
        pending = cls._pending[:]
        cls._pending.clear()
        for cb in pending:
            cb(0)

    @classmethod
    def reset(cls):
        """Discard all pending callbacks (use between tests)."""
        cls._pending.clear()


class MockTouch:
    """Simplified stand-in for kivy.input.MotionEvent."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.ud = {}
        self.grab_list = []
        self.grab_current = None
        self._stack = []

    def push(self):
        self._stack.append((self.x, self.y))

    def pop(self):
        self.x, self.y = self._stack.pop()

    def apply_transform_2d(self, fn):
        self.x, self.y = fn(self.x, self.y)

    def grab(self, widget):
        self.grab_list.append(widget)


class MockButton:
    """Minimal Button-like widget with ButtonBehavior collide_point logic."""
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.always_release = False
        self.released = False  # set to True when on_release fires

    def collide_point(self, x, y):
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            touch.grab(self)
            return True
        return False

    def on_touch_move(self, touch):
        return touch.grab_current is self

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            # Normal (non-grab) dispatch – still check collide
            if self.collide_point(touch.x, touch.y):
                return True
            return False
        # Grab dispatch path
        touch.ungrab = lambda w: touch.grab_list.remove(w) if w in touch.grab_list else None
        if not self.always_release and not self.collide_point(touch.x, touch.y):
            # ButtonBehavior skips on_release when outside bounds
            return False
        self._do_release()
        return True

    def _do_release(self):
        self.released = True
        print("[MockButton] on_release fired – try_login would be called")


class MockPortraitContainer:
    """
    Stripped-down replica of the fixed PortraitContainer touch-dispatch logic.

    Only the matrix path for down/move/up is reproduced; diagnostic hooks are
    omitted for clarity.
    """
    def __init__(self, inv_matrix, virtual_w=1080, virtual_h=1920):
        self._inverse_matrix = inv_matrix
        self.virtual_w = virtual_w
        self.virtual_h = virtual_h
        self.children = []

    def add_child(self, widget):
        self.children.append(widget)

    # ---- helpers ----
    def _dispatch_down(self, touch):
        for child in self.children:
            if child.on_touch_down(touch):
                return True
        return False

    def _dispatch_move(self, touch):
        for child in self.children:
            if child.on_touch_move(touch):
                return True
        return False

    def _dispatch_up(self, touch):
        for child in self.children:
            if child.on_touch_up(touch):
                return True
        return False

    # ---- public touch handlers (mirrors fixed main.py) ----
    def on_touch_down(self, touch):
        inv = self._inverse_matrix
        if inv is None:
            return self._dispatch_down(touch)

        touch.push()
        touch.apply_transform_2d(lambda x, y: inv.transform_point(x, y, 0)[:2])

        # Bounds check
        if (touch.x < 0 or touch.x >= self.virtual_w or
                touch.y < 0 or touch.y >= self.virtual_h):
            print(f"[PortraitContainer] touch out-of-bounds portrait=({touch.x:.1f},{touch.y:.1f}), ignoring")
            touch.pop()
            return False

        ret = self._dispatch_down(touch)

        if touch.grab_list:
            print("[PortraitContainer] grab detected – keeping touch in portrait space")
            touch.ud['_portrait_transformed'] = True
            # Do NOT pop
        else:
            touch.pop()
        return ret

    def on_touch_move(self, touch):
        inv = self._inverse_matrix
        if inv is None:
            return self._dispatch_move(touch)

        if touch.ud.get('_portrait_transformed'):
            return self._dispatch_move(touch)

        touch.push()
        touch.apply_transform_2d(lambda x, y: inv.transform_point(x, y, 0)[:2])
        ret = self._dispatch_move(touch)
        touch.pop()
        return ret

    def on_touch_up(self, touch):
        inv = self._inverse_matrix
        if inv is None:
            return self._dispatch_up(touch)

        if touch.ud.get('_portrait_transformed'):
            ret = self._dispatch_up(touch)
            # Defer the pop so that grab-dispatch (which fires after the normal
            # widget-tree walk in real Kivy) still sees portrait-space coords.
            def _deferred_pop(dt, _touch=touch):
                try:
                    _touch.pop()  # paired with push in on_touch_down
                except IndexError:
                    pass
                _touch.ud.pop('_portrait_transformed', None)
            MockClock.schedule_once(_deferred_pop, 0)
            return ret

        touch.push()
        touch.apply_transform_2d(lambda x, y: inv.transform_point(x, y, 0)[:2])
        ret = self._dispatch_up(touch)
        touch.pop()
        return ret


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def _simulate_grab_dispatch_up(touch, container):
    """
    Simulate Kivy's Window-level grab dispatch.

    In some Kivy versions / platforms (including Kivy 2.3.1 on Raspberry Pi)
    grab-dispatch fires *after* the normal on_touch_up widget-tree walk.  In
    others it fires before.  Both orderings are covered by the test suite.

    Kivy calls widget.dispatch('on_touch_up', touch) with grab_current set
    to each grabbing widget.
    """
    for widget in list(touch.grab_list):
        touch.grab_current = widget
        widget.on_touch_up(touch)
        touch.grab_current = None


def _simulate_grab_dispatch_move(touch, container):
    """Same as above but for move events."""
    for widget in list(touch.grab_list):
        touch.grab_current = widget
        widget.on_touch_move(touch)
        touch.grab_current = None


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

results = []

def run_test(name, fn):
    try:
        fn()
        results.append((name, True, None))
        print(f"  {PASS}  {name}")
    except AssertionError as e:
        results.append((name, False, str(e)))
        print(f"  {FAIL}  {name}: {e}")
    except Exception as e:
        results.append((name, False, traceback.format_exc()))
        print(f"  {FAIL}  {name}: {e}")


def test_button_release_fires_in_portrait():
    """
    A touch that starts and ends inside the Login button should fire on_release
    when grab-dispatch fires before the normal widget-tree walk.
    Window: 1920×1080 (landscape SDL2 window rendering portrait content rotated -90°).
    Button in portrait space: x=300, y=50, w=200, h=70.
    Corresponding window-space center of button:
      xw = ox + s * v_center,  yw = oy + s * (Pw - u_center)
    where u_center=400, v_center=85 (center of button).
    """
    MockClock.reset()
    mat = MockMatrix(virtual_w=1080, virtual_h=1920, win_w=1920, win_h=1080)
    # Forward mapping helper: portrait (u,v) → window (xw, yw)
    # xw = ox + s*v,  yw = oy + s*(Pw - u)  (from -90° rotation formulation)
    s = mat._scale
    ox = mat._ox
    oy = mat._oy
    Pw = 1080

    # Button lives at portrait (x=300,y=50) size (200,70), center=(400,85)
    button = MockButton(x=300, y=50, w=200, h=70)
    container = MockPortraitContainer(inv_matrix=mat)
    container.add_child(button)

    # Window coordinate of button center
    u_c, v_c = 400, 85
    xw = ox + s * v_c
    yw = oy + s * (Pw - u_c)

    touch = MockTouch(x=xw, y=yw)

    # --- down ---
    container.on_touch_down(touch)
    assert button in touch.grab_list, "Button should have grabbed the touch"
    assert touch.ud.get('_portrait_transformed'), "_portrait_transformed flag must be set"

    # --- Kivy grab dispatch fires first (before normal on_touch_up tree walk) ---
    _simulate_grab_dispatch_up(touch, container)

    # Button should have fired on_release during grab dispatch
    assert button.released, "Button on_release must fire during grab dispatch"

    # --- normal on_touch_up tree walk ---
    container.on_touch_up(touch)
    # Flag is cleared and stack is popped via the deferred callback; flush it.
    MockClock.flush()
    assert '_portrait_transformed' not in touch.ud, "Flag must be cleared after deferred pop"


def test_out_of_bounds_touch_ignored():
    """
    A touch in the letterbox area (outside virtual 1080×1920 region) must be
    rejected by on_touch_down (returns False, no grab set).
    Window 800×600: scale = min(800/1920, 600/1080) ≈ 0.417
    ox=(800 - 1920*0.417)/2 ≈ (800 - 800)/2 = 0  (no letterbox horizontally)
    oy=(600 - 1080*0.417)/2 ≈ (600 - 450)/2 = 75  (75 px top/bottom letterbox)
    A touch at (400, 10) is in the bottom letterbox strip (yw < oy).
    """
    mat = MockMatrix(virtual_w=1080, virtual_h=1920, win_w=800, win_h=600)
    button = MockButton(x=300, y=50, w=200, h=70)
    container = MockPortraitContainer(inv_matrix=mat)
    container.add_child(button)

    # Touch is in the letterbox area (below oy)
    touch = MockTouch(x=400, y=10)
    ret = container.on_touch_down(touch)
    assert ret is False, "Out-of-bounds touch should return False"
    assert button not in touch.grab_list, "Button must NOT grab an out-of-bounds touch"


def test_no_double_transform_on_move():
    """
    When _portrait_transformed is set, on_touch_move must not push/transform
    the touch again.  If it did, the coordinates would be wrong.
    """
    mat = MockMatrix()
    button = MockButton(x=300, y=50, w=200, h=70)
    container = MockPortraitContainer(inv_matrix=mat)
    container.add_child(button)

    s = mat._scale
    ox, oy, Pw = mat._ox, mat._oy, 1080
    xw = ox + s * 85
    yw = oy + s * (Pw - 400)
    touch = MockTouch(x=xw, y=yw)

    container.on_touch_down(touch)
    assert touch.ud.get('_portrait_transformed')

    x_after_down = touch.x
    y_after_down = touch.y

    # Simulate Kivy grab dispatch for move
    _simulate_grab_dispatch_move(touch, container)

    # Normal on_touch_move – coordinates must not change
    container.on_touch_move(touch)
    assert touch.x == x_after_down, "on_touch_move must not re-transform x"
    assert touch.y == y_after_down, "on_touch_move must not re-transform y"


def test_push_pop_balanced():
    """
    touch._stack should be empty (no dangling push) after a full down→up cycle
    with a grabbed widget once the deferred pop has been flushed.
    """
    MockClock.reset()
    mat = MockMatrix()
    button = MockButton(x=300, y=50, w=200, h=70)
    container = MockPortraitContainer(inv_matrix=mat)
    container.add_child(button)

    s, ox, oy, Pw = mat._scale, mat._ox, mat._oy, 1080
    xw = ox + s * 85
    yw = oy + s * (Pw - 400)
    touch = MockTouch(x=xw, y=yw)

    container.on_touch_down(touch)
    _simulate_grab_dispatch_move(touch, container)
    container.on_touch_move(touch)
    _simulate_grab_dispatch_up(touch, container)
    container.on_touch_up(touch)
    # Flush the deferred pop scheduled by on_touch_up.
    MockClock.flush()

    assert len(touch._stack) == 0, f"Push/pop imbalance: stack={touch._stack}"


def test_button_release_fires_real_kivy_order():
    """
    On Kivy 2.3.1 / Raspberry Pi the Window-level grab-dispatch fires *after*
    the normal widget-tree walk.  Verify that on_release still fires when this
    ordering is used.

    Sequence:
      1. container.on_touch_down   → transforms, grabs, sets _portrait_transformed
      2. container.on_touch_up     → dispatches normally, schedules deferred pop
      3. grab-dispatch             → Button.on_touch_up with touch in portrait-space
                                     (pop not yet executed) → on_release fires
      4. MockClock.flush           → deferred pop executes, stack balanced
    """
    MockClock.reset()
    mat = MockMatrix(virtual_w=1080, virtual_h=1920, win_w=1920, win_h=1080)
    s = mat._scale
    ox, oy, Pw = mat._ox, mat._oy, 1080

    button = MockButton(x=300, y=50, w=200, h=70)
    container = MockPortraitContainer(inv_matrix=mat)
    container.add_child(button)

    # Window coords for the centre of the portrait button
    u_c, v_c = 400, 85
    xw = ox + s * v_c
    yw = oy + s * (Pw - u_c)
    touch = MockTouch(x=xw, y=yw)

    # 1. touch down
    container.on_touch_down(touch)
    assert touch.ud.get('_portrait_transformed'), "_portrait_transformed must be set after down"

    # 2. normal on_touch_up tree walk (grab-dispatch has NOT happened yet)
    container.on_touch_up(touch)
    assert not button.released, "on_release must NOT have fired before grab-dispatch"
    # Touch must still be in portrait-space (deferred pop not yet flushed)
    assert touch.ud.get('_portrait_transformed'), \
        "Touch must remain in portrait-space until deferred pop runs"

    # 3. grab-dispatch fires after the normal tree walk
    _simulate_grab_dispatch_up(touch, container)
    assert button.released, "on_release must fire during grab-dispatch"

    # 4. next-frame clock flush executes the deferred pop
    MockClock.flush()
    assert '_portrait_transformed' not in touch.ud, \
        "Flag must be cleared after deferred pop"
    assert len(touch._stack) == 0, \
        f"Push/pop imbalance after flush: stack={touch._stack}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("=" * 60)
    print("diag_touch_release.py – portrait touch mapping self-check")
    print("=" * 60)

    run_test("Button on_release fires in portrait mode", test_button_release_fires_in_portrait)
    run_test("Out-of-bounds touch is ignored", test_out_of_bounds_touch_ignored)
    run_test("No double transform on move", test_no_double_transform_on_move)
    run_test("Push/pop balanced after full gesture", test_push_pop_balanced)
    run_test("Button on_release fires – real Kivy grab-dispatch order (after normal walk)",
             test_button_release_fires_real_kivy_order)

    print()
    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = total - passed

    if failed == 0:
        print(f"All {total} tests passed.")
        sys.exit(0)
    else:
        print(f"{failed}/{total} tests FAILED.")
        sys.exit(1)
