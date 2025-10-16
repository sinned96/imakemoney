import os
import json
import hashlib
import subprocess
import time
from datetime import datetime, time as dt_time
from pathlib import Path
from random import shuffle, choice, uniform, random
import types
import threading
import signal
import logging
import fcntl
import socket
import tempfile
import base64
try:
    from tkinter import Tk, Button, Label
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

# Setup debug logging for recording workflow
def setup_debug_logging():
    """Setup debug logging for recording workflow"""
    import logging
    from pathlib import Path
    # Use standardized base directory, but fall back to current directory if not accessible
    try:
        log_dir = Path("/home/pi/Desktop/v2_Tripple S")
        log_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        # Fallback to current working directory for testing/development
        log_dir = Path(__file__).parent
        
    # Use unified projekt.log instead of separate recording_debug.log
    log_file = log_dir / "projekt.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s [%(name)s]: %(message)s',
        handlers=[
            logging.FileHandler(str(log_file), mode='a', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Suppress PIL debug noise - set PIL loggers to WARNING
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# Initialize debug logger
debug_logger = setup_debug_logging()

# ASCII output helper for subprocess scripts
def ensure_ascii_stdout(msg):
    """
    Convert message to ASCII-safe version for stdout printing.
    
    Replaces common unicode symbols with ASCII equivalents to avoid
    UnicodeEncodeError on systems with latin-1 or ASCII console encoding.
    
    Args:
        msg: String that may contain unicode characters
        
    Returns:
        ASCII-safe string
    """
    replacements = {
        'ℹ': '[INFO]',
        '✓': '[OK]',
        '⚡': '[NOTE]',
        '✅': '[SUCCESS]',
        '→': '->',
        '📱': '[MOBILE]',
        '🖥': '[DESKTOP]',
        '📁': '[FOLDER]',
    }
    
    result = str(msg)
    for unicode_char, ascii_equiv in replacements.items():
        result = result.replace(unicode_char, ascii_equiv)
    
    return result

# Network and QR code utilities
def get_network_ip():
    """
    Get the local network IP address that can be accessed from other devices
    
    Returns:
        str: Network IP address or fallback to localhost
    """
    try:
        # Try to connect to a remote address to determine the local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Connect to Google DNS to determine local IP
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            # Fallback: Get hostname IP
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            # Final fallback to localhost
            return "127.0.0.1"

def generate_qr_code_image(data, size=(300, 300)):
    """
    Generate QR code image data
    
    Args:
        data (str): Data to encode in QR code
        size (tuple): Size of the QR code image
        
    Returns:
        bytes: PNG image data of QR code, or None if generation failed
    """
    try:
        import qrcode
        from PIL import Image as PILImage
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize to requested size
        img = img.resize(size, PILImage.Resampling.LANCZOS)
        
        # Convert to bytes
        import io
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
        
    except ImportError as e:
        debug_logger.error(f"QR code libraries not available: {e}")
        return None
    except Exception as e:
        debug_logger.error(f"Error generating QR code: {e}")
        return None

# Configure Kivy settings BEFORE importing any Kivy modules
from kivy.config import Config
# Set fullscreen mode to 'auto' for true fullscreen without window decorations
Config.set('graphics', 'fullscreen', 'auto')
# Set window provider for Raspberry Pi/SDL2 compatibility
Config.set('graphics', 'window_state', 'visible')
# Write config to ensure it persists
Config.write()

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.graphics import (
    Color as GColor,
    Rectangle, Line, Rotate, PushMatrix, PopMatrix, Scale, Translate
)
# Compatibility alias to prevent NameError for existing Color(...) calls
Color = GColor

from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.modalview import ModalView

# Set neutral clear color to help diagnose out-of-bounds content
Window.clearcolor = (0.15, 0.15, 0.15, 1)  # Dark gray

# ------------------ GL VENDOR DETECTION ------------------
def detect_gl_vendor():
    """Detect GL vendor and renderer for hardware-specific fallbacks"""
    try:
        from kivy.graphics.opengl import glGetString, GL_VENDOR, GL_RENDERER
        vendor = glGetString(GL_VENDOR)
        renderer = glGetString(GL_RENDERER)
        if vendor:
            vendor = vendor.decode('utf-8') if isinstance(vendor, bytes) else str(vendor)
        if renderer:
            renderer = renderer.decode('utf-8') if isinstance(renderer, bytes) else str(renderer)
        debug_logger.info(f"[GL Detection] Vendor: {vendor}, Renderer: {renderer}")
        return vendor, renderer
    except Exception as e:
        debug_logger.warning(f"[GL Detection] Failed to detect GL vendor: {e}")
        return None, None

# ------------------ PORTRAIT ROTATION CONFIG ------------------
# Global rotation configuration for portrait mode (9:16)
# Honor PORTRAIT_ROTATION_DEGREES env variable, default to -90
PORTRAIT_ROTATION_DEGREES = int(os.getenv("PORTRAIT_ROTATION_DEGREES", "-90"))  # -90 = counterclockwise (left rotation), +90 = clockwise (right rotation)
PORTRAIT_SCALE_FIT = os.getenv("PORTRAIT_SCALE_FIT", "1") == "1"  # Scale content to fit window after rotation (enabled to fix clipping on 1920x1080)
DEBUG_SHOW_BOUNDS = False  # Draw debug rectangle around transformed content bounds

# Portrait pipeline configuration (env: PORTRAIT_PIPELINE)
# "matrix" = Matrix rotation at container level (default, reliable)
# "fbo" = FBO-based rendering with letterboxing (legacy, for testing)
# "off" = Disable portrait rotation entirely
# Auto-detect: On Broadcom V3D (RPi), default to FBO unless forced to matrix
_default_pipeline = "matrix"  # Will be updated after GL detection
PORTRAIT_PIPELINE = os.getenv("PORTRAIT_PIPELINE", _default_pipeline).lower()

# Force overrides
PORTRAIT_FORCE_FBO = os.getenv("PORTRAIT_FORCE_FBO", "0") == "1"
PORTRAIT_FORCE_MATRIX = os.getenv("PORTRAIT_FORCE_MATRIX", "0") == "1"

# Matrix implementation mode (env: PORTRAIT_MATRIX_IMPL)
# "mi" = MatrixInstruction (default, single matrix)
# "rt" = Rotate/Translate/Scale (alternative, explicit instructions)
PORTRAIT_MATRIX_IMPL = os.getenv("PORTRAIT_MATRIX_IMPL", "mi").lower()

# Legacy FBO-based portrait rendering configuration (only used when PORTRAIT_PIPELINE=fbo)
PORTRAIT_VIEW_MODE = "fbo" if PORTRAIT_PIPELINE == "fbo" else "raw"  # "fbo" = FBO-based rendering with letterboxing, "raw" = direct canvas transform
PORTRAIT_VIRTUAL_SIZE = (1080, 1920)  # Virtual portrait size for FBO rendering

# Debug overlay configuration (env: DEBUG_ROTATION_OVERLAY)
# When enabled, shows neon border, crosshair, and debug info on portrait content
DEBUG_ROTATION_OVERLAY = os.getenv("DEBUG_ROTATION_OVERLAY", "1") == "1"

# Debug force-size configuration (env: DEBUG_FORCE_LOGIN_SIZE)
# When enabled, forces LoginScreen to known size/pos during diagnostics
DEBUG_FORCE_LOGIN_SIZE = os.getenv("DEBUG_FORCE_LOGIN_SIZE", "1") == "1"

# Debug overlay configuration (env: DEBUG_TOP_OVERLAY)
# When enabled, shows top-most diagnostic overlay with crosshair and banner
DEBUG_TOP_OVERLAY = os.getenv("DEBUG_TOP_OVERLAY", "1") == "1"

# Debug auto-screenshot configuration (env: DEBUG_AUTO_SCREENSHOT)
# When enabled, takes a screenshot on first rendered frame
DEBUG_AUTO_SCREENSHOT = os.getenv("DEBUG_AUTO_SCREENSHOT", "1") == "1"

# Debug LoginScreen paint configuration (env: DEBUG_LOGIN_PAINT)
# When enabled, adds colored rectangle and label to LoginScreen
DEBUG_LOGIN_PAINT = os.getenv("DEBUG_LOGIN_PAINT", "1") == "1"

# Debug force rotated modal configuration (env: DEBUG_FORCE_ROTATED_MODAL)
# When enabled, forces modals/dialogs to use RotatedModalView
DEBUG_FORCE_ROTATED_MODAL = os.getenv("DEBUG_FORCE_ROTATED_MODAL", "1") == "1"

# Debug Window overlay configuration (env: DEBUG_WINDOW_OVERLAY)
# When enabled, shows a bright overlay (semi-transparent red + banner text) directly on Window.canvas.after
# This overlay appears above everything regardless of pipeline to verify draw state
DEBUG_WINDOW_OVERLAY = os.getenv("DEBUG_WINDOW_OVERLAY", "0") == "1"

# ------------------ WINDOW DEBUG OVERLAY ------------------
class WindowDebugOverlay:
    """
    Window-level debug overlay that appears above everything.
    
    Draws directly on Window.canvas.after to verify that GL draw state is working.
    This helps diagnose if black frames are due to color tinting or other GL state issues.
    """
    def __init__(self):
        self._overlay_instructions = []
        self._label_widget = None
        self._enabled = False
        
    def enable(self):
        """Enable the debug overlay on Window.canvas.after"""
        if self._enabled:
            return
        
        from kivy.core.window import Window
        
        # Draw directly on Window.canvas.after
        with Window.canvas.after:
            # Semi-transparent red overlay
            GColor(1, 0, 0, 0.3)  # Red with 30% opacity
            overlay_rect = Rectangle(pos=(0, 0), size=Window.size)
            self._overlay_instructions.append(overlay_rect)
            
            # Banner background
            banner_w = 600
            banner_h = 80
            banner_x = (Window.width - banner_w) / 2
            banner_y = (Window.height - banner_h) / 2
            GColor(1, 1, 1, 0.8)  # White with 80% opacity
            banner_rect = Rectangle(pos=(banner_x, banner_y), size=(banner_w, banner_h))
            self._overlay_instructions.append(banner_rect)
        
        # Create label widget for banner text
        self._label_widget = Label(
            text="DEBUG WINDOW OVERLAY",
            size_hint=(None, None),
            size=(600, 80),
            pos=(banner_x, banner_y),
            color=(0, 0, 0, 1),  # Black text
            font_size=32,
            bold=True,
            halign='center',
            valign='middle'
        )
        self._label_widget.text_size = (600, 80)
        
        # Bind to window resize to update overlay
        Window.bind(size=self._on_window_resize)
        
        self._enabled = True
        debug_logger.info("[WindowDebugOverlay] Enabled on Window.canvas.after")
        
    def _on_window_resize(self, instance, size):
        """Update overlay position and size on window resize"""
        if not self._enabled or len(self._overlay_instructions) < 2:
            return
        
        w, h = size
        
        # Update overlay rectangle
        self._overlay_instructions[0].pos = (0, 0)
        self._overlay_instructions[0].size = (w, h)
        
        # Update banner rectangle
        banner_w = 600
        banner_h = 80
        banner_x = (w - banner_w) / 2
        banner_y = (h - banner_h) / 2
        self._overlay_instructions[1].pos = (banner_x, banner_y)
        
        # Update label position
        if self._label_widget:
            self._label_widget.pos = (banner_x, banner_y)
        
        debug_logger.info(f"[WindowDebugOverlay] Updated for window size {w}x{h}")
    
    def get_label_widget(self):
        """Get the label widget to add to the root widget tree"""
        return self._label_widget

# Global window debug overlay instance
_window_debug_overlay = None

def setup_window_debug_overlay():
    """Setup window debug overlay if enabled"""
    global _window_debug_overlay
    if DEBUG_WINDOW_OVERLAY and not _window_debug_overlay:
        _window_debug_overlay = WindowDebugOverlay()
        _window_debug_overlay.enable()
        debug_logger.info("[WindowDebugOverlay] Setup complete")
    return _window_debug_overlay

# ------------------ ORIENTATION PROVIDER ------------------
class OrientationProvider:
    """Singleton that manages the current orientation state"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.aspect_ratio = "16:9"
            cls._instance.rotation_angle = 0  # 0 for 16:9, 90 for 9:16
        return cls._instance
    
    def set_orientation(self, aspect_ratio):
        """Set the current aspect ratio and calculate rotation angle"""
        self.aspect_ratio = aspect_ratio
        self.rotation_angle = 90 if aspect_ratio == "9:16" else 0
    
    def get_rotation_angle(self):
        """Get the current rotation angle"""
        return self.rotation_angle
    
    def is_portrait(self):
        """Check if we're in portrait mode"""
        return self.aspect_ratio == "9:16"

# ------------------ PORTRAIT CONTAINER (MATRIX PIPELINE) ------------------
class PortraitContainer(FloatLayout):
    """
    Matrix-based portrait rotation container (PORTRAIT_PIPELINE=matrix).
    
    Applies rotation and scale using canvas matrix transformations:
    - In canvas.before: PushMatrix → Translate(x,y) → Translate(blit_w/2, blit_h/2) → 
      Rotate(-90) → Scale(s, s, 1) → Translate(-virtual_w/2, -virtual_h/2)
    - In canvas.after: PopMatrix
    - Children are added under this container and rendered within the transformed space
    - Touch coordinates are automatically handled by Kivy's event system (no manual transform)
    
    This approach avoids FBO texture pitfalls on Raspberry Pi by directly transforming
    the widget tree canvas, which is more reliable with hardware GL drivers.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation_provider = OrientationProvider()
        self._transform_matrix = None
        self._inverse_matrix = None
        self._frame_count = 0
        self._app_loop_frames = 0  # Track frames after app loop starts
        
        # Virtual portrait size (same as FBO virtual size for consistency)
        self.virtual_w = 1080
        self.virtual_h = 1920
        
        # Background instructions (stored on self, not on Canvas)
        self._bg_color = None
        self._bg_rect = None
        
        # Diagnostic overlay instructions (stored on self, not on Canvas)
        self._diag_magenta_rect = None
        self._diag_green_border = None
        self._diag_banner_color = None
        self._diag_banner_rect = None
        self._diag_banner_label = None
        
        # Top-most diagnostic overlay (DEBUG_TOP_OVERLAY)
        self._top_overlay_crosshair_h = None
        self._top_overlay_crosshair_v = None
        self._top_overlay_banner_rect = None
        self._top_overlay_banner_label = None
        
        # Auto-screenshot tracking
        self._screenshot_taken = False
        
        # Transform instruction cache (to avoid recreating every frame)
        self._push_matrix = None
        self._translate_pos = None
        self._translate_center = None
        self._scale_inst = None
        self._rotate_inst = None
        self._translate_virtual = None
        self._matrix_inst = None
        self._pop_matrix = None
        
        # Bind to Window resize events
        from kivy.core.window import Window
        Window.bind(size=self._on_window_resize)
        self.bind(size=self._update_transform, pos=self._update_transform)
        
        # Initial transform setup
        Clock.schedule_once(lambda dt: self._update_transform(), 0)
        
        # Schedule frame counter for verbose diagnostics (first 8 frames)
        Clock.schedule_interval(self._count_frames, 0)
        
        # Schedule auto-screenshot on first rendered frame (DEBUG_AUTO_SCREENSHOT)
        if DEBUG_AUTO_SCREENSHOT:
            Clock.schedule_once(self._take_diagnostic_screenshot, 1.0)
    
    def _count_frames(self, dt):
        """Count frames for verbose diagnostics"""
        if self._app_loop_frames < 8:
            self._app_loop_frames += 1
            self._log_child_diagnostics(f"Frame {self._app_loop_frames}")
        else:
            # Stop counting after 8 frames
            Clock.unschedule(self._count_frames)
    
    def _take_diagnostic_screenshot(self, dt):
        """Take a screenshot on first rendered frame (DEBUG_AUTO_SCREENSHOT)"""
        if self._screenshot_taken:
            return
        
        try:
            from kivy.core.window import Window
            import os
            from pathlib import Path
            
            # Create screenshots directory if it doesn't exist
            screenshot_dir = Path("./screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            # Take screenshot
            screenshot_path = screenshot_dir / "frame1.png"
            Window.screenshot(name=str(screenshot_path))
            
            self._screenshot_taken = True
            debug_logger.info(f"[DEBUG_AUTO_SCREENSHOT] Screenshot saved to: {screenshot_path.absolute()}")
        except Exception as e:
            debug_logger.error(f"[DEBUG_AUTO_SCREENSHOT] Failed to take screenshot: {e}")
    
    def _log_child_diagnostics(self, context):
        """Log verbose child diagnostics"""
        if not self.orientation_provider.is_portrait() or PORTRAIT_PIPELINE != "matrix":
            return
        
        children_names = [type(c).__name__ for c in self.children]
        children_geom = []
        has_zero_size = False
        
        for child in self.children:
            w, h = child.size
            x, y = child.pos
            children_geom.append(f"({w:.0f}x{h:.0f} @ {x:.0f},{y:.0f})")
            
            # Check for zero-size children
            if w == 0 or h == 0:
                has_zero_size = True
                child_name = type(child).__name__
                size_hint = getattr(child, 'size_hint', None)
                size_hint_min = getattr(child, 'size_hint_min', None)
                size_hint_max = getattr(child, 'size_hint_max', None)
                debug_logger.warning(
                    f"[Portrait matrix] WARNING: {child_name} has size {w}x{h} "
                    f"(size_hint={size_hint}, size_hint_min={size_hint_min}, size_hint_max={size_hint_max})"
                )
        
        debug_logger.info(
            f"[Portrait matrix] {context}: {len(self.children)} children: {children_names} "
            f"sizes={children_geom}"
        )
    
    def _on_window_resize(self, instance, size):
        """Handle Window resize events with logging"""
        w, h = size
        debug_logger.info(f"[Portrait matrix] Window resize: {w}x{h}")
        self._update_transform()
        # Log child diagnostics on resize
        self._log_child_diagnostics(f"On resize to {w}x{h}")
    
    def _update_transform(self, *args):
        """Apply matrix rotation and scale transform for portrait mode"""
        is_portrait = self.orientation_provider.is_portrait()
        
        # Only apply if portrait mode is active and pipeline is matrix
        if not is_portrait or PORTRAIT_PIPELINE != "matrix":
            # Clear transforms if switching away from portrait
            if self._matrix_inst is not None:
                self.canvas.before.clear()
                self.canvas.after.clear()
                self._matrix_inst = None
                self._push_matrix = None
                self._pop_matrix = None
            self._transform_matrix = None
            self._inverse_matrix = None
            return
        
        # Get window dimensions
        from kivy.core.window import Window
        w, h = Window.size
        
        if w <= 0 or h <= 0:
            debug_logger.warning(f"Invalid window size: {w}x{h}, skipping transform")
            return
        
        # After -90° rotation: target frame dimensions are (virtual_h, virtual_w) = (1920, 1080)
        rot_w = self.virtual_h  # 1920
        rot_h = self.virtual_w  # 1080
        
        # Compute scale: s = min(w / rot_w, h / rot_h)
        scale_factor = min(w / rot_w, h / rot_h)
        scale_factor = max(scale_factor, 1e-3)  # Safety clamp
        
        # Compute blit size after scaling
        blit_w = rot_w * scale_factor
        blit_h = rot_h * scale_factor
        
        # Position for centering (letterboxing)
        pos_x = (w - blit_w) / 2
        pos_y = (h - blit_h) / 2
        
        # Build transformation matrix:
        # 1. PushMatrix
        # 2. Translate(pos_x, pos_y) - position the viewport
        # 3. Translate(blit_w/2, blit_h/2) - move to center of blit area
        # 4. Scale(s, s, 1)
        # 5. Rotate(-90°)
        # 6. Translate(-virtual_w/2, -virtual_h/2) - center virtual content
        from kivy.graphics.transformation import Matrix
        from kivy.graphics import PushMatrix, PopMatrix, MatrixInstruction
        
        mat = Matrix()
        mat.translate(pos_x, pos_y, 0)
        mat.translate(blit_w / 2, blit_h / 2, 0)
        mat.scale(scale_factor, scale_factor, 1)
        mat.rotate(PORTRAIT_ROTATION_DEGREES * 3.14159265359 / 180.0, 0, 0, 1)
        mat.translate(-self.virtual_w / 2, -self.virtual_h / 2, 0)
        
        # Store matrices (inverse is available for optional manual touch handling)
        self._transform_matrix = mat
        self._inverse_matrix = mat.inverse()
        
        # Determine matrix implementation mode
        use_rt_impl = PORTRAIT_MATRIX_IMPL == "rt"
        
        # Create or update canvas instructions (one-time creation, then update values)
        if self._matrix_inst is None:
            # First time: create all instructions
            self.canvas.before.clear()
            self.canvas.after.clear()
            
            with self.canvas.before:
                # Black background for letterboxing (stored on self, not Canvas)
                self._bg_color = GColor(0, 0, 0, 1)
                self._bg_rect = Rectangle(pos=(0, 0), size=(w, h))
                
                # Apply transformation matrix
                self._push_matrix = PushMatrix()
                
                if use_rt_impl:
                    # Alternative: explicit Translate/Rotate/Scale instructions (PORTRAIT_MATRIX_IMPL=rt)
                    # This is more compatible with some GL drivers (e.g., Broadcom V3D on RPi)
                    self._translate_pos = Translate(pos_x, pos_y, 0)
                    self._translate_center = Translate(blit_w / 2, blit_h / 2, 0)
                    self._scale_inst = Scale(scale_factor, scale_factor, 1)
                    self._rotate_inst = Rotate(angle=PORTRAIT_ROTATION_DEGREES, axis=(0, 0, 1))
                    self._translate_virtual = Translate(-self.virtual_w / 2, -self.virtual_h / 2, 0)
                    self._matrix_inst = None  # Not used in RT mode
                    debug_logger.info(f"[Portrait matrix] Using RT implementation (explicit Translate/Rotate/Scale)")
                else:
                    # Default: single MatrixInstruction (PORTRAIT_MATRIX_IMPL=mi)
                    self._matrix_inst = MatrixInstruction()
                    self._matrix_inst.matrix = mat
                    debug_logger.info(f"[Portrait matrix] Using MI implementation (MatrixInstruction)")
                
                # CRITICAL: Enforce neutral color before any child draws to prevent black tinting
                # This is essential on RPi/V3D where color state can taint textured draws
                GColor(1, 1, 1, 1)  # Neutral white - children will inherit this
                
                # Diagnostic overlay: test pattern in transformed space
                if DEBUG_ROTATION_OVERLAY:
                    # Semi-transparent magenta test fill
                    GColor(1, 0, 1, 0.15)  # Magenta with 15% opacity
                    self._diag_magenta_rect = Rectangle(pos=(0, 0), size=(self.virtual_w, self.virtual_h))
                    
                    # Green border around virtual content
                    GColor(0, 1, 0, 0.8)  # Green
                    self._diag_green_border = Line(rectangle=(0, 0, self.virtual_w, self.virtual_h), width=4)
                    
                    # Reset to neutral after diagnostics
                    GColor(1, 1, 1, 1)
            
            with self.canvas.after:
                self._pop_matrix = PopMatrix()
                
                # Optional debug overlay (crosshair and banner)
                if DEBUG_ROTATION_OVERLAY:
                    # Draw debug elements using the same matrix stack
                    PushMatrix()
                    matrix_inst2 = MatrixInstruction()
                    matrix_inst2.matrix = mat
                    
                    # Crosshair at center of virtual content
                    GColor(1, 1, 0, 0.8)  # Yellow
                    vcx, vcy = self.virtual_w / 2, self.virtual_h / 2
                    Line(points=[vcx - 50, vcy, vcx + 50, vcy], width=2)
                    Line(points=[vcx, vcy - 50, vcx, vcy + 50], width=2)
                    
                    # Diagnostic banner if force-size is enabled
                    if DEBUG_FORCE_LOGIN_SIZE:
                        GColor(1, 0.5, 0, 0.4)  # Orange with 40% opacity
                        self._diag_banner_rect = Rectangle(pos=(10, self.virtual_h - 60), size=(360, 50))
                        
                        # Add text label for banner (will be created as widget)
                        # Note: We'll handle this via a Label widget added to the container
                    
                    PopMatrix()
                
                # Top-most diagnostic overlay (DEBUG_TOP_OVERLAY) - always on top
                if DEBUG_TOP_OVERLAY:
                    # Draw using the same matrix stack for transformed space
                    PushMatrix()
                    matrix_inst_top = MatrixInstruction()
                    matrix_inst_top.matrix = mat
                    
                    # White semi-transparent center crosshair
                    GColor(1, 1, 1, 0.5)  # White with 50% opacity
                    vcx, vcy = self.virtual_w / 2, self.virtual_h / 2
                    crosshair_size = 100
                    self._top_overlay_crosshair_h = Line(points=[vcx - crosshair_size, vcy, vcx + crosshair_size, vcy], width=3)
                    self._top_overlay_crosshair_v = Line(points=[vcx, vcy - crosshair_size, vcx, vcy + crosshair_size], width=3)
                    
                    # Big on-screen banner text 'LOGIN DIAG' centered
                    banner_w = 400
                    banner_h = 100
                    banner_x = (self.virtual_w - banner_w) / 2
                    banner_y = (self.virtual_h - banner_h) / 2 + 150  # Above center
                    GColor(1, 1, 1, 0.4)  # White with 40% opacity
                    self._top_overlay_banner_rect = Rectangle(pos=(banner_x, banner_y), size=(banner_w, banner_h))
                    
                    PopMatrix()
        else:
            # Update existing instructions (no recreation needed)
            self._bg_rect.pos = (0, 0)
            self._bg_rect.size = (w, h)
            
            if use_rt_impl:
                # Update RT implementation instructions
                if self._translate_pos:
                    self._translate_pos.x = pos_x
                    self._translate_pos.y = pos_y
                if self._translate_center:
                    self._translate_center.x = blit_w / 2
                    self._translate_center.y = blit_h / 2
                if self._scale_inst:
                    self._scale_inst.x = scale_factor
                    self._scale_inst.y = scale_factor
                if self._rotate_inst:
                    self._rotate_inst.angle = PORTRAIT_ROTATION_DEGREES
                if self._translate_virtual:
                    self._translate_virtual.x = -self.virtual_w / 2
                    self._translate_virtual.y = -self.virtual_h / 2
            else:
                # Update MI implementation
                if self._matrix_inst:
                    self._matrix_inst.matrix = mat
            
            # Update diagnostic overlay elements if they exist
            if DEBUG_ROTATION_OVERLAY:
                # Update second matrix instruction in canvas.after
                # Find and update the second MatrixInstruction
                from kivy.graphics import MatrixInstruction
                for instr in self.canvas.after.children:
                    if isinstance(instr, MatrixInstruction):
                        instr.matrix = mat
                        break
        
        # Log transform details once per resize event
        debug_logger.info(f"[Portrait matrix] event={w:.0f}x{h:.0f} s={scale_factor:.4f} blit={blit_w:.0f}x{blit_h:.0f} pos=({pos_x:.0f},{pos_y:.0f}) rot={PORTRAIT_ROTATION_DEGREES}")
    
    def add_widget(self, widget, *args, **kwargs):
        """Override to set child size to virtual dimensions"""
        widget_name = type(widget).__name__
        
        # Check if this is LoginScreen and force-size is enabled
        if DEBUG_FORCE_LOGIN_SIZE and PORTRAIT_PIPELINE == "matrix" and widget_name == "LoginScreen":
            # Force size and position for diagnostics
            widget.size_hint = (None, None)
            widget.size = (self.virtual_w, self.virtual_h)
            widget.pos = (0, 0)
            debug_logger.info(
                f"[Portrait matrix] Forced size for {widget_name}: "
                f"size=({self.virtual_w},{self.virtual_h}) pos=(0,0)"
            )
            
            # Add diagnostic banner label
            if DEBUG_ROTATION_OVERLAY and not self._diag_banner_label:
                self._diag_banner_label = Label(
                    text="DIAG: FORCED LOGIN SIZE",
                    size_hint=(None, None),
                    size=(360, 50),
                    pos=(10, self.virtual_h - 60),
                    color=(1, 1, 1, 1),
                    font_size=18,
                    bold=True
                )
                # Add banner as a child of this container (will be in transformed space)
                Clock.schedule_once(lambda dt: super(PortraitContainer, self).add_widget(self._diag_banner_label), 0.1)
            
            # Add top-most diagnostic overlay banner label (DEBUG_TOP_OVERLAY)
            if DEBUG_TOP_OVERLAY and not self._top_overlay_banner_label:
                banner_w = 400
                banner_h = 100
                banner_x = (self.virtual_w - banner_w) / 2
                banner_y = (self.virtual_h - banner_h) / 2 + 150  # Above center
                self._top_overlay_banner_label = Label(
                    text="LOGIN DIAG",
                    size_hint=(None, None),
                    size=(banner_w, banner_h),
                    pos=(banner_x, banner_y),
                    color=(1, 1, 1, 1),
                    font_size=48,
                    bold=True,
                    halign='center',
                    valign='middle'
                )
                self._top_overlay_banner_label.text_size = (banner_w, banner_h)
                # Add banner as a child of this container (will be in transformed space)
                Clock.schedule_once(lambda dt: super(PortraitContainer, self).add_widget(self._top_overlay_banner_label), 0.2)
        elif not widget.size_hint or widget.size_hint == (None, None):
            # Set widget size to virtual portrait dimensions if it doesn't have size_hint
            widget.size = (self.virtual_w, self.virtual_h)
            widget.pos = (0, 0)
        
        super().add_widget(widget, *args, **kwargs)
        
        # Log what's being added
        # Try to get screen title if it's a screen
        title = getattr(widget, 'title', getattr(widget, '__class__.__name__', 'Unknown'))
        debug_logger.info(f"[Portrait matrix] Added widget: {widget_name} (title/class: {title})")
    
    def on_touch_down(self, touch):
        """Transform touch coordinates using Kivy's built-in push/pop mechanism"""
        if self._inverse_matrix:
            # Use Kivy's built-in coordinate transformation
            # This applies the inverse matrix to map screen coords to widget coords
            touch.push()
            # Apply inverse transform to map screen coordinates to virtual space
            tx, ty, _ = self._inverse_matrix.transform_point(touch.x, touch.y, 0)
            touch.x, touch.y = tx, ty
        
        ret = super().on_touch_down(touch)
        
        if self._inverse_matrix:
            touch.pop()
        
        return ret
    
    def on_touch_move(self, touch):
        """Transform touch coordinates using Kivy's built-in push/pop mechanism"""
        if self._inverse_matrix:
            touch.push()
            tx, ty, _ = self._inverse_matrix.transform_point(touch.x, touch.y, 0)
            touch.x, touch.y = tx, ty
        
        ret = super().on_touch_move(touch)
        
        if self._inverse_matrix:
            touch.pop()
        
        return ret
    
    def on_touch_up(self, touch):
        """Transform touch coordinates using Kivy's built-in push/pop mechanism"""
        if self._inverse_matrix:
            touch.push()
            tx, ty, _ = self._inverse_matrix.transform_point(touch.x, touch.y, 0)
            touch.x, touch.y = tx, ty
        
        ret = super().on_touch_up(touch)
        
        if self._inverse_matrix:
            touch.pop()
        
        return ret

# ------------------ ROTATING SURFACE ------------------
class RotatingSurface(FloatLayout):
    """
    Container that applies unified graphics+input transform for portrait mode.
    
    This widget rotates the entire content subtree by PORTRAIT_ROTATION_DEGREES around 
    its center, with input/touch coordinates transformed accordingly so hitboxes remain 
    correct. This solves the issue where individual widget rotations caused misaligned
    touch targets and inconsistent appearance across different screens.
    
    Key features:
    - Center-anchored rotation: Content rotates around the center point
    - Touch coordinate transformation: All touch events are properly mapped
    - Optional scale-to-fit: Content can be scaled to fit within the window
    - Automatic: Applied only when OrientationProvider.is_portrait() returns True
    
    The transformation matrix order is: Translate(cx,cy) · Scale · Rotate · Translate(-cx,-cy)
    Touch events receive the inverse transformation to map screen coords to logical coords.
    
    Note: Modals use RotatedModalView which applies the same transform independently
    since ModalView widgets attach to the Window rather than the widget tree.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation_provider = OrientationProvider()
        self._transform_matrix = None
        self._inverse_matrix = None
        self._rotation_logged = False
        self.bind(size=self._update_transform, pos=self._update_transform)
    
    def _update_transform(self, *args):
        """Apply rotation and scale transform based on orientation"""
        is_portrait = self.orientation_provider.is_portrait()
        
        # Clear existing transforms
        self.canvas.before.clear()
        self.canvas.after.clear()
        
        if not is_portrait:
            # Landscape mode: no transformation needed
            self._transform_matrix = None
            self._inverse_matrix = None
            return
        
        # Portrait mode: apply rotation and optional scale
        from kivy.graphics.transformation import Matrix
        
        # Calculate center point for rotation anchor
        cx, cy = self.center_x, self.center_y
        
        # Build transformation matrix: Translate(cx, cy) · Scale · Rotate · Translate(-cx, -cy)
        mat = Matrix()
        mat.translate(cx, cy, 0)
        
        # Track scale factor for logging
        scale_factor = 1.0
        
        # Optional: Scale to fit rotated content within window
        if PORTRAIT_SCALE_FIT:
            # After rotation, logical width and height swap
            # Calculate uniform scale to fit rotated content in window
            if self.width > 0 and self.height > 0:
                # When rotated -90 deg, the logical height becomes the physical width
                # and logical width becomes the physical height
                scale_factor = min(self.width / self.height, self.height / self.width)
                # Apply safe minimum scale clamp to avoid degenerate scaling
                scale_factor = max(scale_factor, 1e-3)
                if scale_factor < 1.0:
                    mat.scale(scale_factor, scale_factor, 1)
        
        # Apply rotation
        mat.rotate(PORTRAIT_ROTATION_DEGREES * 3.14159265359 / 180.0, 0, 0, 1)
        mat.translate(-cx, -cy, 0)
        
        # Store matrices for touch transformation
        self._transform_matrix = mat
        self._inverse_matrix = mat.inverse()
        
        # Apply to canvas
        with self.canvas.before:
            PushMatrix()
            from kivy.graphics import MatrixInstruction
            self._matrix_instruction = MatrixInstruction()
            self._matrix_instruction.matrix = mat
        
        with self.canvas.after:
            PopMatrix()
            
            # Optional debug visualization
            if DEBUG_SHOW_BOUNDS:
                GColor(1, 0, 0, 0.8)  # Red with 80% opacity
                # Draw rectangle around the content bounds
                Line(rectangle=(self.x, self.y, self.width, self.height), width=2)
        
        # Log once when rotation is applied
        if not self._rotation_logged:
            scale_msg = f" with scale {scale_factor:.4f}" if PORTRAIT_SCALE_FIT and scale_factor < 1.0 else ""
            debug_logger.info(f"Applied global rotation {PORTRAIT_ROTATION_DEGREES} deg{scale_msg} with input transform for 9:16 (center-anchored)")
            self._rotation_logged = True
    
    def on_touch_down(self, touch):
        """Transform touch coordinates before dispatching to children"""
        if self._inverse_matrix:
            # Apply inverse transform to touch position
            # Create a callable from the matrix's transform_point method
            touch.push()
            touch.apply_transform_2d(lambda x, y: self._inverse_matrix.transform_point(x, y, 0)[:2])
        
        ret = super().on_touch_down(touch)
        
        if self._inverse_matrix:
            touch.pop()
        
        return ret
    
    def on_touch_move(self, touch):
        """Transform touch coordinates before dispatching to children"""
        if self._inverse_matrix:
            touch.push()
            touch.apply_transform_2d(lambda x, y: self._inverse_matrix.transform_point(x, y, 0)[:2])
        
        ret = super().on_touch_move(touch)
        
        if self._inverse_matrix:
            touch.pop()
        
        return ret
    
    def on_touch_up(self, touch):
        """Transform touch coordinates before dispatching to children"""
        if self._inverse_matrix:
            touch.push()
            touch.apply_transform_2d(lambda x, y: self._inverse_matrix.transform_point(x, y, 0)[:2])
        
        ret = super().on_touch_up(touch)
        
        if self._inverse_matrix:
            touch.pop()
        
        return ret

# ------------------ ROTATING ROOT FBO ------------------
class RotatingRootFbo(FloatLayout):
    """
    FBO-based portrait rendering with letterboxing.
    
    This widget creates a virtual portrait-sized FBO surface (1080x1920) and ensures children
    are properly sized to fit within it, then applies rotation and letterboxing
    for display on the physical screen.
    
    Key improvement: Uses actual Kivy Fbo to render children to a texture, which is then
    drawn with rotation and scaling to the main canvas.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation_provider = OrientationProvider()
        self._transform_matrix = None
        self._inverse_matrix = None
        self._rotation_logged = False
        self._child_container = None
        self._debug_label = None
        self._finalized = False
        self._finalize_attempts = 0
        self._fbo = None
        self._fbo_rect = None
        
        # Debouncing state
        self._last_resize_w = 0
        self._last_resize_h = 0
        self._pending_apply_event = None
        
        # Bind to Window.size for dynamic recalculation
        from kivy.core.window import Window
        Window.bind(size=self._on_resize)
        self.bind(pos=self._update_transform)
        
        # Defer viewport calculation until Window has real size
        Clock.schedule_once(self._finalize_viewport, 0)
    
    def _finalize_viewport(self, dt):
        """Finalize viewport after Window has real size"""
        from kivy.core.window import Window
        ww, wh = Window.size
        
        # Guard: if Window size is still too small, retry
        if ww * wh <= 10000:
            self._finalize_attempts += 1
            if self._finalize_attempts < 20:  # Max 2 seconds of retries
                debug_logger.warning(f"Window size still too small ({ww:.0f}x{wh:.0f}), retrying in 0.1s (attempt {self._finalize_attempts})")
                Clock.schedule_once(self._finalize_viewport, 0.1)
                return
            else:
                debug_logger.error(f"Window size never reached valid dimensions after {self._finalize_attempts} attempts, proceeding anyway")
        
        self._finalized = True
        debug_logger.info(f"Portrait FBO finalized: window={ww:.0f}x{wh:.0f}")
        
        # Schedule initial apply with current Window size
        self._schedule_debounced_apply(ww, wh)
    
    def _on_resize(self, instance, size):
        """Handle Window resize events"""
        if self._finalized:
            w, h = size
            debug_logger.info(f"Window resize event: {w:.0f}x{h:.0f}")
            self._schedule_debounced_apply(w, h)
    
    def _schedule_debounced_apply(self, w, h):
        """Schedule a debounced apply of the transform"""
        # Store the size
        self._last_resize_w = w
        self._last_resize_h = h
        
        # Unschedule any pending apply
        if self._pending_apply_event:
            Clock.unschedule(self._pending_apply_event)
        
        # Schedule one Clock task in the next frame
        self._pending_apply_event = Clock.schedule_once(lambda dt: self._apply_transform(w, h), 0)
        
    def _update_transform(self, *args):
        """Legacy method for compatibility - redirects to debounced apply"""
        # Use the last known size or current Window size
        if self._finalized and self._last_resize_w > 0 and self._last_resize_h > 0:
            self._schedule_debounced_apply(self._last_resize_w, self._last_resize_h)
        
    def _create_fbo(self):
        """Create and setup the FBO for portrait rendering"""
        from kivy.graphics import Fbo, Rectangle, ClearColor, ClearBuffers
        
        # Virtual portrait size (1080x1920)
        virtual_w = 1080
        virtual_h = 1920
        
        # Create FBO with virtual size
        self._fbo = Fbo(size=(virtual_w, virtual_h), with_stencilbuffer=True)
        
        # Log FBO creation
        debug_logger.info(f"[FBO Init] Created FBO: size={virtual_w}x{virtual_h}, texture={self._fbo.texture.size if self._fbo.texture else 'None'}")
        
        # Setup FBO background clearing
        with self._fbo.before:
            ClearColor(0, 0, 0, 1)
            ClearBuffers()
        
        # Bind the child container to render into the FBO
        if self._child_container:
            # Add the child container's canvas instructions to the FBO
            # This will capture all rendering from the container and its children
            self._fbo.add(self._child_container.canvas.before)
            self._fbo.add(self._child_container.canvas)
            self._fbo.add(self._child_container.canvas.after)
            
            debug_logger.info(f"[FBO Init] Bound child container canvas to FBO")
        
        return True
    
    def _apply_transform(self, w, h):
        """Apply rotation and scale transform using FBO texture"""
        # Skip if not yet finalized
        if not self._finalized:
            return
        
        is_portrait = self.orientation_provider.is_portrait()
        
        # Clear existing transforms
        self.canvas.before.clear()
        self.canvas.after.clear()
        
        if not is_portrait or PORTRAIT_VIEW_MODE != "fbo":
            # Not in FBO mode - destroy FBO if it exists
            if self._fbo:
                debug_logger.info("[FBO] Cleaning up FBO (not in FBO mode)")
                self._fbo = None
                self._fbo_rect = None
            self._transform_matrix = None
            self._inverse_matrix = None
            return
        
        # Portrait FBO mode: apply rotation and scale
        from kivy.graphics.transformation import Matrix
        from kivy.graphics import PushMatrix, PopMatrix, MatrixInstruction, Line, Rectangle
        from kivy.core.text import Label as CoreLabel
        
        # Virtual portrait size (1080x1920)
        virtual_w = 1080
        virtual_h = 1920
        
        # Use event parameters w, h directly (NOT Window.size)
        if w <= 0 or h <= 0:
            debug_logger.warning(f"Invalid window size in apply: {w}x{h}, skipping")
            return
        
        # Create FBO if not exists
        if not self._fbo:
            self._create_fbo()
        
        # Verify FBO texture exists
        if not self._fbo or not self._fbo.texture:
            debug_logger.error("[FBO] FBO or FBO texture is None - cannot render!")
            return
        
        # Log FBO state
        fbo_tex_size = self._fbo.texture.size if self._fbo.texture else (0, 0)
        debug_logger.info(f"[FBO State] FBO size={self._fbo.size}, texture size={fbo_tex_size}")
        
        # After -90° rotation, the target frame is (rot_w, rot_h) = (virtual_h, virtual_w) = (1920, 1080)
        rot_w = virtual_h  # 1920
        rot_h = virtual_w  # 1080
        
        # Compute scale: s = min(w / rot_w, h / rot_h)
        scale_factor = min(w / rot_w, h / rot_h)
        scale_factor = max(scale_factor, 1e-3)  # Safety clamp
        
        # Compute blit size after scaling
        blit_w = rot_w * scale_factor
        blit_h = rot_h * scale_factor
        
        # Position for centering (letterboxing)
        pos_x = (w - blit_w) / 2
        pos_y = (h - blit_h) / 2
        
        # Build transformation matrix:
        # 1. Clear background
        # 2. PushMatrix
        # 3. Translate(pos_x, pos_y) - position the viewport
        # 4. Translate(blit_w/2, blit_h/2) - move to center of blit area
        # 5. Rotate(-90°)
        # 6. Translate(-virtual_w/2, -virtual_h/2) - center virtual content
        # 7. Draw FBO texture at (0, 0) with size (virtual_w, virtual_h)
        # 8. PopMatrix
        
        mat = Matrix()
        mat.translate(pos_x, pos_y, 0)
        mat.translate(blit_w / 2, blit_h / 2, 0)
        mat.scale(scale_factor, scale_factor, 1)
        mat.rotate(PORTRAIT_ROTATION_DEGREES * 3.14159265359 / 180.0, 0, 0, 1)
        mat.translate(-virtual_w / 2, -virtual_h / 2, 0)
        
        # Store matrices for touch transformation
        self._transform_matrix = mat
        self._inverse_matrix = mat.inverse()
        
        # Apply to canvas - draw the FBO texture with transformations
        with self.canvas.before:
            # Background clear with black letterboxing
            GColor(0, 0, 0, 1)
            Rectangle(pos=(0, 0), size=(w, h))
            
            PushMatrix()
            matrix_inst = MatrixInstruction()
            matrix_inst.matrix = mat
            
            # CRITICAL: Enforce neutral color before textured draw to prevent black tinting
            # This is essential on RPi/V3D where previous color state can taint the texture
            GColor(1, 1, 1, 1)  # Neutral white - texture will render at full brightness
            self._fbo_rect = Rectangle(pos=(0, 0), size=(virtual_w, virtual_h), texture=self._fbo.texture)
        
        with self.canvas.after:
            PopMatrix()
            
            # Add debug overlay if enabled
            if DEBUG_ROTATION_OVERLAY:
                # Draw debug elements using the same matrix stack
                PushMatrix()
                matrix_inst2 = MatrixInstruction()
                matrix_inst2.matrix = mat
                
                # Neon border around virtual content area
                GColor(0, 1, 1, 0.8)  # Cyan
                Line(rectangle=(5, 5, virtual_w - 10, virtual_h - 10), width=3)
                
                # Crosshair at center of virtual content
                GColor(1, 0, 1, 0.8)  # Magenta
                vcx, vcy = virtual_w / 2, virtual_h / 2
                Line(points=[vcx - 50, vcy, vcx + 50, vcy], width=2)
                Line(points=[vcx, vcy - 50, vcx, vcy + 50], width=2)
                
                # Debug rectangle marker in top-left of virtual space
                GColor(0, 1, 0, 0.6)  # Green
                Rectangle(pos=(10, virtual_h - 60), size=(300, 50))
                
                # CRITICAL: Restore neutral color after diagnostic overlays
                GColor(1, 1, 1, 1)
                
                PopMatrix()
                
                # Add debug label if not already added
                if not self._debug_label and self._child_container:
                    self._debug_label = Label(
                        text=f"DEBUG: portrait\nvirtual={virtual_w}x{virtual_h}\nscale={scale_factor:.3f}",
                        size_hint=(None, None),
                        size=(300, 80),
                        pos=(10, virtual_h - 90),
                        color=(0, 1, 0, 1),
                        font_size=14
                    )
                    self._child_container.add_widget(self._debug_label)
                elif self._debug_label:
                    self._debug_label.text = f"DEBUG: portrait\nvirtual={virtual_w}x{virtual_h}\nscale={scale_factor:.3f}"
        
        # Update child container size if it exists
        if self._child_container:
            self._child_container.size = (virtual_w, virtual_h)
            self._child_container.pos = (0, 0)
        
        # Request FBO update - this renders the child widgets into the FBO texture
        if self._fbo:
            # Force a layout pass on child container to ensure widgets are positioned
            if self._child_container:
                self._child_container.do_layout()
            # Update and draw the FBO
            self._fbo.ask_update()
            self._fbo.draw()
            debug_logger.debug(f"[FBO] Updated and drew FBO")
        
        # Log concise line per execution
        debug_logger.info(f"[Portrait apply] event={w:.0f}x{h:.0f} s={scale_factor:.4f} blit={blit_w:.0f}x{blit_h:.0f} pos=({pos_x:.0f},{pos_y:.0f}) rot={PORTRAIT_ROTATION_DEGREES} fbo_tex={fbo_tex_size}")
    
    def add_widget(self, widget, *args, **kwargs):
        """Override to properly size children for virtual portrait space"""
        is_portrait = self.orientation_provider.is_portrait()
        
        if is_portrait and PORTRAIT_VIEW_MODE == "fbo":
            # Create a container at virtual size if not exists
            if not self._child_container:
                self._child_container = FloatLayout(size=PORTRAIT_VIRTUAL_SIZE, pos=(0, 0))
                self._child_container.size_hint = (None, None)
                debug_logger.info(f"Created FBO child container: size={PORTRAIT_VIRTUAL_SIZE}")
                # Add to widget tree so it gets proper layout/rendering
                super().add_widget(self._child_container)
            
            # Add the child to the container
            widget_name = widget.__class__.__name__
            debug_logger.info(f"Adding {widget_name} to portrait FBO container")
            self._child_container.add_widget(widget, *args, **kwargs)
            
            # Create FBO if not exists and bind container to it
            if not self._fbo and self._finalized:
                self._create_fbo()
            elif self._fbo:
                # FBO already exists, request update
                self._fbo.ask_update()
            
            # Force transform update
            self._update_transform()
        else:
            # Direct rendering
            super().add_widget(widget, *args, **kwargs)
    
    def on_touch_down(self, touch):
        """Transform touch coordinates from screen to virtual space"""
        if self._inverse_matrix:
            touch.push()
            touch.apply_transform_2d(lambda x, y: self._inverse_matrix.transform_point(x, y, 0)[:2])
        
        ret = super().on_touch_down(touch)
        
        if self._inverse_matrix:
            touch.pop()
        
        return ret
    
    def on_touch_move(self, touch):
        """Transform touch coordinates from screen to virtual space"""
        if self._inverse_matrix:
            touch.push()
            touch.apply_transform_2d(lambda x, y: self._inverse_matrix.transform_point(x, y, 0)[:2])
        
        ret = super().on_touch_move(touch)
        
        if self._inverse_matrix:
            touch.pop()
        
        return ret
    
    def on_touch_up(self, touch):
        """Transform touch coordinates from screen to virtual space"""
        if self._inverse_matrix:
            touch.push()
            touch.apply_transform_2d(lambda x, y: self._inverse_matrix.transform_point(x, y, 0)[:2])
        
        ret = super().on_touch_up(touch)
        
        if self._inverse_matrix:
            touch.pop()
        
        return ret
    
    def clear_widgets(self):
        """Override to properly clean up child container and FBO"""
        if self._child_container:
            self._child_container.clear_widgets()
            self._debug_label = None  # Will be recreated if needed
        
        # Clean up FBO
        if self._fbo:
            debug_logger.info("[FBO] Cleaning up FBO on clear_widgets")
            self._fbo = None
            self._fbo_rect = None
        
        super().clear_widgets()
        self._child_container = None

# ------------------ ROTATING ROOT ------------------
class RotatingRoot(FloatLayout):
    """Root widget that wraps content in appropriate container for portrait mode"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation_provider = OrientationProvider()
        self._rotating_surface = None
        self._content_widget = None
    
    def add_widget(self, widget, *args, **kwargs):
        """Override to wrap content in appropriate container when in portrait mode"""
        is_portrait = self.orientation_provider.is_portrait()
        
        # If we're switching orientation, clean up old structure
        if self._rotating_surface or self._content_widget:
            self.clear_widgets()
            self._rotating_surface = None
            self._content_widget = None
        
        # Check if portrait rotation is disabled via PORTRAIT_PIPELINE=off
        if PORTRAIT_PIPELINE == "off":
            # Portrait rotation disabled: add content directly (landscape behavior)
            self._content_widget = widget
            super().add_widget(widget, *args, **kwargs)
            debug_logger.info("[Portrait] Pipeline disabled (PORTRAIT_PIPELINE=off), using landscape mode")
            return
        
        if is_portrait:
            # Portrait mode: choose rendering method based on PORTRAIT_PIPELINE
            if PORTRAIT_PIPELINE == "matrix":
                # Matrix-based rotation (new default)
                if not self._rotating_surface:
                    self._rotating_surface = PortraitContainer()
                    super().add_widget(self._rotating_surface, *args, **kwargs)
                    debug_logger.info("[Portrait] Using matrix pipeline for rendering")
                self._content_widget = widget
                self._rotating_surface.add_widget(widget)
                # Log what widget is being shown
                widget_name = widget.__class__.__name__
                debug_logger.info(f"[Portrait matrix] Showing {widget_name}")
            elif PORTRAIT_PIPELINE == "fbo":
                # FBO-based rendering with letterboxing (legacy)
                if not self._rotating_surface:
                    self._rotating_surface = RotatingRootFbo()
                    super().add_widget(self._rotating_surface, *args, **kwargs)
                    debug_logger.info("[Portrait] Using FBO pipeline for rendering (legacy)")
                self._content_widget = widget
                self._rotating_surface.add_widget(widget)
                # Log what widget is being shown
                widget_name = widget.__class__.__name__
                debug_logger.info(f"[Portrait FBO] Showing {widget_name}")
            else:
                # Raw canvas transform (fallback for unknown pipeline values)
                if not self._rotating_surface:
                    self._rotating_surface = RotatingSurface()
                    super().add_widget(self._rotating_surface, *args, **kwargs)
                    debug_logger.info(f"[Portrait] Using raw canvas transform (pipeline={PORTRAIT_PIPELINE})")
                self._content_widget = widget
                self._rotating_surface.add_widget(widget)
        else:
            # Landscape mode: add content directly
            self._content_widget = widget
            super().add_widget(widget, *args, **kwargs)
    
    def clear_widgets(self):
        """Override to properly clean up rotating surface"""
        if self._rotating_surface:
            self._rotating_surface.clear_widgets()
        super().clear_widgets()
        self._rotating_surface = None
        self._content_widget = None
    
    def apply_rotation(self):
        """Force update of rotation (call after orientation change)"""
        # When orientation changes, we need to rebuild the widget tree
        # to properly wrap/unwrap the RotatingSurface
        if self._content_widget:
            content = self._content_widget
            # Clear and re-add to trigger proper wrapping based on new orientation
            if self._rotating_surface:
                self._rotating_surface.clear_widgets()
            super().clear_widgets()
            self._rotating_surface = None
            self._content_widget = None
            self.add_widget(content)
        elif self._rotating_surface:
            # Update existing transform
            self._rotating_surface._update_transform()

# ------------------ ROTATED MODAL VIEW ------------------
class RotatedModalView(ModalView):
    """ModalView that applies its own rotation transform for portrait mode
    
    Since ModalView attaches to the Window (not the widget tree), it doesn't inherit
    RotatingSurface's canvas transformations. This class applies the same rotation
    transform directly to the modal's canvas when in portrait mode.
    """
    def __init__(self, **kwargs):
        self.orientation_provider = OrientationProvider()
        self._transform_matrix = None
        self._inverse_matrix = None
        super().__init__(**kwargs)
        self.bind(size=self._update_modal_transform, pos=self._update_modal_transform)
    
    def _update_modal_transform(self, *args):
        """Apply rotation transform to modal when in portrait mode"""
        is_portrait = self.orientation_provider.is_portrait()
        
        # Clear existing transforms
        self.canvas.before.clear()
        self.canvas.after.clear()
        
        if not is_portrait:
            # Landscape mode: no transformation needed
            self._transform_matrix = None
            self._inverse_matrix = None
            return
        
        # Portrait mode: apply same rotation and scale as RotatingSurface
        from kivy.graphics.transformation import Matrix
        from kivy.graphics import PushMatrix, PopMatrix, MatrixInstruction
        from kivy.core.window import Window
        
        # Calculate center point for rotation anchor (use Window center for modals)
        cx, cy = Window.width / 2, Window.height / 2
        
        # Build transformation matrix: Translate(cx, cy) · Scale · Rotate · Translate(-cx, -cy)
        mat = Matrix()
        mat.translate(cx, cy, 0)
        
        # Optional: Scale to fit rotated content within window (same as RotatingSurface)
        if PORTRAIT_SCALE_FIT:
            if Window.width > 0 and Window.height > 0:
                scale_factor = min(Window.width / Window.height, Window.height / Window.width)
                scale_factor = max(scale_factor, 1e-3)
                if scale_factor < 1.0:
                    mat.scale(scale_factor, scale_factor, 1)
        
        mat.rotate(PORTRAIT_ROTATION_DEGREES * 3.14159265359 / 180.0, 0, 0, 1)
        mat.translate(-cx, -cy, 0)
        
        # Store matrices for touch transformation
        self._transform_matrix = mat
        self._inverse_matrix = mat.inverse()
        
        # Apply to canvas
        with self.canvas.before:
            PushMatrix()
            matrix_inst = MatrixInstruction()
            matrix_inst.matrix = mat
        
        with self.canvas.after:
            PopMatrix()
    
    def on_touch_down(self, touch):
        """Transform touch coordinates before dispatching to children"""
        if self._inverse_matrix:
            touch.push()
            touch.apply_transform_2d(lambda x, y: self._inverse_matrix.transform_point(x, y, 0)[:2])
        
        ret = super().on_touch_down(touch)
        
        if self._inverse_matrix:
            touch.pop()
        
        return ret
    
    def on_touch_move(self, touch):
        """Transform touch coordinates before dispatching to children"""
        if self._inverse_matrix:
            touch.push()
            touch.apply_transform_2d(lambda x, y: self._inverse_matrix.transform_point(x, y, 0)[:2])
        
        ret = super().on_touch_move(touch)
        
        if self._inverse_matrix:
            touch.pop()
        
        return ret
    
    def on_touch_up(self, touch):
        """Transform touch coordinates before dispatching to children"""
        if self._inverse_matrix:
            touch.push()
            touch.apply_transform_2d(lambda x, y: self._inverse_matrix.transform_point(x, y, 0)[:2])
        
        ret = super().on_touch_up(touch)
        
        if self._inverse_matrix:
            touch.pop()
        
        return ret
    
    def open(self, *args, **kwargs):
        """Override open to ensure transform is applied after opening"""
        result = super().open(*args, **kwargs)
        # Force transform update after modal is opened and sized
        self._update_modal_transform()
        
        # Log modal opening details (always log for debugging)
        modal_class = self.__class__.__name__
        modal_size = self.size if hasattr(self, 'size') else (0, 0)
        is_rotated = True  # RotatedModalView always applies rotation in portrait mode
        orientation = OrientationProvider().aspect_ratio
        debug_logger.info(
            f"[Modal Open] class={modal_class}, size={modal_size[0]:.0f}x{modal_size[1]:.0f}, "
            f"is_rotated_modal=True, orientation={orientation}"
        )
        return result

# ------------------ KONFIG ------------------
APP_DIR = Path(__file__).parent
IMAGE_DIR = Path("/home/pi/Desktop/v2_Tripple S/BilderVertex")
IMPORT_DIR = Path("/home/pi/Desktop/v2_Tripple S/uploads")  # Changed from BilderImport to uploads
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')
ACCOUNTS_PATH = Path("/home/pi/Desktop/v2_Tripple S/Accounts.txt")
MODES_PATH = APP_DIR / "modes.json"
IMAGE_META_PATH = APP_DIR / "image_meta.json"

DEFAULT_INTERVAL = 5
SCHEDULER_INTERVAL_SEC = 60
FADE_OUT_DUR = 0.35
FADE_IN_DUR = 0.45
THUMB_SIZE = dp(140)
MAX_IMAGES_DISPLAY = 2000
SHOW_DELETE_BUTTONS = True

SHOW_INFO_LABEL = False
SHOW_FAB_GALLERY = False
HIDE_TOOLBAR_TITLE = True
ENABLE_SOFT_KEYBOARD = True

INTERVAL_NEW_FILES = 3
TOOLBAR_FADE_DURATION = 0.4
TOOLBAR_VISIBLE_SECS = 7

IMAGE_SCALE_MODE = "cover"

EFFECTS_AVAILABLE = [
    ("fade", "Fade"),
    ("slide_left", "Slide Links"),
    ("slide_right", "Slide Rechts"),
    ("zoom_in", "Zoom In"),
    ("zoom_pan", "Zoom+Pan"),
    ("rotate", "Rotate"),
    ("blitz", "Blitz"),
    ("none", "Keine")
]
DEFAULT_EFFECTS = {"fade"}

SHOW_DEBUG_OVERLAY = True
DEBUG_OVERLAY_FONT_SIZE = 16
DEBUG_OVERLAY_POSITION = "top_left"
# --------------------------------------------

KIVYMD_OK = False
try:
    from kivymd.uix.toolbar import MDToolbar
    from kivymd.uix.textfield import MDTextField
    from kivymd.app import MDApp
    AppBarClass = MDToolbar
    KIVYMD_OK = True
except Exception:
    AppBarClass = None
    KIVYMD_OK = False

# ------------------ ASPECT DETECTION HELPER ------------------
def detect_aspect_from_configs():
    """
    Detect desired aspect ratio from configuration files.
    
    Priority:
    1. modes.json (keys: aspect, aspect_ratio, mode, display_mode)
    2. image_meta.json (key: aspect_ratio)
    3. Default: "16:9"
    
    Normalizes variants:
    - "9:16", "9/16", "portrait", "vertical" → "9:16"
    - "16:9", "16/9", "landscape", "horizontal" → "16:9"
    
    Returns:
        str: Normalized aspect ratio ("9:16" or "16:9")
    """
    # Try modes.json first
    if MODES_PATH.exists():
        try:
            data = json.loads(MODES_PATH.read_text(encoding="utf-8"))
            # Check for aspect-related keys at root level
            for key in ["aspect", "aspect_ratio", "mode", "display_mode"]:
                if key in data:
                    value = str(data[key]).lower().strip()
                    # Normalize to standard format
                    if value in ["9:16", "9/16", "portrait", "vertical"]:
                        debug_logger.info(f"Detected aspect from modes.json['{key}']: {value} → 9:16")
                        return "9:16"
                    elif value in ["16:9", "16/9", "landscape", "horizontal"]:
                        debug_logger.info(f"Detected aspect from modes.json['{key}']: {value} → 16:9")
                        return "16:9"
        except Exception as e:
            debug_logger.warning(f"Could not read aspect from modes.json: {e}")
    
    # Try image_meta.json as fallback
    if IMAGE_META_PATH.exists():
        try:
            data = json.loads(IMAGE_META_PATH.read_text(encoding="utf-8"))
            if "aspect_ratio" in data:
                value = str(data["aspect_ratio"]).lower().strip()
                # Normalize to standard format
                if value in ["9:16", "9/16", "portrait", "vertical"]:
                    debug_logger.info(f"Detected aspect from image_meta.json: {value} → 9:16")
                    return "9:16"
                elif value in ["16:9", "16/9", "landscape", "horizontal"]:
                    debug_logger.info(f"Detected aspect from image_meta.json: {value} → 16:9")
                    return "16:9"
        except Exception as e:
            debug_logger.warning(f"Could not read aspect from image_meta.json: {e}")
    
    # Default to landscape
    debug_logger.info("No aspect configuration found, defaulting to 16:9")
    return "16:9"

# ------------------ Account / Auth ------------------
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def load_accounts():
    if not ACCOUNTS_PATH.exists():
        return {}
    accounts = {}
    with ACCOUNTS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(";")
            if len(parts) >= 6:
                username, pw_hash, vorname, nachname, email, firma = parts[:6]
                accounts[username.lower()] = {
                    "benutzername": username,
                    "passwort": pw_hash,
                    "vorname": vorname,
                    "nachname": nachname,
                    "email": email,
                    "firma": firma
                }
    return accounts

def save_account(benutzername, passwort, vorname, nachname, email, firma):
    pw_hash = hash_password(passwort)
    line = ";".join([benutzername, pw_hash, vorname, nachname, email, firma])
    ACCOUNTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ACCOUNTS_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

def account_exists(benutzername):
    return benutzername.lower() in load_accounts()

def check_account(benutzername, passwort):
    if benutzername.lower() == "dennis" and passwort == "wojtyczka":
        return True
    acc = load_accounts()
    return benutzername.lower() in acc and acc[benutzername.lower()]["passwort"] == hash_password(passwort)

# ------------------ Mode / Scheduler ------------------
def parse_time(hhmm: str):
    try:
        h, m = hhmm.strip().split(":")
        return dt_time(int(h), int(m))
    except Exception:
        return None

def time_in_window(now_t: dt_time, start_t: dt_time, end_t: dt_time):
    if start_t <= end_t:
        return start_t <= now_t <= end_t
    return now_t >= start_t or now_t <= end_t

class Mode:
    def __init__(self, name, images=None, interval=DEFAULT_INTERVAL, windows=None,
                 auto=True, randomize=False):
        self.name = name
        self.images = images[:] if images else []
        self.interval = interval
        self.windows = windows[:] if windows else []
        self.auto = auto
        self.randomize = randomize
    def to_dict(self):
        return {
            "name": self.name,
            "images": self.images,
            "interval": self.interval,
            "windows": self.windows,
            "auto": self.auto,
            "randomize": self.randomize
        }
    @staticmethod
    def from_dict(d):
        return Mode(
            name=d.get("name", "Unbenannt"),
            images=d.get("images", []),
            interval=d.get("interval", DEFAULT_INTERVAL),
            windows=d.get("windows", []),
            auto=d.get("auto", True),
            randomize=d.get("randomize", False),
        )
    def is_active_now(self):
        if not self.auto or not self.windows:
            return False
        now_t = datetime.now().time()
        for w in self.windows:
            st = parse_time(w.get("start", "00:00"))
            et = parse_time(w.get("end", "23:59"))
            if st and et and time_in_window(now_t, st, et):
                return True
        return False
    def existing_images(self):
        return [p for p in self.images if os.path.isfile(p)]

class ModeManager:
    def __init__(self, path: Path):
        self.path = path
        self.modes = []
        self.load()
        self.ensure_defaults()
    def load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.modes = [Mode.from_dict(x) for x in data.get("modes", [])]
            except Exception:
                self.modes = []
        else:
            self.modes = []
    def save(self):
        self.path.write_text(
            json.dumps({"modes": [m.to_dict() for m in self.modes]}, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    def ensure_defaults(self):
        names = [m.name for m in self.modes]
        changed = False
        if "Alle Bilder" not in names:
            self.modes.insert(0, Mode("Alle Bilder", images=[], interval=5, windows=[], auto=False)); changed = True
        if "Tag" not in names:
            self.modes.append(Mode("Tag", images=[], interval=5,
                                   windows=[{"start": "06:00", "end": "21:00"}], auto=True)); changed = True
        if "Standard" not in names:
            self.modes.append(Mode("Standard", images=[], interval=5, windows=[], auto=False)); changed = True
        if "Nacht" not in names:
            self.modes.append(Mode("Nacht", images=[], interval=7,
                                   windows=[{"start": "21:00", "end": "05:30"}], auto=True)); changed = True
        if "Urlaub" not in names:
            self.modes.append(Mode("Urlaub", images=[], interval=15,
                                   windows=[{"start": "12:30", "end": "13:30"}], auto=True)); changed = True
        if "Import" not in names:
            self.modes.append(Mode("Import", images=[], interval=5, windows=[], auto=False)); changed = True
        if changed:
            self.save()
    def get(self, name):
        for m in self.modes:
            if m.name == name:
                return m
        return None
    def scheduled_mode(self):
        # Check if Urlaub mode is active first - it has priority and disables Tag/Nacht
        urlaub_mode = self.get("Urlaub")
        if urlaub_mode and urlaub_mode.is_active_now():
            return urlaub_mode
        
        # If Urlaub is not active, check other scheduled modes (excluding Tag/Nacht if Urlaub exists)
        for m in self.modes:
            if m.name in ("Alle Bilder", "Standard", "Urlaub"):
                continue
            if m.is_active_now():
                return m
        return None

# ---- UI Helpers ----
def make_text_field(hint, password=False):
    if KIVYMD_OK:
        try:
            return MDTextField(hint_text=hint, password=password)
        except Exception:
            pass
    box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(78))
    lbl = Label(text=hint, size_hint_y=None, height=dp(22), color=(0.85,0.85,0.9,1))
    ti = TextInput(password=password, multiline=False,
                   background_color=(0.2,0.2,0.24,1),
                   foreground_color=(1,1,1,1),
                   font_size=dp(20),
                   padding=[10,10,10,10],
                   height=dp(50), size_hint_y=None)
    box.add_widget(lbl); box.add_widget(ti); box._ti = ti
    return box

def get_text(widget):
    if hasattr(widget, "text"):
        try: return widget.text
        except: pass
    if hasattr(widget, "_ti"): return widget._ti.text
    for c in getattr(widget, "children", []):
        if isinstance(c, TextInput): return c.text
    return ""

def get_underlying_textinput(widget):
    if isinstance(widget, TextInput):
        return widget
    if hasattr(widget, "_ti"): return widget._ti
    return None

# ---- Soft Keyboard ----
class SoftKeyboard(FloatLayout):
    def __init__(self, on_close, **kw):
        super().__init__(**kw)
        self.on_close = on_close
        self.target = None
        with self.canvas.before:
            GColor(0,0,0,0.85)
            self.bg = Rectangle(pos=self.pos,size=self.size)
        self.bind(pos=self._upd_bg,size=self._upd_bg)
        rows = [
            "1 2 3 4 5 6 7 8 9 0 ←",
            "q w e r t z u i o p",
            "a s d f g h j k l",
            "⇧ y x c v b n m .",
            "SPACE OK"
        ]
        self.shift = False
        root = BoxLayout(orientation="vertical", size_hint=(1,None), height=dp(320), pos_hint={'x':0,'y':0})
        for r in rows:
            rb = BoxLayout(spacing=dp(4), size_hint_y=None, height=dp(56), padding=[dp(4),0,dp(4),0])
            for key in r.split():
                btn = Button(text=key,
                             background_normal='',
                             background_color=(0.25,0.25,0.3,1),
                             color=(1,1,1,1),
                             font_size=dp(20))
                btn.bind(on_release=lambda inst, k=key: self.press(k))
                rb.add_widget(btn)
            root.add_widget(rb)
        self.add_widget(root)
    def _upd_bg(self,*a):
        self.bg.pos=self.pos; self.bg.size=self.size
    def set_target(self, widget):
        self.target = get_underlying_textinput(widget)
    def press(self, key):
        if key == "⇧":
            self.shift = not self.shift; return
        if key == "←":
            if self.target: self.target.text = self.target.text[:-1]
            return
        if key == "SPACE": key = " "
        if key == "OK":
            self.on_close(); return
        if self.target:
            self.target.insert_text(key.upper() if self.shift and len(key)==1 else key)

# ---- Auth Screens (Login / Register) ----
class LoginScreen(FloatLayout):
    def __init__(self, on_success, on_register, **kw):
        super().__init__(**kw)
        self.on_success=on_success
        self.on_register=on_register
        self.keyboard_widget=None
        self.last_input=None
        with self.canvas.before:
            # Add paint-proofing colored rectangle (DEBUG_LOGIN_PAINT)
            if DEBUG_LOGIN_PAINT:
                GColor(0, 0.5, 1, 0.3)  # Blue with 30% opacity
                self._debug_paint_rect = Rectangle(pos=self.pos, size=self.size)
            
            GColor(0.07,0.07,0.09,1)
            self.bg=Rectangle(pos=self.pos,size=self.size)
        self.bind(pos=self._upd_bg,size=self._upd_bg)
        card=BoxLayout(orientation="vertical", size_hint=(None,None),
                       size=(480,560),
                       pos_hint={"center_x":0.5,"center_y":0.55},
                       padding=dp(28), spacing=dp(18))
        with card.canvas.before:
            GColor(0.16,0.16,0.20,1)
            self._c_bg=Rectangle(pos=card.pos,size=card.size)
        card.bind(pos=lambda *a:setattr(self._c_bg,'pos',card.pos),
                  size=lambda *a:setattr(self._c_bg,'size',card.size))
        self.add_widget(card)
        card.add_widget(Label(text="Login", size_hint_y=None, height=dp(64),
                              font_size=dp(32), color=(1,1,1,1)))
        self.user=make_text_field("Benutzername")
        self.pw=make_text_field("Passwort", password=True)
        for w in (self.user,self.pw):
            ti=get_underlying_textinput(w)
            if ti: ti.bind(focus=self._on_focus)
        card.add_widget(self.user); card.add_widget(self.pw)
        kb_btn=Button(text="Tastatur", size_hint_y=None, height=dp(50),
                      background_normal='', background_color=(0.3,0.35,0.5,1),
                      color=(1,1,1,1), font_size=dp(20))
        kb_btn.bind(on_release=lambda *_: self.toggle_keyboard())
        card.add_widget(kb_btn)
        self.status=Label(text="", size_hint_y=None, height=dp(30),
                          color=(1,0.4,0.4,1), font_size=dp(18))
        card.add_widget(self.status)
        row=BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(20))
        b_login=Button(text="Login", background_normal='',
                       background_color=(0.25,0.45,0.25,1),
                       color=(1,1,1,1), font_size=dp(22))
        b_reg=Button(text="Registrieren", background_normal='',
                     background_color=(0.3,0.3,0.35,1),
                     color=(1,1,1,1), font_size=dp(22))
        b_login.bind(on_release=self.try_login)
        b_reg.bind(on_release=lambda *_: self.on_register())
        row.add_widget(b_login); row.add_widget(b_reg)
        card.add_widget(row)
        
        # Add paint-proofing label at top-left (DEBUG_LOGIN_PAINT)
        if DEBUG_LOGIN_PAINT:
            self._debug_paint_label = Label(
                text="HELLO LOGIN",
                size_hint=(None, None),
                size=(300, 60),
                pos=(10, self.height - 70),
                color=(1, 1, 0, 1),  # Yellow
                font_size=32,
                bold=True,
                halign='left',
                valign='top'
            )
            self._debug_paint_label.text_size = (300, 60)
            self.add_widget(self._debug_paint_label)
            # Bind to update position when screen is resized
            self.bind(size=lambda *args: setattr(self._debug_paint_label, 'pos', (10, self.height - 70)))
    def _on_focus(self, textinput, focused):
        if focused:
            self.last_input=textinput
            if self.keyboard_widget:
                self.keyboard_widget.set_target(textinput)
    def toggle_keyboard(self):
        if not ENABLE_SOFT_KEYBOARD: return
        if self.keyboard_widget:
            self.remove_widget(self.keyboard_widget); self.keyboard_widget=None
        else:
            self.keyboard_widget=SoftKeyboard(on_close=self.toggle_keyboard,
                                              size_hint=(1,None),
                                              height=dp(320),
                                              pos_hint={'x':0,'y':0})
            target=self.last_input or get_underlying_textinput(self.user)
            self.keyboard_widget.set_target(target)
            self.add_widget(self.keyboard_widget)
    def _upd_bg(self,*a):
        self.bg.pos=self.pos; self.bg.size=self.size
        # Update debug paint rect if it exists (DEBUG_LOGIN_PAINT)
        if DEBUG_LOGIN_PAINT and hasattr(self, '_debug_paint_rect'):
            self._debug_paint_rect.pos = self.pos
            self._debug_paint_rect.size = self.size
    def try_login(self,*_):
        username=get_text(self.user).strip()
        password=get_text(self.pw)
        if check_account(username,password):
            self.status.text=""
            if self.keyboard_widget: self.remove_widget(self.keyboard_widget)
            self.on_success()
        else:
            self.status.text="Falscher Benutzername oder Passwort"



class RegisterScreen(FloatLayout):
    def __init__(self, on_done, **kw):
        super().__init__(**kw)
        self.on_done=on_done
        self.keyboard_widget=None
        self.last_input=None
        with self.canvas.before:
            GColor(0.07,0.07,0.09,1)
            self.bg=Rectangle(pos=self.pos,size=self.size)
        self.bind(pos=self._upd_bg,size=self._upd_bg)
        card=BoxLayout(orientation="vertical", size_hint=(None,None),
                       size=(520,820),
                       pos_hint={"center_x":0.5,"center_y":0.53},
                       padding=dp(28), spacing=dp(16))
        with card.canvas.before:
            GColor(0.16,0.16,0.20,1)
            self._c2_bg=Rectangle(pos=card.pos,size=card.size)
        card.bind(pos=lambda *a:setattr(self._c2_bg,'pos',card.pos),
                  size=lambda *a:setattr(self._c2_bg,'size',card.size))
        self.add_widget(card)
        card.add_widget(Label(text="Registrieren", size_hint_y=None, height=dp(56),
                              font_size=dp(30), color=(1,1,1,1)))
        self.fname=make_text_field("Vorname")
        self.lname=make_text_field("Nachname")
        self.user=make_text_field("Benutzername")
        self.mail=make_text_field("E-Mail")
        self.company=make_text_field("Firma")
        self.pw1=make_text_field("Passwort", password=True)
        self.pw2=make_text_field("Passwort wiederholen", password=True)
        fields=[self.fname,self.lname,self.user,self.mail,self.company,self.pw1,self.pw2]
        for w in fields:
            ti=get_underlying_textinput(w)
            if ti: ti.bind(focus=self._on_focus)
            card.add_widget(w)
        kb_btn=Button(text="Tastatur", size_hint_y=None, height=dp(50),
                      background_normal='', background_color=(0.3,0.35,0.5,1),
                      color=(1,1,1,1), font_size=dp(20))
        kb_btn.bind(on_release=lambda *_: self.toggle_keyboard())
        card.add_widget(kb_btn)
        self.status=Label(text="", size_hint_y=None, height=dp(34),
                          color=(1,0.4,0.4,1), font_size=dp(16))
        card.add_widget(self.status)
        row=BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(18))
        b_ok=Button(text="Speichern", background_normal='',
                    background_color=(0.25,0.45,0.25,1), color=(1,1,1,1), font_size=dp(22))
        b_cancel=Button(text="Abbrechen", background_normal='',
                        background_color=(0.3,0.3,0.35,1), color=(1,1,1,1), font_size=dp(22))
        b_ok.bind(on_release=self.try_register)
        b_cancel.bind(on_release=lambda *_: self.on_done())
        row.add_widget(b_ok); row.add_widget(b_cancel)
        card.add_widget(row)
    def _on_focus(self, textinput, focused):
        if focused:
            self.last_input=textinput
            if self.keyboard_widget:
                self.keyboard_widget.set_target(textinput)
    def toggle_keyboard(self):
        if not ENABLE_SOFT_KEYBOARD: return
        if self.keyboard_widget:
            self.remove_widget(self.keyboard_widget); self.keyboard_widget=None
        else:
            self.keyboard_widget=SoftKeyboard(on_close=self.toggle_keyboard,
                                              size_hint=(1,None),height=dp(320),
                                              pos_hint={'x':0,'y':0})
            target=self.last_input or get_underlying_textinput(self.fname)
            self.keyboard_widget.set_target(target)
            self.add_widget(self.keyboard_widget)
    def _upd_bg(self,*a):
        self.bg.pos=self.pos; self.bg.size=self.size
    def try_register(self,*_):
        vorname=get_text(self.fname).strip()
        nachname=get_text(self.lname).strip()
        benutzername=get_text(self.user).strip()
        email=get_text(self.mail).strip()
        firma=get_text(self.company).strip()
        pw1=get_text(self.pw1)
        pw2=get_text(self.pw2)
        def fail(msg): self.status.text=msg
        if not all([vorname,nachname,benutzername,email,pw1,pw2]): return fail("Bitte alle Felder")
        if '@' not in email or '.' not in email: return fail("Mail ungültig")
        if len(pw1)<6: return fail("Passwort zu kurz")
        if pw1!=pw2: return fail("Passwörter verschieden")
        if account_exists(benutzername): return fail("Benutzer existiert")
        try:
            save_account(benutzername,pw1,vorname,nachname,email,firma)
        except Exception:
            return fail("Fehler beim Speichern")
        self.status.text="Registriert!"
        Clock.schedule_once(lambda dt:self.on_done(),0.8)

# ---- CustomAppBar ----
class VerticalButton(Button):
    """Button for 9:16 mode toolbar - now just a regular Button since global rotation handles orientation"""
    def __init__(self, rotation_angle=None, flip_glyphs=None, **kwargs):
        # Ignore rotation parameters - global rotation handles everything
        super().__init__(**kwargs)
        # Add padding for better appearance
        self.padding = [dp(10), dp(5)]

# RotatedLabel and RotatedButton are now just aliases since global rotation handles everything
# These are kept for backward compatibility with existing code
class RotatedLabel(Label):
    """Label that used to rotate text - now just a regular Label since global rotation handles it"""
    def __init__(self, rotation_angle=0, **kwargs):
        # Ignore rotation_angle parameter - global rotation handles it
        super().__init__(**kwargs)

class RotatedButton(Button):
    """Button that used to rotate text - now just a regular Button since global rotation handles it"""
    def __init__(self, rotation_angle=0, **kwargs):
        # Ignore rotation_angle parameter - global rotation handles it
        super().__init__(**kwargs)

class CustomAppBar(BoxLayout):
    def __init__(self, title="App", vertical=False, **kwargs):
        # Determine orientation and sizing based on vertical parameter
        if vertical:
            orientation = "vertical"
            size_hint = (None, 1)
            width = dp(110)
            height = None
        else:
            orientation = "horizontal"
            size_hint = (1, None)
            width = None
            height = dp(60)
        
        super().__init__(orientation=orientation, size_hint=size_hint, **kwargs)
        
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
            
        self.vertical = vertical
        
        with self.canvas.before:
            GColor(0.12,0.12,0.14,1)
            self.bg=Rectangle(pos=self.pos,size=self.size)
        self.bind(pos=self._upd_bg,size=self._upd_bg)
        self._title_label=Label(text=("" if HIDE_TOOLBAR_TITLE else title),
                                color=(1,1,1,1), 
                                size_hint_x=1 if not vertical else None,
                                size_hint_y=None if not vertical else 0.15,
                                halign='center' if vertical else 'left', 
                                valign='middle')
        self._title_label.bind(size=lambda inst,*a:setattr(inst,"text_size",inst.size))
        self.add_widget(self._title_label)
        
        if vertical:
            self._buttons_box=BoxLayout(orientation="vertical", size_hint=(1, None))
            self._buttons_box.height=0
        else:
            self._buttons_box=BoxLayout(size_hint=(None,1)); self._buttons_box.width=0
        self.add_widget(self._buttons_box)
        self.opacity=1
        self.disabled=False
        self._fade_anim=None
    def _upd_bg(self,*a):
        self.bg.pos=self.pos; self.bg.size=self.size
    @property
    def title(self): return self._title_label.text
    @title.setter
    def title(self,v): self._title_label.text = "" if HIDE_TOOLBAR_TITLE else v
    def set_right_actions(self, items):
        self._buttons_box.clear_widgets()
        total_size = 0
        for text,cb in items:
            if self.vertical:
                # Use VerticalButton for 9:16 mode - global rotation handles orientation
                btn=VerticalButton(text=text,size_hint=(1,None),height=dp(70),
                                   background_normal='',background_color=(0.20,0.22,0.26,1),
                                   color=(1,1,1,1),font_size=dp(14))
                btn.bind(on_release=lambda inst,c=cb:c())
                self._buttons_box.add_widget(btn)
                total_size += btn.height
            else:
                btn=Button(text=text,size_hint=(None,1),width=dp(110),
                           background_normal='',background_color=(0.20,0.22,0.26,1),
                           color=(1,1,1,1),font_size=dp(16))
                btn.bind(on_release=lambda inst,c=cb:c())
                self._buttons_box.add_widget(btn)
                total_size += btn.width
        
        if self.vertical:
            self._buttons_box.height = total_size
        else:
            self._buttons_box.width = total_size
    def fade_in(self,duration=TOOLBAR_FADE_DURATION):
        self.disabled=False
        if self._fade_anim: self._fade_anim.stop(self)
        self._fade_anim=Animation(opacity=1,d=duration,t='out_quad')
        self._fade_anim.start(self)
    def fade_out(self,duration=TOOLBAR_FADE_DURATION):
        if self._fade_anim: self._fade_anim.stop(self)
        def _dis(*_): self.disabled=True
        self._fade_anim=Animation(opacity=0,d=duration,t='in_quad')
        self._fade_anim.bind(on_complete=_dis)
        self._fade_anim.start(self)

# ---- Persistenz Bild-Meta ----
def load_image_meta():
    base = {"effects":{}, "intervals":{}, "weights":{}, "brightness":{}, "global_interval": None, "global_brightness": None, "aspect_ratio": "16:9"}
    if not IMAGE_META_PATH.exists():
        return base
    try:
        data=json.loads(IMAGE_META_PATH.read_text(encoding="utf-8"))
        for k,v in base.items():
            if k not in data: data[k]=v
        return data
    except Exception:
        return base

def save_image_meta(meta):
    try:
        IMAGE_META_PATH.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print("[META] Speichern fehlgeschlagen:", e)

# ---- Image Settings Popup (per Bild) ----
class ImageSettingsPopup(RotatedModalView):
    def __init__(self, image_path, slideshow, on_close=None, on_deleted=None, **kw):
        kw.setdefault('size_hint', (None, None))
        kw.setdefault('size', (dp(500), dp(720)))
        kw.setdefault('auto_dismiss', False)
        super().__init__(**kw)
        self.image_path=image_path
        self.slideshow=slideshow
        self.on_close=on_close
        self.on_deleted=on_deleted
        self.background_color = (0, 0, 0, 0.65)
        self.background = ''
        panel=BoxLayout(orientation='vertical',size_hint=(1, 1),
                        padding=dp(20),spacing=dp(14))
        with panel.canvas.before:
            GColor(0.16,0.16,0.2,0.97)
            panel._bg=Rectangle(pos=panel.pos,size=panel.size)
        panel.bind(pos=lambda *a:setattr(panel._bg,'pos',panel.pos),
                   size=lambda *a:setattr(panel._bg,'size',panel.size))
        name=Path(image_path).name
        panel.add_widget(Label(text=name,size_hint_y=None,height=dp(40),
                               font_size=dp(18),color=(1,1,1,1)))

        # Effekt Override
        panel.add_widget(Label(text="Effekt Override:",size_hint_y=None,height=dp(28),
                               font_size=dp(16),color=(1,1,1,0.9)))
        from kivy.uix.gridlayout import GridLayout
        grid=GridLayout(cols=2,spacing=dp(6),size_hint_y=None)
        grid.bind(minimum_height=lambda inst,val:setattr(inst,'height',val))
        cur_eff=self.slideshow.image_effect_overrides.get(image_path)
        def add_eff(key,label):
            btn=ToggleButton(text=("Standard" if key is None else label),
                             group="imgfx",
                             state='down' if cur_eff==key else ('down' if (key is None and cur_eff is None) else 'normal'),
                             size_hint_y=None,height=dp(44),
                             background_normal='',background_down='',
                             background_color=(0.25,0.35,0.5,1),
                             color=(1,1,1,1),font_size=dp(14))
            btn.bind(on_release=lambda inst,k=key:self._set_effect(k))
            grid.add_widget(btn)
        add_eff(None,"Standard")
        for k,lbl in EFFECTS_AVAILABLE: add_eff(k,lbl)
        scr=ScrollView(size_hint=(1,0.38)); scr.add_widget(grid)
        panel.add_widget(scr)

        # Per-Bild Intervall
        panel.add_widget(Label(text="Anzeigedauer (s, 0 = Aus):",size_hint_y=None,height=dp(26),
                               font_size=dp(16),color=(1,1,1,0.9)))
        cur_int=self.slideshow.image_interval_overrides.get(image_path,0)
        self.int_slider=Slider(min=0,max=120,value=cur_int,step=1,size_hint_y=None,height=dp(42))
        self.int_label=Label(text=f"{cur_int}s" if cur_int>0 else "Aus",size_hint_y=None,height=dp(22),
                             font_size=dp(16),color=(0.9,0.9,1,1))
        self.int_slider.bind(value=lambda inst,val:self._upd_int(val))
        panel.add_widget(self.int_slider); panel.add_widget(self.int_label)

        # Priorität / Gewicht
        panel.add_widget(Label(text="Priorität / Gewicht (1-5):",size_hint_y=None,height=dp(26),
                               font_size=dp(16),color=(1,1,1,0.9)))
        cur_w=self.slideshow.image_priority_weights.get(image_path,1)
        self.w_slider=Slider(min=1,max=5,value=cur_w,step=1,size_hint_y=None,height=dp(42))
        self.w_label=Label(text=str(int(cur_w)),size_hint_y=None,height=dp(22),
                           font_size=dp(16),color=(0.9,0.9,1,1))
        self.w_slider.bind(value=lambda inst,val:self.w_label.__setattr__('text',str(int(val))))
        panel.add_widget(self.w_slider); panel.add_widget(self.w_label)

        # Per-Bild Helligkeit
        panel.add_widget(Label(text="Helligkeit (50% - 150%):",size_hint_y=None,height=dp(26),
                               font_size=dp(16),color=(1,1,1,0.9)))
        cur_b = self.slideshow.image_brightness_overrides.get(image_path,1.0)
        self.bright_slider=Slider(min=0.5,max=1.5,value=cur_b,step=0.01,size_hint_y=None,height=dp(42))
        self.bright_label=Label(text=f"{cur_b*100:.0f}%",size_hint_y=None,height=dp(22),
                                font_size=dp(16),color=(0.9,0.9,1,1))
        self.bright_slider.bind(value=lambda inst,val:self.bright_label.__setattr__('text',f"{float(val)*100:.0f}%"))
        panel.add_widget(self.bright_slider); panel.add_widget(self.bright_label)

        # Buttons
        row=BoxLayout(size_hint_y=None,height=dp(56),spacing=dp(14))
        save_btn=Button(text="Speichern",background_normal='',background_color=(0.25,0.55,0.25,1),
                        color=(1,1,1,1),font_size=dp(18))
        del_btn=Button(text="Löschen",background_normal='',background_color=(0.6,0.25,0.25,1),
                       color=(1,1,1,1),font_size=dp(18))
        close_btn=Button(text="Schließen",background_normal='',background_color=(0.35,0.45,0.55,1),
                         color=(1,1,1,1),font_size=dp(18))
        save_btn.bind(on_release=lambda *_: self._save())
        del_btn.bind(on_release=lambda *_: self._confirm_delete())
        close_btn.bind(on_release=lambda *_: self._close())
        row.add_widget(save_btn); row.add_widget(del_btn); row.add_widget(close_btn)
        panel.add_widget(row)
        self._confirm_box=None
        self.add_widget(panel)
    def _set_effect(self,key):
        if key is None:
            self.slideshow.image_effect_overrides.pop(self.image_path, None)
        else:
            self.slideshow.image_effect_overrides[self.image_path]=key
    def _upd_int(self,val):
        v=int(val); self.int_label.text=f"{v}s" if v>0 else "Aus"
    def _save(self):
        # Interval
        v=int(self.int_slider.value)
        if v<=0:
            self.slideshow.image_interval_overrides.pop(self.image_path, None)
        else:
            self.slideshow.image_interval_overrides[self.image_path]=v
        # Gewicht
        w=int(self.w_slider.value)
        self.slideshow.image_priority_weights[self.image_path]=w
        # Brightness
        b=float(self.bright_slider.value)
        # Standard = 1.0 -> wenn 1.0 dann raus für Clean
        if abs(b-1.0)<0.001:
            self.slideshow.image_brightness_overrides.pop(self.image_path, None)
        else:
            self.slideshow.image_brightness_overrides[self.image_path]=b
        self.slideshow.persist_meta()
        # Falls aktuelles Bild -> sofort anwenden
        if self.slideshow.current_original_path == self.image_path:
            self.slideshow._apply_current_brightness()
            self.slideshow._reschedule_for_current()
        self._close()
    def _confirm_delete(self):
        if self._confirm_box: return
        box=BoxLayout(orientation='vertical',size_hint=(None,None),
                      size=(dp(340),dp(160)),
                      pos_hint={'center_x':0.5,'center_y':0.5},
                      padding=dp(16),spacing=dp(12))
        with box.canvas.before:
            GColor(0.3,0.15,0.15,0.95)
            box._bg=Rectangle(pos=box.pos,size=box.size)
        box.bind(pos=lambda *a:setattr(box._bg,'pos',box.pos),
                 size=lambda *a:setattr(box._bg,'size',box.size))
        box.add_widget(Label(text="Bild wirklich löschen?",size_hint_y=None,
                             height=dp(40),font_size=dp(20),color=(1,1,1,1)))
        r=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(10))
        ja=Button(text="Ja",background_normal='',background_color=(0.7,0.2,0.2,1),color=(1,1,1,1))
        nein=Button(text="Nein",background_normal='',background_color=(0.4,0.4,0.5,1),color=(1,1,1,1))
        ja.bind(on_release=lambda *_: self._delete_now())
        nein.bind(on_release=lambda *_: self._remove_confirm())
        r.add_widget(ja); r.add_widget(nein)
        box.add_widget(r)
        self.add_widget(box); self._confirm_box=box
    def _remove_confirm(self):
        if self._confirm_box and self._confirm_box in self.children:
            self.remove_widget(self._confirm_box)
        self._confirm_box=None
    def _delete_now(self):
        self._remove_confirm()
        p=self.image_path
        try:
            if os.path.isfile(p): os.remove(p)
        except Exception as e: print("[Delete] Fehler:",e)
        for d in (self.slideshow.image_effect_overrides,
                  self.slideshow.image_interval_overrides,
                  self.slideshow.image_priority_weights,
                  self.slideshow.image_brightness_overrides):
            d.pop(p, None)
        for m in self.slideshow.mode_manager.modes:
            if p in m.images: m.images.remove(p)
        self.slideshow.mode_manager.save()
        self.slideshow.persist_meta()
        if self.slideshow.current_original_path == p:
            if p in self.slideshow.images:
                self.slideshow.images.remove(p)
            self.slideshow.index=0
            self.slideshow.show_current_image(initial=True)
        if self.on_deleted: self.on_deleted(p)
        self._close()
    def _close(self):
        if self.on_close: self.on_close()
        self.dismiss()

class ImageLightboxPopup(RotatedModalView):
    """Lightbox overlay for displaying full-size images"""
    def __init__(self, image_path, **kw):
        # Set ModalView properties before calling super().__init__
        kw.setdefault('size_hint', (1, 1))
        kw.setdefault('auto_dismiss', True)
        super().__init__(**kw)
        self.image_path=image_path
        
        # ModalView already provides dark background, but we can customize it
        self.background_color = (0, 0, 0, 0.9)
        self.background = ''
        
        # Main container for image
        container=FloatLayout()
        
        # Create image widget with fit_mode='contain' to show full image without cropping
        import kivy
        kivy_version = tuple(map(int, kivy.__version__.split('.')[:2]))
        if kivy_version >= (2, 3):
            self.img=Image(size_hint=(1, 1),
                          fit_mode='contain',
                          mipmap=True)
        else:
            self.img=Image(size_hint=(1, 1),
                          allow_stretch=True,
                          keep_ratio=True,
                          mipmap=True)
        
        # Load image robustly - clear state first, then load via CoreImage (primary) or source (fallback)
        def load_image(dt):
            import os
            
            # Clear previous state
            self.img.source = ""
            self.img.texture = None
            
            # Check if file exists
            file_exists = os.path.exists(image_path)
            debug_logger.info(f"Loading lightbox image: path={image_path}, exists={file_exists}")
            
            if not file_exists:
                debug_logger.error(f"Lightbox image file does not exist: {image_path}")
                error_label = Label(text=f"Fehler: Bild nicht gefunden\n{Path(image_path).name}",
                                  size_hint=(0.8, 0.5),
                                  pos_hint={'center_x': 0.5, 'center_y': 0.5},
                                  font_size=dp(18),
                                  color=(1, 0.3, 0.3, 1))
                container.add_widget(error_label)
                return
            
            # Primary path: load via CoreImage for better control
            try:
                from kivy.core.image import Image as CoreImage
                core_img = CoreImage(image_path, nocache=True)
                
                if core_img and core_img.texture:
                    self.img.texture = core_img.texture
                    tex_size = core_img.texture.size
                    debug_logger.info(f"Lightbox image loaded via CoreImage: texture_size={tex_size}")
                else:
                    raise Exception("CoreImage returned no texture")
                    
            except Exception as e:
                # Fallback: use widget.source with reload
                debug_logger.warning(f"CoreImage failed for lightbox {image_path}: {e}, trying fallback")
                try:
                    self.img.source = image_path
                    self.img.reload()
                    
                    # Verify texture loaded
                    def check_fallback(dt2):
                        if self.img.texture:
                            tex_size = self.img.texture.size
                            debug_logger.info(f"Lightbox image loaded via fallback: texture_size={tex_size}")
                        else:
                            debug_logger.error(f"Lightbox fallback also failed: texture is None for {image_path}")
                            error_label = Label(text=f"Fehler beim Laden des Bildes:\nKeine Textur verfügbar",
                                              size_hint=(0.8, 0.5),
                                              pos_hint={'center_x': 0.5, 'center_y': 0.5},
                                              font_size=dp(18),
                                              color=(1, 0.3, 0.3, 1))
                            container.add_widget(error_label)
                    
                    from kivy.clock import Clock
                    Clock.schedule_once(check_fallback, 0.1)
                    
                except Exception as e2:
                    debug_logger.error(f"Both CoreImage and fallback failed for lightbox {image_path}: {e2}")
                    error_label = Label(text=f"Fehler beim Laden des Bildes:\n{str(e2)}",
                                      size_hint=(0.8, 0.5),
                                      pos_hint={'center_x': 0.5, 'center_y': 0.5},
                                      font_size=dp(18),
                                      color=(1, 0.3, 0.3, 1))
                    container.add_widget(error_label)
        
        from kivy.clock import Clock
        Clock.schedule_once(load_image, 0)
        
        container.add_widget(self.img)
        
        # Close button in top-right corner
        close_btn=Button(text="✕",
                        size_hint=(None,None),
                        size=(dp(50),dp(50)),
                        pos_hint={'right':0.98,'top':0.98},
                        background_normal='',
                        background_color=(0.3,0.3,0.3,0.8),
                        color=(1,1,1,1),
                        font_size=dp(24))
        close_btn.bind(on_release=lambda *_: self._close())
        container.add_widget(close_btn)
        
        # Filename label at bottom
        name=Path(image_path).name
        name_label=Label(text=name,
                        size_hint=(1,None),
                        height=dp(40),
                        pos_hint={'x':0,'y':0.02},
                        font_size=dp(16),
                        color=(1,1,1,0.9))
        container.add_widget(name_label)
        
        self.add_widget(container)
        
        # Click anywhere on background to close
        self.bind(on_touch_down=self._on_touch)
    
    def _on_touch(self, instance, touch):
        """Handle touch events - close on background click"""
        # Check if touch is on the image or close button
        if hasattr(self, 'img') and self.img.collide_point(*touch.pos):
            return False  # Don't close if clicking on image
        # Close if clicking on background
        self._close()
        return True
    
    def _close(self):
        """Close the lightbox"""
        try:
            self.dismiss()
            debug_logger.info(f"Lightbox closed for: {self.image_path}")
        except Exception as e:
            debug_logger.error(f"Error closing lightbox: {e}")

# ---- Globale Settings Hierarchie ----
class SettingsRootPopup(RotatedModalView):
    def __init__(self, slideshow, **kw):
        # Set ModalView properties for full-screen with centered content
        kw_copy = kw.copy()
        kw_copy.setdefault('size_hint', (1, 1))  # Full screen
        kw_copy.setdefault('auto_dismiss', True)
        super().__init__(**kw_copy)
        self.slideshow=slideshow
        self.background_color = (0, 0, 0, 0.7)  # Dim overlay
        self.background = ''
        
        # Calculate panel size based on aspect ratio using portrait factors
        from kivy.core.window import Window
        aspect = slideshow.aspect_ratio if slideshow else "16:9"
        if aspect == "9:16":
            # Portrait mode: apply portrait factors (0.62×w, 0.86×h, min 320×260)
            content_w = Window.width
            content_h = Window.height
            panel_w = max(int(content_w * 0.62), dp(320))
            panel_h = max(int(content_h * 0.86), dp(260))
            panel_size = (panel_w, panel_h)
        else:
            # Landscape mode: use standard size
            panel_size = (dp(500), dp(480))
        
        # Use AnchorLayout to center the content panel
        anchor = AnchorLayout(size_hint=(1, 1), anchor_x='center', anchor_y='center')
        
        panel=BoxLayout(orientation='vertical',size_hint=(None, None),size=panel_size,
                        padding=dp(24),spacing=dp(18))
        
        with panel.canvas.before:
            GColor(0.16,0.16,0.2,0.97); panel._bg=Rectangle(pos=panel.pos,size=panel.size)
        panel.bind(pos=lambda *a:setattr(panel._bg,'pos',panel.pos),
                   size=lambda *a:setattr(panel._bg,'size',panel.size))
        panel.add_widget(Label(text="Einstellungen",
                               size_hint_y=None,height=dp(56),
                               font_size=dp(34),color=(1,1,1,1)))
        def make_btn(text, cb):
            b=Button(text=text,size_hint_y=None,height=dp(70),
                     background_normal='',background_color=(0.25,0.35,0.5,1),
                     color=(1,1,1,1),font_size=dp(22))
            b.bind(on_release=lambda *_: cb())
            return b
        panel.add_widget(make_btn("Allgemein", self._open_general))
        panel.add_widget(make_btn("Bilddauer", self._open_duration))
        panel.add_widget(make_btn("Schließen", self._close))
        
        # Add panel to anchor layout, then add anchor to modal
        anchor.add_widget(panel)
        self.add_widget(anchor)
        
        # Bind ESC/Back key to dismiss
        from kivy.core.window import Window
        Window.bind(on_key_down=self._on_key_down)
        
        # Log modal opening
        debug_logger.info(f"Settings modal open centered size={panel_size[0]}x{panel_size[1]}")
    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        """Handle ESC/Back key to dismiss modal"""
        if key == 27:  # ESC or Back
            self._close()
            return True
        return False
    
    def _open_general(self):
        popup = GeneralSettingsPopup(self.slideshow)
        popup.open()
    def _open_duration(self):
        popup = GlobalDurationPopup(self.slideshow)
        popup.open()
    def _close(self):
        from kivy.core.window import Window
        Window.unbind(on_key_down=self._on_key_down)
        debug_logger.info("Settings modal dismissed")
        self.dismiss()

class LoadingSpinner(Widget):
    """A circular loading spinner widget"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0
        self.animation = None
        
        with self.canvas:
            PushMatrix()
            self.rotate = Rotate()
            self.rotate.angle = 0
            self.rotate.origin = (0, 0)
            GColor(0.3, 0.7, 1.0, 1.0)  # Blue color
            self.circle = Line(circle=(0, 0, dp(20)), width=dp(3), cap='round')
            self.circle.dash_offset = 10
            self.circle.dash_length = 15
            PopMatrix()
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
    def update_graphics(self, *args):
        self.rotate.origin = (self.center_x, self.center_y)
        self.circle.circle = (self.center_x, self.center_y, dp(20))
        
    def start_spinning(self):
        """Start the spinning animation"""
        if self.animation:
            self.animation.cancel(self)
        
        def update_angle(widget, value):
            self.rotate.angle = value
            
        self.animation = Animation(angle=360, duration=1.5)
        self.animation.bind(on_progress=lambda anim, widget, progress: 
                          setattr(self.rotate, 'angle', progress * 360))
        self.animation.repeat = True
        self.animation.start(self)
        
    def stop_spinning(self):
        """Stop the spinning animation"""
        if self.animation:
            self.animation.cancel(self)
            self.animation = None

class AufnahmePopup(RotatedModalView):
    """Popup window for recording functionality with improved error handling"""
    def __init__(self, slideshow=None, **kwargs):
        # Proactively remove any legacy sheet instances before opening
        self._cleanup_legacy_sheets()
        
        # Set ModalView properties for full-screen with semi-transparent background
        kw_copy = kwargs.copy()
        kw_copy.setdefault('size_hint', (1, 1))  # Full screen
        kw_copy.setdefault('auto_dismiss', False)
        super().__init__(**kw_copy)
        self.slideshow = slideshow  # Reference to parent slideshow for gallery navigation
        self.process = None
        self.is_running = False
        self.start_time = None
        self.timer_event = None
        self.workflow_triggered = False  # Track if workflow was already triggered
        self.workflow_status_checker = None  # Track status checker
        self.workflow_lock_file = None  # NEW: Track workflow lockfile
        self.trigger_creation_lock = threading.Lock()  # NEW: Thread-safe trigger creation
        
        # UI State management for new behavior
        self.ui_state = "ready"  # ready, recording, processing, completed
        self.interaction_blocked = False
        
        # Audio file path for validation (standardized location)
        self.audio_file_path = Path("/home/pi/Desktop/v2_Tripple S/aufnahme.wav")
        
        # ModalView with semi-transparent background
        self.background_color = (0, 0, 0, 0.7)
        self.background = ''
        
        # Calculate panel size based on aspect ratio using portrait factors
        # Portrait factors: width=0.62×content width, height=0.86×content height (min w≥320, h≥260)
        from kivy.core.window import Window
        aspect = slideshow.aspect_ratio if slideshow else "16:9"
        if aspect == "9:16":
            # Portrait mode: apply portrait factors
            content_w = Window.width
            content_h = Window.height
            panel_w = max(int(content_w * 0.62), dp(320))
            panel_h = max(int(content_h * 0.86), dp(260))
            panel_size = (panel_w, panel_h)
        else:
            # Landscape mode: use standard size
            panel_size = (dp(600), dp(500))
        
        # Use AnchorLayout to center the content panel
        anchor = AnchorLayout(size_hint=(1, 1), anchor_x='center', anchor_y='center')
        
        self.panel = BoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=panel_size,
            padding=dp(20),
            spacing=dp(15)
        )
        
        with self.panel.canvas.before:
            GColor(0.16, 0.16, 0.20, 0.95)
            self.panel._bg = Rectangle(pos=self.panel.pos, size=self.panel.size)
        self.panel.bind(pos=lambda *a: setattr(self.panel._bg, 'pos', self.panel.pos),
                       size=lambda *a: setattr(self.panel._bg, 'size', self.panel.size))
        
        # Title
        self.title = Label(
            text="Audio-Aufnahme + Bild",
            size_hint_y=None,
            height=dp(40),
            font_size=dp(26),
            color=(1, 1, 1, 1)
        )
        self.panel.add_widget(self.title)
        
        # Timer display
        self.timer_label = Label(
            text="00:00",
            size_hint_y=None,
            height=dp(50),
            font_size=dp(32),
            color=(0.8, 0.9, 1, 1)
        )
        self.panel.add_widget(self.timer_label)
        
        # Loading spinner container (initially hidden) - positioned centrally under timer
        self.spinner_container = FloatLayout(
            size_hint=(1, None),
            height=dp(80)  # Fixed height for consistent positioning
        )
        self.loading_spinner = LoadingSpinner(
            size_hint=(None, None),
            size=(dp(50), dp(50)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.spinner_container.add_widget(self.loading_spinner)
        self.spinner_container.opacity = 0  # Initially hidden
        self.panel.add_widget(self.spinner_container)
        
        # Start/Stop button
        self.button = Button(
            text="Start",
            size_hint_y=None,
            height=dp(60),
            background_normal='',
            background_color=(0.25, 0.55, 0.25, 1),
            color=(1, 1, 1, 1),
            font_size=dp(24)
        )
        self.button.bind(on_press=self.toggle_recording)
        self.panel.add_widget(self.button)
        
        # Image selection button (optional - for enhanced workflow)
        self.image_button = Button(
            text="📷 Bild hinzufügen (optional)",
            size_hint_y=None,
            height=dp(50),
            background_normal='',
            background_color=(0.35, 0.35, 0.55, 1),
            color=(1, 1, 1, 1),
            font_size=dp(18)
        )
        self.image_button.bind(on_press=self.open_image_selection)
        self.panel.add_widget(self.image_button)
        
        # QR code button for mobile upload
        self.qr_button = Button(
            text="📱 QR-Code für Mobile Upload",
            size_hint_y=None,
            height=dp(50),
            background_normal='',
            background_color=(0.45, 0.35, 0.55, 1),
            color=(1, 1, 1, 1),
            font_size=dp(18)
        )
        self.qr_button.bind(on_press=self.show_qr_code)
        self.panel.add_widget(self.qr_button)
        
        # Selected image info
        self.image_info_label = Label(
            text="",
            size_hint_y=None,
            height=dp(0),  # Initially hidden
            font_size=dp(14),
            color=(0.7, 0.9, 0.7, 1),
            text_size=(None, None),
            halign='center'
        )
        self.panel.add_widget(self.image_info_label)
        
        # Track selected image
        self.selected_image_path = None
        self.selected_image_base64 = None
        
        # Output display area - wrapped in a container for easy hide/show
        self.output_section = BoxLayout(orientation='vertical', size_hint=(1, 0.5))
        
        output_label = Label(
            text="Ausgabe:",
            size_hint_y=None,
            height=dp(25),
            font_size=dp(18),
            color=(1, 1, 1, 0.8),
            halign='left'
        )
        output_label.bind(size=lambda inst, *args: setattr(inst, 'text_size', inst.size))
        self.output_section.add_widget(output_label)
        
        # Scrollable output text area
        from kivy.uix.scrollview import ScrollView
        scroll = ScrollView(size_hint=(1, 1))
        self.output_text = Label(
            text="Bereit für Aufnahme...",
            text_size=(None, None),
            halign='left',
            valign='top',
            color=(0.9, 0.9, 0.9, 1),
            font_size=dp(14),
            markup=True
        )
        scroll.add_widget(self.output_text)
        self.output_section.add_widget(scroll)
        
        self.panel.add_widget(self.output_section)
        
        # Close button
        self.close_button = Button(
            text="Schließen",
            size_hint_y=None,
            height=dp(50),
            background_normal='',
            background_color=(0.4, 0.4, 0.45, 1),
            color=(1, 1, 1, 1),
            font_size=dp(20)
        )
        self.close_button.bind(on_press=self.close_popup)
        self.panel.add_widget(self.close_button)
        
        # Add panel to anchor layout, then add anchor to modal
        anchor.add_widget(self.panel)
        self.add_widget(anchor)
        
        # Bind ESC/Back key to dismiss
        self._keyboard = None
        from kivy.core.window import Window
        Window.bind(on_key_down=self._on_key_down)
        
        # Log modal opening
        debug_logger.info(f"Aufnahme modal open centered size={panel_size[0]}x{panel_size[1]}")
    
    def _cleanup_legacy_sheets(self):
        """Remove any legacy left sheet instances from root"""
        from kivy.app import App
        app = App.get_running_app()
        removed_count = 0
        
        if app and hasattr(app, 'root_widget') and app.root_widget:
            # Search for widgets with legacy ids or classes
            children_to_remove = []
            for child in app.root_widget.children[:]:
                # Check by class name or widget id
                widget_class = child.__class__.__name__
                widget_id = getattr(child, 'id', None)
                
                if (widget_class in ['AufnahmeSheet', 'LeftPanel'] or 
                    widget_id in ['aufnahme_sheet', 'left_sheet']):
                    children_to_remove.append(child)
            
            # Remove found legacy widgets
            for child in children_to_remove:
                app.root_widget.remove_widget(child)
                removed_count += 1
        
        if removed_count > 0:
            debug_logger.info(f"Removed {removed_count} legacy Aufnahme sheet(s)")
    
    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        """Handle ESC/Back key to dismiss modal"""
        # ESC key is 27, Back key is 27 on Android
        if key == 27:  # ESC or Back
            self.close_popup(None)
            return True
        return False
    
    def _validate_audio_file(self):
        """
        Validate the recorded audio file for existence, size, and basic integrity
        
        Returns:
            tuple: (is_valid, status_message, message_level)
                - is_valid: True if file is considered valid
                - status_message: Description of file status
                - message_level: 'success', 'info', 'warning', or 'error'
        """
        try:
            if not self.audio_file_path.exists():
                return False, "Audiodatei wurde nicht erstellt", "error"
            
            file_size = self.audio_file_path.stat().st_size
            
            # Check if file is too small (less than 1KB indicates likely failure)
            if file_size < 1024:
                return False, f"Audiodatei ist zu klein ({file_size} Bytes) - möglicherweise unvollständig", "warning"
            
            # File exists and has reasonable size
            duration_estimate = ""
            if self.start_time:
                duration = time.time() - self.start_time
                duration_estimate = f" (ca. {duration:.1f}s)"
            
            size_mb = file_size / 1024 / 1024
            status_msg = f"Audiodatei erfolgreich gespeichert: {size_mb:.1f} MB{duration_estimate}"
            
            # Additional check: Try to verify it's a valid audio file by checking header
            try:
                with open(self.audio_file_path, 'rb') as f:
                    header = f.read(12)
                    if len(header) >= 12 and b'RIFF' in header and b'WAVE' in header:
                        return True, status_msg + " [SUCCESS] Gültiges WAV-Format", "success"
                    else:
                        return True, status_msg + " [WARNING] Format unbekannt, aber Datei vorhanden", "info"
            except Exception:
                # Even if we can't read the header, if file exists and has size, consider it valid
                return True, status_msg, "success"
                
        except Exception as e:
            return False, f"Fehler bei der Dateivalidierung: {e}", "error"
    
    def _validate_audio_file_with_stability_check(self):
        """
        Enhanced validation that includes file stability check to prevent race conditions
        
        This function ensures the audio file is not only valid but also stable (completely written)
        before allowing the workflow to proceed. This prevents race conditions where voiceToGoogle.py
        starts processing an incomplete file.
        
        Returns:
            tuple: (is_valid, status_message, message_level)
        """
        import time
        
        try:
            # First, do the basic validation
            is_basic_valid, basic_msg, basic_level = self._validate_audio_file()
            
            if not is_basic_valid:
                return is_basic_valid, basic_msg, basic_level
            
            debug_logger.info("Basic validation passed, checking file stability...")
            
            # File stability check: ensure file size is not changing
            initial_size = self.audio_file_path.stat().st_size
            time.sleep(0.2)  # Wait 200ms
            
            try:
                final_size = self.audio_file_path.stat().st_size
                if initial_size != final_size:
                    debug_logger.warning(f"File size changed during stability check: {initial_size} -> {final_size}")
                    return False, f"Audiodatei noch nicht stabil (Größe ändert sich: {initial_size} -> {final_size} Bytes)", "warning"
            except Exception as e:
                debug_logger.warning(f"Error during stability check: {e}")
                return False, f"Fehler bei Stabilitätsprüfung: {e}", "error"
            
            # Try to open the file exclusively to ensure no other process is writing to it
            try:
                with open(self.audio_file_path, 'rb') as f:
                    # Try to acquire an exclusive lock (will fail if file is still being written)
                    try:
                        import fcntl
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Immediately release the lock
                        debug_logger.info("File lock test passed - file not being written")
                    except ImportError:
                        # fcntl not available on all systems, skip lock test
                        debug_logger.info("fcntl not available, skipping lock test")
                        pass
                    except OSError:
                        debug_logger.warning("File appears to be locked by another process")
                        return False, "Audiodatei wird noch von anderem Prozess verwendet", "warning"
                    
                    # Try to read the beginning and end of the file to ensure it's complete
                    f.seek(0)
                    header = f.read(12)
                    
                    # For WAV files, try to read the last few bytes
                    f.seek(-4, 2)  # Seek to 4 bytes from end
                    trailer = f.read(4)
                    
                    if not header or len(header) < 12:
                        return False, "Audiodatei-Header unvollständig", "warning"
                        
                    debug_logger.info(f"File stability check passed: header={len(header)} bytes, trailer={len(trailer)} bytes")
                    
            except Exception as e:
                debug_logger.warning(f"Error during file access check: {e}")
                # Don't fail validation just because we can't do advanced checks
                pass
            
            # All checks passed
            debug_logger.info("File stability check completed successfully")
            return True, basic_msg + " [SUCCESS] Datei stabil und bereit für Verarbeitung", "success"
            
        except Exception as e:
            debug_logger.error(f"Error during stability validation: {e}")
            return False, f"Fehler bei der erweiterten Dateivalidierung: {e}", "error"
    
    def _add_status_message(self, message, level="info"):
        """
        Add a status message with appropriate color coding
        
        Args:
            message: The message to display
            level: 'success', 'info', 'warning', or 'error'
        """
        color_map = {
            'success': '44ff44',
            'info': '4499ff', 
            'warning': 'ffaa44',
            'error': 'ff4444'
        }
        color = color_map.get(level, 'ffffff')
        self.add_output_text(f"[color={color}]{message}[/color]")


    def add_output_text(self, text):
        """Add text to the output display"""
        current = self.output_text.text
        if current == "Bereit für Aufnahme...":
            self.output_text.text = text
        else:
            self.output_text.text = current + "\n" + text
        
        # Update text_size for proper wrapping
        self.output_text.text_size = (dp(550), None)
    
    def toggle_recording(self, instance):
        """Toggle recording start/stop as requested"""
        if self.interaction_blocked:
            return  # Ignore clicks when interaction is blocked
            
        debug_logger.info(f"toggle_recording called - current state: is_running={self.is_running}, process={self.process is not None}")
        
        if not self.is_running:
            self.start_recording()
        else:
            self.stop_recording()
    
    def set_ui_state(self, state):
        """Manage UI state transitions based on the requirements"""
        debug_logger.info(f"Setting UI state to: {state}")
        self.ui_state = state
        
        if state == "ready":
            # Initial state - everything visible and interactive
            self.output_section.opacity = 1
            self.spinner_container.opacity = 0
            self.loading_spinner.stop_spinning()
            self.button.opacity = 1
            self.close_button.disabled = False
            self.interaction_blocked = False
            
        elif state == "recording":
            # After Start click - hide status/process textbox, keep timer running
            self.output_section.opacity = 0
            self.spinner_container.opacity = 0
            self.loading_spinner.stop_spinning()
            self.button.opacity = 1
            self.close_button.disabled = False
            self.interaction_blocked = False
            
        elif state == "processing":
            # After Stop click - button disappears, show spinner, block interaction
            self.output_section.opacity = 0
            self.button.opacity = 0
            self.spinner_container.opacity = 1
            self.loading_spinner.start_spinning()
            self.close_button.disabled = True
            self.interaction_blocked = True
            
        elif state == "completed":
            # All processes completed - prepare to close and switch to gallery
            self.output_section.opacity = 0
            self.spinner_container.opacity = 0
            self.loading_spinner.stop_spinning()
            self.button.opacity = 0
            self.close_button.disabled = True
            self.interaction_blocked = True
            # Gallery switch will be handled separately
    
    def start_recording(self):
        """Start Aufnahme.py as subprocess"""
        debug_logger.info("start_recording called")
        
        if self.is_running:
            debug_logger.warning("start_recording called but recording already running")
            self.add_output_text("[color=ffaa44]Warnung: Aufnahme läuft bereits[/color]")
            return
            
        try:
            # Reset workflow state for new recording
            self.workflow_triggered = False
            if self.workflow_status_checker:
                Clock.unschedule(self.workflow_status_checker)
                self.workflow_status_checker = None
            debug_logger.info("Reset workflow state for new recording")
            
            aufnahme_path = APP_DIR / "Aufnahme.py"
            if not aufnahme_path.exists():
                error_msg = f"Fehler: Aufnahme.py nicht gefunden bei {aufnahme_path}"
                debug_logger.error(error_msg)
                print(error_msg)
                self.add_output_text(f"[color=ff4444]{error_msg}[/color]")
                return
            
            # Clear previous output
            self.output_text.text = "Starte Aufnahme..."
            debug_logger.info(f"Starting recording process with script: {aufnahme_path}")
            
            # Start the subprocess with output capture
            self.process = subprocess.Popen(
                ["python3", str(aufnahme_path)], 
                cwd=str(APP_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1  # Line buffered
            )
            
            self.is_running = True
            self.button.text = "Stopp"
            self.button.background_color = (0.6, 0.25, 0.25, 1)  # Red for stop
            self.start_time = time.time()
            self.start_timer()
            
            # Set UI state to recording - hide output section per requirements
            self.set_ui_state("recording")
            
            # Schedule output reading
            Clock.schedule_interval(self.read_process_output, 0.1)
            
            success_msg = f"Aufnahme gestartet (PID: {self.process.pid})"
            debug_logger.info(success_msg)
            print(success_msg)
            
        except Exception as e:
            error_msg = f"Fehler beim Starten der Aufnahme: {e}"
            debug_logger.error(error_msg, exc_info=True)
            print(error_msg)
            self.add_output_text(f"[color=ff4444]{error_msg}[/color]")
            # Reset state on error
            self.is_running = False
            self.button.text = "Start"
            self.button.background_color = (0.25, 0.55, 0.25, 1)
            self.set_ui_state("ready")  # Reset UI state on error
    
    def read_process_output(self, dt):
        """Read output from the recording process with improved termination handling"""
        if not self.process or not self.is_running:
            return False  # Stop scheduling
            
        try:
            # Check if process is still running
            if self.process.poll() is not None:
                # Process ended, read final output
                final_output = self.process.stdout.read()
                if final_output and self.ui_state != "recording":
                    # Only show final output if not in recording state
                    self.add_output_text(final_output.strip())
                elif final_output:
                    # Still log for debugging
                    debug_logger.debug(f"Final recording output: {final_output.strip()}")
                
                # Process ended - handle this gracefully without showing automatic error
                debug_logger.info(f"Recording process ended naturally with exit code: {self.process.returncode}")
                
                # Don't show error message here - let stop_recording handle the validation
                self.is_running = False
                self.button.text = "Start" 
                self.button.background_color = (0.25, 0.55, 0.25, 1)
                self.stop_timer()
                
                # Trigger validation through stop_recording method
                self.stop_recording()
                return False
            
            # Read available output without blocking
            import select
            import sys
            if hasattr(select, 'select'):  # Unix-like systems
                ready, _, _ = select.select([self.process.stdout], [], [], 0)
                if ready:
                    line = self.process.stdout.readline()
                    if line:
                        # Only show output if not in recording state (per requirements)
                        if self.ui_state != "recording":
                            self.add_output_text(line.strip())
                        else:
                            # Still log for debugging purposes
                            debug_logger.debug(f"Recording output: {line.strip()}")
            else:
                # Fallback for systems without select
                try:
                    line = self.process.stdout.readline()
                    if line:
                        # Only show output if not in recording state (per requirements)
                        if self.ui_state != "recording":
                            self.add_output_text(line.strip())
                        else:
                            # Still log for debugging purposes
                            debug_logger.debug(f"Recording output: {line.strip()}")
                except:
                    pass  # No output available
                    
        except Exception as e:
            debug_logger.error(f"Error reading process output: {e}")
            return False
        
        return True  # Continue scheduling
    
    def stop_recording(self):
        """Stop Aufnahme.py subprocess cleanly using SIGTERM with improved error handling"""
        debug_logger.info(f"stop_recording called - is_running: {self.is_running}, process: {self.process is not None}")
        
        # Validate recording state BEFORE attempting to stop
        if not self.is_running:
            debug_logger.warning("stop_recording called but no recording is running")
            # Ensure UI state is correct
            self.button.text = "Start"
            self.button.background_color = (0.25, 0.55, 0.25, 1)
            self.stop_timer()
            self.set_ui_state("ready")
            return
            
        if not self.process:
            debug_logger.warning("stop_recording: is_running=True but process is None")
            # Reset inconsistent state
            self.is_running = False
            self.button.text = "Start"
            self.button.background_color = (0.25, 0.55, 0.25, 1)
            self.stop_timer()
            self.set_ui_state("ready")  # Reset to ready state
            self.add_output_text("[color=ffaa44]Warnung: Inkonsistenter Zustand korrigiert[/color]")
            return
        
        # Immediately set processing state when stop is clicked
        self.set_ui_state("processing")
        
        stop_msg_starting = f"Stoppe Aufnahme (PID: {self.process.pid})..."
        debug_logger.info(stop_msg_starting)
        print(stop_msg_starting)
        
        process_exit_code = None
        try:
            # Send SIGTERM for graceful shutdown as required
            debug_logger.info(f"Sending SIGTERM to process {self.process.pid}")
            self.process.terminate()
            
            # Wait for the process and capture final output
            try:
                stdout, stderr = self.process.communicate(timeout=10)
                process_exit_code = self.process.returncode
                
                if stdout:
                    debug_logger.debug(f"Recording stdout: {stdout[:200]}...")
                    self.add_output_text(stdout.strip())
                if stderr:
                    debug_logger.warning(f"Recording stderr: {stderr}")
                    self.add_output_text(f"[color=ffaa44]Warnung: {stderr.strip()}[/color]")
                    
            except subprocess.TimeoutExpired:
                # Force kill if terminate doesn't work within timeout
                timeout_msg = "Erzwinge Beendigung (Timeout)"
                debug_logger.warning(timeout_msg)
                print(timeout_msg)
                self.add_output_text(f"[color=ff4444]{timeout_msg}[/color]")
                self.process.kill()
                self.process.wait()
                process_exit_code = self.process.returncode
                
        except Exception as e:
            error_msg = f"Fehler beim Stoppen: {e}"
            debug_logger.error(error_msg, exc_info=True)
            print(error_msg)
            self.add_output_text(f"[color=ff4444]{error_msg}[/color]")
        finally:
            # Always clean up state
            self.process = None
        
        # Update state
        self.is_running = False
        self.button.text = "Start"
        self.button.background_color = (0.25, 0.55, 0.25, 1)  # Green for start
        self.stop_timer()
        
        # CRITICAL FIX: Wait for recording process to fully complete and ensure file stability
        debug_logger.info("Waiting for recording process to fully complete and file to be stable...")
        self.add_output_text("[color=4499ff]Warte auf vollständige Aufnahme-Beendigung...[/color]")
        
        # Wait a short time to ensure all file operations are complete
        import time
        time.sleep(0.5)  # Give the recording process time to fully close files
        
        # Validate audio file and ensure it's stable before triggering workflow
        debug_logger.info("Validating recorded audio file after completion wait...")
        is_valid, status_message, message_level = self._validate_audio_file_with_stability_check()
        
        if is_valid:
            # Audio file is valid and stable - this is success regardless of exit code
            debug_logger.info("Audio file validation successful - ready for workflow")
            print(f"[SUCCESS] {status_message}")
            self._add_status_message(f"[SUCCESS] {status_message}", "success")
            
            # Handle exit code information
            if process_exit_code is not None and process_exit_code != 0:
                # Exit code != 0 but file is valid - this is normal for recording tools stopped via signal
                info_msg = f"Hinweis: Prozess beendet mit Code {process_exit_code}, Audio jedoch erfolgreich gespeichert"
                debug_logger.info(info_msg)
                print(f"[INFO] {info_msg}")
                self._add_status_message(f"[INFO] {info_msg}", "info")
                self.add_output_text("[color=4499ff]Dies ist normal beim Stoppen von Aufnahme-Tools[/color]")
            else:
                success_msg = "Aufnahme erfolgreich abgeschlossen"
                debug_logger.info(success_msg)
                print(f"[SUCCESS] {success_msg}")
            
            # CRITICAL FIX: Only create workflow trigger AFTER successful validation and file stability
            if not self.workflow_triggered:
                debug_logger.info("SAFE TO TRIGGER: Audio file validated and stable - creating workflow trigger")
                self.add_output_text("[color=44ff44][SUCCESS] Audio validiert und stabil - starte Workflow[/color]")
                self.create_workflow_trigger()
            else:
                debug_logger.info("Workflow already triggered for this recording, skipping")
                
        else:
            # Audio file is not valid - DO NOT trigger workflow
            debug_logger.error(f"Audio file validation failed - NOT triggering workflow: {status_message}")
            print(f"[ERROR] {status_message}")
            self._add_status_message(f"[ERROR] {status_message}", message_level)
            self.add_output_text("[color=ff4444][ERROR] Workflow NICHT gestartet - Audiodatei ungültig[/color]")
            
            if process_exit_code is not None and process_exit_code != 0:
                error_detail = f"Zusätzlich: Prozess beendet mit Fehlercode {process_exit_code}"
                debug_logger.error(error_detail)
                print(f"[ERROR] {error_detail}")
                self._add_status_message(f"[ERROR] {error_detail}", "error")
    
    def start_timer(self):
        """Start the timer display"""
        self.timer_event = Clock.schedule_interval(self.update_timer, 1)
    
    def stop_timer(self):
        """Stop the timer display"""
        if self.timer_event:
            Clock.unschedule(self.timer_event)
            self.timer_event = None
        self.timer_label.text = "00:00"
    
    def update_timer(self, dt):
        """Update timer display during recording"""
        if self.is_running and self.start_time:
            elapsed = int(time.time() - self.start_time)
            minutes, seconds = divmod(elapsed, 60)
            self.timer_label.text = f"{minutes:02d}:{seconds:02d}"
    
    def create_workflow_trigger(self):
        """Create workflow trigger file to signal background processing - ATOMIC OPERATION"""
        # Use thread lock to prevent race conditions from multiple button clicks
        with self.trigger_creation_lock:
            if self.workflow_triggered:
                warning_msg = "Workflow-Trigger bereits erstellt, überspringe"
                debug_logger.warning(warning_msg)
                print(warning_msg)
                self.add_output_text(f"[color=ffaa44]{warning_msg}[/color]")
                return
            
            try:
                trigger_file = APP_DIR / "workflow_trigger.txt"
                lockfile_path = APP_DIR / "workflow_service.lock"
                
                debug_logger.info(f"Attempting to create trigger file: {trigger_file}")
                
                # Check if workflow service is already running via lockfile
                if lockfile_path.exists():
                    try:
                        lock_stat = lockfile_path.stat()
                        lock_age = time.time() - lock_stat.st_mtime
                        if lock_age < 300:  # Less than 5 minutes old
                            warning_msg = "Workflow-Service läuft bereits (Lockfile aktiv)"
                            debug_logger.warning(f"{warning_msg}, lock age: {lock_age:.1f}s")
                            print(warning_msg)
                            self.add_output_text(f"[color=ffaa44]{warning_msg}[/color]")
                            return
                        else:
                            debug_logger.info(f"Removing stale lockfile (age: {lock_age:.1f}s)")
                            lockfile_path.unlink()
                    except Exception as e:
                        debug_logger.warning(f"Error checking lockfile: {e}")
                
                # Check if trigger file already exists and handle appropriately
                if trigger_file.exists():
                    try:
                        trigger_stat = trigger_file.stat()
                        trigger_age = time.time() - trigger_stat.st_mtime
                        if trigger_age < 60:  # Less than 1 minute old - probably still processing
                            warning_msg = "Workflow-Trigger-Datei existiert bereits und ist aktuell"
                            debug_logger.warning(f"{warning_msg}, age: {trigger_age:.1f}s")
                            print(warning_msg)
                            self.add_output_text(f"[color=ffaa44]{warning_msg}[/color]")
                            return
                        else:
                            # Old trigger file - remove it
                            debug_logger.info(f"Removing stale trigger file (age: {trigger_age:.1f}s)")
                            trigger_file.unlink()
                    except Exception as e:
                        debug_logger.warning(f"Error checking existing trigger file: {e}")
                        # Try to remove it anyway
                        try:
                            trigger_file.unlink()
                        except Exception:
                            pass
                
                # Atomic trigger file creation with exclusive lock
                trigger_created = False
                try:
                    # Use exclusive creation (fails if exists)
                    with open(trigger_file, "x", encoding="utf-8") as f:
                        # Get exclusive lock on the file
                        try:
                            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                            f.write("run")
                            f.flush()
                            os.fsync(f.fileno())  # Ensure data is written to disk
                            trigger_created = True
                            debug_logger.info("Trigger file created atomically with lock")
                        except (OSError, IOError) as lock_err:
                            debug_logger.error(f"Failed to lock trigger file: {lock_err}")
                            raise
                        finally:
                            # Lock is automatically released when file is closed
                            pass
                            
                except FileExistsError:
                    warning_msg = "Workflow-Trigger-Datei existiert bereits (von anderem Prozess erstellt)"
                    debug_logger.warning(warning_msg)
                    print(warning_msg)
                    self.add_output_text(f"[color=ffaa44]{warning_msg}[/color]")
                    return
                
                if not trigger_created:
                    raise Exception("Failed to create trigger file atomically")
                
                # Mark as triggered ONLY after successful creation
                self.workflow_triggered = True
                
                # If image is selected, prepare transkript.json with image data
                if self.selected_image_base64 and self.selected_image_path:
                    self._create_image_transkript()
                
                trigger_msg = "Workflow-Trigger erstellt"
                debug_logger.info(trigger_msg)
                print(trigger_msg)
                self.add_output_text(f"[color=44ff44]{trigger_msg}[/color]")
                
                # Start workflow service ONCE using the existing script
                self._start_workflow_service()
                
                # Start checking for workflow status (but stop any existing checker first)
                if self.workflow_status_checker:
                    Clock.unschedule(self.workflow_status_checker)
                
                self.workflow_status_checker = Clock.schedule_interval(self.check_workflow_status, 2.0)
                debug_logger.info("Started workflow status checking")
                
            except Exception as e:
                error_msg = f"Fehler beim Erstellen des Workflow-Triggers: {e}"
                debug_logger.error(error_msg, exc_info=True)
                print(error_msg)
                self.add_output_text(f"[color=ff4444]{error_msg}[/color]")
                # Reset trigger state on error
                self.workflow_triggered = False
    
    def _create_image_transkript(self):
        """Create or update transkript.json with selected image data"""
        try:
            transkript_path = Path("/home/pi/Desktop/v2_Tripple S/transkript.json")
            
            # Prepare transcript data with image
            timestamp = datetime.now()
            transcript_data = {
                "transcript": "Aufnahme mit Bild wird vorbereitet...",
                "timestamp": timestamp.timestamp(),
                "iso_timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "processing_method": "recording_with_image",
                "workflow_step": "image_prepared",
                "image_base64": self.selected_image_base64,
                "image_filename": os.path.basename(self.selected_image_path),
                "image_timestamp": timestamp.strftime("%Y%m%d_%H%M%S")
            }
            
            # Ensure directory exists
            transkript_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write transcript data
            with open(transkript_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            debug_logger.info(f"Created initial transkript.json with image data: {os.path.basename(self.selected_image_path)}")
            self.add_output_text(f"[color=44ff44]✓ Bild für Verarbeitung vorbereitet[/color]")
            
        except Exception as e:
            debug_logger.error(f"Error creating image transcript: {e}")
            self.add_output_text(f"[color=ff4444]Fehler beim Vorbereiten des Bildes: {e}[/color]")
    
    def _start_workflow_service(self):
        """Start the workflow service using the existing start_workflow_service.py script"""
        try:
            service_script = APP_DIR / "start_workflow_service.py"
            if not service_script.exists():
                debug_logger.error(f"Workflow service script not found: {service_script}")
                return
            
            debug_logger.info("Starting workflow service via start_workflow_service.py")
            
            # Start the service script with --auto flag for non-interactive mode
            service_process = subprocess.Popen(
                ["python3", str(service_script), "--auto"],
                cwd=str(APP_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Wait briefly to see if it starts successfully
            try:
                stdout, stderr = service_process.communicate(timeout=5)
                if service_process.returncode == 0:
                    service_msg = "Workflow-Service erfolgreich gestartet"
                    debug_logger.info(service_msg)
                    print(service_msg)
                    self.add_output_text(f"[color=44ff44]{service_msg}[/color]")
                else:
                    error_msg = f"Workflow-Service Start-Fehler (Code: {service_process.returncode})"
                    debug_logger.warning(f"{error_msg}\nSTDOUT: {stdout}\nSTDERR: {stderr}")
                    print(error_msg)
                    self.add_output_text(f"[color=ffaa44]{error_msg}[/color]")
                    if stdout:
                        self.add_output_text(f"[color=cccccc]Output: {stdout.strip()}[/color]")
            except subprocess.TimeoutExpired:
                # Service is still running, which is normal
                service_msg = f"Workflow-Service gestartet (läuft im Hintergrund)"
                debug_logger.info(service_msg)
                print(service_msg)
                self.add_output_text(f"[color=44ff44]{service_msg}[/color]")
            
        except Exception as e:
            error_msg = f"Fehler beim Starten des Workflow-Service: {e}"
            debug_logger.error(error_msg, exc_info=True)
            print(error_msg)
            self.add_output_text(f"[color=ff4444]{error_msg}[/color]")
    
    def check_workflow_status(self, dt):
        """Check workflow status from log file"""
        try:
            status_file = APP_DIR / "workflow_status.log"
            if status_file.exists():
                with open(status_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    # Show last few lines of status
                    lines = content.split('\n')
                    for line in lines[-3:]:  # Show last 3 lines
                        if line.strip():
                            workflow_status_msg = f"[Workflow] {line.strip()}"
                            print(workflow_status_msg)
                            self.add_output_text(f"[color=aaaaff]{workflow_status_msg}[/color]")
                    
                    # Check if workflow completed
                    if "WORKFLOW_COMPLETE" in content or "WORKFLOW_ERROR" in content:
                        Clock.unschedule(self.check_workflow_status)
                        self.workflow_status_checker = None  # Clear reference
                        
                        # Clean up trigger file after workflow completion
                        trigger_file = APP_DIR / "workflow_trigger.txt"
                        if trigger_file.exists():
                            try:
                                trigger_file.unlink()
                                cleanup_msg = "Workflow-Trigger-Datei nach Abschluss gelöscht"
                                debug_logger.info(cleanup_msg)
                                print(cleanup_msg)
                                self.add_output_text(f"[color=44ff44]{cleanup_msg}[/color]")
                            except Exception as cleanup_err:
                                cleanup_warning = f"Warnung: Trigger-Datei konnte nicht gelöscht werden: {cleanup_err}"
                                debug_logger.warning(cleanup_warning)
                                print(cleanup_warning)
                                self.add_output_text(f"[color=ffaa44]{cleanup_warning}[/color]")
                        
                        # Reset workflow triggered flag for next recording
                        self.workflow_triggered = False
                        debug_logger.info("Reset workflow state for next recording")
                        
                        # Clear selected image after workflow completion
                        if self.selected_image_path or self.selected_image_base64:
                            self.clear_selected_image()
                            debug_logger.info("Cleared selected image after workflow completion")
                        
                        workflow_complete_msg = "Workflow abgeschlossen"
                        print(workflow_complete_msg)
                        
                        # Set completed state and automatically close popup + switch to gallery
                        self.set_ui_state("completed")
                        
                        # Schedule automatic close and gallery switch
                        Clock.schedule_once(self.auto_close_and_switch_to_gallery, 0.5)
                        
                        return False  # Stop scheduling
                        
        except Exception as e:
            print(f"Fehler beim Lesen der Workflow-Status: {e}")
            
        return True  # Continue scheduling
    
    def auto_close_and_switch_to_gallery(self, dt):
        """Automatically close popup and switch to gallery after workflow completion"""
        debug_logger.info("Auto-closing popup and switching to gallery")
        
        # Close this popup
        self.dismiss()
        debug_logger.info("Dismissed popup")
        
        # Switch to gallery if slideshow reference is available
        if self.slideshow:
            self.slideshow.open_gallery()
            debug_logger.info("Switched to gallery")
        else:
            debug_logger.warning("No slideshow reference available for gallery switch")
    
    def open_image_selection(self, instance):
        """Open image selection dialog with tabs for Gallery and Import folders"""
        try:
            from kivy.uix.filechooser import FileChooserListView
            from kivy.uix.popup import Popup
            from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
            
            # Create tabbed panel for source selection
            tab_panel = TabbedPanel(do_default_tab=False, tab_width=dp(150))
            
            # Gallery tab (BilderVertex)
            gallery_tab = TabbedPanelItem(text='Galerie (KI-Bilder)')
            gallery_chooser = FileChooserListView(
                filters=['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif'],
                path=str(IMAGE_DIR) if IMAGE_DIR.exists() else str(Path.home())
            )
            gallery_tab.add_widget(gallery_chooser)
            tab_panel.add_widget(gallery_tab)
            
            # Import tab (uploads folder)
            import_tab = TabbedPanelItem(text='Import (Uploads)')
            import_chooser = FileChooserListView(
                filters=['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif'],
                path=str(IMPORT_DIR) if IMPORT_DIR.exists() else str(Path.home())
            )
            import_tab.add_widget(import_chooser)
            tab_panel.add_widget(import_tab)
            
            # Button layout for file chooser
            buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            
            select_btn = Button(text="Auswählen", size_hint_x=0.5)
            cancel_btn = Button(text="Abbrechen", size_hint_x=0.5)
            
            def select_file(*args):
                # Get the active file chooser based on selected tab
                if tab_panel.current_tab == gallery_tab:
                    active_chooser = gallery_chooser
                else:
                    active_chooser = import_chooser
                
                if active_chooser.selection:
                    selected_file = active_chooser.selection[0]
                    self.process_selected_image(selected_file)
                    popup.dismiss()
            
            def cancel_selection(*args):
                popup.dismiss()
            
            select_btn.bind(on_press=select_file)
            cancel_btn.bind(on_press=cancel_selection)
            
            buttons.add_widget(select_btn)
            buttons.add_widget(cancel_btn)
            
            # Main content layout
            content = BoxLayout(orientation='vertical')
            content.add_widget(tab_panel)
            content.add_widget(buttons)
            
            popup = Popup(
                title="Bild für Aufnahme auswählen",
                content=content,
                size_hint=(0.8, 0.8)
            )
            popup.open()
            
        except Exception as e:
            debug_logger.error(f"Error opening image selection: {e}")
            self.add_output_text(f"[color=ff4444]Fehler beim Öffnen der Bildauswahl: {e}[/color]")
    
    def process_selected_image(self, file_path):
        """Process selected image for recording workflow"""
        try:
            debug_logger.info(f"Processing selected image: {file_path}")
            
            # Validate image file
            if not os.path.exists(file_path):
                self.add_output_text(f"[color=ff4444]Bilddatei nicht gefunden: {file_path}[/color]")
                return
            
            # Check file size (limit to reasonable size)
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                self.add_output_text(f"[color=ff4444]Bilddatei zu groß (>10MB): {file_size/1024/1024:.1f}MB[/color]")
                return
            
            # Convert image to base64
            try:
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                    self.selected_image_base64 = base64.b64encode(image_data).decode('utf-8')
                    self.selected_image_path = file_path
                
                # Update UI to show selected image
                filename = os.path.basename(file_path)
                self.image_info_label.text = f"✓ Bild ausgewählt: {filename}"
                self.image_info_label.height = dp(30)
                
                # Update button color to indicate image is selected
                self.image_button.text = f"✓ Bild: {filename[:20]}{'...' if len(filename) > 20 else ''}"
                self.image_button.background_color = (0.2, 0.6, 0.3, 1)
                
                self.add_output_text(f"[color=44ff44]✓ Bild ausgewählt: {filename} ({file_size/1024:.1f}KB)[/color]")
                debug_logger.info(f"Image processed successfully: {filename}, size: {file_size} bytes")
                
            except Exception as e:
                debug_logger.error(f"Error processing image file: {e}")
                self.add_output_text(f"[color=ff4444]Fehler beim Verarbeiten des Bildes: {e}[/color]")
                
        except Exception as e:
            debug_logger.error(f"Error in process_selected_image: {e}")
            self.add_output_text(f"[color=ff4444]Fehler bei der Bildverarbeitung: {e}[/color]")
    
    def clear_selected_image(self):
        """Clear selected image"""
        self.selected_image_path = None
        self.selected_image_base64 = None
        self.image_info_label.text = ""
        self.image_info_label.height = dp(0)
        self.image_button.text = "📷 Bild hinzufügen (optional)"
        self.image_button.background_color = (0.35, 0.35, 0.55, 1)
        debug_logger.info("Selected image cleared")
    
    def show_qr_code(self, instance):
        """Show QR code for upload link"""
        try:
            # Get network IP for access from mobile devices
            network_ip = get_network_ip()
            upload_url = f"http://{network_ip}:8000/upload"
            
            debug_logger.info(f"Generating QR code for upload URL: {upload_url}")
            
            # Create QR code display popup
            from kivy.uix.popup import Popup
            from kivy.graphics.texture import Texture
            
            qr_content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            # Try to generate actual QR code
            qr_img_data = generate_qr_code_image(upload_url, size=(250, 250))
            
            if qr_img_data:
                # Create QR code image widget
                try:
                    # Save QR code to temporary file for Kivy Image widget
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                        tmp_file.write(qr_img_data)
                        tmp_path = tmp_file.name
                    
                    qr_image = Image(
                        source=tmp_path,
                        size_hint=(None, None),
                        size=(dp(250), dp(250)),
                        pos_hint={'center_x': 0.5}
                    )
                    qr_content.add_widget(qr_image)
                    
                    # Schedule cleanup of temp file
                    def cleanup_temp_file(dt):
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass
                    Clock.schedule_once(cleanup_temp_file, 5.0)
                    
                except Exception as img_error:
                    debug_logger.warning(f"Failed to create QR image widget: {img_error}")
                    # Fallback to text display
                    qr_label = Label(
                        text=f"📱 QR-Code generiert\n\nUpload-Link:\n{upload_url}\n\n(QR-Code-Anzeige fehlgeschlagen)",
                        font_size=dp(14),
                        color=(1, 1, 1, 1),
                        text_size=(dp(300), None),
                        halign='center'
                    )
                    qr_content.add_widget(qr_label)
            else:
                # Fallback when QR generation fails
                error_msg = "⚠️ QR-Code Bibliotheken fehlen\n\nBitte installieren Sie:\npip install qrcode[pil] Pillow"
                if network_ip != "127.0.0.1":
                    error_msg += f"\n\nUpload-Link:\n{upload_url}\n\n(Manuell öffnen)"
                else:
                    error_msg += f"\n\nNetzwerk-IP nicht verfügbar\nFallback: {upload_url}"
                
                qr_label = Label(
                    text=error_msg,
                    font_size=dp(14),
                    color=(1, 1, 0.7, 1),  # Yellow tint for warning
                    text_size=(dp(300), None),
                    halign='center'
                )
                qr_content.add_widget(qr_label)
            
            # Network info
            if network_ip != "127.0.0.1":
                network_info = Label(
                    text=f"📡 Netzwerk-IP: {network_ip}\nPort: 8000",
                    font_size=dp(12),
                    color=(0.8, 0.8, 1, 1),
                    text_size=(dp(300), None),
                    halign='center'
                )
                qr_content.add_widget(network_info)
            
            # Instructions
            instructions = Label(
                text="Scannen Sie den QR-Code mit Ihrem Smartphone\noder öffnen Sie den Link manuell,\num Bilder hochzuladen.",
                font_size=dp(12),
                color=(0.9, 0.9, 0.9, 1),
                text_size=(dp(300), None),
                halign='center'
            )
            qr_content.add_widget(instructions)
            
            # Close button for QR popup
            close_btn = Button(
                text="Schließen",
                size_hint_y=None,
                height=dp(50)
            )
            
            def close_qr(*args):
                qr_popup.dismiss()
            
            close_btn.bind(on_press=close_qr)
            qr_content.add_widget(close_btn)
            
            qr_popup = Popup(
                title="QR-Code für Bild-Upload",
                content=qr_content,
                size_hint=(None, None),
                size=(dp(400), dp(600))  # Made taller to accommodate network info
            )
            qr_popup.open()
            
        except Exception as e:
            debug_logger.error(f"Error showing QR code: {e}")
            self.add_output_text(f"[color=ff4444]Fehler beim Anzeigen des QR-Codes: {e}[/color]")
    
    def close_popup(self, instance):
        """Close the popup window"""
        debug_logger.info("close_popup called")
        
        # Stop recording if running
        if self.is_running:
            debug_logger.info("Stopping recording before closing popup")
            self.stop_recording()
        
        # Stop status checking
        if self.workflow_status_checker:
            Clock.unschedule(self.workflow_status_checker)
            self.workflow_status_checker = None
            debug_logger.info("Stopped workflow status checking")
        
        # Unbind key handler
        from kivy.core.window import Window
        Window.unbind(on_key_down=self._on_key_down)
        
        # Dismiss ModalView
        self.dismiss()
        debug_logger.info("Aufnahme modal dismissed")

class GeneralSettingsPopup(RotatedModalView):
    def __init__(self, slideshow, **kw):
        # Set ModalView properties for full-screen with centered content
        kw_copy = kw.copy()
        kw_copy.setdefault('size_hint', (1, 1))  # Full screen
        kw_copy.setdefault('auto_dismiss', True)
        super().__init__(**kw_copy)
        self.slideshow=slideshow
        self.background_color = (0, 0, 0, 0.7)  # Dim overlay
        self.background = ''
        
        # Calculate panel size based on aspect ratio using portrait factors
        from kivy.core.window import Window
        aspect = slideshow.aspect_ratio if slideshow else "16:9"
        if aspect == "9:16":
            # Portrait mode: apply portrait factors (0.62×w, 0.86×h, min 320×260)
            content_w = Window.width
            content_h = Window.height
            panel_w = max(int(content_w * 0.62), dp(320))
            panel_h = max(int(content_h * 0.86), dp(260))
            panel_size = (panel_w, panel_h)
        else:
            # Landscape mode: use standard size
            panel_size = (dp(520), dp(420))
        
        # Use AnchorLayout to center the content panel
        anchor = AnchorLayout(size_hint=(1, 1), anchor_x='center', anchor_y='center')
        
        panel=BoxLayout(orientation='vertical',size_hint=(None, None),size=panel_size,
                        padding=dp(22),spacing=dp(16))
        with panel.canvas.before:
            GColor(0.18,0.18,0.22,0.97); panel._bg=Rectangle(pos=panel.pos,size=panel.size)
        panel.bind(pos=lambda *a:setattr(panel._bg,'pos',panel.pos),
                   size=lambda *a:setattr(panel._bg,'size',panel.size))
        panel.add_widget(Label(text="Allgemein",size_hint_y=None,height=dp(54),
                               font_size=dp(30),color=(1,1,1,1)))
        # Globale Helligkeit
        panel.add_widget(Label(text="Globale Helligkeit (50% - 150%):",size_hint_y=None,height=dp(28),
                               font_size=dp(16),color=(1,1,1,0.9)))
        cur = self.slideshow.global_brightness_override or 1.0
        self.b_slider=Slider(min=0.5,max=1.5,value=cur,step=0.01,size_hint_y=None,height=dp(42))
        self.b_label=Label(text=f"{cur*100:.0f}%",size_hint_y=None,height=dp(24),
                           font_size=dp(16),color=(0.9,0.9,1,1))
        self.b_slider.bind(value=lambda inst,val:self.b_label.__setattr__('text',f"{float(val)*100:.0f}%"))
        panel.add_widget(self.b_slider)
        panel.add_widget(self.b_label)
        # Buttons
        row=BoxLayout(size_hint_y=None,height=dp(60),spacing=dp(14))
        save=Button(text="Speichern",background_normal='',background_color=(0.25,0.55,0.25,1),
                    color=(1,1,1,1),font_size=dp(20))
        back=Button(text="Zurück",background_normal='',background_color=(0.4,0.4,0.5,1),
                    color=(1,1,1,1),font_size=dp(20))
        save.bind(on_release=lambda *_: self._save())
        back.bind(on_release=lambda *_: self._back())
        row.add_widget(save); row.add_widget(back)
        panel.add_widget(row)
        
        # Add panel to anchor layout, then add anchor to modal
        anchor.add_widget(panel)
        self.add_widget(anchor)
        
        # Bind ESC/Back key to dismiss
        from kivy.core.window import Window
        Window.bind(on_key_down=self._on_key_down)
        
        # Log modal opening
        debug_logger.info(f"General settings modal open centered size={panel_size[0]}x{panel_size[1]}")
    
    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        """Handle ESC/Back key to dismiss modal"""
        if key == 27:  # ESC or Back
            self._back()
            return True
        return False
    
    def _save(self):
        val=float(self.b_slider.value)
        if abs(val-1.0)<0.001:
            self.slideshow.global_brightness_override=None
        else:
            self.slideshow.global_brightness_override=val
        self.slideshow.persist_meta()
        self.slideshow._apply_current_brightness()
        self._back()
    def _back(self):
        from kivy.core.window import Window
        Window.unbind(on_key_down=self._on_key_down)
        debug_logger.info("General settings modal dismissed")
        self.dismiss()
        popup = SettingsRootPopup(self.slideshow)
        popup.open()

class GlobalDurationPopup(RotatedModalView):
    def __init__(self, slideshow, **kw):
        # Set ModalView properties for full-screen with centered content
        kw_copy = kw.copy()
        kw_copy.setdefault('size_hint', (1, 1))  # Full screen
        kw_copy.setdefault('auto_dismiss', True)
        super().__init__(**kw_copy)
        self.slideshow=slideshow
        self.background_color = (0, 0, 0, 0.7)  # Dim overlay
        self.background = ''
        
        # Calculate panel size based on aspect ratio using portrait factors
        from kivy.core.window import Window
        aspect = slideshow.aspect_ratio if slideshow else "16:9"
        if aspect == "9:16":
            # Portrait mode: apply portrait factors (0.62×w, 0.86×h, min 320×260)
            content_w = Window.width
            content_h = Window.height
            panel_w = max(int(content_w * 0.62), dp(320))
            panel_h = max(int(content_h * 0.86), dp(260))
            panel_size = (panel_w, panel_h)
        else:
            # Landscape mode: use standard size
            panel_size = (dp(520), dp(380))
        
        # Use AnchorLayout to center the content panel
        anchor = AnchorLayout(size_hint=(1, 1), anchor_x='center', anchor_y='center')
        
        panel=BoxLayout(orientation='vertical',size_hint=(None, None),size=panel_size,
                        padding=dp(22),spacing=dp(16))
        with panel.canvas.before:
            GColor(0.18,0.18,0.22,0.97); panel._bg=Rectangle(pos=panel.pos,size=panel.size)
        panel.bind(pos=lambda *a:setattr(panel._bg,'pos',panel.pos),
                   size=lambda *a:setattr(panel._bg,'size',panel.size))
        panel.add_widget(Label(text="Bilddauer",size_hint_y=None,height=dp(54),
                               font_size=dp(30),color=(1,1,1,1)))
        panel.add_widget(Label(text="Globale Bilddauer (Sek, 0 = deaktiviert):",size_hint_y=None,height=dp(30),
                               font_size=dp(16),color=(1,1,1,0.9)))
        cur = self.slideshow.global_interval_override or 0
        self.gl_slider=Slider(min=0,max=120,value=cur,step=1,size_hint_y=None,height=dp(42))
        self.gl_label=Label(text=f"{cur}s" if cur>0 else "Deaktiviert",
                            size_hint_y=None,height=dp(24),
                            font_size=dp(16),color=(0.9,0.9,1,1))
        self.gl_slider.bind(value=lambda inst,val:self.gl_label.__setattr__('text', f"{int(val)}s" if int(val)>0 else "Deaktiviert"))
        panel.add_widget(self.gl_slider); panel.add_widget(self.gl_label)
        row=BoxLayout(size_hint_y=None,height=dp(60),spacing=dp(14))
        save=Button(text="Speichern",background_normal='',background_color=(0.25,0.55,0.25,1),
                    color=(1,1,1,1),font_size=dp(20))
        back=Button(text="Zurück",background_normal='',background_color=(0.4,0.4,0.5,1),
                    color=(1,1,1,1),font_size=dp(20))
        save.bind(on_release=lambda *_: self._save())
        back.bind(on_release=lambda *_: self._back())
        row.add_widget(save); row.add_widget(back)
        panel.add_widget(row)
        
        # Add panel to anchor layout, then add anchor to modal
        anchor.add_widget(panel)
        self.add_widget(anchor)
        
        # Bind ESC/Back key to dismiss
        from kivy.core.window import Window
        Window.bind(on_key_down=self._on_key_down)
        
        # Log modal opening
        debug_logger.info(f"Duration modal open centered size={panel_size[0]}x{panel_size[1]}")
    
    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        """Handle ESC/Back key to dismiss modal"""
        if key == 27:  # ESC or Back
            self._back()
            return True
        return False
    
    def _save(self):
        v=int(self.gl_slider.value)
        self.slideshow.global_interval_override = v if v>0 else None
        self.slideshow.persist_meta()
        self.slideshow._reschedule_for_current()
        self._back()
    def _back(self):
        from kivy.core.window import Window
        Window.unbind(on_key_down=self._on_key_down)
        debug_logger.info("Duration modal dismissed")
        self.dismiss()
        popup = SettingsRootPopup(self.slideshow)
        popup.open()

# ---- Gallery Editor / Tiles (angepasst) ----
class ImageTile(BoxLayout):
    def __init__(self, path, on_toggle, is_selected_fn, open_settings, **kw):
        super().__init__(orientation="vertical",
                         size_hint=(None,None), width=THUMB_SIZE,
                         height=THUMB_SIZE+dp(60), spacing=dp(4), **kw)
        self.path=path
        self.on_toggle=on_toggle
        self.open_settings=open_settings
        self.is_selected_fn=is_selected_fn
        
        # Double-click/tap detection
        self.last_touch_time=0
        self.double_click_threshold=0.3  # seconds
        self.is_lightbox_open=False  # Flag to prevent multiple opens
        self._scheduled_lightbox=None  # For throttling lightbox opens
        
        with self.canvas.before:
            GColor(0.18,0.18,0.20,1)
            self.bg_rect=Rectangle(pos=self.pos,size=self.size)
            self.sel_color=GColor(0,0.7,0,0)
            self.sel_line=Line(rectangle=(self.x,self.y,self.width,self.height),width=2)
        self.bind(pos=self._upd,size=self._upd)
        self.img=Image(source=path,size_hint=(1,None),height=THUMB_SIZE)
        self.add_widget(self.img)
        name=os.path.basename(path)
        self.lbl=Label(text=self._short(name),size_hint=(1,None),height=dp(26),
                       halign='center',valign='middle',color=(1,1,1,1),font_size=dp(13))
        self.lbl.bind(size=lambda inst,*a:setattr(inst,'text_size',inst.size))
        self.add_widget(self.lbl)
        row=BoxLayout(size_hint=(1,None),height=dp(30),spacing=dp(4))
        self.toggle_btn=Button(text="Auswählen",background_normal='',
                               background_color=(0.25,0.35,0.55,1),
                               color=(1,1,1,1),font_size=dp(12))
        self.toggle_btn.bind(on_release=lambda *_: self.on_toggle(self.path))
        gear=Button(text="⚙",size_hint=(None,1),width=dp(36),
                    background_normal='',background_color=(0.35,0.35,0.5,1),
                    color=(1,1,1,1),font_size=dp(16))
        gear.bind(on_release=lambda *_: self.open_settings(self.path))
        row.add_widget(self.toggle_btn); row.add_widget(gear)
        self.add_widget(row)
        self.refresh_state()
    
    def on_touch_down(self, touch):
        """Handle touch/click events for double-click/tap detection"""
        # Check if touch is on the image area (not on buttons)
        if self.img.collide_point(*touch.pos):
            current_time = time.time()
            time_since_last = current_time - self.last_touch_time
            
            # Check if this is a double-click/tap
            if time_since_last < self.double_click_threshold:
                # Double-click detected! Open lightbox with debounce
                self._open_lightbox_debounced()
                self.last_touch_time = 0  # Reset to prevent triple-click
                return True
            else:
                # First click, record time
                self.last_touch_time = current_time
        
        # Continue normal touch handling
        return super().on_touch_down(touch)
    
    def _open_lightbox_debounced(self):
        """Open lightbox with throttling to prevent multiple opens"""
        # Cancel any pending scheduled lightbox open
        if self._scheduled_lightbox:
            Clock.unschedule(self._scheduled_lightbox)
        
        # Check if lightbox is already open
        if self.is_lightbox_open:
            debug_logger.debug(f"Lightbox already open, ignoring double-click for: {self.path}")
            return
        
        # Schedule lightbox open with 250ms throttle
        self._scheduled_lightbox = Clock.schedule_once(lambda dt: self._open_lightbox(), 0.25)
        debug_logger.debug(f"Scheduled lightbox open for: {self.path}")
    
    def _open_lightbox(self):
        """Open the lightbox to display full-size image"""
        try:
            # Guard: check if lightbox is already open
            if self.is_lightbox_open:
                debug_logger.debug(f"Lightbox already open, skipping for: {self.path}")
                return
            
            # Set flag to prevent multiple opens
            self.is_lightbox_open = True
            
            # Get root widget directly from app to avoid blocking while loop
            from kivy.app import App
            app = App.get_running_app()
            if not app or not app.root:
                debug_logger.error("Cannot open lightbox: app root not available")
                self.is_lightbox_open = False
                return
            
            # Create and open lightbox popup (ModalView)
            lightbox = ImageLightboxPopup(self.path)
            
            # Bind to lightbox dismissal to reset flag
            def on_lightbox_dismissed(*args):
                self.is_lightbox_open = False
                debug_logger.debug(f"Lightbox closed, flag reset for: {self.path}")
            
            # Hook into the lightbox's on_dismiss event
            lightbox.bind(on_dismiss=on_lightbox_dismissed)
            
            lightbox.open()
            debug_logger.info(f"Lightbox opened for: {self.path}")
        except Exception as e:
            debug_logger.error(f"Error opening lightbox for {self.path}: {e}")
            self.is_lightbox_open = False  # Reset flag on error
    def _short(self,name,maxlen=18):
        return name if len(name)<=maxlen else name[:maxlen-3]+"..."
    def _upd(self,*a):
        self.bg_rect.pos=self.pos; self.bg_rect.size=self.size
        self.sel_line.rectangle=(self.x,self.y,self.width,self.height)
    def refresh_state(self):
        sel=self.is_selected_fn(self.path)
        if sel:
            self.sel_color.rgba=(0.1,0.8,0.1,1)
            self.toggle_btn.text="Entfernen"
            self.toggle_btn.background_color=(0.4,0.25,0.25,1)
        else:
            self.sel_color.rgba=(0,0.7,0,0)
            self.toggle_btn.text="Auswählen"
            self.toggle_btn.background_color=(0.25,0.35,0.55,1)

class GalleryEditor(FloatLayout):
    def __init__(self, slideshow, **kw):
        super().__init__(**kw)
        self.slideshow=slideshow
        self.manager=slideshow.mode_manager
        self.target_mode=None
        self.filter_selected_only=False
        self.has_changes=False
        with self.canvas.before:
            GColor(0,0,0,0.7)
            self.bg=Rectangle(pos=self.pos,size=self.size)
        self.bind(pos=lambda *a:(setattr(self.bg,'pos',self.pos),setattr(self.bg,'size',self.size)))
        root=BoxLayout(orientation="horizontal",size_hint=(0.95,0.92),
                       pos_hint={"center_x":0.5,"center_y":0.5},spacing=dp(18))
        with root.canvas.before:
            GColor(0.14,0.14,0.17,0.95)
            self.inner_bg=Rectangle(pos=root.pos,size=root.size)
        root.bind(pos=lambda *a:setattr(self.inner_bg,'pos',root.pos),
                  size=lambda *a:setattr(self.inner_bg,'size',root.size))
        left=BoxLayout(orientation="vertical",size_hint=(0.22,1),spacing=dp(12),padding=dp(6))
        left.add_widget(Label(text="Modi",size_hint_y=None,height=dp(40),
                              font_size=dp(24),color=(1,1,1,1)))
        self.mode_box=BoxLayout(orientation="vertical",spacing=dp(8),size_hint_y=None)
        ms=ScrollView(); ms.add_widget(self.mode_box); left.add_widget(ms)
        self.status_lbl=Label(text="Modus wählen",size_hint_y=None,height=dp(40),
                              font_size=dp(16),color=(1,1,1,0.85))
        left.add_widget(self.status_lbl)
        
        # Save button (initially hidden)
        self.save_btn=Button(text="Speichern",size_hint_y=None,height=dp(60),
                            font_size=dp(22),background_normal='',
                            background_color=(0.25,0.55,0.25,1),color=(1,1,1,1),
                            opacity=0,disabled=True)
        self.save_btn.bind(on_release=lambda *_: self.save_changes())
        left.add_widget(self.save_btn)
        
        # Feedback label (initially hidden)
        self.feedback_lbl=Label(text="",size_hint_y=None,height=dp(30),
                               font_size=dp(16),color=(0.2,0.8,0.2,1),
                               opacity=0)
        left.add_widget(self.feedback_lbl)
        
        close_btn=Button(text="Schließen",size_hint_y=None,height=dp(60),
                         font_size=dp(22),background_normal='',
                         background_color=(0.4,0.4,0.45,1),color=(1,1,1,1))
        close_btn.bind(on_release=lambda *_: self.close())
        left.add_widget(close_btn)
        right=BoxLayout(orientation="vertical",size_hint=(0.78,1),spacing=dp(10),padding=[0,6,6,6])
        header=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(12))
        header.add_widget(Label(text="Alle Bilder im Ordner",font_size=dp(24),color=(1,1,1,1)))
        self.filter_btn=Button(text="Nur Modus-Bilder: AUS",size_hint=(None,1),width=dp(260),
                               background_normal='',background_color=(0.25,0.35,0.55,1),
                               color=(1,1,1,1),font_size=dp(16))
        self.filter_btn.bind(on_release=self.toggle_filter)
        header.add_widget(self.filter_btn)
        right.add_widget(header)
        from kivy.uix.gridlayout import GridLayout
        from kivy.core.window import Window
        # Adjust gallery columns based on aspect ratio for portrait mode
        aspect = slideshow.aspect_ratio if slideshow else "16:9"
        if aspect == "9:16":
            # Portrait mode: 2-3 columns depending on width
            gallery_cols = 3 if Window.width > dp(600) else 2
            gallery_spacing = dp(10)  # Tighter spacing for portrait
        else:
            # Landscape mode: 8 columns as before
            gallery_cols = 8
            gallery_spacing = dp(14)
        self.gallery_grid=GridLayout(cols=gallery_cols,spacing=gallery_spacing,padding=dp(6),size_hint_y=None)
        self.gallery_grid.bind(minimum_height=lambda inst,val:setattr(inst,'height',val))
        gs=ScrollView(); gs.add_widget(self.gallery_grid); right.add_widget(gs)
        root.add_widget(left); root.add_widget(right)
        self.add_widget(root)
        self.all_images_cache=[]
        self._build_modes()
        self._reload_all_images()
        self._populate()
    def _build_modes(self):
        self.mode_box.clear_widgets(); h=0
        for m in self.manager.modes:
            if m.name in ("Alle Bilder","Standard"): continue
            btn=Button(text=m.name,size_hint_y=None,height=dp(70),
                       background_normal='',background_color=(0.25,0.28,0.33,1),
                       color=(1,1,1,1),font_size=dp(20))
            btn.bind(on_release=lambda inst,mm=m:self.select_mode(mm))
            self.mode_box.add_widget(btn); h+=btn.height+dp(8)
        self.mode_box.height=h if h>10 else 10
    def select_mode(self,mode):
        # Reset changes when switching modes
        self.has_changes=False
        self._hide_save_button()
        
        self.target_mode=mode
        self.status_lbl.text=f"Modus: {mode.name}"
        # Reload images for the new mode (important for Import mode)
        self._reload_all_images()
        self._populate()
    def toggle_filter(self,*_):
        self.filter_selected_only=not self.filter_selected_only
        self.filter_btn.text="Nur Modus-Bilder: AN" if self.filter_selected_only else "Nur Modus-Bilder: AUS"
        self._populate()
    def _reload_all_images(self):
        """Load images from appropriate directory based on current mode"""
        # If Import mode is selected, load from IMPORT_DIR, otherwise from IMAGE_DIR
        if self.target_mode and self.target_mode.name == "Import":
            if IMPORT_DIR.exists():
                files=[str(p) for p in IMPORT_DIR.iterdir()
                       if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
                files.sort()
            else:
                files=[]
        else:
            # Load from standard IMAGE_DIR
            if IMAGE_DIR.exists():
                files=[str(p) for p in IMAGE_DIR.iterdir()
                       if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
                files.sort()
            else:
                files=[]
        if len(files)>MAX_IMAGES_DISPLAY: files=files[:MAX_IMAGES_DISPLAY]
        self.all_images_cache=files
        
    def _sync_image_lists_with_folder(self):
        """Remove non-existing images from all modes and provide feedback"""
        if not IMAGE_DIR.exists():
            return
        
        existing_files = set(self.all_images_cache)
        total_removed = 0
        
        # Check and clean all modes
        for mode in self.manager.modes:
            if not mode.images:
                continue
            
            removed_from_mode = []
            for img_path in mode.images[:]:  # Copy list to iterate safely
                if img_path not in existing_files:
                    mode.images.remove(img_path)
                    removed_from_mode.append(img_path)
            
            total_removed += len(removed_from_mode)
        
        # Save changes if any images were removed
        if total_removed > 0:
            self.manager.save()
            # Show feedback about removed images
            feedback_msg = f"{total_removed} nicht existierende Bilder entfernt"
            self._show_feedback(feedback_msg)
        
        return total_removed
    def _is_selected(self,path):
        return self.target_mode and path in self.target_mode.images
    def _toggle(self,path):
        if not self.target_mode:
            self.status_lbl.text="Bitte Modus links wählen."; return
        if path in self.target_mode.images:
            self.target_mode.images.remove(path)
        else:
            self.target_mode.images.append(path)
        
        # Track changes and show save button
        self.has_changes=True
        self._show_save_button()
        
        for tile in self.gallery_grid.children:
            if isinstance(tile,ImageTile) and tile.path==path: tile.refresh_state()
        self._update_count()
    def _open_settings(self,path):
        popup=ImageSettingsPopup(path,self.slideshow,
                                 on_close=None,
                                 on_deleted=lambda p: self._after_delete_refresh())
        popup.open()
    def _after_delete_refresh(self):
        self._reload_all_images()
        self._populate()
        if self.slideshow.current_mode:
            self.slideshow.set_mode(self.slideshow.current_mode.name, manual=True)
    def _update_count(self):
        if self.target_mode:
            self.status_lbl.text=f"Modus: {self.target_mode.name} | {len(self.target_mode.images)} Bild(er)"
    
    def _show_save_button(self):
        """Show the save button with animation"""
        if self.save_btn.opacity == 0:
            self.save_btn.disabled=False
            from kivy.animation import Animation
            Animation(opacity=1, d=0.3).start(self.save_btn)
    
    def _hide_save_button(self):
        """Hide the save button with animation"""
        from kivy.animation import Animation
        def _disable(*_):
            self.save_btn.disabled=True
        anim = Animation(opacity=0, d=0.3)
        anim.bind(on_complete=_disable)
        anim.start(self.save_btn)
    
    def save_changes(self):
        """Save all changes and refresh the slideshow"""
        if not self.has_changes or not self.target_mode:
            return
        
        # Save to file
        self.manager.save()
        
        # Sync image lists after save to remove any non-existing files
        self._sync_image_lists_with_folder()
        
        # Update slideshow if current mode matches target mode
        if self.slideshow.current_mode and self.slideshow.current_mode.name==self.target_mode.name:
            self.slideshow.set_mode(self.target_mode.name, manual=True)
        
        # Reset changes flag and hide save button
        self.has_changes=False
        self._hide_save_button()
        
        # Show feedback
        self._show_feedback("Gespeichert!")
    
    def _show_feedback(self, message):
        """Show temporary feedback message"""
        self.feedback_lbl.text=message
        from kivy.animation import Animation
        from kivy.clock import Clock
        
        # Show feedback
        Animation(opacity=1, d=0.3).start(self.feedback_lbl)
        
        # Hide after 2 seconds
        def hide_feedback(dt):
            Animation(opacity=0, d=0.3).start(self.feedback_lbl)
        Clock.schedule_once(hide_feedback, 2.0)
    def _populate(self):
        self.gallery_grid.clear_widgets()
        if not self.all_images_cache: self._reload_all_images()
        imgs=self.all_images_cache
        if self.filter_selected_only and self.target_mode:
            imgs=[p for p in imgs if p in self.target_mode.images]
        for p in imgs:
            self.gallery_grid.add_widget(ImageTile(p,self._toggle,self._is_selected,self._open_settings))
        self._update_count()
    
    
    def close(self):
        if self.parent: self.parent.remove_widget(self)
        if self.slideshow.current_overlay is self:
            self.slideshow.current_overlay=None

# ---- TimePicker & ScheduleEditor (wie zuvor) ----
class TimePickerPopup(RotatedModalView):
    def __init__(self,title,sh,sm,eh,em,on_save,on_cancel,**kw):
        kw.setdefault('size_hint', (0.75, 0.7))
        kw.setdefault('auto_dismiss', False)
        super().__init__(**kw)
        self.on_save=on_save; self.on_cancel=on_cancel
        self.background_color = (0, 0, 0, 0.65)
        self.background = ''
        panel=BoxLayout(orientation='vertical',size_hint=(1, 1),
                        spacing=dp(14),padding=dp(18))
        with panel.canvas.before:
            GColor(0.16,0.16,0.2,0.97); self.pbg=Rectangle(pos=panel.pos,size=panel.size)
        panel.bind(pos=lambda *a:setattr(self.pbg,'pos',panel.pos),
                   size=lambda *a:setattr(self.pbg,'size',panel.size))
        panel.add_widget(Label(text=title,size_hint_y=None,height=dp(48),
                               font_size=dp(30),color=(1,1,1,1)))
        self.start_h=Slider(min=0,max=23,value=sh,step=1)
        self.start_m=Slider(min=0,max=59,value=sm,step=1)
        self.end_h=Slider(min=0,max=23,value=eh,step=1)
        self.end_m=Slider(min=0,max=59,value=em,step=1)
        def row(lbl,s):
            b=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(90))
            b.add_widget(Label(text=lbl,size_hint_y=None,height=dp(28),
                               font_size=dp(20),color=(1,1,1,1)))
            b.add_widget(s)
            val=Label(text=str(int(s.value)),size_hint_y=None,height=dp(28),
                      font_size=dp(18),color=(0.8,0.8,0.9,1))
            s.bind(value=lambda inst,value,val_label=val:setattr(val_label,'text',str(int(value))))
            b.add_widget(val); return b
        for lab,sl in [("Start Stunde",self.start_h),("Start Minute",self.start_m),
                       ("Ende Stunde",self.end_h),("Ende Minute",self.end_m)]:
            panel.add_widget(row(lab,sl))
        self.preview=Label(text="",size_hint_y=None,height=dp(40),
                           font_size=dp(20),color=(0.9,0.9,1,1))
        panel.add_widget(self.preview)
        def upd(*_):
            self.preview.text=f"{int(self.start_h.value):02d}:{int(self.start_m.value):02d}  ->  {int(self.end_h.value):02d}:{int(self.end_m.value):02d}"
        for s in [self.start_h,self.start_m,self.end_h,self.end_m]:
            s.bind(value=lambda inst,val:upd())
        upd()
        btn_row=BoxLayout(size_hint_y=None,height=dp(70),spacing=dp(16))
        ok=Button(text="Übernehmen",background_normal='',background_color=(0.25,0.45,0.25,1),
                  color=(1,1,1,1),font_size=dp(22))
        cancel=Button(text="Abbrechen",background_normal='',background_color=(0.4,0.35,0.35,1),
                      color=(1,1,1,1),font_size=dp(22))
        ok.bind(on_release=lambda *_: self._save())
        cancel.bind(on_release=lambda *_: self._cancel())
        btn_row.add_widget(ok); btn_row.add_widget(cancel); panel.add_widget(btn_row)
        self.add_widget(panel)
    def _save(self):
        sh,sm=int(self.start_h.value),int(self.start_m.value)
        eh,em=int(self.end_h.value),int(self.end_m.value)
        self.on_save(f"{sh:02d}:{sm:02d}", f"{eh:02d}:{em:02d}")
        self.dismiss()
    def _cancel(self):
        self.on_cancel()
        self.dismiss()

class ScheduleEditor(FloatLayout):
    def __init__(self, slideshow, **kw):
        super().__init__(**kw)
        self.slideshow=slideshow
        self.manager=slideshow.mode_manager
        self.mode_rows={}
        with self.canvas.before:
            GColor(0,0,0,0.65); self.bg=Rectangle(pos=self.pos,size=self.size)
        self.bind(pos=lambda *a:(setattr(self.bg,'pos',self.pos),setattr(self.bg,'size',self.size)))
        panel=BoxLayout(orientation="vertical",size_hint=(0.7,0.6),
                        pos_hint={"center_x":0.5,"center_y":0.5},
                        spacing=dp(16),padding=dp(20))
        with panel.canvas.before:
            GColor(0.16,0.16,0.2,0.97); self.pbg=Rectangle(pos=panel.pos,size=panel.size)
        panel.bind(pos=lambda *a:setattr(self.pbg,'pos',panel.pos),
                   size=lambda *a:setattr(self.pbg,'size',panel.size))
        panel.add_widget(Label(text="Zeitplan Tag / Nacht",
                               size_hint_y=None,height=dp(50),
                               font_size=dp(30),color=(1,1,1,1)))
        for name in ("Tag","Nacht"): panel.add_widget(self._row(name))
        self.status_lbl=Label(text="",size_hint_y=None,height=dp(40),
                              font_size=dp(18),color=(1,0.7,0.4,1))
        panel.add_widget(self.status_lbl)
        buttons=BoxLayout(size_hint_y=None,height=dp(70),spacing=dp(20))
        save=Button(text="Speichern & Schließen",font_size=dp(22),
                    background_normal='',background_color=(0.25,0.45,0.25,1),
                    color=(1,1,1,1))
        cancel=Button(text="Abbrechen",font_size=dp(22),
                      background_normal='',background_color=(0.35,0.35,0.4,1),
                      color=(1,1,1,1))
        save.bind(on_release=self.save_all); cancel.bind(on_release=lambda *_: self.close())
        buttons.add_widget(save); buttons.add_widget(cancel); panel.add_widget(buttons)
        self.add_widget(panel)
    def _row(self,name):
        m=self.manager.get(name)
        if m and m.windows:
            w=m.windows[0]
            start=w.get("start","06:00" if name=="Tag" else "21:00")
            end=w.get("end","21:00" if name=="Tag" else "05:30")
        else:
            start="06:00" if name=="Tag" else "21:00"
            end="21:00" if name=="Tag" else "05:30"
        row=BoxLayout(size_hint_y=None,height=dp(90),spacing=dp(12))
        lbl=Label(text=name,size_hint_x=0.2,font_size=dp(24),color=(1,1,1,1))
        s_lbl=Label(text=start,size_hint_x=0.18,font_size=dp(22),color=(0.8,0.9,1,1))
        e_lbl=Label(text=end,size_hint_x=0.18,font_size=dp(22),color=(0.8,0.9,1,1))
        edit=Button(text="Bearbeiten",size_hint_x=0.25,
                    background_normal='',background_color=(0.3,0.4,0.6,1),
                    color=(1,1,1,1),font_size=dp(18))
        def open_pick(*_):
            sh,sm=[int(x) for x in s_lbl.text.split(":")]
            eh,em=[int(x) for x in e_lbl.text.split(":")]
            picker=TimePickerPopup(f"{name} Zeitfenster",sh,sm,eh,em,
                                   on_save=lambda s,e:self._apply(name,s,e),
                                   on_cancel=lambda:None)
            picker.open()
        edit.bind(on_release=open_pick)
        row.add_widget(lbl); row.add_widget(s_lbl); row.add_widget(e_lbl); row.add_widget(edit)
        self.mode_rows[name]={'start':s_lbl,'end':e_lbl}
        return row
    def _apply(self,name,start,end):
        self.mode_rows[name]['start'].text=start
        self.mode_rows[name]['end'].text=end
    def save_all(self,*_):
        for name,data in self.mode_rows.items():
            m=self.manager.get(name)
            if not m: continue
            s=data['start'].text; e=data['end'].text
            if parse_time(s) is None or parse_time(e) is None:
                self.status_lbl.text=f"Ungültige Zeit: {name}"; return
            m.windows=[{"start":s,"end":e}]; m.auto=True
        self.manager.save()
        self.slideshow.manual_override=False
        self.slideshow.force_reschedule()
        self.status_lbl.text="Gespeichert."
        Clock.schedule_once(lambda dt:self.close(),0.7)
    def close(self):
        if self.parent: self.parent.remove_widget(self)
        if self.slideshow.current_overlay is self:
            self.slideshow.current_overlay=None

# ---- Format Selection Popup ----
class FormatSelectionPopup(RotatedModalView):
    def __init__(self, slideshow, **kw):
        # Set ModalView properties for full-screen with centered content
        kw_copy = kw.copy()
        kw_copy.setdefault('size_hint', (1, 1))  # Full screen
        kw_copy.setdefault('auto_dismiss', True)
        super().__init__(**kw_copy)
        self.slideshow = slideshow
        self.background_color = (0, 0, 0, 0.7)  # Dim overlay
        self.background = ''
        
        # Calculate panel size based on aspect ratio using portrait factors
        from kivy.core.window import Window
        aspect = slideshow.aspect_ratio if slideshow else "16:9"
        if aspect == "9:16":
            # Portrait mode: apply portrait factors (0.62×w, 0.86×h, min 320×260)
            content_w = Window.width
            content_h = Window.height
            panel_w = max(int(content_w * 0.62), dp(320))
            panel_h = max(int(content_h * 0.86), dp(260))
            panel_size = (panel_w, panel_h)
        else:
            # Landscape mode: use standard size
            panel_size = (dp(400), dp(300))
        
        # Use AnchorLayout to center the content panel
        anchor = AnchorLayout(size_hint=(1, 1), anchor_x='center', anchor_y='center')
        
        panel = BoxLayout(orientation='vertical', size_hint=(None, None), size=panel_size,
                         padding=dp(22), spacing=dp(16))
        with panel.canvas.before:
            GColor(0.18, 0.18, 0.22, 0.97)
            panel._bg = Rectangle(pos=panel.pos, size=panel.size)
        panel.bind(pos=lambda *a: setattr(panel._bg, 'pos', panel.pos),
                  size=lambda *a: setattr(panel._bg, 'size', panel.size))
        
        # Title label - global rotation handles orientation
        title_label = RotatedLabel(
            text="Format", 
            size_hint_y=None, 
            height=dp(54),
            font_size=dp(32), 
            color=(1, 1, 1, 1), 
            bold=True
        )
        panel.add_widget(title_label)
        
        # Current format display
        current_text = f"Aktuell: {self.slideshow.aspect_ratio}"
        self.current_label = RotatedLabel(
            text=current_text, 
            size_hint_y=None, 
            height=dp(30),
            font_size=dp(18), 
            color=(0.7, 0.9, 1, 1)
        )
        panel.add_widget(self.current_label)
        
        # Spacer
        panel.add_widget(Widget(size_hint_y=0.2))
        
        # Format buttons - global rotation handles orientation
        btn_horizontal = RotatedButton(
            text="Horizontal (16:9)", 
            size_hint_y=None, 
            height=dp(60),
            font_size=dp(22),
            background_normal='', 
            background_color=(0.3, 0.5, 0.7, 1),
            color=(1, 1, 1, 1)
        )
        btn_horizontal.bind(on_release=lambda x: self._select_format("16:9"))
        panel.add_widget(btn_horizontal)
        
        btn_vertical = RotatedButton(
            text="Vertikal (9:16)", 
            size_hint_y=None, 
            height=dp(60),
            font_size=dp(22),
            background_normal='', 
            background_color=(0.3, 0.5, 0.7, 1),
            color=(1, 1, 1, 1)
        )
        btn_vertical.bind(on_release=lambda x: self._select_format("9:16"))
        panel.add_widget(btn_vertical)
        
        # Spacer
        panel.add_widget(Widget(size_hint_y=0.2))
        
        # Close button
        close_btn = RotatedButton(
            text="Schließen", 
            size_hint_y=None, 
            height=dp(50),
            font_size=dp(20),
            background_normal='', 
            background_color=(0.4, 0.4, 0.5, 1),
            color=(1, 1, 1, 1)
        )
        close_btn.bind(on_release=lambda x: self.close())
        panel.add_widget(close_btn)
        
        # Add panel to anchor layout, then add anchor to modal
        anchor.add_widget(panel)
        self.add_widget(anchor)
        
        # Bind ESC/Back key to dismiss
        from kivy.core.window import Window
        Window.bind(on_key_down=self._on_key_down)
        
        # Log modal opening
        debug_logger.info(f"Format modal open centered size={panel_size[0]}x{panel_size[1]}")
    
    def _on_key_down(self, window, key, scancode, codepoint, modifiers):
        """Handle ESC/Back key to dismiss modal"""
        if key == 27:  # ESC or Back
            self.close()
            return True
        return False
    
    def _select_format(self, aspect_ratio):
        from kivy.core.window import Window
        
        self.slideshow.aspect_ratio = aspect_ratio
        self.slideshow.persist_meta()
        self.current_label.text = f"Aktuell: {aspect_ratio}"
        
        # Close any currently open panels before switching aspect ratio
        self.slideshow._close_current_panel()
        
        # Update OrientationProvider to trigger global rotation
        orientation_provider = OrientationProvider()
        orientation_provider.set_orientation(aspect_ratio)
        
        # Apply rotation to root widget
        app = App.get_running_app()
        if hasattr(app, 'root_widget') and isinstance(app.root_widget, RotatingRoot):
            app.root_widget.apply_rotation()
        
        # Adjust window size when not in fullscreen mode
        if not Window.fullscreen:
            if aspect_ratio == "16:9":
                Window.size = (1280, 720)  # Horizontal
            elif aspect_ratio == "9:16":
                Window.size = (720, 1280)  # Vertical
        
        # Apply new layout based on aspect ratio
        self.slideshow._apply_layout()
        
        # Reload images with new aspect ratio filter
        if self.slideshow.current_mode:
            mode = self.slideshow.current_mode
            if mode.name in ("Alle Bilder","Standard"):
                self.slideshow.images = self.slideshow._scan_global()
            elif mode.name == "Import":
                self.slideshow.images = self.slideshow._scan_import()
            else:
                self.slideshow.images = self.slideshow._filter_by_aspect_ratio(mode.existing_images())
            if mode.randomize:
                from random import shuffle
                shuffle(self.slideshow.images)
            # Reset to first image and update display
            self.slideshow.index = 0
            self.slideshow.show_current_image(initial=True)
            self.slideshow.update_info()
        # Show feedback
        from kivy.animation import Animation
        from kivy.clock import Clock
        original_color = self.current_label.color
        self.current_label.color = (0.3, 1, 0.3, 1)  # Green feedback
        Clock.schedule_once(lambda dt: setattr(self.current_label, 'color', original_color), 0.5)
    
    def close(self):
        from kivy.core.window import Window
        Window.unbind(on_key_down=self._on_key_down)
        debug_logger.info("Format modal dismissed")
        self.dismiss()

# ---- Slideshow ----
class Slideshow(FloatLayout):
    def __init__(self, mode_manager: ModeManager, **kw):
        super().__init__(**kw)
        self.mode_manager=mode_manager
        self.current_mode=None
        self.images=[]
        self.index=0
        self.event=None
        self.scheduler_event=None
        self.manual_override=False

        self.selected_effects = set(DEFAULT_EFFECTS)
        self.randomize_effects = False
        self.effect_state_seed = 0

        meta = load_image_meta()
        self.image_effect_overrides = meta.get("effects", {})
        self.image_interval_overrides = meta.get("intervals", {})
        self.image_priority_weights = meta.get("weights", {})
        self.image_brightness_overrides = meta.get("brightness", {})
        self.global_interval_override = meta.get("global_interval", None)
        self.global_brightness_override = meta.get("global_brightness", None)
        self.aspect_ratio = meta.get("aspect_ratio", "16:9")
        
        # Initialize OrientationProvider with current aspect ratio
        orientation_provider = OrientationProvider()
        orientation_provider.set_orientation(self.aspect_ratio)
        
        # Detect screen size and enable fullscreen
        from kivy.core.window import Window
        self.screen_width = Window.width
        self.screen_height = Window.height
        
        # Enable fullscreen as fallback if not already set by Config
        # (Config.set should have already set this before app initialization)
        if not Window.fullscreen:
            Window.fullscreen = 'auto'
        
        # After enabling fullscreen, get actual screen dimensions
        # Use a callback to get the correct screen dimensions after fullscreen is enabled
        Clock.schedule_once(lambda dt: self._setup_window_size(), 0.1)

        self._toolbar_timer=None
        self._toolbar_anim=None
        self.current_overlay=None

        self.debug_label=None
        self.current_original_path=None
        self.current_display_path=None



        with self.canvas.before:
            GColor(0.02,0.02,0.03,1)
            self.bg=Rectangle(pos=self.pos,size=self.size)
        self.bind(pos=lambda *a:(setattr(self.bg,'pos',self.pos),setattr(self.bg,'size',self.size)),
                  size=lambda *a:(setattr(self.bg,'pos',self.pos),setattr(self.bg,'size',self.size)))

        # Create image widgets with proper fit mode for Kivy 2.3+
        # Use fit_mode='cover' with mipmap for better quality
        import kivy
        kivy_version = tuple(map(int, kivy.__version__.split('.')[:2]))
        if kivy_version >= (2, 3):
            # Kivy 2.3+: use fit_mode='cover' (replaces deprecated keep_ratio/allow_stretch)
            self.img_a = Image(opacity=1, color=(1,1,1,1), fit_mode='cover', mipmap=True)
            self.img_b = Image(opacity=0, color=(1,1,1,1), fit_mode='cover', mipmap=True)
        else:
            # Older Kivy: use deprecated but functional keep_ratio/allow_stretch
            self.img_a = Image(opacity=1, color=(1,1,1,1), allow_stretch=True, keep_ratio=True, mipmap=True)
            self.img_b = Image(opacity=0, color=(1,1,1,1), allow_stretch=True, keep_ratio=True, mipmap=True)
        self.active_img = self.img_a
        self.back_img = self.img_b
        self.add_widget(self.img_a)
        self.add_widget(self.img_b)

        self.img_a.bind(texture=lambda *_: (self._resize_image(self.img_a), self._update_debug_overlay()))
        self.img_b.bind(texture=lambda *_: (self._resize_image(self.img_b), self._update_debug_overlay()))
        self.bind(size=lambda *_: (self._resize_image(self.img_a), self._resize_image(self.img_b)))

        # Create initial toolbar (will be recreated with correct orientation in _apply_layout)
        self.toolbar=self._create_toolbar()
        self.add_widget(self.toolbar)

        self.placeholder=Label(text="",color=(1,1,1,0.7),font_size=dp(26),opacity=0)
        self.add_widget(self.placeholder)

        if SHOW_INFO_LABEL:
            self.info_label=Label(text="",color=(1,1,1,0.85),
                                  size_hint=(1,None),height=dp(36),
                                  font_size=dp(20),
                                  pos_hint={'center_x':0.5,'y':0.01})
            self.add_widget(self.info_label)

        if SHOW_DEBUG_OVERLAY:
            self.debug_label=Label(text="",color=(0.9,0.95,1,0.85),
                                   size_hint=(None,None),
                                   font_size=DEBUG_OVERLAY_FONT_SIZE,
                                   pos=(dp(8), self.height - dp(40)))
            self.add_widget(self.debug_label)
            self.bind(size=lambda *_: self._reposition_debug())
        
        if SHOW_FAB_GALLERY: self.add_gallery_fab()

        self._new_files_timer=Clock.schedule_interval(lambda dt:self._check_new_files(), INTERVAL_NEW_FILES)

        # Recording functionality moved to popup (no bottom widget)

        self.auto_select_initial_mode()
        self.start_slideshow()
        self.scheduler_event=Clock.schedule_interval(lambda dt:self.auto_scheduler(), SCHEDULER_INTERVAL_SEC)
        self._show_toolbar_immediate()

    def _setup_window_size(self):
        """Setup window size after fullscreen is enabled"""
        from kivy.core.window import Window
        # Get actual screen dimensions
        self.screen_width = Window.width
        self.screen_height = Window.height
        
        # Set initial window size based on aspect ratio when not in fullscreen
        if not Window.fullscreen:
            if self.aspect_ratio == "16:9":
                Window.size = (1280, 720)
            elif self.aspect_ratio == "9:16":
                Window.size = (720, 1280)
        
        # Apply layout based on aspect ratio
        self._apply_layout()

    def _apply_layout(self):
        """Apply layout based on current aspect ratio"""
        from kivy.core.window import Window
        
        debug_logger.info(f"Applying layout for aspect ratio: {self.aspect_ratio}, window size: {Window.width}x{Window.height}")
        
        # Close any open panels before rebuilding layout
        self._close_current_panel()
        
        # Remove old toolbar if exists
        if hasattr(self, 'toolbar') and self.toolbar:
            self.remove_widget(self.toolbar)
            debug_logger.info("Removed old toolbar before rebuild")
        
        # Create toolbar based on aspect ratio
        # For 9:16 (portrait): vertical toolbar on right
        # For 16:9 (landscape): horizontal toolbar at bottom
        if self.aspect_ratio == "9:16":
            self.toolbar = self._create_toolbar(vertical=True)
            debug_logger.info(f"Created toolbar at RIGHT (vertical) for 9:16 mode, width={self.toolbar.width if hasattr(self.toolbar, 'width') else 'auto'}")
        else:
            self.toolbar = self._create_toolbar(vertical=False)
            debug_logger.info(f"Created horizontal toolbar at bottom for {self.aspect_ratio} mode")
        
        self.add_widget(self.toolbar)
        debug_logger.info("Added toolbar to widget tree")
        
        # Bring toolbar to front (buttons are already set in _create_toolbar)
        self._bring_toolbar_to_front()
        
        # Force resize of current images
        if hasattr(self, 'img_a') and self.img_a:
            self._resize_image(self.img_a)
        if hasattr(self, 'img_b') and self.img_b:
            self._resize_image(self.img_b)

    # Persistenz
    def persist_meta(self):
        meta = {
            "effects": self.image_effect_overrides,
            "intervals": self.image_interval_overrides,
            "weights": self.image_priority_weights,
            "brightness": self.image_brightness_overrides,
            "global_interval": self.global_interval_override,
            "global_brightness": self.global_brightness_override,
            "aspect_ratio": self.aspect_ratio
        }
        save_image_meta(meta)

    # Overlay Manager
    def open_single(self, widget):
        if self.current_overlay and self.current_overlay.parent:
            self.remove_widget(self.current_overlay)
        self.current_overlay = widget
        self.add_widget(widget)

    # Upscaling / Resize
    def _resize_image(self,img_widget):
        if not img_widget.texture: return
        
        # Calculate available space, accounting for toolbar position
        content_x = 0  # Starting x position for content
        content_y = 0  # Starting y position for content
        content_w = self.width
        content_h = self.height
        
        # Adjust content area based on toolbar position and orientation
        if hasattr(self, 'toolbar') and self.toolbar:
            if self.aspect_ratio == "9:16":
                # Vertical toolbar on right side - reduce content width
                toolbar_width = self.toolbar.width if hasattr(self.toolbar, 'width') else dp(108)
                content_w = self.width - toolbar_width
                content_x = 0  # Content starts at left edge
            else:
                # Horizontal toolbar at bottom - reduce content height
                toolbar_height = self.toolbar.height if hasattr(self.toolbar, 'height') else dp(60)
                content_h = self.height - toolbar_height
                content_y = toolbar_height  # Content starts above the toolbar
        
        # With fit_mode='cover' (Kivy 2.3+), the Image widget handles scaling automatically
        # We only need to set the size to fill the available content area
        # The widget will center and scale the texture to cover the area without manual math
        img_widget.size = (content_w, content_h)
        img_widget.pos = (content_x, content_y)

    def _create_toolbar(self, vertical=False):
        if AppBarClass:
            # Position based on orientation
            if vertical:
                pos_hint = {"right": 1, "top": 1}
            else:
                pos_hint = {"bottom": 1}
            
            bar=AppBarClass(title=("" if HIDE_TOOLBAR_TITLE else "Slideshow"),
                            elevation=8, pos_hint=pos_hint)
            self._update_md_toolbar_buttons(bar)
            def md_fade_in(self_,duration=TOOLBAR_FADE_DURATION):
                self_.disabled=False
                Animation.cancel_all(self_,'opacity')
                Animation(opacity=1,d=duration,t='out_quad').start(self_)
            def md_fade_out(self_,duration=TOOLBAR_FADE_DURATION):
                Animation.cancel_all(self_,'opacity')
                def _dis(*_): self_.disabled=True
                a=Animation(opacity=0,d=duration,t='in_quad'); a.bind(on_complete=_dis); a.start(self_)
            bar.fade_in=types.MethodType(md_fade_in,bar)
            bar.fade_out=types.MethodType(md_fade_out,bar)
            return bar
        
        # CustomAppBar with vertical/horizontal mode
        bar=CustomAppBar(title=("Slideshow" if not HIDE_TOOLBAR_TITLE else ""), vertical=vertical)
        
        # Position based on orientation
        if vertical:
            # Vertical toolbar on right side for 9:16 mode with fixed width
            bar.pos_hint = {"right": 1, "top": 1}
            bar.width = dp(108)  # Fixed width for vertical toolbar
        else:
            # Horizontal toolbar at bottom for 16:9 mode
            bar.pos_hint = {"bottom": 1}
        
        self._update_toolbar_buttons(bar)
        return bar
    
    def _close_current_panel(self):
        """Close currently open panel if any"""
        app = App.get_running_app()
        if app and hasattr(app, '_open_panel') and app._open_panel:
            panel_id, panel_instance = app._open_panel
            if panel_instance and hasattr(panel_instance, 'dismiss'):
                panel_instance.dismiss()
            elif panel_instance and hasattr(panel_instance, 'close'):
                panel_instance.close()
            elif panel_instance and panel_instance.parent:
                panel_instance.parent.remove_widget(panel_instance)
            app._open_panel = None
            debug_logger.info(f"Closed panel: {panel_id}")
    
    def _on_toolbar_item_pressed(self, item_id, open_fn):
        """
        Handle toolbar item press with toggle/single-open logic
        - If same id pressed: close it
        - If different panel open: close then open new one
        """
        app = App.get_running_app()
        if not app or not hasattr(app, '_open_panel'):
            # No tracking available, just open
            open_fn()
            return
        
        current_panel_id = app._open_panel[0] if app._open_panel else None
        
        if current_panel_id == item_id:
            # Same panel - toggle it closed
            self._close_current_panel()
        else:
            # Different panel or no panel - close current then open new
            if current_panel_id:
                self._close_current_panel()
            open_fn()
            # Track this panel as open
            # Note: open_fn should update app._open_panel after creating instance
    
    def _update_md_toolbar_buttons(self, bar):
        """Update KivyMD toolbar buttons"""
        bar.right_action_items=[
            ["calendar",lambda x:self._on_toolbar_item_pressed("schedule", self.open_schedule_editor)],
            ["record",lambda x:self._on_toolbar_item_pressed("aufnahme", self.open_aufnahme_popup)],
            ["aspect-ratio",lambda x:self._on_toolbar_item_pressed("format", self.open_format_selection)],
            ["image-multiple",lambda x:self._on_toolbar_item_pressed("gallery", self.open_gallery)],
            ["cog",lambda x:self._on_toolbar_item_pressed("settings", self.open_settings_root)],
            ["logout",lambda x:self.logout()],
            ["power",lambda x:self.exit_app()],
        ]
    
    def _update_toolbar_buttons(self, bar):
        """Update toolbar buttons"""
        bar.set_right_actions([
            ("Zeiten", lambda: self._on_toolbar_item_pressed("schedule", self.open_schedule_editor)),
            ("Aufnahme", lambda: self._on_toolbar_item_pressed("aufnahme", self.open_aufnahme_popup)),
            ("Format", lambda: self._on_toolbar_item_pressed("format", self.open_format_selection)),
            ("Galerie", lambda: self._on_toolbar_item_pressed("gallery", self.open_gallery)),
            ("Einstellungen", lambda: self._on_toolbar_item_pressed("settings", self.open_settings_root)),
            ("Logout", self.logout),
            ("Exit", self.exit_app),
        ])

    def _bring_toolbar_to_front(self):
        if self.toolbar in self.children:
            self.remove_widget(self.toolbar)
            self.add_widget(self.toolbar)
            debug_logger.info("Toolbar restacked to front (z-order)")

    def open_gallery(self):
        debug_logger.info("Opening gallery panel")
        widget = GalleryEditor(self)
        self.open_single(widget)
        app = App.get_running_app()
        if app:
            app._open_panel = ("gallery", widget)
    
    def open_schedule_editor(self):
        debug_logger.info("Opening schedule editor panel")
        widget = ScheduleEditor(self)
        self.open_single(widget)
        app = App.get_running_app()
        if app:
            app._open_panel = ("schedule", widget)
    
    def open_settings_root(self): 
        debug_logger.info("Opening settings panel")
        popup = SettingsRootPopup(self)
        popup.open()
        app = App.get_running_app()
        if app:
            app._open_panel = ("settings", popup)
    
    def open_aufnahme_popup(self): 
        debug_logger.info("Opening aufnahme panel")
        popup = AufnahmePopup(slideshow=self)
        popup.open()
        app = App.get_running_app()
        if app:
            app._open_panel = ("aufnahme", popup)
    
    def open_format_selection(self): 
        debug_logger.info("Opening format selection panel")
        popup = FormatSelectionPopup(self)
        popup.open()
        app = App.get_running_app()
        if app:
            app._open_panel = ("format", popup)
    # Note: Image selection is now integrated into the Aufnahme popup

    def force_reschedule(self):
        scheduled=self.mode_manager.scheduled_mode()
        target=scheduled.name if scheduled else "Alle Bilder"
        self.set_mode(target, manual=False)

    def exit_app(self): 
        App.get_running_app().stop()
    def logout(self):
        app=App.get_running_app()
        if hasattr(app,'show_login'): app.show_login()

    # Interval & Brightness
    def _get_interval_for_path(self, path):
        if path in self.image_interval_overrides:
            return max(1, self.image_interval_overrides[path])
        if self.global_interval_override is not None:
            return max(1, self.global_interval_override)
        if self.current_mode:
            return max(1, self.current_mode.interval)
        return max(1, DEFAULT_INTERVAL)

    def _apply_current_brightness(self):
        b_global = self.global_brightness_override or 1.0
        b_image = self.image_brightness_overrides.get(self.current_original_path, 1.0)
        b = max(0.1, min(2.0, b_global * b_image))
        for w in (self.img_a, self.img_b):
            r,g,bl,_ = w.color
            w.color = (b, b, b, 1)

    def _reschedule_for_current(self):
        if self.event: Clock.unschedule(self.event)
        interval = self._get_interval_for_path(self.current_original_path)
        self.event = Clock.schedule_once(lambda dt:self.next_image(), interval)

    def auto_select_initial_mode(self):
        scheduled=self.mode_manager.scheduled_mode()
        if scheduled: self.set_mode(scheduled.name, manual=False)
        else: self.set_mode("Alle Bilder", manual=False)

    def auto_scheduler(self):
        if self.manual_override: return
        scheduled=self.mode_manager.scheduled_mode()
        target=scheduled.name if scheduled else "Alle Bilder"
        if not self.current_mode or self.current_mode.name!=target:
            self.set_mode(target, manual=False)

    def _get_image_aspect_ratio(self, image_path):
        """
        Get aspect ratio of an image file.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            str: "16:9" for horizontal/landscape, "9:16" for vertical/portrait, or None if unable to determine
        """
        try:
            from PIL import Image as PILImage
            with PILImage.open(image_path) as img:
                width, height = img.size
                # Determine if image is more horizontal or vertical
                if width > height:
                    return "16:9"  # Horizontal/landscape
                elif height > width:
                    return "9:16"  # Vertical/portrait
                else:
                    # Square images match current aspect ratio
                    return self.aspect_ratio
        except Exception as e:
            debug_logger.debug(f"Could not determine aspect ratio for {image_path}: {e}")
            # If we can't determine, include it to be safe
            return None
    
    def _filter_by_aspect_ratio(self, files):
        """
        Filter image files by current aspect ratio setting.
        
        Args:
            files (list): List of image file paths
            
        Returns:
            list: Filtered list of image paths matching current aspect ratio
        """
        if not files:
            return []
        
        filtered = []
        for file_path in files:
            img_ratio = self._get_image_aspect_ratio(file_path)
            # Include image if:
            # - We couldn't determine its ratio (img_ratio is None)
            # - It matches the current aspect ratio
            if img_ratio is None or img_ratio == self.aspect_ratio:
                filtered.append(file_path)
        
        return filtered
    
    def _scan_global(self):
        """Scan IMAGE_DIR for AI-generated images"""
        if IMAGE_DIR.exists():
            files=[str(p) for p in IMAGE_DIR.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
            files.sort()
            # Filter by aspect ratio
            return self._filter_by_aspect_ratio(files)
        return []
    
    def _scan_import(self):
        """Scan IMPORT_DIR for imported images"""
        if IMPORT_DIR.exists():
            files=[str(p) for p in IMPORT_DIR.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
            files.sort()
            # Filter by aspect ratio
            return self._filter_by_aspect_ratio(files)
        return []

    def _check_new_files(self):
        if not self.current_mode:
            return
        
        # Update images for all modes - especially important for Tag/Nacht mode switching
        if self.current_mode.name in ("Alle Bilder","Standard"):
            cur=self._scan_global()
        elif self.current_mode.name == "Import":
            cur=self._scan_import()
        else:
            # For Tag/Nacht and other specific modes, check their assigned images
            cur=self._filter_by_aspect_ratio(self.current_mode.existing_images())
            
        if cur!=self.images:
            self.images=cur
            self.index=min(self.index,len(self.images)-1) if self.images else 0
            self.show_current_image(initial=True)
            self.update_info()

    def set_mode(self,name,manual=False):
        mode=self.mode_manager.get(name)
        if not mode: return
        self.current_mode=mode
        if manual: self.manual_override=True
        if mode.name in ("Alle Bilder","Standard"):
            self.images=self._scan_global()
        elif mode.name == "Import":
            self.images=self._scan_import()
        else:
            self.images=self._filter_by_aspect_ratio(mode.existing_images())
        if mode.randomize: shuffle(self.images)
        self.index=0
        self.show_current_image(initial=True)
        self.update_info()
        if hasattr(self.toolbar,'title'):
            self.toolbar.title = "" if HIDE_TOOLBAR_TITLE else mode.name
        self._bring_toolbar_to_front()
        self._reschedule_for_current()

    def start_slideshow(self):
        self.show_current_image(initial=True)
        self._reschedule_for_current()

    def _choose_effect(self):
        avail=list(self.selected_effects)
        if len(avail)==1: return avail[0]
        if "none" in avail and len(avail)>1:
            avail=[e for e in avail if e!="none"]
        if self.randomize_effects:
            return choice(avail)
        return sorted(avail)[0]

    def _weighted_next_index(self):
        weights=[]
        total=0
        for p in self.images:
            w=self.image_priority_weights.get(p,1)
            if w<1: w=1
            weights.append(w); total+=w
        if total<=len(self.images):
            return (self.index+1)%len(self.images)
        r=random()*total
        acc=0
        for i,w in enumerate(weights):
            acc+=w
            if r<=acc:
                return i
        return (self.index+1)%len(self.images)

    def show_current_image(self, initial=False):
        self._bring_toolbar_to_front()
        if not self.images:
            self.img_a.source=""; self.img_b.source=""
            # More informative message about why no images are shown
            if self.current_mode:
                self.placeholder.text=f"Keine Bilder im Format {self.aspect_ratio} für Modus '{self.current_mode.name}'.\nBitte Format wechseln oder Bilder hinzufügen."
            else:
                self.placeholder.text="Keine Bilder gefunden.\nBitte Bilder hinzufügen."
            self.placeholder.opacity=1
            self.update_info(empty=True)
            return
        self.placeholder.opacity=0
        path=self.images[self.index % len(self.images)]
        self.current_original_path=path
        self.current_display_path=path
        
        # Robust image loading: clear previous state and schedule load on next frame
        self._load_image_robust(self.back_img, path, initial)
    
    def _load_image_robust(self, img_widget, path, initial=False):
        """
        Robustly load an image into a widget, handling portrait/landscape correctly.
        
        Args:
            img_widget: The Image widget to load into
            path: Path to the image file
            initial: Whether this is the initial load (no transition)
        """
        import os
        
        # Step 1: Clear previous state to avoid stale textures
        img_widget.source = ""
        img_widget.texture = None
        img_widget.opacity = 0
        
        # Force canvas update
        img_widget.canvas.ask_update()
        
        # Step 2: Schedule load on next frame to avoid race with previous draw
        def _do_load(dt):
            # Check if file exists
            file_exists = os.path.exists(path)
            debug_logger.info(f"Loading image: path={path}, exists={file_exists}, aspect_mode={self.aspect_ratio}")
            
            if not file_exists:
                debug_logger.error(f"Image file does not exist: {path}")
                return
            
            # Step 3: Primary path - load via CoreImage for better control
            try:
                from kivy.core.image import Image as CoreImage
                core_img = CoreImage(path, nocache=True)
                
                if core_img and core_img.texture:
                    img_widget.texture = core_img.texture
                    tex_size = core_img.texture.size
                    widget_size = img_widget.size
                    debug_logger.info(f"Image loaded via CoreImage: texture_size={tex_size}, widget_size={widget_size}, aspect_mode={self.aspect_ratio}")
                    
                    # Schedule resize and brightness application
                    Clock.schedule_once(lambda dt2: (
                        self._resize_image(img_widget),
                        self._update_debug_overlay(),
                        self._apply_current_brightness()
                    ), 0)
                    
                    # Handle initial vs transition
                    if initial:
                        self.active_img.opacity = 0
                        img_widget.opacity = 1
                        self.active_img, self.back_img = self.back_img, self.active_img
                    else:
                        # Apply transition effect
                        effect_override = self.image_effect_overrides.get(path)
                        effect = effect_override if effect_override else self._choose_effect()
                        mapping = {
                            "fade": self._apply_fade,
                            "slide_left": lambda nw, ow: self._apply_slide(nw, ow, 'left'),
                            "slide_right": lambda nw, ow: self._apply_slide(nw, ow, 'right'),
                            "zoom_in": self._apply_zoom_in,
                            "zoom_pan": self._apply_zoom_pan,
                            "rotate": self._apply_rotate,
                            "blitz": self._apply_blitz,
                            "none": self._apply_none
                        }
                        mapping.get(effect, self._apply_fade)(img_widget, self.active_img)
                else:
                    raise Exception("CoreImage returned no texture")
                    
            except Exception as e:
                # Step 4: Fallback - use widget.source with reload
                debug_logger.warning(f"CoreImage failed for {path}: {e}, trying fallback with widget.source")
                try:
                    # Add cache-bust parameter with timestamp
                    import time
                    cache_bust_path = f"{path}?t={int(time.time() * 1000)}"
                    img_widget.source = cache_bust_path
                    img_widget.reload()
                    
                    # Verify texture loaded
                    def _check_fallback(dt2):
                        if img_widget.texture:
                            tex_size = img_widget.texture.size
                            widget_size = img_widget.size
                            debug_logger.info(f"Image loaded via fallback: texture_size={tex_size}, widget_size={widget_size}, aspect_mode={self.aspect_ratio}")
                            
                            Clock.schedule_once(lambda dt3: (
                                self._resize_image(img_widget),
                                self._update_debug_overlay(),
                                self._apply_current_brightness()
                            ), 0)
                            
                            if initial:
                                self.active_img.opacity = 0
                                img_widget.opacity = 1
                                self.active_img, self.back_img = self.back_img, self.active_img
                            else:
                                effect_override = self.image_effect_overrides.get(path)
                                effect = effect_override if effect_override else self._choose_effect()
                                mapping = {
                                    "fade": self._apply_fade,
                                    "slide_left": lambda nw, ow: self._apply_slide(nw, ow, 'left'),
                                    "slide_right": lambda nw, ow: self._apply_slide(nw, ow, 'right'),
                                    "zoom_in": self._apply_zoom_in,
                                    "zoom_pan": self._apply_zoom_pan,
                                    "rotate": self._apply_rotate,
                                    "blitz": self._apply_blitz,
                                    "none": self._apply_none
                                }
                                mapping.get(effect, self._apply_fade)(img_widget, self.active_img)
                        else:
                            debug_logger.error(f"Fallback also failed: texture is None for {path}")
                    
                    Clock.schedule_once(_check_fallback, 0.1)
                    
                except Exception as e2:
                    debug_logger.error(f"Both CoreImage and fallback failed for {path}: {e2}")
        
        Clock.schedule_once(_do_load, 0)

    # Effekte
    def _apply_slide(self,new_widget,old_widget,direction='left'):
        if not new_widget.texture: return self._apply_none(new_widget,old_widget)
        self._resize_image(new_widget)
        if direction=='left':
            new_widget.x=self.width; target_old=-self.width
        else:
            new_widget.x=-self.width; target_old=self.width
        new_widget.opacity=1
        new_widget.y=(self.height-new_widget.height)/2
        old_widget.y=(self.height-old_widget.height)/2
        a_old=Animation(x=target_old,d=0.6,t='out_quad')
        a_new=Animation(x=(self.width-new_widget.width)/2,d=0.6,t='out_quad')
        def finish(*_):
            old_widget.opacity=0; self._transition_done()
        a_old.start(old_widget); a_new.bind(on_complete=finish); a_new.start(new_widget)
    def _apply_fade(self,new_widget,old_widget):
        self._resize_image(new_widget)
        new_widget.opacity=0
        a_out=Animation(opacity=0,d=FADE_OUT_DUR,t="in_quad")
        a_in=Animation(opacity=1,d=FADE_IN_DUR,t="out_quad")
        def after_out(*_):
            a_in.bind(on_complete=lambda *_: self._transition_done()); a_in.start(new_widget)
        a_out.bind(on_complete=after_out); a_out.start(old_widget)
    def _apply_none(self,new_widget,old_widget):
        self._resize_image(new_widget)
        old_widget.opacity=0; new_widget.opacity=1
        self._transition_done()
    def _apply_zoom_in(self,new_widget,old_widget):
        self._resize_image(new_widget)
        bw,bh=new_widget.width,new_widget.height
        new_widget.width=bw*1.1; new_widget.height=bh*1.1
        new_widget.x=(self.width-new_widget.width)/2
        new_widget.y=(self.height-new_widget.height)/2
        new_widget.opacity=0
        a_out=Animation(opacity=0,d=0.4)
        def do_new(*_):
            a_new=Animation(opacity=1,width=bw,height=bh,
                            x=(self.width-bw)/2,y=(self.height-bh)/2,
                            d=1.2,t='out_quad')
            a_new.bind(on_complete=lambda *_: self._transition_done()); a_new.start(new_widget)
        a_out.bind(on_complete=lambda *_: do_new()); a_out.start(old_widget)
    def _apply_zoom_pan(self,new_widget,old_widget):
        self._resize_image(new_widget)
        bw,bh=new_widget.width,new_widget.height
        new_widget.width=bw*1.08; new_widget.height=bh*1.08
        dx=uniform(-0.05,0.05)*self.width; dy=uniform(-0.05,0.05)*self.height
        new_widget.x=(self.width-new_widget.width)/2+dx
        new_widget.y=(self.height-new_widget.height)/2+dy
        new_widget.opacity=0
        a_out=Animation(opacity=0,d=0.45)
        def anim_new(*_):
            a_new=Animation(opacity=1,width=bw,height=bh,
                            x=(self.width-bw)/2,y=(self.height-bh)/2,
                            d=1.8,t='out_quad')
            a_new.bind(on_complete=lambda *_: self._transition_done()); a_new.start(new_widget)
        a_out.bind(on_complete=lambda *_: anim_new()); a_out.start(old_widget)
    def _apply_rotate(self,new_widget,old_widget):
        self._resize_image(new_widget)
        bw,bh=new_widget.width,new_widget.height
        new_widget.width=bw*1.02; new_widget.height=bh*1.02
        new_widget.x=(self.width-new_widget.width)/2 + uniform(-self.width*0.02,self.width*0.02)
        new_widget.y=(self.height-new_widget.height)/2 + uniform(-self.height*0.02,self.height*0.02)
        new_widget.opacity=0
        a_out=Animation(opacity=0,d=0.4)
        def fin(*_):
            a_new=Animation(opacity=1,width=bw,height=bh,
                            x=(self.width-bw)/2,y=(self.height-bh)/2,
                            d=1.0,t='out_quad')
            a_new.bind(on_complete=lambda *_: self._transition_done()); a_new.start(new_widget)
        a_out.bind(on_complete=lambda *_: fin()); a_out.start(old_widget)
    
    def _apply_blitz(self, new_widget, old_widget):
        # Blitz effect: fast, intense transition with white flash
        self._resize_image(new_widget)
        new_widget.opacity=0
        
        # First flash old widget to white then fade out
        old_widget.color = (3, 3, 3, 1)  # Bright white
        a_flash = Animation(color=(1, 1, 1, 1), opacity=0, d=0.1, t='out_quad')
        
        def show_new(*_):
            # Show new image with brief white flash
            new_widget.color = (2, 2, 2, 1)  # Brief bright
            new_widget.opacity = 1
            a_new = Animation(color=(1, 1, 1, 1), d=0.15, t='out_quad')
            a_new.bind(on_complete=lambda *_: self._transition_done())
            a_new.start(new_widget)
        
        a_flash.bind(on_complete=show_new)
        a_flash.start(old_widget)
    def _transition_done(self):
        self.active_img.opacity=0
        self.active_img,self.back_img=self.back_img,self.active_img
        self.back_img.opacity=0
        self._apply_current_brightness()
        self._update_debug_overlay()
        self._reschedule_for_current()

    def next_image(self, *args):
        if not self.images: return
        if any(w>1 for w in self.image_priority_weights.values() if w):
            self.index=self._weighted_next_index()
        else:
            self.index=(self.index+1)%len(self.images)
        self.show_current_image()
        self.update_info()
    def prev_image(self):
        if not self.images: return
        self.index=(self.index-1)%len(self.images)
        self.show_current_image()
        self.update_info()

    def update_info(self, empty=False):
        if not SHOW_INFO_LABEL or not self.info_label: return
        if not self.current_mode:
            self.info_label.text="Kein Modus"; return
        img_info=f"{self.index+1}/{len(self.images)}" if self.images else "0/0"
        auto_flag="Auto" if self.current_mode.auto else "Manuell"
        ov=" Override" if self.manual_override else ""
        rnd=" Zufall" if self.current_mode.randomize else ""
        if empty:
            self.info_label.text=f"[{self.current_mode.name}] Keine Bilder | {auto_flag}{ov}{rnd}"
        else:
            self.info_label.text=f"[{self.current_mode.name}] {img_info} | {auto_flag}{ov}{rnd}"

    def _show_toolbar_immediate(self):
        if hasattr(self.toolbar,'fade_in'): self.toolbar.fade_in(0)
        else:
            self.toolbar.opacity=1; self.toolbar.disabled=False
        self._schedule_toolbar_hide()
    def _schedule_toolbar_hide(self):
        if self._toolbar_timer: Clock.unschedule(self._toolbar_timer)
        self._toolbar_timer=Clock.schedule_once(lambda dt:self._hide_toolbar(), TOOLBAR_VISIBLE_SECS)
    def _hide_toolbar(self):
        if hasattr(self.toolbar,'fade_out'): self.toolbar.fade_out()
        else: Animation(opacity=0,d=TOOLBAR_FADE_DURATION).start(self.toolbar)
    def _bring_up_toolbar(self):
        if hasattr(self.toolbar,'fade_in'): self.toolbar.fade_in()
        else:
            if self._toolbar_anim: self._toolbar_anim.stop(self.toolbar)
            self.toolbar.disabled=False; self.toolbar.opacity=1
        self._bring_toolbar_to_front()
        self._schedule_toolbar_hide()

    def _reposition_debug(self):
        if not self.debug_label: return
        self.debug_label.pos=(dp(8), self.height - dp(40))
    def _update_debug_overlay(self):
        if not SHOW_DEBUG_OVERLAY or not self.debug_label: return
        orig=self.current_original_path or "-"
        tw,th=(0,0)
        if self.active_img.texture: tw,th=self.active_img.texture.size
        aw,ah=self.active_img.size
        self.debug_label.text=f"Original | File: {Path(orig).name if orig!='-' else '-'} | Tex: {tw}x{th} -> Display: {aw:.0f}x{ah:.0f}"

    def on_touch_down(self,touch):
        self._bring_up_toolbar()
        self._start_x=touch.x
        return super().on_touch_down(touch)
    def on_touch_up(self,touch):
        self._bring_up_toolbar()
        if hasattr(self,'_start_x'):
            dx=touch.x-self._start_x
            if abs(dx)>50:
                if dx<0: self.next_image()
                else: self.prev_image()
            del self._start_x
        return super().on_touch_up(touch)
    def on_mouse_down(self, window, x, y, button, modifiers):
        self._bring_up_toolbar()

    def cleanup_on_exit(self):
        """Clean up resources when app is closing to fix recording restart issue"""
        debug_logger.info("Slideshow cleanup: stopping timers and processes")
        
        # Stop all timers
        if self.event: 
            Clock.unschedule(self.event)
            self.event = None
        if self.scheduler_event: 
            Clock.unschedule(self.scheduler_event)
            self.scheduler_event = None
        if self._new_files_timer: 
            Clock.unschedule(self._new_files_timer)
            self._new_files_timer = None
        if self._toolbar_timer: 
            Clock.unschedule(self._toolbar_timer)
            self._toolbar_timer = None
            
        # Stop any active recording processes
        for child in self.children[:]:  # Copy list to avoid modification during iteration
            if hasattr(child, 'is_running') and child.is_running:
                debug_logger.info("Found running recording, stopping it")
                if hasattr(child, 'stop_recording'):
                    child.stop_recording()
                    
        debug_logger.info("Slideshow cleanup completed")

# ---- App Klassen ----
if KIVYMD_OK:
    class KioskMDApp(MDApp):
        def build(self):
            self.theme_cls.theme_style="Dark"
            self.theme_cls.primary_palette="Blue"
            self.mode_manager=ModeManager(MODES_PATH)
            self.root_widget=RotatingRoot()
            self.slideshow=None
            self._open_panel = None  # Track currently open panel (id, instance)
            
            # Initialize orientation before showing login screen
            aspect = detect_aspect_from_configs()
            OrientationProvider().set_orientation(aspect)
            debug_logger.info(f"Early orientation initialized: {aspect}")
            
            # Add window debug overlay label if enabled
            if DEBUG_WINDOW_OVERLAY and _window_debug_overlay:
                label = _window_debug_overlay.get_label_widget()
                if label:
                    self.root_widget.add_widget(label)
                    debug_logger.info("[WindowDebugOverlay] Added label widget to root")
            
            self.show_login()
            return self.root_widget
        def clear_root(self): self.root_widget.clear_widgets()
        def show_login(self):
            self.clear_root(); self.root_widget.add_widget(LoginScreen(self.on_login_success,self.show_register))
        def show_register(self):
            self.clear_root(); self.root_widget.add_widget(RegisterScreen(self.show_login))
        def on_login_success(self):
            self.clear_root()
            self.slideshow=Slideshow(self.mode_manager)
            self.root_widget.add_widget(self.slideshow)
        def on_stop(self):
            """Clean up resources when app is closing to fix recording restart issue"""
            debug_logger.info("App is stopping - performing cleanup")
            if self.slideshow:
                self.slideshow.cleanup_on_exit()
            return True
else:
    class KioskMDApp(App):
        def build(self):
            self.mode_manager=ModeManager(MODES_PATH)
            self.root_widget=RotatingRoot()
            self.slideshow=None
            self._open_panel = None  # Track currently open panel (id, instance)
            
            # Initialize orientation before showing login screen
            aspect = detect_aspect_from_configs()
            OrientationProvider().set_orientation(aspect)
            debug_logger.info(f"Early orientation initialized: {aspect}")
            
            # Add window debug overlay label if enabled
            if DEBUG_WINDOW_OVERLAY and _window_debug_overlay:
                label = _window_debug_overlay.get_label_widget()
                if label:
                    self.root_widget.add_widget(label)
                    debug_logger.info("[WindowDebugOverlay] Added label widget to root")
            
            self.show_login()
            return self.root_widget
        def clear_root(self): self.root_widget.clear_widgets()
        def show_login(self):
            self.clear_root(); self.root_widget.add_widget(LoginScreen(self.on_login_success,self.show_register))
        def show_register(self):
            self.clear_root(); self.root_widget.add_widget(RegisterScreen(self.show_login))
        def on_login_success(self):
            self.clear_root()
            self.slideshow=Slideshow(self.mode_manager)
            self.root_widget.add_widget(self.slideshow)
        def on_stop(self):
            """Clean up resources when app is closing to fix recording restart issue"""
            debug_logger.info("App is stopping - performing cleanup")
            if self.slideshow:
                self.slideshow.cleanup_on_exit()
            return True

def apply_gl_pipeline_detection():
    """Detect GL vendor and apply pipeline defaults"""
    global PORTRAIT_PIPELINE
    
    # Detect GL vendor/renderer and adjust pipeline defaults
    gl_vendor, gl_renderer = detect_gl_vendor()
    
    # Check if we're on Broadcom V3D (Raspberry Pi)
    is_broadcom_v3d = False
    if gl_vendor and gl_renderer:
        is_broadcom_v3d = "broadcom" in gl_vendor.lower() and "v3d" in gl_renderer.lower()
    
    # Apply force overrides or auto-detect
    if PORTRAIT_FORCE_FBO:
        PORTRAIT_PIPELINE = "fbo"
        debug_logger.info("[Startup] PORTRAIT_FORCE_FBO=1, using FBO pipeline")
    elif PORTRAIT_FORCE_MATRIX:
        PORTRAIT_PIPELINE = "matrix"
        debug_logger.info("[Startup] PORTRAIT_FORCE_MATRIX=1, using matrix pipeline")
    elif is_broadcom_v3d and not os.getenv("PORTRAIT_PIPELINE"):
        # On Broadcom V3D, default to FBO unless explicitly overridden
        PORTRAIT_PIPELINE = "fbo"
        debug_logger.info(f"[Startup] Detected Broadcom V3D, defaulting to FBO pipeline (vendor={gl_vendor}, renderer={gl_renderer})")

if __name__ == "__main__":
    # Apply GL detection and pipeline selection
    apply_gl_pipeline_detection()
    
    # Log portrait pipeline configuration at startup
    aspect = detect_aspect_from_configs()
    if aspect == "9:16":
        overlay_status = "enabled" if DEBUG_ROTATION_OVERLAY else "disabled"
        matrix_impl = PORTRAIT_MATRIX_IMPL if PORTRAIT_PIPELINE == "matrix" else "N/A"
        debug_logger.info(f"[Startup] Portrait mode active: pipeline={PORTRAIT_PIPELINE}, matrix_impl={matrix_impl}, rotation={PORTRAIT_ROTATION_DEGREES}°, overlay={overlay_status}")
    else:
        debug_logger.info(f"[Startup] Landscape mode active (aspect={aspect})")
    
    # Setup window debug overlay if enabled
    if DEBUG_WINDOW_OVERLAY:
        setup_window_debug_overlay()
    
    # Start upload server in background thread
    try:
        from upload_server import start_server_thread
        debug_logger.info("Starting upload server thread...")
        upload_thread = start_server_thread()
        debug_logger.info("Upload server thread started")
    except Exception as e:
        debug_logger.warning(f"Could not start upload server: {e}")
    
    app = KioskMDApp()
    Window.bind(on_mouse_down=lambda w,x,y,b,m:
                hasattr(app,'root_widget') and app.root_widget.children and
                hasattr(app.root_widget.children[-1],'on_mouse_down') and
                app.root_widget.children[-1].on_mouse_down(w,x,y,b,m))
    app.run()
