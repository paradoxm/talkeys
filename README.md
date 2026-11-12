# Talkeys

Offline voice dictation for Linux. Press a hotkey and speak: a draft of what
you're saying shows on screen as you talk, and each finished phrase — with
punctuation and capital letters — is pasted wherever your cursor is (a text
editor, a terminal, Claude Code, a browser field). Everything runs locally
on the CPU; no audio leaves the machine.

- **Russian:** [GigaAM-v3](https://github.com/salute-developers/GigaAM)
  (`gigaam-v3-e2e-rnnt`, SberDevices) — punctuation and capitalization are
  built into the model.
- **English:** [Parakeet TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3)
  (NVIDIA, int8 build).
- Both run through [onnx-asr](https://github.com/istupakov/onnx-asr) on
  onnxruntime. No GPU needed.

## How it works

```
Super+R ─► talkeys-toggle ─► talkeys-indicator process (one per session)
                              │
   parec (microphone, 16 kHz) ┤ watchdog.py: 0.2 s chunks, speech/silence by
                              │   loudness against the room's own noise
                              ▼
                             dictation.py: collects a phrase until a ~0.8 s pause
                              │   ├─ while you talk: re-recognizes the phrase
                              │   │  ~once a second → draft in the overlay
                              │   └─ on the pause: recognizes it once more,
                              │      with the last 3 s of the previous phrase
                              │      as context, keeps only the new words
                              ▼
                             paste.py: puts the phrase on the clipboard,
                                presses Ctrl+V (Ctrl+Shift+V in terminals),
                                restores your clipboard
```

- **Phrases, not single words.** The models recognize whole phrases, so text
  lands in the window phrase by phrase, about a second after you pause
  (longer for a long phrase). The overlay shows the draft in the meantime.
  Nothing already pasted is ever retyped.
- **Context across pauses.** A pause in the middle of a sentence used to
  break its grammar ("новым скажи движком"). The tail of the previous phrase
  is now recognized together with the next one (`stt.text_after` cuts it
  off by token timestamps), which fixes endings and word choice at the cut.
- **One paste per phrase.** Typing character by character with `xdotool`
  floods the input method (ibus) with key events and could freeze the X
  session; a clipboard paste is a single keystroke.
- **The desktop stays responsive.** Recognition runs at `nice 10` on half of
  the CPU cores.
- **Auto-stop.** The session ends after ~10s of real silence, or after 2
  minutes in any case (a session forgotten next to a TV would otherwise
  paste its speech for hours). Whatever was said last is still pasted. Need
  more? Press the hotkey again.

## Requirements

- Linux with X11 (`xclip`, `xdotool`, `xprop`). Wayland is not supported.
- PulseAudio or PipeWire (`parec`).
- ~1.5GB of disk for the models, ~1.5GB of RAM while recording.
- Cinnamon (Linux Mint) or GNOME (stock Ubuntu) for automatic hotkey
  binding. Other desktops: bind the two commands manually (see below).
- apt-based distro for the automated installer (Debian/Ubuntu/Mint). Other
  distros: install the packages listed in `install.sh` manually, then run
  the rest of the script.

## Install

```sh
./install.sh
```

This installs the system packages (`xdotool`, `xclip`, `x11-utils`,
`pulseaudio-utils`, GTK3 introspection for the overlay), creates a venv at
`~/.local/share/nerd-dictation/venv`, installs Talkeys into it, and downloads
the models into `~/.local/share/nerd-dictation/models`. The folder names are
historical — Talkeys used to run on nerd-dictation + VOSK — and kept so
existing installs and their hotkeys keep working.

The venv is created with `--system-site-packages` so it can see the system's
GTK bindings (there's no usable pip wheel for those — see `pyproject.toml`).
Everything else Talkeys needs is installed inside it.

On Cinnamon and GNOME the installer offers to bind the hotkeys. Elsewhere,
bind these in your Keyboard Shortcuts settings:

| Action | Command | Suggested key |
| --- | --- | --- |
| Start/stop recording | `~/.local/share/nerd-dictation/venv/bin/talkeys-toggle` | `Super+R` |
| Switch language ru/en | `~/.local/share/nerd-dictation/venv/bin/talkeys-switch-lang` | `Ctrl+Shift+R` |

## Usage

1. Press `Super+R`. A small animated wave appears at the bottom of the
   screen.
2. Speak. The draft of the current phrase shows in a strip above the wave.
3. Pause for a moment — the finished phrase is pasted into the focused
   window.
4. Press `Super+R` again, or just stop talking (10s of silence ends the
   session).

`Ctrl+Shift+R` switches the language for the next session (a notification
shows the new one).

**Accuracy tip:** keep the microphone input volume high (80–100% in the
sound settings). The models make noticeably more mistakes in word endings
on a quiet signal.

## Known limitations

- Your clipboard is restored after each paste only if it held text; an
  image copied before dictating is lost.
- When the model decides a sentence ended at a pause, that phrase is pasted
  with a period; if you then continue the same sentence, the next phrase
  starts lowercase after it ("знаки. препинания"). Already pasted text is
  never edited.
- A phrase that opens mid-sentence with a proper noun gets lowercased
  ("в" + "Москве" → "в москве").
- Filler sounds are transcribed as heard ("а-а", "ну").
- Terminals are detected by window class (`paste.TERMINAL_CLASSES`) to use
  Ctrl+Shift+V; a terminal not on that list gets Ctrl+V.

## Troubleshooting

Errors from the recording process (e.g. a model that failed to load) go to
`~/.local/share/nerd-dictation/dictate.log`.

## Update

```sh
./update.sh
```

Upgrades the installed Talkeys package in place. Models, config, and bound
hotkeys are untouched.

## Uninstall

```sh
./uninstall.sh
```

Stops any running session, removes the venv, the models, the log and the
language setting, and (on Cinnamon or GNOME) the two hotkeys. Files left by
older nerd-dictation-based versions of Talkeys are removed too.

## Project layout

| Module | Job |
| --- | --- |
| `recorder.py` | Start/stop a session from the hotkey, guarded by a lock |
| `indicator.py` | The overlay window; owns the session's watchdog and dictation |
| `watchdog.py` | Microphone capture, speech/silence per chunk, auto-stop |
| `dictation.py` | Phrases, live draft, context, paste order |
| `stt.py` | Model loading and recognition (`onnx-asr`) |
| `text_processing.py` | Joining phrases into running text |
| `paste.py` | Clipboard paste into the focused window |
| `audio.py` | Loudness (RMS) of a chunk of audio |
| `paths.py` | File locations, the language setting, the session marker |
| `desktop.py` | Detects Cinnamon or GNOME |
| `keybindings/` | Cinnamon/GNOME hotkey binding |
| `cli/` | The `talkeys-*` commands (entry points) |

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

- [onnx-asr](https://github.com/istupakov/onnx-asr) and
  [onnxruntime](https://onnxruntime.ai/) — run the speech models.
- [GigaAM-v3](https://github.com/salute-developers/GigaAM) (Russian) and
  [Parakeet TDT v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3)
  (English) — the speech models.
- [xclip](https://github.com/astrand/xclip) and
  [xdotool](https://github.com/jordansissel/xdotool) — paste into the
  focused window via X11.
- [PulseAudio](https://www.freedesktop.org/wiki/Software/PulseAudio/) /
  [PipeWire](https://pipewire.org/) — `parec` records the microphone.
- [GTK3](https://www.gtk.org/) via [PyGObject](https://pygobject.readthedocs.io/)
  — renders the overlay.
