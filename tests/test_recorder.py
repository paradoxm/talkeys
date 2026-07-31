import fcntl
import signal
import subprocess
from unittest.mock import MagicMock

import pytest

from talkeys import paths, recorder


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "RECORDING_MARKER", tmp_path / "recording.marker")
    monkeypatch.setattr(paths, "TOGGLE_LOCK_FILE", tmp_path / "toggle.lock")
    monkeypatch.setattr(paths, "LOG_FILE", tmp_path / "dictate.log")
    monkeypatch.setattr(paths, "INDICATOR_BIN", tmp_path / "venv/bin/talkeys-indicator")
    monkeypatch.setattr(paths, "VENV_PYTHON", tmp_path / "venv/bin/python")
    monkeypatch.setattr(paths, "NERD_DICTATION_BIN", tmp_path / "nerd-dictation/nerd-dictation")


@pytest.fixture(autouse=True)
def no_real_subprocesses(monkeypatch):
    monkeypatch.setattr(subprocess, "run", MagicMock())


def test_is_recording_is_false_when_no_marker_file_exists():
    assert recorder.is_recording() is False


def test_is_recording_is_true_once_a_marker_file_exists():
    paths.RECORDING_MARKER.write_text("1234")

    assert recorder.is_recording() is True


def test_start_recording_writes_the_spawned_indicators_pid_into_the_marker(monkeypatch):
    fake_indicator_process = MagicMock(pid=4242)
    monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=fake_indicator_process))

    recorder.start_recording()

    assert paths.RECORDING_MARKER.read_text() == "4242"


def test_start_recording_spawns_the_indicator_and_then_nerd_dictation(monkeypatch):
    spawned_commands = []

    def fake_popen(command, **_kwargs):
        spawned_commands.append(command)
        return MagicMock(pid=1)

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    recorder.start_recording()

    assert spawned_commands[0] == [str(paths.INDICATOR_BIN)]
    assert spawned_commands[1][0] == str(paths.VENV_PYTHON)
    assert str(paths.NERD_DICTATION_BIN) in spawned_commands[1]
    assert "begin" in spawned_commands[1]


def test_stop_recording_removes_the_marker_file(monkeypatch):
    paths.RECORDING_MARKER.write_text("4242")
    monkeypatch.setattr("os.kill", MagicMock())

    recorder.stop_recording()

    assert not paths.RECORDING_MARKER.exists()


def test_stop_recording_signals_the_pid_recorded_in_the_marker(monkeypatch):
    paths.RECORDING_MARKER.write_text("4242")
    kill_calls = []
    monkeypatch.setattr("os.kill", lambda pid, sig: kill_calls.append((pid, sig)))

    recorder.stop_recording()

    assert kill_calls == [(4242, signal.SIGTERM)]


def test_stop_recording_tolerates_an_indicator_that_already_exited(monkeypatch):
    paths.RECORDING_MARKER.write_text("4242")

    def raise_process_lookup_error(_pid, _sig):
        raise ProcessLookupError()

    monkeypatch.setattr("os.kill", raise_process_lookup_error)

    recorder.stop_recording()  # must not raise

    assert not paths.RECORDING_MARKER.exists()


def test_stop_recording_without_a_marker_file_does_not_signal_anything(monkeypatch):
    kill_calls = []
    monkeypatch.setattr("os.kill", lambda pid, sig: kill_calls.append((pid, sig)))

    recorder.stop_recording()

    assert kill_calls == []


def test_end_dictation_removes_the_marker_even_if_it_was_never_created():
    recorder.end_dictation()  # must not raise

    assert not paths.RECORDING_MARKER.exists()


def test_toggle_starts_recording_when_not_already_recording(monkeypatch):
    monkeypatch.setattr(recorder, "start_recording", MagicMock())
    monkeypatch.setattr(recorder, "stop_recording", MagicMock())

    recorder.toggle()

    recorder.start_recording.assert_called_once()
    recorder.stop_recording.assert_not_called()


def test_toggle_stops_recording_when_already_recording(monkeypatch):
    paths.RECORDING_MARKER.write_text("4242")
    monkeypatch.setattr(recorder, "start_recording", MagicMock())
    monkeypatch.setattr(recorder, "stop_recording", MagicMock())

    recorder.toggle()

    recorder.stop_recording.assert_called_once()
    recorder.start_recording.assert_not_called()


def test_toggle_does_nothing_when_another_invocation_already_holds_the_lock(monkeypatch):
    # A real flock on a real file, not a mock: this is exactly the
    # observable behavior that matters (a concurrent press is a no-op),
    # and flock is cheap and deterministic to exercise for real.
    concurrent_lock_holder = open(paths.TOGGLE_LOCK_FILE, "w")
    fcntl.flock(concurrent_lock_holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
    monkeypatch.setattr(recorder, "start_recording", MagicMock())
    monkeypatch.setattr(recorder, "stop_recording", MagicMock())

    try:
        recorder.toggle()
    finally:
        concurrent_lock_holder.close()

    recorder.start_recording.assert_not_called()
    recorder.stop_recording.assert_not_called()


def test_toggle_releases_the_lock_so_a_later_call_can_proceed(monkeypatch):
    monkeypatch.setattr(recorder, "start_recording", MagicMock())
    monkeypatch.setattr(recorder, "stop_recording", MagicMock())

    recorder.toggle()
    recorder.toggle()

    assert recorder.start_recording.call_count == 2
