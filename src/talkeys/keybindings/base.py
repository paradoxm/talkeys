"""Interface every desktop-specific keybinding backend implements, so
callers (the bind/unbind CLIs) don't need to know which desktop they're
running on beyond picking the right backend once."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio


@dataclass(frozen=True)
class KeybindingTarget:
    """One hotkey to register: a human-readable name, the command it runs,
    and the key combination in the desktop's own binding syntax (e.g.
    "<Super>r")."""

    name: str
    command: str
    binding: str


class KeybindingBackend(ABC):
    """Binds/unbinds custom keyboard shortcuts on one desktop environment,
    without disturbing any pre-existing custom shortcuts that aren't ours."""

    SCHEMA: str
    LIST_KEY: str  # the GSettings key holding the list of custom shortcuts

    def __init__(
        self,
        settings_factory=Gio.Settings.new,
        entry_settings_factory=Gio.Settings.new_with_path,
    ):
        self._settings = settings_factory(self.SCHEMA)
        self._entry_settings_factory = entry_settings_factory

    @abstractmethod
    def _entry_settings(self, entry: str):
        """The settings object for one entry of the `LIST_KEY` list."""

    @abstractmethod
    def bind(self, targets: list[KeybindingTarget]) -> None:
        """Registers each target under a freshly allocated slot."""

    def unbind_matching(self, commands: set[str]) -> int:
        """Removes any existing custom shortcut whose command is in
        `commands`, leaving every other shortcut untouched. Returns how
        many were removed."""
        entries = self._settings.get_strv(self.LIST_KEY)
        kept_entries = []
        for entry in entries:
            entry_settings = self._entry_settings(entry)
            if entry_settings.get_string("command") in commands:
                for key in ("name", "command", "binding"):
                    entry_settings.reset(key)
            else:
                kept_entries.append(entry)

        self._settings.set_strv(self.LIST_KEY, kept_entries)
        return len(entries) - len(kept_entries)
