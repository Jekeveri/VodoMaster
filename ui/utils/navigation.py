import uuid
import os
import json
from pathlib import Path


def make_json_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(i) for i in obj]
    elif hasattr(obj, 'isoformat'):  # Для datetime, Timestamp и пр.
        return obj.isoformat()
    else:
        return obj


class NavigationManager:
    def __init__(self):
        self.additional_nav_buttons = []
        self.on_update_callback = None
        self.on_navigate_callback = None
        self.current_additional_data = None
        # self.current_page = "home"
        self.current_page = "home"
        self.page_history = ["home"]  # История страниц
        self.page_states = {}
        self.main_nav_items = []  # Основные страницы
        self.closed_pages = []
        self._closed_pages_file = Path("data/sessions/last_closed.json")
        self.load_closed_pages()

    def load_closed_pages(self):
        try:
            self._closed_pages_file.parent.mkdir(parents=True, exist_ok=True)
            if self._closed_pages_file.exists():
                with open(self._closed_pages_file, "r", encoding="utf-8") as f:
                    self.closed_pages = json.load(f)
        except Exception as e:
            print(f"Error loading closed pages: {e}")

    def save_closed_pages(self):
        try:
            serializable_pages = make_json_serializable(self.closed_pages)
            with open(self._closed_pages_file, "w", encoding="utf-8") as f:
                json.dump(serializable_pages, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving closed pages: {e}")

    def add_closed_page(self, page_info):
        # Check if page already exists
        exists = any(
            p["id"] == page_info["id"] and
            p.get("additional_data") == page_info.get("additional_data")
            for p in self.closed_pages
        )

        if not exists:
            self.closed_pages.insert(0, page_info)

            # Keep only last 4 pages
            if len(self.closed_pages) > 4:
                self.closed_pages = self.closed_pages[:4]

            self.save_closed_pages()

    def add_main_nav_item(self, item):
        self.main_nav_items.append(item)

    def set_update_callback(self, callback):
        self.on_update_callback = callback

    def set_navigate_callback(self, callback):
        self.on_navigate_callback = callback

    def add_nav_button(self, button_info):
        if 'id' not in button_info or button_info['id'] is None:
            button_info['id'] = str(uuid.uuid4())

        if 'icon' not in button_info:
            button_info['icon'] = 'radio_button_unchecked'

        if 'label' not in button_info:
            button_info['label'] = 'Unnamed Page'

        self.additional_nav_buttons.append(button_info)
        self._update()

    def add_nav_button_and_navigate(self, button_data):
        self.add_nav_button(button_data)
        self.navigate(button_data)

    def remove_nav_button(self, button_id):
        was_current = any(
            btn.get('id') == button_id and btn.get('additional_data') == self.current_additional_data
            for btn in self.additional_nav_buttons
        )

        self.additional_nav_buttons = [
            btn for btn in self.additional_nav_buttons
            if not (btn.get('id') == button_id and
                    btn.get('additional_data') == self.current_additional_data)
        ]

        if was_current:
            fallback_page = self.page_history[-2] if len(self.page_history) >= 2 else "home"
            self.navigate({"id": fallback_page})

        if self.on_update_callback:
            self.on_update_callback()

    def get_additional_buttons(self):
        return self.additional_nav_buttons

    def navigate(self, button_data):
        if self.current_page != button_data['id']:
            self.page_history.append(self.current_page)

        # self.page_history.append(button_data["id"])
        if len(self.page_history) > 10:
            self.page_history = self.page_history[-10:]

        self.current_page = button_data['id']
        self.current_additional_data = button_data.get("additional_data")

        if not any(
                btn.get("id") == button_data["id"] and btn.get("additional_data") == button_data.get("additional_data")
                for btn in self.additional_nav_buttons):
            self.add_nav_button(button_data)

        if self.on_navigate_callback:
            self.on_navigate_callback(button_data)

    def go_back(self):
        if len(self.page_history) > 1:
            self.page_history.pop()

            previous_page = self.page_history[-1]

            if self.on_navigate_callback:
                self.on_navigate_callback({
                    'id': previous_page,
                    'data': 'back_navigation'
                })

            return True

        return False

    def _update(self):
        if self.on_update_callback:
            self.on_update_callback()


nav_manager = NavigationManager()
