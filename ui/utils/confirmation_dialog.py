import json
import os
import sys
from pathlib import Path
from typing import Callable

import flet as ft


class ConfirmationDialogManager:
    _base_dir = None
    _config_file = None

    @classmethod
    def _get_base_dir(cls):
        if cls._base_dir is None:
            if getattr(sys, 'frozen', False):
                # Для собранного приложения
                exe_path = Path(sys.executable).parent
                # Определяем путь к основной директории приложения
                cls._base_dir = exe_path.parent if exe_path.name == '_internal' else exe_path
            else:
                # Для запуска из исходников - берём директорию основного скрипта
                cls._base_dir = Path(os.path.abspath(sys.argv[0])).parent
        return cls._base_dir

    @classmethod
    def _get_config_file(cls):
        return os.path.join(
            cls._get_base_dir(),
            'data', 'sessions', 'confirmation_config.json'
        )

    @classmethod
    def load_config(cls):
        config_file = cls._get_config_file()
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            return {}

    @classmethod
    def save_config(cls, config):
        config_file = cls._get_config_file()
        try:
            # Создаем все необходимые директории
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")

    @classmethod
    def show_confirmation_dialog(
            cls,
            page: ft.Page,
            title: str,
            message: str,
            on_confirm: Callable,
            dialog_type: str = 'default',
            icon_color: str = ft.colors.RED_600,
            confirm_color: str = ft.colors.RED_600
    ):
        config = cls.load_config()
        if config.get(f'disable_dialog_{dialog_type}', False):
            on_confirm()
            return

        dont_show_again = ft.Checkbox(
            label="Больше не показывать",
            value=False
        )

        def confirm_action(e):
            if dont_show_again.value:
                config[f'disable_dialog_{dialog_type}'] = True
                cls.save_config(config)
            page.close(confirm_dialog)
            on_confirm()

        def cancel_action(e):
            page.close(confirm_dialog)

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=icon_color),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.WARNING_ROUNDED, color=icon_color, size=48),
                    ft.Text(message, size=16, color=ft.colors.GREY_800)
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                dont_show_again
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, height=150),
            actions=[
                ft.TextButton("Отмена", on_click=cancel_action),
                ft.FilledButton("Подтвердить", on_click=confirm_action,
                                style=ft.ButtonStyle(bgcolor=confirm_color, color=ft.colors.WHITE))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10)
        )

        page.open(confirm_dialog)
        page.update()

    @classmethod
    def reset_all_dialogs(cls):
        """Сброс всех отключенных диалогов"""
        config = cls.load_config()
        for key in list(config.keys()):
            if key.startswith('disable_dialog_'):
                del config[key]
        cls.save_config(config)