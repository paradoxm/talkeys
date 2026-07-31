from talkeys import keybindings


class DummyBackend:
    """A stand-in backend class: verifies get_backend()'s dispatch logic
    without constructing a real Cinnamon/GNOME backend, which would try to
    open a real GSettings schema that may not be installed on a machine
    that isn't actually running that desktop (e.g. a CI runner)."""


def test_get_backend_picks_the_cinnamon_backend_on_cinnamon(monkeypatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "X-Cinnamon")
    monkeypatch.setitem(keybindings._BACKENDS_BY_DESKTOP, "cinnamon", DummyBackend)

    backend = keybindings.get_backend()

    assert isinstance(backend, DummyBackend)


def test_get_backend_picks_the_gnome_backend_on_gnome(monkeypatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "ubuntu:GNOME")
    monkeypatch.setitem(keybindings._BACKENDS_BY_DESKTOP, "gnome", DummyBackend)

    backend = keybindings.get_backend()

    assert isinstance(backend, DummyBackend)


def test_get_backend_returns_none_on_an_unsupported_desktop(monkeypatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")

    backend = keybindings.get_backend()

    assert backend is None
