"""GNOME (stock Ubuntu desktop) custom-keybinding backend, via GSettings.

Unlike Cinnamon, GNOME's `custom-keybindings` list holds full object paths
(e.g. "/org/gnome/.../custom0/") rather than bare names, has no "__dummy__"
sentinel, and each entry's `binding` is a plain string, not an array.
"""
import re

from .base import KeybindingBackend, KeybindingTarget
from .slots import find_free_slot_numbers

SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"
ENTRY_SCHEMA = f"{SCHEMA}.custom-keybinding"
PATH_BASE = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"
_SLOT_PATH_PATTERN = re.compile(r"custom(\d+)/?$")


class GnomeKeybindings(KeybindingBackend):
    SCHEMA = SCHEMA
    LIST_KEY = "custom-keybindings"

    def _entry_settings(self, path: str):
        return self._entry_settings_factory(ENTRY_SCHEMA, path)

    def bind(self, targets: list[KeybindingTarget]) -> None:
        entries = list(self._settings.get_strv("custom-keybindings"))

        used_numbers = {
            int(match.group(1)) for entry in entries if (match := _SLOT_PATH_PATTERN.search(entry))
        }
        slot_paths = [
            f"{PATH_BASE}/custom{n}/" for n in find_free_slot_numbers(len(targets), used_numbers)
        ]

        for path, target in zip(slot_paths, targets):
            entry_settings = self._entry_settings(path)
            entry_settings.set_string("name", target.name)
            entry_settings.set_string("command", target.command)
            entry_settings.set_string("binding", target.binding)
            entries.append(path)

        self._settings.set_strv("custom-keybindings", entries)
