import os
import sys

import flet as ft

from src.database.auth import check_user_credentials
from src.ui.components.navigations import role_definition
from src.ui.utils.ui_blocker import block_ui


def resource_path(relative_path):
    """Получаем абсолютный путь к ресурсам для работы с PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def authentication(page):
    """Адаптивная форма авторизации с градиентом и центрированием"""
    page.clean()
    page.bgcolor = ft.colors.BLUE_50
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 0
    page.spacing = 0

    # Константы
    MAX_FORM_WIDTH = 500
    MIN_FORM_WIDTH = 300
    MAX_FORM_HEIGHT = 700
    MIN_FORM_HEIGHT = 400

    VERTICAL_PADDING = 20

    MAX_LOGO_SIZE = 150
    MIN_LOGO_SIZE = 80

    @block_ui(page)
    def on_submit(e):
        if not login.value or not password.value:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Пожалуйста, заполните все поля", size=16),
                bgcolor=ft.colors.RED_400,
                action="OK"
            )
            page.snack_bar.open = True
            page.update()
            return

        if check_user_credentials(login.value, password.value, page):
            role_definition(page)
        else:
            login.value = ""
            password.value = ""
            page.update()

    def update_layout():
        """Адаптация элементов при изменении размера окна"""
        form_width = min(MAX_FORM_WIDTH, page.window.width * 0.9)
        logo_size = max(MIN_LOGO_SIZE, min(MAX_LOGO_SIZE, page.window.width * 0.2))
        title_size = max(24, min(60, page.window.width * 0.08))

        form_height = min(MAX_FORM_HEIGHT, max(MIN_FORM_HEIGHT, page.window.height * 0.8))
        vertical_padding = max(VERTICAL_PADDING, page.window.height * 0.05)

        form_container.height = form_height
        form_container.padding = ft.padding.symmetric(
            horizontal=30,
            vertical=vertical_padding
        )

        # Пропорциональные отступы между элементами
        form_container.content.controls[2].height = form_height * 0.05  # 5% от высоты формы
        form_container.content.controls[4].height = form_height * 0.03  # 3% от высоты формы
        form_container.content.controls[6].height = form_height * 0.05  # 5% от высоты формы

        # Обновление размеров элементов
        logowin.width = logo_size
        logowin.height = logo_size
        title.size = title_size

        form_container.content.width = form_width
        form_container.content.height = form_width * 1.4

        login.width = form_width * 0.8
        password.width = form_width * 0.8
        submit_button.width = form_width * 0.8

        page.update()

    # Фон с градиентом
    background = ft.Container(
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.colors.BLUE_600, ft.colors.SURFACE, ft.colors.BLUE_600],
        ),
    )

    # Логотип и заголовок
    logowin = ft.Image(
        resource_path("images/logo_png-round.png"),
        width=MAX_LOGO_SIZE,
        height=MAX_LOGO_SIZE,
        fit=ft.ImageFit.CONTAIN
    )
    title = ft.Text(
        "Водоканал",
        color=ft.colors.BLUE_900,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
        size=60
    )

    # Поля ввода
    login = ft.TextField(
        label="Логин",
        border_color=ft.colors.BLUE_400,
        focused_border_color=ft.colors.BLUE_700,
        prefix_icon=ft.icons.PERSON,
        bgcolor=ft.colors.WHITE,
        # value="master",
        border_radius=10,
        text_size=18,
        adaptive=True
    )

    password = ft.TextField(
        label="Пароль",
        password=True,
        can_reveal_password=True,
        border_color=ft.colors.BLUE_400,
        focused_border_color=ft.colors.BLUE_700,
        prefix_icon=ft.icons.LOCK,
        bgcolor=ft.colors.WHITE,
        # value="master",
        border_radius=10,
        text_size=18,
        adaptive=True
    )

    # Кнопка входа
    submit_button = ft.ElevatedButton(
        content=ft.Text("Войти", size=20, weight=ft.FontWeight.W_500),
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
            bgcolor=ft.colors.BLUE_600,
            padding=ft.padding.symmetric(horizontal=40, vertical=20),
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
        on_click=on_submit,
        adaptive=True
    )

    # Контейнер формы
    form_container = ft.Container(
        content=ft.Column(
            [
                ft.Row([logowin], alignment=ft.MainAxisAlignment.CENTER),
                title,
                ft.Container(height=40, expand=0.6),  # Добавляем expand
                login,
                ft.Container(height=20, expand=0.5),  # Пропорциональные отступы
                password,
                ft.Container(height=30, expand=1),
                submit_button,
            ],
            expand=True,
            spacing=0,
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=30, vertical=VERTICAL_PADDING),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=[ft.colors.WHITE, ft.colors.BLUE_50],
        ),
        border_radius=20,
        shadow=ft.BoxShadow(
            spread_radius=2,
            blur_radius=20,
            color=ft.colors.BLUE_GREY_300,
            offset=ft.Offset(0, 5),
        ),
        width=MAX_FORM_WIDTH,
        height=MAX_FORM_HEIGHT,  # Фиксированная максимальная высота
        alignment=ft.alignment.center,
    )

    # Основная компоновка с правильным центрированием
    page.add(
        ft.Stack(
            [
                background,
                ft.Container(
                    content=ft.ResponsiveRow(
                        [
                            ft.Column(
                                [form_container],
                                col={"xs": 12, "sm": 10, "md": 8, "lg": 6},
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True  # Разрешаем масштабирование
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                        expand=True  # Разрешаем масштабирование
                    ),
                    expand=True,
                    alignment=ft.alignment.center
                )
            ],
            expand=True
        )
    )

    # Обработчик изменения размера
    page.on_resize = lambda e: update_layout()
    update_layout()
    page.update()