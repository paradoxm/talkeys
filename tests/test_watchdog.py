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
    """A quiet room: low noise, not digital zeros."""
    return noise_chunk(10, byte_count)


def noise_chunk(level, byte_count=watchdog.CHUNK_BYTES):
    sample = level.to_bytes(2, "little", signed=True) + (-level).to_bytes(2, "little", signed=True)
    return sample * (byte_count // 4)


def loud_chunk(byte_count=watchdog.CHUNK_BYTES):
    return (30000).to_bytes(2, "little", signed=True) * (byte_count // 2)


def chunk_count_spanning(seconds):
    return int(seconds / watchdog.CHUNK_SECONDS) + 1


def make_watchdog(monkeypatch, chunks):
    clock = FakeClock()
    monkeypatch.setattr(time, "monotonic", clock)
    process = MagicMock()
    process.stdout = ScriptedMicrophone(chunks, clock, watchdog.CHUNK_SECONDS)
    monkeypatch.setattr(subprocess, "Popen", MagicMock(return_value=process))
    on_auto_stop = MagicMock()
    return watchdog.SilenceWatchdog(on_auto_stop), on_auto_stop, process


def test_fires_the_callback_once_silence_lasts_the_full_threshold(monkeypatch):
    quiet_room = silent_chunk()
    full_threshold_of_silence = [silent_chunk()] * chunk_count_spanning(watchdog.SILENCE_SECONDS)
    watch, on_auto_stop, _process = make_watchdog(
        monkeypatch, [quiet_room] + full_threshold_of_silence
    )

    watch.run()

    on_auto_stop.assert_called_once()


def test_does_not_fire_before_silence_has_lasted_the_full_threshold(monkeypatch):
    one_chunk_short_of_threshold = [silent_chunk()] * (
        chunk_count_spanning(watchdog.SILENCE_SECONDS) - 1
    )
    watch, on_auto_stop, _process = make_watchdog(monkeypatch, one_chunk_short_of_threshold)

    watch.run()

    on_auto_stop.assert_not_called()


def test_loud_audio_resets_the_silence_timer(monkeypatch):
    quiet_room = silent_chunk()
    half_the_threshold = [silent_chunk()] * chunk_count_spanning(watchdog.SILENCE_SECONDS / 2 - 1)
    chunks = (
        [quiet_room]
        + half_the_threshold
        + [loud_chunk()]  # speech resumes, the silence clock must restart
        + [silent_chunk()] * chunk_count_spanning(watchdog.SILENCE_SECONDS / 2)
    )
    watch, on_auto_stop, _process = make_watchdog(monkeypatch, chunks)

    watch.run()

    on_auto_stop.assert_not_called()


def test_a_loud_room_raises_the_silence_threshold(monkeypatch):
    # Ambient noise loud enough that a fixed threshold would never
    # classify it as silence — the room baseline must raise the bar to match,
    # so audio at that same ambient level still reads as "silent".
    loud_room = loud_chunk()
    chunks_at_ambient_level = [loud_chunk()] * chunk_count_spanning(watchdog.SILENCE_SECONDS)
    watch, on_auto_stop, _process = make_watchdog(
        monkeypatch, [loud_room] + chunks_at_ambient_level
    )

    watch.run()

    on_auto_stop.assert_called_once()


def test_never_treats_ambient_noise_as_silence_below_the_absolute_floor(monkeypatch):
    # A silent room must not push the threshold to zero —
    # genuinely soft speech should still count as "not silence".
    quiet_room = silent_chunk()
    soft_speech_amplitude = int(watchdog.SILENCE_RMS_FLOOR) + 50
    speech_chunk = soft_speech_amplitude.to_bytes(2, "little", signed=True) * (
        watchdog.CHUNK_BYTES // 2
    )
    chunks = [quiet_room] + [speech_chunk] * chunk_count_spanning(watchdog.SILENCE_SECONDS)
    watch, on_auto_stop, _process = make_watchdog(monkeypatch, chunks)

    watch.run()

    on_auto_stop.assert_not_called()


def test_terminates_its_parec_process_when_the_stream_ends_on_its_own(monkeypatch):
    quiet_room = silent_chunk()
    watch, _on_auto_stop, process = make_watchdog(monkeypatch, [quiet_room])

    watch.run()

    process.terminate.assert_called_once()


def test_stop_terminates_the_parec_process(monkeypatch):
    quiet_room = silent_chunk()
    watch, _on_auto_stop, process = make_watchdog(monkeypatch, [quiet_room])
    watch.run()
    process.terminate.reset_mock()

    watch.stop()

    process.terminate.assert_called_once()


def test_stop_before_the_watchdog_has_started_does_not_raise():
    watch = watchdog.SilenceWatchdog(on_auto_stop=MagicMock())

    watch.stop()  # must not raise


def test_speech_from_the_very_first_moment_is_not_mistaken_for_the_room_noise(monkeypatch):
    # The user starts talking right at the hotkey press: there is no quiet
    # lead-in to learn the room from, only the short gaps between words.
    word_bytes = watchdog.CHUNK_BYTES - watchdog.WINDOW_BYTES
    word = (2000).to_bytes(2, "little", signed=True) * (word_bytes // 2)
    gap = silent_chunk(watchdog.WINDOW_BYTES)
    talking_chunk = word + gap
    chunks = [talking_chunk] * chunk_count_spanning(2 * watchdog.SILENCE_SECONDS)
    watch, on_auto_stop, _process = make_watchdog(monkeypatch, chunks)

    watch.run()

    on_auto_stop.assert_not_called()


def test_every_chunk_is_handed_on_with_whether_it_was_silent(monkeypatch):
    chunks = [silent_chunk(), loud_chunk(), silent_chunk()]
    watch, _on_auto_stop, _process = make_watchdog(monkeypatch, chunks)
    received = []
    watch._on_chunk = lambda chunk, silent: received.append((chunk, silent))

    watch.run()

    assert received == [(chunks[0], True), (chunks[1], False), (chunks[2], True)]


def test_a_session_that_never_goes_quiet_stops_at_the_time_limit(monkeypatch):
    # A forgotten session next to a TV: never silent, must still end.
    tv = [silent_chunk(), loud_chunk()] * chunk_count_spanning(watchdog.MAX_SESSION_SECONDS)
    watch, on_auto_stop, _process = make_watchdog(monkeypatch, tv)
    fed = []
    watch._on_chunk = lambda chunk, _silent: fed.append(chunk)

    watch.run()

    on_auto_stop.assert_called_once()
    assert len(fed) * watchdog.CHUNK_SECONDS <= watchdog.MAX_SESSION_SECONDS + 1


def test_digital_zeros_at_stream_start_do_not_count_as_the_room_noise(monkeypatch):
    # A noisy room (RMS 60, above the absolute floor): after parec's initial
    # burst of zeros, that noise must still read as silence.
    zeros = b"\0" * watchdog.CHUNK_BYTES
    chunks = [zeros] + [noise_chunk(60)] * chunk_count_spanning(watchdog.SILENCE_SECONDS)
    watch, on_auto_stop, _process = make_watchdog(monkeypatch, chunks)

    watch.run()

    on_auto_stop.assert_called_once()
