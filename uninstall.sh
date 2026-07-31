#!/bin/bash
set -euo pipefail

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
rm -rf "$NERD_DIR" "$CONFIG_DIR"

echo "Uninstalled."
