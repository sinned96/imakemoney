"""
portrait_input_overlay.py - Input overlay for matrix portrait pipeline hitbox fix.

This module provides InputOverlayContainer, a transparent full-window overlay that
intercepts touch/mouse events, maps them through an inverse matrix, and dispatches
them to the target widget. This fixes the hitbox misalignment issue in matrix
portrait mode (PORTRAIT_PIPELINE=matrix PORTRAIT_MATRIX_IMPL=rt) without changing
the visual layout.

Key features:
- Full-window transparent overlay (no visual interference)
- Inverse matrix mapping for touch coordinates
- Target widget forwarding (dispatches to underlying rotating_surface)
- Debug logging for diagnostics
- Does not capture keyboard focus

Usage:
    overlay = InputOverlayContainer()
    root.add_widget(overlay)  # Add on top of rotating_surface
    overlay.set_target_widget(rotating_surface)
    overlay.set_inverse_matrix(inverse_matrix)
"""

import logging
from kivy.uix.widget import Widget
from kivy.core.window import Window

# Debug flag - set via DEBUG_ROTATION_OVERLAY env var
DEBUG = False

logger = logging.getLogger(__name__)


class InputOverlayContainer(Widget):
    """
    Transparent full-window input overlay for matrix portrait pipeline.
    
    This widget sits on top of the entire window and intercepts touch events,
    maps them through an inverse matrix, and dispatches them to the target widget.
    This fixes the hitbox misalignment issue without changing visual layout.
    
    The overlay is transparent for rendering (does not draw anything) and does
    not capture keyboard focus. It only handles touch/mouse input mapping.
    
    Architecture:
    - Full-window size (bound to Window.size)
    - Stores inverse matrix for coordinate mapping
    - Stores target widget (the underlying rotating_surface)
    - On touch events: map touch.pos via inverse matrix, dispatch to target widget
    - Preserve original touch.pos by using touch.push()/pop()
    
    Key methods:
    - set_inverse_matrix(matrix): Set the inverse transformation matrix
    - set_target_widget(widget): Set the target widget to forward events to
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Inverse transformation matrix for coordinate mapping
        self._inverse_matrix = None
        
        # Target widget to dispatch events to (typically the rotating_surface)
        self._target_widget = None
        
        # Bind to Window size to keep overlay full-window
        Window.bind(size=self._on_window_resize)
        
        # Set initial size/pos to full window
        self.size = Window.size
        self.pos = (0, 0)
        
        # Disable size_hint to use explicit size
        self.size_hint = (None, None)
        
        logger.info("[InputOverlay] Installed overlay container (full-window, transparent)")
        
        if DEBUG:
            logger.debug(f"[InputOverlay] Initial size: {self.size}, pos: {self.pos}")
    
    def _on_window_resize(self, instance, size):
        """Update overlay size when Window is resized"""
        self.size = size
        self.pos = (0, 0)
        
        if DEBUG:
            logger.debug(f"[InputOverlay] Window resize: updated to {size}")
    
    def set_inverse_matrix(self, matrix):
        """
        Set the inverse transformation matrix for input coordinate mapping.
        
        This matrix is used to map screen coordinates to virtual portrait coordinates.
        When matrix is None, coordinate mapping is disabled (pass-through).
        
        Args:
            matrix: Kivy Matrix object representing the inverse of the portrait transform,
                    or None to disable coordinate mapping.
        """
        self._inverse_matrix = matrix
        
        if matrix:
            logger.info("[InputOverlay] set_inverse_matrix: True")
            if DEBUG:
                logger.debug(f"[InputOverlay] Inverse matrix set: {matrix}")
        else:
            logger.info("[InputOverlay] set_inverse_matrix: None (disabled)")
            if DEBUG:
                logger.debug("[InputOverlay] Inverse matrix cleared")
    
    def set_target_widget(self, widget):
        """
        Set the target widget to forward touch events to.
        
        The target widget is typically the rotating_surface (PortraitContainer or
        PortraitMatrixContainer) that contains the actual UI content.
        
        Args:
            widget: The widget to dispatch touch events to after coordinate mapping.
        """
        self._target_widget = widget
        
        if widget:
            widget_name = widget.__class__.__name__
            logger.info(f"[InputOverlay] set_target_widget: {widget_name}")
            if DEBUG:
                logger.debug(f"[InputOverlay] Target widget set: {widget} ({widget_name})")
        else:
            logger.info("[InputOverlay] set_target_widget: None (disabled)")
            if DEBUG:
                logger.debug("[InputOverlay] Target widget cleared")
    
    def on_touch_down(self, touch):
        """
        Intercept touch_down events, map coordinates, and dispatch to target widget.
        
        This method:
        1. Checks if inverse matrix and target widget are set
        2. If yes: maps touch coordinates via inverse matrix
        3. Dispatches the event to the target widget with mapped coordinates
        4. Restores original touch coordinates
        
        Args:
            touch: Kivy touch object
            
        Returns:
            True if event was dispatched to target widget, False otherwise
        """
        if not self._inverse_matrix or not self._target_widget:
            # No mapping or no target - pass through (should not happen in normal use)
            if DEBUG:
                logger.debug("[InputOverlay] on_touch_down: no matrix or target, pass-through")
            return super().on_touch_down(touch)
        
        # Save original touch position
        touch.push()
        
        # Map touch coordinates via inverse matrix
        orig_x, orig_y = touch.x, touch.y
        tx, ty, _ = self._inverse_matrix.transform_point(touch.x, touch.y, 0)
        touch.x, touch.y = tx, ty
        
        if DEBUG:
            logger.debug(f"[InputOverlay] on_touch_down: ({orig_x:.1f}, {orig_y:.1f}) -> ({tx:.1f}, {ty:.1f})")
        
        # Dispatch to target widget with mapped coordinates
        # Use dispatch() to invoke the target's on_touch_down method directly
        ret = self._target_widget.dispatch('on_touch_down', touch)
        
        # Restore original touch position
        touch.pop()
        
        return ret
    
    def on_touch_move(self, touch):
        """
        Intercept touch_move events, map coordinates, and dispatch to target widget.
        
        This method:
        1. Checks if inverse matrix and target widget are set
        2. If yes: maps touch coordinates via inverse matrix
        3. Dispatches the event to the target widget with mapped coordinates
        4. Restores original touch coordinates
        
        Args:
            touch: Kivy touch object
            
        Returns:
            True if event was dispatched to target widget, False otherwise
        """
        if not self._inverse_matrix or not self._target_widget:
            # No mapping or no target - pass through
            if DEBUG:
                logger.debug("[InputOverlay] on_touch_move: no matrix or target, pass-through")
            return super().on_touch_move(touch)
        
        # Save original touch position
        touch.push()
        
        # Map touch coordinates via inverse matrix
        orig_x, orig_y = touch.x, touch.y
        tx, ty, _ = self._inverse_matrix.transform_point(touch.x, touch.y, 0)
        touch.x, touch.y = tx, ty
        
        if DEBUG:
            logger.debug(f"[InputOverlay] on_touch_move: ({orig_x:.1f}, {orig_y:.1f}) -> ({tx:.1f}, {ty:.1f})")
        
        # Dispatch to target widget
        ret = self._target_widget.dispatch('on_touch_move', touch)
        
        # Restore original touch position
        touch.pop()
        
        return ret
    
    def on_touch_up(self, touch):
        """
        Intercept touch_up events, map coordinates, and dispatch to target widget.
        
        This method:
        1. Checks if inverse matrix and target widget are set
        2. If yes: maps touch coordinates via inverse matrix
        3. Dispatches the event to the target widget with mapped coordinates
        4. Restores original touch coordinates
        
        Args:
            touch: Kivy touch object
            
        Returns:
            True if event was dispatched to target widget, False otherwise
        """
        if not self._inverse_matrix or not self._target_widget:
            # No mapping or no target - pass through
            if DEBUG:
                logger.debug("[InputOverlay] on_touch_up: no matrix or target, pass-through")
            return super().on_touch_up(touch)
        
        # Save original touch position
        touch.push()
        
        # Map touch coordinates via inverse matrix
        orig_x, orig_y = touch.x, touch.y
        tx, ty, _ = self._inverse_matrix.transform_point(touch.x, touch.y, 0)
        touch.x, touch.y = tx, ty
        
        if DEBUG:
            logger.debug(f"[InputOverlay] on_touch_up: ({orig_x:.1f}, {orig_y:.1f}) -> ({tx:.1f}, {ty:.1f})")
        
        # Dispatch to target widget
        ret = self._target_widget.dispatch('on_touch_up', touch)
        
        # Restore original touch position
        touch.pop()
        
        return ret


# Enable debug logging if DEBUG_ROTATION_OVERLAY environment variable is set
import os
if os.getenv("DEBUG_ROTATION_OVERLAY", "0") == "1":
    DEBUG = True
    logger.info("[InputOverlay] Debug logging enabled (DEBUG_ROTATION_OVERLAY=1)")
