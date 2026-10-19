# Меню программы
from __future__ import annotations

import time
from typing import Callable

from .localisation import Localisation
from .screen import Screen


class Menu:
    """Общая основа для всех меню. Наследники задают TITLE, BACK и заполняют self.items."""

    TITLE = "menu.title"  # ключ заголовка в JSON — наследник заменяет на свой
    BACK = "menu.back"  # ключ пункта "0": "Назад" (в главном меню — "Выход")

    def __init__(self, loc: Localisation, screen: Screen):
        self.loc = loc          # данные объекта loc
        self.screen = screen          # данные объекта screen
        # пункты меню: (ключ из JSON, что вызвать при выборе). Наследник заполняет после super().__init__
        self.items: list[tuple[str, Callable[[], None]]] = []

    def run(self) -> None:
        actions = {}
        for number, (_, action) in enumerate(self.items, start=1):
            actions[str(number)] = action
        while True:
            self.screen.clear()
            print(self.loc.t(self.TITLE))
            for number, (key, _) in enumerate(self.items, start=1):
                print(f"{number}. {self.loc.t(key)}")
            print(f"0. {self.loc.t(self.BACK)}")
            choose = input(self.loc.t("menu.prompt"))
            choose = choose.strip()
            if choose == "0":
                return
            action = actions.get(choose)
            if action is None:
                self.message("menu.wrong_choice")
                continue
            action()

    def message(self, key: str) -> None:
        """Показать текст и подождать нажатия, чтобы его успели прочитать до очистки экрана."""
        print(self.loc.t(key))
        self.screen.wait_key()