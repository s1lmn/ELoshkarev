from __future__ import annotations

import unittest
from unittest.mock import patch

from src.db.backend.memory import StudentTable
from src.db.tui import TUI


class TestTUI(unittest.TestCase):
    def setUp(self) -> None:
        self.student_table = StudentTable()
        self.tui = TUI(self.student_table)

    @patch("builtins.print")
    @patch(
        "builtins.input",
        side_effect=["1", "John", "Doe", "20", "M"],
    )
    def test_add_student(self, input_mock, print_mock) -> None:
        self.tui._add_student()

        self.assertEqual(
            self.student_table.select_record(),
            [(1, "John", "Doe", 20, "M")],
        )
        print_mock.assert_any_call("Запись добавлена: (1, 'John', 'Doe', 20, 'M')")

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["", "Jane", "", "", "F"])
    def test_find_students_by_filter(self, input_mock, print_mock) -> None:
        self.student_table.create_record(1, "John", "Doe", 20, "M")
        self.student_table.create_record(2, "Jane", "Smith", 22, "F")

        self.tui._find_students_by_filter()

        print_mock.assert_any_call((2, "Jane", "Smith", 22, "F"))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["x", "3"])
    def test_read_int_retries_until_valid_value(self, input_mock, print_mock) -> None:
        result = self.tui._read_int("age: ")

        self.assertEqual(result, 3)
        print_mock.assert_any_call("Ошибка: введите целое число.")

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["hello", ""])
    def test_read_optional_int_allows_empty_value(self, input_mock, print_mock) -> None:
        result = self.tui._read_optional_int("id: ")

        self.assertIsNone(result)
        print_mock.assert_any_call("Ошибка: введите целое число или оставьте поле пустым.")

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["9", "0"])
    def test_run_handles_unknown_command_and_exit(self, input_mock, print_mock) -> None:
        self.tui.run()

        print_mock.assert_any_call("Неизвестная команда. Повторите ввод.")
        print_mock.assert_any_call("Выход из программы.")
