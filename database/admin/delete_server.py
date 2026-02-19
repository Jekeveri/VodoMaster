from diskcache import Cache

from src.database.api.api_master import create_master_api_client
from src.database.connection import get_session_credentials

cache = Cache('./local_cache')


def delete_tasks(task_ids):
    try:
        # Получаем учетные данные из текущей сессии
        login, password = get_session_credentials()

        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return None

        # Создаем API-клиента с текущими учетными данными
        api_client = create_master_api_client(login, password)

        # Вызываем метод удаления задач
        result = api_client.delete_tasks(task_ids)

        # Очищаем кеш связанный с задачами
        cache.delete("unmade_tasks")
        cache.delete("all_tasks")

        return result

    except Exception as e:
        print(f"Ошибка при удалении задач: {e}")
        return None


def delete_employee(employee_ids):
    try:
        # Получаем учетные данные из текущей сессии
        login, password = get_session_credentials()

        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return None

        # Создаем API-клиента с текущими учетными данными
        api_client = create_master_api_client(login, password)

        # Удаляем каждого сотрудника по отдельности
        result = api_client.delete_employee(employee_ids)

        # Очищаем кеш связанный с сотрудниками
        cache.delete("all_employees")

        return result

    except Exception as e:
        print(f"Ошибка при удалении сотрудников: {e}")
        return None
