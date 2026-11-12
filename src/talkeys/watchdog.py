"""Detects real silence via microphone RMS level, independently of
nerd-dictation's own --timeout (which is unreliable: it compares raw VOSK
JSON, and Kaldi's endpointer changes that JSON's shape on its own even
during total silence, resetting the built-in timer).

Runs as a background thread inside the indicator process rather than a
separate OS process: it needs its own `parec` capture either way, but
folding it into the indicator means the silence-detected callback is a
plain in-process function call (see indicator.py), not IPC back to the
toggle command — and there's one fewer process for the toggle command to
track and clean up.
"""
import math
import subprocess
import threading
import time
from collections.abc import Callable

from . import audio

SAMPLE_RATE = 16000
CHUNK_SECONDS = 0.5
CHUNK_BYTES = int(SAMPLE_RATE * CHUNK_SECONDS) * 2  # 16-bit mono
WINDOW_SECONDS = 0.1
WINDOW_BYTES = int(SAMPLE_RATE * WINDOW_SECONDS) * 2
# A fixed RMS threshold can't tell speech from a noisy room: room/fan noise
# routinely sits well above a value that would look "silent" on a quiet
# mic, so a bare constant either cuts off soft speech or never fires at
# all in a noisy room. The baseline is this room's own ambient noise: the
# quietest 0.1s window heard so far. Short windows catch the gaps between
# words, so speech that starts right at the hotkey press can't be mistaken
# for the room's noise floor (a fixed calibration second could be all
# speech). Anything under a few times that baseline counts as silence.
SILENCE_RMS_FLOOR = 150.0
SILENCE_RMS_MULTIPLIER = 2.5
SILENCE_SECONDS = 10.0


class SilenceWatchdog(threading.Thread):
    """Captures the microphone independently of nerd-dictation and calls
    `on_silence_detected` once real silence has lasted `SILENCE_SECONDS`.

    Call `.start()` to begin monitoring, `.stop()` to end it early (e.g.
    because the user pressed the toggle hotkey themselves).
    """

    def __init__(self, on_silence_detected: Callable[[], None]):
        super().__init__(daemon=True)
        self._on_silence_detected = on_silence_detected
        self._process: subprocess.Popen | None = None

    def run(self) -> None:
        self._process = subprocess.Popen(
            ["parec", "--raw", "--format=s16le", f"--rate={SAMPLE_RATE}", "--channels=1"],
            stdout=subprocess.PIPE,
        )
        try:
            self._monitor_until_silent_or_stopped()
        finally:
            self._process.terminate()

    def stop(self) -> None:
        if self._process is not None:
            self._process.terminate()

    def _monitor_until_silent_or_stopped(self) -> None:
        # Only ever called from run(), right after self._process is set up
        # with stdout=PIPE, so both are always present here.
        assert self._process is not None
        assert self._process.stdout is not None
        microphone = self._process.stdout

        ambient_rms = math.inf
        silent_since = None
        while True:
            data = microphone.read(CHUNK_BYTES)
            if not data:
                return  # `parec` exited — most likely `.stop()` was called.

            ambient_rms = min(
                [ambient_rms]
                + [
                    audio.rms(data[start : start + WINDOW_BYTES])
                    for start in range(0, len(data) - WINDOW_BYTES + 1, WINDOW_BYTES)
                ]
            )
            silence_threshold = max(SILENCE_RMS_FLOOR, ambient_rms * SILENCE_RMS_MULTIPLIER)

            now = time.monotonic()
            if audio.rms(data) < silence_threshold:
                if silent_since is None:
                    silent_since = now
                elif now - silent_since >= SILENCE_SECONDS:
                    self._on_silence_detected()
                    return
            else:
                silent_since = None
