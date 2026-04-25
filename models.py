from __future__ import annotations

from dataclasses import dataclass

from .exceptions import SchemaError, ValidationError

SUPPORTED_TYPES: dict[str, type] = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
}


def is_valid_identifier(name: str) -> bool:
    if not name:
        return False
    return name.replace("_", "").isalnum()


def parse_bool(raw_value: object) -> bool:
    if isinstance(raw_value, bool):
        return raw_value

    normalized = str(raw_value).strip().lower()
    truthy_values = {"true", "1", "yes", "y", "да", "д"}
    falsy_values = {"false", "0", "no", "n", "нет", "н"}

    if normalized in truthy_values:
        return True
    if normalized in falsy_values:
        return False

    raise ValidationError(
        "Некорректное булево значение. Используйте true/false, yes/no, 1/0."
    )


def convert_value(raw_value: object, type_name: str) -> object:
    """Convert a raw value to the type declared in the schema."""
    if type_name not in SUPPORTED_TYPES:
        raise SchemaError(f"Неподдерживаемый тип данных: {type_name}")

    if type_name == "str":
        return str(raw_value).strip()
    if type_name == "bool":
        return parse_bool(raw_value)

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
                "Имя поля должно содержать только буквы, цифры и символ '_' ."
            )
        if self.type_name not in SUPPORTED_TYPES:
            allowed_types = ", ".join(sorted(SUPPORTED_TYPES))
            raise SchemaError(
                f"Тип поля '{self.type_name}' не поддерживается. "
                f"Доступные типы: {allowed_types}."
            )


@dataclass(frozen=True)
class TableSchema:

    name: str
    fields: list[FieldDefinition]
    primary_key: str

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.name):
            raise SchemaError(
                "Имя таблицы должно содержать только буквы, цифры и символ '_' ."
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
