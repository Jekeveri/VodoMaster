from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from datetime import date

from diskcache import Cache

from src.database.api.api_master import create_master_api_client
from src.database.connection import get_session_credentials

cache = Cache('./local_cache')


def select_task_data_all(refresh: bool = False):
    """Получить все задачи"""
    try:
        cache_key = "all_tasks"  # Ключ для кеша

        if refresh:
            print("Обновление данных...")
            cache.delete(cache_key)

        # Проверяем кеш, если не требуется обновление
        if not refresh and cache_key in cache:
            print("Загружаем данные из кеша...")
            return cache[cache_key]

        login, password = get_session_credentials()

        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return []

        api_client = create_master_api_client(login, password)
        tasks_data = api_client.get_all_tasks()

        # Преобразование словарей в кортежи
        converted_tasks = []
        for task in tasks_data:
            converted_task = (
                task.get('task_id', 0),  # ID задачи
                task.get('customer_name', ''),  # ФИО клиента
                task.get('address_id', ''),  # Адрес клиента
                task.get('city', ''),  # Город
                task.get('district', ''),  # Район
                task.get('street', ''),  # Улица
                task.get('hamlet', ''),
                task.get('dom', ''),  # Дом
                task.get('apartment', ''),  # Квартира
                task.get('entrance', ''),  # Подъезд
                task.get('registered_residing', ''),  # Зарегистрированные жильцы
                task.get('address_status', ''),  # Статус адреса
                task.get('standarts', ''),  # Стандарты
                task.get('area', ''),  # Площадь
                task.get('phone_number') or '',  # Телефон
                task.get('personal_account', 0),  # Лицевой счет
                task.get('task_date', ''),  # Дата задачи
                task.get('remark', ''),  # Примечание
                task.get('task_status', ''),  # Статус задачи
                task.get('purpose', ''),  # Цель
                task.get('saldo', ''),  # Сальдо
                task.get('employer_name', ''),
                task.get('date_end', ''),
                task.get('master', ''),
                task.get('meters', {}),
                task.get('acts', {}),
                task.get('photos', {})
            )
            converted_tasks.append(converted_task)

        cache.set(cache_key, converted_tasks, expire=3600)
        return converted_tasks
    except Exception as e:
        print(f"Ошибка при получении всех задач: {e}")
        return []


def get_completed_tasks_export(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        refresh: bool = False
):
    """Получить экспортированные завершенные задачи с кешированием"""
    try:
        # Формируем ключ кеша на основе дат
        cache_key = f"completed_tasks_{start_date}_{end_date}"

        if refresh:
            print("Обновление данных завершенных задач...")
            cache.delete(cache_key)

        if not refresh and cache_key in cache:
            print("Загружаем данные завершенных задач из кеша...")
            return cache[cache_key]

        login, password = get_session_credentials()
        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return []

        api_client = create_master_api_client(login, password)

        response = api_client.export_completed_tasks(
            start_date=start_date,
            end_date=end_date
        )

        tasks = response.get("tasks", [])

        cache.set(cache_key, tasks, expire=3600)
        return tasks

    except Exception as e:
        print(f"Ошибка при получении завершенных задач: {e}")
        return []


def select_address_data_all(refresh: bool = False):
    """Получить все адреса с кешированием"""
    try:
        cache_key = "all_addresses"  # Уникальный ключ кеша

        # Принудительное обновление кеша
        if refresh:
            print("Инициировано обновление кеша адресов...")
            cache.delete(cache_key)

        # Попытка загрузки из кеша
        if not refresh and cache_key in cache:
            print("Загрузка адресов из кеша...")
            return cache[cache_key]

        # Получение учетных данных
        login, password = get_session_credentials()
        if not login or not password:
            print("Ошибка аутентификации: отсутствуют учетные данные")
            return []

        # Запрос данных через API
        api_client = create_master_api_client(login, password)
        raw_addresses = api_client.get_all_addresses()  # Предполагаем существование метода

        # Преобразование данных
        processed_addresses = []
        for addr in raw_addresses:
            address_entry = (
                addr.get('address_id', 0),
                addr.get('customer_id', 0),
                addr.get('customer_full_name', ''),
                addr.get('hamlet_id', 0),
                addr.get('hamlet_name', ''),
                addr.get('street_id', 0),
                addr.get('street_name', ''),
                addr.get('city', ''),
                addr.get('district', ''),
                addr.get('address_type', ''),
                addr.get('house_number', ''),
                addr.get('apartment', ''),
                addr.get('entrance', ''),
                addr.get('area', 0),
                addr.get('standarts', 0),
                addr.get('registered_residing', '')
            )
            processed_addresses.append(address_entry)

        # Кеширование на 1 час
        cache.set(cache_key, processed_addresses, expire=3600)
        return processed_addresses

    except Exception as e:
        print(f"Критическая ошибка в select_address_data_all: {str(e)}")
        # Можно добавить отправку ошибки в систему мониторинга
        return []


def get_address_details(address_id, refresh: bool = False):
    """Получить детали конкретной задачи"""
    try:
        cache_key = f"address_details_{address_id}"

        if refresh:
            print("Обновление данных...")
            cache.delete(cache_key)

        # Проверяем кеш, если не требуется обновление
        if not refresh and cache_key in cache:
            print("Загружаем данные из кеша...")
            return cache[cache_key]

        login, password = get_session_credentials()

        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return None

        api_client = create_master_api_client(login, password)

        address = api_client.get_address_details(address_id)

        if not address:
            print(f"Задача с ID {address_id} не найдена")
            return None

        converted_task = {
            'address_info': address.get('address_info', []),
            'meters': address.get('meters', []),
            'tasks': address.get('tasks', []),
        }

        cache.set(cache_key, converted_task, expire=3600)
        return converted_task
    except Exception as e:
        print(f"Ошибка при получении деталей задачи {address_id}: {e}")
        return None


def select_task_data_unmade(refresh: bool = False):
    """Получить неназначенные задачи"""
    try:
        cache_key = "unmade_tasks"  # Ключ для кеша

        if refresh:
            print("Обновление данных...")
            cache.delete(cache_key)

        # Проверяем кеш, если не требуется обновление
        if not refresh and cache_key in cache:
            print("Загружаем данные из кеша...")
            return cache[cache_key]

        login, password = get_session_credentials()

        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return []

        api_client = create_master_api_client(login, password)
        tasks = api_client.get_unassigned_tasks()

        print(tasks)

        # Преобразование словарей в кортежи
        converted_tasks = []
        for task in tasks:
            converted_task = (
                task.get('task_id', 0),  # ID задачи
                task.get('customer_name', ''),  # ФИО клиента
                task.get('address_id', ''),  # Адрес клиента
                task.get('city', ''),  # Город
                task.get('district', ''),  # Район
                task.get('street', ''),  # Улица
                task.get('hamlet', ''),
                task.get('dom', ''),  # Дом
                task.get('apartment', ''),  # Квартира
                task.get('entrance', ''),  # Подъезд
                task.get('registered_residing', ''),  # Зарегистрированные жильцы
                task.get('address_status', ''),  # Статус адреса
                task.get('standarts', ''),  # Стандарты
                task.get('area', ''),  # Площадь
                task.get('phone_number') or '',  # Телефон
                task.get('personal_account') or '',  # Лицевой счет
                task.get('task_date', ''),  # Дата задачи
                task.get('remark', ''),  # Примечание
                task.get('task_status', ''),  # Статус задачи
                task.get('purpose', ''),  # Цель
                task.get('saldo', ''),  # Сальдо
                task.get('date_end', ''),
            )
            converted_tasks.append(converted_task)

        cache.set(cache_key, converted_tasks, expire=3600)
        return converted_tasks
    except Exception as e:
        print(f"Ошибка при получении всех задач: {e}")
        return []


def get_task_details(task_id, refresh: bool = False):
    """Получить детали конкретной задачи"""
    try:
        cache_key = f"task_details_{task_id}"

        if refresh:
            print("Обновление данных...")
            cache.delete(cache_key)

        # Проверяем кеш, если не требуется обновление
        if not refresh and cache_key in cache:
            print("Загружаем данные из кеша...")
            return cache[cache_key]

        login, password = get_session_credentials()

        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return None

        api_client = create_master_api_client(login, password)

        tasks = api_client.get_task_details(task_id)

        if not tasks:
            print(f"Задача с ID {task_id} не найдена")
            return None

        converted_task = {
            'task': tasks.get('task', []),
            'acts': tasks.get('acts', []),
            'meters': tasks.get('meters', []),
            'photos': tasks.get('photos', []),
        }

        cache.set(cache_key, converted_task, expire=3600)
        return converted_task
    except Exception as e:
        print(f"Ошибка при получении деталей задачи {task_id}: {e}")
        return None


def get_all_employees(refresh: bool = False):
    """Получить список всех сотрудников"""
    try:
        cache_key = "all_employees"  # Ключ для кеша

        if refresh:
            print("Обновление данных...")
            cache.delete(cache_key)

        # Проверяем кеш, если не требуется обновление
        if not refresh and cache_key in cache:
            print("Загружаем данные из кеша...")
            return cache[cache_key]

        login, password = get_session_credentials()

        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return []

        api_client = create_master_api_client(login, password)
        employees = api_client.get_all_employees()

        # Преобразование словарей в кортежи
        converted_employees = []
        for employee in employees:
            converted_employee = (
                employee.get('emp_id', 0),  # ID сотрудника
                employee.get('full_name', ''),  # ФИО
                employee.get('post_name', ''),  # Должность
                employee.get('phone_number', ''),  # Номер телефона
                employee.get('email', ''),  # Электронная почта
                employee.get('health_status', ''),  # Статус здоровья
                employee.get('total_tasks_today', ''),  # Количество задач сегодня
                employee.get('total_tasks_executed_today', ''),  # Количество выполненных задач сегодня               
                employee.get('total_tasks_unmade_today', ''),  # Отчество                 
                employee.get('total_tasks_all_unmade', ''),
            )
            converted_employees.append(converted_employee)

        cache.set(cache_key, converted_employees, expire=3600)
        return converted_employees
    except Exception as e:
        print(f"Ошибка при получении списка сотрудников: {e}")
        return []


def get_employee_details(employee_id: int, refresh: bool = False):
    """Получить детальную информацию о сотруднике"""
    try:
        cache_key = f"employee_details_{employee_id}"

        if refresh:
            print("Обновление данных...")
            cache.delete(cache_key)

        # Проверяем кеш, если не требуется обновление
        if not refresh and cache_key in cache:
            print("Загружаем данные из кеша...")
            return cache[cache_key]

        login, password = get_session_credentials()

        if not login or not password:
            print("Ошибка: не удалось получить учетные данные сессии")
            return None

        api_client = create_master_api_client(login, password)
        employee = api_client.get_employee_details(employee_id)

        if not employee:
            print(f"Сотрудник с ID {employee_id} не найден")
            return None

        # Преобразование деталей сотрудника в кортеж или словарь
        converted_employee = {
            'employee': employee.get('employee', []),
            'tasks': employee.get('tasks', [])
        }

        cache.set(cache_key, converted_employee, expire=3600)
        return converted_employee
    except Exception as e:
        print(f"Ошибка при получении деталей сотрудника {employee_id}: {e}")
        return None


def select_acts_with_tasks_and_addresses(refresh: bool = False) -> List[Tuple]:
    """Получить акты с задачами и адресами"""
    try:
        cache_key = "all_acts"

        if refresh:
            print("Обновление данных актов...")
            cache.delete(cache_key)

        if not refresh and cache_key in cache:
            print("Загружаем акты из кеша...")
            return cache[cache_key]

        login, password = get_session_credentials()
        if not login or not password:
            print("Ошибка аутентификации")
            return []

        api_client = create_master_api_client(login, password)
        acts_data = api_client.get_acts_with_tasks_and_addresses()

        converted_acts = []
        for act in acts_data:
            converted_act = (
                act.get('act_id', 0),
                act.get('act_date', ''),
                act.get('act_reason', ''),
                act.get('task_id', 0),
                act.get('task_date', ''),
                act.get('task_date_end', ''),
                act.get('task_status', ''),
                act.get('task_fio_requestor', ''),
                act.get('task_fio_employer', ''),
                act.get('task_remark', ''),
                act.get('address_city', ''),
                act.get('address_district', ''),
                act.get('address_type', ''),
                act.get('address_dom', ''),
                act.get('address_apartment', ''),
                act.get('address_entrance', ''),
                act.get('street_name', ''),
                act.get('hamlet_name', '')
            )
            converted_acts.append(converted_act)

        cache.set(cache_key, converted_acts, expire=3600)
        return converted_acts

    except Exception as e:
        print(f"Ошибка при получении актов: {e}")
        return []


def get_dashboard_stats_data(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        employee_id: Optional[int] = None,
        refresh: bool = False
) -> Dict[str, Any]:
    """Получить статистику для дашборда"""
    try:
        cache_key = f"dashboard_stats_{start_date}_{end_date}_{employee_id}"

        if refresh:
            print("Обновление статистики дашборда...")
            cache.delete(cache_key)

        if not refresh and cache_key in cache:
            print("Загружаем статистику из кеша...")
            return cache[cache_key]

        login, password = get_session_credentials()
        if not login or not password:
            print("Ошибка аутентификации")
            return {}

        api_client = create_master_api_client(login, password)
        stats = api_client.get_dashboard_stats(
            start_date=start_date,
            end_date=end_date,
            employee_id=employee_id
        )

        # Преобразование данных при необходимости
        processed_stats = {
            'tasks_by_status': [
                {
                    "status": s['status'],
                    "count": s['count']
                } for s in stats.get('tasks_by_status', [])
                if s['count'] > 0
            ],
            'tasks_by_month': [
                {"month": m['month'], "count": m['count']}
                for m in stats.get('tasks_by_month', [])
            ],
            'employee_stats': [
                {
                    "employee_id": e['employee_id'],
                    "employee_name": e['employee_name'],
                    "completed_tasks": e['completed_tasks'],
                    "avg_completion_time": e['avg_completion_time']
                }
                for e in stats.get('employee_stats', [])
            ],
            'general_stats': stats.get('general_stats', {})
        }

        cache.set(cache_key, processed_stats, expire=600)  # Короткий срок кеширования
        return processed_stats

    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        return {}


def select_notifications(refresh: bool = False) -> List[Tuple]:
    """Получить уведомления пользователя"""
    try:
        cache_key = "user_notifications"

        if refresh:
            print("Обновление уведомлений...")
            cache.delete(cache_key)

        if not refresh and cache_key in cache:
            print("Загружаем уведомления из кеша...")
            return cache[cache_key]

        login, password = get_session_credentials()
        if not login or not password:
            print("Ошибка аутентификации")
            return []

        api_client = create_master_api_client(login, password)
        notifications = api_client.get_notifications()

        converted_notifications = []
        for notification in notifications:
            # Исправление: проверяем тип created_at
            created_at = notification.get('created_at', datetime.now())
            if isinstance(created_at, datetime):
                created_at_str = created_at.isoformat()
            else:
                # Если это строка, оставляем как есть
                created_at_str = created_at

            converted_notification = (
                notification.get('id', 0),
                notification.get('task_id', 0),
                notification.get('notification_type', ''),
                created_at_str,  # Исправленное поле
                notification.get('is_showed', False)
            )
            converted_notifications.append(converted_notification)

        cache.set(cache_key, converted_notifications, expire=300)
        return converted_notifications

    except Exception as e:
        print(f"Ошибка при получении уведомлений: {e}")
        return []
