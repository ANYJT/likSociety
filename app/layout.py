# Раскладка экрана по высоте. Её используют и ConsoleWindow (чтобы выбрать размер окна),
# и Screen (чтобы нарисовать картинку), поэтому числа у них всегда совпадают.
from __future__ import annotations

from .settings import BANNER


class Layout:
    """Сверху вниз: картинка + пустая строка + баннер + пустая строка + текст."""

    def __init__(self, height: int) -> None:
        self.height = height
        self.text_rows = max(6, height // 4)  # сколько строк внизу экрана оставить под текст
        self.art_rows = height - len(BANNER) - 2 - self.text_rows  # что остаётся на картинку
