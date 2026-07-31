import signal
import subprocess
import sys
from unittest.mock import MagicMock

from talkeys import keybindings, paths, recorder
from talkeys.cli import bind_hotkeys, indicator as cli_indicator, switch_lang, toggle, unbind_hotkeys


def test_toggle_main_delegates_to_recorder_toggle(monkeypatch):
    monkeypatch.setattr(recorder, "toggle", MagicMock())

    toggle.main()

    recorder.toggle.assert_called_once()


def test_switch_lang_main_flips_russian_to_english(monkeypatch):
    monkeypatch.setattr(paths, "get_lang", MagicMock(return_value="ru"))
    monkeypatch.setattr(paths, "set_lang", MagicMock())
    monkeypatch.setattr(subprocess, "run", MagicMock())

    switch_lang.main()

    paths.set_lang.assert_called_once_with("en")


def test_switch_lang_main_flips_english_to_russian(monkeypatch):
    monkeypatch.setattr(paths, "get_lang", MagicMock(return_value="en"))
    monkeypatch.setattr(paths, "set_lang", MagicMock())
    monkeypatch.setattr(subprocess, "run", MagicMock())

    switch_lang.main()

    paths.set_lang.assert_called_once_with("ru")


def test_switch_lang_main_shows_a_notification_naming_the_new_language(monkeypatch):
    monkeypatch.setattr(paths, "get_lang", MagicMock(return_value="ru"))
    monkeypatch.setattr(paths, "set_lang", MagicMock())
    run_calls = []
    monkeypatch.setattr(subprocess, "run", lambda command: run_calls.append(command))

    switch_lang.main()

    assert run_calls[0][0] == "notify-send"
    assert run_calls[0][-1] == "en"


def test_bind_hotkeys_main_binds_the_toggle_and_switch_lang_targets(monkeypatch):
    fake_backend = MagicMock()
    monkeypatch.setattr(keybindings, "get_backend", MagicMock(return_value=fake_backend))

    exit_code = bind_hotkeys.main()

    assert exit_code == 0
    bound_targets = fake_backend.bind.call_args[0][0]
    bound_commands = {target.command for target in bound_targets}
    assert bound_commands == {str(paths.TOGGLE_BIN), str(paths.SWITCH_LANG_BIN)}


def test_bind_hotkeys_main_fails_with_instructions_when_no_backend_is_available(monkeypatch, capsys):
    monkeypatch.setattr(keybindings, "get_backend", MagicMock(return_value=None))

    exit_code = bind_hotkeys.main()

    assert exit_code == 1
    assert "manually" in capsys.readouterr().out


def test_unbind_hotkeys_main_removes_shortcuts_matching_talkeys_commands(monkeypatch):
    fake_backend = MagicMock()
    fake_backend.unbind_matching.return_value = 2
    monkeypatch.setattr(keybindings, "get_backend", MagicMock(return_value=fake_backend))

    exit_code = unbind_hotkeys.main()

    assert exit_code == 0
    matched_commands = fake_backend.unbind_matching.call_args[0][0]
    assert matched_commands == {str(paths.TOGGLE_BIN), str(paths.SWITCH_LANG_BIN)}


def test_unbind_hotkeys_main_fails_when_no_backend_is_available(monkeypatch):
    monkeypatch.setattr(keybindings, "get_backend", MagicMock(return_value=None))

    exit_code = unbind_hotkeys.main()

    assert exit_code == 1


def test_indicator_main_shows_the_window_and_runs_the_gtk_main_loop(monkeypatch):
    fake_window = MagicMock()
    monkeypatch.setattr(cli_indicator, "Indicator", MagicMock(return_value=fake_window))
    monkeypatch.setattr(cli_indicator.Gtk, "main", MagicMock())
    monkeypatch.setattr(signal, "signal", MagicMock())

    cli_indicator.main()

    fake_window.show_all.assert_called_once()
    cli_indicator.Gtk.main.assert_called_once()


def test_indicator_main_shuts_the_window_down_on_sigterm(monkeypatch):
    fake_window = MagicMock()
    monkeypatch.setattr(cli_indicator, "Indicator", MagicMock(return_value=fake_window))
    monkeypatch.setattr(cli_indicator.Gtk, "main", MagicMock())
    registered_handlers = {}
    monkeypatch.setattr(
        signal, "signal", lambda sig, handler: registered_handlers.setdefault(sig, handler)
    )
    monkeypatch.setattr(sys, "exit", MagicMock(side_effect=SystemExit))

    cli_indicator.main()
    sigterm_handler = registered_handlers[signal.SIGTERM]
    try:
        sigterm_handler()
    except SystemExit:
        pass

    fake_window.shutdown.assert_called_once()
