from datetime import datetime
import flet as ft
import pandas as pd
from src.ui.components.table_components.table_settings_manager import TableStateManager


class PagePanel:
    def __init__(self, page: ft.Page, table=None, page_type=None, page_id=None, search_field=None):
        self.page = page
        self.table = None
        if table is not None:
            table.page_panel = self

        if not hasattr(page, 'active_page_panels'):
            page.active_page_panels = []
        page.active_page_panels.append(self)

        # Colors
        self.red_primary = ft.colors.RED_500
        self.blue_primary = ft.colors.BLUE_500
        self.blue_background = ft.colors.BLUE_50

        # Filter tracking
        self.active_filters = []

        # Create UI components
        self.filter_details_column = ft.Column(
            expand=True,
            width=float("inf"),
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Примененные фильтры:", weight=ft.FontWeight.BOLD)
            ]
        )

        self.reset_filters_button = ft.ElevatedButton(
            content=ft.Text(value="Сбросить фильтры", size=13),
            bgcolor=self.red_primary,
            color=ft.colors.WHITE,
            on_click=self._reset_filters,
        )

        self.column_manager_button = ft.ElevatedButton(
            content=ft.Text(value="Управление столбцами", size=13),
            bgcolor=self.blue_primary,
            color=ft.colors.WHITE,
            on_click=self._show_column_manager
        )
        self.close_icon = ft.icons.CLOSE

        # Create panel
        self.panel = self._create_panel()
        self.is_visible = False
        self.original_on_resize = None

        def on_resize(e):
            self.panel.height = self.page.window.height * 0.965
            self.panel.width = self.page.window.width * 0.250
            self.page.update()

        self.page.on_resize = on_resize

        self.page_type = page_type
        self.page_id = page_id

        self.page = page
        self.table = table
        self.search_field = search_field

        self.page_type = page_type
        if self.table:
            self._load_initial_state()

        # if self.table and (self.table.filter_settings or self.table.search_term):
        #     self.show()

    def _load_initial_state(self):
        """Загружает сохраненное состояние при инициализации"""
        if self.table and self.table.page_type:
            saved_state = TableStateManager.load_state(self.table.page_type)
            if saved_state:
                # Обновляем фильтры в таблице
                try:
                    # if not self.table.filter_settings:
                    #     self.table.filter_settings = saved_state.get('filters', {})
                    # if not self.table.search_term:
                    #     self.table.search_term = saved_state.get('search', '')
                    #
                    # self.table._apply_filters()
                    #
                    # # Обновляем UI
                    # if self.page and self.panel in self.page.overlay:
                    #     self.update_filter_details({
                    #         **self.table.filter_settings,
                    #         "_search": {"value": self.table.search_term} if self.table.search_term else {}
                    #     })
                    #     if self.search_field and self.table.search_term:
                    #         self.search_field.value = self.table.search_term
                    #         self.search_field.update()
                    #
                    #     # Обновляем всю панель
                    #     self._update_ui()
                    #     self.page.update()

                    self.table.filter_settings = saved_state.get('filters', {})
                    self.table.search_term = saved_state.get('search', '')

                    # Применяем фильтры к данным
                    self.table._apply_filters()

                    # Принудительно обновляем UI
                    # self.update_filter_details({
                    #     **self.table.filter_settings,
                    #     "_search": {"value": self.table.search_term} if self.table.search_term else {}
                    # })

                    # Показываем панель если есть активные фильтры
                    # if self.table.filter_settings or self.table.search_term:
                    #     self.show()

                    # Синхронизируем поле поиска
                    if self.search_field and self.table.search_term:
                        self.search_field.value = self.table.search_term
                        self.search_field.update()

                    self.page.update()
                except Exception as e:
                    print(f"Ошибка при загрузке состояния: {str(e)}")

    def _update_ui(self):
        """Принудительно обновляет все элементы UI"""
        if self.panel in self.page.overlay:  # Проверяем добавлена ли панель
            if self.search_field and self.search_field.page is not None:
                self.search_field.update()
            if self.filter_details_column.page is not None:
                self.filter_details_column.update()
            self.reset_filters_button.update()
            self.column_manager_button.update()

    def set_table(self, table):
        """Установка таблицы с дополнительной проверкой"""
        self.table = table
        table.page_panel = self

    def _create_panel(self):
        """Создание панели с фильтрами и управлением"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Фильтры и настройки", size=22, weight=ft.FontWeight.BOLD, color=self.blue_primary),
                    ft.IconButton(
                        icon=ft.icons.CLOSE,
                        icon_color=self.blue_primary,
                        on_click=lambda e: self.hide()
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Column([
                    self.filter_details_column,
                ], spacing=10, expand=True),
                ft.Row([
                    self.reset_filters_button,
                    self.column_manager_button
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
            ], expand=True),
            expand=True,
            width=350,
            height=self.page.window.height,
            padding=15,
            margin=6,
            bgcolor=self.blue_background,
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.colors.BLUE_GREY_400,
                offset=ft.Offset(0, 5),
            ),
            right=0,
            top=0,
            bottom=0
        )

    def _reset_filters(self, e=None):
        """Reset all applied filters"""
        if self.table:
            # self.table.search_term = ""
            self.table._reset_filters()
            self._clear_filter_details()
            self.table.save_current_settings()

    def _show_column_manager(self, e=None):
        """Show column management dialog"""
        if self.table:
            self.table._show_column_manager(e)

    def _clear_filter_details(self):
        """Clear all filter detail controls except the header"""
        # Keep only the first control (header text)
        while len(self.filter_details_column.controls) > 1:
            self.filter_details_column.controls.pop()
        # Update only if column is on the page
        if self.filter_details_column.page is not None:
            self.filter_details_column.update()

    def format_date(self, date_str, col_type):
        """Форматирует дату только для столбцов с типом 'date'"""
        if col_type != 'date':
            return str(date_str)

        if isinstance(date_str, (pd.Timestamp, datetime)):
            return date_str.strftime("%d-%m-%Y")

        try:
            if 'T' in date_str:
                date_part = date_str.split('T')[0]
                dt = datetime.strptime(date_part, "%Y-%m-%d")
                return dt.strftime("%d-%m-%Y")
            elif len(date_str) == 10 and date_str[4] == '-':
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime("%d-%m-%Y")
            else:
                return str(date_str)
        except:
            return str(date_str)

    def _create_filter_item(self, col_name, description, filter_data):
        # Создаем кнопку удаления
        close_button = ft.IconButton(
            icon=self.close_icon,
            icon_size=18,
            icon_color=self.blue_primary,
            on_click=lambda e, col=col_name: self._remove_filter(col),
            tooltip="Удалить фильтр"
        )

        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(f"{col_name}:", size=14, weight=ft.FontWeight.BOLD, color=self.blue_primary),
                    ft.Column(description, spacing=2)
                ], expand=True),
                close_button
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(10),
            bgcolor=ft.colors.with_opacity(0.1, self.blue_primary),
            border_radius=8,
            width=float("inf"),
            margin=ft.margin.only(bottom=10),
            data=filter_data,
            on_click=lambda e, col=col_name: self.toggle_filter_items(col)
        )

    def _remove_filter(self, column_name):
        # Удаляем фильтр из настроек таблицы
        if column_name in self.table.filter_settings:
            del self.table.filter_settings[column_name]

        # Для глобального поиска
        if column_name == "_search":
            self.table.search_term = ""
            if self.search_field:
                self.search_field.value = ""
        elif column_name in self.table.filter_settings:
            del self.table.filter_settings[column_name]

        # Применяем изменения
        self.table._apply_filters()
        self.table.save_current_settings()
        self.update_filter_details({
            **self.table.filter_settings,
            "_search": {"value": self.table.search_term} if self.table.search_term else {}
        })
        self.table.force_update()

    def update_filter_details(self, filter_settings=None):
        """Обновляем отображение фильтров в панели"""
        self.filter_details_column.controls = [
            ft.Text("Примененные фильтры:", weight=ft.FontWeight.BOLD)
        ]
        if not filter_settings:
            self.filter_details_column.controls.append(
                ft.Container(
                    content=ft.Text("Фильтры не применены", size=14, color=self.blue_primary, expand=True),
                    padding=ft.padding.all(10),
                    bgcolor=ft.colors.with_opacity(0.1, self.blue_primary),
                    border_radius=5,
                    width=float("inf"),
                    margin=ft.margin.only(bottom=10),
                )
            )
            return

        if "_search" in filter_settings:
            search_value = filter_settings["_search"].get("value", "")
            if search_value:
                self.filter_details_column.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text("Глобальный поиск:", weight=ft.FontWeight.BOLD),
                                ft.Text(f"'{search_value}'", size=14)
                            ], expand=True),
                            ft.IconButton(
                                icon=ft.icons.CLOSE,
                                on_click=lambda e: self._remove_filter("_search"),
                                icon_color=ft.colors.RED_700
                            )
                        ]),
                        padding=ft.padding.all(10),
                        bgcolor=ft.colors.with_opacity(0.1, self.blue_primary),
                        border_radius=5,
                        width=float("inf"),
                        margin=ft.margin.only(bottom=10),
                    )
                )

        has_filters = False  # Флаг для проверки наличия реальных фильтров

        for col_name, settings in filter_settings.items():
            # Проверяем, есть ли таблица и столбец существует
            if not hasattr(self, 'table') or not self.table or col_name not in self.table.columns_config:
                continue

            col_type = self.table.columns_config.get(col_name, {}).get('type', 'text')
            desc = []
            filter_data = {
                "full_items": [],
                "truncated": False,
                "is_expanded": False
            }

            if 'selected_values' in settings:
                try:
                    unique_values = self.table.original_df[col_name].dropna().unique().tolist()
                    # Конвертируем в строки для сравнения
                    str_unique = list(map(str, unique_values))
                    str_selected = list(map(str, settings['selected_values']))
                except:
                    unique_values = []
                    str_unique = []
                    str_selected = []

                selected = settings['selected_values']
                # all_selected = False
                # if col_type == 'category':
                #     options = self.table.columns_config[col_name].get('options', [])
                #     if set(selected) == set(options):
                #         all_selected = True

                if len(str_selected) == 0:
                    desc.append(ft.Text("Всё исключено", size=12, color=ft.colors.GREY_700, weight=ft.FontWeight.BOLD))
                    has_filters = True
                elif len(str_selected) == len(str_unique):
                    desc.append(ft.Text("Всё выделено", size=12, color=ft.colors.GREY_700, weight=ft.FontWeight.BOLD))
                    has_filters = True
                else:
                    if col_type == 'date':
                        formatted_selected = [self.format_date(d, col_type) for d in selected]
                    elif col_type == 'numeric':
                        formatted_selected = [f"{int(v):,}".replace(",", " ") if isinstance(v, (int, float)) else v
                                              for v in selected]
                    else:
                        formatted_selected = selected

                    display_items, truncated = self._truncate_list(formatted_selected, 3)
                    items_str = ", ".join(map(str, display_items))
                    if truncated:
                        items_str += f" (+{len(selected) - 3})"

                    desc.append(ft.Text(f"Выбрано: {items_str}", size=12, color=ft.colors.GREY_700))
                    has_filters = True

                    # Сохраняем данные для переключения
                    filter_data.update({
                        "full_items": formatted_selected,
                        "truncated": truncated
                    })

            if 'type' in settings and settings['type'] in ['contains', 'does_not_contain']:
                value = settings['value']
                if settings['type'] == 'contains':
                    desc.append(ft.Text(f"Содержит: '{value}'", size=12, color=ft.colors.GREY_700))
                else:
                    desc.append(ft.Text(f"Не содержит: '{value}'", size=12, color=ft.colors.GREY_700))
                has_filters = True

            if col_type == 'date':
                start = settings.get("start_date")
                end = settings.get("end_date")
                selected = settings.get("selected_values", [])
                include_empty = settings.get("include_empty", False)
                if start or end:
                    range_desc = []
                    if start:
                        range_desc.append(f"от {start}")
                    if end:
                        range_desc.append(f"до {end}")
                    desc.append(ft.Text("Диапазон: " + " ".join(range_desc), size=12, color=ft.colors.GREY_700))
                    has_filters = True

                if selected:
                    formatted_selected = [self.format_date(d, col_type) for d in selected]
                    display_items, truncated = self._truncate_list(formatted_selected, 3)
                    items_str = ", ".join(map(str, display_items))
                    if truncated:
                        items_str += f" (+{len(selected) - 3})"
                    # desc.append(f"Выбрано: {items_str}")
                    has_filters = True

                    # Обновляем filter_data для переключения
                    filter_data["full_items"] = formatted_selected
                    filter_data["truncated"] = truncated
                    filter_data["is_expanded"] = False

                if include_empty:
                    desc.append(ft.Text("Включая пустые", size=12, color=ft.colors.GREY_700))
                    has_filters = True

            elif col_type == 'numeric':
                min_val = settings.get("min_value")
                max_val = settings.get("max_value")
                selected = settings.get("selected_values", [])
                include_empty = settings.get("include_empty", False)

                if min_val is not None or max_val is not None:
                    range_desc = []
                    if min_val is not None:
                        range_desc.append(f"от {min_val}")
                    if max_val is not None:
                        range_desc.append(f"до {max_val}")
                    desc.append(ft.Text("Диапазон: " + " ".join(range_desc), size=12, color=ft.colors.GREY_700))
                    has_filters = True

                if selected:
                    selected = [f"{int(v):,}".replace(",", " ") if isinstance(v, (int, float)) else v
                                for v in settings.get("selected_values", [])]
                    display_items, truncated = self._truncate_list(selected, 3)
                    items_str = ", ".join(display_items)
                    if truncated:
                        items_str += f" (+{len(selected) - 3})"
                    # desc.append(f"Значения: {items_str}")
                    has_filters = True

                    # Обновляем filter_data для переключения
                    filter_data["full_items"] = selected
                    filter_data["truncated"] = truncated
                    filter_data["is_expanded"] = False

                if include_empty:
                    desc.append(ft.Text("Включая пустые", size=12, color=ft.colors.GREY_700))
                    has_filters = True

            elif col_type == 'category':
                selected = settings.get("selected_values", [])
                include_empty = settings.get("include_empty", False)

                formatted_selected = [self.format_date(d, col_type) for d in selected]
                display_items, truncated = self._truncate_list(formatted_selected, 3)
                items_str = ", ".join(map(str, display_items))
                if truncated:
                    items_str += f" (+{len(selected) - 3})"
                # desc.append(f"Выбрано: {items_str}")
                has_filters = True

                if include_empty:
                    desc.append(ft.Text("Включая пустые", size=12, color=ft.colors.GREY_700))
                    has_filters = True

            if desc:
                # Создаем контейнер с данными filter_data
                # filter_container = ft.Container(
                #     content=ft.Column(
                #         controls=[
                #             ft.Text(f"{col_name}:", size=14, weight=ft.FontWeight.BOLD, color=self.blue_primary,
                #                     expand=True),
                #             ft.Column(
                #                 controls=desc,
                #                 spacing=2,
                #                 expand=True
                #             ),
                #         ],
                #         expand=True,
                #         spacing=5,
                #         horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                #     ),
                #     width=float("inf"),
                #     # expand=True,
                #     padding=ft.padding.all(10),
                #     bgcolor=ft.colors.with_opacity(0.1, self.blue_primary),
                #     border_radius=8,
                #     margin=ft.margin.only(bottom=10),
                #     data=filter_data,
                #     on_click=lambda e, col=col_name: self.toggle_filter_items(col)
                # )

                filter_container = self._create_filter_item(col_name, desc, filter_data)

                self.filter_details_column.controls.append(filter_container)

        if not has_filters:
            self.filter_details_column.controls.append(
                ft.Container(
                    content=ft.Text("Фильтры не применены", size=14, color=self.blue_primary, expand=True),
                    padding=ft.padding.all(10),
                    bgcolor=ft.colors.with_opacity(0.1, self.blue_primary),
                    border_radius=5,
                    width=float("inf"),
                    margin=ft.margin.only(bottom=10),
                )
            )

        self._update_ui()

    def toggle_filter_items(self, column_name):
        # Находим нужный контейнер с фильтром
        for control in self.filter_details_column.controls:
            if (isinstance(control, ft.Container) and
                    isinstance(control.content, ft.Row) and
                    len(control.content.controls) > 0 and
                    isinstance(control.content.controls[0], ft.Column)):

                # Проверяем заголовок колонки
                header = control.content.controls[0].controls[0]
                if isinstance(header, ft.Text) and header.value.startswith(f"{column_name}:"):

                    # Получаем данные фильтра
                    data = control.data
                    if not data.get("truncated", False):
                        continue

                    # Переключаем состояние
                    data["is_expanded"] = not data.get("is_expanded", False)

                    # Обновляем текст
                    description_column = control.content.controls[0].controls[1]
                    for text_control in description_column.controls:
                        if isinstance(text_control, ft.Text) and "Выбрано:" in text_control.value:
                            if data["is_expanded"]:
                                new_text = f"Выбрано: {', '.join(map(str, data['full_items']))}"
                            else:
                                truncated = ", ".join(map(str, data['full_items'][:3]))
                                if len(data['full_items']) > 3:
                                    truncated += f" (+{len(data['full_items']) - 3})"
                                new_text = f"Выбрано: {truncated}"
                            text_control.value = new_text
                            break

                    # Обновляем данные и интерфейс
                    control.data = data
                    control.update()
                    break

    def _truncate_list(self, items, max_items):
        """Форматирование списка значений с обрезкой. Возвращает (отображаемые элементы, было ли обрезано)"""
        if len(items) > max_items:
            return items[:max_items], True
        return items, False

    def show(self):
        """Показ панели фильтров"""
        if not self.is_visible:
            self.page.overlay.append(self.panel)
            self.is_visible = True
            # if self.table:
            #     self.table.save_current_settings()
            self.page.update()

    def hide(self):
        """Скрытие панели фильтров"""
        if self.is_visible:
            try:
                # Удаляем из overlay страницы
                if self.panel in self.page.overlay:
                    self.page.overlay.remove(self.panel)

                # Удаляем из списка активных панелей
                if self in self.page.active_page_panels:
                    self.page.active_page_panels.remove(self)

                self.is_visible = False

                if self.table:
                    self.table.save_current_settings()

                self.page.update()
            except Exception as e:
                print(f"Ошибка при закрытии панели: {str(e)}")

    def close(self):
        """Полное закрытие и очистка панели"""
        self.hide()

        # Дополнительная очистка ресурсов при необходимости
        if self.table:
            self.table.page_panel = None
            self.table = None

        # Удаляем ссылки на элементы управления
        self.filter_details_column = None
        self.reset_filters_button = None
        self.column_manager_button = None
        self.panel = None
