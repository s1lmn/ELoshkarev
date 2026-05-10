from __future__ import annotations

from .backend.errors import StudentTableError
from .backend.memory import StudentRecord, StudentTable


class TUI:
    def __init__(self, student_table: StudentTable | None = None) -> None:
        self.student_table = student_table or StudentTable()

    def run(self) -> None:
        while True:
            self._print_menu()
            action = input("Выберите действие: ").strip()

            if action == "1":
                self._add_student()
            elif action == "2":
                self._show_all_students()
            elif action == "3":
                self._find_students_by_filter()
            elif action == "0":
                print("Выход из программы.")
                break
            else:
                print("Неизвестная команда. Повторите ввод.")

    @staticmethod
    def _print_menu() -> None:
        print("\n=== База студентов ===")
        print("1. Добавить запись")
        print("2. Показать все записи")
        print("3. Найти записи по фильтру")
        print("0. Выход")

    @staticmethod
    def _read_int(prompt: str) -> int:
        while True:
            raw = input(prompt).strip()
            try:
                return int(raw)
            except ValueError:
                print("Ошибка: введите целое число.")

    @staticmethod
    def _read_optional_int(prompt: str) -> int | None:
        while True:
            raw = input(prompt).strip()
            if raw == "":
                return None
            try:
                return int(raw)
            except ValueError:
                print("Ошибка: введите целое число или оставьте поле пустым.")

    @staticmethod
    def _print_records(records: list[StudentRecord]) -> None:
        if not records:
            print("Записи не найдены.")
            return

        for record in records:
            print(record)

    def _add_student(self) -> None:
        print("\nДобавление записи")
        student_id = self._read_int("id: ")
        first_name = input("first_name: ").strip()
        second_name = input("second_name: ").strip()
        age = self._read_int("age: ")
        sex = input("sex: ").strip()

        try:
            record = self.student_table.create_record(
                student_id,
                first_name,
                second_name,
                age,
                sex,
            )
            print(f"Запись добавлена: {record}")
        except StudentTableError as error:
            print(f"Ошибка: {error}")

    def _show_all_students(self) -> None:
        print("\nСписок записей")
        self._print_records(self.student_table.select_record())

    def _find_students_by_filter(self) -> None:
        print("\nПоиск по фильтру (Enter = пропустить поле)")
        student_id = self._read_optional_int("id: ")
        first_name = input("first_name: ").strip() or None
        second_name = input("second_name: ").strip() or None
        age = self._read_optional_int("age: ")
        sex = input("sex: ").strip() or None

        records = self.student_table.select_record(
            student_id=student_id,
            first_name=first_name,
            second_name=second_name,
            age=age,
            sex=sex,
        )
        self._print_records(records)


def run() -> None:
    TUI().run()
