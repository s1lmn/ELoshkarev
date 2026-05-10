from __future__ import annotations

import unittest

from src.db.backend.errors import MissingColumnError, TableAlreadyExistsError, UnknownColumnError
from src.db.backend.memory import MemoryDatabase


class TestMemoryDatabase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = MemoryDatabase()
        self.db.create_table("students", ("student_id", "name"))

    def test_create_existing_table_raises_error(self) -> None:
        with self.assertRaises(TableAlreadyExistsError):
            self.db.create_table("students", ("student_id", "name"))

    def test_insert_and_select_records(self) -> None:
        self.db.insert_record("students", {"student_id": 1, "name": "Иван"})
        self.db.insert_record("students", {"student_id": 2, "name": "Мария"})

        self.assertEqual(
            self.db.select_records("students", name="Мария"),
            [{"student_id": 2, "name": "Мария"}],
        )

    def test_insert_missing_column_raises_error(self) -> None:
        with self.assertRaises(MissingColumnError):
            self.db.insert_record("students", {"student_id": 1})

    def test_select_unknown_column_raises_error(self) -> None:
        self.db.insert_record("students", {"student_id": 1, "name": "Иван"})

        with self.assertRaises(UnknownColumnError):
            self.db.select_records("students", surname="Иванов")
