from kivy.uix.widget import Widget
from kivy.logger import Logger
from kivy.core.window import Window
import inspect
import os
import math

def window_to_portrait_overlay(xw, yw, ox, oy, s, Pw):
    """
    Analytically map window coordinates to portrait coordinates for -90° rotation.
    
    This is the exact inverse of the forward mapping:
    - Forward: xw = ox + s*v, yw = oy + s*(Pw - u)
    - Inverse: u = Pw - (yw - oy)/s, v = (xw - ox)/s
    
    Args:
        xw, yw: Window coordinates
        ox, oy: Letterbox offset (position of rotated viewport in window)
        s: Scale factor
        Pw: Portrait width (1080 for this app)
    
    Returns:
        (u, v): Portrait coordinates
    """
    u = Pw - (yw - oy) / s
    v = (xw - ox) / s
    return u, v

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
        self._use_analytic = os.getenv("INPUT_OVERLAY_ANALYTIC", "0") == "1"

        # Full-window, but invisible and touch-transparent
        self.size_hint = (None, None)
        self.size = Window.size
        self.pos = (0, 0)
        Window.bind(size=lambda *_: self._resize_to_window())

        # Bind Window touch events for logging and optional remap
        Window.bind(on_touch_down=self._on_window_touch_down,
                    on_touch_move=self._on_window_touch_move,
                    on_touch_up=self._on_window_touch_up)

        mode = "remap" if self._remap_enabled else "logging-only"
        mapping = "analytical" if self._use_analytic else "matrix"
        Logger.info(f"[portrait_input_overlay]: installed mode={mode} mapping={mapping}")

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
    def _maybe_remap_in_place(self, touch):
        """
        If remap is enabled, use target's analytical mapping or inverse matrix to transform touch coords.
        Returns tuple (wx, wy, tx, ty, inv_present) if remapped, None otherwise.
        """
        if not self._remap_enabled or not self._target:
            return None
        
        # Store original window coordinates
        orig_x, orig_y = touch.x, touch.y
        
        # Try analytical mapping first if enabled
        if self._use_analytic:
            params = getattr(self._target, '_portrait_params', None)
            if params:
                try:
                    tx, ty = window_to_portrait_overlay(
                        orig_x, orig_y, 
                        params['ox'], params['oy'], 
                        params['s'], params['Pw']
                    )
                    
                    # Mutate touch in-place
                    touch.x, touch.y = tx, ty
                    
                    # Tag the event so PortraitContainer bypasses its own transform
                    touch._ioverlay_mapped = True
                    
                    return (orig_x, orig_y, tx, ty, True)
                except Exception as e:
                    Logger.warning(f"[InputOverlay] Analytical mapping failed: {e}")
        
        # Fallback to inverse matrix
        inv = getattr(self._target, '_inverse_matrix', None)
        if inv is None:
            return None
        
        # Transform using the target's actual inverse matrix
        try:
            tx, ty, _ = inv.transform_point(orig_x, orig_y, 0)
        except Exception:
            return None
        
        # Mutate touch in-place
        touch.x, touch.y = tx, ty
        
        # Tag the event so PortraitContainer bypasses its own transform
        touch._ioverlay_mapped = True
        
        # Temporarily disable target's inverse during dispatch to prevent double-transform
        if hasattr(self._target, '_inverse_matrix'):
            setattr(touch, '_ioverlay_prev_inv', self._target._inverse_matrix)
            self._target._inverse_matrix = None
        
        return (orig_x, orig_y, tx, ty, True)
    
    def _restore_target_after_dispatch(self, touch):
        """Restore target's inverse matrix after event dispatch"""
        prev = getattr(touch, '_ioverlay_prev_inv', None)
        if prev is not None and self._target is not None:
            self._target._inverse_matrix = prev
            try:
                delattr(touch, '_ioverlay_prev_inv')
            except Exception:
                pass

    def _on_window_touch_down(self, window, touch):
        if self._remap_enabled:
            result = self._maybe_remap_in_place(touch)
            if result:
                wx, wy, tx, ty, inv_present = result
                Logger.info(f"[InputOverlay] down mode=remap from=({round(wx,1)},{round(wy,1)}) "
                           f"to=({round(tx,1)},{round(ty,1)}) inv_present={inv_present}")
            else:
                Logger.info(f"[InputOverlay] down mode=remap (no inv) window={round(touch.x,1)},{round(touch.y,1)}")
        else:
            # Logging-only mode: do not modify touch or target
            Logger.info(f"[InputOverlay] down mode=logging-only passthrough window={round(touch.x,1)},{round(touch.y,1)}")
        # Do not consume; allow normal Kivy routing
        return False

    def _on_window_touch_move(self, window, touch):
        if self._remap_enabled:
            result = self._maybe_remap_in_place(touch)
            if result:
                wx, wy, tx, ty, inv_present = result
                Logger.info(f"[InputOverlay] move mode=remap from=({round(wx,1)},{round(wy,1)}) "
                           f"to=({round(tx,1)},{round(ty,1)}) inv_present={inv_present}")
        else:
            # Logging-only mode: do not modify touch or target
            Logger.info(f"[InputOverlay] move mode=logging-only passthrough window={round(touch.x,1)},{round(touch.y,1)}")
        return False

    def _on_window_touch_up(self, window, touch):
        if self._remap_enabled:
            result = self._maybe_remap_in_place(touch)
            if result:
                wx, wy, tx, ty, inv_present = result
                Logger.info(f"[InputOverlay] up mode=remap from=({round(wx,1)},{round(wy,1)}) "
                           f"to=({round(tx,1)},{round(ty,1)}) inv_present={inv_present}")
            else:
                Logger.info(f"[InputOverlay] up mode=remap (no inv) window={round(touch.x,1)},{round(touch.y,1)}")
            # Restore target mapping after gesture completes
            self._restore_target_after_dispatch(touch)
        else:
            # Logging-only mode: do not modify touch or target
            Logger.info(f"[InputOverlay] up mode=logging-only passthrough window={round(touch.x,1)},{round(touch.y,1)}")
        return False

    # Ensure we never consume via widget dispatch path
    def on_touch_down(self, touch): return False
    def on_touch_move(self, touch): return False
    def on_touch_up(self, touch): return False