from kivy.uix.widget import Widget
from kivy.logger import Logger
from kivy.core.window import Window
import inspect
import os
import math

class InputOverlayContainer(Widget):
    """
    Non-intrusive overlay with optional touch remap fix for matrix portrait pipeline.
    - Default: logging-only (does not consume or re-dispatch events)
    - Optional fix: if INPUT_OVERLAY_REMAP=1, remap Window touch coords to the
      portrait virtual space and transparently pass them on. Dabei wird pro Event
      die inverse Matrix des Zielwidgets vorübergehend deaktiviert (kein Double-Mapping).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._target = None
        self._inverse_matrix = None  # for logging only
        self._remap_enabled = os.getenv("INPUT_OVERLAY_REMAP", "0") == "1"

        # Full-window, but invisible and touch-transparent
        self.size_hint = (None, None)
        self.size = Window.size
        self.pos = (0, 0)
        Window.bind(size=lambda *_: self._resize_to_window())

        # Bind Window touch events for logging and optional remap
        Window.bind(on_touch_down=self._on_window_touch_down,
                    on_touch_move=self._on_window_touch_move,
                    on_touch_up=self._on_window_touch_up)

        Logger.info("[portrait_input_overlay]: installed (non-intrusive, logging-only)" +
                    (" + remap" if self._remap_enabled else ""))

    def _resize_to_window(self):
        self.size = Window.size
        self.pos = (0, 0)

    def set_target_widget(self, widget_or_class):
        # Accept instance or class; resolve class to instance if possible
        target = widget_or_class
        if inspect.isclass(widget_or_class):
            try:
                from kivy.app import App
                root = App.get_running_app().root
                if root:
                    for c in root.walk():
                        if isinstance(c, widget_or_class):
                            target = c
                            break
            except Exception:
                pass
        self._target = target
        Logger.info(f"[portrait_input_overlay] set_target_widget -> "
                    f"{getattr(target, '__class__', type(target)).__name__ if target else None}")

    def set_inverse_matrix(self, matrix):
        # Kept for compatibility/logging; remap uses analytic mapping (not this matrix)
        self._inverse_matrix = matrix
        Logger.info(f"[portrait_input_overlay] set_inverse_matrix -> {bool(matrix)}")

    # ----------------- Window-level observers -----------------
    def _log_touch(self, phase, touch, mapped=None):
        try:
            wx, wy = touch.pos
            if mapped is None and self._inverse_matrix is not None:
                # Fallback mapping for logs using provided inverse matrix (best-effort)
                try:
                    mx, my, _ = self._inverse_matrix.transform_point(wx, wy, 0)
                    mapped = (round(mx, 1), round(my, 1))
                except Exception:
                    mapped = None
            Logger.info(f"[InputOverlay] {phase} window={round(wx,1)},{round(wy,1)} "
                        f"mapped={mapped} id={getattr(touch,'id',None)} "
                        f"profile={getattr(touch,'profile',None)}")
        except Exception as e:
            Logger.warning(f"[InputOverlay] log failed ({phase}): {e}")

    def _map_window_to_virtual(self, wx, wy, v_w, v_h):
        """Analytic mapping from Window coords to portrait virtual coords.
        Mirrors: Translate(pos) · Translate(center) · Scale(s) · Rotate(angle) · Translate(-v_center)
        """
        try:
            angle_deg = int(os.getenv("PORTRAIT_ROTATION_DEGREES", "-90"))
            win_w, win_h = Window.size
            if abs(angle_deg) % 180 == 90:
                rot_w, rot_h = v_h, v_w
            else:
                rot_w, rot_h = v_w, v_h

            s = max(1e-6, min(win_w / rot_w, win_h / rot_h))
            blit_w, blit_h = rot_w * s, rot_h * s
            pos_x = (win_w - blit_w) / 2.0
            pos_y = (win_h - blit_h) / 2.0

            # Inverse of the forward pipeline
            cx = (wx - pos_x - blit_w / 2.0) / s
            cy = (wy - pos_y - blit_h / 2.0) / s

            rad = -math.radians(angle_deg)  # inverse rotate
            x2 = cx * math.cos(rad) - cy * math.sin(rad)
            y2 = cx * math.sin(rad) + cy * math.cos(rad)

            vx = x2 + v_w / 2.0
            vy = y2 + v_h / 2.0
            return vx, vy
        except Exception:
            return wx, wy  # safety fallback

    def _maybe_remap_in_place(self, touch):
        """If remap is enabled and target exists, mutate touch.x/y to virtual coords.
           Also disable target's own mapping temporarily to avoid double-transform."""
        if not self._remap_enabled or not self._target:
            return None

        v_w = getattr(self._target, 'virtual_w', 1080)
        v_h = getattr(self._target, 'virtual_h', 1920)
        vx, vy = self._map_window_to_virtual(touch.x, touch.y, v_w, v_h)

        # Mutate touch in-place so downstream handlers see corrected coords
        touch.x, touch.y = vx, vy

        # Temporarily disable the target's inverse mapping for this event
        if hasattr(self._target, '_inverse_matrix'):
            setattr(touch, '_ioverlay_prev_inv', self._target._inverse_matrix)
            self._target._inverse_matrix = None

        setattr(touch, '_ioverlay_mapped', True)
        return (round(vx, 1), round(vy, 1))

    def _restore_target_after_event(self, touch):
        prev = getattr(touch, '_ioverlay_prev_inv', None)
        if prev is not None and self._target is not None:
            self._target._inverse_matrix = prev
            try:
                delattr(touch, '_ioverlay_prev_inv')
            except Exception:
                pass

    def _on_window_touch_down(self, window, touch):
        mapped = self._maybe_remap_in_place(touch)
        self._log_touch("down", touch, mapped=mapped)
        # Do not consume; allow normal Kivy routing
        return False

    def _on_window_touch_move(self, window, touch):
        mapped = self._maybe_remap_in_place(touch)
        self._log_touch("move", touch, mapped=mapped)
        return False

    def _on_window_touch_up(self, window, touch):
        mapped = self._maybe_remap_in_place(touch)
        self._log_touch("up", touch, mapped=mapped)
        # Restore target mapping after gesture completes
        self._restore_target_after_event(touch)
        return False

    # Ensure we never consume via widget dispatch path
    def on_touch_down(self, touch): return False
    def on_touch_move(self, touch): return False
    def on_touch_up(self, touch): return False