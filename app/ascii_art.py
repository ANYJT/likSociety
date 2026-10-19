# Превращение картинки в ASCII-арт
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from .settings import CHAR_ASPECT

PALETTE = "@%#*+=-:. "  # от тёмного к светлому


class AsciiArt:
    """Картинка, которую можно нарисовать символами нужного размера."""

    def __init__(self, path: Path) -> None:
        self.path = path
        with Image.open(path) as image:
            self.ratio = image.height / image.width

    def size(self, max_columns: int, max_rows: int) -> tuple[int, int]:
        """Размер в символах (столбцы, строки): по всей высоте, но не шире max_columns."""
        rows = max_rows
        columns = round(rows / (self.ratio * CHAR_ASPECT))
        if columns > max_columns:
            columns = max_columns
            rows = max(1, round(columns * self.ratio * CHAR_ASPECT))
        return columns, rows

    def render(self, max_columns: int, max_rows: int) -> list[tuple[str, bool]]:
        """Список (символ, это_край). Края потом красятся в другой цвет."""
        columns, rows = self.size(max_columns, max_rows)
        image = ImageOps.grayscale(Image.open(self.path)).resize((columns, rows))
        pixels = list(image.get_flattened_data())
        result = []
        for y in range(rows):
            for x in range(columns):
                value = pixels[y * columns + x]
                left = pixels[y * columns + max(0, x - 1)]
                right = pixels[y * columns + min(columns - 1, x + 1)]
                up = pixels[max(0, y - 1) * columns + x]
                down = pixels[min(rows - 1, y + 1) * columns + x]
                edge = max(abs(value - left), abs(value - right), abs(value - up), abs(value - down)) > 32
                result.append((PALETTE[value * (len(PALETTE) - 1) // 255], edge))
            if y < rows - 1:
                result.append(("\n", False))
        return result
