#!/bin/bash
set -euo pipefail

APP_DIR="$HOME/.local/share/nerd-dictation"
CONFIG_DIR="$HOME/.config/nerd-dictation"

echo "==> Stopping any running dictation processes"
pkill -f "$APP_DIR/venv/bin/talkeys-indicator" 2>/dev/null || true

if [ -x "$APP_DIR/venv/bin/talkeys-unbind-hotkeys" ]; then
  echo "==> Removing keybindings pointing at Talkeys"
  "$APP_DIR/venv/bin/talkeys-unbind-hotkeys" || true
fi

echo "==> Removing files"
# Only what Talkeys put there: these folders are plain nerd-dictation's too
# (Talkeys used to run on it), so a user's own models or hook must survive.
rm -rf "$APP_DIR/venv" "$APP_DIR/dictate.log" "$CONFIG_DIR/lang" "$CONFIG_DIR/__pycache__" \
  "$APP_DIR/models/gigaam-v3-e2e-rnnt" "$APP_DIR/models/nemo-parakeet-tdt-0.6b-v3"
# Left behind by Talkeys versions that ran on nerd-dictation + VOSK.
rm -rf "$APP_DIR/nerd-dictation" \
  "$APP_DIR/models/vosk-model-small-en-us-0.15" "$APP_DIR/models/vosk-model-small-ru-0.22"
if grep -qs "talkeys" "$CONFIG_DIR/nerd-dictation.py"; then
  rm -f "$CONFIG_DIR/nerd-dictation.py"
fi
rmdir "$APP_DIR/models" "$APP_DIR" "$CONFIG_DIR" 2>/dev/null || true

echo "Uninstalled."
