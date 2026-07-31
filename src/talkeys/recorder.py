"""Starts/stops a dictation session: the indicator (which owns the silence
watchdog as its own background thread — see watchdog.py) and nerd-dictation
itself, guarded by a lock against concurrent toggle presses (X11 key-repeat
firing the hotkey many times a second while held down otherwise spawns
dozens of orphaned processes)."""
import fcntl
import os
import signal
import subprocess
from typing import IO, Optional

from . import paths


def toggle() -> None:
    lock_file = _try_acquire_lock()
    if lock_file is None:
        return
    try:
        if is_recording():
            stop_recording()
        else:
            start_recording()
    finally:
        lock_file.close()


def is_recording() -> bool:
    return paths.RECORDING_MARKER.exists()


def start_recording() -> None:
    # Clean up a stray indicator from a session that ended abnormally
    # (e.g. this process itself got killed before it could record a PID
    # anywhere). This is the one place that still matches by command
    # line rather than a known PID, precisely because there's no marker
    # to read one from yet.
    subprocess.run(
        ["pkill", "-f", str(paths.INDICATOR_BIN)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    log_file = open(paths.LOG_FILE, "a")
    indicator_process = _spawn_detached([str(paths.INDICATOR_BIN)], log_file)
    # The marker's content is the indicator's PID, so an external stop can
    # signal that exact process directly — no pattern matching needed for
    # the common path. Written while `toggle()` still holds the lock, so a
    # repeat press racing in right behind this one sees "recording" (and
    # the right PID) immediately, without waiting on anything to fork.
    paths.RECORDING_MARKER.write_text(str(indicator_process.pid))

    _spawn_detached(_nerd_dictation_begin_command(), log_file)


def stop_recording() -> None:
    """External stop: called by the toggle command when the user presses
    the hotkey again, to end nerd-dictation and signal the indicator
    process from the outside. The silence watchdog's own auto-stop does
    *not* go through this function — see indicator.py, which ends the
    session in-process (via `end_dictation()` alone) and quits itself
    directly, since sending itself a signal would race its own shutdown."""
    indicator_pid = _read_indicator_pid()
    end_dictation()
    if indicator_pid is not None:
        _terminate_process(indicator_pid)


def end_dictation() -> None:
    paths.RECORDING_MARKER.unlink(missing_ok=True)
    subprocess.run([str(paths.VENV_PYTHON), str(paths.NERD_DICTATION_BIN), "end"])


def _read_indicator_pid() -> Optional[int]:
    try:
        return int(paths.RECORDING_MARKER.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


def _terminate_process(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass  # already gone


def _try_acquire_lock() -> Optional[IO]:
    lock_file = open(paths.TOGGLE_LOCK_FILE, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        return None
    return lock_file


def _nerd_dictation_begin_command() -> list:
    return [
        str(paths.VENV_PYTHON),
        str(paths.NERD_DICTATION_BIN),
        "begin",
        f"--vosk-model-dir={paths.model_dir_for_current_lang()}",
        "--simulate-input-tool=XDOTOOL",
        "--continuous",
        "--idle-time=0.3",
        "--full-sentence",
    ]


def _spawn_detached(command: list, log_file: IO) -> subprocess.Popen:
    # `subprocess.Popen` closes all inherited file descriptors other than
    # 0/1/2 in the child by default (`close_fds=True`) — unlike a bash `&`
    # background job, the child never sees our lock's fd, so there's no
    # need to explicitly close it before spawning.
    return subprocess.Popen(command, stdout=log_file, stderr=log_file, start_new_session=True)
