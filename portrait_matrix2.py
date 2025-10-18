# portrait_matrix2.py
# PortraitMatrixContainer: maps input coordinates through inverse transform and
# stays sized/positioned to Window so mapping matches visible content.
#
# Usage:
# - Import PortraitMatrixContainer and use it as the rotating root for the matrix pipeline.
# - After computing the inverse Matrix in _apply_portrait(), call:
#     self._rotating_surface.set_inverse_matrix(self._inverse_matrix)
#
# This version binds to Window.size/pos so it always covers the whole window and
# avoids the layout/position drift that caused the visible displacement.

from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.logger import Logger
from kivy.core.window import Window


class PortraitMatrixContainer(FloatLayout):
    """
    Container that forwards touches to its children after mapping screen coords
    through a provided inverse matrix (inverse of the transform used for drawing).

    The container auto-fills the Window (size/pos bound) so that mapped coordinates
    align with the visible, transformed UI.
    
    This container wraps a PortraitContainer internally to handle visual transformation,
    while providing enhanced input coordinate mapping through set_inverse_matrix().
    """
    _inverse_matrix = ObjectProperty(None, allownone=True)
    _debug = BooleanProperty(False)

    def __init__(self, **kwargs):
        # Create as full-window widget by default
        super().__init__(**kwargs)
        # Make explicit size/pos (don't rely on size_hint for predictable mapping)
        self.size_hint = (None, None)
        self.pos = (0, 0)
        self.size = Window.size
        
        # Import PortraitContainer here to avoid circular imports
        import main
        self._portrait_container = main.PortraitContainer()
        super().add_widget(self._portrait_container)
        
        # Keep in sync with Window
        Window.bind(size=self._on_window_size, top=self._on_window_pos, left=self._on_window_pos)
        
        Logger.info("[portrait_matrix2]: [PortraitMatrixContainer] Container initialized (enhanced input mapping)")

    def _on_window_size(self, instance, size):
        try:
            self.size = size
            if self._debug:
                Logger.debug(f"[PortraitMatrix] Window size updated -> container.size={self.size}")
        except Exception as e:
            Logger.warning(f"[PortraitMatrix] Error setting container size: {e}")

    def _on_window_pos(self, *args):
        # Most desktops keep Window pos 0,0; keep for completeness
        # If you need to account for non-zero window origin, update pos here.
        try:
            self.pos = (0, 0)
        except Exception as e:
            Logger.warning(f"[PortraitMatrix] Error setting container pos: {e}")

    def set_inverse_matrix(self, matrix):
        """Set the inverse Matrix used to transform incoming screen coordinates
        into virtual (portrait) coordinates. Pass None to disable mapping."""
        self._inverse_matrix = matrix
        Logger.info(f"[portrait_matrix2]: [PortraitMatrix] set_inverse_matrix: {bool(matrix)}")
        if self._debug and matrix:
            Logger.debug(f"[PortraitMatrix] inverse matrix: {matrix}")

    def add_widget(self, widget, *args, **kwargs):
        """Override to add widgets to the wrapped PortraitContainer instead of directly to self"""
        if hasattr(self, '_portrait_container') and widget is not self._portrait_container:
            # Add to the wrapped container
            self._portrait_container.add_widget(widget, *args, **kwargs)
        else:
            # This is the initial add of _portrait_container itself
            super().add_widget(widget, *args, **kwargs)

    def _map_point(self, x, y):
        """Map a window point (x,y) through the inverse matrix.
        Returns (mx, my) or original (x,y) on failure."""
        mat = self._inverse_matrix
        if not mat:
            return x, y
        try:
            tx, ty, tz = mat.transform_point(x, y, 0)
            if self._debug:
                Logger.debug(f"[PortraitMatrix] map_point {x:.1f},{y:.1f} -> {tx:.1f},{ty:.1f}")
            return tx, ty
        except Exception as exc:
            Logger.warning(f"[PortraitMatrix] transform_point failed: {exc}")
            return x, y

    # Touch handlers: temporarily modify touch.pos before forwarding to children,
    # then restore original pos so other handlers (or Window) are unaffected.
    def on_touch_down(self, touch):
        orig_pos = touch.pos
        try:
            mx, my = self._map_point(*orig_pos)
            touch.pos = (mx, my)
            return super().on_touch_down(touch)
        finally:
            try:
                touch.pos = orig_pos
            except Exception:
                pass

    def on_touch_move(self, touch):
        orig_pos = touch.pos
        try:
            mx, my = self._map_point(*orig_pos)
            touch.pos = (mx, my)
            return super().on_touch_move(touch)
        finally:
            try:
                touch.pos = orig_pos
            except Exception:
                pass

    def on_touch_up(self, touch):
        orig_pos = touch.pos
        try:
            mx, my = self._map_point(*orig_pos)
            touch.pos = (mx, my)
            return super().on_touch_up(touch)
        finally:
            try:
                touch.pos = orig_pos
            except Exception:
                pass
