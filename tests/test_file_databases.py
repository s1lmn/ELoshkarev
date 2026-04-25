"""Тесты для баз данных, использующих файлы JSON и CSV."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from inmemory_db.database import CsvFileDatabase, JsonFileDatabase
from inmemory_db.exceptions import StorageError
from inmemory_db.models import FieldDefinition


class FileDatabaseMixin:

    database_class = None

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.fields = [
            FieldDefinition(name="id", type_name="int"),
            FieldDefinition(name="title", type_name="str"),
            FieldDefinition(name="author", type_name="str"),
        ]

    def create_database(self):
        return self.database_class(self.temporary_directory.name)

    def test_table_and_records_are_persisted_between_instances(self) -> None:
        database = self.create_database()
        table = database.create_table("books", self.fields, "id")
        table.insert({"id": "1", "title": "DDD", "author": "Eric Evans"})
        table.create_index("author")

        reloaded_database = self.create_database()
        reloaded_table = reloaded_database.get_table("books")

        self.assertEqual(reloaded_table.select({"author": "Eric Evans"})[0]["title"], "DDD")
        self.assertEqual(reloaded_table.list_indexes(), [("author",)])

    def test_updates_and_deletes_are_persisted(self) -> None:
        database = self.create_database()
        table = database.create_table("books", self.fields, "id")
        table.insert({"id": "1", "title": "Initial", "author": "Author"})
        table.update("1", {"title": "Updated"})
        table.delete("1")

        reloaded_database = self.create_database()
        reloaded_table = reloaded_database.get_table("books")
        self.assertEqual(reloaded_table.select(), [])

    def test_list_tables_loads_persisted_table_names(self) -> None:
        database = self.create_database()
        database.create_table("books", self.fields, "id")

        reloaded_database = self.create_database()
        table_names = [table.schema.name for table in reloaded_database.list_tables()]
        self.assertEqual(table_names, ["books"])


class JsonFileDatabaseTests(FileDatabaseMixin, unittest.TestCase):
    database_class = JsonFileDatabase

    def test_invalid_json_raises_storage_error(self) -> None:
        bad_file = Path(self.temporary_directory.name) / "books.json"
        bad_file.write_text("{bad json", encoding="utf-8")

        database = self.create_database()
        with self.assertRaises(StorageError):
            database.get_table("books")


class CsvFileDatabaseTests(FileDatabaseMixin, unittest.TestCase):
    database_class = CsvFileDatabase

    def test_invalid_csv_schema_raises_storage_error(self) -> None:
        schema_file = Path(self.temporary_directory.name) / "books__schema.csv"
        records_file = Path(self.temporary_directory.name) / "books__records.csv"
        schema_file.write_text("field_name,type_name,is_primary_key\nid,int,false\n", encoding="utf-8")
        records_file.write_text("id\n1\n", encoding="utf-8")

        database = self.create_database()
        with self.assertRaises(StorageError):
            database.get_table("books")
