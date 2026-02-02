import os
import re
import shlex

import prompt
from prettytable import PrettyTable

from .constants import METADATA_PATH, TABLE_FILE_TEMPLATE
from .core import (
    create_table,
    delete,
    drop_table,
    info,
    insert,
    list_tables,
    select,
    update,
)
from .decorators import create_cacher
from .parser import parse_set, parse_values, parse_where
from .utils import load_metadata, load_table_data, save_metadata, save_table_data

_CACHE_SELECT = create_cacher()


def print_help() -> None:
    """
    Вывод справки по доступным командам.

    :return: None
    """
    print("\n***База данных***")
    print("Функции:")
    print("<command> create_table <таблица> <столбец:тип> ... - создать таблицу")
    print("<command> list_tables - показать список таблиц")
    print("<command> drop_table <таблица> - удалить таблицу")
    print("<command> insert into <таблица> values (...) - добавить запись")
    print("<command> select from <таблица> - вывести все записи")
    print("<command> select from <таблица> where a = b - фильтрация")
    print("<command> update <таблица> set a = b where c = d - обновить")
    print("<command> delete from <таблица> where a = b - удалить")
    print("<command> info <таблица> - информация о таблице")
    print("<command> exit - выход")
    print("<command> help - справка\n")


def _render_table(schema: list, rows: list) -> None:
    """
    Печать выборки в формате PrettyTable.

    :param schema: схема таблицы (список колонок)
    :param rows: строки (список словарей)
    :return: None
    """
    headers = [c["name"] for c in schema]
    pt = PrettyTable()
    pt.field_names = headers

    for row in rows:
        pt.add_row([row.get(h) for h in headers])

    print(pt)


def run() -> None:
    """
    Главный цикл CLI базы данных.

    :return: None
    """
    print_help()

    while True:
        user_input = prompt.string("Введите команду: ").strip()
        if not user_input:
            continue

        raw = user_input.strip()

        m = re.fullmatch(
            r"insert\s+into\s+(\w+)\s+values\s*\((.*)\)\s*",
            raw,
            flags=re.IGNORECASE,
        )
        if m:
            table = m.group(1)
            values_inner = m.group(2)

            metadata = load_metadata(METADATA_PATH)
            table_data = load_table_data(table)
            values = parse_values(values_inner)

            result = insert(metadata, table, table_data, values)
            if result is None:
                continue

            table_data, new_id = result
            save_table_data(table, table_data)
            print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table}".')
            continue

        m = re.fullmatch(
            r"select\s+from\s+(\w+)(?:\s+where\s+(.+))?\s*",
            raw,
            flags=re.IGNORECASE,
        )
        if m:
            table = m.group(1)
            where_raw = m.group(2)

            metadata = load_metadata(METADATA_PATH)
            if table not in metadata:
                print(f'Ошибка: Таблица "{table}" не существует.')
                continue

            table_data = load_table_data(table)
            where_clause = parse_where(where_raw) if where_raw else None

            filepath = TABLE_FILE_TEMPLATE.format(table=table)
            mtime = os.path.getmtime(filepath) if os.path.exists(filepath) else 0.0
            key = (table, where_raw or "", mtime)

            rows = _CACHE_SELECT(key, lambda: select(table_data, where_clause))
            if rows is None:
                continue

            schema = metadata[table]["columns"]
            _render_table(schema, rows)
            continue

        m = re.fullmatch(
            r"update\s+(\w+)\s+set\s+(.+?)\s+where\s+(.+)\s*",
            raw,
            flags=re.IGNORECASE,
        )
        if m:
            table = m.group(1)
            set_raw = m.group(2)
            where_raw = m.group(3)

            metadata = load_metadata(METADATA_PATH)
            if table not in metadata:
                print(f'Ошибка: Таблица "{table}" не существует.')
                continue

            table_data = load_table_data(table)
            set_clause = parse_set(set_raw)
            where_clause = parse_where(where_raw)

            result = update(metadata, table, table_data, set_clause, where_clause)
            if result is None:
                continue

            table_data, updated = result
            save_table_data(table, table_data)

            if updated == 0:
                print("Ничего не обновлено (нет подходящих записей).")
            else:
                msg = (
                    f'Записи в таблице "{table}" успешно обновлены. '
                    f"Изменено: {updated}."
                )
                print(msg)
            continue

        m = re.fullmatch(
            r"delete\s+from\s+(\w+)\s+where\s+(.+)\s*",
            raw,
            flags=re.IGNORECASE,
        )
        if m:
            table = m.group(1)
            where_raw = m.group(2)

            metadata = load_metadata(METADATA_PATH)
            if table not in metadata:
                print(f'Ошибка: Таблица "{table}" не существует.')
                continue

            table_data = load_table_data(table)
            where_clause = parse_where(where_raw)

            result = delete(table_data, where_clause)
            if result is None:
                continue

            table_data, deleted = result
            save_table_data(table, table_data)
            print(f"Удалено записей: {deleted}.")
            continue

        m = re.fullmatch(r"info\s+(\w+)\s*", raw, flags=re.IGNORECASE)
        if m:
            table = m.group(1)

            metadata = load_metadata(METADATA_PATH)
            if table not in metadata:
                print(f'Ошибка: Таблица "{table}" не существует.')
                continue

            table_data = load_table_data(table)
            res = info(metadata, table, table_data)
            if res is None:
                continue

            print(f'Таблица: {res["table"]}')
            print(f'Столбцы: {res["columns"]}')
            print(f'Количество записей: {res["count"]}')
            continue

        try:
            args = shlex.split(user_input)
        except ValueError:
            print("Некорректное значение <input>. Попробуйте снова.")
            continue

        if not args:
            continue

        command = args[0]
        cmd_args = args[1:]
        metadata = load_metadata(METADATA_PATH)

        match command:
            case "help":
                print_help()

            case "exit":
                return

            case "list_tables":
                tables = list_tables(metadata)
                if tables is None:
                    continue
                if not tables:
                    print("- (нет таблиц)")
                else:
                    for t in tables:
                        print(f"- {t}")

            case "create_table":
                if len(cmd_args) < 2:
                    print("Некорректное значение: <args>. Попробуйте снова.")
                    continue

                table_name = cmd_args[0]
                columns = cmd_args[1:]

                new_metadata = create_table(metadata, table_name, columns)
                if new_metadata is None:
                    continue

                save_metadata(METADATA_PATH, new_metadata)
                cols = new_metadata[table_name]["columns"]
                cols_text = ", ".join([f'{c["name"]}:{c["type"]}' for c in cols])

                print(
                    f'Таблица "{table_name}" успешно создана со столбцами: '
                    f"{cols_text}"
                )

            case "drop_table":
                if len(cmd_args) != 1:
                    print("Некорректное значение: <args>. Попробуйте снова.")
                    continue

                table_name = cmd_args[0]

                new_metadata = drop_table(metadata, table_name)
                if new_metadata is None:
                    continue

                save_metadata(METADATA_PATH, new_metadata)

                filepath = TABLE_FILE_TEMPLATE.format(table=table_name)
                if os.path.exists(filepath):
                    os.remove(filepath)

                print(f'Таблица "{table_name}" успешно удалена.')

            case _:
                print(f"Функции {command} нет. Попробуйте снова.")
