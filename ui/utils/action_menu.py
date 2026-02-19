import flet as ft


class PopupMenuUp:
    def __init__(self, items, page, icon=ft.Icons.MORE_VERT):
        self.page = page
        self.items = items
        self.icon = icon
        self.menu_overlay = None

        self.button = ft.IconButton(icon=self.icon, on_click=self.toggle_menu)
        self.container = ft.Container(content=self.button, ref=ft.Ref())  # обёртка с ссылкой
        self.stack = ft.Stack([self.container])  # Добавим кнопку и позже меню

        # Регистрируем себя в списке активных попапов страницы
        if not hasattr(page, 'active_popups'):
            page.active_popups = []
        page.active_popups.append(self)

    def set_items(self, items):
        self.items = items

        # Если меню уже открыто — перерисовать его
        if self.menu_overlay and self.menu_overlay in self.page.overlay:
            self.toggle_menu(None)  # Закрыть
            self.toggle_menu(None)  # Открыть заново с новыми пунктами

    def update_items(self, selected_count):
        # Пример логики: разные кнопки для разных состояний
        if selected_count == 0:
            self.items = []  # Ничего не показываем
        elif selected_count == 1:
            self.items = [
                {"text": "Редактировать", "on_click": lambda e: print("Редактировать"),
                 "icon": ft.Icon(ft.icons.EDIT, color=ft.colors.ORANGE_600)}
            ]
        else:
            self.items = [
                {"text": f"Удалить ({selected_count})", "on_click": lambda e: print("Удалить"),
                 "icon": ft.Icon(ft.icons.DELETE, color=ft.colors.RED_600)}
            ]

        # Перерисовать, если меню открыто
        if self.menu_overlay and self.menu_overlay in self.page.overlay:
            self.toggle_menu(None)  # Закрыть текущее
            self.toggle_menu(None)  # Открыть заново с обновлённым списком

    def close(self):
        # Удаляем меню из overlay
        if self.menu_overlay and self.menu_overlay in self.page.overlay:
            self.page.overlay.remove(self.menu_overlay)
            self.page.update()
        self.menu_overlay = None

        # Удаляем себя из списка активных попапов
        if self in self.page.active_popups:
            self.page.active_popups.remove(self)

    def toggle_menu(self, e):
        page = self.page

        if self.menu_overlay:
            page.overlay.remove(self.menu_overlay)
            self.menu_overlay = None
            page.update()
            return

        for popup in self.page.active_popups[:]:
            if popup != self:
                popup.close()

        # Отображаем меню над кнопкой
        # Исправленная версия блока menu_overlay
        self.menu_overlay = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Дополнительные действия",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=ft.colors.BLUE_900,
                            expand=True,
                            text_align=ft.TextAlign.CENTER),
                    ft.Divider(height=1, color=ft.colors.BLUE_100),
                    ft.Container(ft.Column(
                        controls=[
                            ft.Container(
                                content=ft.Row([
                                    item['icon'],
                                    ft.Text(item['text'],
                                            size=14,
                                            text_align=ft.TextAlign.LEFT,
                                            color=ft.colors.GREY_700,
                                            expand=True)
                                ], spacing=10, run_spacing=10),
                                ink=True,
                                padding=5,
                                border_radius=8,
                                bgcolor=ft.colors.GREY_200,
                                shadow=ft.BoxShadow(
                                    color=ft.colors.BLUE_GREY_300,
                                    offset=ft.Offset(0, 1),
                                    blur_radius=3
                                ),
                                on_click=item['on_click'],
                                animate=ft.animation.Animation(300, "easeOutBack"),
                            ) for item in self.items
                        ],
                        spacing=8
                    ), padding=ft.padding.only(0, 20, 0, 10))
                ],
                tight=True,
                spacing=0,
            ),
            bgcolor=ft.colors.WHITE,
            border_radius=8,
            padding=15,
            width=250,
            right=50,
            bottom=85,
            shadow=ft.BoxShadow(
                color=ft.colors.BLUE_GREY_300,
                offset=ft.Offset(0, 0),
                blur_radius=7,
                spread_radius=1,
            ),
            animate_scale=ft.animation.Animation(400, "easeOutQuint"),
            animate_opacity=ft.animation.Animation(300, "easeOutQuad")
        )

        page.overlay.append(self.menu_overlay)
        page.update()

    def get_view(self):
        return self.stack
