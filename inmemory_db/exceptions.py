"""Custom exceptions for the in-memory database project."""


class DatabaseError(Exception):
    """Base exception for all database-related errors."""


class ValidationError(DatabaseError):
    """Raised when input data does not match table schema."""


class SchemaError(DatabaseError):
    """Raised when a table schema is invalid."""


class TableNotFoundError(DatabaseError):
    """Raised when the requested table does not exist."""


class DuplicateRecordError(DatabaseError):
    """Raised when trying to insert a record with an existing primary key."""


class RecordNotFoundError(DatabaseError):
    """Raised when the requested record does not exist."""
