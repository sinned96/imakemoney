#!/usr/bin/env python3
"""
diag_touch_release.py – Minimal standalone diagnostic for Button on_release
under the PortraitContainer matrix-pipeline touch mapping.

Purpose
-------
Reproduces and verifies the fix for the Kivy portrait-mode touch bug where
Login/Register buttons appeared to do nothing.

Root cause (PR #107 regression)
---------------------------------
PortraitContainer.on_touch_down applied an inverse-matrix transform to put
touch coordinates into virtual portrait space (1080×1920).  When a Button
grabbed the touch, the container *skipped* touch.pop() so the touch object
remained in portrait-space.  The intent was that Kivy's grab-dispatch phase
(Button.on_touch_up with grab_current=self) would see portrait coords and
pass the collide_point check.

The regression: Kivy's input provider **overwrites** touch.x/y with the
current window coords for *every* new event (move/up).  So by the time
on_touch_up fires, the portrait coords set during on_touch_down are gone.
The stale "don't pop" push had no effect.  The container dispatched on_touch_up
with window-space coords, ButtonBehavior.collide_point() failed, and
on_release never fired.

Fix (this PR)
-------------
1. on_touch_down: **always** pop after dispatch.  Set
   touch.ud['_portrait_transformed'] when a widget grabbed the touch so that
   on_touch_up knows to use the deferred-pop pattern.

2. on_touch_move: always apply a fresh inverse transform (push → apply →
   dispatch → pop).  Never short-circuit on _portrait_transformed.

3. on_touch_up: when _portrait_transformed is True, apply a fresh inverse
   transform (push → apply), dispatch, then *defer* the pop.  The deferred
   pop keeps portrait coords on the touch object until after Kivy's
   grab-dispatch fires (which happens after the normal tree walk on
   RPi / Kivy 2.3.1).  ButtonBehavior.on_touch_up checks collide_point when
   grab_current is self; with portrait coords in place this check passes and
   on_release fires correctly.

How to run
----------
1. Pure-Python simulation (no Kivy required) – run directly:

       python3 tools/diag_touch_release.py

   The mock Kivy classes simulate the grab mechanism *and* the provider
   coord-reset behaviour (MockTouch.reset_coords()) to verify on_release
   fires for a realistic down→up sequence.

2. Live app – set env var before launching main.py:

       DIAG_TOUCH_TRACE=1 PORTRAIT_PIPELINE=matrix python3 main.py

   Then tap the Login button.  The log (projekt.log) should contain lines
   like::

       [Portrait] on_touch_down matrix map pos=(...)
       [Portrait] on_touch_down grab detected – will apply fresh transform on up
       [Portrait] on_touch_up matrix map (grab) pos=(...)
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

    def reset_coords(self, x, y):
        """Simulate Kivy's input provider resetting touch.x/y for a new event.

        In real Kivy the input provider overwrites touch.x/y (and their
        normalised counterparts) for every move/up event.  The push/pop stack
        is NOT affected – it retains whatever was pushed earlier.  Calling
        this method before dispatching move/up accurately reproduces that
        behaviour.
        """
        self.x = x
        self.y = y


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
            print("[PortraitContainer] grab detected – will apply fresh transform on up")
            touch.ud['_portrait_transformed'] = True
        # Always pop: Kivy's input provider resets touch.x/y to window coords for
        # every subsequent event (move/up), so keeping portrait coords on the
        # touch object between events provides no benefit.  on_touch_up applies a
        # fresh transform and uses deferred-pop instead.
        touch.pop()
        return ret

    def on_touch_move(self, touch):
        inv = self._inverse_matrix
        if inv is None:
            return self._dispatch_move(touch)

        # Always apply a fresh inverse transform.  The provider has reset
        # touch.x/y to window coords for this event.
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
            # Grab path: apply a fresh inverse transform for this event.
            # (touch.x/y was reset to window coords by the input provider.)
            # Push the current (window) coords, transform to portrait, dispatch,
            # then defer the pop so that Kivy's grab-dispatch (which fires after
            # the normal tree walk) still sees portrait coords when
            # ButtonBehavior.on_touch_up checks collide_point.
            touch.push()
            touch.apply_transform_2d(lambda x, y: inv.transform_point(x, y, 0)[:2])
            ret = self._dispatch_up(touch)
            def _deferred_pop(dt, _touch=touch):
                try:
                    _touch.pop()  # paired with push above
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
    Simulate Kivy's Window-level grab dispatch for on_touch_up.

    In Kivy 2.3.1 on Raspberry Pi, grab-dispatch fires *after* the normal
    on_touch_up widget-tree walk.  Kivy wraps each grab-dispatch call with
    push()/pop() so the widget sees the current touch state (portrait coords
    if we have not yet popped them via the deferred callback).

    Kivy calls widget.dispatch('on_touch_up', touch) with grab_current set
    to each grabbing widget.
    """
    for widget in list(touch.grab_list):
        touch.push()           # Kivy wraps each grab dispatch with push/pop
        touch.grab_current = widget
        widget.on_touch_up(touch)
        touch.grab_current = None
        touch.pop()            # restore after grab dispatch


def _simulate_grab_dispatch_move(touch, container):
    """Same as above but for move events."""
    for widget in list(touch.grab_list):
        touch.push()
        touch.grab_current = widget
        widget.on_touch_move(touch)
        touch.grab_current = None
        touch.pop()


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
    Full down→up cycle with provider-reset simulation (realistic Kivy behaviour).

    Kivy's input provider overwrites touch.x/y with window coords for every
    new event (move/up).  We simulate this with reset_coords().  Grab-dispatch
    fires *after* the normal tree walk (Kivy 2.3.1 / Raspberry Pi order).

    Sequence:
      1. provider sets down coords → container.on_touch_down → grab → pop
      2. provider resets touch to up window coords
      3. container.on_touch_up → fresh transform → deferred pop scheduled
      4. grab-dispatch (with Kivy-style push/pop) → portrait coords → on_release
      5. MockClock.flush → deferred pop → stack balanced
    """
    MockClock.reset()
    mat = MockMatrix(virtual_w=1080, virtual_h=1920, win_w=1920, win_h=1080)
    s = mat._scale
    ox, oy, Pw = mat._ox, mat._oy, 1080

    # Button lives at portrait (300, 50, 200, 70), center=(400, 85)
    button = MockButton(x=300, y=50, w=200, h=70)
    container = MockPortraitContainer(inv_matrix=mat)
    container.add_child(button)

    # Window coords for the centre of the portrait button
    u_c, v_c = 400, 85
    xw_down = ox + s * v_c
    yw_down = oy + s * (Pw - u_c)

    touch = MockTouch(x=xw_down, y=yw_down)

    # 1. down
    container.on_touch_down(touch)
    assert button in touch.grab_list, "Button should have grabbed the touch"
    assert touch.ud.get('_portrait_transformed'), "_portrait_transformed flag must be set"
    # After always-pop, touch is back in window coords
    assert touch.x == xw_down, "touch must be back in window coords after on_touch_down"

    # 2. Kivy input provider resets touch.x/y to the up-event window coords
    #    (may differ from down coords if the finger moved slightly)
    xw_up = xw_down + 2   # slight drift, still maps onto the button
    yw_up = yw_down + 1
    touch.reset_coords(xw_up, yw_up)

    # 3. normal on_touch_up tree walk
    container.on_touch_up(touch)
    assert not button.released, "on_release must NOT have fired before grab-dispatch"
    assert touch.ud.get('_portrait_transformed'), \
        "Touch must still carry _portrait_transformed until deferred pop runs"

    # 4. grab-dispatch fires (Kivy wraps with push/pop)
    _simulate_grab_dispatch_up(touch, container)
    assert button.released, "Button on_release must fire during grab-dispatch"

    # 5. next-frame clock flush executes the deferred pop
    MockClock.flush()
    assert '_portrait_transformed' not in touch.ud, \
        "Flag must be cleared after deferred pop"
    assert len(touch._stack) == 0, \
        f"Push/pop imbalance after flush: stack={touch._stack}"


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


def test_fresh_transform_on_move():
    """
    on_touch_move must apply a fresh inverse transform even for grabbed touches.

    With the new always-pop design, on_touch_down pops the touch back to window
    coords.  Kivy's provider then resets touch.x/y to new window coords for the
    move event.  on_touch_move must therefore always push/transform/dispatch/pop
    to give children portrait-space coordinates.
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
    # After always-pop, touch is in window coords
    assert touch.x == xw, "touch must be in window coords after on_touch_down"

    # Simulate provider reset for move event
    xw_move = xw + 3
    yw_move = yw - 2
    touch.reset_coords(xw_move, yw_move)

    # on_touch_move must transform fresh and restore after (no dangling push)
    stack_depth_before = len(touch._stack)
    container.on_touch_move(touch)
    assert len(touch._stack) == stack_depth_before, \
        "on_touch_move must leave push/pop stack balanced"
    # After the pop, touch is back in window coords
    assert touch.x == xw_move, \
        "touch must be back in window coords after on_touch_move"


def test_push_pop_balanced():
    """
    touch._stack should be empty (no dangling push) after a full down→up cycle
    with a grabbed widget once the deferred pop has been flushed.

    Includes provider-reset simulation for move and up events.
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

    # Simulate provider reset + move
    touch.reset_coords(xw + 2, yw + 1)
    _simulate_grab_dispatch_move(touch, container)
    container.on_touch_move(touch)

    # Simulate provider reset + up
    touch.reset_coords(xw + 1, yw)
    _simulate_grab_dispatch_up(touch, container)
    container.on_touch_up(touch)
    # Flush the deferred pop scheduled by on_touch_up.
    MockClock.flush()

    assert len(touch._stack) == 0, f"Push/pop imbalance: stack={touch._stack}"


def test_button_release_fires_real_kivy_order():
    """
    On Kivy 2.3.1 / Raspberry Pi the Window-level grab-dispatch fires *after*
    the normal widget-tree walk.  Verify that on_release still fires when this
    ordering is used, including the provider-reset simulation.

    Sequence:
      1. container.on_touch_down   → transforms, grabs, always pops
      2. provider resets touch to up-event window coords
      3. container.on_touch_up     → fresh transform, dispatches, deferred pop
      4. grab-dispatch             → Kivy push/pop → portrait coords → on_release
      5. MockClock.flush           → deferred pop → stack balanced
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
    # After always-pop, touch is back in window coords
    assert touch.x == xw

    # 2. provider resets touch to up-event window coords
    touch.reset_coords(xw, yw)   # same position (finger didn't move)

    # 3. normal on_touch_up tree walk (grab-dispatch has NOT happened yet)
    container.on_touch_up(touch)
    assert not button.released, "on_release must NOT have fired before grab-dispatch"
    # Touch must still carry _portrait_transformed (deferred pop not yet flushed)
    assert touch.ud.get('_portrait_transformed'), \
        "Touch must remain flagged until deferred pop runs"

    # 4. grab-dispatch fires after the normal tree walk (Kivy push/pop wrapping)
    _simulate_grab_dispatch_up(touch, container)
    assert button.released, "on_release must fire during grab-dispatch"

    # 5. next-frame clock flush executes the deferred pop
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

    run_test("Button on_release fires in portrait mode (provider-reset simulation)",
             test_button_release_fires_in_portrait)
    run_test("Out-of-bounds touch is ignored", test_out_of_bounds_touch_ignored)
    run_test("Fresh transform on move (provider-reset simulation)",
             test_fresh_transform_on_move)
    run_test("Push/pop balanced after full gesture (provider-reset simulation)",
             test_push_pop_balanced)
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
