from .. import desktop
from .base import KeybindingBackend, KeybindingTarget
from .cinnamon import CinnamonKeybindings
from .gnome import GnomeKeybindings

__all__ = ["KeybindingBackend", "KeybindingTarget", "get_backend"]

_BACKENDS_BY_DESKTOP = {
    desktop.CINNAMON: CinnamonKeybindings,
    desktop.GNOME: GnomeKeybindings,
}


def get_backend() -> KeybindingBackend | None:
    """Returns the keybinding backend for the current desktop, or None if
    it isn't one this project knows how to auto-bind on."""
    detected_desktop = desktop.detect()
    if detected_desktop is None:
        return None
    backend_class = _BACKENDS_BY_DESKTOP.get(detected_desktop)
    return backend_class() if backend_class else None
