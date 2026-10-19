# Точка входа: только запуск программы. Весь код — в папке app/
from app.console_window import ConsoleWindow
from app.localisation import Localisation
from app.menu import MainMenu
from app.screen import Screen
from app.settings import Config

if __name__ == "__main__":
    config = Config()
    ConsoleWindow().setup()
    with Screen() as screen:
        screen.show_logo()
        screen.wait_key()
        loc = Localisation(config.language)  # внутри Screen, чтобы ошибка локализации была видна под лого
        MainMenu(loc).show()
        input()
