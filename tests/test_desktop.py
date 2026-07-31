import pytest

from talkeys import desktop


@pytest.mark.parametrize(
    "xdg_current_desktop, expected_desktop",
    [
        ("X-Cinnamon", "cinnamon"),
        ("cinnamon", "cinnamon"),
        ("GNOME", "gnome"),
        ("ubuntu:GNOME", "gnome"),
        ("KDE", None),
        ("", None),
    ],
)
def test_detect_maps_xdg_current_desktop_to_the_matching_desktop(
    monkeypatch, xdg_current_desktop, expected_desktop
):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", xdg_current_desktop)

    assert desktop.detect() == expected_desktop


def test_detect_returns_none_when_the_variable_is_unset(monkeypatch):
    monkeypatch.delenv("XDG_CURRENT_DESKTOP", raising=False)

    assert desktop.detect() is None
