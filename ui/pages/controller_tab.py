import uuid
import flet as ft
from flet import (
    IconButton, ElevatedButton, TextField, Container, Column, Row,
    MainAxisAlignment, BoxShadow, padding, colors, icons, ButtonStyle,
    FontWeight, ScrollMode, alignment
)
import src.database.admin.delete_server as delete_server
import src.database.admin.select_server as select_server
from src.ui.components.crud_dialogs.create_empl_dialog import CreateEmployeeDialog
from src.ui.components.crud_dialogs.further_details_empl_dialog import FurtherDetailsEmployeeDialog
from src.ui.components.crud_dialogs.update_empl_dialog import UpdateEmployeeDialog
from src.ui.components.table_components.class_table import FilterableDataTable
from src.ui.components.table_components.data_tuples import load_data_from_tuples
from src.ui.components.table_components.page_setting import PagePanel
from src.ui.utils.navigation import nav_manager

from src.ui.utils.ui_blocker import block_ui
from src.ui.utils.action_menu import PopupMenuUp
from src.utils.show_snack_bar import show_snack_bar


def controller_tab(page):
    @block_ui(page)
    def load_employees():
        return select_server.get_all_employees()

    emp_data = load_employees()

    employee_data = load_data_from_tuples(
        data_tuples=emp_data,
        columns=['ID', 'ФИО', 'Права', 'Телефон', 'Почта', 'Статус здоровья',
                 'Задач сегодня', 'Выполненных сегодня', 'Не выполнено сегодня', 'Всего не выполнено'],
        numeric_columns=['ID', 'Задач сегодня', 'Выполненных сегодня', 'Не выполнено сегодня',
                         'Всего не выполнено'],
        string_columns=['ФИО', 'Права', 'Телефон', 'Почта', 'Статус здоровья']
    )

    def perform_search(e):
        search_term = search_field.value.lower() if search_field.value else ""
        employee_table.apply_search_filter(search_term)

        if isinstance(search_field.suffix_icon, ft.IconButton):
            search_field.suffix_icon.visible = bool(search_term)
            search_field.update()

        employee_table.force_update()

        if employee_table.page:
            employee_table.page.update()

    def clear_search(e):
        search_field.value = ""
        perform_search(e)

    def reload_page(e):
        @block_ui(page)
        def load_employees():
            return select_server.get_all_employees(refresh=True)

        # Данные сотрудников
        emp_data = load_employees()

        employee_data.original_df = load_data_from_tuples(
            data_tuples=emp_data,
            columns=['ID', 'ФИО', 'Права', 'Телефон', 'Почта', 'Статус здоровья',
                     'Задач сегодня', 'Выполненных сегодня', 'Не выполнено сегодня', 'Всего не выполнено'],
            numeric_columns=['ID', 'Задач сегодня', 'Выполненных сегодня', 'Не выполнено сегодня',
                             'Всего не выполнено'],
            string_columns=['ФИО', 'Права', 'Телефон', 'Почта', 'Статус здоровья']
        )
        employee_table.filtered_df = employee_data.original_df.copy()

        employee_table.filter_settings.clear()
        employee_table.current_page = 0
        employee_table.selected_rows.clear()

        # Принудительно обновляем таблицу
        employee_table._update_table()
        employee_table._update_selection_count_indicator()

        if hasattr(employee_table, 'page_panel'):
            # Используем правильное имя метода с подчеркиванием
            employee_table._reset_filters_full()

        # Обновляем страницу
        if hasattr(page, 'update'):
            page.update()

    def show_filter_panel(e):
        employee_table.show_filters()

    def create_animated_container(content, **kwargs):
        return Container(
            content=content,
            animate=ft.animation.Animation(300, curve=ft.AnimationCurve.EASE_OUT),
            **kwargs
        )

    def create_action_button(text, on_click, icon, color=colors.BLUE, disabled=False):
        return ElevatedButton(
            content=Row(
                [
                    ft.Icon(icon, color=colors.WHITE),
                    ft.Text(text, color=colors.WHITE, weight=FontWeight.W_500)
                ],
                alignment=MainAxisAlignment.CENTER,
                spacing=5,
            ),
            style=ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor=color,
                elevation=5,
            ),
            on_click=on_click,
            disabled=disabled,
        )

    def create_employee_button(e=None):
        dialog = CreateEmployeeDialog(page)
        dialog.open()

    def update_action_buttons(selected_rows):
        num_selected = len(selected_rows)
        button_edit.visible = num_selected == 1
        page.update()

    @block_ui(page)
    def update_employee_button(e=None):
        """Обработчик обновления сотрудника"""
        selected_ids = employee_table.filtered_df.loc[list(employee_table.selected_rows), 'ID'].tolist()

        if len(selected_ids) != 1:
            show_snack_bar(page, "Выберите одного сотрудника для обновления")
            return

        # Получаем ID единственного выбранного сотрудника
        employee_id = selected_ids[0]

        # Создаем и открываем диалог обновления
        update_dialog = UpdateEmployeeDialog(page, employee_id)  # Передаем ID как число
        update_dialog.open()

    @block_ui(page)
    def further_details_button(e=None):
        """Обработчик открытия подробной информации о сотруднике"""
        mass_ids = employee_table.filtered_df.loc[list(employee_table.selected_rows), 'ID'].tolist()

        if len(mass_ids) != 1:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Выберите одного сотрудника для просмотра подробностей", color=ft.colors.RED),
                duration=3000
            )
            page.snack_bar.open = True
            page.update()
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

        # Создаем и открываем диалог подробной информации
        # details_dialog = FurtherDetailsEmployeeDialog(page, employee_data)  # Передаем ID сотрудника
        # details_dialog.open()

    def delete_task_button(e=None):
        mass_ids = employee_table.filtered_df.loc[list(employee_table.selected_rows), 'ID'].tolist()

        # Создание диалога подтверждения
        @block_ui(page)
        def confirm_delete(e):
            page.close(confirm_dialog)
            page.update()
            delete_server.delete_employee(mass_ids)
            reload_page(e)

        def cancel_delete(e):
            page.close(confirm_dialog)
            page.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Удаление задач",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.RED_600
            ),
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.icons.WARNING_ROUNDED, color=ft.colors.RED_600, size=48),
                    ft.Text(
                        f"Вы действительно хотите удалить сотрудника {len(mass_ids)} ?",
                        size=16,
                        color=ft.colors.GREY_800
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                ft.Text(
                    "Восстановить удаленного сотрудника будет невозможно.",
                    color=ft.colors.RED_600,
                    italic=True,
                    size=14
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, height=150),
            actions=[
                ft.TextButton(
                    "Отмена",
                    on_click=cancel_delete,
                    style=ft.ButtonStyle(color=ft.colors.GREY_700)
                ),
                ft.FilledButton(
                    "Удалить",
                    on_click=confirm_delete,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.RED_600,
                        color=ft.colors.WHITE
                    )
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10)
        )

        page.open(confirm_dialog)
        page.update()

    # UI Components
    search_field = TextField(
        label="Поиск сотрудников",
        expand=True,
        prefix_icon=icons.SEARCH,
        border_color=colors.BLUE,
        focused_border_color=colors.BLUE,
        cursor_color=colors.BLUE,
        on_change=perform_search,
        suffix_icon=ft.IconButton(
            icon=icons.CLOSE,
            on_click=clear_search,
            icon_size=18,
            visible=False,
            style=ButtonStyle(
                padding=padding.all(0),
                overlay_color=colors.TRANSPARENT,
            )
        ),
    )

    button_edit = Row(
        [
            create_action_button("Редактировать",
                                 update_employee_button,
                                 icons.EDIT),
            create_action_button("Подробнее",
                                 further_details_button,
                                 icons.INFO),
            create_action_button("Удалить",
                                 delete_task_button,
                                 icons.DELETE, colors.RED_600),
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=10,
        visible=False,
    )

    employee_table = FilterableDataTable(
        employee_data,
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
        on_selection_change=update_action_buttons,
        page_type="employeer",
        search_field=search_field

    )
    employee_table.set_page(page)

    top_bar = create_animated_container(
        Column([
            Row(
                [
                    search_field,
                    create_animated_container(
                        IconButton(
                            icon=icons.SEARCH,
                            tooltip="Поиск",
                            on_click=perform_search,
                            style=ButtonStyle(color=colors.WHITE, shape=ft.CircleBorder()),
                            icon_size=28,
                        ),
                        width=50,
                        height=50,
                        bgcolor=colors.BLUE_600,
                        border_radius=ft.border_radius.all(15),
                        alignment=alignment.center,
                    ),
                    create_animated_container(
                        IconButton(
                            icon=icons.REFRESH,
                            tooltip="Обновить",
                            on_click=reload_page,
                            style=ButtonStyle(color=colors.WHITE, shape=ft.CircleBorder()),
                            icon_size=28,
                        ),
                        width=50,
                        height=50,
                        bgcolor=colors.BLUE_GREY_600,
                        border_radius=ft.border_radius.all(15),
                        alignment=alignment.center,
                    ),
                    create_animated_container(
                        IconButton(
                            icon=icons.FILTER_LIST,
                            tooltip="Фильтры",
                            on_click=lambda e: show_filter_panel(e),
                            style=ButtonStyle(color=colors.WHITE, shape=ft.CircleBorder()),
                            icon_size=28,
                        ),
                        width=50,
                        height=50,
                        bgcolor=colors.BLUE_GREY_600,
                        border_radius=ft.border_radius.all(15),
                        alignment=alignment.center,
                    ),
                ],
                alignment=MainAxisAlignment.END,
                spacing=12,
            )
        ]),
        border_radius=15,
        bgcolor=colors.WHITE,
        margin=5,
        padding=padding.symmetric(horizontal=20, vertical=18),
        shadow=BoxShadow(
            color=colors.BLUE_GREY_300,
            offset=ft.Offset(2, 0),
            blur_radius=5,
            spread_radius=1,
        ),
    )

    table_container = Container(
        content=Column([
            employee_table.selection_count_indicator,
            employee_table.filter_indicator,
            Row([employee_table.data_table], scroll=ScrollMode.AUTO)
        ], scroll=ScrollMode.AUTO),  # Добавляем горизонтальный скролл
        expand=True,
        padding=10
    )

    content = Column([
        top_bar,
        table_container,
    ], expand=True)

    bottom_panel = Container(
        content=Row(
            [
                # Группа 1: Основные действия
                Column(
                    [
                        Row(
                            [
                                create_action_button(
                                    "Добавить",
                                    create_employee_button,
                                    icons.ADD,
                                    colors.GREEN_600,
                                ),
                                employee_table.add_pagination_controls()
                            ]
                        )
                    ],
                    alignment=MainAxisAlignment.CENTER,
                ),
                Row(
                    [
                        button_edit,
                    ],
                    alignment=MainAxisAlignment.CENTER,
                ),
            ],
            alignment=MainAxisAlignment.SPACE_BETWEEN,
            spacing=20,
        ),
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

    container = Container(
        content=Column([
            content,
            bottom_panel
        ]),
        expand=True
    )

    container.table = employee_table  # Добавляем ссылку на таблицу
    page.update()
    return container
