"""Fixes a nerd-dictation `--continuous` mode quirk: it resets its own
diff-tracking state after every finalized utterance, which drops the space
that would normally separate one spoken phrase from the next.

We can't see nerd-dictation's internal "this is a new utterance" event —
only the raw text of each call — so utterance boundaries are inferred from
the text itself. A plain "shorter than last call" check is too eager:
VOSK's partial hypothesis can occasionally shrink slightly *within* a
single utterance as the decoder revises it, which would insert a spurious
mid-word space. So a boundary is either a drop to a fraction of the
utterance's peak length seen so far, or a different first word — the
second catches a short utterance ("ok") followed by a longer one
("thanks"), which never shrinks. The cost: if VOSK revises the very first
word of the session's first utterance, that utterance gets a leading
space.
"""

SHRINK_RATIO = 0.5


class SpacingFixer:
    """Tracks state across nerd-dictation's per-call text and prepends a
    separating space at each inferred utterance boundary."""

    def __init__(self) -> None:
        self._peak_length = 0
        self._first_word = ""
        self._needs_leading_space = False
        self._has_emitted_text = False

    def process(self, text: str) -> str:
        if not text:
            return text

        first_word = (text.split() or [""])[0]
        if self._peak_length and (
            len(text) < self._peak_length * SHRINK_RATIO or first_word != self._first_word
        ):
            self._needs_leading_space = self._has_emitted_text
            self._peak_length = 0

        self._peak_length = max(self._peak_length, len(text))
        self._first_word = first_word
        self._has_emitted_text = True

        return " " + text if self._needs_leading_space else text
