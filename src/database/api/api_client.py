from typing import Optional, List, Dict, Any
from datetime import date
import requests


class WaterUtilityAPIClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = requests.Session()

    def _make_request(self, method: str, endpoint: str,
                      data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        print(f"Making request to {url}")
        print(f"Data: {data}")

        params = params or {}
        params.update({"username": self.username, "password": self.password})

        try:
            if method == "GET":
                response = self.session.get(url, params=params)
            elif method == "POST":
                response = self.session.post(url, json=data, params=params)
            elif method == "DELETE":
                response = self.session.delete(url, params=params, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            raise

    def login(self) -> Dict[str, Any]:
        return self._make_request("POST", "login", data={"username": self.username, "password": self.password})

    # Методы для работы с задачами
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Получить все задачи"""
        return self._make_request("GET", "tasks/all")

    def export_completed_tasks(self, start_date: Optional[date] = None,
                               end_date: Optional[date] = None):
        params = {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }

        return self._make_request("GET", "tasks/export_completed", params=params)

    def get_all_addresses(self) -> List[Dict[str, Any]]:
        """Получить все задачи"""
        return self._make_request("GET", "addresses/full")

    def get_address_details(self, address_id: int) -> Dict[str, Any]:
        """Получить детали конкретной задачи"""
        return self._make_request("GET", f"addresses/{address_id}/details")

    def get_unassigned_tasks(self) -> List[Dict[str, Any]]:
        """Получить незакрепленные задачи"""
        return self._make_request("GET", "tasks/unassigned")

    def upsert_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить или создать задачу"""
        return self._make_request("POST", "tasks/changes_tasks", data=task_data)

    def insert_tasks_bulk(self, tasks_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Вставить несколько задач"""
        return self._make_request("POST", "tasks/insert_from_json", data=tasks_data)

    def delete_tasks(self, task_ids: List[int]):
        """Удалить задачи"""
        return self._make_request("DELETE", "tasks/delete", data=task_ids)

    def get_task_details(self, task_id: int) -> Dict[str, Any]:
        """Получить детали конкретной задачи"""
        return self._make_request("GET", f"tasks/{task_id}/details")

    # Методы для работы с сотрудниками
    def get_all_employees(self) -> List[Dict[str, Any]]:
        """Получить список всех сотрудников"""
        return self._make_request("GET", "employees")

    def get_acts_with_tasks_and_addresses(self) -> List[Dict[str, Any]]:
        """Получить акты с задачами и адресами"""
        return self._make_request("GET", "acts")

    def get_dashboard_stats(
            self,
            start_date: Optional[date] = None,
            end_date: Optional[date] = None,
            employee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Получить статистику для дашборда"""
        params = {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "employee_id": employee_id
        }
        return self._make_request("GET", "dashboard/stats", params=params)

    def get_notifications(self) -> List[Dict[str, Any]]:
        """Получить уведомления пользователя"""
        return self._make_request("GET", "notifications")

    def mark_notification_as_shown(self, notification_id: int) -> Dict[str, Any]:
        """Пометить уведомление как прочитанное"""
        return self._make_request("POST", f"notifications/{notification_id}/mark-as-shown")

    def unassign_tasks(self, task_ids: List[int], fio_emp: List[int]) -> Dict[str, Any]:
        """Отменить назначение задач"""
        return self._make_request("POST", "tasks/unassign", data={"task_ids": task_ids, "fio_emp": fio_emp})

    def upsert_employee(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить или создать сотрудника"""
        print(employee_data)
        return self._make_request("POST", "employees/changes_employees", data=employee_data)

    def delete_employee(self, employee_ids: List[int]):
        """Удалить сотрудника"""
        print(employee_ids)
        return self._make_request("DELETE", "employees/delete", data=employee_ids)

    def get_employee_details(self, employee_id: int) -> Dict[str, Any]:
        """Получить детали конкретного сотрудника"""
        return self._make_request("GET", f"employees/{employee_id}/details")

    def set_employee_to_task(self, update_tasks_data: Dict[str, Any]) -> Dict[str, Any]:
        """Назначить сотрудника на задачу"""
        return self._make_request("POST", f"employees/update_task_employer", data=update_tasks_data)
