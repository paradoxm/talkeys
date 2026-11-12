"""Filesystem locations and small pieces of persistent state shared across
the toggle, indicator, and watchdog processes."""
import os
import tempfile
from pathlib import Path

# Historical folder names from when Talkeys ran on nerd-dictation; kept so
# existing installs and their bound hotkeys keep working.
APP_DIR = Path.home() / ".local/share/nerd-dictation"
CONFIG_DIR = Path.home() / ".config/nerd-dictation"

VENV_BIN_DIR = APP_DIR / "venv/bin"
INDICATOR_BIN = VENV_BIN_DIR / "talkeys-indicator"
TOGGLE_BIN = VENV_BIN_DIR / "talkeys-toggle"
SWITCH_LANG_BIN = VENV_BIN_DIR / "talkeys-switch-lang"

MODELS_DIR = APP_DIR / "models"

LANG_FILE = CONFIG_DIR / "lang"
LOG_FILE = APP_DIR / "dictate.log"

# A plain marker file, not a `pgrep` check, is the source of truth for
# "is a recording session active": it's written synchronously while the
# toggle command still holds its lock, before any helper process is
# spawned, so a repeat press racing in right behind it always sees the
# marker already in its new state — `pgrep` can't offer that guarantee,
# since a just-forked process isn't visible to it until fork+exec
# actually completes, which under load can take long enough for a fast
# repeat press to slip through and start a second copy.
#
# Both live in the per-user runtime dir: only this user can write there, and
# it's wiped at logout, so a marker left by a session killed mid-recording
# can't make the next login's first press "stop" a stale PID.
STATE_DIR = Path(os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir())
RECORDING_MARKER = STATE_DIR / "dictate-recording.marker"
TOGGLE_LOCK_FILE = STATE_DIR / "dictate-toggle.lock"

LANGS = ("ru", "en")
DEFAULT_LANG = "ru"


def get_lang() -> str:
    try:
        lang = LANG_FILE.read_text().strip()
    except FileNotFoundError:
        return DEFAULT_LANG
    return lang if lang in LANGS else DEFAULT_LANG


def set_lang(lang: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LANG_FILE.write_text(lang + "\n")

