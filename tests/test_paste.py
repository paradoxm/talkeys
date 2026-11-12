import subprocess
from unittest.mock import MagicMock

import pytest

from talkeys import paste


class FakeX:
    """Stands in for xclip/xdotool/xprop: a clipboard and a focused window."""

    def __init__(self, clipboard=b"old", wm_class='"gnome-text-editor", "Gnome-text-editor"'):
        self.clipboard = clipboard
        self.wm_class = wm_class
        self.keys: list[str] = []
        self.clipboard_at_paste: bytes | None = None

    def run(self, command, input=None, **_kwargs):
        tool = command[0]
        if tool == "xclip" and "-o" in command:
            if self.clipboard is None:
                return MagicMock(returncode=1, stdout=b"")
            return MagicMock(returncode=0, stdout=self.clipboard)
        if tool == "xclip":
            self.clipboard = input
            return MagicMock(returncode=0)
        if command[:2] == ["xdotool", "getactivewindow"]:
            return MagicMock(returncode=0, stdout="123\n")
        if tool == "xprop":
            return MagicMock(returncode=0, stdout=f"WM_CLASS(STRING) = {self.wm_class}\n")
        if command[:2] == ["xdotool", "key"]:
            self.keys.append(command[-1])
            self.clipboard_at_paste = self.clipboard
            return MagicMock(returncode=0)
        raise AssertionError(f"unexpected command {command}")


@pytest.fixture
def fake_x(monkeypatch):
    fake = FakeX()
    monkeypatch.setattr(subprocess, "run", fake.run)
    monkeypatch.setattr(paste.time, "sleep", MagicMock())
    return fake


def test_pastes_the_text_through_the_clipboard(fake_x):
    paste.paste("Привет, мир.")

    assert fake_x.clipboard_at_paste == "Привет, мир.".encode()
    assert fake_x.keys == ["ctrl+v"]


def test_restores_the_previous_clipboard(fake_x):
    paste.paste("Привет")

    assert fake_x.clipboard == b"old"


def test_an_empty_or_non_text_clipboard_is_left_with_the_pasted_text(fake_x):
    fake_x.clipboard = None

    paste.paste("Привет")

    assert fake_x.clipboard == "Привет".encode()


def test_terminals_get_ctrl_shift_v(fake_x):
    fake_x.wm_class = '"gnome-terminal-server", "Gnome-terminal"'

    paste.paste("ls")

    assert fake_x.keys == ["ctrl+shift+v"]


def test_no_focused_window_falls_back_to_ctrl_v(monkeypatch, fake_x):
    real_run = fake_x.run

    def run(command, **kwargs):
        if command[:2] == ["xdotool", "getactivewindow"]:
            return MagicMock(returncode=1, stdout="")
        return real_run(command, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)

    paste.paste("Привет")

    assert fake_x.keys == ["ctrl+v"]
