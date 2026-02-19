from datetime import datetime

import flet as ft

import src.database.admin.select_server as select_server


class FurtherDetailsEmployeeDialog:
    def __init__(self, page: ft.Page, employee_id):
        self.page = page
        self.employee_id = employee_id
        self.dialog = None
        self.employee_data = None
        self.tasks_data = None
        self.current_view = "info"  # Текущее отображаемое представление
        self._load_employee_data()
        self._create_dialog()
        self._setup_dialog()

    def _load_employee_data(self):
        """Загрузка данных сотрудника"""
        try:
            # Получаем детальную информацию о сотруднике
            employee_details = select_server.get_employee_details(self.employee_id)

            if not employee_details:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Не удалось загрузить данные сотрудника", color=ft.colors.RED),
                    duration=3000
                )
                self.page.snack_bar.open = True
                return

            self.employee_data = employee_details.get('employee', {})
            self.tasks_data = employee_details.get('tasks', [])

        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Ошибка загрузки данных: {str(e)}", color=ft.colors.RED),
                duration=3000
            )
            self.page.snack_bar.open = True

    def _create_employee_info_view(self):
        """Создание представления с информацией о сотруднике"""
        if not self.employee_data:
            return ft.Container()

        # Словарь для маппинга причин отсутствия
        absence_reasons = {
            '': 'Нет',
            'sick': 'Болезнь',
            'family': 'Семейные обстоятельства',
            'vacation': 'Отпуск',
            'other': 'Другое'
        }

        return ft.ListView(
            controls=[
                self._create_info_section("Основная информация", [
                    self._create_info_card("ID сотрудника", str(self.employee_data.get('id', ''))),
                    self._create_info_card("ФИО", self.employee_data.get('full_name', '')),
                    self._create_info_card("Должность", self.employee_data.get('post_name', '')),
                    self._create_info_card("Телефон", self.employee_data.get('phone_number', '')),
                    self._create_info_card("Email", self.employee_data.get('email', ''))
                ]),
                self._create_info_section("Статус отсутствия", [
                        self._create_info_card(
                            "Причина отсутствия",
                            absence_reasons.get(self.employee_data.get('reason', ''), 'Нет'
                                                )),
                        self._create_date_card(
                            "Дата начала отсутствия",
                            self.employee_data.get('start_date')
                        ),
                        self._create_date_card(
                            "Дата окончания отсутствия",
                            self.employee_data.get('end_date')
                        ),
                ])
            ],
            spacing=10,
            padding=10,
            expand=True
        )

    def _create_tasks_view(self):
        """Создание представления с задачами"""
        if not self.tasks_data:
            return ft.Container(
                content=ft.Text(
                    "У сотрудника нет задач",
                    color=ft.colors.BLACK,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=20,
                border_radius=10,
                bgcolor=ft.colors.BLUE_100
            )

        columns = [
            ft.DataColumn(ft.Text("ID", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Статус", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Дата начала", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Дата окончания", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Заказчик", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Примечание", weight=ft.FontWeight.BOLD))
        ]

        rows = []
        for task in self.tasks_data:
            rows.append(ft.DataRow([
                ft.DataCell(ft.Text(str(task.get('id', '')), color=ft.colors.BLACK)),
                ft.DataCell(ft.Text(task.get('status', ''), color=ft.colors.BLACK)),
                ft.DataCell(ft.Text(task.get('start_date', ''), color=ft.colors.BLACK)),
                ft.DataCell(ft.Text(task.get('end_date', ''), color=ft.colors.BLACK)),
                ft.DataCell(ft.Text(task.get('requestor', ''), color=ft.colors.BLACK)),
                ft.DataCell(ft.Text(task.get('remark', ''), color=ft.colors.BLACK))
            ]))

        return ft.Container(
            content=ft.DataTable(
                columns=columns,
                rows=rows,
                width=600,
                vertical_lines=ft.BorderSide(1, ft.colors.BLUE_100),
                horizontal_lines=ft.BorderSide(1, ft.colors.BLUE_100),
                border_radius=10,
                column_spacing=32,
                data_row_min_height=50,
                show_checkbox_column=False
            ),
            bgcolor=ft.colors.BLUE_100,
            border_radius=10,
            padding=10
        )

    def _create_info_section(self, title, cards):
        """Создание секции с заголовком"""
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    title,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_900
                ),
                ft.Column(cards, spacing=5)
            ], spacing=10),
            padding=10,
            border_radius=10,
            bgcolor=ft.colors.BLUE_100
        )

    def _create_info_card(self, label, value):
        """Создание карточки с информацией"""
        return ft.Container(
            content=ft.Row([
                ft.Text(f"{label}:", weight=ft.FontWeight.BOLD, width=200, color=ft.colors.BLUE_900),
                ft.Text(str(value) if value is not None else "Не указано", color=ft.colors.BLACK)
            ], spacing=10),
            padding=10,
            border_radius=5,
            border=ft.border.all(1, ft.colors.BLUE_200),
            bgcolor=ft.colors.WHITE
        )

    def _create_date_card(self, label, date_str):
        """Создание карточки с датой"""
        try:
            if date_str:
                formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
            else:
                formatted_date = "Не указано"
        except (ValueError, TypeError):
            formatted_date = "Некорректный формат даты"

        return ft.Container(
            content=ft.Row([
                ft.Text(f"{label}:", weight=ft.FontWeight.BOLD, width=200, color=ft.colors.BLUE_900),
                ft.Text(formatted_date, color=ft.colors.BLACK)
            ], spacing=10),
            padding=10,
            border_radius=5,
            border=ft.border.all(1, ft.colors.BLUE_200),
            bgcolor=ft.colors.WHITE
        )

    def _create_navigation_buttons(self):
        """Создание кнопок навигации"""
        return ft.Row(
            controls=[
                ft.ElevatedButton(
                    "Информация",
                    icon=ft.icons.PERSON,
                    on_click=lambda e: self._switch_view("info"),
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.BLUE_700 if self.current_view == "info" else ft.colors.BLUE_300,
                        color=ft.colors.WHITE
                    )
                ),
                ft.ElevatedButton(
                    "Задачи",
                    icon=ft.icons.TASK,
                    on_click=lambda e: self._switch_view("tasks"),
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.BLUE_700 if self.current_view == "tasks" else ft.colors.BLUE_300,
                        color=ft.colors.WHITE
                    )
                )
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER
        )

    def _switch_view(self, view_name):
        """Переключение между представлениями"""
        self.current_view = view_name
        self._update_content()
        self.page.update()

    def _update_content(self):
        """Обновление содержимого в зависимости от текущего представления"""
        if self.current_view == "info":
            self.content_view.content = self._create_employee_info_view()
        else:
            self.content_view.content = self._create_tasks_view()

        # Обновляем стили кнопок
        for button in self.nav_buttons.controls:
            if button.text == "Информация":
                button.style.bgcolor = ft.colors.BLUE_700 if self.current_view == "info" else ft.colors.BLUE_300
            elif button.text == "Задачи":
                button.style.bgcolor = ft.colors.BLUE_700 if self.current_view == "tasks" else ft.colors.BLUE_300

    def _create_dialog(self):
        """Создание содержимого диалога"""
        if not self.employee_data:
            return

        # Создаем кнопки навигации
        self.nav_buttons = self._create_navigation_buttons()

        # Создаем контейнер для контента
        self.content_view = ft.Container(
            content=self._create_employee_info_view(),
            padding=10,
            expand=True
        )

    def _setup_dialog(self):
        """Настройка диалогового окна"""
        if not self.employee_data:
            return

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Column([
                ft.Text(
                    "Подробная информация о сотруднике",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_900
                ),
                self.nav_buttons
            ], spacing=10),
            content=ft.Container(
                content=self.content_view,
                width=800,
                height=600,
                expand=True,
                bgcolor=ft.colors.BLUE_50
            ),
            actions=[
                ft.TextButton(
                    "Закрыть",
                    on_click=self.close_dialog,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.BLUE_600,
                        color=ft.colors.WHITE
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=10),
            surface_tint_color=ft.colors.BLUE_50,
            bgcolor=ft.colors.BLUE_50,
            elevation=5
        )

    def close_dialog(self, e=None):
        """Закрытие диалога"""
        self.dialog.open = False
        self.page.update()

    def open(self):
        """Открытие диалога"""
        if not self.employee_data:
            return

        self.page.open(self.dialog)
        self.page.dialog = self.dialog
        self.dialog.open = True
        self.page.update()