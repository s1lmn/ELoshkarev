from __future__ import annotations

from collections.abc import Callable

from .database import BaseDatabase, InMemoryDatabase
from .exceptions import DatabaseError, ValidationError
from .io_handler import ConsoleIO, IOHandler
from .models import FieldDefinition, SUPPORTED_TYPES


class ConsoleInterface:

    def __init__(
        self,
        database: BaseDatabase | None = None,
        io_handler: IOHandler | None = None,
    ) -> None:
        self.database = database or InMemoryDatabase()
        self.io = io_handler or ConsoleIO()
        self._actions: dict[str, Callable[[], None]] = {
            "1": self._handle_create_table,
            "2": self._handle_insert,
            "3": self._handle_select,
            "4": self._handle_update,
            "5": self._handle_delete,
            "6": self._handle_sort,
            "7": self._handle_create_index,
            "8": self._handle_list_tables,
        }

    def run(self) -> None:
        self._print_welcome()

        while True:
            self._print_menu()

            try:
                choice = self.io.input("Выберите действие: ").strip()
                if choice == "0":
                    self.io.output("Работа завершена.")
                    break

                action = self._actions.get(choice)
                if action is None:
                    self.io.output("Неизвестная команда. Повторите ввод.")
                    continue

                action()
            except DatabaseError as error:
                self.io.output(f"Ошибка: {error}")
            except KeyboardInterrupt:
                self.io.output("\nРабота завершена пользователем.")
                break

    def _print_welcome(self) -> None:
        self.io.output("Консольная СУБД")
        self.io.output(f"Текущий backend: {self.database.backend_name}")
        self.io.output(
            "Сначала создайте хотя бы одну таблицу, затем добавляйте и запрашивайте записи."
        )

    def _print_menu(self) -> None:
        self.io.output("\nМеню:")
        self.io.output("1. Создать таблицу")
        self.io.output("2. Добавить запись")
        self.io.output("3. Прочитать записи с фильтрацией")
        self.io.output("4. Обновить запись")
        self.io.output("5. Удалить запись")
        self.io.output("6. Отсортировать записи")
        self.io.output("7. Создать индекс")
        self.io.output("8. Показать список таблиц")
        self.io.output("0. Выход")

    def _handle_create_table(self) -> None:
        table_name = self.io.input("Введите имя таблицы: ").strip()
        field_count = self._read_positive_int("Введите количество полей: ")
        fields: list[FieldDefinition] = []

        self.io.output(f"Доступные типы: {', '.join(sorted(SUPPORTED_TYPES))}")
        for index in range(1, field_count + 1):
            field_name = self.io.input(f"Имя поля #{index}: ").strip()
            field_type = self.io.input(f"Тип поля #{index}: ").strip().lower()
            fields.append(FieldDefinition(name=field_name, type_name=field_type))

        primary_key = self.io.input(
            "Введите имя поля, которое будет первичным ключом: "
        ).strip()
        self.database.create_table(table_name=table_name, fields=fields, primary_key=primary_key)
        self.io.output(f"Таблица '{table_name}' успешно создана.")

    def _handle_insert(self) -> None:
        table = self._read_table()
        record_data = {}

        self.io.output(f"Добавление записи в таблицу '{table.schema.name}'.")
        for field in table.schema.fields:
            prompt = f"{field.name} ({field.type_name}): "
            record_data[field.name] = self.io.input(prompt).strip()

        inserted_record = table.insert(record_data)
        self.io.output(f"Запись добавлена: {inserted_record}")

    def _handle_select(self) -> None:
        table = self._read_table()
        filters = self._read_filters(table.schema.name)
        records = table.select(filters)
        self._render_records(records, "Записи не найдены.")

    def _handle_update(self) -> None:
        table = self._read_table()
        primary_key_name = table.schema.primary_key
        primary_key_value = self.io.input(
            f"Введите значение первичного ключа '{primary_key_name}': "
        ).strip()
        update_count = self._read_positive_int("Сколько полей нужно обновить: ")
        updated_values = {}

        for index in range(1, update_count + 1):
            field_name = self.io.input(f"Имя обновляемого поля #{index}: ").strip()
            field_value = self.io.input(
                f"Новое значение для поля '{field_name}': "
            ).strip()
            updated_values[field_name] = field_value

        updated_record = table.update(primary_key_value, updated_values)
        self.io.output(f"Запись обновлена: {updated_record}")

    def _handle_delete(self) -> None:
        table = self._read_table()
        primary_key_name = table.schema.primary_key
        primary_key_value = self.io.input(
            f"Введите значение первичного ключа '{primary_key_name}' для удаления: "
        ).strip()
        deleted_record = table.delete(primary_key_value)
        self.io.output(f"Запись удалена: {deleted_record}")

    def _handle_sort(self) -> None:
        table = self._read_table()
        field_name = self.io.input("Введите поле для сортировки: ").strip()
        descending = self._read_sort_direction()
        records = table.sort_records(field_name, descending=descending)
        self._render_records(records, "В таблице нет записей для сортировки.")

    def _handle_create_index(self) -> None:
        table = self._read_table()
        raw_fields = self.io.input(
            "Введите одно или несколько полей через запятую: "
        ).strip()
        field_names = [field.strip() for field in raw_fields.split(",") if field.strip()]
        created_index = table.create_index(field_names)
        self.io.output(f"Индекс создан: {', '.join(created_index)}")

    def _handle_list_tables(self) -> None:
        tables = self.database.list_tables()
        if not tables:
            self.io.output("Таблицы ещё не созданы.")
            return

        self.io.output("Список таблиц:")
        for table in tables:
            field_descriptions = ", ".join(
                f"{field.name}:{field.type_name}" for field in table.schema.fields
            )
            index_descriptions = ", ".join("+".join(index) for index in table.list_indexes())
            indexes_part = index_descriptions if index_descriptions else "нет"
            self.io.output(
                f"- {table.schema.name} | PK: {table.schema.primary_key} | "
                f"Поля: {field_descriptions} | Записей: {table.count()} | "
                f"Индексы: {indexes_part}"
            )

    def _read_table(self):
        table_name = self.io.input("Введите имя таблицы: ").strip()
        return self.database.get_table(table_name)

    def _read_filters(self, table_name: str) -> dict[str, str]:
        wants_filters = self.io.input("Нужна фильтрация? (yes/no): ").strip().lower()
        if wants_filters in {"no", "n", "нет", "н"}:
            return {}
        if wants_filters not in {"yes", "y", "да", "д"}:
            raise ValidationError("Ответьте yes/no.")

        filter_count = self._read_positive_int("Введите количество фильтров: ")
        filters: dict[str, str] = {}

        for index in range(1, filter_count + 1):
            field_name = self.io.input(
                f"Поле фильтра #{index} для таблицы '{table_name}': "
            ).strip()
            field_value = self.io.input(
                f"Значение фильтра для поля '{field_name}': "
            ).strip()
            filters[field_name] = field_value

        return filters

    def _read_sort_direction(self) -> bool:
        direction = self.io.input(
            "Направление сортировки (asc/desc): "
        ).strip().lower()
        if direction == "asc":
            return False
        if direction == "desc":
            return True
        raise ValidationError("Используйте asc или desc.")

    def _render_records(self, records: list[dict[str, object]], empty_message: str) -> None:
        if not records:
            self.io.output(empty_message)
            return

        self.io.output(f"Найдено записей: {len(records)}")
        for index, record in enumerate(records, start=1):
            self.io.output(f"{index}. {record}")

    def _read_positive_int(self, prompt: str) -> int:
        raw_value = self.io.input(prompt).strip()
        try:
            parsed_value = int(raw_value)
        except ValueError as error:
            raise ValidationError("Нужно ввести целое число.") from error

        if parsed_value <= 0:
            raise ValidationError("Число должно быть больше нуля.")
        return parsed_value
