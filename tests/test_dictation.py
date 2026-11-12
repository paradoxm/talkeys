import threading

from talkeys import dictation
from talkeys.dictation import Dictation

CHUNK = int(0.2 * dictation.BYTES_PER_SECOND)


def speech(marker=1):
    return bytes([marker, 0]) * (CHUNK // 2)


def silence():
    return b"\0" * CHUNK


def pause_chunks():
    return int(dictation.PAUSE_SECONDS * dictation.BYTES_PER_SECOND) // CHUNK


class Recorder:
    """Fake transcriber + paste target; `transcribe` answers by the marker
    byte the test put into the speech."""

    def __init__(self, text_by_marker=None):
        self.text_by_marker = {1: "Привет."} if text_by_marker is None else text_by_marker
        self.transcribed: list[bytes] = []
        self.contexts: list[bytes] = []
        self.pasted: list[str] = []
        self.previews: list[str] = []
        self.pasted_event = threading.Event()
        self.preview_event = threading.Event()

    def transcribe(self, audio: bytes, context: bytes) -> str:
        self.transcribed.append(audio)
        self.contexts.append(context)
        markers = [m for m in self.text_by_marker if bytes([m]) in audio]
        return self.text_by_marker[markers[-1]] if markers else ""

    def paste(self, text: str) -> None:
        self.pasted.append(text)
        self.pasted_event.set()

    def on_preview(self, text: str) -> None:
        self.previews.append(text)
        if text:
            self.preview_event.set()

    def dictation(self) -> Dictation:
        return Dictation(lambda: self.transcribe, self.paste, self.on_preview)


def test_a_pause_pastes_the_phrase_without_waiting_for_the_session_to_end():
    fake = Recorder()
    session = fake.dictation()

    for _ in range(3):
        session.feed(speech(), silent=False)
    for _ in range(pause_chunks()):
        session.feed(silence(), silent=True)

    assert fake.pasted_event.wait(timeout=5)
    assert fake.pasted == ["Привет."]
    session.finish()


def test_finishing_pastes_the_phrase_still_being_spoken():
    fake = Recorder()
    session = fake.dictation()
    session.feed(speech(), silent=False)

    session.finish()

    assert fake.pasted == ["Привет."]


def test_phrases_join_into_running_text():
    fake = Recorder({1: "Привет, как", 2: "Дела?"})
    session = fake.dictation()
    session.feed(speech(1), silent=False)
    for _ in range(pause_chunks()):
        session.feed(silence(), silent=True)
    session.feed(speech(2), silent=False)

    session.finish()

    assert fake.pasted == ["Привет, как", " дела?"]


def test_only_one_chunk_of_leading_silence_is_kept_before_speech():
    fake = Recorder()
    session = fake.dictation()
    for _ in range(10):
        session.feed(silence(), silent=True)
    session.feed(speech(), silent=False)

    session.finish()

    assert len(fake.transcribed[-1]) == 2 * CHUNK


def test_a_phrase_without_a_pause_is_cut_at_the_maximum_length():
    fake = Recorder()
    session = fake.dictation()
    max_chunks = int(dictation.MAX_PHRASE_SECONDS * dictation.BYTES_PER_SECOND) // CHUNK

    for _ in range(max_chunks):
        session.feed(speech(), silent=False)

    assert fake.pasted_event.wait(timeout=5)
    session.finish()
    assert len(fake.transcribed[0]) <= dictation.MAX_PHRASE_SECONDS * dictation.BYTES_PER_SECOND


def test_a_draft_is_shown_while_the_phrase_is_still_being_spoken():
    fake = Recorder()
    session = fake.dictation()
    preview_chunks = int(dictation.PREVIEW_EVERY_SECONDS * dictation.BYTES_PER_SECOND) // CHUNK

    for _ in range(preview_chunks):
        session.feed(speech(), silent=False)

    assert fake.preview_event.wait(timeout=5)
    assert fake.pasted == []
    session.finish()
    assert fake.previews[-1] == ""  # the draft is cleared once the phrase is pasted


def test_silence_alone_pastes_nothing():
    fake = Recorder()
    session = fake.dictation()
    for _ in range(20):
        session.feed(silence(), silent=True)

    session.finish()

    assert fake.pasted == []


def test_a_phrase_recognized_as_empty_pastes_nothing():
    fake = Recorder({})
    session = fake.dictation()
    session.feed(speech(), silent=False)

    session.finish()

    assert fake.pasted == []


def test_a_model_that_fails_to_load_does_not_hang_the_session(monkeypatch):
    errors = []
    monkeypatch.setattr(threading, "excepthook", lambda args: errors.append(args.exc_value))

    def broken_loader():
        raise RuntimeError("model missing")

    session = Dictation(broken_loader, paste=lambda _text: None, on_preview=lambda _text: None)
    session.feed(speech(), silent=False)

    session.finish()  # returns instead of waiting forever

    assert [str(error) for error in errors] == ["model missing"]


def test_the_next_phrase_is_recognized_with_the_tail_of_the_previous_one():
    fake = Recorder({1: "Привет, как", 2: "Дела?"})
    session = fake.dictation()
    first = [speech(1)] * 20 + [silence()] * pause_chunks()  # 4 s of speech, then a pause
    for chunk in first:
        session.feed(chunk, silent=chunk == silence())
    session.feed(speech(2), silent=False)

    session.finish()

    context_bytes = int(dictation.CONTEXT_SECONDS * dictation.BYTES_PER_SECOND)
    assert fake.contexts[0] == b""
    assert fake.contexts[-1] == b"".join(first)[-context_bytes:]
