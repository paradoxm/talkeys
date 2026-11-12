"""Turns the microphone stream into phrases while the user is talking.

The silence watchdog's capture thread hands every chunk to `feed`. Audio
collects into the current phrase; a short pause ends it. A worker thread
then recognizes the finished phrase and pastes it once. While a phrase is
still being spoken, the worker re-recognizes it about once a second and
reports the draft through `on_preview`, so the text shows up live without
retyping anything in the target window.
"""
import threading
from collections.abc import Callable

from . import text_processing

BYTES_PER_SECOND = 16000 * 2  # 16 kHz mono s16le
PAUSE_SECONDS = 0.8
MAX_PHRASE_SECONDS = 20.0
PREVIEW_EVERY_SECONDS = 1.0
# The tail of the previous phrase is recognized again in front of the next
# one, so a sentence cut by a pause keeps its grammar ("новым, скажем,
# движком", not "новым скажи движком"). Costs ~0.25s of recognition.
CONTEXT_SECONDS = 3.0


class Dictation:
    def __init__(
        self,
        load_transcriber: Callable[[], Callable[[bytes, bytes], str]],
        paste: Callable[[str], None],
        on_preview: Callable[[str], None],
    ):
        self._load_transcriber = load_transcriber
        self._paste = paste
        self._on_preview = on_preview
        self._condition = threading.Condition()
        self._phrase = bytearray()
        self._has_speech = False
        self._silent_bytes = 0
        self._previewed_bytes = 0
        self._finished_phrases: list[bytes] = []
        self._finishing = False
        self._typed = ""
        self._context = b""  # worker thread only
        # Not a daemon: the last phrase must be pasted before the process exits.
        self._worker = threading.Thread(target=self._run)
        self._worker.start()

    def feed(self, chunk: bytes, silent: bool) -> None:
        with self._condition:
            if silent and not self._has_speech:
                self._phrase = bytearray(chunk)  # keep only a short lead-in
                return
            self._phrase += chunk
            if silent:
                self._silent_bytes += len(chunk)
            else:
                self._has_speech = True
                self._silent_bytes = 0
            if (
                self._silent_bytes >= PAUSE_SECONDS * BYTES_PER_SECOND
                or len(self._phrase) >= MAX_PHRASE_SECONDS * BYTES_PER_SECOND
            ):
                self._end_phrase()
            self._condition.notify()

    def finish(self) -> None:
        """Ends the session: recognizes and pastes whatever was said last,
        then returns once everything is pasted."""
        with self._condition:
            if self._has_speech:
                self._end_phrase()
            self._finishing = True
            self._condition.notify()
        self._worker.join()

    def _end_phrase(self) -> None:
        self._finished_phrases.append(bytes(self._phrase))
        self._phrase = bytearray()
        self._has_speech = False
        self._silent_bytes = 0
        self._previewed_bytes = 0

    def _preview_due(self) -> bool:
        return (
            self._has_speech
            and len(self._phrase) - self._previewed_bytes >= PREVIEW_EVERY_SECONDS * BYTES_PER_SECOND
        )

    def _run(self) -> None:
        # An exception here (e.g. the model failed to load) ends the thread;
        # threading prints it to stderr (dictate.log), and finish() returns.
        transcribe = self._load_transcriber()
        while True:
            with self._condition:
                self._condition.wait_for(
                    lambda: self._finished_phrases or self._finishing or self._preview_due()
                )
                if self._finished_phrases:
                    audio, final = self._finished_phrases.pop(0), True
                elif self._finishing:
                    return
                else:
                    audio, final = bytes(self._phrase), False
                    self._previewed_bytes = len(self._phrase)
            text = transcribe(audio, self._context)
            if final:
                self._context = audio[-int(CONTEXT_SECONDS * BYTES_PER_SECOND) :]
                piece = text_processing.join(self._typed, text)
                if piece:
                    self._paste(piece)
                    self._typed += piece
                self._on_preview("")
            else:
                self._on_preview(text)
