# Настройки и пути. Этот файл ничего не импортирует из проекта, поэтому его можно импортировать откуда угодно.
from __future__ import annotations

import configparser
from pathlib import Path

# Пути
ROOT_DIR = Path(__file__).parent.parent.absolute()  # папка проекта (на уровень выше app/)
CONFIG_PATH = ROOT_DIR / "config" / "config.ini"
LOCALISATION_DIR = ROOT_DIR / "localisation"
LOGO = ROOT_DIR / "resources" / "likSocLogo.jpg"

# Лого + Баннер
CHAR_ASPECT = 0.48  # ширина символа консоли / его высота
MARGIN = 2  # пустых столбцов слева и справа от картинки

BANNER = [
    " _   _   _      ____                   _          _",
    "| | (_) | | __ / ___|    ___     ___  (_)   ___  | |_   _   _",
    "| | | | | |/ / \\___ \\   / _ \\   / __| | |  / _ \\ | __| | | | |",
    "| | | | |   <   ___) | | (_) | | (__  | | |  __/ | |_  | |_| |",
    "|_| |_| |_|\\_\\ |____/   \\___/   \\___| |_|  \\___|  \\__|  \\__, |",
    "                                                        |___/",
]
BANNER_WIDTH = max(len(line) for line in BANNER)

# Окно
TITLE = "likSociety"  # надпись в заголовке окна консоли
WINDOW_SCREEN_PART = 0.9  # какую часть высоты экрана занимает окно (0.9 = 90%)
WINDOW_ASPECT = 3 / 4  # ширина окна / высота окна


class Config:
    """Настройки пользователя из config/config.ini."""

    def __init__(self, path: Path = CONFIG_PATH) -> None:
        self.path = path
        self.parser = configparser.ConfigParser()
        self.parser.read(path, encoding="utf-8")

    @property
    def language(self) -> str:
        return self.parser.get("main", "localisation", fallback="ru")

    @language.setter
    def language(self, value: str) -> None:
        if not self.parser.has_section("main"):
            self.parser.add_section("main")
        self.parser.set("main", "localisation", value)

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as file:
            self.parser.write(file)
