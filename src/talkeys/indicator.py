"""A borderless, click-through, animated overlay shown while recording.
Owns the silence watchdog as a background thread (see watchdog.py) so
auto-stop is a plain in-process call, not IPC to a separate process."""
import math
import time

import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk

from . import recorder
from .watchdog import SilenceWatchdog

WIDTH = 220
HEIGHT = 48
BAR_COUNT = 24
REDRAW_INTERVAL_MS = 80


class Indicator(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.POPUP)
        self.set_default_size(WIDTH, HEIGHT)
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_accept_focus(False)
        self.set_app_paintable(True)
        self.stick()

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None:
            self.set_visual(visual)

        self.connect("draw", self._on_draw)
        self.connect("realize", self._on_realize)

        self._start_time = time.time()
        GLib.timeout_add(REDRAW_INTERVAL_MS, self._on_tick)

        self._watchdog = SilenceWatchdog(on_silence_detected=self._on_silence_detected)
        self._watchdog.start()

        self._move_to_bottom_center()

    def shutdown(self) -> None:
        """Called when something external (a SIGTERM from the toggle
        command's manual stop) is ending this process — stop the
        watchdog's own `parec` capture so it isn't left running."""
        self._watchdog.stop()

    def _move_to_bottom_center(self) -> None:
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geometry = monitor.get_geometry()
        self.move(
            geometry.x + geometry.width // 2 - WIDTH // 2,
            geometry.y + geometry.height - HEIGHT - 60,
        )

    def _on_realize(self, *_args) -> None:
        window = self.get_window()
        # pycairo's bundled stub declares Region()'s "rectangle" argument
        # as required, but the zero-arg form (an empty region) is valid at
        # runtime — this is exactly what makes the window click-through.
        window.input_shape_combine_region(cairo.Region(), 0, 0)  # type: ignore[call-arg]

    def _on_tick(self) -> bool:
        self.queue_draw()
        return True

    def _on_silence_detected(self) -> None:
        # The watchdog calls this from its own background thread; GTK/GLib
        # calls must happen on the main thread, so hop back over via
        # `idle_add` instead of touching the window directly here.
        GLib.idle_add(self._end_session_and_quit)

    def _end_session_and_quit(self) -> bool:
        recorder.end_dictation()
        Gtk.main_quit()
        return False

    def _on_draw(self, _widget, cr) -> bool:
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        elapsed = time.time() - self._start_time
        center_x = WIDTH / 2
        for bar_index in range(BAR_COUNT):
            fraction = bar_index / (BAR_COUNT - 1)
            x = 10 + fraction * (WIDTH - 20)
            distance_from_center = abs(x - center_x) / center_x
            phase = elapsed * 6.0 - distance_from_center * 5.0
            amplitude = (0.35 + 0.65 * max(0.0, 1.0 - distance_from_center)) * (
                0.5 + 0.5 * math.sin(phase)
            )
            bar_height = 4 + amplitude * (HEIGHT - 14)

            hue_shift = 0.5 + 0.5 * math.sin(elapsed * 1.3 + fraction * 3.0)
            cr.set_source_rgba(0.45 + 0.35 * hue_shift, 0.25 + 0.2 * (1 - hue_shift), 0.95, 0.75)
            cr.set_line_width(4)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.move_to(x, HEIGHT / 2 - bar_height / 2)
            cr.line_to(x, HEIGHT / 2 + bar_height / 2)
            cr.stroke()

        return False
