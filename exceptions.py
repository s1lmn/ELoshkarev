"""Пользовательские исключения для проекта базы данных, работающей в оперативной памяти"""


class DatabaseError(Exception):
    """Базовое исключение для всех ошибок, связанных с базой данных"""


class ValidationError(DatabaseError):
    """Эта ошибка возникает, когда входные данные не соответствуют схеме таблицы"""


class SchemaError(DatabaseError):
    """Генерируется при недопустимой схеме таблицы"""


class TableNotFoundError(DatabaseError):
    """Генерируется, если запрошенная таблица не существует"""


class DuplicateRecordError(DatabaseError):
    """Эта ошибка возникает при попытке вставить запись с уже существующим первичным ключом"""


class RecordNotFoundError(DatabaseError):
    """Генерируется, если запрашиваемая запись не существует"""
