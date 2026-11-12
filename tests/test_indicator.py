from unittest.mock import MagicMock

import cairo
import gi
import pytest

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from talkeys import indicator as indicator_module
from talkeys import recorder
from talkeys.indicator import Indicator


@pytest.fixture
def indicator(monkeypatch):
    fake_watchdog = MagicMock()
    monkeypatch.setattr(indicator_module, "SilenceWatchdog", MagicMock(return_value=fake_watchdog))
    monkeypatch.setattr(indicator_module, "Dictation", MagicMock())
    window = Indicator()
    yield window, fake_watchdog
    window.destroy()


def test_construction_starts_the_silence_watchdog(indicator):
    _window, fake_watchdog = indicator

    fake_watchdog.start.assert_called_once()


def test_the_watchdog_feeds_its_audio_to_the_dictation(indicator):
    _window, _fake_watchdog = indicator

    watchdog_kwargs = indicator_module.SilenceWatchdog.call_args.kwargs
    assert watchdog_kwargs["on_chunk"] == indicator_module.Dictation.return_value.feed


def test_shutdown_stops_the_microphone_before_pasting_the_last_phrase(indicator):
    window, fake_watchdog = indicator
    calls = []
    fake_watchdog.stop.side_effect = lambda: calls.append("stop microphone")
    fake_watchdog.join.side_effect = lambda: calls.append("wait for microphone")
    indicator_module.Dictation.return_value.finish.side_effect = lambda: calls.append("finish")

    window.shutdown()

    assert calls == ["stop microphone", "wait for microphone", "finish"]


def test_dictation_uses_the_model_for_the_current_language(monkeypatch, indicator):
    _window, _fake_watchdog = indicator
    monkeypatch.setattr(indicator_module.stt, "load", MagicMock())
    load_transcriber = indicator_module.Dictation.call_args.kwargs["load_transcriber"]

    load_transcriber()

    indicator_module.stt.load.assert_called_once_with(indicator_module.paths.get_lang())


def test_a_preview_from_the_worker_thread_is_handed_to_the_main_loop(monkeypatch, indicator):
    window, _fake_watchdog = indicator
    scheduled = []
    monkeypatch.setattr(indicator_module.GLib, "idle_add", lambda *args: scheduled.append(args))
    on_preview = indicator_module.Dictation.call_args.kwargs["on_preview"]

    on_preview("привет")

    assert scheduled == [(window._set_preview, "привет")]
    assert window._set_preview("привет") is False
    assert window._preview == "привет"


def test_auto_stop_schedules_ending_the_session_on_the_main_loop(monkeypatch, indicator):
    window, _fake_watchdog = indicator
    scheduled_callbacks = []
    monkeypatch.setattr(indicator_module.GLib, "idle_add", scheduled_callbacks.append)

    window._on_auto_stop()

    assert scheduled_callbacks == [window._end_session_and_quit]


def test_ending_the_session_calls_end_dictation(monkeypatch, indicator):
    window, _fake_watchdog = indicator
    monkeypatch.setattr(recorder, "end_dictation", MagicMock())
    monkeypatch.setattr(indicator_module.Gtk, "main_quit", MagicMock())

    window._end_session_and_quit()

    recorder.end_dictation.assert_called_once()


def test_ending_the_session_pastes_the_last_phrase(monkeypatch, indicator):
    window, _fake_watchdog = indicator
    monkeypatch.setattr(recorder, "end_dictation", MagicMock())
    monkeypatch.setattr(indicator_module.Gtk, "main_quit", MagicMock())

    window._end_session_and_quit()

    indicator_module.Dictation.return_value.finish.assert_called_once()


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


def test_drawing_a_long_preview_paints_text_above_the_wave(indicator):
    window, _fake_watchdog = indicator
    window._set_preview("очень длинный черновик фразы " * 20)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, indicator_module.WIDTH, indicator_module.HEIGHT)

    window._on_draw(window, cairo.Context(surface))

    surface.flush()
    stride = surface.get_stride()
    text_area = bytes(surface.get_data())[: stride * indicator_module.TEXT_HEIGHT]
    assert any(text_area[3::4])  # some pixel of the text panel is not transparent
