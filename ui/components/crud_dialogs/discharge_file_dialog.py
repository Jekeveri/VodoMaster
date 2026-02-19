import os
import flet as ft
from datetime import datetime, date
from typing import Optional
import dbf
import traceback
import asyncio
from src.database.admin.select_server import get_completed_tasks_export


class ExportTasksDialog(ft.Row):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.tasks_data = None
        self.PRIMARY_BLUE = "#2196F3"
        self.LIGHT_BLUE = "#E3F2FD"

        # Текстовые поля для отображения дат
        self.start_date_field = ft.TextField(
            label="Начальная дата",
            read_only=True,

            value="",
        )

        self.end_date_field = ft.TextField(
            label="Конечная дата",
            read_only=True,
            value="",
        )

        # DatePicker для выбора дат
        self.start_date_picker = ft.DatePicker(
            value=None,
            first_date=datetime(2023, 1, 1),
            last_date=datetime(2030, 12, 31),
            on_change=self._on_date_change,
        )

        self.end_date_picker = ft.DatePicker(
            value=None,
            first_date=datetime(2023, 1, 1),
            last_date=datetime(2030, 12, 31),
            on_change=self._on_date_change,
        )

        # FilePicker для сохранения файла
        self.file_picker = ft.FilePicker(on_result=self.file_picker_handler)

        # Добавляем все пикеры в overlay страницы
        self.page.overlay.extend([
            self.start_date_picker,
            self.end_date_picker,
            self.file_picker
        ])

        # Кнопки для открытия DatePicker
        self.start_date_btn = ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self._show_date_picker(self.start_date_picker),
            icon_color=self.PRIMARY_BLUE
        )

        self.end_date_btn = ft.IconButton(
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self._show_date_picker(self.end_date_picker),
            icon_color=self.PRIMARY_BLUE
        )

        # Кнопка выгрузки
        self.export_btn = ft.ElevatedButton(
            "Выгрузить в DBF",
            icon=ft.icons.DOWNLOAD,
            icon_color=ft.colors.WHITE,
            style=ft.ButtonStyle(
                bgcolor=self.PRIMARY_BLUE,
                color=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=self.export_to_dbf,
            disabled=False
        )

        # Кнопка сохранения
        self.save_btn = ft.ElevatedButton(
            "Сохранить",
            icon=ft.icons.SAVE,
            icon_color=ft.colors.WHITE,
            style=ft.ButtonStyle(
                bgcolor=self.PRIMARY_BLUE,
                color=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=self.save_to_file,
            disabled=True
        )

        # Индикатор загрузки
        self.progress_ring = ft.ProgressRing(visible=False, width=20, height=20)

        # Отображение статуса
        self.status_message = ft.Text("", color=self.PRIMARY_BLUE)
        self.task_count_display = ft.Container(
            content=ft.Column([
                ft.Text("Количество задач",
                        color=self.PRIMARY_BLUE,
                        weight=ft.FontWeight.BOLD,
                        size=16),
                ft.Text("0",
                        color=self.PRIMARY_BLUE,
                        size=32,
                        weight=ft.FontWeight.BOLD),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            width=200,
            height=120,
            border_radius=15,
            border=ft.border.all(2, self.PRIMARY_BLUE),
            padding=20,
            alignment=ft.alignment.center,
            bgcolor=self.LIGHT_BLUE
        )

        self.dialog = self.build()

    def build(self):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Выгрузка задач в файл"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Даты опциональны. Если не указаны, будут выгружены все задачи.",
                            color=self.PRIMARY_BLUE, size=12, italic=True),
                    ft.Row([
                        ft.Row([
                            self.start_date_field,
                            self.start_date_btn,
                        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                        ft.Row([
                            self.end_date_field,
                            self.end_date_btn,
                        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                    ]),
                    ft.Divider(color=self.PRIMARY_BLUE),
                    ft.Row([self.export_btn, self.progress_ring],
                           alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(self.task_count_display,
                                 alignment=ft.alignment.center, width=600),
                    ft.Row([self.save_btn],
                           alignment=ft.MainAxisAlignment.CENTER),
                    self.status_message
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                padding=20,
                bgcolor=self.LIGHT_BLUE,
                border_radius=15,
                height=450,
                width=750
            ),
            actions=[
                ft.TextButton("Закрыть", on_click=self.close_dialog,
                              style=ft.ButtonStyle(
                                  bgcolor=ft.colors.BLUE_600,
                                  color=ft.colors.WHITE
                              ))
            ],
            bgcolor=ft.colors.BLUE_50,
            surface_tint_color=ft.colors.BLUE_50,
            elevation=5
        )

        return dialog

    def _on_date_change(self, e):
        # Закрываем DatePicker после выбора даты
        e.control.open = False

        # Определяем, какой пикер изменился и обновляем соответствующее поле
        if e.control == self.start_date_picker:
            if self.start_date_picker.value:
                self.start_date_field.value = self.start_date_picker.value.strftime("%d.%m.%Y")
            else:
                self.start_date_field.value = ""
        else:
            if self.end_date_picker.value:
                self.end_date_field.value = self.end_date_picker.value.strftime("%d.%m.%Y")
            else:
                self.end_date_field.value = ""

        self.page.update()

    def _show_date_picker(self, date_picker):
        date_picker.open = True
        self.page.update()

    async def export_to_dbf(self, e):
        try:
            self.export_btn.disabled = True
            self.progress_ring.visible = True
            self.status_message.value = "Получение данных..."
            self.status_message.color = self.PRIMARY_BLUE
            self.page.update()

            # Получаем даты из пикеров
            start_date = self.start_date_picker.value
            end_date = self.end_date_picker.value

            # Проверяем, что если обе даты выбраны, то конечная не меньше начальной
            if start_date and end_date and start_date > end_date:
                self.status_message.value = "Конечная дата не может быть меньше начальной"
                self.status_message.color = ft.colors.RED
                self.progress_ring.visible = False
                self.export_btn.disabled = False
                self.page.update()
                return

            # Используем asyncio.to_thread для запуска синхронной функции в отдельном потоке
            tasks = await asyncio.to_thread(
                get_completed_tasks_export,
                start_date.date() if start_date else None,
                end_date.date() if end_date else None
            )

            if not tasks:
                self.status_message.value = "Нет данных для выбранного диапазона дат"
                self.status_message.color = ft.colors.ORANGE
                self.progress_ring.visible = False
                self.export_btn.disabled = False
                return

            self.tasks_data = tasks

            # Обновляем счетчик задач
            self.task_count_display.content.controls[1].value = str(len(tasks))
            self.status_message.value = "Данные получены. Нажмите 'Сохранить' для выбора места сохранения."
            self.status_message.color = self.PRIMARY_BLUE
            self.save_btn.disabled = False

        except Exception as ex:
            # Получаем полную информацию об ошибке
            error_traceback = traceback.format_exc()
            error_msg = f"Ошибка: {str(ex)}"

            # Логируем полную трассировку для отладки
            print(f"Ошибка в export_to_dbf: {error_traceback}")

            self.status_message.value = error_msg
            self.status_message.color = ft.colors.RED
        finally:
            self.progress_ring.visible = False
            self.export_btn.disabled = False
            self.page.update()

    def save_to_file(self, e):
        if self.tasks_data:
            self.file_picker.save_file(
                allowed_extensions=["dbf"],
                file_name=f"tasks_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dbf"
            )
        else:
            self.status_message.value = "Сначала необходимо выгрузить данные"
            self.status_message.color = ft.colors.RED
            self.page.update()

    def file_picker_handler(self, e: ft.FilePickerResultEvent):
        if e.path and self.tasks_data:
            try:
                file_path = e.path
                if not file_path.endswith('.dbf'):
                    file_path += '.dbf'

                self.convert_to_dbf(self.tasks_data, file_path)
                self.status_message.value = f"Данные успешно сохранены в файл: {os.path.basename(file_path)}"
                self.status_message.color = self.PRIMARY_BLUE
            except Exception as ex:
                error_traceback = traceback.format_exc()
                print(f"Ошибка при сохранении: {error_traceback}")

                self.status_message.value = f"Ошибка при сохранении: {str(ex)}"
                self.status_message.color = ft.colors.RED
        else:
            self.status_message.value = "Сохранение отменено"
            self.status_message.color = ft.colors.ORANGE

        self.page.update()

    def convert_to_dbf(self, tasks, file_path):
        try:
            # Определяем структуру DBF файла в строковом формате
            table_definition = """
                ID_TASK C(20);
                DATE D;
                HAMLET C(50);
                LS C(20);
                FIO C(100);
                STREET C(50);
                DOM C(10);
                APARTMENT C(10);
                SALDO C(20);
                PRICHINA C(100);
                PRIMECHANI C(100);
                TELEFON C(20);
                PROPISANO C(10);
                NORMATIV C(10);
                AREA C(10);
                MARKA C(50);
                ZAVOD_N C(50);
                NOMER_PL C(50);
                NOMER_FI C(50);
                DATAPOVE D;
                DATALIKV D;
                MESTO_RA C(50);
                TIP_USLU C(50);
                TIP_POKA C(50);
                KONR_POK C(20);
                DATAKONR D;
                KOL_MES_ N(5,0)
            """

            # Создаем DBF таблицу
            table = dbf.Table(file_path, table_definition, codepage='cp866')
            table.open(mode=dbf.READ_WRITE)

            # Создаем записи для DBF
            for task in tasks:
                # Для каждого счетчика в задаче создаем отдельную запись
                for meter in task.get('meters', []):
                    # Подготавливаем данные для записи
                    record_data = {
                        'ID_TASK': str(task.get('id_task', '')),
                        'DATE': self.parse_date(task.get('date', '')),
                        'HAMLET': task.get('address', {}).get('hamlet', ''),
                        'LS': str(task.get('customers', {}).get('personal_account', '')),
                        'FIO': task.get('customers', {}).get('fio_customers', ''),
                        'STREET': task.get('address', {}).get('street', ''),
                        'DOM': task.get('address', {}).get('dom', ''),
                        'APARTMENT': task.get('address', {}).get('apartment', ''),
                        'SALDO': str(task.get('customers', {}).get('saldo', '')),
                        'PRICHINA': task.get('purpose', ''),
                        'PRIMECHANI': task.get('remark', ''),
                        'TELEFON': task.get('customers', {}).get('phone_number', ''),
                        'PROPISANO': task.get('address', {}).get('registered_residing', ''),
                        'NORMATIV': str(task.get('address', {}).get('standards', '')),
                        'AREA': str(task.get('address', {}).get('area', '')),
                        'MARKA': meter.get('marka', ''),
                        'ZAVOD_N': meter.get('meter_number', ''),
                        'NOMER_PL': meter.get('seal_number', ''),
                        'NOMER_FI': str(meter.get('seal_filter', '')),
                        'DATAPOVE': self.parse_date(meter.get('date_next_verification', '')),
                        'DATALIKV': self.parse_date(meter.get('date_meter_end', '')),
                        'MESTO_RA': meter.get('location', ''),
                        'TIP_USLU': meter.get('type_service', ''),
                        'TIP_POKA': meter.get('meter_reading', {}).get('type_reading', ''),
                        'KONR_POK': str(meter.get('meter_reading', {}).get('reading_value', '')),
                        'DATAKONR': self.parse_date(meter.get('meter_reading', {}).get('reading_date', '')),
                        'KOL_MES_': meter.get('month_not_reading', 0),
                    }

                    # Заменяем None на пустые значения или 0 для числовых полей
                    for key, value in record_data.items():
                        if value is None:
                            if key == 'KOL_MES_':
                                record_data[key] = 0
                            else:
                                record_data[key] = ''

                    # Добавляем запись в таблицу
                    table.append(record_data)

            table.close()

        except Exception as ex:
            error_traceback = traceback.format_exc()
            print(f"Ошибка при создании DBF: {error_traceback}")
            raise

    def parse_date(self, date_value):
        """Преобразует различные форматы даты в объект datetime.date"""
        if not date_value:
            return None

        try:
            # Если это уже объект date/datetime
            if isinstance(date_value, (date, datetime)):
                return date_value.date() if isinstance(date_value, datetime) else date_value

            # Если это строка, пробуем разные форматы
            if isinstance(date_value, str):
                for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%Y/%m/%d'):
                    try:
                        return datetime.strptime(date_value, fmt).date()
                    except ValueError:
                        continue
        except Exception:
            return None

        return None

    def handle_error(self, message: str):
        self.status_message.value = message
        self.status_message.color = ft.colors.RED
        self.export_btn.disabled = False
        self.page.update()

    def show_message(self, message: str, error: bool = False):
        self.status_message.value = message
        self.status_message.color = ft.colors.RED if error else self.PRIMARY_BLUE
        self.page.update()

    def close_dialog(self, e=None):
        self.page.close(self.dialog)
        self.page.update()

    def open(self):
        # Убедимся, что все пикеры добавлены в overlay перед открытием диалога
        if self.start_date_picker not in self.page.overlay:
            self.page.overlay.append(self.start_date_picker)
        if self.end_date_picker not in self.page.overlay:
            self.page.overlay.append(self.end_date_picker)
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)

        self.page.open(self.dialog)
        self.page.update()

    def reset_state(self):
        self.tasks_data = None
        self.export_btn.disabled = False
        self.save_btn.disabled = True
        self.start_date_field.value = ""
        self.end_date_field.value = ""
        self.start_date_picker.value = None
        self.end_date_picker.value = None
        self.task_count_display.content.controls[1].value = "0"
        self.status_message.value = ""
        self.page.update()