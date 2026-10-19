# Окно консоли Windows: заголовок, размер, положение. Всё через функции Windows (ctypes).
from __future__ import annotations

import ctypes
import os
import time

from .ascii_art import AsciiArt
from .layout import Layout
from .settings import BANNER_WIDTH, LOGO, MARGIN, TITLE, WINDOW_ASPECT, WINDOW_SCREEN_PART

SW_MAXIMIZE, SW_RESTORE = 3, 9
GWL_STYLE = -16
WS_SIZEBOX, WS_MAXIMIZEBOX = 0x00040000, 0x00010000
SC_SIZE, SC_MOVE, SC_MAXIMIZE, SC_RESTORE = 0xF000, 0xF010, 0xF030, 0xF120
SPI_GETWORKAREA = 0x0030
SWP_NOSIZE, SWP_NOMOVE, SWP_NOZORDER, SWP_FRAMECHANGED = 0x0001, 0x0002, 0x0004, 0x0020
GA_ROOTOWNER = 3
STD_OUTPUT_HANDLE = -11

if os.name == "nt":
    from ctypes import wintypes

    class CONSOLE_FONT_INFOEX(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.ULONG),
            ("nFont", wintypes.DWORD),
            ("dwFontSize", wintypes._COORD),
            ("FontFamily", wintypes.UINT),
            ("FontWeight", wintypes.UINT),
            ("FaceName", wintypes.WCHAR * 32),
        ]

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    # типы аргументов и результатов, чтобы на 64-битной Windows адреса окон не обрезались
    kernel32.GetConsoleWindow.restype = wintypes.HWND
    kernel32.GetStdHandle.restype = wintypes.HANDLE
    kernel32.GetLargestConsoleWindowSize.restype = wintypes._COORD
    kernel32.GetLargestConsoleWindowSize.argtypes = [wintypes.HANDLE]
    kernel32.GetCurrentConsoleFontEx.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(CONSOLE_FONT_INFOEX)]
    kernel32.SetConsoleScreenBufferSize.argtypes = [wintypes.HANDLE, wintypes._COORD]
    kernel32.SetConsoleTitleW.argtypes = [wintypes.LPCWSTR]
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
    user32.AdjustWindowRect.argtypes = [ctypes.POINTER(wintypes.RECT), wintypes.DWORD, wintypes.BOOL]
    user32.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]


class ConsoleWindow:
    """Окно консоли: задаёт заголовок, делает прямоугольным (WINDOW_ASPECT), ставит по центру
    и запрещает менять размер. На не-Windows ничего не делает."""

    def __init__(self) -> None:
        self.enabled = os.name == "nt"
        if not self.enabled:
            return
        # считаем в настоящих пикселях экрана, даже если в Windows включено масштабирование 125%/150%
        user32.SetProcessDPIAware()
        self.hwnd = kernel32.GetConsoleWindow()
        self.output = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    def setup(self) -> None:
        """Всё сразу: заголовок, размер, центр."""
        if not self.enabled:
            return
        self.set_title(TITLE)
        if os.environ.get("WT_SESSION"):
            self.maximize_terminal()
            return
        if not self.hwnd:
            return
        user32.ShowWindow(self.hwnd, SW_RESTORE)  # если окно было развёрнуто — возвращаем обычный режим
        self.lock_size()
        self.measure()
        width, height = self.choose_size()
        self.resize(width, height)
        self.center(width, height)
        time.sleep(0.1)  # ждём, пока консоль применит новый размер

    def set_title(self, title: str) -> None:
        """Надпись в заголовке окна (работает и в Windows Terminal)."""
        kernel32.SetConsoleTitleW(title)

    def maximize_terminal(self) -> None:
        """Windows Terminal: размер окна в символах отсюда не задать, поэтому просто разворачиваем."""
        window = (self.hwnd and user32.GetAncestor(self.hwnd, GA_ROOTOWNER)) or user32.GetForegroundWindow()
        if window:
            user32.ShowWindow(window, SW_MAXIMIZE)
            time.sleep(0.3)  # ждём, пока терминал пересчитает размер

    def lock_size(self) -> None:
        """Убираем рамку изменения размера, кнопку "развернуть" и пункты меню окна."""
        self.style = user32.GetWindowLongW(self.hwnd, GWL_STYLE) & ~WS_SIZEBOX & ~WS_MAXIMIZEBOX
        user32.SetWindowLongW(self.hwnd, GWL_STYLE, self.style)
        menu = user32.GetSystemMenu(self.hwnd, False)
        if menu:
            for command in (SC_SIZE, SC_MOVE, SC_MAXIMIZE, SC_RESTORE):
                user32.DeleteMenu(menu, command, 0)
        flags = SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_FRAMECHANGED
        user32.SetWindowPos(self.hwnd, None, 0, 0, 0, 0, flags)

    def measure(self) -> None:
        """Узнаём размеры: экран без панели задач, рамка окна, один символ шрифта."""
        self.work = wintypes.RECT()
        user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(self.work), 0)
        self.work_w = self.work.right - self.work.left
        self.work_h = self.work.bottom - self.work.top
        frame = wintypes.RECT(0, 0, 0, 0)
        user32.AdjustWindowRect(ctypes.byref(frame), self.style, False)
        self.frame_w = frame.right - frame.left  # левая и правая рамка
        self.frame_h = frame.bottom - frame.top  # заголовок + верхняя и нижняя рамка
        font = CONSOLE_FONT_INFOEX()
        font.cbSize = ctypes.sizeof(CONSOLE_FONT_INFOEX)
        kernel32.GetCurrentConsoleFontEx(self.output, False, ctypes.byref(font))
        self.char_w = font.dwFontSize.X or 8
        self.char_h = font.dwFontSize.Y or 16
        self.largest = kernel32.GetLargestConsoleWindowSize(self.output)

    def choose_size(self) -> tuple[int, int]:
        """Высота — WINDOW_SCREEN_PART от экрана, ширина — по пропорции WINDOW_ASPECT,
        но не уже картинки с полями (иначе картинка не влезет). Возвращает (столбцы, строки)."""
        height = min(self.largest.Y, (int(self.work_h * WINDOW_SCREEN_PART) - self.frame_h) // self.char_h)
        width = round(height * self.char_h * WINDOW_ASPECT) // self.char_w
        columns, _ = AsciiArt(LOGO).size(self.largest.X - 2 * MARGIN, Layout(height).art_rows)
        width = min(self.largest.X, max(width, columns + 2 * MARGIN, BANNER_WIDTH + 2 * MARGIN))
        return width, height

    def resize(self, width: int, height: int) -> None:
        """Окно не может быть больше буфера, поэтому сначала сжимаем окно до 1x1,
        потом ставим буфер, потом растягиваем окно до буфера (буфер = окно, значит без полос прокрутки)."""
        tiny = wintypes.SMALL_RECT(0, 0, 0, 0)
        kernel32.SetConsoleWindowInfo(self.output, True, ctypes.byref(tiny))
        kernel32.SetConsoleScreenBufferSize(self.output, wintypes._COORD(width, height))
        rect = wintypes.SMALL_RECT(0, 0, width - 1, height - 1)
        kernel32.SetConsoleWindowInfo(self.output, True, ctypes.byref(rect))

    def center(self, width: int, height: int) -> None:
        """Ставим окно по центру экрана. Размер в пикселях считаем сами (символы × шрифт + рамка):
        консоль меняет размер не мгновенно, и GetWindowRect сразу после смены может вернуть старый."""
        window_w = width * self.char_w + self.frame_w
        window_h = height * self.char_h + self.frame_h
        x = self.work.left + (self.work_w - window_w) // 2
        y = self.work.top + (self.work_h - window_h) // 2
        user32.SetWindowPos(self.hwnd, None, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER)
