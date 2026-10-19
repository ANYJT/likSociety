# Библиотеки
from __future__ import annotations

import ctypes
import os
import time
from pathlib import Path

import json
import configparser

from PIL import Image, ImageOps
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.text import Text

# Параметры
cfg = configparser.ConfigParser()
path = Path(__file__)
ROOT_DIR = path.parent.absolute()

# Локализация
local_ru = os.path.join(ROOT_DIR, "localisation/local_ru.json")
local_en = os.path.join(ROOT_DIR, "localisation/local_en.json")

# Конфиг
cfgpath = os.path.join(ROOT_DIR, "config/config.ini")
cfg.read(cfgpath)
current_localisation = cfg.get("main", "localisation", fallback="Не указана локализация")

# Лого + Баннер
LOGO = os.path.join(ROOT_DIR, "resources/likSocLogo.jpg")
CHAR_ASPECT = 0.48  # ширина символа консоли / его высота

BANNER = [
    "  _     _ _      ____             ",
    " | |   (_) | __ / ___|  ___   ___ ",
    " | |   | | |/ / \\___ \\ / _ \\ / __|",
    " | |___| |   <   ___) | (_) | (__ ",
    " |_____|_|_|\\_\\ |____/ \\___/ \\___|",
]

# Функция локализации
# ВЫЗОВ === print(t_("menu.title")) --> [категория.сообщение]
def t_(message):
    print(current_localisation)
    try:
        json_localisation = os.path.join(ROOT_DIR, "localisation/local_"+current_localisation+".json")
        with open(json_localisation, "r", encoding="utf-8") as file:
            raw = json.load(file)  # Превращает JSON в словарь (dict) или список (list)
        lc_mes = raw[message]
    except:
        print("Ошибка локализации. Откат на русскую локализацию")
        json_localisation = local_ru
        with open(json_localisation, "r", encoding="utf-8") as file:
            raw = json.load(file)  # Превращает JSON в словарь (dict) или список (list)
        lc_mes = raw[message]
    return lc_mes

# Основные функции
def maximize_console() -> None:
    """Разворачивает консоль на весь экран и не даёт менять её размер."""
    if os.name != "nt":
        return
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    kernel32.GetConsoleWindow.restype = wintypes.HWND
    kernel32.GetStdHandle.restype = wintypes.HANDLE
    kernel32.GetLargestConsoleWindowSize.restype = wintypes._COORD
    kernel32.GetLargestConsoleWindowSize.argtypes = [wintypes.HANDLE]
    kernel32.SetConsoleScreenBufferSize.argtypes = [wintypes.HANDLE, wintypes._COORD]
    kernel32.SetConsoleWindowInfo.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(wintypes.SMALL_RECT)]
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
    user32.GetSystemMenu.restype = wintypes.HMENU
    user32.GetSystemMenu.argtypes = [wintypes.HWND, wintypes.BOOL]
    user32.DeleteMenu.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.UINT]
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND] + [ctypes.c_int] * 4 + [wintypes.UINT]

    SW_MAXIMIZE = 3
    hwnd = kernel32.GetConsoleWindow()

    if os.environ.get("WT_SESSION"):
        # Windows Terminal: консольное окно скрыто, разворачиваем окно самого терминала
        window = (hwnd and user32.GetAncestor(hwnd, 3)) or user32.GetForegroundWindow()  # GA_ROOTOWNER
        if window:
            user32.ShowWindow(window, SW_MAXIMIZE)
            time.sleep(0.3)  # ждём, пока терминал пересчитает размер
        return

    if not hwnd:
        return
    output = kernel32.GetStdHandle(-11)
    largest = kernel32.GetLargestConsoleWindowSize(output)
    width, height = largest.X, largest.Y
    # буфер ровно по размеру экрана, чтобы не было полос прокрутки
    kernel32.SetConsoleScreenBufferSize(output, wintypes._COORD(width, height))
    user32.ShowWindow(hwnd, SW_MAXIMIZE)
    rect = wintypes.SMALL_RECT(0, 0, width - 1, height - 1)
    kernel32.SetConsoleWindowInfo(output, True, ctypes.byref(rect))
    kernel32.SetConsoleScreenBufferSize(output, wintypes._COORD(width, height))
    # фиксируем: без рамки изменения размера, кнопки "развернуть" и пунктов меню
    GWL_STYLE = -16
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~0x00040000 & ~0x00010000)
    menu = user32.GetSystemMenu(hwnd, False)
    if menu:
        for command in (0xF000, 0xF010, 0xF030, 0xF120):  # SC_SIZE, SC_MOVE, SC_MAXIMIZE, SC_RESTORE
            user32.DeleteMenu(menu, command, 0)
    user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0020)
    time.sleep(0.1)


def image_to_ascii(path: Path, max_columns: int, max_rows: int) -> list[tuple[str, bool]]:
    image = ImageOps.grayscale(Image.open(path))
    ratio = image.height / image.width
    # подгоняем картинку под доступную высоту, не вылезая за ширину
    rows = max_rows
    columns = round(rows / (ratio * CHAR_ASPECT))
    if columns > max_columns:
        columns = max_columns
        rows = max(1, round(columns * ratio * CHAR_ASPECT))
    image = image.resize((columns, rows))
    palette = "@%#*+=-:. "
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
            result.append((palette[value * (len(palette) - 1) // 255], edge))
        if y < rows - 1:
            result.append(("\n", False))
    return result


def wait_key() -> None:
    if os.name == "nt":
        import msvcrt

        msvcrt.getch()
    else:
        input()


def show_logo() -> None:
    console = Console()
    width, height = console.size
    banner_width = max(len(line) for line in BANNER)
    banner = Text("\n".join(line.ljust(banner_width) for line in BANNER), style="bold #800020")
    # картинка + пустая строка + баннер = вся высота консоли
    art = image_to_ascii(LOGO, max_columns=width - 2, max_rows=height - len(BANNER) - 1)
    shown = Text()

    def frame(*parts: Text) -> Align:
        return Align.center(Group(*(Align.center(p) for p in parts)), vertical="middle")

    with Live(console=console, screen=True, refresh_per_second=30) as live:
        for char, is_edge in art:
            shown.append(char, style="bold #800020" if is_edge else "grey30")
            live.update(frame(shown))
            time.sleep(0.001)
        live.update(frame(shown, Text(), banner))
        wait_key()

def main_menu():
    print("Выберите действие")
    
if __name__ == "__main__":
    # maximize_console()
    # show_logo()
    print(t_("menu.title"))
    input()
