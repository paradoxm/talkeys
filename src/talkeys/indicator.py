"""A borderless, click-through overlay shown while recording: an animated
wave, and above it the draft of the phrase being spoken. Owns the session:
the microphone capture (watchdog.py) and the dictation (dictation.py), so
auto-stop is a plain in-process call, not IPC to a separate process."""
import math
import time

import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gdk, GLib, Gtk, Pango, PangoCairo

from . import paste, paths, recorder, stt
from .dictation import Dictation
from .watchdog import SilenceWatchdog

WIDTH = 640
TEXT_HEIGHT = 56
WAVE_HEIGHT = 48
HEIGHT = TEXT_HEIGHT + WAVE_HEIGHT
WAVE_WIDTH = 220
BAR_COUNT = 24
PREVIEW_MAX_CHARS = 120  # about two lines; older words scroll off the left
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
        self._preview = ""
        GLib.timeout_add(REDRAW_INTERVAL_MS, self._on_tick)

        lang = paths.get_lang()
        self._dictation = Dictation(
            load_transcriber=lambda: stt.load(lang),
            paste=paste.paste,
            on_preview=lambda text: GLib.idle_add(self._set_preview, text),
        )
        self._watchdog = SilenceWatchdog(
            on_auto_stop=self._on_auto_stop, on_chunk=self._dictation.feed
        )
        self._watchdog.start()

        self._move_to_bottom_center()

    def shutdown(self) -> None:
        """Ends the session: stops the microphone, then waits until the
        last phrase is recognized and pasted. Called on auto-stop and on a
        SIGTERM from the toggle command's manual stop."""
        self.hide()
        while Gtk.events_pending():
            Gtk.main_iteration()
        self._watchdog.stop()
        self._watchdog.join()
        self._dictation.finish()

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

    def _on_auto_stop(self) -> None:
        # The watchdog calls this from its own background thread; GTK/GLib
        # calls must happen on the main thread, so hop back over via
        # `idle_add` instead of touching the window directly here.
        GLib.idle_add(self._end_session_and_quit)

    def _end_session_and_quit(self) -> bool:
        recorder.end_dictation()
        self.shutdown()
        Gtk.main_quit()
        return False

    def _set_preview(self, text: str) -> bool:
        self._preview = text
        return False

    def _on_draw(self, _widget, cr) -> bool:
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        if self._preview:
            self._draw_preview(cr)

        elapsed = time.time() - self._start_time
        center_x = WIDTH / 2
        half_wave = WAVE_WIDTH / 2
        for bar_index in range(BAR_COUNT):
            fraction = bar_index / (BAR_COUNT - 1)
            x = center_x - half_wave + 10 + fraction * (WAVE_WIDTH - 20)
            distance_from_center = abs(x - center_x) / half_wave
            phase = elapsed * 6.0 - distance_from_center * 5.0
            amplitude = (0.35 + 0.65 * max(0.0, 1.0 - distance_from_center)) * (
                0.5 + 0.5 * math.sin(phase)
            )
            bar_height = 4 + amplitude * (WAVE_HEIGHT - 14)

            hue_shift = 0.5 + 0.5 * math.sin(elapsed * 1.3 + fraction * 3.0)
            cr.set_source_rgba(0.45 + 0.35 * hue_shift, 0.25 + 0.2 * (1 - hue_shift), 0.95, 0.75)
            cr.set_line_width(4)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            wave_middle = TEXT_HEIGHT + WAVE_HEIGHT / 2
            cr.move_to(x, wave_middle - bar_height / 2)
            cr.line_to(x, wave_middle + bar_height / 2)
            cr.stroke()

        return False

    def _draw_preview(self, cr) -> None:
        text = self._preview
        if len(text) > PREVIEW_MAX_CHARS:
            text = "…" + text[-PREVIEW_MAX_CHARS:]
        cr.set_source_rgba(0.08, 0.08, 0.12, 0.8)
        cr.rectangle(0, 0, WIDTH, TEXT_HEIGHT)
        cr.fill()
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(Pango.FontDescription.from_string("Sans 13"))
        layout.set_width((WIDTH - 24) * Pango.SCALE)
        layout.set_wrap(Pango.WrapMode.WORD_CHAR)
        layout.set_text(text, -1)
        cr.set_source_rgba(1, 1, 1, 0.95)
        cr.move_to(12, 6)
        PangoCairo.show_layout(cr, layout)
