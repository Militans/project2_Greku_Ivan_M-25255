from dataclasses import dataclass

from .constants import RESERVED_ID_COLUMN, SUPPORTED_TYPES


@dataclass(frozen=True)
class InvalidValueError(Exception):
    """
    Недопустимое значение, введенное пользователем

    :param value: недопустимое значение
    """
    value: str

class TableAlreadyExistsError(Exception):
    """
    Ошибка, возникающая при создании существующей таблицы
    """

class TableDoesNotExistError(Exception):
    """
    Ошибка, возникающая при обращении к несуществующей таблице
    """

def _parse_column_type(column_token: str) -> tuple:
    """
    Парсинг колонки и ее типа

    :param column_token: Токен колонки в формате 'name:type'
    :return: tuple (column_name, column_type)
    :raises: InvalidValueError: если формат или название недопустимы
    """
    if ":" not in column_token:
        raise InvalidValueError(column_token)

    name, col_type = column_token.split(":", 1)
    name = name.strip()
    col_type = col_type.strip()

    if not name or not col_type:
        raise InvalidValueError(column_token)

    if name == RESERVED_ID_COLUMN:
        raise InvalidValueError(name)

    if col_type not in SUPPORTED_TYPES:
        raise InvalidValueError(col_type)

    return name, col_type


def create_table(metadata: dict, table_name: str, columns: list) -> dict:
    """
    Создание новой таблицы и сохранение ее схемы в метаданных

    :param metadata: Метаданные бд
    :param table_name: Название таблицы
    :param columns: Колонки таблицы
    :return: Загрузка данных таблицы в метаданные бд
    :raises: TableAlreadyExistsError: Если таблица существует
    :raises: InvalidValueError: Если название таблицы или колонок недопустимы
    """
    table_name = table_name.strip()

    if not table_name:
        raise InvalidValueError(table_name)

    if table_name in metadata:
        raise TableAlreadyExistsError(table_name)

    if not columns:
        raise InvalidValueError("<columns>")

    parsed_columns = [{"name": RESERVED_ID_COLUMN, "type": "int"}]
    seen_columns = {RESERVED_ID_COLUMN}

    for column in columns:
        column_name, column_type = _parse_column_type(column)

        if column_name in seen_columns:
            raise InvalidValueError(column_name)

        seen_columns.add(column_name)
        parsed_columns.append({"name": column_name, "type": column_type})
    new_metadata = dict(metadata)
    new_metadata[table_name] = {"columns": parsed_columns}

    return new_metadata







def drop_table(metadata: dict, table_name: str) -> dict:
    """
    Удаление таблицы из метаданных

    :param metadata: Метаданные бд
    :param table_name: Название таблицы
    :return: dict: Обновленные метаданные бд
    :raises: TableDoesNotExistError: Если таблицы не существует
    """

    table_name = table_name.strip()
    if table_name not in metadata:
        raise TableDoesNotExistError(table_name)

    new_metadata = dict(metadata)
    del new_metadata[table_name]
    return new_metadata


def list_tables(metadata: dict) -> list:
    """
    Отображение списка существующих таблиц

    :param metadata: Метаданные бд
    :return: list: Список имен таблиц
    """
    return sorted(metadata.keys())





