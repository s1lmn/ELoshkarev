class DatabaseError(Exception):
    pass


class TableAlreadyExistsError(DatabaseError):
    pass


class TableNotFoundError(DatabaseError):
    pass


class MissingColumnError(DatabaseError):
    pass


class UnknownColumnError(DatabaseError):
    pass


class InvalidStorageDataError(DatabaseError):
    pass
