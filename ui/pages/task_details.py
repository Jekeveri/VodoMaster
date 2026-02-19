import base64
from datetime import datetime
from binascii import unhexlify

import flet as ft
from flet import (
    Container, Column, Row, Text, padding,
    BoxShadow, colors, icons,
)


class CustomTabControl:
    def __init__(self, tabs, on_change=None):
        self.tabs = tabs
        self.current_index = 0
        self.on_change = on_change
        self.controls = self._build_controls()

    def _build_controls(self):
        tab_buttons = Row(spacing=0)
        for i, tab in enumerate(self.tabs):
            tab_buttons.controls.append(
                self._create_tab_button(tab['text'], i)
            )
        return tab_buttons

    def _create_tab_button(self, text, index):
        return ft.TextButton(
            text,
            on_click=lambda e: self.switch_tab(index),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                bgcolor=colors.PRIMARY if index == self.current_index else colors.TRANSPARENT,
                padding=20,
                color=colors.ON_PRIMARY if index == self.current_index else colors.PRIMARY,
            )
        )

    def switch_tab(self, index):
        self.current_index = index
        # Обновляем стили кнопок
        for i, btn in enumerate(self.controls.controls):
            btn.style.bgcolor = colors.PRIMARY if i == index else colors.TRANSPARENT
            btn.style.color = colors.ON_PRIMARY if i == index else colors.PRIMARY
        if self.on_change:
            self.on_change(index)


class TaskDetailsPage:
    def __init__(self, page: ft.Page, task_data: dict):
        self.page = page
        self.task_data = task_data
        self.current_image_base64 = None
        self.download_picker = ft.FilePicker()
        self.page.overlay.append(self.download_picker)
        self.download_picker.on_result = self.on_download_result
        self.build_ui()

    def build_ui(self):
        # Создаем содержимое вкладок
        self.tab_contents = [
            self.create_task_info_tab(),
            self.create_meters_tab()
        ]

        # Создаем кастомные вкладки
        self.tab_control = CustomTabControl(
            tabs=[
                {'text': 'Детали задания', 'content': self.tab_contents[0]},
                {'text': 'Счетчики', 'content': self.tab_contents[1]}
            ],
            on_change=self.on_tab_change
        )

            # Основной контейнер
        self.container = Container(
            content=Column([
                self.tab_control.controls,
                ft.Divider(height=1),
                ft.Stack(self.tab_contents, expand=True)
            ], expand=True),
        )

        self.on_tab_change(0)

    def create_photo_previews(self, photos):
        if not photos:
            return ft.Text("Нет фото")

        photo_controls = []
        for photo in photos:
            value = photo.get('value')
            if not value:
                continue
            try:
                hex_value = value.replace("\\x", "")
                binary_data = unhexlify(hex_value)
                base64_str = base64.b64encode(binary_data).decode('utf-8')

                img = ft.Image(
                    src_base64=base64_str,
                    width=150,
                    height=150,
                    fit=ft.ImageFit.COVER
                )
                container = ft.Container(
                    content=img,
                    data=base64_str,
                    on_click=self.open_image_dialog,
                    tooltip=photo.get('name', 'Фото'),
                    padding=2,
                    border=ft.border.all(1, ft.colors.BLACK38),
                    border_radius=5,
                    ink=True
                )
                photo_controls.append(container)
            except Exception as e:
                photo_controls.append(ft.Text(f"Ошибка: {e}"))

        return ft.Row(photo_controls, wrap=True, spacing=5)

    def open_image_dialog(self, e):
        self.current_image_base64 = e.control.data
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Просмотр фото", text_align=ft.TextAlign.CENTER),
            content=ft.Container(
                width=min(self.page.window.width * 0.9, 800),
                height=min(self.page.window.height * 0.8, 600),
                content=ft.Image(
                    src_base64=self.current_image_base64,
                    fit=ft.ImageFit.CONTAIN,
                    gapless_playback=True
                ),
                alignment=ft.alignment.center,
                padding=10,
                bgcolor=ft.colors.BLACK12,
                border_radius=10,
            ),
            actions=[
                ft.TextButton(
                    "Скачать",
                    icon=ft.icons.DOWNLOAD,
                    on_click=lambda _: self.download_image()
                ),
                ft.TextButton(
                    "Закрыть",
                    icon=ft.icons.CLOSE,
                    on_click=lambda _: self.close_dialog(dlg)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=10)
        )
        self.page.dialog = dlg
        self.page.open(dlg)
        self.page.update()

    def download_image(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"photo_{timestamp}.png"
        self.download_picker.save_file(
            dialog_title="Сохранить фото",
            file_name=filename,
            allowed_extensions=["png", "jpg", "jpeg"]
        )

    def on_download_result(self, e: ft.FilePickerResultEvent):
        if e.path and self.current_image_base64:
            try:
                image_bytes = base64.b64decode(self.current_image_base64)
                with open(e.path, "wb") as f:
                    f.write(image_bytes)
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("Файл сохранен!"),
                    duration=2000
                )
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(f"Ошибка: {ex}"),
                    duration=3000
                )
        else:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Скачивание отменено"),
                duration=1000
            )
        self.page.snack_bar.open = True
        self.page.update()

    def close_dialog(self, dialog):
        self.page.close(dialog)
        self.page.update()

    def create_info_card(self, title: str, icon: str, content: ft.Control):
        return Container(
            content=Column([
                Row([
                    ft.Icon(icon, color=colors.BLUE_700, size=24),  # Увеличиваем размер иконки
                    Text(title,
                         weight=ft.FontWeight.BOLD,
                         size=18,
                         color=colors.BLUE_900),
                ], spacing=12),
                Container(
                    content=content,
                    alignment=ft.alignment.top_left  # Прижимаем контент к верху
                )
            ],
                spacing=20,
                alignment=ft.MainAxisAlignment.START  # Выравнивание всей колонки по верху
            ),
            padding=padding.symmetric(vertical=20, horizontal=25),  # Увеличиваем отступы
            bgcolor=colors.WHITE,
            expand=True,
            border_radius=15,
            shadow=BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=colors.BLUE_GREY_300,
                offset=ft.Offset(0, 0)
            ),
            alignment=ft.alignment.top_center  # Выравнивание всего контейнера по верху
        )

    def create_task_info_tab(self):
        task = self.task_data['task']
        address = task['address']
        meters = self.task_data['meters'][0] if self.task_data['meters'] else {}

        # Основная информация
        main_info = Column([
            self.create_info_row("Статус:", task['status'], icons.FLAG),
            self.create_info_row("Цель визита:", task['purpose'], icons.ASSIGNMENT),
            self.create_info_row("Дата начала:", task['start_date'], icons.CALENDAR_MONTH),
            self.create_info_row("Дата окончания:", task['end_date'], icons.CALENDAR_MONTH),
            self.create_info_row("Лицевой счет:", str(task['personal_account']), icons.CREDIT_CARD),
            self.create_info_row("Исполнитель:", task['employer'], icons.PERSON),
        ], spacing=10)

        # Адрес
        address_info = Column([
            self.create_info_row("Город:", address['city'], icons.LOCATION_CITY),
            self.create_info_row("Улица:", address['street'], icons.STREETVIEW),
            self.create_info_row("Дом:", address['dom'], icons.HOME),
            self.create_info_row("Квартира:", address['apartment'], icons.DOORBELL),
            self.create_info_row("Подъезд:", address['entrance'], icons.STAIRS),
            self.create_info_row("Поселок:", address['hamlet'], icons.HOLIDAY_VILLAGE),
            self.create_info_row("Прописано:", address['registered_residing'], icons.ASSIGNMENT),
            self.create_info_row("Тип Дома:", address['status'], icons.WARNING),
            # ft.ElevatedButton(
            #     content=Row(
            #         [
            #             ft.Icon(icons.INFO, color=colors.WHITE),
            #             ft.Text("Подробнее", color=colors.WHITE, weight=ft.FontWeight.W_500)
            #         ],
            #         alignment=ft.MainAxisAlignment.CENTER,
            #         spacing=5,
            #     ),
            #     style=ft.ButtonStyle(
            #         shape=ft.RoundedRectangleBorder(radius=8),
            #         bgcolor=colors.BLUE,
            #         elevation=5,
            #     ),
            #     on_click=print(123),
            # )
        ], spacing=10)

        general_photos = [p for p in self.task_data.get('photos', [])
                          if not p.get('meter_id')]

        if general_photos:
            photos_card = self.create_info_card(
                "Фото по заданию/акту",
                icons.PHOTO_CAMERA,
                self.create_photo_previews(general_photos)
            )
        else:
            photos_card = self.create_info_card(
                "Фото по заданию/акту",
                icons.PHOTO_CAMERA,
                Text("Нет фотографий", color=colors.GREY_500)
            )

        main_column = Container(
            Column([
                Row(
                    [
                        Column(
                            [
                                self.create_info_card("Основная информация", icons.INFO, main_info),
                                self.create_info_card("Адрес объекта", icons.PLACE, address_info),
                            ],
                            expand=True,
                            spacing=15
                        ),
                        Column(
                            [
                                Container(
                                    content=photos_card,
                                    expand=True,
                                    margin=ft.margin.only(left=20)
                                )
                            ], expand=True
                        )
                    ], expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH
                ),
                self.create_remark_section()
            ]), expand=True, padding=5)

        return Container(
            content=main_column,
            padding=padding.symmetric(vertical=10)
        )

    def create_meters_tab(self):
        # Основной контейнер для счетчиков
        meters_container = Column(
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        # Создаем карточки для каждого счетчика
        for meter in self.task_data['meters']:
            meter_card = self._create_meter_card(meter)
            meters_container.controls.append(meter_card)

        return Container(
            content=meters_container,
        )

    def _create_meter_card(self, meter):
        # Фильтруем фотографии
        meter_number = str(meter.get('meter_number', ''))
        meter_photos = [
            p for p in self.task_data.get('photos', [])
            if str(p.get('meter_id', '')).strip() == meter_number.strip()
        ]

        # Секция с фото
        photos_content = Container(
            content=Column([
                Row([
                    ft.Icon(icons.PHOTO_CAMERA, color=colors.BLUE_700, size=24),
                    Text("Фотографии счетчика:",
                         weight=ft.FontWeight.BOLD,
                         size=18,
                         color=colors.BLUE_900)
                ]),
                self.create_photo_previews(meter_photos) if meter_photos
                else Text("Нет фотографий", color=colors.GREY_500)
            ], spacing=10),
            padding=20,
            bgcolor=colors.GREY_50,
            border_radius=15,
            width=400,
            height=400
        )

        # Основная информация о счетчике
        info_content = Container(
            content=Column([
                self._create_info_item("Номер счетчика:", meter.get('meter_number'), icons.SPEED),
                self._create_info_item("Тип воды:", meter.get('type_water'), icons.WATER_DROP),
                self._create_info_item("Марка:", meter.get('marka'), icons.BRANDING_WATERMARK),
                self._create_info_item("Местоположение:", meter.get('location'), icons.PIN_DROP),
                self._create_info_item("Дата установки:", meter.get('installation_date'), icons.CALENDAR_MONTH),
                self._create_info_item("След. поверка:", meter.get('next_verification'), icons.ACCESS_TIME),
                self._create_info_item("Дата окончания:", meter.get('meter_end_date'), icons.CALENDAR_TODAY),
                self._create_info_item("Антимагнитная защита:",
                                       "Да" if meter.get('antimagnetic_protection') else "Нет",
                                       icons.SECURITY),
                self._create_info_item("Средний расход:",
                                       f"{meter.get('average_consumption')} м³/мес" if meter.get('average_consumption')
                                       else "Нет данных",
                                       icons.DATA_USAGE),
                self._create_info_item("Месяцев без показаний:", str(meter.get('month_not_reading')), icons.DATE_RANGE),
                self._create_info_item("Номер пломбы:", meter.get('seal_number'), icons.NUMBERS_SHARP),
                self._create_info_item("Дата пломбировки:", meter.get('seal_installation_date'), icons.DATE_RANGE),
                self._create_info_item("Последние показания:",
                                       f"{meter.get('last_reading_value')} ({meter.get('last_reading_date')})",
                                       icons.EDIT_ATTRIBUTES)
            ], spacing=8),
            padding=20,
            expand=True
        )

        return Container(
            content=Row(
                controls=[
                    # Блок с информацией (60% ширины)
                    Container(
                        content=info_content,
                        width=self.page.window.width * 0.6 - 60,
                        bgcolor=colors.WHITE,
                        border_radius=15,
                        shadow=BoxShadow(
                            spread_radius=1,
                            blur_radius=15,
                            color=colors.BLUE_GREY_300,
                            offset=ft.Offset(0, 0)
                        )
                    ),
                    photos_content
                ],
                spacing=20,
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
            padding=10,
            bgcolor=colors.WHITE,
            border_radius=15,
        )

    def _create_info_item(self, label, value, icon):
        return Row(
            controls=[
                ft.Icon(icon, size=18, color=colors.BLUE_GREY_600),
                Text(label, width=150, color=colors.BLUE_GREY_700),
                Text(value or "Не указано",
                     color=colors.BLUE_GREY_800,
                     weight=ft.FontWeight.W_500,
                     selectable=True),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

    # def _create_photos_column(self):
    #     self.selected_meter_photos = Column(
    #         [Text("Выберите счетчик для просмотра фото", size=16)],
    #         alignment=ft.MainAxisAlignment.START,
    #         scroll=ft.ScrollMode.AUTO
    #     )
    #     return self.selected_meter_photos
    #
    # def _show_meter_photos(self, meter_data):
    #     self.selected_meter_photos.controls.clear()
    #
    #     # Добавляем заголовок
    #     self.selected_meter_photos.controls.append(
    #         Row([
    #             ft.Icon(icons.PHOTO_CAMERA, color=colors.BLUE_700, size=24),
    #             Text(f"Фото счетчика {meter_data['meter_number']}",
    #                  weight=ft.FontWeight.BOLD,
    #                  size=18,
    #                  color=colors.BLUE_900)
    #         ])
    #     )
    #
    #     # Получаем фото для выбранного счетчика
    #     meter_id = str(meter_data.get('id'))
    #     meter_photos = [p for p in self.task_data.get('photos', [])
    #                     if str(p.get('meter_id', '')) == meter_id]
    #
    #     # Добавляем превью фотографий
    #     if meter_photos:
    #         self.selected_meter_photos.controls.append(
    #             self.create_photo_previews(meter_photos)
    #         )
    #     else:
    #         self.selected_meter_photos.controls.append(
    #             Text("Нет фотографий для этого счетчика")
    #         )
    #
    #     self.page.update()

    def create_info_row(self, label: str, value: str, icon: str = None):
        return Row(
            controls=[
                ft.Icon(icon, size=18, color=colors.BLUE_GREY_600) if icon else Container(width=18),
                Text(label, width=150, color=colors.BLUE_GREY_700),
                Text(value or "Не указано", color=colors.BLUE_GREY_800, weight=ft.FontWeight.W_500),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

    def create_remark_section(self):
        remark = self.task_data['task'].get('remark')
        if not remark:
            print(321321321321321)
            return ft.Container()
        print(123123123123123123123122222222222222)
        return Container(
            content=Column([
                Row([
                    ft.Icon(icons.COMMENT, color=colors.ORANGE_800, size=24),  # Увеличим размер иконки
                    Text("Особые заметки",
                         weight=ft.FontWeight.BOLD,
                         size=18,  # Увеличим размер текста
                         color=colors.BLUE_900),
                ], spacing=10),
                Container(
                    content=Text(remark,
                                 color=colors.BLUE_GREY_800,
                                 size=14),
                    padding=padding.only(left=34, top=10, bottom=10),
                )
            ]),
            padding=padding.all(20),
            bgcolor=colors.WHITE,
            border_radius=15,
            shadow=BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=colors.BLUE_GREY_300,
                offset=ft.Offset(0, 0)
            ),
            margin=ft.margin.only(top=15)  # Добавим отступ сверху
        )

    def on_tab_change(self, index):
        for i, content in enumerate(self.tab_contents):
            content.visible = (i == index)
        self.page.update()

    def get_content(self):
        return self.container


def task_details(page: ft.Page, task_data: dict):
    details_page = TaskDetailsPage(page, task_data)
    print(task_data['meters'])
    return details_page.get_content()
