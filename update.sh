#!/bin/bash
# Updates Talkeys in place, without touching downloaded models, config, or
# bound hotkeys.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/.local/share/nerd-dictation"

echo "==> Updating Talkeys"
"$APP_DIR/venv/bin/pip" install --quiet --upgrade "$SCRIPT_DIR"

echo "Done."
