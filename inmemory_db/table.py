from __future__ import annotations

from copy import deepcopy
from typing import Callable, Iterable, Sequence

from .exceptions import DuplicateRecordError, RecordNotFoundError, ValidationError
from .models import TableSchema, convert_value

Record = dict[str, object]
IndexDefinition = tuple[str, ...]
IndexBucket = dict[tuple[object, ...], set[object]]


class Table:

    def __init__(
        self,
        schema: TableSchema,
        records: Sequence[Record] | None = None,
        indexed_fields: Sequence[Sequence[str]] | None = None,
        save_callback: Callable[[], None] | None = None,
    ) -> None:
        self.schema = schema
        self._records: dict[object, Record] = {}
        self._indexes: dict[IndexDefinition, IndexBucket] = {}
        self._save_callback = save_callback
        self._last_query_used_index = False

        for record in records or []:
            prepared_record = self._build_full_record(record)
            primary_key_value = prepared_record[self.schema.primary_key]
            self._records[primary_key_value] = prepared_record

        for index_fields in indexed_fields or []:
            normalized_fields = self._normalize_index_fields(index_fields)
            self._indexes[normalized_fields] = {}

        self._rebuild_all_indexes()

    def insert(self, record_data: dict[str, object]) -> Record:
        prepared_record = self._build_full_record(record_data)
        primary_key_value = prepared_record[self.schema.primary_key]

        if primary_key_value in self._records:
            raise DuplicateRecordError(
                f"Запись с ключом '{primary_key_value}' уже существует."
            )

        self._records[primary_key_value] = prepared_record
        self._after_data_changed()
        return deepcopy(prepared_record)

    def select(
        self,
        filters: dict[str, object] | None = None,
        sort_by: str | None = None,
        descending: bool = False,
    ) -> list[Record]:
        matched_records = self._filter_records(filters)
        if sort_by is not None:
            matched_records = self._sort_records(matched_records, sort_by, descending)
        return [deepcopy(record) for record in matched_records]

    def update(self, primary_key_value: object, updated_values: dict[str, object]) -> Record:
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
        self._after_data_changed()
        return deepcopy(record)

    def delete(self, primary_key_value: object) -> Record:
        typed_primary_key = self._convert_primary_key(primary_key_value)
        if typed_primary_key not in self._records:
            raise RecordNotFoundError(
                f"Запись с ключом '{typed_primary_key}' не найдена."
            )

        deleted_record = self._records.pop(typed_primary_key)
        self._after_data_changed()
        return deepcopy(deleted_record)

    def sort_records(self, field_name: str, descending: bool = False) -> list[Record]:
        sorted_records = self._sort_records(self._records.values(), field_name, descending)
        return [deepcopy(record) for record in sorted_records]

    def create_index(self, field_names: str | Sequence[str]) -> IndexDefinition:
        normalized_fields = self._normalize_index_fields(field_names)
        if normalized_fields not in self._indexes:
            self._indexes[normalized_fields] = {}
            self._rebuild_index(normalized_fields)
            self._persist()
        return normalized_fields

    def list_indexes(self) -> list[IndexDefinition]:
        return sorted(self._indexes)

    @property
    def last_query_used_index(self) -> bool:
        return self._last_query_used_index

    def count(self) -> int:
        return len(self._records)

    def export_records(self) -> list[Record]:
        return [deepcopy(record) for record in self._records.values()]

    def _build_full_record(self, record_data: dict[str, object]) -> Record:
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
        if not filters:
            self._last_query_used_index = False
            return list(self._records.values())

        prepared_filters = self._prepare_filters(filters)
        candidate_primary_keys = self._find_index_candidates(prepared_filters)
        self._last_query_used_index = candidate_primary_keys is not None

        if candidate_primary_keys is None:
            candidate_records = list(self._records.values())
        else:
            candidate_records = [
                self._records[primary_key]
                for primary_key in candidate_primary_keys
                if primary_key in self._records
            ]

        return self._scan_records(candidate_records, prepared_filters)

    def _prepare_filters(self, filters: dict[str, object]) -> dict[str, object]:
        field_map = self.schema.field_map
        prepared_filters: dict[str, object] = {}

        for field_name, raw_value in filters.items():
            if field_name not in field_map:
                raise ValidationError(f"Фильтрация по полю '{field_name}' невозможна.")
            prepared_filters[field_name] = convert_value(raw_value, field_map[field_name].type_name)

        return prepared_filters

    def _normalize_index_fields(
        self,
        field_names: str | Sequence[str],
    ) -> IndexDefinition:
        if isinstance(field_names, str):
            normalized_fields = (field_names,)
        else:
            normalized_fields = tuple(field_names)

        if not normalized_fields:
            raise ValidationError("Нужно указать хотя бы одно поле для индекса.")
        if len(set(normalized_fields)) != len(normalized_fields):
            raise ValidationError("Поля в индексе должны быть уникальными.")

        for field_name in normalized_fields:
            if field_name not in self.schema.field_map:
                raise ValidationError(f"Поля '{field_name}' нет в таблице '{self.schema.name}'.")

        return normalized_fields

    def _find_index_candidates(
        self,
        prepared_filters: dict[str, object],
    ) -> set[object] | None:
        matching_indexes = [
            index_fields
            for index_fields in self._indexes
            if all(field_name in prepared_filters for field_name in index_fields)
        ]
        if not matching_indexes:
            return None

        best_index = max(matching_indexes, key=len)
        lookup_key = tuple(prepared_filters[field_name] for field_name in best_index)
        return set(self._indexes[best_index].get(lookup_key, set()))

    def _scan_records(
        self,
        records: Iterable[Record],
        prepared_filters: dict[str, object],
    ) -> list[Record]:
        matched_records = []
        for record in records:
            if all(record[field_name] == expected for field_name, expected in prepared_filters.items()):
                matched_records.append(record)
        return matched_records

    def _rebuild_all_indexes(self) -> None:
        for index_fields in list(self._indexes):
            self._rebuild_index(index_fields)

    def _rebuild_index(self, index_fields: IndexDefinition) -> None:
        index_bucket: IndexBucket = {}
        primary_key_name = self.schema.primary_key

        for record in self._records.values():
            lookup_key = tuple(record[field_name] for field_name in index_fields)
            primary_key_value = record[primary_key_name]
            index_bucket.setdefault(lookup_key, set()).add(primary_key_value)

        self._indexes[index_fields] = index_bucket

    def _after_data_changed(self) -> None:
        self._rebuild_all_indexes()
        self._persist()

    def _persist(self) -> None:
        if self._save_callback is not None:
            self._save_callback()

    def _sort_records(
        self,
        records: Iterable[Record],
        field_name: str,
        descending: bool,
    ) -> list[Record]:
        if field_name not in self.schema.field_map:
            raise ValidationError(f"Сортировка по полю '{field_name}' невозможна.")

        return sorted(records, key=lambda record: record[field_name], reverse=descending)

    def _convert_primary_key(self, raw_value: object) -> object:
        primary_key_type = self.schema.field_map[self.schema.primary_key].type_name
        return convert_value(raw_value, primary_key_type)
