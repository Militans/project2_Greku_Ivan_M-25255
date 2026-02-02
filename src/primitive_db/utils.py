import json
from json import JSONDecodeError


def load_metadata(filepath: str) -> dict:
    """
    Загрузка файла метаданных БД
    Если файлов нет - возврат пустого словаря

    :param filepath: Путь к метаданным
    :return: Словарь с метаданными
    """
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
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
