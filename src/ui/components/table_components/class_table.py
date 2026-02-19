import flet as ft
import numpy as np
import pandas as pd
from datetime import datetime
from flet import (
    DataTable, DataColumn, DataRow, DataCell, Text, Checkbox,
    Column, Row, TextField, IconButton, Container, PopupMenuButton,
    PopupMenuItem, AlertDialog, DatePicker, colors, icons, border,
    FontWeight, MainAxisAlignment, ScrollMode, ButtonStyle, GestureDetector
)
import asyncio
from src.ui.components.table_components.table_settings_manager import TableStateManager
from src.ui.components.table_components.page_setting import PagePanel


class FilterableDataTable:
    def __init__(self, df, columns_config, page=None, page_panel=None, page_size=15, hidden_columns=None,
                 on_selection_change=None, page_type=None, page_id=None, search_field=None):
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

        self._is_initialized = False

        self.original_df = df.copy()
        self.filtered_df = df.copy()
        self.columns_config = columns_config
        self.filter_settings = {}
        self.page = page
        # self.page_panel = page_panel
        self.page_size = page_size  # Размер страницы

        self.search_term = ""  # Новое поле для хранения поискового запроса
        self.search_field = search_field
        self.search_df = df.copy()

        self.on_selection_change = on_selection_change

        self.current_page = 0  # Текущая страница
        self.total_pages = max(1, len(df) // page_size + (len(df) % page_size > 0))  # Общее количество страниц

        self.first_page_button = None
        self.prev_page_button = None
        self.page_number_field = None
        self.next_page_button = None
        self.last_page_button = None

        self.selected_rows = set()

        self.selection_count_text = ft.Text(
            "0",
            size=14,
            color=colors.BLUE_GREY_700
        )

        self.selection_count_indicator = ft.Row([
            ft.Text("Выделено строк: ", size=14, color=colors.BLUE_GREY_700),
            self.selection_count_text,

        ])

        self.filter_indicator = ft.Text(
            "Примененные фильтры:\n",
            size=14,
            color=colors.BLUE_GREY_700
        )

        self.data_table = DataTable(
            columns=[],
            border_radius=10,
            border=ft.border.all(3, colors.BLUE_200),
            vertical_lines=border.BorderSide(2, colors.BLUE_200),
            horizontal_lines=border.BorderSide(2, colors.BLUE_200),
            heading_row_color=colors.BLUE_50,
            heading_row_height=40,
            data_row_max_height=float("inf"),
            data_row_min_height=40,
            column_spacing=32,
            divider_thickness=0,
            expand=True,
            # show_checkbox_column=True
        )

        self.column_visibility = {col_name: True for col_name in self.columns_config}

        if hidden_columns:
            for col in hidden_columns:
                if col in self.column_visibility:
                    self.column_visibility[col] = False

        self._setup_columns()

        self._update_table()

        self.selection_count_indicator.visible = False
        self.filter_indicator.visible = False

        self.page_panel = None
        self.page_type = page_type
        self._init_page_panel()

        self._load_initial_settings()

    def _init_page_panel(self):
        if self.page and not self.page_panel:
            self.page_panel = PagePanel(
                page=self.page,
                page_type=self.page_type,
                search_field=self.search_field
            )
            self.page_panel.set_table(self)
            # self.page_panel.update_filter_details({
            #     **self.filter_settings,
            #     "_search": {"value": self.search_term} if self.search_term else {}
            # })

    def show_filters(self):
        if not self.page_panel:
            self._init_page_panel()

        self.page_panel.update_filter_details({
            **self.filter_settings,
            "_search": {"value": self.search_term} if self.search_term else {}
        })
        self.page_panel.show()

    def _load_initial_settings(self):
        """Загружает начальные настройки с улучшенной обработкой ошибок"""
        try:
            if not self.page_type:
                return

            saved_state = TableStateManager.load_state(self.page_type)
            if not saved_state:
                return

            if saved_state:
                self.filter_settings = saved_state.get('filters', {})
                visible_columns = saved_state.get('visible_columns', [])

                for col in self.column_visibility:
                    self.column_visibility[col] = col in visible_columns

                self._setup_columns()

                # self.search_term = saved_state.get('search_term', '')

            if self.search_term:
                self.apply_search_filter(self.search_term)


            # if self.page_panel:
            #     self.page_panel.update_filter_details({
            #         **self.filter_settings,
            #         "_search": {"value": self.search_term} if self.search_term else {}
            #     })

            if self.page:
                self.page.update()

            if self._is_initialized:
                self._apply_filters()
                self._safe_update_table()
        except Exception as e:
            print(f"Ошибка загрузки настроек: {str(e)}")
            # self.filter_settings = {}

    def save_current_settings(self):
        """Сохраняет текущие настройки таблицы"""
        if not self.page_type:
            return
        visible_columns = [col for col, visible in self.column_visibility.items() if visible]
        state = {
            'visible_columns': visible_columns,
            'filters': self.filter_settings.copy()
        }

        TableStateManager.save_state(self.page_type, state)

    def _handle_row_click(self, row_idx):
        if row_idx in self.selected_rows:
            self.selected_rows.remove(row_idx)
        else:
            self.selected_rows.add(row_idx)

        self._update_selection_count_indicator()
        self._update_table()

        if self.on_selection_change:
            self.on_selection_change(self.selected_rows)

    def _handle_cell_hover(self, e, idx):
        e.control.border = (
            ft.border.all(1, colors.BLUE_300)
            if e.data == "true"
            else ft.border.all(1, colors.TRANSPARENT)
        )
        e.control.update()

    def set_page(self, page):
        if not page:
            return self
        self.page = page
        try:
            if not self._is_initialized:
                # Убираем прямое добавление элементов в page
                if self.page_panel and self.page_panel.panel not in page.overlay:
                    page.overlay.append(self.page_panel.panel)
                    self.page_panel.panel.visible = False

                self._is_initialized = True

            if not hasattr(self, '_settings_loaded'):
                self._load_initial_settings()
                self._settings_loaded = True

            if self.page_panel:
                self.page_panel.update_filter_details({
                    **self.filter_settings,
                    "_search": {"value": self.search_term} if self.search_term else {}
                })
        except Exception as e:
            print(f"Error adding controls to page: {e}")

        return self

    def _setup_columns(self):
        self.data_table.columns.clear()

        self.select_all_checkbox = Checkbox(
            tristate=True,
            value=False,
            on_change=self._toggle_select_all_header
        )

        self.selection_count_text = Text(
            f"0",
            color=colors.BLUE_GREY_700,
            size=18
        )

        self.data_table.columns.append(
            DataColumn(Row([
                self.select_all_checkbox,
                self.selection_count_text
            ], alignment=MainAxisAlignment.CENTER))
        )

        for col_name, config in self.columns_config.items():
            if self.column_visibility[col_name]:
                self.data_table.columns.append(
                    DataColumn(
                        Row([
                            Text(col_name, weight=FontWeight.BOLD),
                            self._create_column_menu(col_name, config['type'])
                        ])
                    )
                )

    def _create_column_menu(self, column_name, column_type):
        def open_filter(e):
            self._open_filter_dialog(column_name)

        def sort_asc(e):
            self._sort_data(column_name, ascending=True)

        def sort_desc(e):
            self._sort_data(column_name, ascending=False)

        return PopupMenuButton(
            icon=icons.FILTER_LIST,
            items=[
                PopupMenuItem(
                    text="Сортировка ↑" if column_type in ['numeric', 'date'] else "Сортировка А-Я",
                    on_click=sort_asc,
                ),
                PopupMenuItem(
                    text="Сортировка ↓" if column_type in ['numeric', 'date'] else "Сортировка Я-А",
                    on_click=sort_desc,
                ),
                PopupMenuItem(
                    text="Содержит",
                    on_click=lambda e, col=column_name: self._open_contains_filter(e, col)
                ),
                PopupMenuItem(
                    text="Не содержит",
                    on_click=lambda e, col=column_name: self._open_does_not_contain_filter(e, col)
                ),
                PopupMenuItem(
                    text="Фильтр",
                    on_click=open_filter,
                ),
            ],
        )

    def get_selected_rows(self):
        """Возвращает выделенные строки"""
        return self.selected_rows

    def get_selected_items(self):
        """Возвращает список выбранных элементов с данными"""
        return [row for row in self.filtered_data if row.get('_selected')]

    def get_selected_ids(self):
        """Возвращает список ID выделенных строк"""
        if not self.selected_rows:
            return []

        # Для DataFrame индексы могут быть разными, поэтому лучше работать с данными
        ids = []
        for row in self.selected_rows:
            if isinstance(row, dict) and 'ID' in row:
                ids.append(row['ID'])
            elif isinstance(row, (int, str)):
                ids.append(row)
        return ids

    def _sort_data(self, column_name, ascending=True):
        self.filtered_df = self.filtered_df.sort_values(by=column_name, ascending=ascending)
        # self.save_current_settings()
        self._update_table()

    def _update_table(self):
        # Clear existing rows
        if not self._is_initialized:
            return

        self.data_table.rows.clear()

        # Ensure total_pages is calculated even if filtered_df is empty
        total_rows = len(self.filtered_df)
        self.total_pages = max(1, total_rows // self.page_size + (total_rows % self.page_size > 0))
        self.current_page = min(max(0, self.current_page), self.total_pages - 1)

        # Вычисляем индексы для текущей страницы
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size

        def smart_wrap_text(text, max_length=20):
            """
            Интеллектуальный перенос текста с учетом длинных слов и разделителей
            """
            # Если текст короче max_length, возвращаем его как есть
            if len(text) <= max_length:
                return [text]

            # Разбиваем текст на слова и специальные символы
            import re
            tokens = re.findall(r'\w+|[^\w\s]', text)

            lines = []
            current_line = ""

            for token in tokens:
                # Если добавление токена не превышает лимит
                if len(current_line) + len(token) + 1 <= max_length:
                    current_line += (" " + token if current_line else token)
                else:
                    # Сохраняем текущую строку и начинаем новую
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = token

            # Добавляем последнюю строку
            if current_line:
                lines.append(current_line.strip())

            return lines

        # Итерируемся только по строкам текущей страницы
        page_data = self.filtered_df.iloc[start_idx:end_idx]
        for global_idx, row in page_data.iterrows():
            cells = []

            checkbox = Checkbox(
                value=global_idx in self.selected_rows,
                data=global_idx,
                on_change=lambda e, row_idx=global_idx: self._toggle_row_selection(e, row_idx)
            )
            cells.append(DataCell(checkbox))

            for col_name in self.columns_config:
                if self.column_visibility[col_name]:
                    value = row[col_name]

                    if pd.isna(value):
                        cell_content = Text("")
                    elif isinstance(value, (pd.Timestamp, datetime)):
                        try:
                            cell_content = Text(value.strftime("%d-%m-%Y") if pd.notna(value) else "")
                        except (AttributeError, ValueError):
                            cell_content = Text("")
                    elif isinstance(value, (float, int)):  # Обработка числовых значений
                        if isinstance(value, float) and value.is_integer():  # Проверка на целое число
                            value = int(value)
                        else:
                            value = value  # Преобразуем к целому для отображения
                        wrapped_text = smart_wrap_text(str(value), max_length=20)
                        cell_content = Column(
                            controls=[
                                Text(line, size=12) for line in wrapped_text
                            ],
                            spacing=2

                        )
                    else:
                        # Преобразуем значение в строку и применяем умный перенос
                        wrapped_text = smart_wrap_text(str(value), max_length=20)
                        cell_content = Column(
                            controls=[
                                Text(line, size=12) for line in wrapped_text
                            ],
                            spacing=2,
                        )

                    cells.append(DataCell(cell_content))

            if cells:
                row_obj = DataRow(
                    cells=cells,
                    color=colors.BLUE_GREY_50 if global_idx in self.selected_rows else colors.WHITE,
                    on_select_changed = lambda e, idx=global_idx: self._handle_row_click(idx)
                )
                self.data_table.rows.append(row_obj)

        # Trigger data table update
        try:
            if self.page and self.data_table in self.page.controls:
                self.data_table.update()
        except Exception as e:
            print(f"Error updating data table: {e}")

        # Update selection count
        self._update_selection_count_indicator()

    def get_button_style(self, disabled):
        return ButtonStyle(
            color=colors.BLUE_600 if not disabled else colors.GREY_400,
            shape=ft.CircleBorder(),
        )

    def add_pagination_controls(self):
        self.first_page_button = ft.IconButton(
            icon=ft.icons.FIRST_PAGE,
            on_click=lambda _: self._go_to_page(0),
            style=self.get_button_style(self.current_page == 0),
            disabled=self.current_page == 0,
            icon_size=20
        )

        self.prev_page_button = ft.IconButton(
            icon=ft.icons.ARROW_BACK,
            on_click=self._prev_page,
            style=self.get_button_style(self.current_page == 0),
            disabled=self.current_page == 0,
            icon_size=20
        )

        # Поле ввода страницы
        self.page_number_field = ft.TextField(
            value=str(self.current_page + 1),
            width=60,
            text_size=14,
            text_align=ft.TextAlign.CENTER,
            on_submit=self._on_page_input,
            input_filter=ft.NumbersOnlyInputFilter(),
            border_color=colors.BLUE_600,
            focused_border_color=colors.BLUE_800,
        )

        self.next_page_button = ft.IconButton(
            icon=ft.icons.ARROW_FORWARD,
            on_click=self._next_page,
            style=self.get_button_style(self.current_page >= self.total_pages - 1),
            disabled=self.current_page >= self.total_pages - 1,
            icon_size=20
        )

        self.last_page_button = ft.IconButton(
            icon=ft.icons.LAST_PAGE,
            on_click=lambda _: self._go_to_page(self.total_pages - 1),
            style=self.get_button_style(self.current_page >= self.total_pages - 1),
            disabled=self.current_page >= self.total_pages - 1,
            icon_size=20
        )

        # Информация о страницах
        self.page_info_text = ft.Text(
            f"из {self.total_pages}",
            size=14,
            color=colors.GREY_600
        )

        # Собираем панель
        pagination_row = ft.Row([
            self.first_page_button,
            self.prev_page_button,
            ft.Container(
                content=self.page_number_field,
                border_radius=8,
                border=ft.border.all(1, colors.BLUE_300),
            ),
            self.page_info_text,
            self.next_page_button,
            self.last_page_button
        ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )

        # Контейнер с фоном и тенью
        return ft.Container(
            content=pagination_row,
            border_radius=12,
            bgcolor=colors.WHITE,
        )

    def _go_to_page(self, page_number):
        if 0 <= page_number < self.total_pages:
            self.current_page = page_number
            self._update_pagination_controls()
            self._update_table()

    def _on_page_input(self, e):
        try:
            page = int(self.page_number_field.value) - 1
            if 0 <= page < self.total_pages:
                self._go_to_page(page)
            else:
                self.page_number_field.value = str(self.current_page + 1)
                self.page_number_field.update()
        except ValueError:
            self.page_number_field.value = str(self.current_page + 1)
            self.page_number_field.update()

    def _update_pagination_controls(self):
        # Проверяем инициализацию элементов
        if not all([self.first_page_button, self.prev_page_button,
                    self.next_page_button, self.last_page_button]):
            return

        # Обновляем состояния кнопок с проверкой атрибутов
        if hasattr(self.first_page_button, 'disabled'):
            self.first_page_button.disabled = self.current_page == 0
            self.first_page_button.style = self.get_button_style(self.current_page == 0)

        if hasattr(self.prev_page_button, 'disabled'):
            self.prev_page_button.disabled = self.current_page == 0
            self.prev_page_button.style = self.get_button_style(self.current_page == 0)

        if hasattr(self.next_page_button, 'disabled'):
            self.next_page_button.disabled = self.current_page >= self.total_pages - 1
            self.next_page_button.style = self.get_button_style(self.current_page >= self.total_pages - 1)

        if hasattr(self.last_page_button, 'disabled'):
            self.last_page_button.disabled = self.current_page >= self.total_pages - 1
            self.last_page_button.style = self.get_button_style(self.current_page >= self.total_pages - 1)

        # Обновляем текстовые поля
        if hasattr(self.page_number_field, 'value'):
            self.page_number_field.value = str(self.current_page + 1)
            self.page_number_field.update()

        if hasattr(self.page_info_text, 'value'):
            self.page_info_text.value = f"из {self.total_pages}"
            self.page_info_text.update()

        # Обновляем отображение
        self.page_number_field.update()
        self.page_info_text.update()
        self.first_page_button.update()
        self.prev_page_button.update()
        self.next_page_button.update()
        self.last_page_button.update()

    def _prev_page(self, e=None):
        if self.current_page > 0:
            self.current_page -= 1
            self.force_update()

    def _next_page(self, e=None):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.force_update()

    def force_update(self):
        if hasattr(self, 'page') and self.page:
            # Update pagination controls
            self.total_pages = max(1, len(self.filtered_df) // self.page_size + (
                    len(self.filtered_df) % self.page_size > 0))

            self._update_pagination_controls()
            # Update the table
            self._update_table()
            # Trigger page update
            self.page.update()

    def _show_column_manager(self, e):
        def update_indicator(col_name):
            visible_columns_count = sum(self.column_visibility.values())
            return self.column_visibility[col_name] and visible_columns_count == 1

        def on_checkbox_change(e, col_name):
            self.column_visibility[col_name] = e.control.value

            self._setup_columns()
            self._update_table()

            if hasattr(self, 'page'):
                # for child in self.filter_details_column.controls:
                #     if isinstance(child, ft.Checkbox):  # Проверяем тип элемента
                #         child.disabled = sum(self.column_visibility.values()) == 1 and child.value
                self.page.update()

            for checkbox in checkboxes.controls:
                checkbox.disabled = update_indicator(checkbox.label)

            dialog.content.update()
            self.save_current_settings()

        def on_search_change(e):
            search_query = e.control.value.lower()
            filtered_checkboxes = [
                checkbox for checkbox in all_checkboxes
                if search_query in checkbox.label.lower()
            ]
            checkboxes.controls = filtered_checkboxes
            dialog.content.update()

        def toggle_select_all(e):
            select_all = e.control.value
            for checkbox in all_checkboxes:
                checkbox.value = select_all
                self.column_visibility[checkbox.label] = select_all
            checkboxes.controls = [checkbox for checkbox in all_checkboxes if not checkboxes.disabled]
            dialog.content.update()
            self._setup_columns()
            self._update_table()
            if hasattr(self, 'page'):
                self.page.update()
            self.save_current_settings()

        all_checkboxes = []
        for col_name in self.columns_config:
            checkbox = ft.Checkbox(
                label=col_name,
                value=self.column_visibility[col_name],
                on_change=lambda e, col=col_name: on_checkbox_change(e, col),
                disabled=update_indicator(col_name)
            )
            all_checkboxes.append(checkbox)

        select_all_checkbox = ft.Checkbox(
            label="Выделить все",
            value=all(checkbox.value for checkbox in all_checkboxes),
            on_change=toggle_select_all
        )

        # Создаем поле поиска
        search_field = ft.TextField(
            label="Поиск...",
            width=200,
            on_change=on_search_change
        )

        checkboxes = ft.Column(all_checkboxes, scroll=ft.ScrollMode.AUTO)

        dialog = AlertDialog(
            title=ft.Text("Управление столбцами"),
            content=ft.Column([
                ft.Row([search_field, select_all_checkbox]),
                checkboxes
            ],
                scroll=ft.ScrollMode.AUTO,
                width=400,
                height=500
            ),
            actions=[
                ft.TextButton("Закрыть", on_click=lambda e: self._close_dialog(dialog))
            ]
        )

        if dialog not in getattr(self, 'page', None).overlay:
            getattr(self, 'page', None).overlay.append(dialog)
        dialog.open = True
        if hasattr(self, 'page'):
            self.page.update()

    def _open_contains_filter(self, e, column_name):
        saved_filter = self.filter_settings.get(column_name, {})
        current_value = saved_filter.get("value", "")

        input_field = ft.TextField(
            label="Введите текст для поиска",
            value=current_value)

        dialog = ft.AlertDialog(
            title=ft.Text(f"Выборка строк, для столбца '{column_name}'"),
            content=ft.Column([
                input_field
            ], height=self.page.window.height * 0.1, width=self.page.window.width * 0.15,
                alignment=ft.alignment.center),
            actions=[
                ft.TextButton("Применить",
                              on_click=lambda _: self._apply_text_filter(column_name, input_field.value,
                                                                         "contains", dialog)),
                ft.TextButton("Отмена", on_click=lambda e: self._close_dialog(dialog)),

            ],
            on_dismiss=lambda e: None
        )
        self.page.open(dialog)
        self.page.update()

    def _open_does_not_contain_filter(self, e, column_name):
        saved_filter = self.filter_settings.get(column_name, {})
        current_value = saved_filter.get("value", "")

        input_field = ft.TextField(
            label="Введите текст для поиска",
            value=current_value)

        dialog = ft.AlertDialog(
            title=ft.Text(f"Исключение строк, для столбца '{column_name}'"),
            content=ft.Column([
                input_field
            ], height=self.page.window.height * 0.1, width=self.page.window.width * 0.15,
                alignment=ft.alignment.center),
            actions=[
                ft.TextButton("Применить",
                              on_click=lambda _: self._apply_text_filter(column_name, input_field.value,
                                                                         "does_not_contain", dialog)),
                ft.TextButton("Отмена", on_click=lambda e: self._close_dialog(dialog)),

            ],
            on_dismiss=lambda e: None
        )
        self.page.open(dialog)
        self.page.update()

    def _apply_text_filter(self, column_name, text_value, filter_type, dialog):
        if not text_value.strip():
            # Удаляем текущий текстовый фильтр, если он есть
            if column_name in self.filter_settings:
                del self.filter_settings[column_name]
        else:
            self.filter_settings[column_name] = {
                "type": filter_type,
                "value": text_value.strip()
            }
        self._apply_filters()
        self._close_dialog(dialog)
        self.force_update()

    async def _apply_filters_async(self):
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._apply_filters)
            self.current_page = 0  # Сбрасываем на первую страницу
            # if hasattr(self, 'select_all_checkbox'):
            #     self.select_all_checkbox.value = False
            # self.save_current_settings()
            if self.page_panel:
                self.page_panel.update_filter_details({
                    **self.filter_settings,
                    "_search": {"value": self.search_term} if self.search_term else {}
                })
            self.force_update()
        except Exception as e:
            print(f"Filter error: {str(e)}")

    # def _apply_filters(self):
    #     df = self.original_df.copy()
    #
    #     for column_name, settings in self.filter_settings.items():
    #         if column_name not in self.columns_config:
    #             continue
    #
    #         mask = pd.Series(True, index=df.index)
    #         df_col = df[column_name]
    #         col_type = self.columns_config[column_name]['type']
    #         include_empty = settings.get('include_empty', False)
    #
    #         # Преобразование столбца дат в datetime
    #         if col_type == 'date':
    #             start_date_str = settings.get('start_date', '')
    #             end_date_str = settings.get('end_date', '')
    #             selected_values = settings.get('selected_values', [])
    #             include_empty = settings.get('include_empty', False)
    #
    #             # Парсим даты
    #             start_date = pd.to_datetime(start_date_str, errors='coerce') if start_date_str else None
    #             end_date = pd.to_datetime(end_date_str, errors='coerce') if end_date_str else None
    #
    #             condition = pd.Series(True, index=df.index)
    #
    #             # Применяем диапазон дат
    #             if start_date or end_date:
    #                 if start_date:
    #                     condition &= (df_col >= start_date)
    #                 if end_date:
    #                     condition &= (df_col <= end_date + pd.Timedelta(days=1))  # Включаем весь последний день
    #
    #             # Применяем выбранные даты
    #             if selected_values:
    #                 valid_dates = []
    #                 for v in selected_values:
    #                     dt = pd.to_datetime(v, errors='coerce')
    #                     if not pd.isnull(dt):
    #                         valid_dates.append(dt)
    #                 if valid_dates:
    #                     condition &= df_col.isin(valid_dates)
    #
    #             # Включаем пустые значения
    #             if include_empty:
    #                 condition |= df_col.isna()
    #
    #             df = df[condition]
    #         elif col_type == 'numeric':
    #             try:
    #                 selected_numbers = [float(v) for v in selected_values]
    #                 condition = df_col.isin(selected_numbers)
    #             except Exception as e:
    #                 condition = pd.Series(False, index=self.filtered_df.index)
    #
    #             min_val = float(settings.get("min_value")) if settings.get("min_value") else None
    #             max_val = float(settings.get("max_value")) if settings.get("max_value") else None
    #
    #             range_condition = pd.Series(True, index=self.filtered_df.index)
    #             if min_val is not None:
    #                 range_condition &= (df_col >= min_val)
    #             if max_val is not None:
    #                 range_condition &= (df_col <= max_val)
    #             value_condition = condition & range_condition
    #
    #             df = df[value_condition]
    #
    #
    #         # Основная логика фильтрации
    #         condition = pd.Series(True, index=df.index)
    #
    #         if 'type' in settings and settings['type'] in ['contains', 'does_not_contain']:
    #             value = settings.get('value', '')
    #             if value:
    #                 if settings['type'] == 'contains':
    #                     condition = df_col.astype(str).str.contains(value, case=False, na=False)
    #                 else:
    #                     condition = ~df_col.astype(str).str.contains(value, case=False, na=False)
    #
    #         elif 'selected_values' in settings:
    #             selected_values = settings.get('selected_values', [])
    #             include_empty = settings.get('include_empty', False)
    #
    #             value_condition = df_col.isin(selected_values)
    #
    #             if include_empty:
    #                 empty_condition = df_col.isna() | (df_col == "")
    #                 value_condition |= empty_condition
    #
    #             condition = value_condition
    #
    #         if include_empty:
    #             empty_condition = df_col.isna() | (df_col == "")
    #             value_condition |= empty_condition
    #
    #         # self.filtered_df = self.filtered_df[value_condition]
    #         # df = df.loc[mask]
    #         df = df[condition]
    #
    #     if self.search_term:
    #         search_mask = df.astype(str).apply(
    #             lambda x: x.str.lower().str.contains(self.search_term)
    #         ).any(axis=1)
    #         df = df.loc[search_mask]
    #
    #     self.filtered_df = df
    #     self.selected_rows.clear()
    #     self.current_page = 0
    #     self.total_pages = max(1, len(self.filtered_df) // self.page_size)
    #
    #     self._safe_update_table()
    #     self.save_current_settings()
    #
    #     if self.page:
    #         self.page.update()
    #
    #     if self.page_panel:
    #         self.page_panel.update_filter_details({
    #             **self.filter_settings,
    #             "_search": {"value": self.search_term} if self.search_term else {}
    #         })

    def _apply_filters(self):
        df = self.original_df.copy()

        # Применяем фильтры для каждой колонки
        for column_name, settings in self.filter_settings.items():
            if column_name not in self.columns_config:
                continue

            col_type = self.columns_config[column_name]['type']
            df_col = df[column_name]
            include_empty = settings.get('include_empty', False)
            condition = pd.Series(True, index=df.index)

            # Фильтрация для дат
            if col_type == 'date':
                # Диапазон дат
                start_date = pd.to_datetime(settings.get('start_date'), errors='coerce')
                end_date = pd.to_datetime(settings.get('end_date'), errors='coerce')

                if not pd.isnull(start_date):
                    condition &= (df_col >= start_date)
                if not pd.isnull(end_date):
                    condition &= (df_col <= end_date + pd.Timedelta(days=1))

                # Выбранные даты
                selected_dates = pd.to_datetime(settings.get('selected_values', []), errors='coerce')
                if not selected_dates.empty:
                    date_condition = df_col.isin(selected_dates)
                    condition &= date_condition

            # Фильтрация для чисел
            elif col_type == 'numeric':
                # Диапазон значений
                try:
                    min_val = float(settings['min_value']) if settings.get('min_value') else None
                    max_val = float(settings['max_value']) if settings.get('max_value') else None

                    if min_val is not None:
                        condition &= (df_col >= min_val)
                    if max_val is not None:
                        condition &= (df_col <= max_val)
                except:
                    pass

                # Выбранные значения
                selected_numbers = []
                for v in settings.get('selected_values', []):
                    try:
                        selected_numbers.append(float(v))
                    except:
                        continue
                if selected_numbers:
                    condition &= df_col.isin(selected_numbers)
                else:
                    condition &= pd.Series(False, index=df.index)

            # Фильтрация для категорий и текста
            else:
                selected_values = settings.get('selected_values', [])
                filter_type = settings.get('type')
                filter_value = settings.get('value', '').lower()

                # Базовое условие
                condition = pd.Series(True, index=df.index)

                # Применяем selected_values
                if selected_values:
                    condition &= df_col.isin(selected_values)
                else:
                    condition &= pd.Series(False, index=df.index)

                # Применяем текстовый фильтр (contains/does_not_contain)
                if filter_type in ['contains', 'does_not_contain'] and filter_value:
                    contains_condition = df_col.astype(str).str.lower().str.contains(filter_value, na=False)
                    if filter_type == 'contains':
                        condition &= contains_condition
                    else:
                        condition &= ~contains_condition

                # if selected_values:
                #     condition &= df_col.isin(selected_values)
                # else:
                #     condition &= pd.Series(False, index=df.index)
                #
                # # Фильтр по подстроке
                # if 'type' in settings and settings['type'] == 'contains':
                #     search_text = settings.get('value', '').lower()
                #     if search_text:
                #         condition &= df_col.astype(str).str.lower().str.contains(search_text, na=False)
                # elif 'type' in settings and settings['type'] == 'does_not_contain':
                #     search_text = settings.get('value', '').lower()
                #     if search_text:
                #         condition &= ~df_col.astype(str).str.lower().str.contains(search_text, na=False)

                # Учет пустых значений
                if include_empty:
                    condition |= df_col.isna() | (df_col == "")

            # Применяем фильтр для колонки
            df = df[condition]

        # Глобальный поиск
        if self.search_term:
            search_mask = df.astype(str).apply(
                lambda x: x.str.lower().str.contains(self.search_term.lower(), na=False)
            ).any(axis=1)
            df = df[search_mask]

        # Обновляем состояние
        self.filtered_df = df
        self.current_page = 0
        self.total_pages = max(1, (len(self.filtered_df) + self.page_size - 1) // self.page_size)

        # Очищаем выделение и обновляем UI
        self.selected_rows.clear()
        self._safe_update_table()
        self.save_current_settings()

        if self.page:
            self.page.update()

        if self.page_panel:
            self.page_panel.update_filter_details({
                **self.filter_settings,
                "_search": {"value": self.search_term} if self.search_term else {}
            })

    def _safe_update_table(self):
        """Обновление таблицы с проверкой инициализации"""
        if self._is_initialized and self.page:
            try:
                self._update_table()
                self._update_pagination_controls()
                self.page.update()
            except Exception as e:
                print(f"Update error: {str(e)}")

    def perform_search(self, search_term):
        self.search_term = search_term.lower() if search_term else ""
        self._apply_filters()
        self.save_current_settings()

    def _reset_filters_full(self):
        """Полный сброс всех фильтров и поиска"""
        self.search_term = ""
        self.filter_settings.clear()
        self.selected_rows.clear()
        self.current_page = 0
        self._update_pagination_controls()

        if self.search_field:
            self.search_field.value = ""
        self.save_current_settings()

    def _open_filter_dialog(self, column_name):
        saved_state = TableStateManager.load_state(self.page_type) if self.page_type else None
        if saved_state:
            self.filter_settings = saved_state.get('filters', {})

        col_type = self.columns_config[column_name]['type']
        unique_values = []

        for v in self.original_df[column_name].dropna().unique():
            if pd.isna(v):
                continue
            if col_type == 'date':
                try:
                    if isinstance(v, (pd.Timestamp, datetime)):
                        unique_values.append(v.strftime('%Y-%m-%d'))
                    else:
                        unique_values.append(str(v))
                except:
                    unique_values.append(str(v))
            else:
                unique_values.append(str(v))

        saved_settings = self.filter_settings.get(column_name, {})
        saved_selected_values = saved_settings.get("selected_values", list(unique_values))

        if col_type == 'date':
            # Преобразуем сохраненные даты в список строк ISO формата
            saved_selected_values = [
                v.strftime('%Y-%m-%d')
                if isinstance(v, (pd.Timestamp, datetime)) else v
                for v in saved_selected_values
            ]

        checkboxes = []

        include_empty = saved_settings.get("include_empty", True)
        has_empty_values = self.original_df[column_name].isna().any() or (self.original_df[column_name] == "").any()

        checkboxes = []
        for value in unique_values:
            if pd.isna(value) or value == '':
                continue

            if col_type == 'date':
                display_label = pd.to_datetime(value).strftime("%d-%m-%Y")
                checkbox_value = value in map(str, saved_selected_values)
                checkboxes.append(
                    Checkbox(
                        label=display_label,
                        value=checkbox_value,
                        visible=True,
                        data=value  # Сохраняем в ISO-формате
                    )
                )

            else:
                try:
                    if isinstance(value, float) and value.is_integer():
                        display_label = str(int(value))  # Целое число
                    elif isinstance(value, (pd.Timestamp, datetime)):
                        display_label = value.strftime("%d-%m-%Y")  # Дата в формате дд-мм-гггг
                    else:
                        display_label = str(value)  # Строки или другие типы
                except Exception as e:
                    display_label = str(value)  # Если что-то пошло не так — используем raw строку

                # Проверяем, было ли значение выбрано ранее
                checkbox_value = str(value) in [str(v) for v in saved_selected_values]

                # Создаем чекбокс для текущего value
                checkboxes.append(
                    Checkbox(
                        label=display_label,
                        value=checkbox_value,
                        visible=True,
                        data=value  # Хранит оригинальное значение для фильтрации
                    )
                )

        select_all_checkbox = Checkbox(
            label="Выделить все",
            value=all(checkbox.value for checkbox in checkboxes),
            visible=True,
            on_change=lambda e: self._toggle_select_all(e, checkboxes),
        )

        select_search_results_checkbox = Checkbox(
            label="Выделить все результаты поиска",
            value=True,
            visible=False,
            on_change=lambda e: self._toggle_search_results(e, checkboxes),
        )

        search_field = TextField(
            label="Поиск...",
            on_change=lambda e, col=column_name: self._handle_search(
                e, checkboxes, select_all_checkbox,
                select_search_results_checkbox
            ),
        )

        date_range_fields = []
        number_range_fields = []

        if col_type == 'date':
            start_date_val = saved_settings.get("start_date", "")
            end_date_val = saved_settings.get("end_date", "")
            selected_values = saved_settings.get("selected_values", [])

            def format_date(date_str):
                if not date_str:
                    return ""
                date_part = date_str.split('T')[0] if 'T' in date_str else date_str
                try:
                    dt = datetime.strptime(date_part, "%Y-%m-%d")
                    return dt.strftime("%d-%m-%Y")
                except ValueError:
                    return ""

            start_date_display = format_date(start_date_val)
            end_date_display = format_date(end_date_val)

            start_date_field = TextField(
                label="Начальная дата",
                read_only=True,
                expand=True,
                value=pd.to_datetime(start_date_val).strftime("%d-%m-%Y")
                if start_date_val and pd.to_datetime(start_date_val, errors='coerce')
                else "",
                data=start_date_val
            )

            end_date_field = TextField(
                label="Конечная дата",
                read_only=True,
                expand=True,
                value=pd.to_datetime(end_date_val).strftime("%d-%m-%Y")
                if end_date_val and pd.to_datetime(end_date_val, errors='coerce')
                else "",
                data=end_date_val
            )

            start_date_picker = DatePicker(
                value=pd.to_datetime(start_date_val) if start_date_val else None,
                last_date=datetime.now().replace(year=datetime.now().year + 1),
                on_change=lambda e: self._on_date_change(e, start_date_picker, start_date_field),
                date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR,
                date_picker_mode=ft.DatePickerMode.DAY
            )
            end_date_picker = DatePicker(
                value=pd.to_datetime(end_date_val) if end_date_val else None,
                last_date=datetime.now().replace(year=datetime.now().year + 1),
                on_change=lambda e: self._on_date_change(e, end_date_picker, end_date_field),
                date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR,
                date_picker_mode=ft.DatePickerMode.DAY
            )

            date_range_fields = [
                Row([
                    Text("Диапазон дат:"),
                    start_date_field,
                    IconButton(icon=icons.CALENDAR_TODAY,
                               on_click=lambda _: self._show_date_picker(_, start_date_picker)),
                    end_date_field,
                    IconButton(icon=icons.CALENDAR_TODAY, on_click=lambda _: self._show_date_picker(_, end_date_picker))
                ])
            ]

            if start_date_picker not in getattr(self, 'page', None).overlay:
                getattr(self, 'page', None).overlay.append(start_date_picker)
            if end_date_picker not in getattr(self, 'page', None).overlay:
                getattr(self, 'page', None).overlay.append(end_date_picker)

        elif col_type == 'numeric':
            min_value = self.filter_settings.get(column_name, {}).get("min_value")
            max_value = self.filter_settings.get(column_name, {}).get("max_value")

            min_value_field = TextField(
                label="Минимальное значение",
                value=str(min_value) if min_value is not None else "",
                expand=True,
                input_filter=ft.InputFilter(
                    allow=True,
                    regex_string=r"^-?\d*\.?\d*$",  # Разрешаем только числа
                    replacement_string=""
                )
            )

            max_value_field = TextField(
                label="Максимальное значение",
                value=str(max_value) if max_value is not None else "",
                expand=True,
                input_filter=ft.InputFilter(
                    allow=True,
                    regex_string=r"^-?\d*\.?\d*$",
                    replacement_string=""
                )
            )

            number_range_fields = [
                Row([Text("Диапазон значений:"), min_value_field, max_value_field])
            ]

        empty_checkbox = Checkbox(label="Пустые", value=include_empty, visible=has_empty_values)

        async def apply_filter(e):
            selected_values = [checkbox.data for checkbox in checkboxes if checkbox.value and checkbox.visible]
            include_empty = empty_checkbox.value if empty_checkbox.visible else False

            if col_type == 'date':
                start_date_str = start_date_field.data if start_date_field.data else ""
                end_date_str = end_date_field.data if end_date_field.data else ""
                self.filter_settings[column_name] = {
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "selected_values": selected_values,
                    "include_empty": include_empty
                }

            elif col_type == 'numeric':
                min_value = min_value_field.value.strip()
                max_value = max_value_field.value.strip()

                try:
                    min_val = float(min_value) if min_value else None
                except ValueError:
                    min_val = None

                try:
                    max_val = float(max_value) if max_value else None
                except ValueError:
                    max_val = None

                    # Корректировка min/max
                if min_val is not None and max_val is not None and min_val > max_val:
                    min_val, max_val = max_val, min_val

                self.filter_settings[column_name] = {
                    "min_value": min_value,
                    "max_value": max_value,
                    "selected_values": selected_values,
                    "include_empty": include_empty
                }

                print(f"Numeric filter settings for {column_name}:",
                      self.filter_settings[column_name])

            else:
                self.filter_settings[column_name] = {
                    "selected_values": selected_values,
                    "include_empty": include_empty
                }

            await self._apply_filters_async()
            dialog.open = False

            if hasattr(self, 'page'):
                self.page.update()

        dialog = AlertDialog(
            title=Text(f"Фильтр: {column_name}"),
            content=Column(
                date_range_fields + number_range_fields + [
                    search_field,
                    select_all_checkbox,
                    select_search_results_checkbox,
                    empty_checkbox,
                    Container(
                        content=Column(checkboxes, scroll=ScrollMode.AUTO),
                        height=200,
                        expand=True,
                    ),
                ],
                width=600,
                height=500
            ),
            actions=[
                ft.TextButton("Применить", on_click=apply_filter),
                ft.TextButton("Отмена", on_click=lambda e: self._close_dialog(dialog)),
            ],
        )

        if dialog not in getattr(self, 'page', None).overlay:
            getattr(self, 'page', None).overlay.append(dialog)

        dialog.open = True

        if hasattr(self, 'page'):
            self.page.update()

    def _toggle_select_all(self, e, checkboxes):
        new_value = e.control.value
        for checkbox in checkboxes:
            checkbox.value = new_value
        self.page.update()

    def _toggle_search_results(self, e, checkboxes):
        new_value = e.control.value
        for checkbox in checkboxes:
            if checkbox.visible:
                checkbox.value = new_value
        self.page.update()

    def _toggle_column_visibility(self, e, column_name):
        self.column_visibility[column_name] = e.control.value
        self._setup_columns()
        self._update_table()
        self.save_current_settings()
        if hasattr(self, 'page'):
            self.page.update()

    def _handle_search(self, e, checkboxes, select_all, select_search):
        search_term = e.control.value.strip().lower()
        visible_count = 0
        for checkbox in checkboxes:
            match = search_term in checkbox.label.lower()
            checkbox.visible = match
            if match:
                visible_count += 1
                checkbox.value = True
        select_all.visible = not search_term
        select_search.visible = bool(search_term)
        if hasattr(self, 'page'):
            self.page.update()

    def _show_date_picker(self, e, picker):
        picker.cancel_text = "Отмена"
        picker.confirm_text = "Выбрать"
        picker.help_text = "Выберите дату"

        picker.open = True
        if hasattr(self, 'page'):
            self.page.update()

    def _on_date_change(self, e, picker, target_field):
        try:
            if picker.value:
                selected_date = picker.value
                machine_date = selected_date.strftime('%Y-%m-%d')
                display_date = selected_date.strftime('%d-%m-%Y')
                target_field.value = display_date
                target_field.data = machine_date
        except Exception as ex:
            print(f"Ошибка преобразования даты: {ex}")
            target_field.value = ""
            target_field.data = ""
        finally:
            if hasattr(self, 'page'):
                self.page.update()

    def _close_dialog(self, dialog):
        dialog.open = False
        self.save_current_settings()
        if hasattr(self, 'page'):
            self.page.update()

    # В классе FilterableDataTable
    def apply_search_filter(self, search_term):
        self.search_term = search_term.lower() if search_term else ""
        self._apply_filters()
        self.save_current_settings()
        # Затем применяем поиск к уже отфильтрованным данным
        if self.page_panel:
            self.page_panel.update_filter_details({
                **self.filter_settings,
                "_search": {"value": self.search_term} if self.search_term else {}
            })

        self.current_page = 0
        self._update_table()
        self._update_pagination_controls()

        if self.page:
            self.page.update()

    def _reset_filters(self, e=None):
        # Очищаем фильтры независимо от состояния поля поиска
        current_search = self.search_term

        # Полный сброс
        self.filter_settings.clear()
        self.selected_rows.clear()

        # Восстанавливаем поиск, если он был
        self.search_term = current_search

        # Применяем оставшиеся фильтры (только поиск, если он был)
        self._apply_filters()

        self.current_page = 0
        self.total_pages = max(1,
                               len(self.filtered_df) // self.page_size + (len(self.filtered_df) % self.page_size > 0))

        if hasattr(self, 'select_all_checkbox'):
            self.select_all_checkbox.value = False

        self._update_table()
        # self._update_filter_indicator()

        if self.on_selection_change:
            self.on_selection_change(self.selected_rows)

        # Обновляем пагинацию
        if hasattr(self, 'pagination_row'):
            self._update_pagination_controls()

        if hasattr(self, 'page_panel'):
            self.page_panel.update_filter_details(self.filter_settings)

        if self.page_panel:
            self.page_panel.hide()

        self.save_current_settings()

        if self.page:
            self.page.update()

    def full_reset(self):
        """Полный сброс таблицы"""
        self.filter_settings.clear()
        self.selected_rows.clear()
        self.current_page = 0
        if hasattr(self, 'select_all_checkbox'):
            self.select_all_checkbox.value = False
        self._update_table()
        # self._update_filter_indicator()
        self._update_selection_count_indicator()

    def _toggle_select_all_header(self, e):
        is_selected = e.control.value
        self.selected_rows.clear()

        for row in self.data_table.rows:
            row.cells[0].content.value = is_selected

        if is_selected:
            self.selected_rows = set(self.filtered_df.index.tolist())
        else:
            self.selected_rows.clear()

        self._update_table()
        self._update_selection_count_indicator()
        self.save_current_settings()

        if self.on_selection_change:
            self.on_selection_change(self.selected_rows)

    def _update_selection_count_indicator(self):
        if not self._is_initialized or not self.page:
            return

        count = len(self.selected_rows)
        self.selection_count_text.value = f"{count}"

        if self.selection_count_indicator.visible:
            self.selection_count_text.update()

        all_selected = len(self.selected_rows) == len(self.filtered_df)
        any_selected = len(self.selected_rows) > 0

        if all_selected:
            self.select_all_checkbox.value = True
        elif any_selected:
            self.select_all_checkbox.value = None
        else:
            self.select_all_checkbox.value = False

        # Обновляем цвета строк
        for row in self.data_table.rows:
            row_idx = row.cells[0].content.data
            row.color = colors.BLUE_GREY_50 if row_idx in self.selected_rows else colors.WHITE

        # Принудительно обновляем элементы
        if self.page:
            if self.selection_count_text.page is not None:
                self.selection_count_text.update()
            if self.select_all_checkbox.page is not None:
                self.select_all_checkbox.update()
            if self.data_table.page is not None:
                self.data_table.update()
            self.page.update()

    def _toggle_row_selection(self, e, row_idx):
        if e.control.value:
            self.selected_rows.add(row_idx)
        else:
            self.selected_rows.discard(row_idx)

        self._update_selection_count_indicator()

        if self.on_selection_change:
            self.on_selection_change(self.selected_rows)
