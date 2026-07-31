from talkeys.keybindings.slots import find_free_slot_numbers


def test_returns_the_lowest_numbers_when_none_are_used():
    free_slots = find_free_slot_numbers(3, used_numbers=set())

    assert free_slots == [0, 1, 2]


def test_skips_numbers_that_are_already_used():
    free_slots = find_free_slot_numbers(2, used_numbers={0, 1})

    assert free_slots == [2, 3]


def test_fills_in_gaps_left_by_scattered_used_numbers():
    free_slots = find_free_slot_numbers(2, used_numbers={0, 2, 4})

    assert free_slots == [1, 3]


def test_requesting_zero_slots_returns_an_empty_list():
    free_slots = find_free_slot_numbers(0, used_numbers={0, 1, 2})

    assert free_slots == []


def test_used_numbers_far_above_any_needed_slot_are_irrelevant():
    free_slots = find_free_slot_numbers(1, used_numbers={5, 6, 7})

    assert free_slots == [0]
