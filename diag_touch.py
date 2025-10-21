"""
diag_touch.py - Touch diagnostics and tracing for portrait input debugging.

Provides TouchTraceController for opt-in diagnostics to trace touch event dispatch,
widget focus changes, and visual overlay markers. All features are controlled by
environment flags and have zero impact when disabled.

Environment Flags:
- DIAG_TOUCH_TRACE: Enable touch tracing (default off, set to "1" or "true")
- DIAG_TOUCH_TRACE_OVERLAY: Draw visual markers at touch points (default off)
- DIAG_TOUCH_TRACE_LEVEL: Log level - "debug" or "info" (default "info")

Usage:
    from diag_touch import TouchTraceController
    
    controller = TouchTraceController()
    if controller.enabled():
        path_entries = [...]  # List of (widget, collide, returned_true) tuples
        controller.log_touch_event("down", touch, path_entries, accepted_by_widget)
        controller.mark_point(canvas, (x, y))
"""

import os
import logging
from kivy.logger import Logger
from kivy.graphics import Color, Ellipse, Line

# Get logger for this module
logger = logging.getLogger(__name__)


class TouchTraceController:
    """
    Controller for touch event diagnostics and tracing.
    
    Provides methods to:
    - Check if diagnostics are enabled via environment flags
    - Log touch events with full dispatch path information
    - Draw visual overlay markers at touch coordinates
    - Format widget information for logging
    """
    
    def __init__(self):
        """Initialize the touch trace controller."""
        # Check environment flags
        self._enabled = os.getenv("DIAG_TOUCH_TRACE", "0").lower() in ("1", "true", "yes")
        self._overlay_enabled = os.getenv("DIAG_TOUCH_TRACE_OVERLAY", "0").lower() in ("1", "true", "yes")
        self._log_level = os.getenv("DIAG_TOUCH_TRACE_LEVEL", "info").lower()
        
        # Track if we've logged z-order info yet
        self._z_order_logged = False
        
        # Overlay graphics storage (canvas instruction groups)
        self._overlay_markers = []
        
        if self._enabled:
            Logger.info(f"[diag] TouchTraceController enabled: overlay={self._overlay_enabled} level={self._log_level}")
    
    def enabled(self):
        """
        Check if touch tracing is enabled.
        
        Returns:
            bool: True if DIAG_TOUCH_TRACE is set to "1" or "true"
        """
        return self._enabled
    
    def overlay_enabled(self):
        """
        Check if visual overlay is enabled.
        
        Returns:
            bool: True if DIAG_TOUCH_TRACE_OVERLAY is set to "1" or "true"
        """
        return self._overlay_enabled
    
    def log_touch_event(self, phase, touch, path_entries, accepted_by):
        """
        Log a touch event with full dispatch path information.
        
        Args:
            phase (str): Touch phase - "down", "move", or "up"
            touch: Kivy touch object with pos, sx, sy attributes
            path_entries (list): List of (widget, collide_result, returned_true) tuples
                                representing the dispatch path from root to leaf
            accepted_by: Widget that accepted the event (returned True), or None
        
        Example log output:
            [diag] touch down win=(1138,581) map=(499,1138) accepted_by=LoginScreen.password 
                   path=[Root(collide=True, ret=True), Overlay(collide=True, ret=False), ...]
        """
        if not self._enabled:
            return
        
        # Extract touch coordinates
        win_x, win_y = touch.pos
        # Try to get normalized coordinates (sx, sy are in 0-1 range)
        sx = getattr(touch, 'sx', None)
        sy = getattr(touch, 'sy', None)
        
        # Build coordinates string
        coords_str = f"win=({int(win_x)},{int(win_y)})"
        if sx is not None and sy is not None:
            coords_str += f" norm=({sx:.3f},{sy:.3f})"
        
        # Format accepted_by widget
        if accepted_by:
            accepted_str = self._format_widget(accepted_by)
        else:
            accepted_str = "None"
        
        # Format dispatch path
        path_str = self._format_path(path_entries)
        
        # Build final log message
        log_msg = f"[diag] touch {phase} {coords_str} accepted_by={accepted_str} path={path_str}"
        
        # Log at appropriate level
        if self._log_level == "debug":
            Logger.debug(log_msg)
        else:
            Logger.info(log_msg)
    
    def log_focus_change(self, widget, has_focus):
        """
        Log a focus change event for a widget (e.g., TextInput).
        
        Args:
            widget: The widget that gained/lost focus
            has_focus (bool): True if widget gained focus, False if lost
        
        Example log output:
            [diag] focus LoginScreen.username=True cursor=(5, 5)
        """
        if not self._enabled:
            return
        
        # Format widget information
        widget_str = self._format_widget(widget)
        
        # Try to get cursor position if it's a TextInput
        cursor_str = ""
        if hasattr(widget, 'cursor'):
            cursor = widget.cursor
            cursor_str = f" cursor={cursor}"
        
        # Log the focus change
        log_msg = f"[diag] focus {widget_str}={has_focus}{cursor_str}"
        
        if self._log_level == "debug":
            Logger.debug(log_msg)
        else:
            Logger.info(log_msg)
    
    def log_z_order(self, root_widget):
        """
        Log the z-order and geometry of top-level children.
        
        This helps identify any full-window transparent overlays that might
        be intercepting touch events.
        
        Args:
            root_widget: The root widget whose children to inspect
        """
        if not self._enabled or self._z_order_logged:
            return
        
        self._z_order_logged = True
        
        Logger.info("[diag] Z-order summary (bottom to top):")
        
        if not hasattr(root_widget, 'children'):
            Logger.info("[diag]   (root has no children)")
            return
        
        # Children are in reverse z-order (last added is on top)
        children = list(reversed(root_widget.children))
        
        for i, child in enumerate(children):
            widget_str = self._format_widget(child, include_geometry=True)
            Logger.info(f"[diag]   [{i}] {widget_str}")
    
    def mark_point(self, canvas, pos):
        """
        Draw a small visual marker at the specified position.
        
        This creates a translucent red dot/cross overlay to visually confirm
        where mapped coordinates land.
        
        Args:
            canvas: Kivy canvas to draw on (typically canvas.after)
            pos (tuple): (x, y) coordinates to mark
        """
        if not self._enabled or not self._overlay_enabled:
            return
        
        x, y = pos
        marker_size = 10  # Radius of the marker dot
        
        # Draw a translucent red circle
        with canvas:
            Color(1, 0, 0, 0.6)  # Red with 60% opacity
            ellipse = Ellipse(pos=(x - marker_size/2, y - marker_size/2), 
                            size=(marker_size, marker_size))
            
            # Draw a crosshair
            Color(1, 1, 1, 0.8)  # White with 80% opacity
            cross_size = marker_size * 2
            h_line = Line(points=[x - cross_size/2, y, x + cross_size/2, y], width=1.5)
            v_line = Line(points=[x, y - cross_size/2, x, y + cross_size/2], width=1.5)
            
            # Store references to clean up later if needed
            self._overlay_markers.append((ellipse, h_line, v_line))
    
    def clear_markers(self):
        """Clear all overlay markers."""
        self._overlay_markers.clear()
    
    def _format_widget(self, widget, include_geometry=False):
        """
        Format widget information as a string for logging.
        
        Args:
            widget: The widget to format
            include_geometry (bool): If True, include position and size
        
        Returns:
            str: Formatted widget string like "LoginScreen#my_id" or "Button(100x50@10,20)"
        """
        if widget is None:
            return "None"
        
        # Get class name
        class_name = widget.__class__.__name__
        
        # Get widget ID if available
        widget_id = getattr(widget, 'id', None)
        if widget_id:
            result = f"{class_name}#{widget_id}"
        else:
            result = class_name
        
        # Add geometry if requested
        if include_geometry:
            try:
                w = int(widget.width) if hasattr(widget, 'width') else 0
                h = int(widget.height) if hasattr(widget, 'height') else 0
                x = int(widget.x) if hasattr(widget, 'x') else 0
                y = int(widget.y) if hasattr(widget, 'y') else 0
                result += f"({w}x{h}@{x},{y})"
            except Exception:
                pass
        
        return result
    
    def _format_path(self, path_entries):
        """
        Format the dispatch path as a string.
        
        Args:
            path_entries (list): List of (widget, collide_result, returned_true) tuples
        
        Returns:
            str: Formatted path like "[Root(c=T,r=T), Child(c=T,r=F), ...]"
        """
        if not path_entries:
            return "[]"
        
        formatted = []
        for widget, collide, returned in path_entries:
            widget_str = self._format_widget(widget)
            c_str = "T" if collide else "F"
            r_str = "T" if returned else "F"
            formatted.append(f"{widget_str}(c={c_str},r={r_str})")
        
        return "[" + ", ".join(formatted) + "]"
    
    def get_widget_path(self, widget):
        """
        Get the full widget path from widget to root.
        
        Args:
            widget: The widget to start from
        
        Returns:
            list: List of widgets from widget to root
        """
        path = []
        current = widget
        while current is not None:
            path.append(current)
            current = getattr(current, 'parent', None)
        return path


# Global singleton instance
_controller = None


def get_controller():
    """
    Get the global TouchTraceController singleton.
    
    Returns:
        TouchTraceController: The global controller instance
    """
    global _controller
    if _controller is None:
        _controller = TouchTraceController()
    return _controller
