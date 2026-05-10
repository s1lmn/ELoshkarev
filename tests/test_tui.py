from __future__ import annotations

import unittest
from unittest.mock import patch

from src.db.backend.memory import MemoryDatabase
from src.db.tui import TUI


class TestTUI(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MemoryDatabase()
        self.tui = TUI(self.db)

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["students", "2", "student_id", "name"])
    def test_create_table(self, input_mock, print_mock) -> None:
        self.tui._create_table()

        self.assertTrue(self.db._table_exists("students"))
        print_mock.assert_any_call("Таблица 'students' создана.")

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["bad", "0", "2"])
    def test_read_positive_int(self, input_mock, print_mock) -> None:
        result = self.tui._read_positive_int("Количество: ")

        self.assertEqual(result, 2)
        print_mock.assert_any_call("Ошибка: введите целое число.")
        print_mock.assert_any_call("Ошибка: число должно быть больше нуля.")

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["9", "0"])
    def test_run_handles_unknown_command_and_exit(self, input_mock, print_mock) -> None:
        self.tui.run()

        print_mock.assert_any_call("Неизвестная команда. Повторите ввод.")
        print_mock.assert_any_call("Выход из программы.")
