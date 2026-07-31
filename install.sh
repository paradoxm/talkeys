#!/bin/bash
# Voice dictation via nerd-dictation (offline, VOSK) with hotkey toggle,
# language switch, and an on-screen recording indicator.
#
# Everything Talkeys' own code needs lives inside one isolated venv at
# $NERD_DIR/venv: it's created with --system-site-packages only so it can
# see the system's GTK bindings (there's no usable pip wheel for those —
# see pyproject.toml), not so it shares anything else with system Python.
# Talkeys itself is installed as a regular pip package with console-script
# entry points (talkeys-toggle, talkeys-indicator, ...) — nothing is
# copied into place by hand, so `update.sh` is just `pip install --upgrade`.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NERD_DIR="$HOME/.local/share/nerd-dictation"
CONFIG_DIR="$HOME/.config/nerd-dictation"

echo "==> Checking system dependencies"
APT_PACKAGES="git curl unzip python3-venv xdotool pulseaudio-utils libnotify-bin python3-gi gir1.2-gtk-3.0 python3-gi-cairo"
if command -v apt-get >/dev/null; then
  missing=""
  for pkg in $APT_PACKAGES; do
    dpkg -s "$pkg" >/dev/null 2>&1 || missing="$missing $pkg"
  done
  if [ -n "$missing" ]; then
    echo "Installing missing packages:$missing"
    sudo apt-get update
    # shellcheck disable=SC2086
    sudo apt-get install -y $missing
  else
    echo "All required packages already installed, skipping apt."
  fi
else
  echo "This installer only automates apt-based systems (Debian/Ubuntu/Mint)."
  echo "Please install manually: $APT_PACKAGES"
fi

mkdir -p "$NERD_DIR" "$CONFIG_DIR"

echo "==> Fetching nerd-dictation"
if [ ! -d "$NERD_DIR/nerd-dictation" ]; then
  git clone --depth 1 https://github.com/ideasman42/nerd-dictation.git "$NERD_DIR/nerd-dictation"
else
  echo "already present, skipping"
fi

echo "==> Setting up Python venv"
if [ ! -d "$NERD_DIR/venv" ]; then
  /usr/bin/python3 -m venv --system-site-packages "$NERD_DIR/venv"
fi
"$NERD_DIR/venv/bin/pip" install --quiet --upgrade pip
"$NERD_DIR/venv/bin/pip" install --quiet vosk
"$NERD_DIR/venv/bin/pip" install --quiet "$SCRIPT_DIR"

echo "==> Downloading speech models (English + Russian, ~90MB total)"
mkdir -p "$NERD_DIR/models"
cd "$NERD_DIR/models"
if [ ! -d vosk-model-small-en-us-0.15 ]; then
  curl -L -o en.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
  unzip -oq en.zip
  rm en.zip
fi
if [ ! -d vosk-model-small-ru-0.22 ]; then
  curl -L -o ru.zip https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
  unzip -oq ru.zip
  rm ru.zip
fi

echo "==> Installing nerd-dictation's text-processing hook"
# nerd-dictation loads this exact path itself; it can't be a normal part
# of the installed package (see config/nerd-dictation.py for why).
cp "$SCRIPT_DIR/config/nerd-dictation.py" "$CONFIG_DIR/"
[ -f "$CONFIG_DIR/lang" ] || echo ru > "$CONFIG_DIR/lang"

echo
echo "==================================================================="
echo "Done. Two commands need a global hotkey in your desktop environment:"
echo
echo "  Start/stop recording:   $NERD_DIR/venv/bin/talkeys-toggle"
echo "  Switch language ru/en:  $NERD_DIR/venv/bin/talkeys-switch-lang"
echo

if command -v gsettings >/dev/null; then
  read -r -p "Auto-bind Super+R and Ctrl+Shift+R now? [y/N] " reply
  if [[ "$reply" =~ ^[Yy]$ ]]; then
    "$NERD_DIR/venv/bin/talkeys-bind-hotkeys" || true
  fi
else
  echo "Bind them manually in your desktop's Keyboard Shortcuts settings"
  echo "(e.g. Super+R for toggle, Ctrl+Shift+R for language switch)."
fi
