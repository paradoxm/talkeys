from unittest.mock import MagicMock

import cairo
import gi
import pytest

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from talkeys import indicator as indicator_module, recorder
from talkeys.indicator import Indicator


@pytest.fixture
def indicator(monkeypatch):
    fake_watchdog = MagicMock()
    monkeypatch.setattr(indicator_module, "SilenceWatchdog", MagicMock(return_value=fake_watchdog))
    window = Indicator()
    yield window, fake_watchdog
    window.destroy()


def test_construction_starts_the_silence_watchdog(indicator):
    _window, fake_watchdog = indicator

    fake_watchdog.start.assert_called_once()


def test_shutdown_stops_the_silence_watchdog(indicator):
    window, fake_watchdog = indicator

    window.shutdown()

    fake_watchdog.stop.assert_called_once()


def test_silence_detected_schedules_ending_the_session_on_the_main_loop(monkeypatch, indicator):
    window, _fake_watchdog = indicator
    scheduled_callbacks = []
    monkeypatch.setattr(indicator_module.GLib, "idle_add", scheduled_callbacks.append)

    window._on_silence_detected()

    assert scheduled_callbacks == [window._end_session_and_quit]


def test_ending_the_session_calls_end_dictation(monkeypatch, indicator):
    window, _fake_watchdog = indicator
    monkeypatch.setattr(recorder, "end_dictation", MagicMock())
    monkeypatch.setattr(indicator_module.Gtk, "main_quit", MagicMock())

    window._end_session_and_quit()

    recorder.end_dictation.assert_called_once()


def test_ending_the_session_quits_the_gtk_main_loop(monkeypatch, indicator):
    window, _fake_watchdog = indicator
    monkeypatch.setattr(recorder, "end_dictation", MagicMock())
    monkeypatch.setattr(indicator_module.Gtk, "main_quit", MagicMock())

    window._end_session_and_quit()

    indicator_module.Gtk.main_quit.assert_called_once()


def test_ending_the_session_reports_glib_should_not_call_it_again(monkeypatch, indicator):
    window, _fake_watchdog = indicator
    monkeypatch.setattr(recorder, "end_dictation", MagicMock())
    monkeypatch.setattr(indicator_module.Gtk, "main_quit", MagicMock())

    # `GLib.idle_add` treats this callback's return value the same way a
    # `GLib.timeout_add` callback's is: `False` means "don't call again".
    result = window._end_session_and_quit()

    assert result is False


def test_tick_queues_a_redraw_and_asks_glib_to_call_it_again(indicator):
    window, _fake_watchdog = indicator

    result = window._on_tick()

    assert result is True


def test_showing_the_window_realizes_it_without_raising(indicator):
    window, _fake_watchdog = indicator

    window.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration()

    assert window.get_realized()


def test_drawing_the_wave_does_not_raise(indicator):
    window, _fake_watchdog = indicator
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, indicator_module.WIDTH, indicator_module.HEIGHT)
    cairo_context = cairo.Context(surface)

    result = window._on_draw(window, cairo_context)

    assert result is False
