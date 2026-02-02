import prompt

import shlex


from .constants import METADATA_PATH
from .core import (
    InvalidValueError,
    TableAlreadyExistsError,
    TableDoesNotExistError,
    create_table,
    drop_table,
    list_tables,
)
from .utils import load_metadata, save_metadata



# src/primitive_db/engine.py
def print_help():
    """Prints the help message for the current mode."""

    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\nОбщие команды:")
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

                cols_text = ", ".join([f'{c["name"]}:{c["type"]}' for c in new_metadata[table_name]["columns"]])
                print(f'Таблица "{table_name}" успешно создана со столбцами: {cols_text}')

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


