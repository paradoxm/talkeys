"""Fixes a nerd-dictation `--continuous` mode quirk: it resets its own
diff-tracking state after every finalized utterance, which drops the space
that would normally separate one spoken phrase from the next.

We can't see nerd-dictation's internal "this is a new utterance" event —
only the raw text of each call — so utterance boundaries are inferred from
the text getting shorter. A plain "shorter than last call" check is too
eager: VOSK's partial hypothesis can occasionally shrink slightly *within*
a single utterance as the decoder revises it, which would insert a
spurious mid-word space. Requiring the text to drop to a fraction of the
utterance's peak length seen so far makes that a much rarer false
positive, while still reliably catching a genuine boundary (which drops to
whatever the new utterance's first, short partial is).
"""

DEFAULT_SHRINK_RATIO = 0.5


class SpacingFixer:
    """Tracks state across nerd-dictation's per-call text and prepends a
    separating space at each inferred utterance boundary."""

    def __init__(self, shrink_ratio: float = DEFAULT_SHRINK_RATIO):
        self._shrink_ratio = shrink_ratio
        self._peak_length = 0
        self._needs_leading_space = False
        self._has_emitted_text = False

    def process(self, text: str) -> str:
        if not text:
            return text

        if self._peak_length and len(text) < self._peak_length * self._shrink_ratio:
            self._needs_leading_space = self._has_emitted_text
            self._peak_length = 0

        self._peak_length = max(self._peak_length, len(text))
        self._has_emitted_text = True

        return " " + text if self._needs_leading_space else text
