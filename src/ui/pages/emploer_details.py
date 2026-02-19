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


class EmployerTab:
    def __init__(self, page: ft.Page, employee_id=None):
        self.page = page
        self.employee_id = employee_id
        self.current_tab = 0
        self.search_term = ""

        self.empty_tasks_message = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.ASSIGNMENT_LATE, size=48, color=ft.colors.BLUE_GREY_300),
                    ft.Text(
                        "Нет назначенных заданий",
                        size=20,
                        color=ft.colors.BLUE_GREY_500,
                        weight=ft.FontWeight.W_500
                    )
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=True,
            alignment=ft.alignment.center,
            visible=False
        )

        self.task_table_container = None

        self.initialize_data()
        self.build_ui()
        self.selected_rows = []

    def initialize_data(self):
        """Загрузка и подготовка данных"""
        try:
            # Получаем детальную информацию о сотруднике
            employee_details = select_server.get_employee_details(self.employee_id, refresh=True)

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

    def build_ui(self):
        """Построение пользовательского интерфейса"""
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
                {'text': 'Детали сотрудника', 'content': self.tab_contents[0]},
                {'text': 'Его задания', 'content': self.tab_contents[1]}
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
        self.search_field_task = TextField(
            label="Поиск",
            expand=True,
            prefix_icon=icons.SEARCH,
            on_change=self.perform_search_task,
            border_color=colors.BLUE,
            focused_border_color=colors.BLUE
        )

        self.top_bar_task = Container(
            content=Row([
                self.search_field_task,
                self.create_icon_button(icons.SEARCH, self.perform_search_task, colors.BLUE_600),
                self.create_icon_button(icons.FILTER_LIST, self.show_filter_panel_task, colors.BLUE_GREY_600)
            ], alignment=MainAxisAlignment.END, spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=padding.symmetric(horizontal=20, vertical=18),
            bgcolor=colors.WHITE,
            border_radius=15,
            margin=5,
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
        """Инициализация таблиц задач с учетом структуры данных"""
        # Преобразуем raw задачи в формат для таблицы

        processed_tasks = []
        for task in self.tasks_data:
            address = task.get("address", {})
            processed_tasks.append({
                "ID": task.get("id"),
                "Тип": task.get("purpose"),
                "Статус": task.get("status"),
                "Дата_начала": task.get("start_date"),
                "Дата_окончания": task.get("end_date"),
                "Комментарий": task.get("remark"),
                "Исполнитель": task.get("employer"),
                "Город": address.get("city"),
                "Поселок": address.get("hamlet"),
                "Улица": address.get("street"),
                "Дом": address.get("dom"),
                "Квартира": address.get("apartment"),
                "Район": address.get("district"),
                "Подъезд": address.get("entrence"),
                "Нормативы": address.get("standarts"),
                "Прописано": address.get("registred_residing"),
                "Площадь": address.get("area"),
                "Причина": task.get("purpose"),
            })

        # Конфигурация колонок
        columns_config = {
            "ID": {"type": "numeric"},
            "Тип": {"type": "category"},
            "Статус": {"type": "category"},
            "Дата_начала": {"type": "date"},
            "Дата_окончания": {"type": "date"},
            "Комментарий": {"type": "category"},
            "Исполнитель": {"type": "category"},
            "Город": {"type": "category"},
            "Поселок": {"type": "category"},
            "Улица": {"type": "category"},
            "Дом": {"type": "category"},
            "Квартира": {"type": "numeric"},
            "Район": {"type": "category"},
            "Подъезд": {"type": "category"},
            "Нормативы": {"type": "numeric"},
            "Прописано": {"type": "category"},
            "Площадь": {"type": "numeric"},
            "Причина": {"type": "category"},
        }

        # Скрываем дополнительные технические поля
        hidden_columns = [
            "Район", "Подъезд", "Нормативы",
            "Прописано", "Площадь", "Причина", "Исполнитель"
        ]

        # Инициализация таблицы
        self.task_table = FilterableDataTable(
            processed_tasks,
            columns_config=columns_config,
            hidden_columns=hidden_columns,
            on_selection_change=self.update_action_buttons_task,
            page_type="empl_details_tasks"
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

        self.unassign_tasks_button = ElevatedButton(
            "Снять задание",
            on_click=self.unassign_tasks,
            icon=icons.DO_NOT_TOUCH,
            icon_color=colors.WHITE,
            style=ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=colors.BLUE,
                color=colors.WHITE
            ),
            visible=False
        )

    def create_employee_tab_content(self):
        """Содержимое вкладки сотрудника"""
        # Основные данные
        main_info = Container(
            content=Column([
                Row([
                    ft.Icon(icons.PERSON, color=colors.BLUE_600),
                    ft.Text(
                        f"{self.employee_data.get('last_name', '')} {self.employee_data.get('first_name', '')}",
                        size=24,
                        weight=ft.FontWeight.BOLD
                    )
                ], spacing=10),

                ft.Divider(height=10, color=colors.TRANSPARENT),

                Row([
                    ft.Icon(icons.WORK, color=colors.GREEN_600),
                    ft.Text(
                        f"Должность: {self.employee_data.get('post_name', 'не указана')}",
                        size=16
                    )
                ], spacing=10),

                ft.Divider(height=5, color=colors.TRANSPARENT),

                Row([
                    ft.Icon(icons.PHONE, color=colors.TEAL_600),
                    ft.Text(
                        f"Телефон: {self.employee_data.get('phone_number') or 'не указан'}",
                        size=16
                    )
                ], spacing=10),

                ft.Divider(height=5, color=colors.TRANSPARENT),

                Row([
                    ft.Icon(icons.MAIL, color=colors.TEAL_600),
                    ft.Text(
                        f"Почта: {self.employee_data.get('email') or 'не указана'}",
                        size=16
                    )
                ], spacing=10),
            ]),
            padding=20,
            bgcolor=colors.WHITE,
            border_radius=15,
            shadow=BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=colors.BLUE_GREY_300,
                offset=ft.Offset(0, 0)
            )
        )

        # Учетные данные
        auth_info = Container(
            content=Column([
                ft.Text("Учетная запись:", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),

                Row([
                    ft.Icon(icons.PERSON_OUTLINE, color=colors.DEEP_ORANGE),
                    ft.Text(f"Логин: {self.employee_data.get('login', '')}", size=14)
                ], spacing=10),

                Row([
                    ft.Icon(icons.PASSWORD, color=colors.RED_ACCENT),
                    ft.Text(f"Пароль: {self.employee_data.get('password', '')}", size=14)
                ], spacing=10),
            ]),
            padding=20,
            bgcolor=colors.WHITE,
            border_radius=15,
            shadow=BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=colors.BLUE_GREY_300,
                offset=ft.Offset(0, 0)
            )
        )

        return Container(
            content=Column(
                [
                    main_info,
                    auth_info
                ],
                scroll=ScrollMode.AUTO,
                expand=True
            ),
            padding=20
        )

    def create_task_tab_content(self):
        """Содержимое вкладки задач"""
        self.task_table_container = ft.Container(
            content=Row(
                [self.task_table.data_table],
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
                    # Верхняя часть с таблицей
                    Container(
                        content=Column([
                            self.top_bar_task,
                            Container(
                                content=Column(
                                    controls=[
                                        self.task_table.selection_count_indicator,
                                        self.task_table.filter_indicator,
                                        self.task_table_container,
                                        self.empty_tasks_message
                                    ],
                                    expand=True,
                                    alignment=ft.MainAxisAlignment.START
                                ),
                                expand=True,
                            )
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
                                            self.back_button,
                                            self.task_table.add_pagination_controls(),
                                        ]
                                    )
                                ],
                                alignment=MainAxisAlignment.CENTER),
                            Row(
                                [
                                    self.unassign_tasks_button,
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

    def perform_search_task(self, e):
        search_term = self.search_field_task.value.lower() if self.search_field_task.value else ""
        self.task_table.apply_search_filter(search_term)

        if isinstance(self.search_field_task.suffix_icon, ft.IconButton):
            self.search_field_task.suffix_icon.visible = bool(search_term)
            self.search_field_task.update()

        self.task_table.force_update()

        if self.task_table.page:
            self.task_table.page.update()

    def update_action_buttons_task(self, selected_rows):
        """Обновление кнопок действий"""
        self.selected_rows = selected_rows
        self.details_button_task.visible = len(selected_rows) == 1
        self.unassign_tasks_button.visible = len(selected_rows) == 1
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

        # self._update_selection_count_indicator()
        #
        # if self.on_selection_change:
        #     self.on_selection_change(self.selected_rows)
        #
        # self.update()

    def update_task(self, e):
        """Обновление задачи с исправленной обработкой выделенных строк"""
        try:
            if self.current_tab == 0:  # Вкладка сотрудников
                selected_ids = 0
            else:  # Вкладка задач
                selected_ids = self.task_table.get_selected_ids()

            if not selected_ids:
                print("Нет выделенных строк")
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
            # set_employer_to_task(task_ids, employee_id, fio_name)
            # self.navigate_back()

        except Exception as ex:
            print(f"Ошибка при обновлении задачи: {ex}")
            # Можно добавить вывод ошибки в интерфейс
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {str(ex)}"))
            self.page.snack_bar.open = True
            self.page.update()

    def show_filter_panel_task(self, e):
        self.task_table.show_filters()

    def back_to_leave(self, e):
        """Обработка кнопки Назад"""
        self.navigate_back()

    def reload_tasks(self):
        """Перезагрузка данных таблицы задач"""
        # Обновляем данные из БД
        self.initialize_data()

        # Формируем новые данные для таблицы
        processed_tasks = []
        for task in self.tasks_data:
            address = task.get("address", {})
            processed_tasks.append({
                "ID": task.get("id"),
                "Тип": task.get("purpose"),
                "Статус": task.get("status"),
                "Дата_начала": task.get("start_date"),
                "Дата_окончания": task.get("end_date"),
                "Комментарий": task.get("remark"),
                "Исполнитель": task.get("employer"),
                "Город": address.get("city"),
                "Поселок": address.get("hamlet"),
                "Улица": address.get("street"),
                "Дом": address.get("dom"),
                "Квартира": address.get("apartment"),
                "Район": address.get("district"),
                "Подъезд": address.get("entrence"),
                "Нормативы": address.get("standarts"),
                "Прописано": address.get("registred_residing"),
                "Площадь": address.get("area"),
                "Причина": task.get("purpose"),
            })

        has_tasks = len(self.tasks_data) > 0

        # Обновляем данные в таблице
        self.task_table.original_df = pd.DataFrame(processed_tasks)
        self.task_table.filtered_df = self.task_table.original_df.copy()

        self.task_table_container.visible = has_tasks
        self.empty_tasks_message.visible = not has_tasks

        # Применяем обновления
        self.task_table._update_table()
        self.task_table._reset_filters_full()
        self.task_table.selected_rows.clear()
        # Сбрасываем выделение и обновляем UI
        self.task_table.selected_rows = []
        self.task_table.current_page = 0
        self.task_table._update_selection_count_indicator()
        self.task_table._update_pagination_controls()

        if hasattr(self.page, 'update'):
            self.page.update()

    def unassign_tasks(self, e):
        selected_rows = list(self.task_table.selected_rows)

        mass_ids = self.task_table.filtered_df.loc[selected_rows, 'ID'].tolist()
        fio_emp = self.employee_data.get('last_name', '') + " " + self.employee_data.get('first_name', '')

        # Создание диалога подтверждения
        def confirm_unassign(e):
            self.page.close(confirm_dialog)
            try:
                # Вызов API для снятия задач
                result = modification_server.unassign_tasks(mass_ids, [fio_emp])
                if result:
                    show_snack_bar(self.page, f"Снято {len(mass_ids)} задач")
                    self.reload_tasks()
                else:
                    show_snack_bar(self.page, "Ошибка при снятии задач")
            except Exception as ex:
                print(f"Ошибка: {str(ex)}")

        def cancel_unassign(e):
            self.page.close(confirm_dialog)
            self.page.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Снятие задач с исполнителя",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLUE_600
            ),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.WARNING_ROUNDED, color=ft.colors.ORANGE_600, size=48),
                    ft.Text(
                        f"Вы действительно хотите снять {len(mass_ids)} задач(и) с текущего исполнителя?",
                        size=16,
                        color=ft.colors.GREY_800
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                ft.Text(
                    "Задачи вернутся в статус 'Не назначены'",
                    color=ft.colors.BLUE_600,
                    italic=True,
                    size=14
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, height=150),
            actions=[
                ft.TextButton(
                    "Отмена",
                    on_click=cancel_unassign,
                    style=ft.ButtonStyle(color=ft.colors.GREY_700)
                ),
                ft.FilledButton(
                    "Снять",
                    on_click=confirm_unassign,
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
        self.page.open(confirm_dialog)
        self.page.update()

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
def employer_details(page, employee_id=None):
    print(employee_id['employee_id'])

    return EmployerTab(page, employee_id['employee_id']).get_content()
