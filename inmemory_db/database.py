from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .exceptions import SchemaError, TableNotFoundError
from .models import FieldDefinition, TableSchema
from .storage import CsvTableStorage, JsonTableStorage, TableStorage
from .table import Table


class BaseDatabase(ABC):

    def __init__(self) -> None:
        self._tables: dict[str, Table] = {}

    def create_table(
        self,
        table_name: str,
        fields: list[FieldDefinition],
        primary_key: str,
    ) -> Table:
        if self._table_exists(table_name):
            raise SchemaError(f"Таблица '{table_name}' уже существует.")

        schema = TableSchema(name=table_name, fields=fields, primary_key=primary_key)
        table = self._build_table(schema)
        self._tables[table_name] = table
        self._after_table_created(table_name)
        return table

    def get_table(self, table_name: str) -> Table:
        if table_name not in self._tables:
            if not self._stored_table_exists(table_name):
                raise TableNotFoundError(f"Таблица '{table_name}' не найдена.")
            self._tables[table_name] = self._load_table(table_name)
        return self._tables[table_name]

    def list_tables(self) -> list[Table]:
        for table_name in self._stored_table_names():
            if table_name not in self._tables:
                self._tables[table_name] = self._load_table(table_name)
        return [self._tables[name] for name in sorted(self._tables)]

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Удобочитаемое название бэкэнда."""

    def _table_exists(self, table_name: str) -> bool:
        return table_name in self._tables or self._stored_table_exists(table_name)

    @abstractmethod
    def _build_table(
        self,
        schema: TableSchema,
        records: list[dict[str, object]] | None = None,
        indexes: list[list[str]] | None = None,
    ) -> Table:
        """Создайте экземпляр таблицы для этого бэкэнда."""

    def _after_table_created(self, table_name: str) -> None:
        """Хук для сохранения данных в только что созданной таблице."""

    def _stored_table_exists(self, table_name: str) -> bool:
        return False

    def _stored_table_names(self) -> list[str]:
        return []

    def _load_table(self, table_name: str) -> Table:
        raise TableNotFoundError(f"Таблица '{table_name}' не найдена.")


class InMemoryDatabase(BaseDatabase):

    backend_name = "memory"

    def _build_table(
        self,
        schema: TableSchema,
        records: list[dict[str, object]] | None = None,
        indexes: list[list[str]] | None = None,
    ) -> Table:
        return Table(schema=schema, records=records, indexed_fields=indexes)


class FileDatabase(BaseDatabase):

    def __init__(self, storage: TableStorage) -> None:
        super().__init__()
        self.storage = storage

    def _build_table(
        self,
        schema: TableSchema,
        records: list[dict[str, object]] | None = None,
        indexes: list[list[str]] | None = None,
    ) -> Table:
        return Table(
            schema=schema,
            records=records,
            indexed_fields=indexes,
            save_callback=lambda table_name=schema.name: self._save_table(table_name),
        )

    def _after_table_created(self, table_name: str) -> None:
        self._save_table(table_name)

    def _stored_table_exists(self, table_name: str) -> bool:
        return self.storage.table_exists(table_name)

    def _stored_table_names(self) -> list[str]:
        return self.storage.list_table_names()

    def _load_table(self, table_name: str) -> Table:
        table_data = self.storage.load_table(table_name)
        schema = TableSchema.from_dict(table_data["schema"])
        return self._build_table(
            schema=schema,
            records=table_data.get("records", []),
            indexes=table_data.get("indexes", []),
        )

    def _save_table(self, table_name: str) -> None:
        table = self._tables[table_name]
        self.storage.save_table(
            {
                "schema": table.schema.to_dict(),
                "records": table.export_records(),
                "indexes": [list(index_fields) for index_fields in table.list_indexes()],
            }
        )


class JsonFileDatabase(FileDatabase):

    backend_name = "json"

    def __init__(self, data_dir: str | Path) -> None:
        super().__init__(JsonTableStorage(data_dir))


class CsvFileDatabase(FileDatabase):

    backend_name = "csv"

    def __init__(self, data_dir: str | Path) -> None:
        super().__init__(CsvTableStorage(data_dir))
