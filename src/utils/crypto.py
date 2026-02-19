"""Утилиты для шифрования данных"""
import base64
import json
import os


class Crypto:
    def __init__(self):
        self._key_file = "data/crypto/crypto.key"
        self._key = self._init_key()

    def _generate_key(self):
        """Генерация ключа шифрования"""
        key = os.urandom(32)
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(self._key_file), exist_ok=True)
        with open(self._key_file, 'wb') as f:
            f.write(key)
        return key

    def _load_key(self):
        """Загрузка существующего ключа"""
        try:
            with open(self._key_file, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Ошибка при загрузке ключа: {e}")
            return None

    def _init_key(self):
        """Инициализация ключа"""
        key = self._load_key()
        if not key:
            key = self._generate_key()
        return key

    def _xor_bytes(self, data: bytes, key: bytes) -> bytes:
        """XOR шифрование"""
        key_len = len(key)
        return bytes(b ^ key[i % key_len] for i, b in enumerate(data))

    def encrypt(self, data: str) -> str:
        """Шифрование строки"""
        data_bytes = data.encode()
        encrypted = self._xor_bytes(data_bytes, self._key)
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, encrypted_str: str) -> str:
        """Расшифровка строки"""
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_str.encode())
            decrypted = self._xor_bytes(encrypted, self._key)
            return decrypted.decode()
        except Exception as e:
            print(f"Ошибка расшифровки: {e}")
            return ""

    def encrypt_dict(self, data: dict) -> str:
        """Шифрование словаря"""
        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, encrypted_str: str) -> dict:
        """Расшифровка словаря"""
        try:
            decrypted_str = self.decrypt(encrypted_str)
            return json.loads(decrypted_str)
        except Exception as e:
            print(f"Ошибка расшифровки: {e}")
            return {}


# Глобальный экземпляр для шифрования
crypto = Crypto()
