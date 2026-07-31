import pytest
from fakes import FakeSettingsRegistry

from talkeys.keybindings.base import KeybindingTarget
from talkeys.keybindings.gnome import ENTRY_SCHEMA, PATH_BASE, SCHEMA, GnomeKeybindings

TOGGLE_TARGET = KeybindingTarget(name="Toggle", command="/bin/toggle", binding="<Super>r")
LANG_TARGET = KeybindingTarget(name="Lang", command="/bin/lang", binding="<Primary><Shift>r")


@pytest.fixture
def registry():
    return FakeSettingsRegistry()


@pytest.fixture
def backend(registry):
    return GnomeKeybindings(
        settings_factory=registry.settings_factory,
        entry_settings_factory=registry.entry_settings_factory,
    )


def entry_settings(registry, path):
    return registry.entry_settings_factory(ENTRY_SCHEMA, path)


def top_settings(registry):
    return registry.settings_factory(SCHEMA)


def test_bind_registers_each_target_under_its_own_full_object_path(backend, registry):
    backend.bind([TOGGLE_TARGET, LANG_TARGET])

    toggle_path = f"{PATH_BASE}/custom0/"
    toggle_settings = entry_settings(registry, toggle_path)
    assert toggle_settings.get_string("name") == "Toggle"
    assert toggle_settings.get_string("command") == "/bin/toggle"
    assert toggle_settings.get_string("binding") == "<Super>r"

    lang_settings = entry_settings(registry, f"{PATH_BASE}/custom1/")
    assert lang_settings.get_string("command") == "/bin/lang"


def test_bind_stores_the_new_paths_in_the_top_level_list(backend, registry):
    backend.bind([TOGGLE_TARGET, LANG_TARGET])

    assert top_settings(registry).get_strv("custom-keybindings") == [
        f"{PATH_BASE}/custom0/",
        f"{PATH_BASE}/custom1/",
    ]


def test_bind_does_not_disturb_pre_existing_unrelated_shortcuts(backend, registry):
    unrelated_path = f"{PATH_BASE}/custom0/"
    top_settings(registry).set_strv("custom-keybindings", [unrelated_path])

    backend.bind([TOGGLE_TARGET])

    assert top_settings(registry).get_strv("custom-keybindings") == [
        unrelated_path,
        f"{PATH_BASE}/custom1/",
    ]


def test_bind_reuses_slot_numbers_freed_by_gaps(backend, registry):
    top_settings(registry).set_strv(
        "custom-keybindings", [f"{PATH_BASE}/custom0/", f"{PATH_BASE}/custom3/"]
    )

    backend.bind([TOGGLE_TARGET])

    assert top_settings(registry).get_strv("custom-keybindings") == [
        f"{PATH_BASE}/custom0/",
        f"{PATH_BASE}/custom3/",
        f"{PATH_BASE}/custom1/",
    ]


def test_unbind_matching_removes_only_shortcuts_with_a_matching_command(backend, registry):
    backend.bind([TOGGLE_TARGET, LANG_TARGET])
    unrelated_path = f"{PATH_BASE}/custom9/"
    top_settings(registry).set_strv(
        "custom-keybindings", [unrelated_path] + top_settings(registry).get_strv("custom-keybindings")
    )
    unrelated_settings = entry_settings(registry, unrelated_path)
    unrelated_settings.set_string("command", "/bin/something-else")

    removed_count = backend.unbind_matching({"/bin/toggle", "/bin/lang"})

    assert removed_count == 2
    assert top_settings(registry).get_strv("custom-keybindings") == [unrelated_path]
    assert unrelated_settings.get_string("command") == "/bin/something-else"


def test_unbind_matching_clears_the_name_command_and_binding_of_removed_entries(backend, registry):
    backend.bind([TOGGLE_TARGET])
    toggle_settings = entry_settings(registry, f"{PATH_BASE}/custom0/")

    backend.unbind_matching({"/bin/toggle"})

    assert toggle_settings.get_string("command") == ""
    assert toggle_settings.get_string("binding") == ""


def test_unbind_matching_on_an_empty_list_removes_nothing(backend, registry):
    removed_count = backend.unbind_matching({"/bin/toggle"})

    assert removed_count == 0
    assert top_settings(registry).get_strv("custom-keybindings") == []
