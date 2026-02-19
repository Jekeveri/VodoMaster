import json
import os
import time
from typing import Optional, Dict, Any

from src.config.config import APP_CONFIG
from src.utils.crypto import crypto


class SessionManager:
    def __init__(self):
        self.session_file = "data/sessions/session.json"
        self.session_ttl = APP_CONFIG['session_ttl']
        self._current_user_id = None

    def _load_sessions(self) -> Dict:
        """Загрузить сессии из файла"""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    encrypted_sessions = json.load(f)
                    sessions = {}
                    for user_id, encrypted_data in encrypted_sessions.items():
                        try:
                            decrypted_data = crypto.decrypt(encrypted_data)
                            sessions[user_id] = json.loads(decrypted_data)
                        except Exception as e:
                            print(f"Ошибка при расшифровке сессии {user_id}: {e}")
                            continue
                    return sessions
            except Exception as e:
                print(f"Ошибка при загрузке сессий: {e}")
        return {}

    def _save_sessions(self, sessions: Dict) -> None:
        """Сохранить сессии в файл"""
        try:
            # Создаем директорию, если она не существует
            os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
            
            encrypted_sessions = {}
            for user_id, session_data in sessions.items():
                try:
                    encrypted_sessions[user_id] = crypto.encrypt(json.dumps(session_data))
                except Exception as e:
                    print(f"Ошибка при шифровании сессии {user_id}: {e}")
                    continue
                
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении сессий: {e}")

    def create_session(self, user_id: int, user_data: Dict[str, Any]) -> None:
        """Создать новую сессию"""
        sessions = self._load_sessions()
        self._current_user_id = user_id

        sessions[str(user_id)] = {
            'data': {
                'id': user_id,
                'login': user_data.get('login'),
                'password': user_data.get('password'),
                'privileges': user_data.get('privileges'),
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name')
            },
            'expires_at': time.time() + self.session_ttl
        }
        self._save_sessions(sessions)

    def get_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные сессии"""
        if user_id is None:
            return None
            
        try:
            sessions = self._load_sessions()
            session = sessions.get(str(user_id))
            
            if not session or not isinstance(session, dict):
                return None

            # Проверяем срок действия сессии
            expires_at = session.get('expires_at')
            if not expires_at or time.time() > expires_at:
                self.delete_session(user_id)
                return None

            return session.get('data')
        except Exception as e:
            print(f"Ошибка при получении сессии {user_id}: {e}")
            return None

    def delete_session(self, user_id: int) -> None:
        """Удалить сессию"""
        sessions = self._load_sessions()
        if str(user_id) in sessions:
            del sessions[str(user_id)]
            self._save_sessions(sessions)

    def update_session(self, user_id: int, update_data: Dict[str, Any]) -> None:
        """Обновить данные сессии"""
        sessions = self._load_sessions()
        if str(user_id) in sessions:
            sessions[str(user_id)]['data'].update(update_data)
            sessions[str(user_id)]['expires_at'] = time.time() + self.session_ttl
            self._save_sessions(sessions)
    
    def get_current_user_id(self) -> Optional[int]:
        """Получить ID последнего активного пользователя"""
        sessions = self._load_sessions()
        
        # Находим последнюю активную сессию
        active_sessions = [
            int(user_id) for user_id, session in sessions.items() 
            if session.get('expires_at', 0) > time.time()
        ]
        
        # Возвращаем последний активный ID или None
        return max(active_sessions) if active_sessions else None


# Глобальный экземпляр менеджера сессий
session_manager = SessionManager()
