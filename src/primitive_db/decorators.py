import time
from functools import wraps

import prompt


class OperationCancelledError(Exception):
    """
    Исключение для отмены опасной операции пользователем.
    """


def handle_db_errors(func):
    """
    Централизованная обработка ошибок для функций БД.

    Перехватывает FileNotFoundError, KeyError, ValueError и печатает сообщение.
    При ошибке возвращает None.

    :param func: оборачиваемая функция
    :return: обертка
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except OperationCancelledError:
            print("Операция отменена.")
            return None

        except FileNotFoundError:
            print("Ошибка: Файл данных не найден.")
            return None

        except KeyError as e:
            msg = getattr(e, "args", None)
            text = msg[0] if msg else str(e)
            print(f'Ошибка: {text}.')
            return None

        except ValueError as e:
            bad_value = getattr(e, "value", None)
            if bad_value is None:
                bad_value = str(e)
            print(f"Некорректное значение: {bad_value}. Попробуйте снова.")
            return None

    return wrapper


def confirm_action(action_name: str):
    """
    Фабрика декораторов для подтверждения опасных операций.

    :param action_name: название действия для подтверждения
    :return: декоратор
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ans = prompt.string(
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            ).strip().lower()

            if ans != "y":
                raise OperationCancelledError(action_name)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func):
    """
    Замер времени выполнения функции.

    Выводит: Функция <имя> выполнилась за X.XXX секунд.

    :param func: оборачиваемая функция
    :return: обертка
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        result = func(*args, **kwargs)
        elapsed = time.monotonic() - start

        if result is not None:
            print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")

        return result

    return wrapper


def create_cacher():
    """
    Создает кэшер на основе замыкания.

    Внутренняя функция cache_result(key, value_func) возвращает значение по ключу
    из кэша или вычисляет его через value_func, сохраняет и возвращает.

    :return: функция cache_result(key, value_func)
    """
    cache = {}

    def cache_result(key, value_func):
        if key in cache:
            return cache[key]
        value = value_func()
        cache[key] = value
        return value

    return cache_result
