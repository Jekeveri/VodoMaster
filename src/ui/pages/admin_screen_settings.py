import flet as ft

from src.core.toggle_user_sessions import logout


class SettingsPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_tab = 0
        self.setup_ui()

    def setup_ui(self):
        # 1. Создаем содержимое вкладок
        self.general_content = self.create_general_tab()
        self.account_content = self.create_account_tab()

        # 2. Область отображения контента
        self.content_area = ft.Container(expand=True)

        # 3. Кнопки переключения вкладок
        self.tab_buttons = ft.Row([
            self.create_tab_button("Общие", 0),
            self.create_tab_button("Аккаунт", 1)
        ], spacing=0)

        # 4. Собираем основной интерфейс
        self.view = ft.Column([
            ft.Container(
                content=self.tab_buttons,
                padding=ft.padding.only(top=10)
            ),
            ft.Divider(height=1),
            self.content_area
        ], expand=True)

        # 5. Инициализируем первую вкладку
        self.switch_tab(0)

    def create_tab_button(self, text, index):
        return ft.TextButton(
            text,
            on_click=lambda e: self.switch_tab(index),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=0),
                side=ft.border.BorderSide(
                    color=ft.colors.BLUE if index == self.current_tab
                    else ft.colors.TRANSPARENT,
                    width=2
                ),
                padding=20
            )
        )

    def create_general_tab(self):
        return ft.Column([
            ft.Text("Общие настройки", size=20, weight="bold"),
            ft.Container(
                content=ft.Column([
                    ft.Text("Версия приложения"),
                    ft.Text("v1.1.4.0", color=ft.colors.GREY_600),
                ]),
                padding=10,
                border=ft.border.all(1, ft.colors.OUTLINE),
                border_radius=8,
            ),
        ], spacing=20)

    def create_account_tab(self):
        return ft.Column([
            ft.Text("Управление аккаунтом", size=20, weight="bold"),
            ft.Container(
                content=ft.ElevatedButton(
                    "Выйти из аккаунта",
                    on_click=self.logout_account,
                    icon=ft.icons.LOGOUT,
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.RED,
                ),
                padding=10,
                border=ft.border.all(1, ft.colors.OUTLINE),
                border_radius=8,
            ),
        ], spacing=20)

    def switch_tab(self, index):
        self.current_tab = index
        self.content_area.content = (
            self.general_content if index == 0
            else self.account_content
        )

        # Обновляем стили кнопок
        for i, btn in enumerate(self.tab_buttons.controls):
            btn.style.side = ft.border.BorderSide(
                color=ft.colors.BLUE if i == index
                else ft.colors.TRANSPARENT,
                width=2
            )

        self.page.update()

    def logout_account(self, e):
        global dlg
        dlg = ft.AlertDialog(
            title=ft.Text("Подтверждение"),
            content=ft.Text("Вы действительно хотите выйти?"),
            actions=[
                ft.TextButton("Да", on_click=lambda e: self.confirm_logout()),
                ft.TextButton("Нет", on_click=lambda e: self.close_dialog())
            ],
        )
        self.page.open(dlg)
        self.page.update()

    def confirm_logout(self):
        self.page.close(dialog)
        self.page.close(dlg)
        self.page.update()
        logout(self.page)

    def close_dialog(self):
        self.page.close(dlg)
        self.page.close(dialog)
        self.page.update()


def open_settings(page: ft.Page):
    settings = SettingsPage(page)
    global dialog
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Настройки"),
        content=ft.Container(
            content=settings.view,
            width=600,
            height=400,
            padding=20,
        ),
        actions=[
            ft.TextButton("Закрыть", on_click=lambda e: close_dialog(page))
        ],
    )

    def close_dialog(page):
        page.close(dialog)
        page.update()

    page.open(dialog)
    page.update()