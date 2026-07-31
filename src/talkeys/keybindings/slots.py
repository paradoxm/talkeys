"""Pure helper shared by the Cinnamon and GNOME keybinding backends: given
which numeric keybinding slots are already taken, pick free ones."""


def find_free_slot_numbers(count: int, used_numbers: set[int]) -> list[int]:
    """Returns `count` non-negative integers not in `used_numbers`, in
    ascending order."""
    free_numbers: list[int] = []
    candidate = 0
    while len(free_numbers) < count:
        if candidate not in used_numbers:
            free_numbers.append(candidate)
        candidate += 1
    return free_numbers
