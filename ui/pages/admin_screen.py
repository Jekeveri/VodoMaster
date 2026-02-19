import threading
import time

import flet as ft

from src.ui.components.notification_components.notification_tab import notification_tab, NotificationManager
from src.ui.pages.admin_screen_settings import open_settings
from src.ui.pages.controller_tab import controller_tab
from src.ui.pages.meters_tab import meters_tab
from src.ui.pages.search_tab import search_tab
from src.ui.pages.task_controller import employer_tab
from src.ui.pages.master_task_tab import master_task_tab
from src.ui.pages.task_details import task_details
from src.ui.pages.emploer_details import employer_details
from src.ui.pages.home_tab import home_tab
from src.ui.utils.confirmation_dialog import ConfirmationDialogManager
from src.ui.utils.navigation import nav_manager
from src.ui.utils.ui_blocker import block_ui
from src.ui.pages.acts_tab import acts_tab
from src.ui.pages.graphs_tab import graphs_tab
from src.ui.pages.address_tab import address_tab
from src.ui.pages.address_details import address_details


def admin_main(page: ft.Page):
    page.bgcolor = ft.colors.BLUE_200
    page.padding = 0
    page.spacing = 0

    sidebar_expanded = ft.Ref[bool]()
    sidebar_expanded.current = True
    badge = ft.Ref[ft.Container]()

    def update_badge():
        count = sum(1 for n in manager.notifications if not n["read"])
        print(f"Обновление бейджа: {count} уведомлений")

        if badge.current:  # Проверяем, что бейдж существует
            badge.current.content.value = str(count)
            badge.current.visible = count > 0
            page.update()

    manager = NotificationManager(page)
    manager.load_notifications(refresh=True)
    update_badge()

    last_activity_time = time.time()

    def handle_activity(_):
        nonlocal last_activity_time
        last_activity_time = time.time()

    page.on_keyboard_event = handle_activity
    page.on_pointer_event = handle_activity

    def check_notifications_loop():
        while True:
            is_active = (time.time() - last_activity_time) < 60
            if is_active:
                try:
                    manager.load_notifications(refresh=True)
                    update_badge()
                except Exception as e:
                    print(f"Ошибка автообновления: {e}")

                time.sleep(90)
            else:
                try:
                    manager.load_notifications(refresh=True)
                    update_badge()
                except Exception as e:
                    print(f"Ошибка автообновления: {e}")

                time.sleep(600)

    threading.Thread(target=check_notifications_loop, daemon=True).start()

    manager.on_change = update_badge

    content_area = ft.Container(
        expand=True,
        content=home_tab(page),
        bgcolor=ft.colors.SURFACE,
        border_radius=15,
        padding=20,
    )

    def on_close(e):
        nav_manager.save_closed_pages()

        if hasattr(page, 'active_popups'):
            for popup in page.active_popups[:]:
                popup.close()
            page.active_popups.clear()

        if hasattr(page, 'active_page_panels'):
            for panel in page.active_page_panels[:]:
                panel.close()
            page.active_page_panels.clear()

        page.update()

    page.on_close = on_close

    def change_page(button_data):
        block_ui(page)

        if hasattr(page, 'active_popups'):
            for popup in page.active_popups[:]:
                popup.close()
            page.active_popups.clear()

        if hasattr(page, 'active_page_panels'):
            for panel in page.active_page_panels[:]:
                panel.hide()
            page.active_page_panels.clear()

        if button_data.get('data') != "settings":
            # PagePanel._instance.hide()
            pass

        def load_page_content():
            try:
                selected_page = button_data['data']
                additional_data = button_data.get('additional_data', {})

                if selected_page == 'back_navigation':
                    remove_nav_button(nav_manager.current_page, nav_manager.current_additional_data)

                if selected_page == "settings":
                    block_ui(page)
                    open_settings(page)
                    page.update()
                    return

                content_map = {
                    "home": home_tab,
                    "search": search_tab,
                    "master_task": master_task_tab,
                    # "assignment": assignment_tab,
                    "controller": controller_tab,
                    "meters": meters_tab,
                    "acts_tab": lambda p: acts_tab(p),
                    "address_tab": lambda p: address_tab(p),
                    "graphs_tab": lambda p: graphs_tab(p),
                    "address_details": lambda p: address_details(p, additional_data),
                    "notifications": lambda p: notification_tab(p),
                    "task_controller": lambda p: employer_tab(p, additional_data),
                    "empl_details": lambda p: employer_details(p, additional_data),
                    "task_details": lambda p: task_details(p, additional_data),
                }

                if selected_page in content_map:
                    new_content = content_map[selected_page](page)

                    content_area.content = new_content

                    nav_manager.current_page = button_data.get('id', 'btn_home')
                    nav_manager.current_additional_data = additional_data

                    block_ui(page)
                    update_sidebar()

            except Exception as e:
                block_ui(page)
                show_snack_bar(page, f"Ошибка: {str(e)}")

        load_page_content()

    def show_notifications(e):
        change_page({"data": "notifications", "id": "btn_notifications"})

    def create_nav_button(icon, label, data, button_id=None, additional_data=None, deletable=False):
        icon_name = icon.value if hasattr(icon, 'value') else icon

        button_row = ft.Row(
            [
                ft.Icon(name=icon_name, color=ft.colors.ON_PRIMARY),
                ft.Text(label, size=16, color=ft.colors.ON_PRIMARY, expand=True),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
            expand=True,
        )

        delete_button = None
        if deletable and button_id is not None:
            delete_button = ft.Container(
                content=ft.Icon(name=ft.icons.CLOSE, color=ft.colors.ON_PRIMARY, size=20),
                width=25,
                height=25,
                alignment=ft.alignment.center,
                on_click=lambda _, bid=button_id: remove_nav_button(bid, additional_data),
                border_radius=5,
                visible=sidebar_expanded.current,
                ink=True,
                padding=2,
                ink_color=ft.colors.with_opacity(0.3, ft.colors.ON_PRIMARY)
            )
            button_row.controls.append(delete_button)

        nav_container = ft.Container(
            content=button_row,
            data={
                "id": button_id,
                "data": data,
                "additional_data": additional_data or {},
                "delete_button": delete_button
            },
            on_click=lambda e: change_page(e.control.data),
            ink=True,
            padding=10,
            height=45,
            border_radius=10,
        )

        return nav_container

    def remove_nav_button(button_id, additional_data=None):
        def confirm_remove():
            buttons_to_remove = [
                btn for btn in nav_manager.additional_nav_buttons
                if btn["id"] == button_id and
                   btn.get("additional_data") == additional_data
            ]

            for btn in buttons_to_remove:
                nav_manager.add_closed_page({
                    "id": btn["id"],
                    "label": btn["label"],
                    "icon": btn["icon"],
                    "data": btn["data"],
                    "additional_data": btn.get("additional_data", {})
                })
                change_page({"id": "btn_home", "data": "home"})
                nav_manager.additional_nav_buttons.remove(btn)

            update_sidebar()

        ConfirmationDialogManager.show_confirmation_dialog(
            page=page,
            title="Удаление вкладки",
            message="У вас есть несохраненные изменения. Продолжить?",
            on_confirm=confirm_remove,
            dialog_type='remove_nav_button'
        )

    toggle_button = ft.IconButton(
        icon=ft.icons.CHEVRON_LEFT,
        tooltip="Свернуть меню",
        icon_color=ft.colors.ON_PRIMARY,
        padding=10,
        on_click=lambda _: toggle_sidebar(),
    )

    badge = ft.Ref[ft.Container]()
    notification_badge = ft.Container(
        content=ft.Text("0", color="white", size=10),
        bgcolor="red",
        padding=ft.padding.all(3),
        border_radius=50,
        top=0,
        left=5,
        visible=False,
        ref=badge
    )

    sidebar_header = ft.Row(
        controls=[
            toggle_button,
            ft.Text('Меню мастера', size=16),
            ft.Container(
                ft.Stack([
                    ft.IconButton(
                        icon=ft.icons.NOTIFICATIONS,
                        on_click=show_notifications,
                        icon_color=ft.colors.WHITE
                    ),
                    notification_badge
                ]),
                alignment=ft.alignment.center_right,
                expand=True
            )
        ],
        alignment=ft.MainAxisAlignment.START,
        spacing=10,
    )

    settings_button = create_nav_button(ft.icons.SETTINGS, "Настройки", "settings")

    nav_items = [
        {"icon": "HOME", "label": "Главная", "data": "home", "id": "btn_home"},
        {"icon": "search", "label": "Поиск заданий", "data": "search", "id": "btn_search"},
        {"icon": "ASSIGNMENT", "label": "Мои задания", "data": "master_task", "id": "btn_master_task"},
        # {"icon": ft.icons.ASSIGNMENT, "label": "Не назначенные", "data": "assignment", "id": "btn_assignment"},
        {"icon": "people", "label": "Сотрудники", "data": "controller", "id": "btn_controller"},
        # {"icon": "gas_meter", "label": "Счетчики", "data": "meters", "id": "btn_meters"},
    ]

    nav_buttons = [create_nav_button(item["icon"], item["label"], item["data"], item.get("id"), deletable=False) for
                   item in nav_items]

    for item in nav_items:
        nav_manager.add_main_nav_item(item)

    sidebar = ft.Container(
        content=ft.Column(
            controls=[
                sidebar_header,
                *nav_buttons,
                ft.Divider(),
                ft.Container(expand=True),
                settings_button,
            ],
            spacing=10,
            expand=True,
        ),
        width=250,
        bgcolor=ft.colors.PRIMARY,
        padding=8,
        border_radius=15,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.colors.BLUE_GREY_400,
            offset=ft.Offset(0, 5),
        ),
    )

    def toggle_sidebar():
        sidebar_expanded.current = not sidebar_expanded.current
        sidebar.width = 250 if sidebar_expanded.current else 60
        all_buttons = nav_buttons + [
            create_nav_button(btn["icon"], btn["label"], btn["data"], btn.get('id'), btn.get('additional_data', {}))
            for btn in nav_manager.get_additional_buttons()
        ]
        for btn in all_buttons + [settings_button]:
            if hasattr(btn, 'content') and btn.content and hasattr(btn.content, 'controls'):
                if len(btn.content.controls) > 1:
                    btn.content.controls[1].visible = sidebar_expanded.current

            # Безопасная проверка delete_button
            if hasattr(btn, 'data') and btn.data and 'delete_button' in btn.data:
                delete_btn = btn.data['delete_button']
                if delete_btn is not None:
                    delete_btn.visible = sidebar_expanded.current

        toggle_button.icon = (
            ft.icons.CHEVRON_LEFT if sidebar_expanded.current else ft.icons.CHEVRON_RIGHT
        )
        update_sidebar()
        page.update()

    def update_sidebar():
        all_buttons = nav_buttons + [
            create_nav_button(
                btn["icon"],
                btn["label"],
                btn["data"],
                btn.get('id'),
                btn.get('additional_data', {}),
                deletable=True
            )
            for btn in nav_manager.get_additional_buttons()
        ]

        for btn in all_buttons + [settings_button]:
            is_active = (
                    btn.data and
                    btn.data.get('id') == nav_manager.current_page and
                    # Добавляем более строгое сравнение additional_data
                    (not btn.data.get('additional_data') or
                     btn.data.get('additional_data') == nav_manager.current_additional_data)
            )

            btn.bgcolor = ft.colors.PRIMARY_CONTAINER if is_active else None

            if btn.content and hasattr(btn.content, 'controls') and btn.content.controls:
                btn.content.controls[0].color = ft.colors.PRIMARY if is_active else ft.colors.ON_PRIMARY

                if len(btn.content.controls) > 1:
                    btn.content.controls[1].color = ft.colors.PRIMARY if is_active else ft.colors.ON_PRIMARY
                    btn.content.controls[1].visible = sidebar_expanded.current

            if btn.data and isinstance(btn.data, dict) and 'delete_button' in btn.data:
                delete_btn = btn.data['delete_button']
                if delete_btn:
                    delete_btn.visible = sidebar_expanded.current

                    if hasattr(delete_btn, 'content'):
                        delete_btn.content.color = (
                            ft.colors.PRIMARY if is_active
                            else ft.colors.ON_PRIMARY
                        )

        dynamic_buttons_container = ft.Column(
            controls=[btn for btn in all_buttons if btn not in nav_buttons],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )

        # badge = ft.Container(
        #     content=ft.Text("0", color="white", size=10),
        #     bgcolor="red",
        #     padding=ft.padding.all(3),
        #     border_radius=50,
        #     top=0,
        #     left=5,
        #     visible=False
        # )

        sidebar.content = ft.Column(
            controls=[
                ft.Row(
                    [toggle_button,
                     ft.Text('Меню мастера', size=16, color=ft.colors.ON_PRIMARY),
                     ft.Container(
                         ft.Stack(
                             [
                                 ft.IconButton(icon=ft.icons.NOTIFICATIONS,
                                               on_click=show_notifications,
                                               icon_color=ft.colors.WHITE,
                                               padding=5),
                                 notification_badge
                             ]
                         ), expand=True, alignment=ft.alignment.center_right
                     )
                     ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                ),
                *nav_buttons,
                ft.Divider(),
                dynamic_buttons_container,
                settings_button,
            ]
        )

        page.update()

    main_layout = ft.Row(
        controls=[
            ft.Container(content=sidebar, padding=5),
            ft.Container(content=content_area, expand=True, padding=5),
        ],
        expand=True,
        spacing=0,
    )

    nav_manager.current_page = "btn_home"
    nav_manager.set_update_callback(update_sidebar)
    nav_manager.set_navigate_callback(change_page)

    update_badge()

    page.add(main_layout)
    update_sidebar()
    page.update()


def show_snack_bar(page: ft.Page, message: str):
    page.snack_bar = ft.SnackBar(ft.Text(message))
    page.snack_bar.open = True
    # page.update()
