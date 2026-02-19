from src.core.session_manager import session_manager
from src.core.verifications import authentication
from src.ui.components.navigations import role_definition


def check_session(page):
    """Проверяет наличие активной сессии"""
    try:
        # Проверяем все сессии
        sessions = session_manager._load_sessions()
        for user_id, session in sessions.items():
            session_data = session_manager.get_session(int(user_id))
            if session_data and session_data.get('privileges'):
                return role_definition(page)
        return False
    except Exception as e:
        print(f"Ошибка при проверке сессии: {e}")
        return False


def toggle_sessions(page):
    """Проверяет сессию и перенаправляет пользователя"""
    if not check_session(page):
        authentication(page)


def logout(page):
    """Выход из системы"""
    try:
        # Получаем текущего пользователя
        sessions = session_manager._load_sessions()
        for user_id in sessions:
            session_manager.delete_session(int(user_id))
        
        # Очищаем страницу и перенаправляем на страницу входа
        page.clean()
        authentication(page)
    except Exception as e:
        print(f"Ошибка при выходе из системы: {e}")
        # В случае ошибки все равно перенаправляем на страницу входа
        page.clean()
        authentication(page)
