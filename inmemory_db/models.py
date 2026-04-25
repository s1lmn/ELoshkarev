from __future__ import annotations

from dataclasses import dataclass

from .exceptions import SchemaError, ValidationError

SUPPORTED_TYPES: dict[str, type] = {
    "bool": bool,
    "float": float,
    "int": int,
    "str": str,
}


def is_valid_identifier(name: str) -> bool:
    if not name:
        return False
    return name.replace("_", "").isalnum()


def parse_bool(raw_value: object) -> bool:
    if isinstance(raw_value, bool):
        return raw_value

    normalized = str(raw_value).strip().lower()
    truthy_values = {"1", "true", "yes", "y", "да", "д"}
    falsy_values = {"0", "false", "no", "n", "нет", "н"}

    if normalized in truthy_values:
        return True
    if normalized in falsy_values:
        return False

    raise ValidationError(
        "Некорректное булево значение. Используйте true/false, yes/no, 1/0."
    )


def convert_value(raw_value: object, type_name: str) -> object:
    if type_name not in SUPPORTED_TYPES:
        raise SchemaError(f"Неподдерживаемый тип данных: {type_name}")

    if type_name == "bool":
        return parse_bool(raw_value)
    if type_name == "str":
        return str(raw_value).strip()

    try:
        return SUPPORTED_TYPES[type_name](raw_value)
    except (TypeError, ValueError) as error:
        raise ValidationError(
            f"Не удалось преобразовать значение '{raw_value}' к типу {type_name}."
        ) from error


@dataclass(frozen=True)
class FieldDefinition:

    name: str
    type_name: str

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.name):
            raise SchemaError(
                "Имя поля должно содержать только буквы, цифры и символ '_'."
            )
        if self.type_name not in SUPPORTED_TYPES:
            available_types = ", ".join(sorted(SUPPORTED_TYPES))
            raise SchemaError(
                f"Тип поля '{self.type_name}' не поддерживается. "
                f"Доступные типы: {available_types}."
            )

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "type_name": self.type_name}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "FieldDefinition":
        return cls(name=data["name"], type_name=data["type_name"])


@dataclass(frozen=True)
class TableSchema:

    name: str
    fields: list[FieldDefinition]
    primary_key: str

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.name):
            raise SchemaError(
                "Имя таблицы должно содержать только буквы, цифры и символ '_'."
            )
        if not self.fields:
            raise SchemaError("Таблица должна содержать хотя бы одно поле.")

        field_names = [field.name for field in self.fields]
        if len(set(field_names)) != len(field_names):
            raise SchemaError("Имена полей в таблице должны быть уникальными.")
        if self.primary_key not in field_names:
            raise SchemaError("Первичный ключ должен совпадать с одним из полей таблицы.")

    @property
    def field_map(self) -> dict[str, FieldDefinition]:
        return {field.name: field for field in self.fields}

    @property
    def field_names(self) -> list[str]:
        return [field.name for field in self.fields]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "fields": [field.to_dict() for field in self.fields],
            "primary_key": self.primary_key,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "TableSchema":
        fields = [FieldDefinition.from_dict(item) for item in data["fields"]]
        return cls(name=data["name"], fields=fields, primary_key=data["primary_key"])
