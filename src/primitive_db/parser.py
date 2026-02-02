import re


def _split_commas(text: str) -> list[str]:
    """
    Разбивает строку по запятым, игнорируя запятые внутри кавычек.

    :param text: исходная строка
    :return: список частей
    """
    parts: list[str] = []
    buf: list[str] = []
    in_quotes = False
    i = 0

    while i < len(text):
        ch = text[i]

        if in_quotes and ch == "\\" and i + 1 < len(text):
            buf.append(text[i + 1])
            i += 2
            continue

        if ch == '"':

            if in_quotes and i + 1 < len(text) and text[i + 1] == '"':
                buf.append('"')
                i += 2
                continue

            in_quotes = not in_quotes
            buf.append(ch)
            i += 1
            continue

        if ch == "," and not in_quotes:
            parts.append("".join(buf))
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    parts.append("".join(buf))
    return parts


def _split_one_equals(part: str) -> tuple[str, str]:
    """
    Делит выражение key=value по '=', учитывая кавычки.
    Запрещает '==' и любые два '=' вне кавычек.

    :param part: строка присваивания
    :return: (key, value)
    :raises ValueError: если формат некорректный
    """
    in_quotes = False
    eq_pos: int | None = None

    i = 0
    while i < len(part):
        ch = part[i]

        if in_quotes and ch == "\\" and i + 1 < len(part):
            i += 2
            continue

        if ch == '"':
            if in_quotes and i + 1 < len(part) and part[i + 1] == '"':
                i += 2
                continue
            in_quotes = not in_quotes
            i += 1
            continue

        if ch == "=" and not in_quotes:
            if eq_pos is None:
                eq_pos = i
            else:
                raise ValueError(part)
        i += 1

    if eq_pos is None:
        raise ValueError(part)

    key = part[:eq_pos].strip()
    val = part[eq_pos + 1 :].strip()

    if not key:
        raise ValueError(part)

    return key, val


def parse_scalar(raw: str):
    """
    Преобразует строку в int/bool/str.
    Важно: если значение в двойных кавычках - это строка (без конвертаций).

    :param raw: исходное значение
    :return: преобразованное значение
    """
    s = raw.strip()

    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]

    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False

    if re.fullmatch(r"-?\d+", s):
        return int(s)

    return s


def parse_values(values_inner: str) -> list:
    """
    Парсит содержимое внутри values(...).

    :param values_inner: строка внутри скобок values(...)
    :return: список значений
    """
    if not values_inner.strip():
        return []

    parts = _split_commas(values_inner)
    result: list = []

    for part in parts:
        token = part.strip()
        if token == "":
            continue
        result.append(parse_scalar(token))

    return result


def parse_assignments(assignments: str) -> dict:
    """
    Парсит присваивания вида 'a = 1, b = "x"' в словарь.

    :param assignments: строка присваиваний
    :return: dict {поле: значение}
    :raises ValueError: если формат некорректен
    """
    if not assignments.strip():
        raise ValueError(assignments)

    parts = _split_commas(assignments)
    result: dict = {}

    for raw_part in parts:
        part = raw_part.strip()
        if part == "":
            raise ValueError(raw_part)

        key, val = _split_one_equals(part)
        result[key] = parse_scalar(val)

    return result


def parse_where(where_part: str) -> dict:
    """
    Парсит where-условие вида 'age = 28'.

    :param where_part: строка после where
    :return: dict условия
    """
    return parse_assignments(where_part)


def parse_set(set_part: str) -> dict:
    """
    Парсит set-выражение вида 'age = 29, active = true'.

    :param set_part: строка после set
    :return: dict изменений
    """
    return parse_assignments(set_part)
