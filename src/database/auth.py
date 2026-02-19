from src.core.session_manager import session_manager
from src.database.api.api_master import create_master_api_client
from src.ui.components.navigations import role_definition
from src.utils.show_snack_bar import show_snack_bar


def check_user_credentials(login, password, page):
    """Проверка учетных данных пользователя через API"""
    try:
        # Создаем API-клиента с переданными учетными данными
        api_client = create_master_api_client(login, password)
        
        # Вызываем метод авторизации
        auth_response = api_client.login()
        
        # Проверяем успешность авторизации
        if auth_response and 'employee_id' in auth_response:
            # Подготавливаем данные сессии
            session_data = {
                'login': auth_response['login'],
                'password': password,
                'privileges': auth_response['privileges'],
                'first_name': auth_response['first_name'],
                'last_name': auth_response['last_name']
            }
            
            # Создаем сессию
            if auth_response['privileges'] == 1:
                session_manager.create_session(
                    auth_response['employee_id'], 
                    session_data
                )
                role_definition(page)
                return True
            else:
                show_snack_bar(page, "Пользовательский интерфейс предназначен для мобильных устройств")
                return False
        else:
            # Если авторизация не удалась
            show_snack_bar(page, "Неверный логин или пароль")
            return False
    
    except Exception as e:
        print(f"Ошибка при проверке учетных данных через API: {e}")
        show_snack_bar(page, "Произошла ошибка при проверке учетных данных")
        return False