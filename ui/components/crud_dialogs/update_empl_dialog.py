import re

import flet as ft

import src.database.admin.modification_server as modification_server
import src.database.admin.select_server as select_server
from src.utils.show_snack_bar import show_snack_bar


class UpdateEmployeeDialog:
    def __init__(self, page: ft.Page, employee_id):
        self.page = page
        self.employee_id = employee_id
        self.dialog = None
        self.employee_data = None
        self._load_employee_data()
        self._create_dialog()
        self._setup_dialog()

    def _load_employee_data(self):
        """Загрузка данных сотрудника"""
        try:
            # Получаем детальную информацию о сотруднике
            employee_details = select_server.get_employee_details(self.employee_id)

            if not employee_details or 'employee' not in employee_details:
                show_snack_bar(self.page, "Не удалось загрузить данные сотрудника")
                return None

            self.employee_data = employee_details['employee']

        except Exception as e:
            show_snack_bar(self.page, f"Ошибка загрузки данных: {str(e)}")
            return None

    def _create_dialog(self):
        # Проверяем, что данные загружены
        if not self.employee_data:
            return

        # Поля ввода
        self.first_name = ft.TextField(
            label="Имя",
            width=400,
            hint_text="Введите имя",
            capitalization=ft.TextCapitalization.WORDS,
            value=self.employee_data.get('first_name', ''),
            bgcolor=ft.colors.WHITE
        )

        self.last_name = ft.TextField(
            label="Фамилия",
            width=400,
            hint_text="Введите фамилию",
            capitalization=ft.TextCapitalization.WORDS,
            value=self.employee_data.get('last_name', ''),
            bgcolor=ft.colors.WHITE
        )

        self.patronymic = ft.TextField(
            label="Отчество",
            width=400,
            hint_text="Введите отчество (необязательно)",
            capitalization=ft.TextCapitalization.WORDS,
            value=self.employee_data.get('patronymic', ''),
            bgcolor=ft.colors.WHITE
        )

        self.phone = ft.TextField(
            label="Телефон",
            width=400,
            hint_text="Введите 10 цифр номера",
            prefix_text="+7",
            max_length=10,
            value=self.employee_data.get('phone_number', '').replace("+7", "") if self.employee_data.get(
                'phone_number') else '',
            bgcolor=ft.colors.WHITE
        )

        self.email = ft.TextField(
            label="Email",
            width=400,
            hint_text="example@company.com",
            value=self.employee_data.get('email', ''),
            bgcolor=ft.colors.WHITE
        )

        self.login = ft.TextField(
            label="Логин",
            width=400,
            hint_text="Введите логин",
            value=self.employee_data.get('login', ''),
            bgcolor=ft.colors.WHITE
        )

        self.password = ft.TextField(
            label="Новый пароль",
            width=400,
            value=self.employee_data.get('password', ''),
            hint_text="Введите новый пароль (необязательно)",
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
                ft.dropdown.Option("Контроллер")
            ],
            value=self.employee_data.get('post_name', '')
        )

    def validate_data(self):
        """Валидация введенных данных"""
        errors = []

        # Проверка имени и фамилии
        if not self.first_name.value:
            errors.append("Введите имя")
        if not self.last_name.value:
            errors.append("Введите фамилию")

        # Проверка телефона (если указан)
        if self.phone.value:
            phone_pattern = r'^\d{10}$'
            if not re.match(phone_pattern, self.phone.value):
                errors.append("Некорректный формат телефона")

        # Проверка email (если указан)
        if self.email.value:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.email.value):
                errors.append("Некорректный формат email")

        # Проверка логина
        if not self.login.value:
            errors.append("Введите логин")

        # Проверка пароля (если указан)
        if self.password.value and len(self.password.value) < 6:
            errors.append("Пароль должен быть не короче 6 символов")

        # Проверка должности
        if not self.post.value:
            errors.append("Выберите должность")

        return errors

    def save_employee(self, e):
        """Обновление сотрудника"""
        errors = self.validate_data()

        if errors:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("\n".join(errors), color=ft.colors.RED),
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        try:
            # Подготовка данных для обновления
            update_data = {
                "id": self.employee_id,
                "first_name": self.first_name.value,
                "last_name": self.last_name.value,
                "patronimyc": self.patronymic.value or "",
                "phone_number": f"+7{self.phone.value}" if self.phone.value else "",
                "email": self.email.value or "",
                "login": self.login.value,
                "password": self.password.value or "",
                "post": self.post.value
            }

            # Добавляем пароль только если он указан
            if self.password.value:
                update_data["password"] = self.password.value

            # Вызов метода обновления из модуля модификации
            result = modification_server.send_employee_data(update_data)

            if result:
                # Успешное обновление
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Сотрудник успешно обновлен", color=ft.colors.GREEN),
                    duration=3000
                )
                self.page.snack_bar.open = True
                self.close_dialog()
            else:
                # Ошибка обновления
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Ошибка при обновлении сотрудника", color=ft.colors.RED),
                    duration=3000
                )
                self.page.snack_bar.open = True

        except Exception as ex:
            # Системная ошибка
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Ошибка: {str(ex)}", color=ft.colors.RED),
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()

    def close_dialog(self, e=None):
        """Закрытие диалога"""
        self.dialog.open = False
        self.page.update()

    def _setup_dialog(self):
        """Настройка диалогового окна"""
        if not self.employee_data:
            return

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Обновление сотрудника",
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
                        color=ft.colors.BLUE_900
                    )
                ),
                ft.FilledButton(
                    "Обновить",
                    on_click=self.save_employee,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.BLUE_600
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=10),
            bgcolor=ft.colors.BLUE_50,
            surface_tint_color=ft.colors.BLUE_50,
            shadow_color=ft.colors.BLUE_200,
            elevation=5
        )

    def open(self):
        """Открытие диалога"""
        if not self.employee_data:
            show_snack_bar(self.page, "Не удалось загрузить данные сотрудника")
            return

        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()
        self.page.open(self.dialog)

