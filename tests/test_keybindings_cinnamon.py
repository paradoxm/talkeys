import pytest
from fakes import FakeSettingsRegistry

from talkeys.keybindings.base import KeybindingTarget
from talkeys.keybindings.cinnamon import ENTRY_SCHEMA, PATH_BASE, SCHEMA, CinnamonKeybindings

TOGGLE_TARGET = KeybindingTarget(name="Toggle", command="/bin/toggle", binding="<Super>r")
LANG_TARGET = KeybindingTarget(name="Lang", command="/bin/lang", binding="<Primary><Shift>r")


@pytest.fixture
def registry():
    return FakeSettingsRegistry()


@pytest.fixture
def backend(registry):
    return CinnamonKeybindings(
        settings_factory=registry.settings_factory,
        entry_settings_factory=registry.entry_settings_factory,
    )


def entry_settings(registry, slot_name):
    return registry.entry_settings_factory(ENTRY_SCHEMA, f"{PATH_BASE}/{slot_name}/")


def top_settings(registry):
    return registry.settings_factory(SCHEMA)


def test_bind_registers_each_target_with_its_own_name_command_and_binding(backend, registry):
    backend.bind([TOGGLE_TARGET, LANG_TARGET])

    toggle_settings = entry_settings(registry, "custom0")
    assert toggle_settings.get_string("name") == "Toggle"
    assert toggle_settings.get_string("command") == "/bin/toggle"
    assert toggle_settings.get_strv("binding") == ["<Super>r"]

    lang_settings = entry_settings(registry, "custom1")
    assert lang_settings.get_string("command") == "/bin/lang"
    assert lang_settings.get_strv("binding") == ["<Primary><Shift>r"]


def test_bind_appends_the_dummy_sentinel_after_the_new_slots(backend, registry):
    backend.bind([TOGGLE_TARGET, LANG_TARGET])

    assert top_settings(registry).get_strv("custom-list") == ["custom0", "custom1", "__dummy__"]


def test_bind_does_not_disturb_pre_existing_unrelated_shortcuts(backend, registry):
    top_settings(registry).set_strv("custom-list", ["custom0", "__dummy__"])

    backend.bind([TOGGLE_TARGET, LANG_TARGET])

    assert top_settings(registry).get_strv("custom-list") == [
        "custom0",
        "custom1",
        "custom2",
        "__dummy__",
    ]


def test_bind_reuses_slot_numbers_freed_by_gaps(backend, registry):
    top_settings(registry).set_strv("custom-list", ["custom0", "custom3", "__dummy__"])

    backend.bind([TOGGLE_TARGET])

    assert top_settings(registry).get_strv("custom-list") == [
        "custom0",
        "custom3",
        "custom1",
        "__dummy__",
    ]


def test_unbind_matching_removes_only_shortcuts_with_a_matching_command(backend, registry):
    backend.bind([TOGGLE_TARGET, LANG_TARGET])
    top_settings(registry).set_strv(
        "custom-list", ["customUNRELATED"] + top_settings(registry).get_strv("custom-list")
    )
    unrelated_settings = entry_settings(registry, "customUNRELATED")
    unrelated_settings.set_string("command", "/bin/something-else")

    removed_count = backend.unbind_matching({"/bin/toggle", "/bin/lang"})

    assert removed_count == 2
    assert top_settings(registry).get_strv("custom-list") == ["customUNRELATED", "__dummy__"]
    assert unrelated_settings.get_string("command") == "/bin/something-else"


def test_unbind_matching_clears_the_name_command_and_binding_of_removed_entries(backend, registry):
    backend.bind([TOGGLE_TARGET])
    toggle_settings = entry_settings(registry, "custom0")

    backend.unbind_matching({"/bin/toggle"})

    assert toggle_settings.get_string("command") == ""
    assert toggle_settings.get_strv("binding") == []


def test_unbind_matching_preserves_the_dummy_sentinel_when_it_was_already_present(backend, registry):
    top_settings(registry).set_strv("custom-list", ["custom0", "__dummy__"])
    entry_settings(registry, "custom0").set_string("command", "/bin/toggle")

    backend.unbind_matching({"/bin/toggle"})

    assert top_settings(registry).get_strv("custom-list") == ["__dummy__"]


def test_unbind_matching_does_not_invent_a_dummy_sentinel_that_was_never_there(backend, registry):
    # A system with zero pre-existing custom shortcuts has no "__dummy__"
    # entry until Cinnamon's own settings UI creates one; uninstalling
    # Talkeys must not leave one behind that wasn't there before.
    top_settings(registry).set_strv("custom-list", ["custom0"])
    entry_settings(registry, "custom0").set_string("command", "/bin/toggle")

    backend.unbind_matching({"/bin/toggle"})

    assert top_settings(registry).get_strv("custom-list") == []
