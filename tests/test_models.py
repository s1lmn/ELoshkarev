from __future__ import annotations

import unittest

from inmemory_db.exceptions import SchemaError, ValidationError
from inmemory_db.models import FieldDefinition, TableSchema, convert_value, parse_bool


class ModelHelpersTests(unittest.TestCase):
    def test_parse_bool_supports_multiple_literals(self) -> None:
        self.assertTrue(parse_bool("yes"))
        self.assertTrue(parse_bool("Да"))
        self.assertFalse(parse_bool("0"))
        self.assertFalse(parse_bool("нет"))

    def test_parse_bool_raises_for_invalid_literal(self) -> None:
        with self.assertRaises(ValidationError):
            parse_bool("maybe")

    def test_convert_value_converts_numeric_types(self) -> None:
        self.assertEqual(convert_value("12", "int"), 12)
        self.assertEqual(convert_value("12.5", "float"), 12.5)
        self.assertEqual(convert_value(" book ", "str"), "book")

    def test_convert_value_raises_for_invalid_type(self) -> None:
        with self.assertRaises(SchemaError):
            convert_value("value", "list")

    def test_field_definition_rejects_invalid_field_name(self) -> None:
        with self.assertRaises(SchemaError):
            FieldDefinition(name="bad field", type_name="str")

    def test_table_schema_requires_unique_fields(self) -> None:
        fields = [
            FieldDefinition(name="id", type_name="int"),
            FieldDefinition(name="id", type_name="str"),
        ]

        with self.assertRaises(SchemaError):
            TableSchema(name="books", fields=fields, primary_key="id")

    def test_table_schema_requires_existing_primary_key(self) -> None:
        fields = [
            FieldDefinition(name="id", type_name="int"),
            FieldDefinition(name="title", type_name="str"),
        ]

        with self.assertRaises(SchemaError):
            TableSchema(name="books", fields=fields, primary_key="missing")

    def test_schema_serialization_roundtrip(self) -> None:
        schema = TableSchema(
            name="books",
            fields=[
                FieldDefinition(name="id", type_name="int"),
                FieldDefinition(name="title", type_name="str"),
            ],
            primary_key="id",
        )

        restored_schema = TableSchema.from_dict(schema.to_dict())
        self.assertEqual(restored_schema, schema)
