import json
from pathlib import Path
import os
from datetime import datetime


class TableStateManager:
    @staticmethod
    def save_state(page_type, state):
        """Сохраняет состояние таблицы в файл"""
        dir_path = Path("data") / "sessions"
        os.makedirs(dir_path, exist_ok=True)
        file_path = dir_path / f"settings_{page_type}.json"

        if state is None:  # Удаляем файл если настройки дефолтные
            try:
                if file_path.exists():
                    file_path.unlink()
                return True
            except Exception as e:
                print(f"Ошибка удаления настроек: {e}")
                return False

        try:
            state['last_updated'] = datetime.now().isoformat()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения состояния: {e}")
            return False

    @staticmethod
    def get_settings_path(page_type):
        # Создаем абсолютный путь для надежности
        base_dir = Path(__file__).parent.parent.parent / "data" / "sessions"
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / f"settings_{page_type}.json"

    @staticmethod
    def load_state(page_type):
        """Загружает состояние таблицы из файла"""
        file_path = Path("data") / "sessions" / f"settings_{page_type}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки состояния: {e}")
            return None