import flet as ft
from datetime import datetime
from typing import List
import uuid
import src.database.admin.select_server as select_server
from src.ui.utils.navigation import nav_manager
from src.ui.utils.ui_blocker import block_ui
from src.database.admin.modification_server import mark_notification_as_shown
from src.database.admin.select_server import select_notifications


class NotificationManager:
    def __init__(self, page: ft.Page):
        self.page = page
        self.notifications: List[dict] = []
        self._cached_notifications = []
        self.on_change = None

    @block_ui()
    def load_notifications(self, refresh=False):
        try:
            if refresh or not self._cached_notifications:
                # Загружаем данные только при первом запросе или явном обновлении
                self._cached_notifications = select_notifications(refresh=refresh)

            old_notifications = {n["id"]: n["read"] for n in self.notifications}

            self.notifications = []
            for n in self._cached_notifications:
                notification_id, task_id, notification_type, created_at, is_showed = n

                action_text = self._map_notification_type(notification_type)
                if not action_text:
                    continue

                self.notifications.append({
                    "id": str(notification_id),
                    "title": f"Задание {task_id}",
                    "message": f"Задание было {action_text}",
                    "read": is_showed,
                    "date": created_at,
                    "action": f"/task/{task_id}",
                    "raw_type": notification_type
                })
            # Сортировка по дате (новые сверху)
            self.notifications.sort(
                key=lambda x: datetime.fromisoformat(x['date']),
                reverse=True
            )
            if self.on_change:
                self.on_change()
        except Exception as e:
            print(f"Ошибка загрузки уведомлений: {e}")
            self.notifications = []

        if self.on_change:
            self.on_change()
        return self.notifications

    @block_ui()
    def mark_as_read(self, notification_id):
        try:
            for n in self.notifications:
                if n["id"] == notification_id:
                    n["read"] = True
                    break

            result = mark_notification_as_shown(int(notification_id), refresh=True)
            if result:
                # Обновляем локальное состояние
                for n in self.notifications:
                    if n["id"] == notification_id:
                        n["read"] = True
                        break
                if self.on_change:
                    self.on_change()

            self.load_notifications(refresh=True)
        except Exception as e:
            print(f"Ошибка при обновлении уведомления: {e}")

    def _map_notification_type(self, n_type):
        type_map = {
            "просрочено": "просрочено",
            "выполнено": "выполнено",
            "выполнено с фото": "выполнено с прикреплённой фотографией"
        }
        return type_map.get(n_type, "Системное уведомление")


def notification_tab(page: ft.Page):
    manager = NotificationManager(page)
    unread_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    history_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    initial_filters = {"просрочено", "выполнено", "выполнено с фото"}
    selected_filters = set(initial_filters)

    initial_history_filters = {"просрочено", "выполнено", "выполнено с фото"}
    selected_history_filters = set(initial_history_filters)

    filter_buttons_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=10)

    def update_filter_buttons():
        filter_buttons_row.controls = create_filter_buttons()
        page.update()

    # update_filter_buttons()

    def create_filter_buttons():
        filter_types = {
            "просрочено": ("Просроченные", ft.icons.ACCESS_TIME_FILLED),
            "выполнено": ("Выполненные", ft.icons.CHECK_CIRCLE),
            "выполнено с фото": ("С фото", ft.icons.CAMERA_ALT)
        }

        buttons = []
        for f_type, (text, icon) in filter_types.items():
            is_selected = f_type in selected_filters
            btn = ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(icon, color=ft.colors.BLUE if is_selected else ft.colors.GREY_400),
                    ft.Text(text, color=ft.colors.BLUE if is_selected else ft.colors.GREY_600)
                ]),
                style=ft.ButtonStyle(
                    bgcolor=ft.colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=10),
                    side=ft.BorderSide(
                        width=2,
                        color=ft.colors.BLUE if is_selected else ft.colors.GREY_400
                    )
                ),
                on_click=lambda e, f=f_type: toggle_filter(f)
            )
            buttons.append(btn)
        return buttons

    def create_history_filter_buttons():
        filter_types = {
            "просрочено": ("Просроченные", ft.icons.ACCESS_TIME_FILLED),
            "выполнено": ("Выполненные", ft.icons.CHECK_CIRCLE),
            "выполнено с фото": ("С фото", ft.icons.CAMERA_ALT)
        }

        buttons = []
        for f_type, (text, icon) in filter_types.items():
            is_selected = f_type in selected_history_filters
            btn = ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(icon, color=ft.colors.BLUE if is_selected else ft.colors.GREY_400),
                    ft.Text(text, color=ft.colors.BLUE if is_selected else ft.colors.GREY_600)
                ]),
                style=ft.ButtonStyle(
                    bgcolor=ft.colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=10),
                    side=ft.BorderSide(
                        width=2,
                        color=ft.colors.BLUE if is_selected else ft.colors.GREY_400
                    )
                ),
                on_click=lambda e, f=f_type: toggle_history_filter(f)
            )
            buttons.append(btn)
        return buttons

    def toggle_filter(filter_type):
        if filter_type in selected_filters:
            selected_filters.remove(filter_type)
        else:
            selected_filters.add(filter_type)
        update_filter_buttons()  # Обновляем кнопки после изменения фильтров
        refresh_notifications()

    def toggle_history_filter(filter_type):
        if filter_type in selected_history_filters:
            selected_history_filters.remove(filter_type)
        else:
            selected_history_filters.add(filter_type)
        update_history_filters()
        open_history_dialog(update_only=True)

    def apply_filters(notifications):
        # Если нет активных фильтров - показываем все
        if not selected_filters:
            return notifications
        # Фильтруем по выбранным типам
        return [n for n in notifications if n["raw_type"] in selected_filters]

    def apply_history_filters(notifications):
        if not selected_history_filters:
            return notifications
        return [n for n in notifications if n["raw_type"] in selected_history_filters]

    history_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Column([
            ft.Text("Вся история уведомлений"),
            ft.Row([], scroll=ft.ScrollMode.AUTO)  # Добавляем фильтры
        ]),
        content=ft.Container(
            content=ft.Column([], scroll=ft.ScrollMode.AUTO),
            width=600,
            height=400
        ),
        actions=[
            ft.TextButton("Закрыть", on_click=lambda e: page.close(history_dialog))
        ]
    )

    def update_history_filters():
        history_dialog.title.controls[1].controls = create_history_filter_buttons()
        page.update()

    def open_history_dialog(e=None, update_only=False):
        # Очищаем и заполняем содержимое диалога
        update_history_filters()
        history_column = history_dialog.content.content  # Получаем Column из Container
        history_column.controls.clear()

        # Получаем все прочитанные уведомления
        history_notifications = apply_history_filters(
            [n for n in manager.notifications if n["read"]]
        )

        if not history_notifications:
            history_column.controls.append(
                ft.Row(
                    [ft.Text("История уведомлений пуста", italic=True)],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            )
        else:
            for notification in history_notifications:
                history_column.controls.append(
                    ft.ListTile(
                        title=ft.Text(notification["title"]),
                        subtitle=ft.Text(notification["message"]),
                        trailing=ft.Text(
                            datetime.fromisoformat(notification["date"]).strftime("%d.%m.%Y %H:%M"),
                            size=12
                        ),
                        on_click=lambda e, n=notification: handle_notification_click(n),
                    )
                )

        # Открываем диалог
        if not update_only:
            page.dialog = history_dialog
            page.open(history_dialog)
        page.update()

    def handle_notification_click(notification: dict):
        # Извлекаем task_id из URL действия
        try:
            if history_dialog in page.overlay:
                page.close(history_dialog)

            task_id = int(notification["action"].split("/")[-1])
            notification_id = notification["id"]

            manager.mark_as_read(notification_id)
            handle_task_action(task_id)
        except (IndexError, ValueError) as e:
            print(f"Ошибка получения task_id: {e}")

    def handle_task_action(task_id: int):
        @block_ui(page)
        def load_data():
            return select_server.get_task_details(task_id, refresh=True)
        try:
            data = load_data()
            nav_manager.add_nav_button_and_navigate({
                "icon": ft.icons.INFO,
                "label": "Детали задания",
                "data": "task_details",
                "id": f"task_details_{task_id}",
                "additional_data": data,
            })
            page.update()
        except Exception as e:
            print(f"Ошибка загрузки данных задания: {e}")

    def create_notification_card(notification):
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(
                            ft.icons.NOTIFICATIONS_ACTIVE if not notification["read"]
                            else ft.icons.NOTIFICATIONS_NONE,
                            color=ft.colors.BLUE_600
                        ),
                        ft.Column(
                            [
                                ft.Text(notification["title"], weight=ft.FontWeight.BOLD),
                                ft.Text(notification["message"], size=14),
                                ft.Text(
                                    datetime.fromisoformat(notification["date"]).strftime("%d.%m.%Y %H:%M"),
                                    size=12,
                                    color=ft.colors.GREY
                                )
                            ],
                            expand=True,
                            spacing=5
                        ),
                        ft.IconButton(
                            icon=ft.icons.CLOSE,
                            on_click=lambda e, nid=notification["id"]: manager.mark_as_read(nid),
                            tooltip="Удалить уведомление"
                        )
                    ],
                    spacing=15,
                    vertical_alignment=ft.CrossAxisAlignment.START
                ),
                padding=15,
                bgcolor=ft.colors.BLUE_50 if notification["read"] else ft.colors.WHITE,
                border_radius=10,
                on_click=lambda e, n=notification: handle_notification_click(n),
            ),
            elevation=2 if notification["read"] else 8,
            shadow_color=ft.colors.BLUE_100
        )

    def refresh_notifications(e=None, force_refresh=False):
        unread_column.controls.clear()
        history_column.controls.clear()

        # manager.load_notifications(refresh=True)
        filtered_notifications = apply_filters(
            manager.load_notifications(refresh=force_refresh)
        )

        if not filtered_notifications:
            empty_state = ft.Column(
                [
                    ft.Icon(ft.icons.NOTIFICATIONS_NONE, size=50, color=ft.colors.GREY_400),
                    ft.Text("Нет уведомлений по выбранным фильтрам", size=16, color=ft.colors.GREY_600)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            )
            unread_column.controls.append(empty_state)
        else:
            for notification in filtered_notifications:
                card = create_notification_card(notification)
                if notification["read"]:
                    history_column.controls.append(card)
                else:
                    unread_column.controls.append(card)

        page.update()

    def remove_notification(notification_id):
        manager.notifications = [n for n in manager.notifications if n["id"] != notification_id]
        if manager.on_change:
            manager.on_change()
        refresh_notifications()

    def initial_load():
        update_filter_buttons()  # Инициализируем кнопки фильтров
        refresh_notifications()

    initial_load()

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Уведомления", size=26, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.icons.REFRESH,
                            on_click=lambda e: refresh_notifications(e, force_refresh=True),
                            tooltip="Обновить список"
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                filter_buttons_row,
                # ft.Row(
                #     create_filter_buttons(),
                #     spacing=10,
                #     scroll=ft.ScrollMode.AUTO
                # ),
                ft.Divider(height=20),
                ft.Text("Активные уведомления", size=18, weight=ft.FontWeight.W_600),
                unread_column,
                ft.Divider(height=20),
                ft.Row(
                    [
                        ft.Text("История уведомлений", size=18, weight=ft.FontWeight.W_600),
                        ft.IconButton(
                            icon=ft.icons.HISTORY,
                            on_click=open_history_dialog,
                            tooltip="Показать полную историю"
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                )
            ],
            spacing=15,
            expand=True
        ),
        padding=20,
        expand=True
    )
