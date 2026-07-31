import signal
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ..indicator import Indicator


def main() -> None:
    window = Indicator()
    window.show_all()

    def handle_sigterm(*_args) -> None:
        window.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)
    Gtk.main()
