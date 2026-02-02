import re
import shlex

import prompt
from prettytable import PrettyTable

from .constants import METADATA_PATH
from .core import (
    InvalidValueError,
    TableAlreadyExistsError,
    TableDoesNotExistError,
    create_table,
    delete,
    drop_table,
    info,
    insert,
    list_tables,
    select,
    update,
)
from .parser import parse_set, parse_values, parse_where
from .utils import load_metadata, load_table_data, save_metadata, save_table_data


def print_help() -> None:
    """
    Вывод справочной информации по доступным командам

    :return: None
    """
    print("\n***Управление таблицами***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\n***Операции с данными***")
    print("Функции:")
    print('<command> insert into <таблица> values ("str", 1, true) - создать запись')
    print("<command> select from <таблица> - прочитать все записи")
    print(
        "<command> select from <таблица> where <столбец> = <значение> - фильтрация"
    )
    print(
        "<command> update <таблица> set <столбец> = <значение> "
        "where <столбец> = <значение> - обновить"
    )
    print("<command> delete from <таблица> where <столбец> = <значение> - удалить")
    print("<command> info <таблица> - информация о таблице")

    print("\n***Общие команды***")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def run() -> None:
    """
    Главый цикл программы

    :return: None
    """
    print_help()

    while True:
        user_input = prompt.string("Введите команду: ").strip()

        if not user_input:
            continue

        raw = user_input.strip()

        m = re.fullmatch(
            r'insert\s+into\s+(\w+)\s+values\s*\((.*)\)\s*',
            raw,
            flags=re.IGNORECASE,
        )

        if m:
            table = m.group(1)
            values_inner = m.group(2)
            metadata = load_metadata(METADATA_PATH)
            table_data = load_table_data(table)

            values = parse_values(values_inner)
            try:
                table_data, new_id = insert(metadata, table, table_data, values)
            except (TableDoesNotExistError, InvalidValueError) as e:
                bad_value = getattr(e, "value", str(e))
                print(f"Некорректное значение: {bad_value}. Попробуйте снова.")
                continue

            save_table_data(table, table_data)
            print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table}".')
            continue

        m = re.fullmatch(
            r'select\s+from\s+(\w+)(?:\s+where\s+(.+))?\s*',
            raw,
            flags=re.IGNORECASE,
        )

        if m:
            table = m.group(1)
            where_raw = m.group(2)

            metadata = load_metadata(METADATA_PATH)
            _ = metadata.get(table)
            if table not in metadata:
                print(f'Ошибка: Таблица "{table}" не существует.')
                continue

            table_data = load_table_data(table)
            where_clause = parse_where(where_raw) if where_raw else None
            rows = select(table_data, where_clause)

            schema = metadata[table]["columns"]
            headers = [c["name"] for c in schema]

            pt = PrettyTable()
            pt.field_names = headers
            for r in rows:
                pt.add_row([r.get(h) for h in headers])

            print(pt)
            continue

        m = re.fullmatch(
            r'update\s+(\w+)\s+set\s+(.+?)\s+where\s+(.+)\s*',
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
            try:
                set_clause = parse_set(set_raw)
                where_clause = parse_where(where_raw)
                table_data, updated = update(
                    metadata,
                    table,
                    table_data,
                    set_clause,
                    where_clause,
                )
            except InvalidValueError as e:
                print(f"Некорректное значение: {e.value}. Попробуйте снова.")
                continue

            save_table_data(table, table_data)
            if updated == 0:
                print("Ничего не обновлено (нет подходящих записей).")
            else:
                print(
                    f'Записи в таблице "{table}" успешно обновлены. '
                    f'Изменено: {updated}.'
                )
            continue

        m = re.fullmatch(
            r'delete\s+from\s+(\w+)\s+where\s+(.+)\s*',
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
            table_data, deleted = delete(table_data, where_clause)

            save_table_data(table, table_data)
            print(f'Удалено записей: {deleted}.')
            continue

        m = re.fullmatch(r'info\s+(\w+)\s*', raw, flags=re.IGNORECASE)
        if m:
            table = m.group(1)
            metadata = load_metadata(METADATA_PATH)
            if table not in metadata:
                print(f'Ошибка: Таблица "{table}" не существует.')
                continue

            table_data = load_table_data(table)
            res = info(metadata, table, table_data)
            print(f'Таблица: {res["table"]}')
            print(f'Столбцы: {res["columns"]}')
            print(f'Количество записей: {res["count"]}')
            continue

        try:
            args = shlex.split(user_input)
        except ValueError:
            print("Некорректное значение <input>. Попробуйте снова")
            continue

        command = args[0]
        cmd_args = args[1:]

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

                try:
                    new_metadata = create_table(metadata, table_name, columns)
                except TableAlreadyExistsError as e:
                    print(f"Ошибка: {e}")
                    continue
                except InvalidValueError as e:
                    print(f"Некорректное значение: {e.value}. Попробуйте снова.")
                    continue

                save_metadata(METADATA_PATH, new_metadata)

                cols = new_metadata[table_name]["columns"]
                cols_text = ", ".join(
                    [f'{c["name"]}:{c["type"]}' for c in cols]
                )
                print(
                    f'Таблица "{table_name}" успешно создана со столбцами: '
                    f'{cols_text}'
                )

            case "drop_table":
                if len(cmd_args) != 1:
                    print("Некорректное значение: <args>. Попробуйте снова.")
                    continue

                table_name = cmd_args[0]

                try:
                    new_metadata = drop_table(metadata, table_name)
                except TableDoesNotExistError as e:
                    print(f"Ошибка: {e}")
                    continue

                save_metadata(METADATA_PATH, new_metadata)
                print(f'Таблица "{table_name}" успешно удалена.')

            case _:
                print(f"Функции {command} нет. Попробуйте снова.")
