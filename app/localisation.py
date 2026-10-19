# Локализация: тексты программы на разных языках из localisation/local_<язык>.json
from __future__ import annotations

import json
from pathlib import Path

from .settings import LOCALISATION_DIR


class Localisation:
    """Загружает переводы один раз и отдаёт их по ключу.

    ВЫЗОВ === loc.t("menu.title") --> [категория.сообщение]
    """

    def __init__(self, language: str, fallback: str = "ru", folder: Path = LOCALISATION_DIR) -> None:
        self.folder = folder
        self.language = language
        self.fallback = self.load(fallback)
        self.texts = self.load(language)
        if not self.texts:
            print("Ошибка локализации. Откат на русскую локализацию")

    def load(self, language: str) -> dict[str, str]:
        """Читает local_<language>.json. Если файла нет или он сломан — пустой словарь."""
        path = self.folder / f"local_{language}.json"
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)  # Превращает JSON в словарь (dict)
        except (OSError, json.JSONDecodeError):
            return {}

    def t(self, key: str, **values: object) -> str:
        """Текст по ключу. Нет в текущем языке — берём из запасного, нет и там — возвращаем сам ключ."""
        text = self.texts.get(key) or self.fallback.get(key) or key
        return text.format(**values) if values else text
