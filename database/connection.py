from src.core.session_manager import SessionManager


def get_session_credentials():
    """Получить логин и пароль из текущей сессии"""
    session_manager = SessionManager()
    current_user_id = session_manager.get_current_user_id()

    if current_user_id is None:
        print("DEBUG: Текущий пользователь не установлен")
        return None, None

    session_data = session_manager.get_session(current_user_id)

    if session_data is None:
        print("DEBUG: Сессия не найдена")
        return None, None

    login = session_data.get('login')
    password = session_data.get('password')

    return login, password
