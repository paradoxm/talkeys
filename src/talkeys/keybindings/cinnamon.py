"""Cinnamon (Linux Mint's desktop) custom-keybinding backend, via GSettings.

Cinnamon keeps a `custom-list` of bare slot names (e.g. "custom0"), plus a
"__dummy__" sentinel Cinnamon's own settings UI manages — if it was already
there, this leaves it exactly as found; it never adds or removes it itself.
"""
import re

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio

from .base import KeybindingBackend, KeybindingTarget
from .slots import find_free_slot_numbers

SCHEMA = "org.cinnamon.desktop.keybindings"
ENTRY_SCHEMA = f"{SCHEMA}.custom-keybinding"
PATH_BASE = "/org/cinnamon/desktop/keybindings/custom-keybindings"
DUMMY_ENTRY = "__dummy__"
_SLOT_NAME_PATTERN = re.compile(r"^custom(\d+)$")


class CinnamonKeybindings(KeybindingBackend):
    def __init__(
        self,
        settings_factory=Gio.Settings.new,
        entry_settings_factory=Gio.Settings.new_with_path,
    ):
        self._settings = settings_factory(SCHEMA)
        self._entry_settings_factory = entry_settings_factory

    def _entry_settings(self, slot_name: str):
        return self._entry_settings_factory(ENTRY_SCHEMA, f"{PATH_BASE}/{slot_name}/")

    def bind(self, targets: list[KeybindingTarget]) -> None:
        entries = [entry for entry in self._settings.get_strv("custom-list") if entry != DUMMY_ENTRY]

        used_numbers = {
            int(match.group(1)) for entry in entries if (match := _SLOT_NAME_PATTERN.match(entry))
        }
        slot_names = [f"custom{n}" for n in find_free_slot_numbers(len(targets), used_numbers)]

        for slot_name, target in zip(slot_names, targets):
            entry_settings = self._entry_settings(slot_name)
            entry_settings.set_string("name", target.name)
            entry_settings.set_string("command", target.command)
            entry_settings.set_strv("binding", [target.binding])
            entries.append(slot_name)

        entries.append(DUMMY_ENTRY)
        self._settings.set_strv("custom-list", entries)

    def unbind_matching(self, commands: set[str]) -> int:
        entries = list(self._settings.get_strv("custom-list"))
        kept_entries = []
        removed_count = 0

        for entry in entries:
            if entry == DUMMY_ENTRY:
                kept_entries.append(entry)
                continue
            entry_settings = self._entry_settings(entry)
            if entry_settings.get_string("command") in commands:
                entry_settings.reset("name")
                entry_settings.reset("command")
                entry_settings.reset("binding")
                removed_count += 1
            else:
                kept_entries.append(entry)

        self._settings.set_strv("custom-list", kept_entries)
        return removed_count
