import json
from json import JSONDecodeError
import os

from .constants import TABLE_FILE_TEMPLATE, DATA_DIR

def _ensure_data_dir() -> None:
    """Создает директорию data/, если ее нет."""
    os.makedirs(DATA_DIR, exist_ok=True)


def load_metadata(filepath: str) -> dict:
    """
    Загрузка файла метаданных БД
    Если файлов нет - возврат пустого словаря

    :param filepath: Путь к метаданным
    :return: Словарь с метаданными
    """
    _ensure_data_dir()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except JSONDecodeError:
        return {}


def save_metadata(filepath: str, data: dict) -> None:
    """
    Сохранение метаданных БД в JSON файл

    :param filepath: Путь к бд
    :param data: Словарь с сохраняемыми метаданными
    :return: None
    """
    _ensure_data_dir()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_table_data(table_name: str) -> list:
    """
    Загрузка данных таблицы

    :param table_name: Имя таблицы
    :return: Список записей
    """
    _ensure_data_dir()
    filepath = TABLE_FILE_TEMPLATE.format(table=table_name)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except FileNotFoundError:
        return []
    except JSONDecodeError:
        return []

def save_table_data(table_name: str, data: list) -> None:
    """
    Сохранение данных таблицы

    :param table_name: Имя таблицы
    :param data: Список записей
    :return: None
    """
    _ensure_data_dir()
    filepath = TABLE_FILE_TEMPLATE.format(table=table_name)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)