import datetime

import flet as ft

from src.database.admin.modification_server import send_task_data


class CreateTaskDialog:
    def __init__(self, page, on_submit_callback=None):
        self.page = page
        self.on_submit_callback = on_submit_callback or self._default_submit_handler

        # Define color scheme
        self.colors = {
            'primary': ft.colors.BLUE_600,
            'secondary': ft.colors.BLUE_200,
            'background': ft.colors.BLUE_50,
            'text': ft.colors.BLUE_GREY_900,
        }

        # Create date picker
        self.date_picker = ft.DatePicker(
            first_date=datetime.datetime.now(),
            last_date=datetime.datetime.now().replace(year=datetime.datetime.now().year + 1),
            on_change=self._on_date_change,
            date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR,
            date_picker_mode=ft.DatePickerMode.DAY,
            cancel_text="Назад",
            confirm_text="Выбрать",
            help_text="Выберите дату"
        )

        self.end_date_picker = ft.DatePicker(
            first_date=datetime.datetime.now(),
            last_date=datetime.datetime.now().replace(year=datetime.datetime.now().year + 1),
            on_change=self._on_end_date_change,
            date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR,
            date_picker_mode=ft.DatePickerMode.DAY,
            cancel_text="Назад",
            confirm_text="Выбрать",
            help_text="Выберите дату"
        )

        # Add end date picker to page overlay
        self.page.overlay.append(self.end_date_picker)

        self.page.overlay.append(self.date_picker)
        self.page.update()

        self.dialog = self._create_dialog()

    def _create_dialog(self):
        # Styling function for text fields
        def styled_textfield(label, expand=True, multiline=False, min_lines=1, max_lines=1, mandatory=False):
            return ft.TextField(
                label=label,
                expand=expand,
                multiline=multiline,
                min_lines=min_lines,
                max_lines=max_lines,
                bgcolor=ft.colors.WHITE,
                border_color=self.colors['primary'],
                focused_border_color=self.colors['secondary'],
                label_style=ft.TextStyle(color=self.colors['text']),
                error_style=ft.TextStyle(color=ft.colors.RED),
                # Add validation for mandatory fields
                on_change=lambda e: self._validate_mandatory_field(e.control) if mandatory else None
            )

        # Personal Information
        self.applicant_name = styled_textfield("ФИО обратившегося", mandatory=True)
        self.phone_number = styled_textfield("Телефон")
        self.personal_account = styled_textfield("Лицевой счет", mandatory=True)

        # Address Information
        self.district = styled_textfield("Район")
        self.street = styled_textfield("Улица", mandatory=True)
        self.dom = styled_textfield("Дом", mandatory=True)
        self.apartment = styled_textfield("Квартира")
        self.hamlet = styled_textfield("Поселок")

        # Task Details
        self.purpose = styled_textfield("Цель задания", multiline=True, min_lines=1, max_lines=4, mandatory=True)
        today = datetime.date.today()
        self.task_date = styled_textfield("Дата задачи", expand=False)
        self.task_date.value = today.strftime('%Y-%m-%d')
        self.date_icon = ft.IconButton(
            icon=ft.icons.CALENDAR_TODAY,
            on_click=lambda _: self.page.open(self.date_picker),
            icon_color=self.colors['primary']
        )
        self.remark = styled_textfield("Примечание", multiline=True, min_lines=2, max_lines=4)

        self.end_task_date = styled_textfield("Дата окончания задачи", expand=False)
        self.end_date_icon = ft.IconButton(
            icon=ft.icons.CALENDAR_TODAY,
            on_click=lambda _: self.page.open(self.end_date_picker),
            icon_color=self.colors['primary']
        )

        # Styled Text for section headers
        def styled_header(text, mandatory=False):
            header_children = [
                ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary'])
            ]

            if mandatory:
                # Add a red asterisk for mandatory sections
                header_children.append(
                    ft.Text("*", color=ft.colors.RED, size=16)
                )

            return ft.Row(
                controls=header_children,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )

        # Dialog Content
        dialog_content = ft.Column([
            ft.Text("Создание новой задачи", size=24, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
            ft.Divider(color=self.colors['secondary'], thickness=2),

            styled_header("Личные данные"),
            ft.Row([self.applicant_name, self.phone_number, self.personal_account]),

            styled_header("Адрес", mandatory=True),
            ft.Row([self.district, self.street, self.dom]),
            ft.Row([self.apartment, self.hamlet]),

            styled_header("Детали задачи", mandatory=True),
            ft.Column([
                ft.Row([self.purpose], spacing=5),
                ft.Row([
                    ft.Row([
                        self.task_date,
                        self.date_icon,
                    ],
                        expand=True
                    ),
                    ft.Row([
                        self.end_task_date,
                        self.end_date_icon,
                    ],
                        expand=True
                    ),
                ]),
            ]),

            styled_header("Примечания"),
            self.remark
        ], width=800, spacing=20)

        # Create dialog
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
                height=710,
                bgcolor=self.colors['background'],
                border_radius=10,
                padding=20,
            ),
            actions=[
                ft.TextButton(
                    "Отмена",
                    on_click=self.close_dialog,
                    style=ft.ButtonStyle(color=self.colors['text'])
                ),
                ft.ElevatedButton(
                    "Создать",
                    on_click=self.submit_task,
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

    def _validate_mandatory_field(self, field):
        if not field.value or field.value.strip() == '':
            field.error_text = "Это поле обязательно"
            field.border_color = ft.colors.RED
            field.focused_border_color = ft.colors.RED
        else:
            field.error_text = None
            field.border_color = self.colors['primary']
            field.focused_border_color = self.colors['secondary']
        self.page.update()

    def _show_date_picker(self, e):
        if self.date_picker not in self.page.overlay:
            self.page.overlay.append(self.date_picker)
            self.page.update()

        self.page.open(self.date_picker)
        self.page.overlay.append(self.date_picker)

    def _on_end_date_change(self, e):
        """
        Обработчик изменения даты окончания задачи
        """
        if self.end_date_picker.value:
            selected_date = self.end_date_picker.value
            machine_date = selected_date.strftime('%Y-%m-%d')
            self.end_task_date.value = machine_date
            self.page.update()

    def _on_date_change(self, e):
        if self.date_picker.value:
            selected_date = self.date_picker.value

            machine_date = selected_date.strftime('%Y-%m-%d')

            self.task_date.value = machine_date
            self.page.update()

    def _calculate_end_date(self, start_date=None):
        if start_date is None:
            start_date = datetime.date.today()

        end_date = start_date + datetime.timedelta(days=15)
        return end_date.strftime('%Y-%m-%d')

    def submit_task(self, e=None):
        # Validate mandatory address fields
        mandatory_address_fields = [
            self.district,
            self.street,
            self.dom,
            self.purpose
        ]

        # Check if any mandatory field is empty
        has_empty_fields = any(
            not field.value or field.value.strip() == ''
            for field in mandatory_address_fields
        )

        if has_empty_fields:
            # Highlight empty mandatory fields
            for field in mandatory_address_fields:
                self._validate_mandatory_field(field)

            # Show an error snackbar
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Пожалуйста, заполните все обязательные поля адреса"),
                bgcolor=ft.colors.RED_600
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        type_of_property = 'ЧС' if self.hamlet.value and self.hamlet.value.strip() else 'МКД'

        task_data = {
            'fio_requestor': self.applicant_name.value,
            'city': 'Магнитогорск',  # Default city as specified
            'district': self.district.value,
            'street': self.street.value,
            'type': type_of_property,
            'dom': self.dom.value,
            'apartment': self.apartment.value or '',
            'entrence': '',
            'hamlet': self.hamlet.value or '',
            'phone_number': self.phone_number.value or '',
            'personal_account': self.personal_account.value,
            'date': self.task_date.value or datetime.date.today().strftime('%Y-%m-%d'),
            'remark': self.remark.value or '',
            'status': 'не выполнен',  # Default status
            'date_end': self.end_task_date.value or self._calculate_end_date(),
            'purpose': self.purpose.value,
        }

        self.on_submit_callback(task_data)
        self.close_dialog()

    def _default_submit_handler(self, task_data):
        try:
            send_task_data(task_data)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Задача успешно создана"),
                bgcolor=self.colors['primary']
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Ошибка при создании задачи: {str(e)}"),
                bgcolor=ft.colors.RED_600
            )
            self.page.snack_bar.open = True
            self.page.update()

    def close_dialog(self, e=None):
        self.page.close(self.dialog)
        self.page.update()

    def open(self):
        self.page.open(self.dialog)
        self.page.update()
