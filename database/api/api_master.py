from typing import Dict, List, Any, Optional

from src.database.api.api_client import WaterUtilityAPIClient

from dotenv import load_dotenv
import os


load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")

def create_master_api_client(login: str, password: str) -> WaterUtilityAPIClient:
    return WaterUtilityAPIClient(API_BASE_URL, login, password)


# Функции-обертки для удобного использования
def get_all_tasks(login: str, password: str) -> Optional[List[Dict[str, Any]]]:
    """Получить все задачи"""
    api_client = create_master_api_client(login, password)
    try:
        return api_client.get_all_tasks()
    except Exception as e:
        print(f"Ошибка при получении всех задач: {e}")
        return None


def get_unassigned_tasks(login: str, password: str) -> Optional[List[Dict[str, Any]]]:
    """Получить незакрепленные задачи"""
    api_client = create_master_api_client(login, password)
    try:
        return api_client.get_unassigned_tasks()
    except Exception as e:
        print(f"Ошибка при получении незакрепленных задач: {e}")
        return None


def upsert_task(login: str, password: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Обновить данные задачи или создать новую"""
    api_client = create_master_api_client(login, password)
    try:
        return api_client.upsert_task(task_data)
    except Exception as e:
        print(f"Ошибка при обновлении/создании задачи: {e}")
        return None


def insert_tasks_bulk(login: str, password: str, tasks_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Массовая вставка задач"""
    api_client = create_master_api_client(login, password)
    try:
        return api_client.insert_tasks_bulk(tasks_data)
    except Exception as e:
        print(f"Ошибка при массовой вставке задач: {e}")
        return None


def delete_tasks(login: str, password: str, task_ids: List[int]) -> Optional[Dict[str, Any]]:
    """Удалить задачи"""
    api_client = create_master_api_client(login, password)
    try:
        return api_client.delete_tasks(task_ids)
    except Exception as e:
        print(f"Ошибка при удалении задач: {e}")
        return None


def get_task_details(login: str, password: str, task_id: int) -> Optional[Dict[str, Any]]:
    """Получить детали задачи"""
    api_client = create_master_api_client(login, password)
    try:
        return api_client.get_task_details(task_id)
    except Exception as e:
        print(f"Ошибка при получении деталей задачи: {e}")
        return None


# Аналогичные функции для работы с сотрудниками
def get_all_employees(login: str, password: str, refresh: bool = False) -> Optional[List[Dict[str, Any]]]:
    """Получить список всех сотрудников"""
    api_client = create_master_api_client(login, password)
    try:
        return api_client.get_all_employees(refresh)
    except Exception as e:
        print(f"Ошибка при получении списка сотрудников: {e}")
        return None


def upsert_employee(login: str, password: str, employee_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Обновить данные сотрудника или создать нового"""
    api_client = create_master_api_client(login, password)
    try:
        return api_client.upsert_employee(employee_data)
    except Exception as e:
        print(f"Ошибка при обновлении/создании сотрудника: {e}")
        return None


def delete_employee(login: str, password: str, employee_id: int) -> Optional[Dict[str, Any]]:
    """Удалить сотрудника"""
    api_client = create_master_api_client(login, password)
    try:
        return api_client.delete_employee(employee_id)
    except Exception as e:
        print(f"Ошибка при удалении сотрудника: {e}")
        return None


def get_employee_details(login: str, password: str, employee_id: int) -> Optional[Dict[str, Any]]:
    """Получить детали сотрудника"""
    api_client = create_master_api_client(login, password)
    try:
        return api_client.get_employee_details(employee_id)
    except Exception as e:
        print(f"Ошибка при получении деталей сотрудника: {e}")
        return None


def set_employee_to_task(login: str, password: str, update_tasks_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Назначить сотрудника на задачу"""
    api_client = create_master_api_client(login, password)
    try:
        return api_client.set_employee_to_task(update_tasks_data)
    except Exception as e:
        print(f"Ошибка при назначении сотрудника на задачу: {e}")
        return None
