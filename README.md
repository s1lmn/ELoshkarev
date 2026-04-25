## Описание проекта

Проект представляет собой консольную СУБД с объектно-ориентированной архитектурой.
Приложение поддерживает три backend-а хранения:

- `memory` - данные живут только во время работы программы;
- `json` - структура таблиц, записи и индексы сохраняются в JSON-файлах;
- `csv` - структура таблиц, записи и индексы сохраняются в CSV-файлах.

Также реализована индексация по одному или нескольким полям для ускорения операций чтения.

## Структура проекта

```text
project_root/
├── main.py
├── README.md
├── .gitignore
├── inmemory_db/
│   ├── __init__.py
│   ├── cli.py
│   ├── database.py
│   ├── exceptions.py
│   ├── io_handler.py
│   ├── models.py
│   ├── storage.py
│   └── table.py
└── tests/
    ├── __init__.py
    ├── test_cli.py
    ├── test_database.py
    ├── test_file_databases.py
    ├── test_main.py
    ├── test_models.py
    └── test_table.py
```

## Назначение модулей

- `main.py` - разбор аргументов и запуск приложения.
- `inmemory_db/database.py` - реализации баз данных: in-memory, JSON и CSV.
- `inmemory_db/table.py` - таблица, CRUD-операции, сортировка и индексы.
- `inmemory_db/storage.py` - файловые адаптеры хранения для JSON и CSV.
- `inmemory_db/models.py` - схема таблиц, поля и преобразование типов.
- `inmemory_db/cli.py` - консольный интерфейс.
- `inmemory_db/exceptions.py` - пользовательские исключения.
- `tests/` - автоматизированные тесты.

## Реализованная функциональность

- создание нескольких таблиц;
- добавление, чтение, обновление и удаление записей;
- фильтрация по одному или нескольким полям;
- сортировка записей по выбранному полю;
- создание индексов по одному или нескольким полям;
- использование индексов в операциях чтения;
- корректное обновление индексов после `insert`, `update` и `delete`;
- хранение данных в памяти, JSON или CSV;
- восстановление таблиц, записей и индексов после перезапуска программы;
- обработка ошибок пользовательского ввода и ошибок работы с файлами.

## Различия между реализациями

- `InMemoryDatabase` не сохраняет данные на диск и подходит для временной работы.
- `JsonFileDatabase` сохраняет каждую таблицу в отдельный JSON-файл.
- `CsvFileDatabase` сохраняет схему, записи и индексы таблицы в набор CSV-файлов.

Публичный интерфейс у всех реализаций одинаковый:

- `create_table(...)`
- `get_table(...)`
- `list_tables()`

Каждая таблица поддерживает:

- `insert(...)`
- `select(...)`
- `update(...)`
- `delete(...)`
- `sort_records(...)`
- `create_index(...)`

## Запуск программы

### In-memory режим

```
python3 main.py
```

### JSON backend

```
python3 main.py --backend json --data-dir ./data/json
```

### CSV backend

```
python3 main.py --backend csv --data-dir ./data/csv
```

Если `--data-dir` не указан, используется каталог `data/json` или `data/csv` относительно корня проекта.

## Запуск тестов

```
python3 -m unittest discover -s tests -v
```

## Проверка покрытия

Если установлен модуль `coverage`:

```
python3 -m coverage run -m unittest discover -s tests
python3 -m coverage report -m
```

Если `coverage` не установлен, можно воспользоваться стандартным модулем Python:

```
python3 -m trace --count --summary --module unittest discover -s tests
```

## Особенности хранения файлов

### JSON

Для каждой таблицы создаётся один файл:

- `table_name.json`

### CSV

Для каждой таблицы создаётся набор файлов:

- `table_name__schema.csv`
- `table_name__records.csv`
- `table_name__indexes.csv`
