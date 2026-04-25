from __future__ import annotations

import unittest

from inmemory_db.cli import ConsoleInterface
from inmemory_db.exceptions import ValidationError


class FakeIO:

    def __init__(self, inputs: list[str] | None = None, raises_interrupt: bool = False) -> None:
        self._inputs = list(inputs or [])
        self._raises_interrupt = raises_interrupt
        self.outputs: list[str] = []

    def input(self, prompt: str) -> str:
        self.outputs.append(prompt)
        if self._raises_interrupt:
            raise KeyboardInterrupt
        if not self._inputs:
            raise AssertionError("Недостаточно входных данных для теста.")
        return self._inputs.pop(0)

    def output(self, message: str) -> None:
        self.outputs.append(message)


class ConsoleInterfaceTests(unittest.TestCase):
    def test_run_handles_full_flow_with_sorting(self) -> None:
        fake_io = FakeIO(
            [
                "1",
                "books",
                "4",
                "id",
                "int",
                "title",
                "str",
                "author",
                "str",
                "year",
                "int",
                "id",
                "7",
                "books",
                "author",
                "2",
                "books",
                "1",
                "Refactoring",
                "Martin Fowler",
                "1999",
                "2",
                "books",
                "2",
                "Clean Code",
                "Robert Martin",
                "2008",
                "3",
                "books",
                "yes",
                "1",
                "author",
                "Robert Martin",
                "6",
                "books",
                "year",
                "desc",
                "8",
                "0",
            ]
        )

        interface = ConsoleInterface(io_handler=fake_io)
        interface.run()

        joined_output = "\n".join(fake_io.outputs)
        self.assertIn("Текущий backend: memory", joined_output)
        self.assertIn("Таблица 'books' успешно создана.", joined_output)
        self.assertIn("Индекс создан: author", joined_output)
        self.assertIn(
            "Запись добавлена: {'id': 1, 'title': 'Refactoring', 'author': 'Martin Fowler', 'year': 1999}",
            joined_output,
        )
        self.assertIn(
            "Запись добавлена: {'id': 2, 'title': 'Clean Code', 'author': 'Robert Martin', 'year': 2008}",
            joined_output,
        )
        self.assertIn(
            "1. {'id': 2, 'title': 'Clean Code', 'author': 'Robert Martin', 'year': 2008}",
            joined_output,
        )
        self.assertIn("Список таблиц:", joined_output)
        self.assertIn("Работа завершена.", joined_output)

    def test_run_reports_database_error(self) -> None:
        fake_io = FakeIO(["2", "missing", "0"])

        interface = ConsoleInterface(io_handler=fake_io)
        interface.run()

        joined_output = "\n".join(fake_io.outputs)
        self.assertIn("Ошибка: Таблица 'missing' не найдена.", joined_output)

    def test_run_reports_invalid_command(self) -> None:
        fake_io = FakeIO(["42", "0"])

        interface = ConsoleInterface(io_handler=fake_io)
        interface.run()

        self.assertIn("Неизвестная команда. Повторите ввод.", fake_io.outputs)

    def test_run_handles_keyboard_interrupt(self) -> None:
        fake_io = FakeIO(raises_interrupt=True)

        interface = ConsoleInterface(io_handler=fake_io)
        interface.run()

        self.assertIn("\nРабота завершена пользователем.", fake_io.outputs)

    def test_read_positive_int_raises_for_invalid_value(self) -> None:
        fake_io = FakeIO(["abc"])
        interface = ConsoleInterface(io_handler=fake_io)

        with self.assertRaisesRegex(ValidationError, "Нужно ввести целое число."):
            interface._read_positive_int("Введите число: ")

    def test_read_sort_direction_accepts_desc(self) -> None:
        fake_io = FakeIO(["desc"])
        interface = ConsoleInterface(io_handler=fake_io)

        self.assertTrue(interface._read_sort_direction())
