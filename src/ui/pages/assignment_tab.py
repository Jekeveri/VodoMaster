import flet as ft
from flet import (
    IconButton, ElevatedButton, TextField, Checkbox, Text,
    DataTable, DataColumn, DataCell, DataRow, Container, Column, Row,
    MainAxisAlignment, BoxShadow, border, padding, ScrollMode, colors, icons, ButtonStyle, FontWeight,
    alignment
)

import src.database.admin.delete_server as delete_server
import src.database.admin.select_server as select_server
from src.ui.components.crud_dialogs.create_task_dialog import CreateTaskDialog
from src.ui.components.crud_dialogs.create_task_load_dialog import AddNewTaskDialog
from src.ui.components.crud_dialogs.further_details_task_dialog import FurtherDetailsTaskDialog
from src.ui.components.crud_dialogs.update_task_dialog import UpdateTaskDialog
from src.ui.utils.navigation import nav_manager
from src.ui.utils.ui_blocker import block_ui
from src.utils.show_snack_bar import show_snack_bar


def assignment_tab(page, table_name='tasks_assign'):
    @block_ui(page)
    def load_data():
        return select_server.select_task_data_unmade()

    data = load_data()
    filter_panel = None
    selected_rows = set()
    selected_data = set()

    def create_filter_group():
        nonlocal data

        @block_ui(page)
        def load_data():
            return select_server.select_task_data_unmade()

        data = load_data()

        filter_panel.data = data

    def show_filter_panel(e):
        create_filter_group()
        filter_panel.show()

    def reload_page(e):
        nonlocal data

        @block_ui(page)
        def load_data():
            return select_server.select_task_data_unmade(refresh=True)

        data = load_data()
        update_table(data)
        page.update()

    def perform_search(e):
        nonlocal data
        search_term = search_field.value.lower() if search_field.value else ""

        if not search_term:
            update_table(data)
            return

        filtered_results = [
            row for row in data
            if any(search_term in str(cell).lower() for cell in row)
        ]

        update_table(filtered_results)

        page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(f"Найдено результатов: {len(filtered_results)}"),
                duration=2000
            )
        )

    def create_animated_container(content, **kwargs):
        return Container(
            content=content,
            animate=ft.animation.Animation(300, curve=ft.AnimationCurve.EASE_OUT),  # Use proper enum
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

    def assign_tasks(selected_rows):
        new_buttons = [
            {
                "icon": ft.icons.CHECKLIST,
                "label": "Выбор сотрудника",
                "data": "task_controller",
                "id": f"task_controller_{len(selected_rows)}",
                "additional_data": selected_rows,
            }
        ]

        # Добавляем кнопку через навигационный менеджер
        nav_manager.add_nav_button_and_navigate(new_buttons[0])

    def create_task_button(e=None):
        task_dialog = CreateTaskDialog(page)
        task_dialog.open()

    def update_task_button(e=None):
        nonlocal selected_data
        if not selected_data:
            print("No row selected")
            return

        task_data = list(selected_data)[0]

        task_dialog = UpdateTaskDialog(page, task_data)
        task_dialog.open()

    def further_task_button(e=None):
        nonlocal selected_data
        if not selected_data:
            print("No row selected")
            return

        task_data = list(selected_data)[0]

        task_dialog = FurtherDetailsTaskDialog(page, task_data)
        task_dialog.open()

    def delete_task_button(e=None):
        nonlocal selected_data, selected_rows
        if not selected_data:
            print("No row selected")
            return

        selected_rows_list = list(selected_rows)

        # Создание диалога подтверждения
        def confirm_delete(e):
            confirm_dialog.open = False
            page.update()
            delete_server.delete_tasks(selected_rows_list)

        def cancel_delete(e):
            confirm_dialog.open = False
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
                        f"Вы действительно хотите удалить {len(selected_rows_list)} задач(и)?",
                        size=16,
                        color=ft.colors.GREY_800
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                ft.Text(
                    "Восстановить удаленные задачи будет невозможно.",
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

        page.dialog = confirm_dialog
        confirm_dialog.open = True
        page.update()

    def open_load_dialog(e):
        dialog = AddNewTaskDialog(page)

        # Создаем AlertDialog с содержимым UserControl
        excel_dialog = ft.AlertDialog(
            title=ft.Text("Загрузка задач из Excel"),
            content=dialog,
            actions=[
                ft.TextButton("Закрыть", on_click=lambda e: dialog.close_dialog(e),
                              style=ft.ButtonStyle(
                                  bgcolor=ft.colors.BLUE_600,
                                  color=ft.colors.WHITE
                              ))
            ],
            bgcolor=ft.colors.BLUE_50,
            surface_tint_color=ft.colors.BLUE_50,
            elevation=5
        )

        # Устанавливаем диалог и открываем его
        page.dialog = excel_dialog
        page.dialog.open = True
        page.update()

    button_edit = Row(
        [
            create_action_button("Редактировать", update_task_button, icons.EDIT),
            create_action_button("Подробнее", further_task_button, icons.INFO),
            create_action_button("Удалить", delete_task_button, icons.DELETE, colors.RED_600),
            create_action_button("Назначить", lambda _: assign_tasks(selected_rows), icons.ASSIGNMENT),
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=10,
        visible=False,
    )

    button_action_2 = Row(
        [
            create_action_button("Удалить", delete_task_button, icons.DELETE, colors.RED_600),
            create_action_button("Назначить", lambda _: assign_tasks(selected_rows), icons.ASSIGNMENT),
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=10,
        visible=False,
    )

    def update_buttons():
        button_edit.visible = len(selected_rows) == 1
        button_action_2.visible = len(selected_rows) > 1
        button_edit.update()
        button_action_2.update()

    data_table = DataTable(
        columns=[
            DataColumn(
                Checkbox(on_change=lambda e: toggle_all_checkboxes(e.control.value), active_color=colors.BLUE_500, )),
            DataColumn(Text("ФИО клиента", weight=FontWeight.BOLD, color=colors.BLUE_700)),
            DataColumn(Text("Адрес", weight=FontWeight.BOLD, color=colors.BLUE_700)),
            DataColumn(Text("Телефон", weight=FontWeight.BOLD, color=colors.BLUE_700)),
            DataColumn(Text("Лицевой счет", weight=FontWeight.BOLD, color=colors.BLUE_700)),
            DataColumn(Text("Дата задачи", weight=FontWeight.BOLD, color=colors.BLUE_700)),
            DataColumn(Text("Примечание", weight=FontWeight.BOLD, color=colors.BLUE_700)),
            DataColumn(Text("Статус задачи", weight=FontWeight.BOLD, color=colors.BLUE_700)),
            DataColumn(Text("Цель", weight=FontWeight.BOLD, color=colors.BLUE_700)),
            DataColumn(Text("Тип", weight=FontWeight.BOLD, color=colors.BLUE_700)),
            DataColumn(Text("ID", weight=FontWeight.BOLD, color=colors.BLUE_700)),
        ],
        rows=[],
        border=border.all(3, colors.BLUE_200),
        column_spacing=32,
        border_radius=12,
        data_row_max_height=100,
        data_row_min_height=50,
        show_bottom_border=True,
        vertical_lines=ft.BorderSide(2, colors.BLUE_200),
        horizontal_lines=ft.BorderSide(2, colors.BLUE_200),
        heading_row_color=colors.BLUE_50,
        heading_row_height=70,
    )

    def get_row_id(row):
        try:
            cell_content = row.cells[10].content
            if hasattr(cell_content, 'value'):
                return int(cell_content.value)
            else:
                return int(str(cell_content))
        except (AttributeError, ValueError, TypeError) as e:
            print(f"Error extracting row ID: {e}")
            return None

    def select_row(row_id, is_selected, row_data=None):
        if row_id is not None:
            if is_selected:
                selected_rows.add(row_id)
                update_selected_data(row_data, is_selected)
            else:
                selected_rows.discard(row_id)
                update_selected_data(row_data, is_selected)
            update_row_selection()
            update_buttons()

    def update_selected_data(row_data, checkbox):
        if checkbox:
            selected_data.add(tuple(row_data))
        else:
            selected_data.discard(tuple(row_data))

    def update_row_selection():
        if data_table.rows:
            for row in data_table.rows:
                row_id = get_row_id(row)
                row.color = colors.BLUE_GREY_50 if row_id in selected_rows else colors.WHITE
            page.update()
        else:
            # Optional: Add a message or log if no rows are present
            print("No rows to update")

    def toggle_all_checkboxes(is_selected):
        if data_table.rows:
            selected_rows.clear() if not is_selected else selected_rows.update(
                get_row_id(row) for row in data_table.rows
            )
            selected_data.clear()  # Очищаем данные при снятии выделения всех строк
            if is_selected:  # Если все строки выделяются, добавляем их данные
                for row in data_table.rows:
                    row_id = get_row_id(row)
                    row_data = extract_row_data(row)
                    if row_id not in selected_data:
                        selected_data.add(tuple(row_data))

            update_buttons()
            for row in data_table.rows:
                checkbox = next((cell.content for cell in row.cells if isinstance(cell.content, ft.Checkbox)), None)
                if checkbox is not None:
                    checkbox.value = is_selected
                row.color = colors.BLUE_GREY_50 if is_selected else colors.WHITE
            page.update()
        else:
            print("No rows to toggle")

    def extract_row_data(row):
        """Функция для извлечения данных строки из DataRow."""
        return [cell.content.value if hasattr(cell.content, 'value') else "" for cell in row.cells]

    def update_table(table_data):
        try:
            # Ensure data_table.rows is a list
            if data_table.rows is None:
                data_table.rows = []

            data_table.rows.clear()

            for row_data in table_data:
                full_address = (
                    f"""**Район:** {row_data[4] if row_data[4] else " "}   
                     **Улица:** {row_data[5] if row_data[5] else " "}  
                     **Поселок:** {row_data[6] if row_data[6] else " "}      
                     **Дом:** {row_data[7] if row_data[7] else " "} **Квартира:** {row_data[8] if row_data[8] else " "}"""
                )
                date_tasks = (
                    f"""**Дата начала:**  
                    {row_data[16]}   
                     **Дата окончания:**  
                     {row_data[21] if row_data[21] else "Нет"}"""
                )

                checkbox = Checkbox(
                    value=row_data[0] in selected_rows,
                    on_change=lambda e, id=row_data[0], data=row_data: select_row(id, e.control.value, data),
                    active_color=colors.BLUE_500,
                )

                def styled_text(value):
                    formatted_value = str(value)
                    if len(formatted_value) > 15:
                        words = formatted_value.split()
                        wrapped_lines = []
                        current_line = []
                        current_length = 0

                        for word in words:
                            if current_length + len(word) > 15:
                                wrapped_lines.append(' '.join(current_line))
                                current_line = [word]
                                current_length = len(word)
                            else:
                                current_line.append(word)
                                current_length += len(word) + 1

                        if current_line:
                            wrapped_lines.append(' '.join(current_line))

                        formatted_value = '\n'.join(wrapped_lines)

                    return Text(
                        formatted_value,
                        size=14,
                        weight=FontWeight.W_400,
                        color=colors.BLUE_GREY_900,
                    )

                row_cells = [
                    DataCell(checkbox),
                    DataCell(styled_text(row_data[1])),  # ФИО клиента
                    DataCell(ft.Markdown(full_address)),
                    DataCell(styled_text(row_data[14])),  # Телефон
                    DataCell(styled_text(row_data[15])),  # Лицевой счет
                    DataCell(ft.Markdown(date_tasks)),  # Дата задачи
                    DataCell(styled_text(row_data[17] if row_data[17] else " ")),  # Примечание                    
                    DataCell(styled_text(row_data[18])),  # Статус задачи
                    DataCell(styled_text(row_data[19])),  # Цель
                    DataCell(styled_text(row_data[11] if row_data[11] else " ")),  # Тип адреса
                    DataCell(ft.Text(str(row_data[0]))),  # ID задачи
                ]

                data_table.rows.append(
                    DataRow(
                        cells=row_cells,
                        color=colors.BLUE_GREY_50 if row_data[0] in selected_rows else colors.WHITE,
                    )
                )
            page.update()
        except Exception as e:
            print(f"Error updating table: {e}")
            show_snack_bar(page, f"Ошибка обновления таблицы: {e}")

    update_table(data)

    search_field = TextField(
        label="Поиск",
        expand=True,
        prefix_icon=icons.SEARCH,
        border_color=colors.BLUE,
        focused_border_color=colors.BLUE,
        cursor_color=colors.BLUE,
        # on_submit=perform_search,
    )

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
                            on_click=show_filter_panel,
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

    content = Column([
        top_bar,
        create_animated_container(
            Column([Row([data_table], expand=True, alignment=ft.MainAxisAlignment.CENTER)], expand=True,
                   scroll=ScrollMode.AUTO),
            expand=True,
            border_radius=12,
            padding=padding.symmetric(horizontal=3, vertical=12),
            bgcolor=colors.WHITE,
        ),
    ], expand=True, scroll=ScrollMode.AUTO)

    bottom_panel = Container(
        content=Row(
            [
                # Группа 1: Основные действия
                Column(
                    [
                        Row(
                            [
                                create_action_button(
                                    "Загрузить файл",
                                    open_load_dialog,
                                    icons.ADD,
                                    colors.GREEN_600,
                                ),
                                create_action_button(
                                    "Добавить",
                                    create_task_button,
                                    icons.ADD,
                                    colors.GREEN_600,
                                ),
                            ]
                        )
                    ],
                    alignment=MainAxisAlignment.CENTER,
                ),
                # Группа 3: Дополнительные действия
                Row(
                    [
                        button_edit,
                        button_action_2
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

    page.padding = 0
    search_field.on_submit = perform_search
    top_bar.content.controls[0].controls[0].on_click = perform_search

    return Container(
        content=Column([
            content,
            bottom_panel,
        ], ),
        expand=True,
    )
