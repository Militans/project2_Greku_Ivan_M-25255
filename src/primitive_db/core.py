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


class TableSchemaError(Exception):
    """
    Ошибка схемы таблицы
    """


def _get_schema(metadata: dict, table_name: str) -> list:
    """
    Получение схемы таблицы из метаданных

    :param metadata: Метаданные бд
    :param table_name: Название таблицы
    :return: list: Схема таблицы (список колонок)
    :raises: TableDoesNotExistError: Если таблицы не существует
    :raises: TableSchemaError: Если схема таблицы повреждена
    """
    if table_name not in metadata:
        raise TableDoesNotExistError(table_name)

    cols = metadata[table_name].get("columns")
    if not isinstance(cols, list):
        raise TableSchemaError(table_name)

    return cols


def _validate_value(col_type: str, value: object) -> object:
    """
    Валидация значения по типу колонки

    :param col_type: Тип колонки (int/str/bool)
    :param value: Значение для проверки
    :return: object: Валидное значение
    :raises: InvalidValueError: Если значение не соответствует типу
    """
    if col_type == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            raise InvalidValueError(str(value))
        return value

    if col_type == "bool":
        if not isinstance(value, bool):
            raise InvalidValueError(str(value))
        return value

    if col_type == "str":
        if not isinstance(value, str):
            raise InvalidValueError(str(value))
        return value

    raise InvalidValueError(col_type)


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


def insert(metadata: dict, table_name: str, table_data: list, values: list) -> tuple:
    """
    Добавление записи в таблицу

    :param metadata: Метаданные бд
    :param table_name: Название таблицы
    :param table_data: Данные таблицы
    :param values: Значения (без ID)
    :return: tuple: (Обновленные данные, новый ID)
    :raises: TableDoesNotExistError: Если таблицы не существует
    :raises: InvalidValueError: Если количество значений или типы некорректны
    """
    schema = _get_schema(metadata, table_name)

    expected = len(schema) - 1
    if len(values) != expected:
        raise InvalidValueError(f"values_count={len(values)}")

    existing_ids = [
        row.get("ID")
        for row in table_data
        if isinstance(row.get("ID"), int)
    ]
    new_id = (max(existing_ids) + 1) if existing_ids else 1

    row = {"ID": new_id}
    for col_def, value in zip(schema[1:], values, strict=True):
        col_name = col_def["name"]
        col_type = col_def["type"]
        row[col_name] = _validate_value(col_type, value)

    table_data.append(row)
    return table_data, new_id


def select(table_data: list, where_clause: dict | None = None) -> list:
    """
    Получение записей из таблицы

    :param table_data: Данные таблицы
    :param where_clause: Условие where (опционально)
    :return: list: Список записей
    """
    if not where_clause:
        return list(table_data)

    (key, value), = where_clause.items()
    return [row for row in table_data if row.get(key) == value]


def update(
    metadata: dict,
    table_name: str,
    table_data: list,
    set_clause: dict,
    where_clause: dict,
) -> tuple:
    """
    Обновление записей по условию

    :param metadata: Метаданные бд
    :param table_name: Название таблицы
    :param table_data: Данные таблицы
    :param set_clause: Данные для обновления
    :param where_clause: Условие where
    :return: tuple: (Обновленные данные, количество обновленных записей)
    :raises: TableDoesNotExistError: Если таблицы не существует
    :raises: InvalidValueError: Если колонка или значение некорректны
    """
    schema = _get_schema(metadata, table_name)
    types_map = {c["name"]: c["type"] for c in schema}

    if "ID" in set_clause:
        raise InvalidValueError("ID")

    (w_key, w_val), = where_clause.items()

    updated = 0
    for row in table_data:
        if row.get(w_key) == w_val:
            for key, val in set_clause.items():
                if key not in types_map:
                    raise InvalidValueError(key)
                row[key] = _validate_value(types_map[key], val)
            updated += 1

    return table_data, updated


def delete(table_data: list, where_clause: dict) -> tuple:
    """
    Удаление записей по условию

    :param table_data: Данные таблицы
    :param where_clause: Условие where
    :return: tuple: (Обновленные данные, количество удаленных записей)
    """
    (key, value), = where_clause.items()

    before = len(table_data)
    new_data = [row for row in table_data if row.get(key) != value]
    deleted = before - len(new_data)

    return new_data, deleted


def info(metadata: dict, table_name: str, table_data: list) -> dict:
    """
    Получение информации о таблице

    :param metadata: Метаданные бд
    :param table_name: Название таблицы
    :param table_data: Данные таблицы
    :return: dict: Информация о таблице (имя, столбцы, количество записей)
    :raises: TableDoesNotExistError: Если таблицы не существует
    """
    schema = _get_schema(metadata, table_name)
    cols_str = ", ".join([f'{c["name"]}:{c["type"]}' for c in schema])
    return {"table": table_name, "columns": cols_str, "count": len(table_data)}
