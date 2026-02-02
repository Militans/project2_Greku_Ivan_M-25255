# Primitive DB — project2 (primitive_db)

Примитивная JSON-база данных с консольным интерфейсом: управление таблицами, CRUD-операции, подтверждение опасных действий, замер времени выполнения и кэширование выборок.

## Возможности

### Управление таблицами
- `create_table <table> <col:type> ...` - создать таблицу (колонка `ID:int` добавляется автоматически)
- `list_tables` - показать список таблиц
- `drop_table <table>` - удалить таблицу (с подтверждением)

Поддерживаемые типы данных: `int`, `str`, `bool`.

### CRUD-операции
- `insert into <table> values (<v1>, <v2>, ...)` - добавить запись (ID генерируется автоматически)
- `select from <table>` - вывести все записи
- `select from <table> where <col> = <value>` - вывести записи по условию
- `update <table> set <col> = <value> where <col> = <value>` - обновить записи по условию
- `delete from <table> where <col> = <value>` - удалить записи по условию (с подтверждением)
- `info <table>` - информация о таблице (схема + количество записей)

### Декораторы и улучшения качества
- Централизованная обработка ошибок (`handle_db_errors`)
- Подтверждение опасных операций (`confirm_action`) для `drop_table` и `delete`
- Замер времени выполнения (`log_time`) для “медленных” операций
- Кэширование результатов одинаковых `select` на основе замыкания

## Хранение данных

- Метаданные: `data/db_meta.json`
- Данные таблиц: `data/<table>.json`

## Установка и запуск

### Через Makefile
```bash
make install
make project
```

### Через Poetry
```bash
poetry install
poetry run database
```

Также доступен запуск:
```bash
poetry run project
```

## Проверка стиля (Ruff)

```bash
make lint
# или
poetry run ruff check .
```

## Сборка и dry-run публикации

```bash
make build
make publish
```

## Демонстрация (asciinema)


[![asciicast](https://asciinema.org/connect/3781b6e0-ce51-411b-9da8-c33c05c23451.svg)](https://asciinema.org/connect/3781b6e0-ce51-411b-9da8-c33c05c23451)



## Пример сценария в консоли

```text
create_table users name:str age:int is_active:bool
list_tables
insert into users values ("Sergei", 28, true)
select from users
select from users where age = 28
update users set age = 29 where name = "Sergei"
select from users where age = 29
delete from users where ID = 1
info users
drop_table users
list_tables
exit
```


