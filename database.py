from __future__ import annotations

from .exceptions import SchemaError, TableNotFoundError
from .models import FieldDefinition, TableSchema
from .table import Table


class InMemoryDatabase:

    def __init__(self) -> None:
        self._tables: dict[str, Table] = {}

    def create_table(
        self,
        table_name: str,
        fields: list[FieldDefinition],
        primary_key: str,
    ) -> Table:
        if table_name in self._tables:
            raise SchemaError(f"Таблица '{table_name}' уже существует.")

        schema = TableSchema(name=table_name, fields=fields, primary_key=primary_key)
        table = Table(schema)
        self._tables[table_name] = table
        return table

    def get_table(self, table_name: str) -> Table:
        try:
            return self._tables[table_name]
        except KeyError as error:
            raise TableNotFoundError(f"Таблица '{table_name}' не найдена.") from error

    def list_tables(self) -> list[Table]:
        return list(self._tables.values())
