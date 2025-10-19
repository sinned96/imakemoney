from kivy.uix.widget import Widget
from kivy.logger import Logger
from kivy.core.window import Window
import inspect

class InputOverlayContainer(Widget):
    """
    Non-intrusive overlay: observes Window touch events and logs mapped coords.
    Provides set_target_widget and set_inverse_matrix so main.py can call them.
    Does not consume or re-dispatch touch events.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._target = None
        self._inverse_matrix = None
        self._bound = False
        Logger.info("[portrait_input_overlay]: shim-installed (non-intrusive)")
        self._bind_window()

    def _bind_window(self):
        if self._bound:
            return
        Window.bind(on_touch_down=self._on_window_touch,
                    on_touch_move=self._on_window_touch,
                    on_touch_up=self._on_window_touch)
        self._bound = True

    def _on_window_touch(self, window, touch):
        # Log a short diagnostic line with window coords and, if available, mapped coords
        try:
            wx, wy = touch.pos
            mapped = None
            if self._inverse_matrix:
                try:
                    mx, my, _ = self._inverse_matrix.transform_point(wx, wy, 0)
                    mapped = (mx, my)
                except Exception:
                    mapped = None
            Logger.info(f"[InputOverlay] window={wx:.1f},{wy:.1f} mapped={mapped} id={getattr(touch,'id',None)} profile={getattr(touch,'profile',None)}")
        except Exception as e:
            Logger.warning(f"[InputOverlay] touch log failed: {e}")
        # Do not consume the touch — return False to allow normal routing
        return False

    def set_target_widget(self, widget_or_class):
        # Accept instance or class (resolve to instance if class provided)
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
        Logger.info(f"[portrait_input_overlay] set_target_widget -> {self._target}")

    def set_inverse_matrix(self, matrix):
        self._inverse_matrix = matrix
        Logger.info(f"[portrait_input_overlay] set_inverse_matrix -> {bool(matrix)}")
