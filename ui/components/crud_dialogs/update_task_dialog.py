import datetime

import flet as ft

from src.database.admin.modification_server import send_task_data
from src.ui.components.crud_dialogs.create_task_dialog import CreateTaskDialog
from src.utils.show_snack_bar import show_snack_bar


class UpdateTaskDialog(CreateTaskDialog):
    def __init__(self, page, task_data=None):
        # Store the page first
        self.page = page

        # Store the original task data and task ID first
        self.original_task_data = task_data
        self.task_id = task_data[0] if task_data else None

        # Create color scheme
        self.colors = {
            'primary': ft.colors.BLUE_600,
            'secondary': ft.colors.BLUE_200,
            'background': ft.colors.BLUE_50,
            'text': ft.colors.BLUE_GREY_900,
        }

        # Styling function for text fields
        def styled_textfield(label, expand=True, multiline=False, min_lines=1, max_lines=1, mandatory=False):
            return ft.TextField(
                label=label,
                expand=expand,
                multiline=multiline,
                min_lines=min_lines,
                max_lines=max_lines,
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

        # Date icon
        self.date_icon = ft.IconButton(
            icon=ft.icons.CALENDAR_TODAY,
            on_click=self._show_date_picker,
            icon_color=self.colors['primary']
        )

        # Remark
        self.remark = styled_textfield("Примечание", multiline=True, min_lines=2, max_lines=4)

        # Create date picker
        self.date_picker = ft.DatePicker(
            first_date=datetime.datetime.now(),
            last_date=datetime.datetime.now().replace(year=datetime.datetime.now().year + 1),
            on_change=self._on_date_change,
            date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR,
            date_picker_mode=ft.DatePickerMode.DAY
        )

        # Add date picker to page overlay
        self.page.overlay.append(self.date_picker)

        # Create an additional date picker for task end date
        self.end_date_picker = ft.DatePicker(
            first_date=datetime.datetime.now(),
            last_date=datetime.datetime.now().replace(year=datetime.datetime.now().year + 1),
            on_change=self._on_end_date_change,
            date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR,
            date_picker_mode=ft.DatePickerMode.DAY
        )

        # Add end date picker to page overlay
        self.page.overlay.append(self.end_date_picker)

        # Create end date field and icon
        self.end_task_date = styled_textfield("Дата окончания задачи", expand=False)
        self.end_date_icon = ft.IconButton(
            icon=ft.icons.CALENDAR_TODAY,
            on_click=self._show_end_date_picker,
            icon_color=self.colors['primary']
        )

        self.task_status = ft.Dropdown(
            label="Статус задачи",
            options=[
                ft.dropdown.Option("в исполнении"),
                ft.dropdown.Option("не выполнен"),
                ft.dropdown.Option("выполнен")
            ],
            value="в исполнении",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary']
        )
        # Call parent constructor AFTER creating all fields
        super().__init__(page)

        # Modify the _create_dialog method to be a method, not a function
        self.dialog = self._create_dialog()

        # If task data is provided, pre-fill the fields
        if task_data:
            self.pre_fill_task_data(task_data)

        self.page.update()

    def pre_fill_task_data(self, task_data):
        """
        Pre-fill dialog fields with existing task data
        Follows the order of task_data tuple from the database query
        """
        # Personal Information
        self.task_id = task_data[0]
        self.applicant_name.value = task_data[1] or ''  # customer_name
        self.phone_number.value = task_data[14] or ''  # phone
        self.personal_account.value = task_data[15] or ''  # personal_account

        # Address Information
        self.district.value = task_data[4] or ''  # district
        self.street.value = task_data[5] or ''  # street
        self.dom.value = task_data[7] or ''  # dom
        self.apartment.value = task_data[8] or ''  # apartment
        self.hamlet.value = task_data[6] or ''  # hamlet

        # Task Details
        self.purpose.value = task_data[19] or ''  # purpose

        # Start Date
        if task_data[16]:
            self.task_date.value = task_data[16]  # date

        # Remark
        self.remark.value = task_data[17] or ''  # remark

        # Добавляем статус задачи
        self.task_status.value = task_data[18] if len(task_data) > 21 else "в исполнении"

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
        self.page.update()

    def _show_end_date_picker(self, e):
        if self.end_date_picker not in self.page.overlay:
            self.page.overlay.append(self.end_date_picker)
            self.page.update()

        self.end_date_picker.cancel_text = "Отмена"
        self.end_date_picker.confirm_text = "Выбрать"
        self.end_date_picker.help_text = "Выберите дату окончания"

        self.end_date_picker.pick_date()

    def _on_end_date_change(self, e):
        if self.end_date_picker.value:
            selected_date = self.end_date_picker.value
            machine_date = selected_date.strftime('%Y-%m-%d')
            self.end_task_date.value = machine_date
            self.page.update()

    def _calculate_end_date(self, start_date=None):
        if start_date is None:
            start_date = datetime.date.today()

        end_date = start_date + datetime.timedelta(days=15)
        return end_date.strftime('%Y-%m-%d')

    def _create_dialog(self):
        # Use self as the context for method calls
        def styled_header(text, mandatory=False):
            header_children = [
                ft.Text(text, size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary'])
            ]

            if mandatory:
                header_children.append(
                    ft.Text("*", color=ft.colors.RED, size=16)
                )

            return ft.Row(
                controls=header_children,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )

        # Modify the dialog content to include end date
        dialog_content = ft.Column([
            ft.Text("Редактирование задачи", size=24, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
            ft.Divider(color=self.colors['secondary'], thickness=2),

            styled_header("Личные данные"),
            ft.Row([self.applicant_name, self.phone_number, self.personal_account]),

            styled_header("Адрес", mandatory=True),
            ft.Row([self.district, self.street, self.dom]),
            ft.Row([self.apartment, self.hamlet]),

            styled_header("Статус задачи"),
            ft.Row([self.task_status]),

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

        # Create dialog with updated content and actions
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
                height=830,
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
                    "Обновить",
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

    def submit_task(self, e=None):
        """
        Проверка и обновление задачи с предупреждением
        """
        # Проверка обязательных полей
        if not self.purpose.value:
            show_snack_bar(self.page, "Заполните цель задания")
            return

        # Создание диалога подтверждения
        def confirm_update(e):
            confirm_dialog.open = False
            self.page.update()

            # Логика обновления задачи
            try:
                # Здесь ваш существующий код обновления задачи
                mandatory_address_fields = [
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
                        content=ft.Text("Пожалуйста, заполните все обязательные поля"),
                        bgcolor=ft.colors.RED_600
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    return

                # Determine the type based on hamlet
                type_of_property = 'ЧС' if self.hamlet.value and self.hamlet.value.strip() else 'МКД'

                task_data = {
                    'id': self.task_id,  # Use the stored task ID
                    'fio_customer': self.applicant_name.value,
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
                    'date_end': self.end_task_date.value or self._calculate_end_date(),
                    'remark': self.remark.value or '',
                    'status': self.task_status.value,  # Default status
                    'purpose': self.purpose.value,
                }

                # Call submit callback (which should handle update logic)
                self.on_submit_callback(task_data)

                # Close dialog
                self.close_dialog()

            except Exception as ex:
                show_snack_bar(self.page, f"Ошибка при обновлении: {str(ex)}")

        def cancel_update(e):
            confirm_dialog.open = False
            self.page.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Обновление задачи",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLUE_600
            ),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.INFO_ROUNDED, color=ft.colors.BLUE_600, size=48),
                    ft.Text(
                        "Вы действительно хотите обновить задачу?",
                        size=16,
                        color=ft.colors.GREY_800
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                ft.Text(
                    "Текущие данные будут заменены новыми.",
                    color=ft.colors.BLUE_600,
                    italic=True,
                    size=14
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, height=150),
            actions=[
                ft.TextButton(
                    "Отмена",
                    on_click=cancel_update,
                    style=ft.ButtonStyle(color=ft.colors.GREY_700)
                ),
                ft.FilledButton(
                    "Обновить",
                    on_click=confirm_update,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.BLUE_600,
                        color=ft.colors.WHITE
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10)
        )

        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    def _default_submit_handler(self, task_data):
        try:
            # This should be replaced with an update task function
            send_task_data(task_data)

            # Show success snackbar
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Задача успешно обновлена"),
                bgcolor=self.colors['primary']
            )
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as e:
            # Show error snackbar
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Ошибка при обновлении задачи: {str(e)}"),
                bgcolor=ft.colors.RED_600
            )
            self.page.snack_bar.open = True
            self.page.update()
