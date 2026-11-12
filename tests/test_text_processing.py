from talkeys.text_processing import join


def test_the_first_phrase_is_inserted_as_is():
    assert join("", "Привет, мир.") == "Привет, мир."


def test_a_phrase_after_a_finished_sentence_keeps_its_capital_and_gets_a_space():
    assert join("Привет.", "Как дела?") == " Как дела?"


def test_a_phrase_continuing_a_sentence_is_lowercased():
    assert join("наверное, надеюсь", "Решить, какую модель.") == " решить, какую модель."


def test_abbreviations_in_capitals_are_left_alone():
    assert join("используем", "API для записи") == " API для записи"


def test_question_and_exclamation_marks_end_a_sentence_too():
    assert join("Правда?", "Да") == " Да"
    assert join("Ура!", "Работает") == " Работает"


def test_empty_or_blank_text_inserts_nothing():
    assert join("Привет.", "") == ""
    assert join("Привет.", "   ") == ""


def test_surrounding_whitespace_is_trimmed():
    assert join("Привет.", "  Как дела?  ") == " Как дела?"
