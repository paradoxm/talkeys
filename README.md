# Talkeys

Offline push-to-talk voice dictation for Linux: press a hotkey, speak, press it
again — the recognized text is typed wherever your cursor is (a terminal,
Claude Code, a text field, anywhere). Runs fully offline via
[nerd-dictation](https://github.com/ideasman42/nerd-dictation) + [VOSK](https://alphacephei.com/vosk/).

Includes:

- A toggle hotkey to start/stop recording.
- A hotkey to switch between English and Russian.
- A borderless, click-through animated overlay shown while recording (no
  sound, no notifications — just the overlay).
- Auto-stop after ~10s of real silence, detected independently via
  microphone RMS level, calibrated against the room's own ambient noise.

## Requirements

- Linux with X11 (uses `xdotool` to type text — Wayland needs a different
  `--simulate-input-tool`, see nerd-dictation's readme).
- Cinnamon (Linux Mint) or GNOME (stock Ubuntu) for automatic hotkey
  binding. Other desktop environments: bind the two commands manually.
- apt-based distro for the automated installer (Debian/Ubuntu/Mint). Other
  distros: install the dependencies listed in `install.sh` manually, then run
  the rest of the script.

## Install

```sh
./install.sh
```

This installs system packages (`xdotool`, `parec`, GTK3 introspection for the
overlay, etc.), clones `nerd-dictation`, creates a venv at
`~/.local/share/nerd-dictation/venv`, installs Talkeys and `vosk` into it, and
downloads the small English and Russian VOSK models (~90MB total).

The venv is created with `--system-site-packages` so it can see the system's
GTK bindings (there's no usable pip wheel for those — see `pyproject.toml`),
not so it shares anything else with system Python. Everything Talkeys' own
code needs is otherwise isolated inside it.

On Cinnamon and GNOME it offers to bind the hotkeys automatically. On other
desktop environments, bind these two commands yourself in your Keyboard
Shortcuts settings:

| Action | Command | Suggested key |
| --- | --- | --- |
| Start/stop recording | `~/.local/share/nerd-dictation/venv/bin/talkeys-toggle` | `Super+R` |
| Switch language ru/en | `~/.local/share/nerd-dictation/venv/bin/talkeys-switch-lang` | `Ctrl+Shift+R` |

## Usage

1. Press the toggle hotkey. An animated wave at the bottom of the screen
   confirms recording started.
2. Speak.
3. Press the toggle hotkey again, or just stop talking — recording auto-stops
   after ~10s of silence. There can be a short delay (a few seconds) before
   the final text is typed — this is `nerd-dictation` finishing its internal
   buffer, not a bug.

## Known limitations

- Under heavy CPU load (many background apps competing for cores),
  `nerd-dictation` can fall behind real-time: audio keeps buffering but
  isn't transcribed promptly, so text can appear in a delayed burst instead
  of live. This isn't a bug in these scripts — it clears up once CPU
  pressure drops. Closing heavy background tools (IDEs with language
  servers, dev servers, etc.) helps.
- The VOSK "small" models are fast and lightweight but don't add punctuation
  and are noticeably less accurate than a full-size model or Whisper. Bigger
  VOSK models improve accuracy but not punctuation, and use ~1.8GB more RAM.
- Switching to Whisper would give much better accuracy and real punctuation,
  at the cost of losing live "type as you speak" (Whisper transcribes after
  you stop, not incrementally). Not implemented here.

## Update

```sh
./update.sh
```

Pulls the latest `nerd-dictation` and upgrades the installed Talkeys package
in place. Models, config, and bound hotkeys are untouched.

## Uninstall

```sh
./uninstall.sh
```

Stops any running dictation process, removes the installed files, and (on
Cinnamon or GNOME) removes the two keybindings it bound during install.

## Development

```sh
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest       # tests + coverage (fails under 98%)
.venv/bin/python -m ruff check src/ tests/
.venv/bin/python -m mypy src/talkeys tests/
```

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
(`feat:`, `fix:`, `docs:`, `refactor:`, ...) — CI parses them on every push to
`main` to decide whether to bump the version in `pyproject.toml` and publish
a release.

## Built with

- [nerd-dictation](https://github.com/ideasman42/nerd-dictation) — the
  offline dictation engine that ties audio capture, VOSK, and text output
  together. This project is a hotkey/overlay/reliability layer on top of it.
- [VOSK](https://alphacephei.com/vosk/) — the offline speech recognition
  models and toolkit.
- [xdotool](https://github.com/jordansissel/xdotool) — types the recognized
  text into the focused window via X11.
- [PulseAudio](https://www.freedesktop.org/wiki/Software/PulseAudio/) /
  [PipeWire](https://pipewire.org/) — `parec` records the microphone, both
  for `nerd-dictation` and for the silence watchdog.
- [GTK3](https://www.gtk.org/) via [PyGObject](https://pygobject.readthedocs.io/)
  — renders the animated recording overlay.
