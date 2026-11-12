#!/bin/bash
# Offline voice dictation (GigaAM-v3 / Parakeet via onnx-asr) with hotkey
# toggle, language switch, and an on-screen recording indicator.
#
# Everything Talkeys' own code needs lives inside one isolated venv at
# $APP_DIR/venv: it's created with --system-site-packages only so it can
# see the system's GTK bindings (there's no usable pip wheel for those —
# see pyproject.toml), not so it shares anything else with system Python.
# Talkeys itself is installed as a regular pip package with console-script
# entry points (talkeys-toggle, talkeys-indicator, ...) — nothing is
# copied into place by hand, so `update.sh` is just `pip install --upgrade`.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Folder names are historical (Talkeys used to run on nerd-dictation); kept
# so existing installs and their bound hotkeys keep working.
APP_DIR="$HOME/.local/share/nerd-dictation"
CONFIG_DIR="$HOME/.config/nerd-dictation"

echo "==> Checking system dependencies"
APT_PACKAGES="python3-venv xdotool xclip x11-utils pulseaudio-utils libnotify-bin python3-gi gir1.2-gtk-3.0 python3-gi-cairo"
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

mkdir -p "$APP_DIR" "$CONFIG_DIR"

echo "==> Setting up Python venv"
if [ ! -d "$APP_DIR/venv" ]; then
  /usr/bin/python3 -m venv --system-site-packages "$APP_DIR/venv"
fi
"$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/venv/bin/pip" install --quiet --upgrade "$SCRIPT_DIR"

echo "==> Downloading speech models (Russian + English, ~1.5GB, into $APP_DIR/models)"
"$APP_DIR/venv/bin/python" -c 'from talkeys import stt; [stt.load(lang) for lang in stt.MODEL_BY_LANG]'

[ -f "$CONFIG_DIR/lang" ] || echo ru > "$CONFIG_DIR/lang"

echo
echo "==================================================================="
echo "Done. Two commands need a global hotkey in your desktop environment:"
echo
echo "  Start/stop recording:   $APP_DIR/venv/bin/talkeys-toggle"
echo "  Switch language ru/en:  $APP_DIR/venv/bin/talkeys-switch-lang"
echo

if command -v gsettings >/dev/null; then
  read -r -p "Auto-bind Super+R and Ctrl+Shift+R now? [y/N] " reply
  if [[ "$reply" =~ ^[Yy]$ ]]; then
    "$APP_DIR/venv/bin/talkeys-bind-hotkeys" || true
  fi
else
  echo "Bind them manually in your desktop's Keyboard Shortcuts settings"
  echo "(e.g. Super+R for toggle, Ctrl+Shift+R for language switch)."
fi
