import uuid

import flet as ft
from flet import (
    IconButton, ElevatedButton, TextField, Container, Column, Row,
    MainAxisAlignment, BoxShadow, padding, colors, icons, ButtonStyle, FontWeight, ScrollMode,
    alignment
)
import src.database.admin.modification_server as modification_server
import src.database.admin.delete_server as delete_server
import src.database.admin.select_server as select_server
from src.ui.components.crud_dialogs.create_task_dialog import CreateTaskDialog
from src.ui.components.crud_dialogs.create_task_load_dialog import AddNewTaskDialog
from src.ui.components.table_components.class_table import FilterableDataTable
from src.ui.components.table_components.data_tuples import load_data_from_tuples
from src.ui.components.table_components.page_setting import PagePanel
from src.ui.utils.navigation import nav_manager
from src.ui.utils.ui_blocker import block_ui
from src.utils.show_snack_bar import show_snack_bar
from src.ui.utils.action_menu import PopupMenuUp


def acts_tab(page):
    @block_ui(page)
    def load_data():
        return select_server.select_acts_with_tasks_and_addresses()

    data_server = load_data()

    data = load_data_from_tuples(
        data_tuples=data_server,
        exclude_columns=[],
        columns=[
            'ID', 'Дата', 'Причина', 'ID Задания', 'Дата задания', 'Дата окончания задания',
            'Статус задания', 'ФИО Клиента', 'ФИО Сотрудника', 'Примечание', 'Город',
            'Район', 'Тип', 'Дом', 'Квартира', 'Подъезд',
            'Улица', 'Поселок'
        ],
        date_columns=['Дата', 'Дата задания', 'Дата окончания задания'],
        numeric_columns=['ID', 'id_квартиры', 'Квартира'],
        string_columns=[
            'Причина', 'Статус задания', 'ФИО Клиента', 'ФИО Сотрудника', 'Примечание', 'Город',
            'Район', 'Тип', 'Дом', 'Подъезд',
            'Улица', 'Поселок'
        ],
        json_columns=[]
    )

    def perform_search(e):
        search_term = search_field.value.lower() if search_field.value else ""
        table.apply_search_filter(search_term)

        if isinstance(search_field.suffix_icon, ft.IconButton):
            search_field.suffix_icon.visible = bool(search_term)
            search_field.update()

        table.force_update()

        if table.page:
            table.page.update()

    def clear_search(e):
        search_field.value = ""

        if isinstance(search_field.suffix_icon, ft.IconButton):
            search_field.suffix_icon.visible = False

        perform_search(e)

    def reload_page(e):
        nonlocal data, table, search_field

        @block_ui(page)
        def load_data():
            return select_server.select_acts_with_tasks_and_addresses(refresh=True)

        # Очищаем поле поиска
        search_field.value = ""
        if hasattr(table, '_reset_filters_full'):
            table._reset_filters_full()

        data_server = load_data()

        data = load_data_from_tuples(
            data_tuples=data_server,
            exclude_columns=[],
            columns=[
                'ID', 'Дата', 'Причина', 'ID Задания', 'Дата задания', 'Дата окончания задания',
                'Статус задания', 'ФИО Клиента', 'ФИО Сотрудника', 'Примечание', 'Город',
                'Район', 'Тип', 'Дом', 'Квартира', 'Подъезд',
                'Улица', 'Поселок'
            ],
            date_columns=['Дата', 'Дата задания', 'Дата окончания задания'],
            numeric_columns=['ID', 'id_квартиры', 'Квартира'],
            string_columns=[
                'Причина', 'Статус задания', 'ФИО Клиента', 'ФИО Сотрудника', 'Примечание', 'Город',
                'Район', 'Тип', 'Дом', 'Подъезд',
                'Улица', 'Поселок'
            ],
            json_columns=[]
        )

        table.original_df = data
        table.filtered_df = data.copy()
        table.filter_settings.clear()
        table.current_page = 0
        table.selected_rows.clear()

        # Принудительно обновляем таблицу
        table._update_table()
        table._update_selection_count_indicator()

        if hasattr(table, 'page_panel'):
            # Используем правильное имя метода с подчеркиванием
            table._reset_filters_full()

        # Обновляем страницу
        if hasattr(page, 'update'):
            page.update()

    def open_load_dialog(e):
        dialog = AddNewTaskDialog(page)
        dialog.open()
        page.update()

    def create_task_button(e=None):
        task_dialog = CreateTaskDialog(page)
        task_dialog.open()

    def show_filter_panel(e):
        table.show_filters()

    def create_animated_container(content, **kwargs):
        return Container(
            content=content,
            animate=ft.animation.Animation(300, curve=ft.animation.AnimationCurve.EASE_OUT),
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

    search_field = TextField(
        label="Поиск",
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
            visible=False,  # Изначально скрыта
            style=ButtonStyle(
                padding=padding.all(0),
                overlay_color=colors.TRANSPARENT,
            )
        ),
    )

    button_edit = Row(
        [
            create_action_button("Подробнее о задании", lambda _: further_task_button(), icons.INFO),
            # create_action_button("Снять задание", lambda _: unassign_tasks(), icons.DO_NOT_TOUCH),
            # create_action_button("Назначить", lambda _: assign_tasks(), icons.ASSIGNMENT)
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=10,
        visible=False
    )

    button_assign = Row(
        [
            create_action_button("Снять задание", lambda _: unassign_tasks(), icons.DO_NOT_TOUCH),
            create_action_button("Назначить", lambda _: assign_tasks(), icons.ASSIGNMENT)
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=10,
        visible=False
    )

    action_menu = ft.PopupMenuButton(
        items=[],
        icon=ft.icons.MORE_VERT,
        tooltip="Дополнительные действия",
        menu_position=ft.PopupMenuPosition.UNDER,
        padding=padding.all(8.0)
    )

    def update_action_buttons(selected_rows):
        num_selected = len(selected_rows)

        button_edit.visible = num_selected == 1
        button_assign.visible = num_selected > 1

        items = []

        if num_selected == 0:
            items.append({
                "text": "Добавить задание",
                "on_click": lambda _: create_task_button(),
                "icon": ft.Icon(icons.ADD, color=ft.colors.GREEN_600)
            })

        if num_selected == 1:
            items.append({
                "text": "Редактировать задание",
                "on_click": lambda _: update_task_button(),
                "icon": ft.Icon(ft.icons.EDIT, color=ft.colors.ORANGE_600)
            })

        if num_selected >= 1:
            items.append({
                "text": f"Удалить задание",
                "on_click": lambda _: delete_task_button(),
                "icon": ft.Icon(ft.icons.DELETE, color=ft.colors.RED_600)
            })

        menu.set_items(items)
        page.update()

    def update_task_button():
        show_snack_bar(page, "Функция редактирования в разработке")

    def further_task_button():
        selected_ids = table.filtered_df.loc[list(table.selected_rows), 'ID Задания'].tolist()
        result = selected_ids[0]

        @block_ui(page)
        def load_data():
            return select_server.get_task_details(result, refresh=True)

        data_server = load_data()

        new_buttons = [
            {
                "icon": ft.icons.INFO,
                "label": "Детали задания",
                "data": "task_details",
                "id": f"task_details_{uuid.uuid4()}",
                "additional_data": data_server,
            }
        ]
        nav_manager.add_nav_button_and_navigate(new_buttons[0])

    def delete_task_button():
        mass_ids = table.filtered_df.loc[list(table.selected_rows), 'ID'].tolist()

        # Создание диалога подтверждения
        def confirm_delete(e):
            page.close(confirm_dialog)
            page.update()
            delete_server.delete_tasks(mass_ids)
            reload_page(e)

        # Отмена удаления
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
                        f"Вы действительно хотите удалить {len(mass_ids)} задач(и)?",
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

        page.open(confirm_dialog)
        page.update()

    def assign_tasks():
        selected_rows_data = table.filtered_df.loc[list(table.selected_rows)].to_dict("records")

        new_buttons = [
            {
                "icon": ft.icons.CHECKLIST,
                "label": "Выбор сотрудника",
                "data": "task_controller",
                "id": f"task_controller_{uuid.uuid4()}",
                "additional_data": selected_rows_data,
            }
        ]

        nav_manager.add_nav_button_and_navigate(new_buttons[0])

    def unassign_tasks():
        selected_rows = list(table.selected_rows)
        if not selected_rows:
            show_snack_bar(page, "Выберите задачи для отмены назначения")
            return

        mass_ids = table.filtered_df.loc[selected_rows, 'ID'].tolist()
        fio_emp = table.filtered_df.loc[selected_rows, 'Исполнитель'].tolist()

        # Создание диалога подтверждения
        def confirm_unassign(e):
            page.close(confirm_dialog)
            try:
                # Вызов API для снятия задач
                result = modification_server.unassign_tasks(mass_ids, fio_emp)
                if result:
                    show_snack_bar(page, f"Снято {len(mass_ids)} задач")
                    reload_page(e)
                else:
                    show_snack_bar(page, "Ошибка при снятии задач")
            except Exception as ex:
                print(f"Ошибка: {str(ex)}")

        def cancel_unassign(e):
            page.close(confirm_dialog)
            page.update()

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

        page.dialog = confirm_dialog
        page.open(confirm_dialog)
        page.update()

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

    columns_config = {
        "Дата": {"type": "date"},
        "Причина": {"type": "category"},
        "Тип": {"type": "category"},
        "ФИО Клиента": {"type": "category"},
        "ФИО Сотрудника": {"type": "category"},
        "Поселок": {"type": "category"},
        "Улица": {"type": "category"},
        "Дом": {"type": "category"},
        "Квартира": {"type": "numeric"},
        "Примечание": {"type": "category"},
        "Статус задания": {"type": "category"},
        "Дата задания": {"type": "date"},
        "Дата окончания задания": {"type": "date"},
        "Город": {"type": "category"},
        "Район": {"type": "category"},
        "Подъезд": {"type": "category"},
        "ID": {"type": "numeric"},
        "ID Задания": {"type": "numeric"}
    }

    table = FilterableDataTable(
        data,
        columns_config,
        hidden_columns=["ID", "Город", "Район", "Подъезд", "ID Задания"],
        on_selection_change=update_action_buttons,
        page_type="act",
        search_field=search_field
    )
    # filter_panel = PagePanel(page, page_type="search", search_field=search_field)

    table.set_page(page)
    # filter_panel.set_table(table)
    # table.page_panel = filter_panel

    # В функции search_tab заменить создание table_container
    table_container = Container(
        content=Column([
            table.selection_count_indicator,
            table.filter_indicator,
            Row([table.data_table], scroll=ScrollMode.AUTO)
        ], scroll=ScrollMode.AUTO),  # Добавляем горизонтальный скролл
        expand=True,
        padding=10
    )

    menu = PopupMenuUp([
        {
            "text": "Добавить задание",
            "on_click": lambda _: create_task_button(),
            "icon": ft.Icon(icons.ADD, color=ft.colors.GREEN_600)
        }
    ], page)

    content = Column([
        top_bar,
        table_container,
    ], expand=True)

    bottom_panel = Container(
        content=Row(
            [
                Column(
                    [
                        Row(
                            [
                                # create_action_button(
                                #     "Загрузить файл",
                                #     open_load_dialog,
                                #     icons.ADD,
                                #     colors.GREEN_600,
                                # ),
                                table.add_pagination_controls()
                            ]
                        )
                    ],
                    alignment=MainAxisAlignment.CENTER,
                ),
                Row(
                    [
                        button_edit,
                        # button_assign,
                        # menu.get_view()
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
            bottom_panel,
        ]),
        expand=True,
    )
    container.table = table  # Добавляем ссылку на таблицу
    page.update()
    return container
