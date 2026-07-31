from .. import keybindings, paths

COMMANDS = {str(paths.TOGGLE_BIN), str(paths.SWITCH_LANG_BIN)}


def main() -> int:
    backend = keybindings.get_backend()
    if backend is None:
        print("No automatic binder for this desktop environment.")
        print("Remove the hotkeys yourself if you bound them manually.")
        return 1

    removed_count = backend.unbind_matching(COMMANDS)
    print(f"Removed {removed_count} keybinding(s).")
    return 0
