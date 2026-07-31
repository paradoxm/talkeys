"""nerd-dictation loads this exact path (~/.config/nerd-dictation/nerd-dictation.py)
and calls `nerd_dictation_process` from it — that contract is nerd-dictation's,
not ours, so this stays a thin shim; the actual logic is in talkeys.text_processing,
where it's a plain, independently testable class."""
from talkeys.text_processing import SpacingFixer

_fixer = SpacingFixer()


def nerd_dictation_process(text):
    return _fixer.process(text)
