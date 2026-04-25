from __future__ import annotations

from .database import InMemoryDatabase
from .exceptions import DatabaseError, ValidationError
from .models import FieldDefinition, SUPPORTED_TYPES


class ConsoleInterface:

    def __init__(self) -> None:
        self.database = InMemoryDatabase()

    def run(self) -> None:
        self._print_welcome()

        while True:
            self._print_menu()
            choice = input("Выберите действие: ").strip()

            try:
                if choice == "1":
                    self._handle_create_table()
                elif choice == "2":
                    self._handle_insert()
                elif choice == "3":
                    self._handle_select()
                elif choice == "4":
                    self._handle_update()
                elif choice == "5":
                    self._handle_delete()
                elif choice == "6":
                    self._handle_list_tables()
                elif choice == "0":
                    print("Работа завершена.")
                    break
                else:
                    print("Неизвестная команда. Повторите ввод.")
            except DatabaseError as error:
                print(f"Ошибка: {error}")
            except KeyboardInterrupt:
                print("\nРабота завершена пользователем.")
                break

    def _print_welcome(self) -> None:
        print("In-memory база данных")
        print("Сначала создайте хотя бы одну таблицу, затем добавляйте и запрашивайте записи.")

    def _print_menu(self) -> None:
        print("\nМеню:")
        print("1. Создать таблицу")
        print("2. Добавить запись")
        print("3. Прочитать записи с фильтрацией")
        print("4. Обновить запись")
        print("5. Удалить запись")
        print("6. Показать список таблиц")
        print("0. Выход")

    def _handle_create_table(self) -> None:
        table_name = input("Введите имя таблицы: ").strip()
        field_count = self._read_positive_int("Введите количество полей: ")
        fields: list[FieldDefinition] = []

        print(f"Доступные типы: {', '.join(sorted(SUPPORTED_TYPES))}")
        for index in range(1, field_count + 1):
            field_name = input(f"Имя поля #{index}: ").strip()
            field_type = input(f"Тип поля #{index}: ").strip().lower()
            fields.append(FieldDefinition(name=field_name, type_name=field_type))

        primary_key = input("Введите имя поля, которое будет первичным ключом: ").strip()
        self.database.create_table(table_name=table_name, fields=fields, primary_key=primary_key)
        print(f"Таблица '{table_name}' успешно создана.")

    def _handle_insert(self) -> None:
        table = self._read_table()
        record_data = {}

        print(f"Добавление записи в таблицу '{table.schema.name}'.")
        for field in table.schema.fields:
            record_data[field.name] = input(
                f"{field.name} ({field.type_name}): "
            ).strip()

        inserted_record = table.insert(record_data)
        print(f"Запись добавлена: {inserted_record}")

    def _handle_select(self) -> None:
        table = self._read_table()
        filters = self._read_filters(table.schema.name)
        records = table.select(filters)

        if not records:
            print("Записи не найдены.")
            return

        print(f"Найдено записей: {len(records)}")
        for index, record in enumerate(records, start=1):
            print(f"{index}. {record}")

    def _handle_update(self) -> None:
        table = self._read_table()
        primary_key_name = table.schema.primary_key
        primary_key_value = input(
            f"Введите значение первичного ключа '{primary_key_name}': "
        ).strip()
        update_count = self._read_positive_int("Сколько полей нужно обновить: ")
        updated_values = {}

        for index in range(1, update_count + 1):
            field_name = input(f"Имя обновляемого поля #{index}: ").strip()
            field_value = input(f"Новое значение для поля '{field_name}': ").strip()
            updated_values[field_name] = field_value

        updated_record = table.update(primary_key_value, updated_values)
        print(f"Запись обновлена: {updated_record}")

    def _handle_delete(self) -> None:
        table = self._read_table()
        primary_key_name = table.schema.primary_key
        primary_key_value = input(
            f"Введите значение первичного ключа '{primary_key_name}' для удаления: "
        ).strip()
        deleted_record = table.delete(primary_key_value)
        print(f"Запись удалена: {deleted_record}")

    def _handle_list_tables(self) -> None:
        tables = self.database.list_tables()
        if not tables:
            print("Таблицы ещё не созданы.")
            return

        print("Список таблиц:")
        for table in tables:
            field_descriptions = ", ".join(
                f"{field.name}:{field.type_name}" for field in table.schema.fields
            )
            print(
                f"- {table.schema.name} | PK: {table.schema.primary_key} | "
                f"Поля: {field_descriptions} | Записей: {table.count()}"
            )

    def _read_table(self):
        table_name = input("Введите имя таблицы: ").strip()
        return self.database.get_table(table_name)

    def _read_filters(self, table_name: str) -> dict[str, str]:
        wants_filters = input("Нужна фильтрация? (yes/no): ").strip().lower()
        if wants_filters in {"no", "n", "нет", "н"}:
            return {}
        if wants_filters not in {"yes", "y", "да", "д"}:
            raise ValidationError("Ответьте yes/no.")

        filter_count = self._read_positive_int("Введите количество фильтров: ")
        filters: dict[str, str] = {}

        for index in range(1, filter_count + 1):
            field_name = input(f"Поле фильтра #{index} для таблицы '{table_name}': ").strip()
            field_value = input(f"Значение фильтра для поля '{field_name}': ").strip()
            filters[field_name] = field_value

        return filters

    @staticmethod
    def _read_positive_int(prompt: str) -> int:
        raw_value = input(prompt).strip()
        try:
            parsed_value = int(raw_value)
        except ValueError as error:
            raise ValidationError("Нужно ввести целое число.") from error

        if parsed_value <= 0:
            raise ValidationError("Число должно быть больше нуля.")
        return parsed_value
