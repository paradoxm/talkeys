#!/bin/bash
# Updates Talkeys itself and nerd-dictation in place, without touching
# downloaded models, config, or bound hotkeys.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NERD_DIR="$HOME/.local/share/nerd-dictation"

echo "==> Updating nerd-dictation"
git -C "$NERD_DIR/nerd-dictation" pull --ff-only

echo "==> Updating Talkeys"
"$NERD_DIR/venv/bin/pip" install --quiet --upgrade "$SCRIPT_DIR"

echo "Done."
