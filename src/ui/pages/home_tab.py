import flet as ft
import uuid
from src.core.session_manager import session_manager
from src.ui.utils.navigation import nav_manager
import src.database.admin.select_server as select_server
from src.ui.components.crud_dialogs.create_task_load_dialog import AddNewTaskDialog
from src.ui.components.crud_dialogs.discharge_file_dialog import ExportTasksDialog
from src.utils.show_snack_bar import show_snack_bar


def home_tab(page: ft.Page):
    def handle_hover(e):
        icon = e.control.content.controls[0]
        text = e.control.content.controls[1]

        if e.data == "true":
            e.control.bgcolor = ft.colors.PRIMARY
            icon.color = ft.colors.WHITE
            text.color = ft.colors.WHITE
        else:
            e.control.bgcolor = ft.colors.WHITE
            icon.color = ft.colors.PRIMARY
            text.color = ft.colors.PRIMARY
        e.control.update()

    def create_button_container(text, icon, on_click_action, details=None, width_conteiners=200):
        content_controls = [
            ft.Icon(name=icon, color=ft.colors.PRIMARY, size=32),
            ft.Text(text, size=14, weight=ft.FontWeight.BOLD,
                    color=ft.colors.PRIMARY, text_align=ft.TextAlign.CENTER),
        ]

        if details:
            content_controls.append(
                ft.Column(
                    controls=[
                        ft.Text(detail, size=10, color=ft.colors.GREY_600,
                                text_align=ft.TextAlign.CENTER)
                        for detail in details
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        return ft.Container(
            content=ft.Column(
                content_controls,
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            margin=10,
            padding=15,
            width=width_conteiners,
            height=200,
            border_radius=15,
            bgcolor=ft.colors.WHITE,
            on_click=on_click_action,
            on_hover=handle_hover,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.BLUE_GREY_300,
                offset=ft.Offset(2, 2),
            ),
        )

    def open_load_dialog():
        dialog = AddNewTaskDialog(page)
        dialog.open()
        page.update()

    def open_upload_dialog():
        dialog = ExportTasksDialog(page)
        dialog.open()
        page.update()

    def create_pie_chart():
        stats_data = select_server.get_dashboard_stats_data(refresh=True)
        tasks_by_status = stats_data.get('tasks_by_status', [])

        if not tasks_by_status:
            return ft.Container(
                content=ft.Text("Нет данных для отображения"),
                alignment=ft.alignment.center
            )

        normal_radius = 160
        hover_radius = 170
        normal_title_style = ft.TextStyle(
            size=0, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD
        )
        hover_title_style = ft.TextStyle(
            size=22,
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD,
            shadow=ft.BoxShadow(blur_radius=2, color=ft.Colors.BLACK54),
        )

        status_colors = {
            "не выполнен": ft.Colors.BLUE,  # Жёлтый
            "выполнен": ft.Colors.GREEN,
            "в исполнении": '#ffc107',
            "просрочен": ft.Colors.RED
        }

        filtered_statuses = [s for s in tasks_by_status if s['count'] > 0]
        total = sum(s['count'] for s in filtered_statuses) or 1

        sections = []
        for status in filtered_statuses:
            percent = (status['count'] / total) * 100
            sections.append(
                ft.PieChartSection(
                    percent,
                    title=f"{status['count']} ({round(percent)}%)",
                    title_style=normal_title_style,
                    color=status_colors.get(status['status'], ft.Colors.GREY),
                    radius=normal_radius
                )
            )

        def on_chart_event(e: ft.PieChartEvent):
            for idx, section in enumerate(chart.sections):
                if idx == e.section_index:
                    section.radius = hover_radius
                    section.title_style = hover_title_style
                else:
                    section.radius = normal_radius
                    section.title_style = normal_title_style
            chart.update()

        chart = ft.PieChart(
            sections=sections,
            sections_space=3,
            center_space_radius=40,
            on_chart_event=on_chart_event,
            expand=True,
        )

        legend_items = []
        for status in filtered_statuses:
            legend_items.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            width=20,
                            height=20,
                            border_radius=8,
                            bgcolor=status_colors.get(status['status'], ft.Colors.GREY),
                        ),
                        ft.Text(f"{status['status']} ({status['count']})", size=18),
                    ],
                    spacing=8,
                )
            )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Статусы задач", style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=22)),
                    ft.Text(f"Всего задач: {total}", style=ft.TextStyle(size=18)),
                    chart,
                    ft.Column(
                        legend_items,
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                    )
                ],
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
        )

    def view_meter():
        new_buttons = [
            {
                "icon": ft.icons.GAS_METER,
                "label": "Счетчики",
                "data": "meters",
                "id": f"btn_meters_{uuid.uuid4()}",
                "additional_data": "",
            }
        ]
        nav_manager.add_nav_button_and_navigate(new_buttons[0])

    def view_acts():
        new_buttons = [
            {
                "icon": ft.icons.TASK,
                "label": "Акты",
                "data": "acts_tab",
                "id": f"btn_acts_{uuid.uuid4()}",
                "additional_data": "",
            }
        ]
        nav_manager.add_nav_button_and_navigate(new_buttons[0])

    def view_address():
        new_buttons = [
            {
                "icon": ft.icons.HOME,
                "label": "Адреса",
                "data": "address_tab",
                "id": f"btn_address_{uuid.uuid4()}",
                "additional_data": "",
            }
        ]
        nav_manager.add_nav_button_and_navigate(new_buttons[0])

    def view_graphs():
        new_buttons = [
            {
                "icon": ft.icons.INFO,
                "label": "Статистика",
                "data": "graphs_tab",
                "id": f"btn_graphs_{uuid.uuid4()}",
                "additional_data": "",
            }
        ]
        nav_manager.add_nav_button_and_navigate(new_buttons[0])

    recent_pages = nav_manager.closed_pages

    bottom_controls = []
    first_history = True
    for idx, page_info in enumerate(recent_pages):
        first_history = False

        details = []
        additional_data = page_info.get("additional_data", {})

        if additional_data:
            if page_info['data'] == 'empl_details':
                employee_id = additional_data.get('employee_id')
                details.append(f"ID сотрудника: {employee_id}")

            elif page_info['data'] == 'task_details':
                task_data = additional_data.get('task', {})
                if task_data:
                    details.extend([
                        f"Адрес: {task_data.get('address', {}).get('street', '')} {task_data.get('address', {}).get('dom', '')}"
                    ])

        def create_handler(data, pi=page_info):
            return lambda e: nav_manager.navigate({
                "id": pi["id"],
                "label": pi.get("label", "Без названия"),
                "icon": pi.get("icon", "help"),
                "data": pi["data"],
                "additional_data": pi.get("additional_data", {})
            })

        bottom_controls.append(
            create_button_container(
                text=page_info.get("label", "Без названия"),
                icon=page_info.get("icon", "help"),
                on_click_action=create_handler(page_info),
                details=details
            )
        )
    else:
        if first_history:
            bottom_controls.append(
                ft.Container(
                    content=ft.Text(
                        "История отсутствует",
                        size=16,
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    margin=10,
                    padding=15,
                    visible=first_history,
                    width=200,
                    height=200,
                    border_radius=15,
                    bgcolor=ft.colors.WHITE,
                    alignment=ft.alignment.center,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=10,
                        color=ft.colors.BLUE_GREY_300,
                        offset=ft.Offset(2, 2),
                    ),
                )
            )

    top_controls = [
        create_button_container("Счетчики", "gas_meter", lambda _: view_meter()),
        create_button_container("Акты", "task", lambda _: view_acts()),
        create_button_container("Адреса", "home", lambda _: view_address()),
        create_button_container("Статистика", "info", lambda _: view_graphs()),
    ]

    third_controls = [
        create_button_container("Загрузка заданий", "DOWNLOADING", lambda _: open_load_dialog(), width_conteiners=435),
        create_button_container("Выгрузка заданий", "UPLOAD", lambda _: open_upload_dialog(), width_conteiners=435),
    ]

    current_user_id = session_manager.get_current_user_id()
    if not current_user_id:
        return ft.Container()

    session_data = session_manager.get_session(current_user_id)
    if not session_data:
        return ft.Container()
    current_user_login = session_data.get('login')

    return ft.Column(
        [
            ft.Container(
                content=ft.Text(
                    f"Здравствуйте, {current_user_login}",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.PRIMARY
                ),
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
            ),
            ft.Divider(height=1),
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Column(
                                [
                                    ft.Text("Дополнительные страницы",
                                            style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD)),
                                    ft.ResponsiveRow(
                                        [ft.Container(btn, col={"sm": 4, "md": 4, "lg": 3}) for btn in
                                         top_controls],
                                        spacing=10,
                                    ),
                                    ft.Text("Работа с данными",
                                            style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD)),
                                    ft.ResponsiveRow(
                                        [ft.Container(btn, col=6) for btn in third_controls],
                                        spacing=10,
                                    ),
                                    ft.Text("История закрытых страниц",
                                            style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD)),
                                    ft.ResponsiveRow(
                                        [ft.Container(btn, col={"sm": 4, "md": 4, "lg": 3}) for btn in
                                         bottom_controls],
                                        spacing=10,
                                    ),
                                ],
                                spacing=20,
                                scroll=ft.ScrollMode.AUTO,
                                expand=True,
                            ),
                        ],
                        expand=True,
                        spacing=20,
                    ),

                    ft.Container(
                        content=create_pie_chart(),
                        margin=10,
                        padding=15,
                        width=(page.window.width // 3) - 30,
                        height=page.window.height - 200,
                        border_radius=15,
                        bgcolor=ft.colors.WHITE,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color=ft.colors.BLUE_GREY_300,
                            offset=ft.Offset(2, 2),
                        ),
                        visible=True,
                        animate=ft.animation.Animation(300, "decelerate"),
                    )
                ],
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        height=page.window.height,
    )
