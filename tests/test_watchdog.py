import subprocess
import time
from unittest.mock import MagicMock

from talkeys import watchdog


class ScriptedMicrophone:
    """Stands in for a `parec` subprocess's stdout: yields each PCM chunk
    in order, advancing a fake clock by one chunk-duration per read (as if
    that much real time had passed while it was captured), then acts like
    the process exited (empty reads) once the script runs out."""

    def __init__(self, chunks, clock, seconds_per_read):
        self._chunks = list(chunks)
        self._clock = clock
        self._seconds_per_read = seconds_per_read

    def read(self, _size):
        if not self._chunks:
            return b""
        self._clock.advance(self._seconds_per_read)
        return self._chunks.pop(0)


class FakeClock:
    def __init__(self, start_time=0.0):
        self.current_time = start_time

    def advance(self, seconds):
        self.current_time += seconds

    def __call__(self):
        return self.current_time


def silent_chunk(byte_count=watchdog.CHUNK_BYTES):
    return (0).to_bytes(2, "little", signed=True) * (byte_count // 2)


def loud_chunk(byte_count=watchdog.CHUNK_BYTES):
    return (30000).to_bytes(2, "little", signed=True) * (byte_count // 2)


def chunk_count_spanning(seconds):
    return int(seconds / watchdog.CHUNK_SECONDS) + 1


def make_watchdog(monkeypatch, chunks):
    clock = FakeClock()
    monkeypatch.setattr(time, "time", clock)
    process = MagicMock()
    process.stdout = ScriptedMicrophone(chunks, clock, watchdog.CHUNK_SECONDS)
    monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=process))
    on_silence_detected = MagicMock()
    return watchdog.SilenceWatchdog(on_silence_detected), on_silence_detected, process


def test_fires_the_callback_once_silence_lasts_the_full_threshold(monkeypatch):
    calibration = silent_chunk(watchdog.CALIBRATION_BYTES)
    full_threshold_of_silence = [silent_chunk()] * chunk_count_spanning(watchdog.SILENCE_SECONDS)
    watch, on_silence_detected, _process = make_watchdog(
        monkeypatch, [calibration] + full_threshold_of_silence
    )

    watch.run()

    on_silence_detected.assert_called_once()


def test_does_not_fire_before_silence_has_lasted_the_full_threshold(monkeypatch):
    calibration = silent_chunk(watchdog.CALIBRATION_BYTES)
    one_chunk_short_of_threshold = [silent_chunk()] * (
        chunk_count_spanning(watchdog.SILENCE_SECONDS) - 1
    )
    watch, on_silence_detected, _process = make_watchdog(
        monkeypatch, [calibration] + one_chunk_short_of_threshold
    )

    watch.run()

    on_silence_detected.assert_not_called()


def test_loud_audio_resets_the_silence_timer(monkeypatch):
    calibration = silent_chunk(watchdog.CALIBRATION_BYTES)
    half_the_threshold = [silent_chunk()] * chunk_count_spanning(watchdog.SILENCE_SECONDS / 2 - 1)
    chunks = (
        [calibration]
        + half_the_threshold
        + [loud_chunk()]  # speech resumes, the silence clock must restart
        + [silent_chunk()] * chunk_count_spanning(watchdog.SILENCE_SECONDS / 2)
    )
    watch, on_silence_detected, _process = make_watchdog(monkeypatch, chunks)

    watch.run()

    on_silence_detected.assert_not_called()


def test_calibrating_against_a_loud_room_raises_the_silence_threshold(monkeypatch):
    # Ambient noise loud enough that a fixed threshold would never
    # classify it as silence — calibration must raise the bar to match,
    # so audio at that same ambient level still reads as "silent".
    loud_ambient_calibration = loud_chunk(watchdog.CALIBRATION_BYTES)
    chunks_at_ambient_level = [loud_chunk()] * chunk_count_spanning(watchdog.SILENCE_SECONDS)
    watch, on_silence_detected, _process = make_watchdog(
        monkeypatch, [loud_ambient_calibration] + chunks_at_ambient_level
    )

    watch.run()

    on_silence_detected.assert_called_once()


def test_never_treats_ambient_noise_as_silence_below_the_absolute_floor(monkeypatch):
    # A silent room's calibration must not push the threshold to zero —
    # genuinely soft speech should still count as "not silence".
    calibration = silent_chunk(watchdog.CALIBRATION_BYTES)
    soft_speech_amplitude = int(watchdog.SILENCE_RMS_FLOOR) + 50
    speech_chunk = soft_speech_amplitude.to_bytes(2, "little", signed=True) * (
        watchdog.CHUNK_BYTES // 2
    )
    chunks = [calibration] + [speech_chunk] * chunk_count_spanning(watchdog.SILENCE_SECONDS)
    watch, on_silence_detected, _process = make_watchdog(monkeypatch, chunks)

    watch.run()

    on_silence_detected.assert_not_called()


def test_terminates_its_parec_process_when_the_stream_ends_on_its_own(monkeypatch):
    calibration = silent_chunk(watchdog.CALIBRATION_BYTES)
    watch, _on_silence_detected, process = make_watchdog(monkeypatch, [calibration])

    watch.run()

    process.terminate.assert_called_once()


def test_stop_terminates_the_parec_process(monkeypatch):
    calibration = silent_chunk(watchdog.CALIBRATION_BYTES)
    watch, _on_silence_detected, process = make_watchdog(monkeypatch, [calibration])
    watch.run()
    process.terminate.reset_mock()

    watch.stop()

    process.terminate.assert_called_once()


def test_stop_before_the_watchdog_has_started_does_not_raise():
    watch = watchdog.SilenceWatchdog(on_silence_detected=MagicMock())

    watch.stop()  # must not raise
