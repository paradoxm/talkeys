# CHANGELOG


## v0.2.0 (2026-11-12)

### Features

- Replace nerd-dictation + VOSK with GigaAM-v3 via onnx-asr
  ([#2](https://github.com/paradoxm/talkeys/pull/2),
  [`7e93468`](https://github.com/paradoxm/talkeys/commit/7e9346815ada2ca0686298769fc52e60397152e1))

- recognize Russian with GigaAM-v3 e2e (punctuation and capitals built in) and English with Parakeet
  TDT v3 int8, through onnx-asr on the CPU - show a live draft of the phrase in the overlay; paste
  each finished phrase once through the clipboard after a ~0.8s pause instead of retyping character
  by character with xdotool - recognize each phrase together with the last 3s of the previous one
  and keep only the new words, so pauses mid-sentence keep the grammar - end a session after 2
  minutes even if it never goes quiet - silence detection: ignore parec's initial digital zeros,
  lower the absolute floor so quiet microphones are not read as silence - run recognition at nice 10
  on half the cores - download models into the app folder; drop nerd-dictation, VOSK and the
  nerd-dictation hook; uninstall removes leftovers of older versions - rewrite the README for the
  new engine


## v0.1.1 (2026-11-12)

### Bug Fixes

- Harden silence auto-stop, phrase spacing, hotkeys and install scripts
  ([#1](https://github.com/paradoxm/talkeys/pull/1),
  [`41a4ab5`](https://github.com/paradoxm/talkeys/commit/41a4ab575b3c79de1846f90c03dc6faff6ca4ec9))

- watchdog: learn the room's noise from the quietest 0.1s window instead of a fixed first second, so
  speech that starts at the hotkey press no longer triggers auto-stop mid-sentence; use a monotonic
  clock - text_processing: a changed first word also marks a new utterance, so a short phrase
  followed by a longer one gets its separating space; drop the unused shrink_ratio option -
  bind_hotkeys: remove our own earlier bindings before binding again - paths: keep the recording
  marker and toggle lock in XDG_RUNTIME_DIR - install.sh keeps a different existing nerd-dictation
  hook as a backup; uninstall.sh removes only what install.sh created - keybindings: share __init__
  and unbind_matching in the base class - ci: release runs only after tests pass on main


## v0.1.0 (2026-07-31)

### Bug Fixes

- Resolve ruff/mypy/semantic-release CI failures
  ([`bef4421`](https://github.com/paradoxm/talkeys/commit/bef442174759bc9c66b6d0cdfccca096213477e6))

- Fix genuine ruff findings (import sorting, explicit subprocess.run check=, context managers for
  file handles) instead of pinning an older ruff to dodge them. - semantic_release.build_command
  must be a string; "" disables the build step, a bare `false` doesn't validate.

### Features

- Offline push-to-talk voice dictation via nerd-dictation + VOSK
  ([`f537ad8`](https://github.com/paradoxm/talkeys/commit/f537ad8b12d35f59aecd46c7156bbe2b50712030))

Hotkey toggle (Cinnamon/GNOME auto-bind), ru/en switch, an animated recording overlay, and an
  RMS-based silence watchdog calibrated to ambient noise for auto-stop (nerd-dictation's own
  --timeout is unreliable for this). Packaged as an installable Python package with 100% test
  coverage, ruff/mypy in CI, and semantic-release versioning.
