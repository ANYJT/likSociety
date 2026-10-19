# Экран программы: лого сверху, весь текст (print / input) — блоком по центру под ним
from __future__ import annotations

import builtins
import os
import sys
import threading
import time

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.text import Text

from .ascii_art import AsciiArt
from .layout import Layout
from .settings import BANNER, BANNER_WIDTH, LOGO, MARGIN

ACCENT = "bold #800020"  # цвет краёв картинки и баннера


class Screen:
    """Внутри `with Screen() as screen:` любой print() и input() выводится под лого."""

    def __init__(self) -> None:
        self.console = Console(file=sys.stdout)  # rich пишет в настоящую консоль
        width, height = self.console.size
        layout = Layout(height)  # та же раскладка, что и в ConsoleWindow, поэтому картинка встаёт ровно
        self.text_rows = layout.text_rows  # сколько строк текста помещается под лого
        self.banner = Text("\n".join(line.ljust(BANNER_WIDTH) for line in BANNER), style=ACCENT)
        self.art = AsciiArt(LOGO).render(max_columns=width - 2 * MARGIN, max_rows=layout.art_rows)
        self.shown = Text()
        self.show_banner = False
        self.lines = [""]  # строки текста под лого, последняя — та, что печатается сейчас
        self.lock = threading.Lock()
        self.live = Live(
            console=self.console,
            screen=True,
            refresh_per_second=30,
            get_renderable=self.render,
            redirect_stdout=False,
            redirect_stderr=False,
        )

    def __enter__(self) -> Screen:
        self.live.start()
        # всё, что выводит программа через print() и input(), попадает на экран под лого
        self.old_stdout, self.old_input = sys.stdout, builtins.input
        sys.stdout = self
        builtins.input = self.input
        return self

    def __exit__(self, *exc) -> None:
        sys.stdout, builtins.input = self.old_stdout, self.old_input
        self.live.stop()

    def render(self) -> Group:
        with self.lock:
            lines = self.lines[-self.text_rows:]
        lines += [""] * (self.text_rows - len(lines))
        # строки выровнены по левому краю, а весь блок стоит по центру экрана
        text = Align.center(Text("\n".join(lines), no_wrap=True, overflow="ellipsis"))
        parts = [Align.center(self.shown), Text(" ")]
        if self.show_banner:
            parts += [Align.center(self.banner), Text(" ")]
        else:
            parts.append(Text("\n" * len(BANNER)))  # место под баннер, чтобы лого не прыгало
        parts.append(text)
        return Group(*parts)

    # --- методы, которые делают Screen заменой sys.stdout ---
    def write(self, data: str) -> int:
        with self.lock:
            chunks = data.split("\n")
            self.lines[-1] += chunks[0]
            self.lines.extend(chunks[1:])
        return len(data)

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        return False

    # --- работа с экраном ---
    def show_logo(self) -> None:
        for char, is_edge in self.art:
            self.shown.append(char, style=ACCENT if is_edge else "grey30")
            time.sleep(0.001)
        self.show_banner = True

    def clear(self) -> None:
        with self.lock:
            self.lines = [""]

    def wait_key(self, hint: str = "Нажмите любую клавишу...") -> None:
        print(hint, end="")
        if os.name == "nt":
            import msvcrt

            msvcrt.getwch()
        else:
            sys.stdin.readline()
        self.clear()

    def input(self, prompt: str = "") -> str:
        """Замена input(): ввод показывается по центру под лого."""
        print(prompt, end="")
        if os.name != "nt":
            answer = sys.stdin.readline().rstrip("\n")
            print(answer)
            return answer
        import msvcrt

        answer = ""
        print("_", end="")  # курсор
        while True:
            char = msvcrt.getwch()
            if char in ("\x00", "\xe0"):  # стрелки, F1... — пропускаем
                msvcrt.getwch()
                continue
            if char == "\x03":  # Ctrl+C
                raise KeyboardInterrupt
            with self.lock:
                self.lines[-1] = self.lines[-1][:-1]  # убираем курсор
            if char == "\r":
                print()
                return answer
            if char == "\b":
                if answer:
                    answer = answer[:-1]
                    with self.lock:
                        self.lines[-1] = self.lines[-1][:-1]
            elif char.isprintable():
                answer += char
                print(char, end="")
            print("_", end="")
