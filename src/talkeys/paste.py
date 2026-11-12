"""Inserts text into the focused window through the clipboard: one paste
keystroke instead of typing every character with xdotool, which floods the
input method (ibus) with key events and can stall the whole X session."""
import re
import subprocess
import time

# Terminals paste with Ctrl+Shift+V; Ctrl+V there is a control character.
TERMINAL_CLASSES = {
    "gnome-terminal",
    "gnome-terminal-server",
    "xterm",
    "uxterm",
    "urxvt",
    "konsole",
    "kitty",
    "alacritty",
    "tilix",
    "terminator",
    "xfce4-terminal",
    "mate-terminal",
    "lxterminal",
    "org.wezfurlong.wezterm",
}
# How long the pasted text stays in the clipboard before the user's own
# clipboard comes back: the target app reads it asynchronously.
RESTORE_DELAY_SECONDS = 0.3


def paste(text: str) -> None:
    # shortcut: only a text clipboard is restored; an image copied before
    # dictating is lost. Save all targets with xclip -t if that matters.
    previous = _read_clipboard()
    _write_clipboard(text.encode())
    subprocess.run(["xdotool", "key", "--clearmodifiers", _paste_keys()], check=False)
    time.sleep(RESTORE_DELAY_SECONDS)
    if previous is not None:
        _write_clipboard(previous)


def _read_clipboard() -> bytes | None:
    result = subprocess.run(
        ["xclip", "-selection", "clipboard", "-o"], capture_output=True, timeout=2, check=False
    )
    return result.stdout if result.returncode == 0 else None


def _write_clipboard(data: bytes) -> None:
    # xclip forks a background owner that serves the selection; the
    # foreground process exits right after reading stdin.
    subprocess.run(["xclip", "-selection", "clipboard", "-i"], input=data, timeout=2, check=True)


def _paste_keys() -> str:
    window = subprocess.run(
        ["xdotool", "getactivewindow"], capture_output=True, text=True, check=False
    ).stdout.strip()
    if not window:
        return "ctrl+v"
    wm_class = subprocess.run(
        ["xprop", "-id", window, "WM_CLASS"], capture_output=True, text=True, check=False
    ).stdout
    names = {name.lower() for name in re.findall(r'"([^"]*)"', wm_class)}
    return "ctrl+shift+v" if names & TERMINAL_CLASSES else "ctrl+v"
