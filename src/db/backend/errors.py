class StudentTableError(Exception):
    pass


class InvalidAgeError(StudentTableError):
    pass


class DuplicateIDError(StudentTableError):
    pass
