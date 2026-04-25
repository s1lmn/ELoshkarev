"""Tests for database-level operations."""

from __future__ import annotations

import unittest

from inmemory_db.database import InMemoryDatabase
from inmemory_db.exceptions import SchemaError, TableNotFoundError
from inmemory_db.models import FieldDefinition


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = InMemoryDatabase()
        self.fields = [
            FieldDefinition(name="id", type_name="int"),
            FieldDefinition(name="title", type_name="str"),
            FieldDefinition(name="year", type_name="int"),
        ]

    def test_create_and_get_table(self) -> None:
        created_table = self.database.create_table("books", self.fields, "id")
        fetched_table = self.database.get_table("books")

        self.assertIs(created_table, fetched_table)
        self.assertEqual(fetched_table.schema.primary_key, "id")

    def test_create_table_raises_for_duplicate_name(self) -> None:
        self.database.create_table("books", self.fields, "id")

        with self.assertRaises(SchemaError):
            self.database.create_table("books", self.fields, "id")

    def test_get_table_raises_for_missing_table(self) -> None:
        with self.assertRaises(TableNotFoundError):
            self.database.get_table("missing")

    def test_list_tables_returns_all_created_tables(self) -> None:
        self.database.create_table("books", self.fields, "id")
        self.database.create_table(
            "authors",
            [
                FieldDefinition(name="id", type_name="int"),
                FieldDefinition(name="name", type_name="str"),
            ],
            "id",
        )

        table_names = sorted(table.schema.name for table in self.database.list_tables())
        self.assertEqual(table_names, ["authors", "books"])
