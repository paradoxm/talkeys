import subprocess

from .. import paths

_OTHER_LANG = {"en": "ru", "ru": "en"}


def main() -> None:
    new_lang = _OTHER_LANG[paths.get_lang()]
    paths.set_lang(new_lang)
    subprocess.run(
        ["notify-send", "-i", "preferences-desktop-locale", "Dictation language", new_lang],
        check=False,
    )
