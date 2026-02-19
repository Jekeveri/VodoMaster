import re

import flet as ft

import src.database.admin.modification_server as modification_server


class CreateEmployeeDialog:
    def __init__(self, page: ft.Page):
        self.page = page
        self.dialog = None
        self._create_dialog()
        self._setup_dialog()

    def _create_dialog(self):
        # Поля ввода
        self.first_name = ft.TextField(
            label="Имя",
            width=400,
            hint_text="Введите имя",
            capitalization=ft.TextCapitalization.WORDS,
            bgcolor=ft.colors.WHITE
        )

        self.last_name = ft.TextField(
            label="Фамилия",
            width=400,
            hint_text="Введите фамилию",
            capitalization=ft.TextCapitalization.WORDS,
            bgcolor=ft.colors.WHITE
        )

        self.patronymic = ft.TextField(
            label="Отчество",
            width=400,
            hint_text="Введите отчество (необязательно)",
            capitalization=ft.TextCapitalization.WORDS,
            bgcolor=ft.colors.WHITE
        )

        self.phone = ft.TextField(
            label="Телефон",
            width=400,
            hint_text="Введите 10 цифр номера",
            prefix_text="+7",
            max_length=10,
            bgcolor=ft.colors.WHITE
        )

        self.email = ft.TextField(
            label="Email",
            width=400,
            hint_text="example@company.com",
            bgcolor=ft.colors.WHITE
        )

        self.login = ft.TextField(
            label="Логин",
            width=400,
            hint_text="Введите логин",
            bgcolor=ft.colors.WHITE
        )

        self.password = ft.TextField(
            label="Пароль",
            width=400,
            hint_text="Введите пароль",
            password=True,
            can_reveal_password=True,
            bgcolor=ft.colors.WHITE
        )

        self.post = ft.Dropdown(
            label="Должность",
            width=400,
            filled=True,
            fill_color=ft.colors.WHITE,
            options=[
                ft.dropdown.Option("Мастер"),
                ft.dropdown.Option("Контролёр")
            ]
        )

    def _setup_dialog(self):
        """Настройка диалогового окна"""
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Создание сотрудника",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLUE_900
            ),
            content=ft.Column([
                self.first_name,
                self.last_name,
                self.patronymic,
                self.phone,
                self.email,
                self.login,
                self.password,
                self.post
            ], width=400, height=500),
            actions=[
                ft.TextButton(
                    "Отмена",
                    on_click=self.close_dialog,
                    style=ft.ButtonStyle(
                        color=ft.colors.BLUE_900,
                    )
                ),
                ft.FilledButton(
                    "Сохранить",
                    on_click=self.save_employee,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.BLUE_600,
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=10),
            surface_tint_color=ft.colors.BLUE_50,
            bgcolor=ft.colors.BLUE_50,
            shadow_color=ft.colors.BLUE_200,
            elevation=5
        )

        # Стилизация полей ввода
        blue_text_field_style = {
            "border_color": ft.colors.BLUE_300,
            "focused_border_color": ft.colors.BLUE_600,
            "label_style": {"color": ft.colors.BLUE_900},
            "cursor_color": ft.colors.BLUE_600,
            "selection_color": ft.colors.BLUE_100
        }

        # Применение стиля ко всем полям
        for field in [
            self.first_name,
            self.last_name,
            self.patronymic,
            self.phone,
            self.email,
            self.login,
            self.password
        ]:
            field.border_color = blue_text_field_style["border_color"]
            field.focused_border_color = blue_text_field_style["focused_border_color"]
            field.label_style = blue_text_field_style["label_style"]
            field.cursor_color = blue_text_field_style["cursor_color"]
            field.selection_color = blue_text_field_style["selection_color"]

        # Стилизация дропдауна
        self.post.border_color = ft.colors.BLUE_300
        self.post.focused_border_color = ft.colors.BLUE_600
        self.post.label_style = {"color": ft.colors.BLUE_900}

    def validate_data(self):
        """Валидация введенных данных"""
        errors = []

        # Проверка имени и фамилии
        if not self.first_name.value:
            errors.append("Введите имя")
        if not self.last_name.value:
            errors.append("Введите фамилию")

        # Проверка телефона
        # phone_pattern = r'^\+7\d{10}$'
        # if not re.match(phone_pattern, f"+7{self.phone.value}"):
        #     errors.append("Некорректный формат телефона")
        #
        # # Проверка email
        # email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        # if not re.match(email_pattern, self.email.value):
        #     errors.append("Некорректный формат email")

        # Проверка логина
        if not self.login.value:
            errors.append("Введите логин")

        # Проверка пароля
        if not self.password.value or len(self.password.value) < 4:
            errors.append("Пароль должен быть не короче 4 символов")

        # Проверка должности
        if not self.post.value:
            errors.append("Выберите должность")

        return errors

    def save_employee(self, e):
        """Сохранение сотрудника"""
        errors = self.validate_data()

        if errors:
            # Используем стандартный SnackBar Flet
            snack_bar = ft.SnackBar(
                content=ft.Text("\n".join(errors), color=ft.colors.RED),
                duration=3000,
                open=True
            )
            self.page.overlay.append(snack_bar)
            self.page.update()
            return

        try:
            # Вызов метода сохранения из модуля модификации
            result = modification_server.send_employee_data({
                "first_name": self.first_name.value,
                "last_name": self.last_name.value,
                "patronimyc": self.patronymic.value or "",
                "phone_number": f"+7{self.phone.value}",
                "email": self.email.value,
                "login": self.login.value,
                "password": self.password.value,
                "post": self.post.value
            })

            if result:
                # Успешное создание
                snack_bar = ft.SnackBar(
                    content=ft.Text("Сотрудник успешно создан", color=ft.colors.GREEN),
                    duration=3000,
                    open=True
                )
                self.page.overlay.append(snack_bar)
                self.close_dialog()
            else:
                # Ошибка создания
                snack_bar = ft.SnackBar(
                    content=ft.Text("Ошибка при создании сотрудника", color=ft.colors.RED),
                    duration=3000,
                    open=True
                )
                self.page.overlay.append(snack_bar)

        except Exception as ex:
            # Системная ошибка
            snack_bar = ft.SnackBar(
                content=ft.Text(f"Ошибка: {str(ex)}", color=ft.colors.RED),
                duration=3000,
                open=True
            )
            self.page.overlay.append(snack_bar)
            self.page.update()

    def close_dialog(self, e=None):
        """Закрытие диалога"""
        self.page.close(self.dialog)
        self.page.update()

    def open(self):
        """Открытие диалога"""
        self.page.open(self.dialog)
        self.page.update()
