"""Implementation of a single in-memory table."""

from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from .exceptions import DuplicateRecordError, RecordNotFoundError, ValidationError
from .models import TableSchema, convert_value

Record = dict[str, object]


class Table:
    """In-memory storage for one table."""

    def __init__(self, schema: TableSchema) -> None:
        self.schema = schema
        self._records: dict[object, Record] = {}

    def insert(self, record_data: dict[str, object]) -> Record:
        """Insert a new record after schema validation."""
        prepared_record = self._build_full_record(record_data)
        primary_key_value = prepared_record[self.schema.primary_key]

        if primary_key_value in self._records:
            raise DuplicateRecordError(
                f"Запись с ключом '{primary_key_value}' уже существует."
            )

        self._records[primary_key_value] = prepared_record
        return deepcopy(prepared_record)

    def select(
        self,
        filters: dict[str, object] | None = None,
        sort_by: str | None = None,
        descending: bool = False,
    ) -> list[Record]:
        """Return records that satisfy filters and optional sorting."""
        matched_records = self._filter_records(filters)
        if sort_by is not None:
            matched_records = self._sort_records(matched_records, sort_by, descending)
        return [deepcopy(record) for record in matched_records]

    def update(self, primary_key_value: object, updated_values: dict[str, object]) -> Record:
        """Update a record by primary key."""
        if not updated_values:
            raise ValidationError("Нужно передать хотя бы одно поле для обновления.")

        typed_primary_key = self._convert_primary_key(primary_key_value)
        if typed_primary_key not in self._records:
            raise RecordNotFoundError(
                f"Запись с ключом '{typed_primary_key}' не найдена."
            )

        if self.schema.primary_key in updated_values:
            raise ValidationError("Изменение первичного ключа не поддерживается.")

        record = deepcopy(self._records[typed_primary_key])
        field_map = self.schema.field_map

        for field_name, raw_value in updated_values.items():
            if field_name not in field_map:
                raise ValidationError(f"Поля '{field_name}' нет в таблице '{self.schema.name}'.")
            record[field_name] = convert_value(raw_value, field_map[field_name].type_name)

        self._records[typed_primary_key] = record
        return deepcopy(record)

    def delete(self, primary_key_value: object) -> Record:
        """Delete a record by primary key."""
        typed_primary_key = self._convert_primary_key(primary_key_value)
        if typed_primary_key not in self._records:
            raise RecordNotFoundError(
                f"Запись с ключом '{typed_primary_key}' не найдена."
            )

        deleted_record = self._records.pop(typed_primary_key)
        return deepcopy(deleted_record)

    def sort_records(self, field_name: str, descending: bool = False) -> list[Record]:
        """Return all records sorted by the selected field."""
        sorted_records = self._sort_records(self._records.values(), field_name, descending)
        return [deepcopy(record) for record in sorted_records]

    def count(self) -> int:
        """Return the number of records in the table."""
        return len(self._records)

    def _build_full_record(self, record_data: dict[str, object]) -> Record:
        """Validate and convert a new record according to the schema."""
        field_map = self.schema.field_map
        unknown_fields = set(record_data) - set(field_map)
        if unknown_fields:
            unknown_names = ", ".join(sorted(unknown_fields))
            raise ValidationError(f"Неизвестные поля: {unknown_names}.")

        missing_fields = [field_name for field_name in field_map if field_name not in record_data]
        if missing_fields:
            missing_names = ", ".join(missing_fields)
            raise ValidationError(f"Не заполнены обязательные поля: {missing_names}.")

        prepared_record: Record = {}
        for field_name, field in field_map.items():
            prepared_record[field_name] = convert_value(record_data[field_name], field.type_name)

        return prepared_record

    def _filter_records(self, filters: dict[str, object] | None = None) -> list[Record]:
        """Return internal records matching all filter values."""
        if not filters:
            return list(self._records.values())

        prepared_filters = self._prepare_filters(filters)
        matched_records = []

        for record in self._records.values():
            if all(record[field_name] == expected for field_name, expected in prepared_filters.items()):
                matched_records.append(record)

        return matched_records

    def _prepare_filters(self, filters: dict[str, object]) -> dict[str, object]:
        """Validate filter fields and convert filter values."""
        field_map = self.schema.field_map
        prepared_filters: dict[str, object] = {}

        for field_name, raw_value in filters.items():
            if field_name not in field_map:
                raise ValidationError(f"Фильтрация по полю '{field_name}' невозможна.")
            prepared_filters[field_name] = convert_value(raw_value, field_map[field_name].type_name)

        return prepared_filters

    def _sort_records(
        self,
        records: Iterable[Record],
        field_name: str,
        descending: bool,
    ) -> list[Record]:
        """Sort records by a single existing field."""
        if field_name not in self.schema.field_map:
            raise ValidationError(f"Сортировка по полю '{field_name}' невозможна.")

        return sorted(records, key=lambda record: record[field_name], reverse=descending)

    def _convert_primary_key(self, raw_value: object) -> object:
        """Convert primary key value to the type declared in the schema."""
        primary_key_type = self.schema.field_map[self.schema.primary_key].type_name
        return convert_value(raw_value, primary_key_type)
