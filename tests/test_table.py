"""Tests for table CRUD operations and sorting."""

from __future__ import annotations

import unittest

from inmemory_db.exceptions import (
    DuplicateRecordError,
    RecordNotFoundError,
    ValidationError,
)
from inmemory_db.models import FieldDefinition, TableSchema
from inmemory_db.table import Table


class TableTests(unittest.TestCase):
    def setUp(self) -> None:
        schema = TableSchema(
            name="books",
            fields=[
                FieldDefinition(name="id", type_name="int"),
                FieldDefinition(name="title", type_name="str"),
                FieldDefinition(name="year", type_name="int"),
                FieldDefinition(name="available", type_name="bool"),
            ],
            primary_key="id",
        )
        self.table = Table(schema)
        self.table.insert(
            {"id": "2", "title": "Clean Code", "year": "2008", "available": "yes"}
        )
        self.table.insert(
            {"id": "1", "title": "Refactoring", "year": "1999", "available": "no"}
        )

    def test_insert_converts_types(self) -> None:
        inserted_record = self.table.insert(
            {"id": "3", "title": "DDD", "year": "2003", "available": "true"}
        )

        self.assertEqual(inserted_record["id"], 3)
        self.assertEqual(inserted_record["year"], 2003)
        self.assertTrue(inserted_record["available"])

    def test_insert_raises_for_duplicate_primary_key(self) -> None:
        with self.assertRaises(DuplicateRecordError):
            self.table.insert(
                {"id": "1", "title": "Other", "year": "2000", "available": "yes"}
            )

    def test_select_returns_filtered_records(self) -> None:
        records = self.table.select({"available": "yes"})

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["title"], "Clean Code")

    def test_select_supports_sorting(self) -> None:
        records = self.table.select(sort_by="year", descending=True)

        self.assertEqual([record["year"] for record in records], [2008, 1999])

    def test_select_raises_for_unknown_filter_field(self) -> None:
        with self.assertRaises(ValidationError):
            self.table.select({"unknown": "value"})

    def test_update_changes_existing_record(self) -> None:
        updated = self.table.update("2", {"title": "Clean Code 2", "available": "false"})

        self.assertEqual(updated["title"], "Clean Code 2")
        self.assertFalse(updated["available"])

    def test_update_raises_for_missing_record(self) -> None:
        with self.assertRaises(RecordNotFoundError):
            self.table.update("99", {"title": "Missing"})

    def test_delete_removes_record(self) -> None:
        deleted = self.table.delete("1")

        self.assertEqual(deleted["title"], "Refactoring")
        self.assertEqual(self.table.count(), 1)

    def test_delete_raises_for_missing_record(self) -> None:
        with self.assertRaises(RecordNotFoundError):
            self.table.delete("99")

    def test_sort_records_returns_ascending_order(self) -> None:
        records = self.table.sort_records("id")
        self.assertEqual([record["id"] for record in records], [1, 2])

    def test_sort_records_returns_descending_order(self) -> None:
        records = self.table.sort_records("title", descending=True)
        self.assertEqual([record["title"] for record in records], ["Refactoring", "Clean Code"])

    def test_sort_records_raises_for_unknown_field(self) -> None:
        with self.assertRaises(ValidationError):
            self.table.sort_records("missing")
