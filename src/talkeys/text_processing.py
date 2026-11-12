"""Joins recognized phrases into running text.

The recognizer sees each phrase on its own, so it starts every phrase with a
capital letter and knows nothing about the space that should separate it
from the text already typed.
"""

SENTENCE_END = ".!?…"


def join(typed: str, phrase: str) -> str:
    """Returns what to insert after `typed` so that `phrase` continues it:
    a separating space, and a lowercase first letter when `typed` ends
    mid-sentence ("надеюсь" + "Решить" -> " решить").

    shortcut: a proper noun that opens a phrase mid-sentence gets lowercased
    too ("в" + "Москве" -> " москве"); fix with a word list if it bites."""
    phrase = phrase.strip()
    if not phrase or not typed:
        return phrase
    if typed[-1] not in SENTENCE_END and phrase[:1].isupper() and phrase[1:2].islower():
        phrase = phrase[0].lower() + phrase[1:]
    return " " + phrase
