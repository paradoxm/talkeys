from .. import keybindings, paths

TARGETS = [
    keybindings.KeybindingTarget(
        name="Voice dictation toggle",
        command=str(paths.TOGGLE_BIN),
        binding="<Super>r",
    ),
    keybindings.KeybindingTarget(
        name="Voice dictation switch language",
        command=str(paths.SWITCH_LANG_BIN),
        binding="<Primary><Shift>r",
    ),
]


def main() -> int:
    backend = keybindings.get_backend()
    if backend is None:
        print("No automatic binder for this desktop environment.")
        print("Bind these manually in your desktop's Keyboard Shortcuts settings:")
        print(f"  Super+R       -> {paths.TOGGLE_BIN}")
        print(f"  Ctrl+Shift+R  -> {paths.SWITCH_LANG_BIN}")
        return 1

    backend.bind(TARGETS)
    print("Bound Super+R (toggle) and Ctrl+Shift+R (switch language).")
    return 0
