from __future__ import annotations

from .backend import DatabaseError, FileDatabase, MemoryDatabase


class TUI:
    def __init__(self, database=None) -> None:
        self.database = database or self._choose_database()

    @staticmethod
    def _choose_database():
        print("Выберите тип базы данных:")
        print("1. In-memory")
        print("2. File database (JSON)")

        choice = input("Введите номер: ").strip()
        if choice == "2":
            return FileDatabase()
        return MemoryDatabase()

    def run(self) -> None:
        while True:
            self._print_menu()
            action = input("Выберите действие: ").strip()

            try:
                if action == "1":
                    self._create_table()
                elif action == "2":
                    self._insert_record()
                elif action == "3":
                    self._select_records()
                elif action == "0":
                    print("Выход из программы.")
                    break
                else:
                    print("Неизвестная команда. Повторите ввод.")
            except DatabaseError as error:
                print(f"Ошибка: {error}")

    @staticmethod
    def _print_menu() -> None:
        print("\n=== База данных ===")
        print("1. Создать таблицу")
        print("2. Добавить запись")
        print("3. Найти записи")
        print("0. Выход")

    def _create_table(self) -> None:
        table_name = input("Имя таблицы: ").strip()
        column_count = self._read_positive_int("Количество полей: ")
        columns: list[str] = []

        for index in range(1, column_count + 1):
            columns.append(input(f"Имя поля #{index}: ").strip())

        self.database.create_table(table_name, tuple(columns))
        print(f"Таблица '{table_name}' создана.")

    def _insert_record(self) -> None:
        table_name = input("Имя таблицы: ").strip()
        columns = self.database.get_columns(table_name)
        record: dict[str, str] = {}

        for column in columns:
            record[column] = input(f"{column}: ").strip()

        self.database.insert_record(table_name, record)
        print("Запись добавлена.")

    def _select_records(self) -> None:
        table_name = input("Имя таблицы: ").strip()
        wants_filters = input("Нужна фильтрация? (yes/no): ").strip().lower()
        filters: dict[str, str] = {}

        if wants_filters in {"yes", "y", "да", "д"}:
            filter_count = self._read_positive_int("Количество фильтров: ")
            for index in range(1, filter_count + 1):
                field_name = input(f"Поле фильтра #{index}: ").strip()
                field_value = input(f"Значение поля '{field_name}': ").strip()
                filters[field_name] = field_value

        records = self.database.select_records(table_name, **filters)
        if not records:
            print("Записи не найдены.")
            return

        for record in records:
            print(record)

    @staticmethod
    def _read_positive_int(prompt: str) -> int:
        while True:
            raw_value = input(prompt).strip()
            try:
                parsed_value = int(raw_value)
            except ValueError:
                print("Ошибка: введите целое число.")
                continue

            if parsed_value <= 0:
                print("Ошибка: число должно быть больше нуля.")
                continue

            return parsed_value


def run() -> None:
    TUI().run()
