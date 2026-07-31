"""Detects which desktop environment is running, to pick a keybinding
backend. `XDG_CURRENT_DESKTOP` can hold compound values (Ubuntu's GNOME
session reports "ubuntu:GNOME"), so this checks substrings, not equality.
"""
import os

CINNAMON = "cinnamon"
GNOME = "gnome"


def detect() -> str | None:
    current_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if CINNAMON in current_desktop:
        return CINNAMON
    if GNOME in current_desktop:
        return GNOME
    return None
