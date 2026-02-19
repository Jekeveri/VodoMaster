import flet as ft


class FurtherDetailsTaskDialog:
    def __init__(self, page, task_data=None):
        self.page = page
        self.task_data = task_data

        # Цветовая схема
        self.colors = {
            'primary': ft.colors.BLUE_600,
            'secondary': ft.colors.BLUE_200,
            'background': ft.colors.BLUE_50,
            'text': ft.colors.BLUE_GREY_900,
        }

        # Создание полей только для чтения
        def readonly_textfield(label, expand=True, value='', min_lines=1, max_lines=1, multiline=False):
            return ft.TextField(
                label=label,
                value=value,
                expand=expand,
                read_only=True,  # Запрет редактирования
                min_lines=min_lines,
                max_lines=max_lines,
                multiline=multiline,
                border_color=self.colors['primary'],
                focused_border_color=self.colors['secondary'],
                label_style=ft.TextStyle(color=self.colors['text']),
                text_style=ft.TextStyle(color=self.colors['text']),
            )

        # Личные данные
        self.applicant_name = readonly_textfield("ФИО обратившегося")
        self.phone_number = readonly_textfield("Телефон")
        self.personal_account = readonly_textfield("Лицевой счет")

        # Адресные данные
        self.district = readonly_textfield("Район")
        self.street = readonly_textfield("Улица")
        self.dom = readonly_textfield("Дом")
        self.apartment = readonly_textfield("Квартира")
        self.hamlet = readonly_textfield("Поселок")

        # Детали задачи
        self.purpose = readonly_textfield("Цель задания", multiline=True)
        self.task_date = readonly_textfield("Дата начала")
        self.end_task_date = readonly_textfield("Дата окончания")
        self.task_status = readonly_textfield("Статус задачи")
        self.remark = readonly_textfield("Примечание", multiline=True)

        # Заполнение данными
        if task_data:
            self._fill_task_data(task_data)

        # Modify the _create_dialog method to be a method, not a function
        self.dialog = self._create_dialog()

    def _fill_task_data(self, task_data):
        """
        Заполнение полей данными задачи
        """
        print("Заполнение данных:", task_data)  # Отладочная печать

        # Личные данные
        self.applicant_name.value = task_data[1] or ''  # customer_name
        self.phone_number.value = task_data[14] or ''  # phone
        self.personal_account.value = task_data[15] or ''  # personal_account

        # Адресные данные
        self.district.value = task_data[4] or ''  # district
        self.street.value = task_data[5] or ''  # street
        self.dom.value = task_data[7] or ''  # dom
        self.apartment.value = task_data[8] or ''  # apartment
        self.hamlet.value = task_data[6] or ''  # hamlet

        # Детали задачи
        self.purpose.value = task_data[19] or ''  # purpose
        self.task_date.value = task_data[16] or ''  # date

        def is_valid_date(value):
            """
            Проверка, является ли значение корректной датой
            """
            if not value:
                return False

            # Проверяем, что это строка и похожа на дату
            if not isinstance(value, str):
                return False

            # Проверяем формат даты YYYY-MM-DD
            try:
                from datetime import datetime
                datetime.strptime(value, '%Y-%m-%d')
                return True
            except (ValueError, TypeError):
                return False

        # Находим первый элемент, который является корректной датой
        # Безопасная версия с проверкой длины
        valid_dates = [date for date in
                       (task_data[22] if len(task_data) > 22 else None,
                        task_data[21] if len(task_data) > 21 else None)
                       if is_valid_date(date)]

        self.end_task_date.value = valid_dates[0] if valid_dates else ''

        self.task_status.value = task_data[18] or ''  # status
        self.remark.value = task_data[17] or ''  # remark

    def _create_dialog(self):
        """
        Создание диалогового окна с подробностями задачи
        """

        def styled_header(text):
            return ft.Text(
                text,
                size=16,
                weight=ft.FontWeight.BOLD,
                color=self.colors['primary']
            )

        dialog_content = ft.Column([
            ft.Text("Редактирование задачи", size=24, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
            ft.Divider(color=self.colors['secondary'], thickness=2),

            styled_header("Личные данные"),
            ft.Row([self.applicant_name, self.phone_number, self.personal_account]),

            styled_header("Адрес"),
            ft.Row([self.district, self.street, self.dom]),
            ft.Row([self.apartment, self.hamlet]),

            styled_header("Статус задачи"),
            ft.Row([self.task_status]),

            styled_header("Детали задачи"),
            ft.Column([
                ft.Row([self.purpose], spacing=5),
                ft.Row([
                    ft.Row([
                        self.task_date,
                    ],
                        expand=True
                    ),
                    ft.Row([
                        self.end_task_date,
                    ],
                        expand=True
                    ),
                ]),
            ]),

            styled_header("Примечания"),
            self.remark
        ], width=800, spacing=20)

        dialog = ft.AlertDialog(
            modal=True,
            content=ft.Container(
                content=ft.ListView(
                    controls=[dialog_content],
                    expand=True,
                    spacing=10,
                    auto_scroll=True
                ),
                width=800,
                height=800,
                bgcolor=self.colors['background'],
                border_radius=10,
                padding=20,
            ),
            actions=[
                ft.TextButton(
                    "Закрыть",
                    on_click=self.close_dialog,
                    style=ft.ButtonStyle(
                        bgcolor=self.colors['primary'],
                        color=ft.colors.WHITE
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=self.colors['background']
        )

        return dialog

    def open(self):
        """
        Открытие диалогового окна с подробностями задачи
        """
        # Добавление диалога в overlay страницы, если его там нет
        if self.dialog not in self.page.overlay:
            self.page.overlay.append(self.dialog)

        # Открытие диалога
        self.dialog.open = True
        self.page.update()

    def close_dialog(self, e=None):
        self.dialog.open = False
        self.page.update()
