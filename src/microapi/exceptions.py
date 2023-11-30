class ApiError(Exception):
    """
    A generic base exception for all exceptions to inherit from.

    This makes handling all exceptions raised by this library easier to catch.
    """

    pass


class DataValidationError(ApiError):
    """
    An exception raised when invalid data is provided by the user.
    """

    pass


class InvalidFieldError(ApiError):
    """
    Raised by deserialization when unexpected (non-Model) data is provided by
    the user.
    """

    pass
