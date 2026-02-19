import functools
import sys
from typing import Callable, Optional

import flet as ft

from src.utils.show_snack_bar import show_snack_bar


def block_ui(page: Optional[ft.Page] = None):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Пытаемся найти страницу
            current_page = page

            # Проверяем kwargs на наличие страницы
            if current_page is None and 'page' in kwargs:
                current_page = kwargs['page']

            # Проверяем аргументы
            if current_page is None:
                for arg in list(args) + list(kwargs.values()):
                    if isinstance(arg, ft.Page):
                        current_page = arg
                        break

            # Если страница не найдена, пробуем извлечь из первого аргумента
            if current_page is None and args:
                first_arg = args[0]
                if hasattr(first_arg, 'page'):
                    current_page = first_arg.page
                elif hasattr(first_arg, 'Page'):
                    current_page = first_arg.Page

            # Если страница все еще не найдена, пробуем получить из текущего контекста
            if current_page is None:
                # Ищем страницу в глобальных переменных
                for name, value in sys.modules.items():
                    if hasattr(value, 'page') and isinstance(getattr(value, 'page'), ft.Page):
                        current_page = getattr(value, 'page')
                        break

            # Если страница все еще не найдена, выбрасываем исключение
            if current_page is None:
                raise ValueError(
                    "Не удалось найти страницу для блокировки UI. "
                    "Передайте страницу явно в декоратор или в аргументы функции."
                )

            # Создаем полупрозрачный фон
            overlay_bg = ft.Container(
                width=current_page.width,
                height=current_page.height,
                bgcolor=ft.colors.BLACK45,
                opacity=0.5
            )

            # Создаем индикатор загрузки
            progress_ring = ft.Container(
                content=ft.ProgressRing(width=50, height=50),
                alignment=ft.alignment.center,
                width=current_page.width,
                height=current_page.height
            )

            # Добавляем оверлеи
            current_page.overlay.append(overlay_bg)
            current_page.overlay.append(progress_ring)
            current_page.update()

            try:
                # Выполняем основную функцию
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                # Обработка ошибок
                show_snack_bar(page, f"Ошибка: {str(e)}")
                raise
            finally:
                # Убираем индикаторы загрузки
                if overlay_bg in current_page.overlay:
                    current_page.overlay.remove(overlay_bg)
                if progress_ring in current_page.overlay:
                    current_page.overlay.remove(progress_ring)
                current_page.update()

        return wrapper

    return decorator
