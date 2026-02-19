import os
import sys
import ctypes
import logging
from pathlib import Path
from datetime import datetime


def is_32bit():
    return sys.maxsize <= 2 ** 32


def setup_logging():
    """Настройка надежного логирования с проверкой прав доступа"""
    try:
        appdata = os.getenv('APPDATA')
        if not appdata:
            raise EnvironmentError("Не найдена переменная окружения APPDATA")

        log_dir = Path(appdata) / "VodoMaster" / "logs"

        # Попытка создания директории с обработкой ошибок
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Альтернативный путь, если нет прав в APPDATA
            log_dir = Path.home() / "VodoMaster_logs"
            log_dir.mkdir(parents=True, exist_ok=True)

        # Уникальное имя файла с timestamp
        log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        # Проверка возможности записи
        try:
            with open(log_file, 'a'):
                pass
        except IOError as e:
            raise RuntimeError(f"Невозможно записать в файл логов: {e}")

        # Настройка логгера
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # Очистка старых обработчиков
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Форматтер
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Файловый обработчик
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        logging.info(f"Инициализация логгирования. Логи будут записываться в: {log_file}")
        return True

    except Exception as e:
        # Аварийное логирование в stderr, если обычное не сработало
        sys.stderr.write(f"ОШИБКА НАСТРОЙКИ ЛОГГИРОВАНИЯ: {str(e)}\n")
        return False


def check_dependencies():
    """Проверка зависимостей с подробным логированием"""
    try:
        required_dlls = ['vcruntime140.dll', 'msvcp140.dll']
        missing = []
        search_paths = []

        # Определяем пути для поиска DLL
        if is_32bit():
            search_paths.append(os.path.join(os.environ['SYSTEMROOT'], 'System32'))
        else:
            search_paths.append(os.path.join(os.environ['SYSTEMROOT'], 'System32'))
            search_paths.append(os.path.join(os.environ['SYSTEMROOT'], 'SysWOW64'))

        # Добавляем директорию с исполняемым файлом
        search_paths.append(os.path.dirname(sys.executable))

        logging.info(f"Поиск DLL в: {', '.join(search_paths)}")

        for dll in required_dlls:
            found = False
            for path in search_paths:
                dll_path = os.path.join(path, dll)
                if os.path.exists(dll_path):
                    try:
                        ctypes.CDLL(dll_path)
                        logging.info(f"Найдена и загружена: {dll_path}")
                        found = True
                        break
                    except OSError as e:
                        logging.warning(f"Ошибка загрузки {dll_path}: {e}")

            if not found:
                missing.append(dll)
                logging.error(f"Не найдена: {dll}")

        if missing:
            logging.error(f"Отсутствуют DLL: {', '.join(missing)}")
            return False
        return True

    except Exception as e:
        logging.exception("Ошибка при проверке зависимостей")
        return False


def main():
    if not setup_logging():
        # Если логирование не настроилось, попробуем хотя бы записать в файл рядом с exe
        try:
            with open("vodo_error.log", "a") as f:
                f.write(f"{datetime.now()} - Не удалось настроить логирование\n")
        except:
            pass

    try:
        logging.info(f"Запуск приложения на {'32-битной' if is_32bit() else '64-битной'} системе")
        logging.info(f"Python: {sys.version}")
        logging.info(f"Рабочая директория: {os.getcwd()}")
        logging.info(f"Путь к исполняемому файлу: {sys.executable}")

        if not check_dependencies():
            msg = "Не найдены необходимые системные библиотеки. Убедитесь, что установлен Visual C++ Redistributable."
            logging.error(msg)
            ctypes.windll.user32.MessageBoxW(
                0,
                msg,
                "Ошибка запуска",
                0x10
            )
            return

        logging.info("Все зависимости найдены, запуск основного приложения...")

        import flet
        from main import main as app_main

        if is_32bit():
            os.environ["FLET_DISABLE_DIRECTWRITE"] = "1"
            logging.info("Применены настройки для 32-битной системы")

        flet.app(
            target=app_main,
            view=flet.AppView.FLET_APP,
            assets_dir=str(Path(__file__).parent / "assets")
                           )

    except Exception as e:
        logging.exception("Критическая ошибка в основном потоке")
        error_msg = f"Критическая ошибка: {str(e)}\nПодробности в лог-файле."
        try:
            ctypes.windll.user32.MessageBoxW(
                0,
                error_msg,
                "Сбой приложения",
                0x10
            )
        except:
            pass


if __name__ == "__main__":
    main()