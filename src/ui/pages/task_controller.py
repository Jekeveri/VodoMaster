import math
import uuid
import flet as ft
from flet import (
    Container, Column, Row, TextField, IconButton, ElevatedButton,
    ButtonStyle, BoxShadow, padding, alignment,
    ScrollMode, colors, icons, MainAxisAlignment, border
)
import src.database.admin.select_server as select_server
from src.database.admin.modification_server import set_employer_to_task
from src.database.admin.select_server import get_all_employees
from src.ui.components.table_components.class_table import FilterableDataTable
from src.ui.components.crud_dialogs.further_details_empl_dialog import FurtherDetailsEmployeeDialog
from src.ui.components.table_components.data_tuples import load_data_from_tuples
from src.ui.utils.navigation import nav_manager
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


class EmployerTab:
    def __init__(self, page: ft.Page, tasks_data=None):
        self.page = page
        self.tasks_data = tasks_data or []
        self.current_tab = 0
        self.search_term = ""
        self.initialize_data()
        self.build_ui()
        self.selected_rows = []

    def initialize_data(self):
        """Загрузка и подготовка данных"""

        @block_ui(self.page)
        def load_employees():
            return get_all_employees()

        # Данные сотрудников
        emp_data = load_employees()
        self.employee_data = load_data_from_tuples(
            data_tuples=emp_data,
            columns=['ID', 'ФИО', 'Права', 'Телефон', 'Почта', 'Статус здоровья',
                     'Задач сегодня', 'Выполненных сегодня', 'Не выполнено сегодня', 'Всего не выполнено'],
            numeric_columns=['ID', 'Задач сегодня', 'Выполненных сегодня', 'Не выполнено сегодня',
                             'Всего не выполнено'],
            string_columns=['ФИО', 'Права', 'Телефон', 'Почта', 'Статус здоровья']
        )

        # Данные задач
        selected_fields = [
            'ID', 'ФИО', 'id_квартиры', 'Город', 'Район', 'Улица',
            'Поселок', 'Дом', 'Квартира', 'Подъезд', 'Прописано',
            'Тип', 'Нормативы', 'Площадь', 'Телефон', 'Лицевой_счет',
            'Дата', 'Комментарий', 'Статус', 'Причина',
            'Сальдо', 'Исполнитель', 'Дата_выполнения',
            'Счетчики', 'Акты', 'Фото', 'Расположение'
        ]

        tuple_data = []
        for item in self.tasks_data:
            row = []
            for field in selected_fields:
                # Обрабатываем отсутствующие поля и NaN значения
                value = item.get(field, '')
                if isinstance(value, float) and math.isnan(value):
                    value = ''
                row.append(value)
            tuple_data.append(tuple(row))

        self.task_data = load_data_from_tuples(
            data_tuples=tuple_data,
            columns=selected_fields,
            date_columns=['Дата', 'Дата_выполнения'],
            numeric_columns=['ID', 'Нормативы', 'Квартира', 'Лицевой_счет'],
            string_columns=[col for col in selected_fields if col not in
                            ['ID', 'Нормативы', 'Квартира', 'Лицевой_счет',
                             'Дата', 'Дата_выполнения']]
        )

    def build_ui(self):
        """Построение пользовательского интерфейса"""
        # Создаем элементы управления
        self.create_search_controls()
        self.create_tables()
        self.create_action_buttons()

        # Собираем содержимое вкладок
        self.tab_contents = [
            self.create_employee_tab_content(),
            self.create_task_tab_content()
        ]

        # Создаем кастомные вкладки
        self.tab_control = CustomTabControl(
            tabs=[
                {'text': 'Сотрудники', 'content': self.tab_contents[0]},
                {'text': 'Выбранные задания', 'content': self.tab_contents[1]}
            ],
            on_change=self.on_tab_change
        )

        # Инициализируем видимость
        self.tab_contents[1].visible = False

        # Основной контейнер
        self.container = Container(
            content=Column([
                self.tab_control.controls,
                ft.Divider(height=1),
                ft.Stack(self.tab_contents, expand=True)
            ], expand=True)
        )

    def create_search_controls(self):
        """Панель поиска"""
        self.search_field = TextField(
            label="Поиск",
            expand=True,
            prefix_icon=icons.SEARCH,
            on_change=self.perform_search,
            border_color=colors.BLUE,
            focused_border_color=colors.BLUE
        )

        self.search_field_task = TextField(
            label="Поиск",
            expand=True,
            prefix_icon=icons.SEARCH,
            on_change=self.perform_search_task,
            border_color=colors.BLUE,
            focused_border_color=colors.BLUE
        )

        self.top_bar = Container(
            content=Row([
                self.search_field,
                self.create_icon_button(icons.SEARCH, self.perform_search, colors.BLUE_600),
                self.create_icon_button(icons.REFRESH, self.reload_page, colors.BLUE_GREY_600),
                self.create_icon_button(icons.FILTER_LIST, self.show_filter_panel, colors.BLUE_GREY_600)
            ], alignment=MainAxisAlignment.END, spacing=12),
            padding=padding.symmetric(horizontal=20, vertical=18),
            bgcolor=colors.WHITE,
            border_radius=15,
            shadow=BoxShadow(blur_radius=5)
        )

        self.top_bar_task = Container(
            content=Row([
                self.search_field_task,
                self.create_icon_button(icons.SEARCH, self.perform_search_task, colors.BLUE_600),
                self.create_icon_button(icons.FILTER_LIST, self.show_filter_panel_task, colors.BLUE_GREY_600)
            ], alignment=MainAxisAlignment.END, spacing=12),
            padding=padding.symmetric(horizontal=20, vertical=18),
            bgcolor=colors.WHITE,
            border_radius=15,
            shadow=BoxShadow(blur_radius=5)
        )

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

    def create_tables(self):
        """Инициализация таблиц"""
        # Таблица сотрудников
        self.employee_table = FilterableDataTable(
            self.employee_data,
            columns_config={
                "ID": {"type": "numeric"},
                "ФИО": {"type": "category"},
                "Права": {"type": "category"},
                "Телефон": {"type": "category"},
                "Почта": {"type": "category"},
                "Статус здоровья": {"type": "category"},
                "Задач сегодня": {"type": "numeric"},
                "Выполненных сегодня": {"type": "numeric"},
                "Не выполнено сегодня": {"type": "numeric"},
                "Всего не выполнено": {"type": "numeric"}
            },
            on_selection_change=self.update_action_buttons,
            page_type="employeer_assign",
            search_field=self.search_term

        )
        self.employee_table.set_page(self.page)

        # Таблица задач
        self.task_table = FilterableDataTable(
            self.task_data,
            columns_config={
                "Тип": {"type": "category"},
                "Дата": {"type": "date"},
                "ФИО": {"type": "category"},
                "Телефон": {"type": "category"},
                "Поселок": {"type": "category"},
                "Улица": {"type": "category"},
                "Дом": {"type": "category"},
                "Квартира": {"type": "numeric"},
                "Причина": {"type": "category"},
                "Комментарий": {"type": "category"},
                "Исполнитель": {"type": "category"},
                "Статус": {"type": "category"},
                "Дата_выполнения": {"type": "date"},
                "Лицевой_счет": {"type": "numeric"},
                "Нормативы": {"type": "numeric"},
                "Расположение": {"type": "category"},
                "Город": {"type": "category"},
                "Район": {"type": "category"},
                "Подъезд": {"type": "category"},
                "Прописано": {"type": "category"},
                "Площадь": {"type": "category"},
                "Сальдо": {"type": "category"},
                "ID": {"type": "numeric"},
            },
            hidden_columns=["Сальдо", "Город", "Район", "Подъезд",
                            "Площадь", "Прописано", "Нормативы"],
            on_selection_change=self.update_action_buttons_task,
            page_type="assign_tasks"
        )
        self.task_table.set_page(self.page)

    def create_action_buttons(self):
        """Кнопки действий"""
        self.button_edit = ElevatedButton(
            "Выбрать",
            on_click=self.update_task,
            icon=icons.ASSIGNMENT,
            icon_color=colors.WHITE,
            style=ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=colors.BLUE,
                color=colors.WHITE
            ),
            visible=False
        )

        self.back_button = ElevatedButton(
            "Назад",
            on_click=self.back_to_leave,
            icon=icons.ARROW_BACK,
            icon_color=colors.WHITE,
            style=ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=colors.BLUE_GREY_600,
                color=colors.WHITE
            )
        )

        self.details_button = ElevatedButton(
            "Подробнее",
            on_click=self.further_details_button,
            icon=icons.INFO,
            icon_color=colors.WHITE,
            style=ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=colors.BLUE,
                color=colors.WHITE
            ),
            visible=False
        )

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

    def create_employee_tab_content(self):
        """Содержимое вкладки сотрудников"""
        return Container(
            content=Column([
                Column([
                    self.top_bar,
                    Container(
                        content=Column([
                            self.employee_table.selection_count_indicator,
                            self.employee_table.filter_indicator,
                            Row([self.employee_table.data_table], scroll=ScrollMode.AUTO)
                        ], scroll=ScrollMode.AUTO),
                        expand=True,
                        padding=10
                    )
                ], expand=True),
                Container(
                    content=Row([
                        Column(
                            [
                                Row(
                                    [
                                        self.back_button,
                                        self.employee_table.add_pagination_controls(),
                                    ]
                                )
                            ],
                            alignment=MainAxisAlignment.CENTER),
                        Row(
                            [
                                self.details_button,
                                self.button_edit
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
            ], expand=True)
        )

    def create_task_tab_content(self):
        """Содержимое вкладки задач"""
        return Container(
            content=Column([
                self.top_bar_task,
                Container(
                    content=Column(
                        [
                            self.task_table.selection_count_indicator,
                            self.task_table.filter_indicator,
                            Row([self.task_table.data_table], scroll=ScrollMode.AUTO)
                        ], scroll=ScrollMode.AUTO),
                    expand=True,
                    padding=10
                ),
                Container(
                    content=Row([
                        Column(
                            [
                                Row(
                                    [
                                        self.back_button,
                                        self.task_table.add_pagination_controls(),
                                    ]
                                )
                            ],
                            alignment=MainAxisAlignment.CENTER),
                        Row(
                            [
                                self.details_button_task
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
            ], expand=True)
        )

    def on_tab_change(self, index):
        """Обработчик переключения вкладок"""
        self.current_tab = index
        for i, content in enumerate(self.tab_contents):
            content.visible = (i == index)
        self.page.update()

    def perform_search(self, e):
        search_term = self.search_field.value.lower() if self.search_field.value else ""
        self.employee_table.apply_search_filter(search_term)

        if isinstance(self.search_field.suffix_icon, ft.IconButton):
            self.search_field.suffix_icon.visible = bool(search_term)
            self.search_field.update()

        self.employee_table.force_update()

        if self.employee_table.page:
            self.employee_table.page.update()

    def perform_search_task(self, e):
        search_term = self.search_field_task.value.lower() if self.search_field_task.value else ""
        self.task_table.apply_search_filter(search_term)

        if isinstance(self.search_field_task.suffix_icon, ft.IconButton):
            self.search_field_task.suffix_icon.visible = bool(search_term)
            self.search_field_task.update()

        self.task_table.force_update()

        if self.task_table.page:
            self.task_table.page.update()

    def reload_page(self, e):
        # self.employee_table.clear_pagination_controls()

        @block_ui(self.page)
        def load_employees():
            return get_all_employees(refresh=True)

        # Данные сотрудников
        emp_data = load_employees()

        self.employee_data.original_df = load_data_from_tuples(
            data_tuples=emp_data,
            columns=['ID', 'ФИО', 'Права', 'Телефон', 'Почта', 'Статус здоровья',
                     'Задач сегодня', 'Выполненных сегодня', 'Не выполнено сегодня', 'Всего не выполнено'],
            numeric_columns=['ID', 'Задач сегодня', 'Выполненных сегодня', 'Не выполнено сегодня',
                             'Всего не выполнено'],
            string_columns=['ФИО', 'Права', 'Телефон', 'Почта', 'Статус здоровья']
        )
        self.employee_table.filtered_df = self.employee_data.original_df.copy()

        self.employee_table.filter_settings.clear()
        self.employee_table.current_page = 0
        self.employee_table.selected_rows.clear()

        # Принудительно обновляем таблицу
        self.employee_table._update_table()
        self.employee_table._update_selection_count_indicator()

        if hasattr(self.employee_table, 'page_panel'):
            # Используем правильное имя метода с подчеркиванием
            self.employee_table._reset_filters_full()

        # Обновляем страницу
        if hasattr(self.page, 'update'):
            self.page.update()

    def update_action_buttons(self, selected_rows):
        """Обновление кнопок действий"""
        self.selected_rows = selected_rows
        self.button_edit.visible = len(selected_rows) == 1
        self.details_button.visible = len(selected_rows) == 1
        self.page.update()

    def update_action_buttons_task(self, selected_rows):
        """Обновление кнопок действий"""
        self.selected_rows = selected_rows
        self.details_button_task.visible = len(selected_rows) == 1
        self.page.update()

    def get_selected_ids(self):
        """Возвращает список ID выделенных строк"""
        if not self.selected_rows:
            return []

        # Проверяем тип первого элемента
        if isinstance(self.selected_rows[0], dict):
            return [row.get('ID') for row in self.selected_rows if row.get('ID') is not None]
        elif isinstance(self.selected_rows[0], (int, str)):
            return [id for id in self.selected_rows]
        return []

    def _handle_row_select(self, e):
        """Обработчик выделения строки"""
        row_data = e.control.data
        if row_data in self.selected_rows:
            self.selected_rows.remove(row_data)
        else:
            self.selected_rows.append(row_data)

        self._update_selection_count_indicator()

        if self.on_selection_change:
            self.on_selection_change(self.selected_rows)

        self.update()

    def update_task(self, e):
        """Обновление задачи с исправленной обработкой выделенных строк"""
        try:
            if self.current_tab == 0:  # Вкладка сотрудников
                selected_ids = self.employee_table.get_selected_rows()
            else:  # Вкладка задач
                selected_ids = self.task_table.get_selected_ids()

            if not selected_ids:
                print("Нет выделенных строк")
                return

            mass_ids = self.employee_table.filtered_df.loc[
                list(self.employee_table.selected_rows), 'ID'].tolist()
            employee_id = mass_ids[0] if mass_ids else 0
            if not employee_id or employee_id == 0:
                print("Неверный ID сотрудника")
                return

            task_ids = []
            fio_name = []
            for item in self.tasks_data:
                if isinstance(item, dict) and 'ID' in item:
                    task_ids.append(item['ID'])
                    fio_name.append(item['Исполнитель'])
                elif isinstance(item, (int, str)):
                    task_ids.append(item)
                    fio_name.append(item)

            if not task_ids:
                print("Нет задач для назначения")
                return

            # Назначаем задачи первому выбранному сотруднику
            set_employer_to_task(task_ids, employee_id, fio_name)
            self.navigate_back()

        except Exception as ex:
            print(f"Ошибка при обновлении задачи: {ex}")
            # Можно добавить вывод ошибки в интерфейс
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {str(ex)}"))
            self.page.snack_bar.open = True
            self.page.update()

    def show_filter_panel(self, e):
        self.employee_table.show_filters()

    def show_filter_panel_task(self, e):
        self.task_table.show_filters()

    def back_to_leave(self, e):
        """Обработка кнопки Назад"""
        self.navigate_back()

    def further_details_button(self, e=None):
        """Обработчик открытия подробной информации о сотруднике"""
        mass_ids = self.employee_table.filtered_df.loc[list(self.employee_table.selected_rows), 'ID'].tolist()
        if len(mass_ids) != 1:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Выберите одного сотрудника для просмотра подробностей", color=ft.colors.RED),
                duration=3000
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        employee_data = mass_ids[0]

        new_buttons = [
            {
                "icon": ft.icons.INFO,
                "label": "Детали сотрудника",
                "data": "empl_details",
                "id": f"empl_details_{uuid.uuid4()}",
                "additional_data": {"employee_id": employee_data},
            }
        ]
        nav_manager.add_nav_button_and_navigate(new_buttons[0])


    def further_details_button_task(self, e=None):
        """Обработчик открытия подробной информации о задании"""
        try:
            # Получаем выбранные строки из таблицы
            selected_rows = self.task_table.filtered_df.loc[list(self.task_table.selected_rows), 'ID'].tolist()

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

    def navigate_back(self):
        """Навигация назад"""
        try:
            if not nav_manager.go_back() and nav_manager.on_navigate_callback:
                nav_manager.on_navigate_callback({
                    'id': 'search',
                    'data': 'btn_search'
                })
        except Exception as ex:
            print(f"Ошибка навигации: {ex}")

    def get_content(self):
        """Получить содержимое для отображения"""
        return self.container


# Функция для совместимости
def employer_tab(page, tasks_data=None):
    return EmployerTab(page, tasks_data).get_content()
