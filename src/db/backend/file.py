from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .database import Database
from .errors import (
    InvalidStorageDataError,
    MissingColumnError,
    StorageAccessError,
    TableNotFoundError,
    UnknownColumnError,
)
from .table import Table


class FileDatabase(Database):
    def __init__(self, directory: str = "data") -> None:
        self.directory = Path(directory)
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise StorageAccessError(
                f"Не удалось подготовить каталог хранилища: {self.directory}."
            ) from error

    def _table_exists(self, table_name: str) -> bool:
        return self._get_table_path(table_name).exists()

    def _load_table(self, table_name: str) -> Table:
        table_path = self._get_table_path(table_name)
        if not table_path.exists():
            raise TableNotFoundError(f"Таблица '{table_name}' не существует.")

        try:
            with table_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise InvalidStorageDataError(
                "Файл таблицы содержит некорректный JSON."
            ) from error
        except OSError as error:
            raise StorageAccessError(
                f"Не удалось прочитать файл таблицы: {table_path}."
            ) from error

        return self._deserialize_table(data)

    def _save_table(self, table_name: str, table: Table) -> None:
        table_path = self._get_table_path(table_name)
        try:
            with table_path.open("w", encoding="utf-8") as file:
                json.dump(
                    self._serialize_table(table),
                    file,
                    ensure_ascii=False,
                    indent=2,
                )
        except OSError as error:
            raise StorageAccessError(
                f"Не удалось записать файл таблицы: {table_path}."
            ) from error

    def _get_table_path(self, table_name: str) -> Path:
        return self.directory / f"{table_name}.json"

    @staticmethod
    def _serialize_table(table: Table) -> dict[str, Any]:
        return {
            "columns": list(table.columns),
            "records": [record.copy() for record in table.records],
        }

    @staticmethod
    def _deserialize_table(data: dict[str, Any]) -> Table:
        if not isinstance(data, dict):
            raise InvalidStorageDataError(
                "Файл таблицы имеет некорректную структуру."
            )

        if "columns" not in data or "records" not in data:
            raise InvalidStorageDataError(
                "Файл таблицы имеет некорректную структуру."
            )

        columns_data = data["columns"]
        records_data = data["records"]

        if not isinstance(columns_data, list) or not columns_data:
            raise InvalidStorageDataError(
                "Поле columns должно быть непустым списком."
            )
        if any(not isinstance(column, str) or not column.strip() for column in columns_data):
            raise InvalidStorageDataError(
                "Все имена колонок должны быть непустыми строками."
            )
        if len(set(columns_data)) != len(columns_data):
            raise InvalidStorageDataError("Имена колонок должны быть уникальными.")

        if not isinstance(records_data, list):
            raise InvalidStorageDataError("Поле records должно быть списком.")
        if any(not isinstance(record, dict) for record in records_data):
            raise InvalidStorageDataError(
                "Каждая запись в records должна быть словарём."
            )

        columns = tuple(columns_data)

        try:
            return Table(columns, records_data)
        except (MissingColumnError, UnknownColumnError) as error:
            raise InvalidStorageDataError(
                "Файл таблицы содержит некорректные записи."
            ) from error
