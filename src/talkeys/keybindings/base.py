"""Interface every desktop-specific keybinding backend implements, so
callers (the bind/unbind CLIs) don't need to know which desktop they're
running on beyond picking the right backend once."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


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

    @abstractmethod
    def bind(self, targets: list[KeybindingTarget]) -> None:
        """Registers each target under a freshly allocated slot."""

    @abstractmethod
    def unbind_matching(self, commands: set[str]) -> int:
        """Removes any existing custom shortcut whose command is in
        `commands`, leaving every other shortcut untouched. Returns how
        many were removed."""
