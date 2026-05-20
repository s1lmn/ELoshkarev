from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.db.backend.errors import (
    InvalidStorageDataError,
    StorageAccessError,
    TableNotFoundError,
)
from src.db.backend.file import FileDatabase


class TestFileDatabase(unittest.TestCase):
    def test_data_is_saved_between_instances(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first_db = FileDatabase(directory)
            first_db.create_table("students", ("student_id", "name"))
            first_db.insert_record("students", {"student_id": 1, "name": "Иван"})

            second_db = FileDatabase(directory)
            records = second_db.select_records("students")

            self.assertEqual(records, [{"student_id": 1, "name": "Иван"}])

    def test_select_with_filters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = FileDatabase(directory)
            db.create_table("students", ("student_id", "name"))
            db.insert_record("students", {"student_id": 1, "name": "Иван"})
            db.insert_record("students", {"student_id": 2, "name": "Мария"})

            records = db.select_records("students", name="Мария")

            self.assertEqual(records, [{"student_id": 2, "name": "Мария"}])

    def test_select_from_missing_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = FileDatabase(directory)

            with self.assertRaises(TableNotFoundError):
                db.select_records("students")

    def test_invalid_json_raises_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            table_path = Path(directory) / "students.json"
            table_path.write_text("{bad json", encoding="utf-8")

            db = FileDatabase(directory)
            with self.assertRaises(InvalidStorageDataError):
                db.select_records("students")

    def test_invalid_structure_raises_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            table_path = Path(directory) / "students.json"
            table_path.write_text(json.dumps({"records": []}), encoding="utf-8")

            db = FileDatabase(directory)
            with self.assertRaises(InvalidStorageDataError):
                db.select_records("students")

    def test_invalid_columns_raise_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            table_path = Path(directory) / "students.json"
            table_path.write_text(
                json.dumps({"columns": ["student_id", ""], "records": []}),
                encoding="utf-8",
            )

            db = FileDatabase(directory)
            with self.assertRaises(InvalidStorageDataError):
                db.select_records("students")

    def test_invalid_record_item_raises_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            table_path = Path(directory) / "students.json"
            table_path.write_text(
                json.dumps({"columns": ["student_id", "name"], "records": ["bad"]}),
                encoding="utf-8",
            )

            db = FileDatabase(directory)
            with self.assertRaises(InvalidStorageDataError):
                db.select_records("students")

    def test_init_storage_access_error(self) -> None:
        with patch("pathlib.Path.mkdir", side_effect=PermissionError):
            with self.assertRaises(StorageAccessError):
                FileDatabase("data")

    def test_load_storage_access_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            table_path = Path(directory) / "students.json"
            table_path.write_text(
                json.dumps({"columns": ["student_id", "name"], "records": []}),
                encoding="utf-8",
            )

            db = FileDatabase(directory)
            with patch("pathlib.Path.open", side_effect=PermissionError):
                with self.assertRaises(StorageAccessError):
                    db.select_records("students")

    def test_save_storage_access_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = FileDatabase(directory)
            db.create_table("students", ("student_id", "name"))

            with patch("pathlib.Path.open", side_effect=PermissionError):
                with self.assertRaises(StorageAccessError):
                    db.insert_record("students", {"student_id": 1, "name": "Иван"})
