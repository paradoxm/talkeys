# CHANGELOG


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
