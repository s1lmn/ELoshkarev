from __future__ import annotations

import unittest

from src.db.backend.errors import MissingColumnError, UnknownColumnError
from src.db.backend.table import Table


class TestTable(unittest.TestCase):
    def test_insert_record(self) -> None:
        table = Table(("id", "name"))
        table.insert_record({"id": 1, "name": "Иван"})

        self.assertEqual(table.records, [{"id": 1, "name": "Иван"}])

    def test_insert_record_with_unknown_column(self) -> None:
        table = Table(("id", "name"))

        with self.assertRaises(UnknownColumnError):
            table.insert_record({"id": 1, "name": "Иван", "age": 20})

    def test_insert_record_with_missing_column(self) -> None:
        table = Table(("id", "name"))

        with self.assertRaises(MissingColumnError):
            table.insert_record({"id": 1})

    def test_select_records_without_filters(self) -> None:
        table = Table(("id", "name"))
        table.insert_record({"id": 1, "name": "Иван"})

        self.assertEqual(table.select_records(), [{"id": 1, "name": "Иван"}])
