import pytest

from talkeys import paths


@pytest.fixture(autouse=True)
def isolated_lang_file(tmp_path, monkeypatch):
    lang_file = tmp_path / "lang"
    monkeypatch.setattr(paths, "LANG_FILE", lang_file)
    monkeypatch.setattr(paths, "CONFIG_DIR", tmp_path / "config")
    return lang_file


def test_get_lang_defaults_to_ru_when_no_lang_file_exists():
    assert paths.get_lang() == "ru"


def test_set_lang_then_get_lang_round_trips(isolated_lang_file):
    paths.set_lang("en")

    assert paths.get_lang() == "en"


def test_get_lang_falls_back_to_the_default_for_unrecognized_content(isolated_lang_file):
    isolated_lang_file.write_text("french\n")

    assert paths.get_lang() == "ru"


def test_get_lang_ignores_surrounding_whitespace(isolated_lang_file):
    isolated_lang_file.write_text("  en  \n")

    assert paths.get_lang() == "en"


def test_set_lang_creates_the_config_directory_if_missing(isolated_lang_file):
    assert not paths.CONFIG_DIR.exists()

    paths.set_lang("en")

    assert paths.CONFIG_DIR.exists()


def test_model_dir_for_current_lang_matches_the_stored_language(isolated_lang_file):
    paths.set_lang("en")

    assert paths.model_dir_for_current_lang() == paths.MODEL_DIR_BY_LANG["en"]


def test_model_dir_for_current_lang_defaults_to_russian_model():
    assert paths.model_dir_for_current_lang() == paths.MODEL_DIR_BY_LANG["ru"]
