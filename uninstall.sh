#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NERD_DIR="$HOME/.local/share/nerd-dictation"
CONFIG_DIR="$HOME/.config/nerd-dictation"

echo "==> Stopping any running dictation processes"
pkill -f "$NERD_DIR/venv/bin/talkeys-indicator" 2>/dev/null || true
pkill -f "$NERD_DIR/nerd-dictation/nerd-dictation begin" 2>/dev/null || true

if [ -x "$NERD_DIR/venv/bin/talkeys-unbind-hotkeys" ]; then
  echo "==> Removing keybindings pointing at Talkeys"
  "$NERD_DIR/venv/bin/talkeys-unbind-hotkeys" || true
fi

echo "==> Removing files"
# Only what install.sh puts there: these folders are plain nerd-dictation's
# too, so a user's own models or hook must survive.
rm -rf "$NERD_DIR/venv" "$NERD_DIR/nerd-dictation" "$NERD_DIR/dictate.log" \
  "$NERD_DIR/models/vosk-model-small-en-us-0.15" "$NERD_DIR/models/vosk-model-small-ru-0.22" \
  "$CONFIG_DIR/lang" "$CONFIG_DIR/__pycache__"
if cmp -s "$SCRIPT_DIR/config/nerd-dictation.py" "$CONFIG_DIR/nerd-dictation.py"; then
  rm -f "$CONFIG_DIR/nerd-dictation.py"
fi
rmdir "$NERD_DIR/models" "$NERD_DIR" "$CONFIG_DIR" 2>/dev/null || true

echo "Uninstalled."
