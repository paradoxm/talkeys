"""Test doubles standing in for Gio.Settings in the keybinding backend
tests. Real GSettings/dconf touches live desktop state, which is exactly
what these tests must not do."""


class FakeSettings:
    """Stands in for one Gio.Settings instance. Stores whatever's written
    regardless of whether it came through the strv or string API, since
    each real schema key only ever uses one of the two."""

    def __init__(self):
        self._values = {}

    def get_strv(self, key):
        return list(self._values.get(key, []))

    def set_strv(self, key, value):
        self._values[key] = list(value)

    def get_string(self, key):
        return self._values.get(key, "")

    def set_string(self, key, value):
        self._values[key] = value

    def reset(self, key):
        self._values.pop(key, None)


class FakeSettingsRegistry:
    """Stands in for Gio.Settings.new / Gio.Settings.new_with_path: returns
    the same FakeSettings for a given schema (+ path), so a write made
    through one call is visible to a later call against the same
    schema/path — exactly like real dconf."""

    def __init__(self):
        self._by_key = {}

    def settings_factory(self, schema):
        return self._by_key.setdefault(("top", schema), FakeSettings())

    def entry_settings_factory(self, schema, path):
        return self._by_key.setdefault(("entry", schema, path), FakeSettings())
