# Меню программы
from __future__ import annotations

import time

from .localisation import Localisation

class MainMenu:
    """Главное меню. Пункты — ключи из localisation/local_<язык>.json."""

    KEYS = ["menu.title", "menu.tools", "menu.info", "menu.donate"]

    def __init__(self, loc: Localisation, delay: float = 0.1) -> None:
        self.loc = loc
        self.delay = delay  # пауза между буквами при печати

    def show(self) -> None:
        full_text = "\n".join(self.loc.t(key) for key in self.KEYS)
        for char in full_text:
            print(char, end="", flush=True)
            time.sleep(self.delay)
        print()