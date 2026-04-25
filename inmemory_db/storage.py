from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from pathlib import Path

from .exceptions import StorageError


class TableStorage(ABC):

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def list_table_names(self) -> list[str]:
        """Возвращает имена всех сохраненных таблиц"""

    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """Проверяет, существует ли сохраненная таблица"""

    @abstractmethod
    def save_table(self, table_data: dict[str, object]) -> None:
        """Сохранение схемы таблиц, записей и индексов"""

    @abstractmethod
    def load_table(self, table_name: str) -> dict[str, object]:
        """Загрузка схемы таблицы, записей и индексов."""


class JsonTableStorage(TableStorage):

    def list_table_names(self) -> list[str]:
        return sorted(path.stem for path in self.data_dir.glob("*.json"))

    def table_exists(self, table_name: str) -> bool:
        return self._table_path(table_name).exists()

    def save_table(self, table_data: dict[str, object]) -> None:
        table_name = table_data["schema"]["name"]
        try:
            with self._table_path(table_name).open("w", encoding="utf-8") as file:
                json.dump(table_data, file, ensure_ascii=False, indent=2)
        except OSError as error:
            raise StorageError(f"Не удалось сохранить JSON-таблицу '{table_name}'.") from error

    def load_table(self, table_name: str) -> dict[str, object]:
        try:
            with self._table_path(table_name).open("r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError as error:
            raise StorageError(f"Файл таблицы '{table_name}' не найден.") from error
        except (OSError, json.JSONDecodeError) as error:
            raise StorageError(f"Не удалось загрузить JSON-таблицу '{table_name}'.") from error

    def _table_path(self, table_name: str) -> Path:
        return self.data_dir / f"{table_name}.json"


class CsvTableStorage(TableStorage):

    def list_table_names(self) -> list[str]:
        suffix = "__schema.csv"
        table_names = []
        for path in self.data_dir.glob(f"*{suffix}"):
            table_names.append(path.name[: -len(suffix)])
        return sorted(table_names)

    def table_exists(self, table_name: str) -> bool:
        return self._schema_path(table_name).exists()

    def save_table(self, table_data: dict[str, object]) -> None:
        schema = table_data["schema"]
        table_name = schema["name"]

        try:
            self._save_schema(table_name, schema)
            self._save_records(table_name, schema["fields"], table_data.get("records", []))
            self._save_indexes(table_name, table_data.get("indexes", []))
        except OSError as error:
            raise StorageError(f"Не удалось сохранить CSV-таблицу '{table_name}'.") from error

    def load_table(self, table_name: str) -> dict[str, object]:
        try:
            schema = self._load_schema(table_name)
            records = self._load_records(table_name, schema["fields"])
            indexes = self._load_indexes(table_name)
            return {"schema": schema, "records": records, "indexes": indexes}
        except FileNotFoundError as error:
            raise StorageError(f"Файлы таблицы '{table_name}' не найдены.") from error
        except (OSError, csv.Error, json.JSONDecodeError, KeyError) as error:
            raise StorageError(f"Не удалось загрузить CSV-таблицу '{table_name}'.") from error

    def _save_schema(self, table_name: str, schema: dict[str, object]) -> None:
        with self._schema_path(table_name).open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=("field_name", "type_name", "is_primary_key"),
            )
            writer.writeheader()
            for field in schema["fields"]:
                writer.writerow(
                    {
                        "field_name": field["name"],
                        "type_name": field["type_name"],
                        "is_primary_key": str(field["name"] == schema["primary_key"]),
                    }
                )

    def _save_records(
        self,
        table_name: str,
        fields: list[dict[str, str]],
        records: list[dict[str, object]],
    ) -> None:
        field_names = [field["name"] for field in fields]
        with self._records_path(table_name).open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=field_names)
            writer.writeheader()
            for record in records:
                writer.writerow(
                    {
                        field_name: json.dumps(record[field_name], ensure_ascii=False)
                        for field_name in field_names
                    }
                )

    def _save_indexes(self, table_name: str, indexes: list[list[str]]) -> None:
        with self._indexes_path(table_name).open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=("fields",))
            writer.writeheader()
            for index_fields in indexes:
                writer.writerow({"fields": ",".join(index_fields)})

    def _load_schema(self, table_name: str) -> dict[str, object]:
        fields: list[dict[str, str]] = []
        primary_key = None

        with self._schema_path(table_name).open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                fields.append(
                    {
                        "name": row["field_name"],
                        "type_name": row["type_name"],
                    }
                )
                if row["is_primary_key"].lower() == "true":
                    primary_key = row["field_name"]

        if primary_key is None:
            raise StorageError(f"В CSV-схеме таблицы '{table_name}' не указан первичный ключ.")

        return {"name": table_name, "fields": fields, "primary_key": primary_key}

    def _load_records(
        self,
        table_name: str,
        fields: list[dict[str, str]],
    ) -> list[dict[str, object]]:
        field_names = [field["name"] for field in fields]
        records: list[dict[str, object]] = []

        with self._records_path(table_name).open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                records.append(
                    {
                        field_name: json.loads(row[field_name])
                        for field_name in field_names
                    }
                )

        return records

    def _load_indexes(self, table_name: str) -> list[list[str]]:
        indexes_path = self._indexes_path(table_name)
        if not indexes_path.exists():
            return []

        indexes: list[list[str]] = []
        with indexes_path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                field_names = [field for field in row["fields"].split(",") if field]
                if field_names:
                    indexes.append(field_names)
        return indexes

    def _schema_path(self, table_name: str) -> Path:
        return self.data_dir / f"{table_name}__schema.csv"

    def _records_path(self, table_name: str) -> Path:
        return self.data_dir / f"{table_name}__records.csv"

    def _indexes_path(self, table_name: str) -> Path:
        return self.data_dir / f"{table_name}__indexes.csv"
