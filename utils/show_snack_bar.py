import flet as ft


def show_snack_bar(page, message):
    """Показать всплывающее сообщение"""
    snack_bar = ft.SnackBar(
        content=ft.Text(message),
        action="Ок",
        duration=800,
        open=True
    )
    page.overlay.append(snack_bar)
    page.update()
