from __future__ import annotations

from typing import Any

from .errors import MissingColumnError, UnknownColumnError


class Table:
    def __init__(
        self,
        columns: tuple[str, ...],
        records: list[dict[str, Any]] | None = None,
    ) -> None:
        self.columns = columns
        self.records: list[dict[str, Any]] = []

        if records is not None:
            for record in records:
                self.insert_record(record)

    def insert_record(self, record: dict[str, Any]) -> None:
        missing_columns = [column for column in self.columns if column not in record]
        if missing_columns:
            raise MissingColumnError(
                f"Отсутствует поле '{missing_columns[0]}' в записи."
            )

        extra_columns = [column for column in record if column not in self.columns]
        if extra_columns:
            raise UnknownColumnError(
                f"Поле '{extra_columns[0]}' не определено в структуре таблицы."
            )

        self.records.append(record.copy())

    def select_records(self, **filters: Any) -> list[dict[str, Any]]:
        unknown_filters = [key for key in filters if key not in self.columns]
        if unknown_filters:
            raise UnknownColumnError(
                f"Поле '{unknown_filters[0]}' не определено в структуре таблицы."
            )

        if not filters:
            return [record.copy() for record in self.records]

        result: list[dict[str, Any]] = []
        for record in self.records:
            if all(record.get(key) == value for key, value in filters.items()):
                result.append(record.copy())

        return result
