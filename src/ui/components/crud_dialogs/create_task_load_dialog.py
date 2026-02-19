import os

import flet as ft
import pandas as pd
from dbfread import DBF

from src.database.admin.modification_server import send_tasks_bulk


class AddNewTaskDialog(ft.Row):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.original_data = None
        self.transformed_data = None
        self.PRIMARY_BLUE = "#2196F3"
        self.LIGHT_BLUE = "#E3F2FD"

        self.file_picker = ft.FilePicker(on_result=self.file_picker_handler)
        self.page.overlay.append(self.file_picker)
        self.page.update()

        self.file_path_display = ft.Text(
            "Файл не выбран",
            color=self.PRIMARY_BLUE,
            weight=ft.FontWeight.BOLD
        )

        self.select_file_btn = ft.ElevatedButton(
            "Выбрать файл",
            icon=ft.icons.UPLOAD_FILE,
            icon_color=ft.colors.WHITE,
            style=ft.ButtonStyle(
                bgcolor=self.PRIMARY_BLUE,
                color=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=self.open_file_picker
        )

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

        self.transform_btn = ft.ElevatedButton(
            "Преобразовать данные",
            icon=ft.icons.TRANSFORM,
            icon_color=ft.colors.WHITE,
            style=ft.ButtonStyle(
                bgcolor=self.PRIMARY_BLUE,
                color=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=self.transform_data,
            disabled=True
        )

        self.upload_btn = ft.ElevatedButton(
            "Загрузить в базу",
            icon=ft.icons.CLOUD_UPLOAD,
            icon_color=ft.colors.WHITE,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.GREY,
                color=ft.colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10)
            ),
            on_click=self.upload_to_database,
            disabled=self.transformed_data is None
        )

        self.status_message = ft.Text("", color=self.PRIMARY_BLUE)

        self.dialog = self.build()

    def build(self):
        dialog = ft.AlertDialog(
            title=ft.Text("Загрузка задач из файла"),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([self.select_file_btn, self.file_path_display],
                           alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(color=self.PRIMARY_BLUE),
                    ft.Container(self.task_count_display,
                                 alignment=ft.alignment.center, width=600),
                    ft.Row([self.transform_btn, self.upload_btn],
                           alignment=ft.MainAxisAlignment.CENTER),
                    self.status_message
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                padding=20,
                bgcolor=self.LIGHT_BLUE,
                border_radius=15,
                height=350,
                width=600
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

    def open_file_picker(self, e):
        self.file_picker.pick_files(
            allowed_extensions=["dbf"],
            dialog_title="Выберите файл Excel"
        )

    def file_picker_handler(self, e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext != '.dbf':
                self.handle_error("Ошибка: Требуется файл DBF")
                self.reset_state()
                return

            try:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Файл не найден: {file_path}")

                self.file_path_display.value = f"Выбран файл: {file_path}"
                self.transform_btn.disabled = False
                self.upload_btn.disabled = True
                self.load_dbf_preview(file_path)

            except Exception as e:
                self.handle_error(f"Ошибка загрузки: {str(e)}")
                self.reset_state()
        else:
            self.file_path_display.value = "Файл не выбран"
            self.transform_btn.disabled = True
            self.upload_btn.disabled = True
        self.upload_btn.bgcolor = ft.colors.GREY
        self.page.update()

    def load_dbf_preview(self, file_path: str):
        try:
            try:
                dbf_table = DBF(file_path, encoding='cp866', ignore_missing_memofile=True)
            except UnicodeDecodeError:
                dbf_table = DBF(file_path, encoding='cp1251', ignore_missing_memofile=True)

            df = pd.DataFrame(iter(dbf_table))

            if df.iloc[0, 0] == "OBRASHCHEN":
                df = df.iloc[1:].reset_index(drop=True)

            self.original_data = df

            # Используем ту же логику группировки, что и в transform_data
            temp_df = df.copy()
            temp_df.iloc[:, 0] = temp_df.iloc[:, 0].replace('', pd.NA)
            temp_df.iloc[:, 3] = temp_df.iloc[:, 3].replace('', pd.NA)
            temp_df['group_key'] = temp_df.iloc[:, 0].combine_first(temp_df.iloc[:, 3])
            temp_df = temp_df.dropna(subset=['group_key'])

            # Считаем количество уникальных групп
            task_count = temp_df['group_key'].nunique()

            self.task_count_display.content.controls[1].value = str(task_count)
            self.show_message("Файл успешно загружен")

        except Exception as e:
            self.handle_error(f"Ошибка чтения DBF: {str(e)}")
            self.reset_state()

    def transform_data(self, e):
        if self.original_data is None:
            self.show_message("Сначала выберите файл", error=True)
            return

        try:
            result = []
            df = self.original_data.copy()

            df.iloc[:, 0] = df.iloc[:, 0].replace('', pd.NA)
            df.iloc[:, 3] = df.iloc[:, 3].replace('', pd.NA)

            df['group_key'] = df.iloc[:, 0].combine_first(df.iloc[:, 3])
            df = df.dropna(subset=['group_key'])

            grouped = df.groupby('group_key', dropna=True)

            for _, group in grouped:
                # if pd.isna(id_task):
                #     continue
                has_real_id = not pd.isna(group.iloc[0, 0])

                id_task_value = ""
                if has_real_id:
                    try:
                        id_task_value = str(int(float(group.iloc[0, 0])))
                    except (ValueError, TypeError):
                        id_task_value = ""

                saldo_value = ""
                if not pd.isna(group.iloc[0, 8]):
                    try:
                        saldo_str = str(group.iloc[0, 8]).replace(',', '.')
                        saldo_float = float(saldo_str)
                        saldo_value = f"{saldo_float:.2f}"
                    except (ValueError, TypeError):
                        saldo_value = ""

                entry = {
                    "id_task": id_task_value,
                    "date": str(group.iloc[0, 1]) if not pd.isna(group.iloc[0, 1]) else "",
                    "address": {
                        "hamlet": str(group.iloc[0, 2]) if not pd.isna(group.iloc[0, 2]) else "",
                        "street": str(group.iloc[0, 5]) if not pd.isna(group.iloc[0, 5]) else "",
                        "dom": str(group.iloc[0, 6]) if not pd.isna(group.iloc[0, 6]) else "",
                        "apartment": str(group.iloc[0, 7]) if not pd.isna(group.iloc[0, 7]) else "",
                        "registered_residing": str(group.iloc[0, 12]) if not pd.isna(group.iloc[0, 12]) else "",
                        "standards": str(group.iloc[0, 13]).replace(',', '.') if not pd.isna(group.iloc[0, 13]) else "",
                        "area": str(group.iloc[0, 14]).replace(',', '.') if not pd.isna(group.iloc[0, 14]) else ""
                    },
                    "customers": {
                        "personal_account": str(group.iloc[0, 3]) if not pd.isna(group.iloc[0, 3]) else "",  # LS (D)
                        "fio_customers": str(group.iloc[0, 4]) if not pd.isna(group.iloc[0, 4]) else "",  # FIO (E)
                        "phone_number": str(group.iloc[0, 11]) if not pd.isna(group.iloc[0, 11]) else "",  # TELEFON (L)
                        "saldo": saldo_value
                    },
                    "purpose": str(group.iloc[0, 9]) if not pd.isna(group.iloc[0, 9]) else "",  # PRICHINA (J)
                    "remark": str(group.iloc[0, 10]) if not pd.isna(group.iloc[0, 10]) else "",  # PRIMECHANI (K)
                    "meters": []
                }

                for _, row in group.iterrows():
                    # Обработка числовых значений с защитой от ошибок
                    month_not_reading = 0
                    if not pd.isna(row.iloc[26]):  # KOL MES NE (AA)
                        try:
                            month_not_reading = int(row.iloc[26])
                        except:
                            month_not_reading = 0

                    reading_value = 0.0
                    if not pd.isna(row.iloc[24]):  # KONR POKAZ (Y)
                        try:
                            value_str = str(row.iloc[24]).replace(',', '.')
                            reading_value = float(value_str)
                        except:
                            reading_value = 0.0

                    meter = {
                        "marka": str(row.iloc[15]) if not pd.isna(row.iloc[15]) else "",  # MARKA (P)
                        "meter_number": str(row.iloc[16]) if not pd.isna(row.iloc[16]) else "",  # ZAVOD NOME (Q)
                        "seal_number": str(row.iloc[17]) if not pd.isna(row.iloc[17]) else "",  # NOMER PLOM (R)
                        "seal_filter": str(row.iloc[18]) if not pd.isna(row.iloc[18]) else "",  # NOMER FILT (R)
                        "date_next_verification": str(row.iloc[19]) if not pd.isna(row.iloc[19]) else "",
                        "date_meter_end": str(row.iloc[20]) if not pd.isna(row.iloc[20]) else "",  # DATALIKV (U)
                        "location": str(row.iloc[21]) if not pd.isna(row.iloc[21]) else "",  # MESTO RASP (V)
                        "type_service": str(row.iloc[22]) if not pd.isna(row.iloc[22]) else "",  # TIP USLUGI (W)
                        "month_not_reading": month_not_reading,
                        "meter_reading": {
                            "type_reading": str(row.iloc[23]) if not pd.isna(row.iloc[23]) else "",  # TIP POKAZA (X)
                            "reading_value": f"{reading_value:.3f}",
                            "reading_date": str(row.iloc[25]) if not pd.isna(row.iloc[25]) else ""  # DATAKONRPO (Z)
                        }
                    }
                    entry["meters"].append(meter)

                result.append(entry)

            self.transformed_data = result

            self.upload_btn.bgcolor = self.PRIMARY_BLUE
            self.task_count_display.content.controls[1].value = str(len(result))
            self.upload_btn.disabled = False
            self.show_message(f"Успешно преобразовано {len(result)} записей")

        except Exception as e:
            self.handle_error(f"Ошибка преобразования: {str(e)}")
            self.reset_state()

    def upload_to_database(self, e):
        if self.transformed_data is None:
            self.show_message("Сначала преобразуйте данные", error=True)
            return
        if not self.transformed_data:
            self.show_message("Нет данных для отправки", error=True)
            return

        try:
            result = send_tasks_bulk(self.transformed_data)

            if result is None:
                raise Exception("Ошибка при отправке задач. Сервер не ответил.")

            if isinstance(result, dict) and result.get("error"):
                error_msg = result.get("error", "Неизвестная ошибка")
                raise Exception(error_msg)

            success_count = len(self.transformed_data)
            self.show_message(f"Успешно отправлено задач: {success_count}")
            self.reset_state()

        except Exception as e:
            self.handle_error(f"Ошибка: {str(e)}")
            self.reset_state()

    def handle_error(self, message: str):
        self.status_message.value = message
        self.status_message.color = ft.colors.RED
        self.transform_btn.disabled = True
        self.upload_btn.disabled = True
        self.page.update()

    def show_message(self, message: str, error: bool = False):
        self.status_message.value = message
        self.status_message.color = ft.colors.RED if error else self.PRIMARY_BLUE
        self.page.update()

    def close_dialog(self, e=None):
        self.page.close(self.dialog)
        self.page.update()

    def open(self):
        self.page.open(self.dialog)
        self.page.update()

    def reset_state(self):
        self.transformed_data = None
        self.original_data = None
        self.upload_btn.disabled = True
        self.transform_btn.disabled = True
        self.file_path_display.value = "Файл не выбран"
        self.task_count_display.content.controls[1].value = "0"
        self.page.update()
