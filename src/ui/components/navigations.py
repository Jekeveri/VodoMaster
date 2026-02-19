from src.core.session_manager import session_manager
from src.utils.show_snack_bar import show_snack_bar


def role_definition(page):
    """Определяет роль пользователя и перенаправляет на соответствующий экран"""
    try:
        # Очищаем страницу перед переходом
        page.clean()
        page.controls.clear()
        
        # Проверяем сессию и определяем роль
        sessions = session_manager._load_sessions()
        for user_id, session in sessions.items():
            session_data = session_manager.get_session(int(user_id))
            if session_data:
                privileges = session_data.get('privileges')
                if privileges == 1:  # Admin
                    from src.ui.pages.admin_screen import admin_main
                    admin_main(page)
                    return True
                elif privileges == 2:  # User
                    show_snack_bar(page, "Пользовательский интерфейс предназначен для мобильных устройств")
                    return False
        
        show_snack_bar(page, "Ошибка: сессия не найдена")
        return False
    except Exception as e:
        print(f"Ошибка при определении роли: {e}")
        show_snack_bar(page, f"Ошибка при определении роли: {e}")
        return False


def debugging():
    """Функция для отладки и обратной связи"""
    print('Тут можно добавить инфу по приложению, может быть обратную связь')
