from typing import Dict, List, Any, Optional, Tuple

from diskcache import Cache

from src.database.api.api_master import create_master_api_client
from src.database.connection import get_session_credentials

cache = Cache('./local_cache')


def send_task_data(task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        # Получаем учетные данные из текущей сессии
        login, password = get_session_credentials()

        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return None

        api_client = create_master_api_client(login, password)
        result = api_client.upsert_task(task_data)

        if not result:
            print(f"Ошибка при отправке данных задачи: {result}")
            return None

        cache.delete("unmade_tasks")
        cache.delete("all_tasks")

        return result

    except Exception as e:
        print(f"Ошибка при отправке данных задачи: {e}")
        return None


def send_tasks_bulk(tasks_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    try:
        login, password = get_session_credentials()

        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return None

        print(tasks_data)

        api_client = create_master_api_client(login, password)
        result = api_client.insert_tasks_bulk(tasks_data)

        if not result:
            print(f"Ошибка при массовой отправке задач: {result}")
            return None

        cache.delete("unmade_tasks")
        cache.delete("all_tasks")

        return result

    except Exception as e:
        print(f"Ошибка при массовой отправке задач: {e}")
        return None


def send_employee_data(employee_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        # Получаем учетные данные из текущей сессии
        login, password = get_session_credentials()

        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return None

        api_client = create_master_api_client(login, password)
        result = api_client.upsert_employee(employee_data)

        if not result:
            print(f"Ошибка при отправке данных сотрудника: {result}")
            return None

        cache.delete("all_employees")
        if 'id' in employee_data:
            cache.delete(f"employee_details_{employee_data['id']}")

        return result

    except Exception as e:
        print(f"Ошибка при отправке данных сотрудника vvv: {e}")
        return None


def set_employer_to_task(task_ids, emp_id, fio_name):
    try:
        login, password = get_session_credentials()

        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return None

        update_tasks_data = {
            "task_ids": task_ids,
            "emp_id": emp_id,
            "fio_name": fio_name
        }

        api_client = create_master_api_client(login, password)
        result = api_client.set_employee_to_task(update_tasks_data)

        if not result:
            print(f"Ошибка при назначении задачи: {result}")
            return None

        cache.delete("all_employees")
        cache.delete("unmade_tasks")
        cache.delete("all_tasks")
        cache.delete(f"employee_details_{emp_id}")

        return result
    except Exception as ex:
        print(f"Ошибка при назначении задачи: {ex}")


def unassign_tasks(task_ids: List[int], fio_emp: List[int]) -> Optional[Dict[str, Any]]:
    try:
        login, password = get_session_credentials()
        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return None

        api_client = create_master_api_client(login, password)
        result = api_client.unassign_tasks(task_ids, fio_emp)

        cache.delete("unmade_tasks")
        cache.delete("all_tasks")

        return result
    except Exception as e:
        print(f"Ошибка при отмене назначения задач: {e}")
        return None


def mark_notification_as_shown(notification_id: int, refresh: bool = False) -> Tuple:
    """Пометить уведомление как прочитанное"""
    try:
        login, password = get_session_credentials()
        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return ()

        # Инвалидация кеша уведомлений
        cache.delete("user_notifications")

        api_client = create_master_api_client(login, password)
        response = api_client.mark_notification_as_shown(notification_id)

        # Преобразование ответа в кортеж
        converted_response = (
            response.get('id', 0),
            response.get('task_id', 0),
            response.get('notification_type', ''),
            response.get('created_at', ''),
            response.get('is_showed', False)
        )

        if refresh:
            cache.delete(f"notification_{notification_id}")

        return converted_response

    except Exception as e:
        print(f"Общая ошибка при обновлении уведомления: {str(e)}")
        return None
