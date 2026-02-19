import flet as ft
from src.core.toggle_user_sessions import toggle_sessions
import logging
import sys
import os
from pathlib import Path

# Настройка логгирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',
    filemode='w'
)


def resource_path(relative_path):
    """Получаем абсолютный путь к ресурсам для работы с PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main(page: ft.Page):
    """Главная функция приложения"""
    try:
        if sys.maxsize <= 2 ** 32:
            page.disable_animation = True

        logging.info("Инициализация приложения")

        # Настройки окна
        page.theme_mode = ft.ThemeMode.LIGHT
        page.title = "Водоканал - Мастер"
        page.window.width = 1920
        page.window.height = 1080
        page.window.maximized = True
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.window.prevent_close = True

        page.add(ft.ProgressRing())
        page.update()

        # Локализация
        page.locale_configuration = ft.LocaleConfiguration(
            supported_locales=[
                ft.Locale("es", "ES"),
                ft.Locale("ru", "RU"),
            ],
            current_locale=ft.Locale("ru", "RU")
        )

        # Иконка (используем resource_path для совместимости с PyInstaller)
        icon_path = resource_path("images/logoWin.ico")
        if os.path.exists(icon_path):
            page.window.icon = icon_path
        else:
            logging.warning(f"Файл иконки не найден: {icon_path}")

        # Диалог подтверждения закрытия
        def handle_window_event(e):
            if e.data == "close":
                logging.info("Запрос на закрытие приложения")
                page.open(confirm_dialog)

        page.window.on_event = handle_window_event

        def yes_click(e):
            logging.info("Пользователь подтвердил выход")
            page.window.destroy()

        def no_click(e):
            logging.info("Пользователь отменил выход")
            page.close(confirm_dialog)

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Пожалуйста, подтвердите"),
            content=ft.Text("Вы действительно хотите выйти из этого приложения?"),
            actions=[
                ft.ElevatedButton("Да", on_click=yes_click),
                ft.OutlinedButton("Нет", on_click=no_click),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # Основная логика приложения
        logging.info("Запуск toggle_sessions")
        toggle_sessions(page)

        logging.info("Интерфейс инициализирован")

    except Exception as e:
        logging.exception("Ошибка в main()")
        raise


if __name__ == "__main__":
    try:
        logging.info("Запуск Flet приложения")
        ft.app(
            target=main,
            view=ft.AppView.FLET_APP,
            assets_dir=resource_path(".") if getattr(sys, 'frozen', False) else None
        )
    except Exception as e:
        logging.exception("Ошибка при запуске Flet")
        input("Нажмите Enter для выхода...")  # Удержание консоли для просмотра ошибки
