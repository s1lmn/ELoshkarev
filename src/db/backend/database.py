from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .errors import TableAlreadyExistsError
from .table import Table


class Database(ABC):
    def create_table(self, table_name: str, columns: tuple[str, ...]) -> None:
        if self._table_exists(table_name):
            raise TableAlreadyExistsError(f"Таблица '{table_name}' уже существует.")

        self._save_table(table_name, Table(columns))

    def get_columns(self, table_name: str) -> tuple[str, ...]:
        table = self._load_table(table_name)
        return table.columns

    def insert_record(self, table_name: str, record: dict[str, Any]) -> None:
        table = self._load_table(table_name)
        table.insert_record(record)
        self._save_table(table_name, table)

    def select_records(
        self,
        table_name: str,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        table = self._load_table(table_name)
        return table.select_records(**filters)

    @abstractmethod
    def _table_exists(self, table_name: str) -> bool:
        pass

    @abstractmethod
    def _load_table(self, table_name: str) -> Table:
        pass

    @abstractmethod
    def _save_table(self, table_name: str, table: Table) -> None:
        pass
