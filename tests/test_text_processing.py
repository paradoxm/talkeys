from talkeys.text_processing import SpacingFixer


def test_the_first_utterance_of_a_session_has_no_leading_space():
    fixer = SpacingFixer()

    result = fixer.process("hello")

    assert result == "hello"


def test_a_growing_partial_hypothesis_within_one_utterance_keeps_no_leading_space():
    fixer = SpacingFixer()
    fixer.process("hello")

    result = fixer.process("hello world")

    assert result == "hello world"


def test_a_new_utterance_after_a_finalized_one_gets_a_leading_space():
    fixer = SpacingFixer()
    fixer.process("hello world")  # grows, then nerd-dictation finalizes it

    result = fixer.process("hi")  # nerd-dictation reset its own diff state here

    assert result == " hi"


def test_the_leading_space_persists_while_the_new_utterance_keeps_growing():
    fixer = SpacingFixer()
    fixer.process("hello world")
    fixer.process("hi")

    result = fixer.process("hi there")

    assert result == " hi there"


def test_every_utterance_after_the_first_gets_a_leading_space():
    fixer = SpacingFixer()
    fixer.process("hello there")  # first utterance sets a peak length
    fixer.process("hi")  # second utterance, short enough to trip the boundary

    result = fixer.process("hey")  # third utterance

    assert result == " hey"


def test_a_minor_downward_wobble_within_an_utterance_does_not_insert_a_space():
    # VOSK's partial hypothesis can occasionally shrink slightly within a
    # single utterance as the decoder revises it. A bare "shorter than the
    # last call" check would misread this as a new utterance boundary and
    # insert a space mid-word; the shrink-ratio heuristic must not.
    fixer = SpacingFixer()
    fixer.process("recognize speech")

    result = fixer.process("recognize spee")

    assert result == "recognize spee"


def test_a_drop_below_the_shrink_ratio_is_still_treated_as_a_new_utterance():
    fixer = SpacingFixer()
    fixer.process("recognize speech")  # 17 characters

    result = fixer.process("hi")  # far below the default 50% shrink ratio

    assert result == " hi"


def test_empty_text_is_returned_unchanged():
    fixer = SpacingFixer()
    fixer.process("hello world")

    result = fixer.process("")

    assert result == ""


def test_empty_text_does_not_affect_whether_the_next_utterance_gets_a_space():
    fixer = SpacingFixer()
    fixer.process("hello world")
    fixer.process("")

    result = fixer.process("hi")

    assert result == " hi"


def test_empty_text_as_the_very_first_call_has_no_leading_space():
    fixer = SpacingFixer()

    result = fixer.process("")

    assert result == ""


def test_a_more_lenient_shrink_ratio_treats_smaller_drops_as_new_utterances():
    lenient_fixer = SpacingFixer(shrink_ratio=0.9)
    lenient_fixer.process("recognize speech")  # 17 characters

    result = lenient_fixer.process("recognize spee")  # 14 characters, drop to ~82%

    assert result == " recognize spee"
