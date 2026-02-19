import math
import uuid
import flet as ft
import pandas as pd
from flet import (
    Container, Column, Row, TextField, IconButton, ElevatedButton,
    ButtonStyle, BoxShadow, padding, alignment,
    ScrollMode, colors, icons, MainAxisAlignment, border
)
import src.database.admin.select_server as select_server
import src.database.admin.modification_server as modification_server
from src.database.admin.modification_server import set_employer_to_task
from src.database.admin.select_server import get_all_employees
from src.ui.components.table_components.class_table import FilterableDataTable
from src.ui.components.crud_dialogs.further_details_empl_dialog import FurtherDetailsEmployeeDialog
from src.ui.components.table_components.data_tuples import load_data_from_tuples
from src.ui.utils.navigation import nav_manager
from src.utils.show_snack_bar import show_snack_bar

from src.ui.utils.ui_blocker import block_ui


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
            style=ButtonStyle(
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


class AddressTab:
    def __init__(self, page: ft.Page, address_id=None):
        self.page = page
        self.address_id = address_id
        self.current_tab = 0
        self.search_term = ""

        # Элементы для пустых состояний
        self.empty_meters_message = self._create_empty_message("Нет зарегистрированных счетчиков")
        self.empty_tasks_message = self._create_empty_message("Нет связанных задач")

        self.task_table_container = None
        self.meters_table_container = None

        self.initialize_data()
        self.build_ui()
        self.selected_rows = {'meters': [], 'tasks': []}

    def _create_empty_message(self, text):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.ASSIGNMENT_LATE, size=48, color=ft.colors.BLUE_GREY_300),
                    ft.Text(
                        text,
                        size=20,
                        color=ft.colors.BLUE_GREY_500,
                        weight=ft.FontWeight.W_500
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.alignment.center,
            visible=False
        )

    def initialize_data(self):
        try:
            address_details = select_server.get_address_details(self.address_id, refresh=True)
            self.address_info = address_details.get('address_info', {})
            self.meters_data = address_details.get('meters', [])
            self.tasks_data = address_details.get('tasks', [])

            print(self.address_info)
            print(self.meters_data)
            print(self.tasks_data)

        except Exception as e:
            show_snack_bar(self.page, f"Ошибка загрузки данных: {str(e)}")

    def build_ui(self):
        self.create_search_controls()
        self.create_tables()
        self.create_action_buttons()

        self.tab_contents = [
            self.create_info_tab_content(),
            self.create_meters_tab_content(),
            self.create_tasks_tab_content()
        ]

        self.tab_control = CustomTabControl(
            tabs=[
                {'text': 'Информация', 'content': self.tab_contents[0]},
                {'text': 'Счетчики', 'content': self.tab_contents[1]},
                {'text': 'Задачи', 'content': self.tab_contents[2]}
            ],
            on_change=self.on_tab_change
        )

        self.tab_contents[1].visible = False
        self.tab_contents[2].visible = False

        self.container = Container(
            content=Column([
                self.tab_control.controls,
                ft.Divider(height=1),
                ft.Stack(self.tab_contents, expand=True)
            ], expand=True)
        )

    def create_search_controls(self):
        # Поиск для счетчиков
        self.search_field_meters = TextField(
            label="Поиск счетчиков",
            expand=True,
            prefix_icon=icons.SEARCH,
            on_change=lambda e: self.perform_search('meters'),
            border_color=colors.BLUE
        )

        # Поиск для задач
        self.search_field_tasks = TextField(
            label="Поиск задач",
            expand=True,
            prefix_icon=icons.SEARCH,
            on_change=lambda e: self.perform_search('tasks'),
            border_color=colors.BLUE
        )

    def create_tables(self):
        # Таблица счетчиков
        processed_meters = []
        for m in self.meters_data:
            last_reading = m.get('last_reading', {})
            processed_meters.append({
                "ID": str(m.get('meter_id', '')),  # Добавляем ID для идентификации
                "Тип": m.get('type_water', ''),
                "Номер": m.get('meter_number', ''),
                "Показание": f"{last_reading.get('value', '')} ({last_reading.get('date', '')})",
                "Установлен": m.get('installation_date', ''),
                "Поверка": m.get('next_verification', '')
            })

        self.meters_table = FilterableDataTable(
            processed_meters,
            columns_config={
                "Тип": {"type": "category"},
                "Номер": {"type": "category"},
                "Показание": {"type": "category"},
                "Установлен": {"type": "date"},
                "Поверка": {"type": "date"}
            },
            hidden_columns=["ID"],
            page_type="address_details_meters",
            on_selection_change=lambda s: self.update_action_buttons('meters', s)
        )
        self.meters_table.set_page(self.page)

        # Таблица задач (аналогично примеру)
        processed_tasks = []
        for task in self.tasks_data:
            employees = task.get("employees", {})
            processed_tasks.append({
                "ID": str(task.get("task_id", '')),
                "Тип": task.get("type", ""),
                "Статус": task.get("status", "неизвестно").capitalize(),
                "Дата_начала": task.get("dates", {}).get("start", ""),
                "Дата_окончания": task.get("dates", {}).get("end", ""),
                "Комментарий": task.get("remarks", ""),
                "Исполнитель": employees.get("name", "")
            })

        self.tasks_table = FilterableDataTable(
            processed_tasks,
            columns_config={
                "ID": {"type": "numeric"},
                "Тип": {"type": "category"},
                "Статус": {"type": "category"},
                "Дата_начала": {"type": "date"},
                "Дата_окончания": {"type": "date"},
                "Комментарий": {"type": "category"},
                "Исполнитель": {"type": "category"},
            },
            hidden_columns=["ID"],
            page_type="address_details_tasks",
            on_selection_change=lambda s: self.update_action_buttons('tasks', s)
        )
        self.tasks_table.set_page(self.page)

    def further_details_button_task(self, e=None):
        """Обработчик открытия подробной информации о задании"""
        try:
            # Получаем выбранные строки из таблицы
            selected_rows = self.tasks_table.filtered_df.loc[list(self.tasks_table.selected_rows), 'ID'].tolist()

            result = selected_rows[0]

            @block_ui(self.page)
            def load_data():
                return select_server.get_task_details(result, refresh=True)

            data_server = load_data()

            # Создаем навигационную кнопку
            new_button = {
                "icon": ft.icons.INFO,
                "label": "Детали задания",
                "data": "task_details",
                "id": f"task_details_{uuid.uuid4()}",
                "additional_data": data_server,
            }

            # Выполняем навигацию
            nav_manager.add_nav_button_and_navigate(new_button)

        except Exception as ex:
            print(f"Ошибка при загрузке данных: {str(ex)}")

    def create_action_buttons(self):
        # Кнопки для счетчиков
        self.details_button_task = ElevatedButton(
            "Подробнее",
            on_click=self.further_details_button_task,
            icon=icons.INFO,
            icon_color=colors.WHITE,
            style=ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=colors.BLUE,
                color=colors.WHITE
            ),
            visible=False
        )

    def create_info_tab_content(self):
        location = self.address_info.get('location', {})
        customer = self.address_info.get('customer', {})
        technical = self.address_info.get('technical', {})

        return Container(
            content=Column([
                # Блок клиента
                Container(
                    content=Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.PERSON, color=colors.BLUE_600),
                            title=Row([
                                    ft.Text(
                                        f"{customer.get('full_name', '')}",
                                        size=20,
                                        weight=ft.FontWeight.BOLD
                                    )
                                ], spacing=10),
                            subtitle=Column([
                                # ft.Text(f"ФИО: {customer.get('full_name', '')}", size=16),
                                ft.Text(f"Лицевой счет: {customer.get('personal_account', '')}", size=16),
                                ft.Text(f"Телефон: {customer.get('phone', '')}", size=16)
                            ])
                        )
                    ]),
                    padding=15,
                    bgcolor=colors.WHITE,
                    border_radius=15,
                    shadow=BoxShadow(
                        spread_radius=1,
                        blur_radius=15,
                        color=colors.BLUE_GREY_300,
                        offset=ft.Offset(0, 0)
                    )
                ),

                # Блок адреса
                Container(
                    content=Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.LOCATION_ON, color=colors.GREEN_600),
                            title=Row([
                                    ft.Text(
                                        f"Адрес:",
                                        size=20,
                                        weight=ft.FontWeight.BOLD
                                    )
                                ], spacing=10),
                            subtitle=Column([
                                ft.Text(f"Город: {location.get('city', '')}", size=16),
                                ft.Text(f"Улица: {location.get('street', '')}", size=16),
                                ft.Text(f"Дом: {location.get('house', '')}", size=16),
                                ft.Text(f"Квартира: {location.get('apartment', '')}", size=16)
                            ])
                        )
                    ]),
                    padding=15,
                    bgcolor=colors.WHITE,
                    border_radius=15,
                    shadow=BoxShadow(
                        spread_radius=1,
                        blur_radius=15,
                        color=colors.BLUE_GREY_300,
                        offset=ft.Offset(0, 0)
                    ),
                    margin=ft.margin.only(top=10)
                )
            ],
                scroll=ScrollMode.AUTO,
                expand=True),
            padding=20,
            visible=True
        )

    def show_filter_panel_task(self, e):
        self.tasks_table.show_filters()

    def show_filter_panel_meters(self, e):
        self.meters_table.show_filters()

    def create_tasks_tab_content(self):
        self.task_table_container = ft.Container(
            content=Row(
                [self.tasks_table.data_table],
                scroll=ScrollMode.AUTO,
                vertical_alignment=ft.CrossAxisAlignment.START  # Выравнивание по верху
            ),
            expand=True,
            padding=10,
            visible=False
        )

        has_tasks = len(self.tasks_data) > 0
        self.task_table_container.visible = has_tasks
        self.empty_tasks_message.visible = not has_tasks

        return Container(
            content=Column(
                controls=[
                    Container(
                        content=Column([
                            Container(Row([
                                self.search_field_tasks,
                                self.create_icon_button(icons.SEARCH, lambda e: self.perform_search('tasks'),
                                                        colors.BLUE_600),
                                self.create_icon_button(icons.FILTER_LIST, self.show_filter_panel_task,
                                                        colors.BLUE_GREY_600)
                            ], alignment=MainAxisAlignment.END, spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=padding.symmetric(horizontal=20, vertical=18),
                                bgcolor=colors.WHITE,
                                border_radius=15,
                                margin=5,
                                shadow=BoxShadow(blur_radius=5)
                            ),
                            Container(
                                content=Column([
                                    self.tasks_table.selection_count_indicator,
                                    self.tasks_table.filter_indicator,
                                    self.task_table_container,
                                    self.empty_tasks_message
                                ],
                                    expand=True,
                                    alignment=ft.MainAxisAlignment.START
                                ),
                                expand=True
                            ),
                        ],
                            scroll=ScrollMode.AUTO,
                            expand=True
                        ),
                        padding=10,
                        expand=True
                    ),
                    Container(
                        content=Row([
                            Column(
                                [
                                    Row(
                                        [
                                            # self.back_button,
                                            self.tasks_table.add_pagination_controls(),
                                        ]
                                    )
                                ],
                                alignment=MainAxisAlignment.CENTER),
                            Row(
                                [
                                    self.details_button_task,
                                    # self.details_button_task
                                ],
                                alignment=MainAxisAlignment.CENTER,
                            ),
                        ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                        padding=padding.symmetric(horizontal=15, vertical=12),
                        bgcolor=colors.WHITE,
                        border_radius=12,
                        shadow=BoxShadow(
                            color=colors.BLUE_GREY_300,
                            offset=ft.Offset(0, -2),
                            blur_radius=5,
                            spread_radius=1,
                        ),
                    )
                ], expand=True))

    def create_meters_tab_content(self):
        self.meters_table_container = ft.Container(
            content=Row(
                [self.meters_table.data_table],
                scroll=ScrollMode.AUTO,
                vertical_alignment=ft.CrossAxisAlignment.START  # Выравнивание по верху
            ),
            expand=True,
            padding=10,
            visible=False
        )

        has_meters = len(self.meters_data) > 0
        self.meters_table_container.visible = has_meters
        self.empty_meters_message.visible = not has_meters

        return Container(
            content=Column(
                controls=[
                    Container(
                        content=Column([
                            Container(Row([
                                self.search_field_meters,
                                self.create_icon_button(icons.SEARCH, lambda e: self.perform_search('meters'),
                                                        colors.BLUE_600),
                                self.create_icon_button(icons.FILTER_LIST, self.show_filter_panel_meters,
                                                        colors.BLUE_GREY_600)
                            ], alignment=MainAxisAlignment.END, spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                padding=padding.symmetric(horizontal=20, vertical=18),
                                bgcolor=colors.WHITE,
                                border_radius=15,
                                margin=5,
                                shadow=BoxShadow(blur_radius=5)
                            ),
                            Container(
                                content=Column([
                                    self.meters_table.selection_count_indicator,
                                    self.meters_table.filter_indicator,
                                    self.meters_table_container,
                                    self.empty_meters_message
                                ],
                                    expand=True,
                                    alignment=ft.MainAxisAlignment.START
                                ),
                                expand=True
                            ),
                        ],
                            scroll=ScrollMode.AUTO,
                            expand=True
                        ),
                        padding=10,
                        expand=True
                    ),
                    Container(
                        content=Row([
                            Column(
                                [
                                    Row(
                                        [
                                            # self.back_button,
                                            self.meters_table.add_pagination_controls(),
                                        ]
                                    )
                                ],
                                alignment=MainAxisAlignment.CENTER),
                            Row(
                                [
                                    # self.unassign_tasks_button,
                                    # self.details_button_task
                                ],
                                alignment=MainAxisAlignment.CENTER,
                            ),
                        ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                        padding=padding.symmetric(horizontal=15, vertical=12),
                        bgcolor=colors.WHITE,
                        border_radius=12,
                        shadow=BoxShadow(
                            color=colors.BLUE_GREY_300,
                            offset=ft.Offset(0, -2),
                            blur_radius=5,
                            spread_radius=1,
                        ),
                    )
                ], expand=True))

    def create_icon_button(self, icon, on_click, bgcolor):
        """Кнопка с иконкой"""
        return Container(
            IconButton(
                icon=icon,
                on_click=on_click,
                style=ButtonStyle(color=colors.WHITE)
            ),
            width=50, height=50,
            bgcolor=bgcolor,
            border_radius=15,
            alignment=alignment.center
        )

    def on_tab_change(self, index):
        self.current_tab = index
        for i, content in enumerate(self.tab_contents):
            content.visible = (i == index)
        self.page.update()

    def perform_search(self, tab_type):
        search_term = getattr(self, f"search_field_{tab_type}").value.lower()
        table = getattr(self, f"{tab_type}_table")
        table.apply_search_filter(search_term)
        table.force_update()
        if table.page:
            table.page.update()

    def update_action_buttons(self, tab_type, selected_rows):
        self.selected_rows[tab_type] = selected_rows
        if tab_type == 'meters':
            pass
            # self.add_meter_button.visible = len(selected_rows) > 0
        elif tab_type == 'tasks':
            self.details_button_task.visible = len(selected_rows) > 0
        self.page.update()


def address_details(page: ft.Page, address_id=None):
    # address_id = params.get('address_id') if params else None
    return AddressTab(page, address_id['employee_id']).container
