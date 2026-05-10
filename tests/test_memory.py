from __future__ import annotations

import unittest

from src.db.backend.errors import DuplicateIDError, InvalidAgeError
from src.db.backend.memory import StudentTable


class TestMemory(unittest.TestCase):
    def setUp(self) -> None:
        self.student_table = StudentTable()

    def test_student_table_allocation(self) -> None:
        self.assertIsInstance(self.student_table, StudentTable)

    def test_create_record(self) -> None:
        cases = [
            (1, "John", "Doe", 20, "M"),
            (2, "Jane", "Smith", 22, "F"),
            (3, "Alice", "Johnson", 19, "F"),
        ]

        for test_data in cases:
            with self.subTest(test_data=test_data):
                record = self.student_table.create_record(*test_data)
                self.assertEqual(record, test_data)

    def test_create_record_negative_age(self) -> None:
        with self.assertRaises(InvalidAgeError) as context:
            self.student_table.create_record(1, "John", "Doe", -5, "M")

        self.assertEqual(str(context.exception), "Поле age не может быть отрицательным.")

    def test_create_record_duplicate_id(self) -> None:
        self.student_table.create_record(1, "John", "Doe", 20, "M")

        with self.assertRaises(DuplicateIDError) as context:
            self.student_table.create_record(1, "Jane", "Smith", 22, "F")

        self.assertEqual(str(context.exception), "Запись с id=1 уже существует.")

    def test_select_record(self) -> None:
        test_datas = [
            (1, "John", "Doe", 20, "M"),
            (2, "Jane", "Smith", 22, "F"),
            (3, "Alice", "Johnson", 19, "F"),
            (4, "Bob", "Brown", 21, "M"),
        ]

        for test_data in test_datas:
            self.student_table.create_record(*test_data)

        cases = [
            ("all", {}, test_datas),
            ("id", {"student_id": 1}, [test_datas[0]]),
            ("first_name", {"first_name": "Jane"}, [test_datas[1]]),
            ("age", {"age": 21}, [test_datas[3]]),
            ("sex", {"sex": "F"}, [test_datas[1], test_datas[2]]),
            (
                "combined",
                {"first_name": "Alice", "age": 19},
                [test_datas[2]],
            ),
        ]

        for name, filters, expected in cases:
            with self.subTest(case=name):
                self.assertEqual(self.student_table.select_record(**filters), expected)
