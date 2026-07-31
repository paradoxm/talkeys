"""Filesystem locations and small pieces of persistent state shared across
the toggle, indicator, and watchdog processes."""
from pathlib import Path

NERD_DIR = Path.home() / ".local/share/nerd-dictation"
CONFIG_DIR = Path.home() / ".config/nerd-dictation"

NERD_DICTATION_BIN = NERD_DIR / "nerd-dictation/nerd-dictation"
VENV_BIN_DIR = NERD_DIR / "venv/bin"
VENV_PYTHON = VENV_BIN_DIR / "python"
INDICATOR_BIN = VENV_BIN_DIR / "talkeys-indicator"
TOGGLE_BIN = VENV_BIN_DIR / "talkeys-toggle"
SWITCH_LANG_BIN = VENV_BIN_DIR / "talkeys-switch-lang"
MODELS_DIR = NERD_DIR / "models"

LANG_FILE = CONFIG_DIR / "lang"
LOG_FILE = NERD_DIR / "dictate.log"

# A plain marker file, not a `pgrep` check, is the source of truth for
# "is a recording session active": it's written synchronously while the
# toggle command still holds its lock, before any helper process is
# spawned, so a repeat press racing in right behind it always sees the
# marker already in its new state — `pgrep` can't offer that guarantee,
# since a just-forked process isn't visible to it until fork+exec
# actually completes, which under load can take long enough for a fast
# repeat press to slip through and start a second copy.
RECORDING_MARKER = Path("/tmp/dictate-recording.marker")
TOGGLE_LOCK_FILE = Path("/tmp/dictate-toggle.lock")

MODEL_DIR_BY_LANG = {
    "en": MODELS_DIR / "vosk-model-small-en-us-0.15",
    "ru": MODELS_DIR / "vosk-model-small-ru-0.22",
}
DEFAULT_LANG = "ru"


def get_lang() -> str:
    try:
        lang = LANG_FILE.read_text().strip()
    except FileNotFoundError:
        return DEFAULT_LANG
    return lang if lang in MODEL_DIR_BY_LANG else DEFAULT_LANG


def set_lang(lang: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LANG_FILE.write_text(lang + "\n")


def model_dir_for_current_lang() -> Path:
    return MODEL_DIR_BY_LANG[get_lang()]
