class UnimplementedException(Exception):
    """Exception raised when the requested operation isn't supported by the server."""

    pass


class AlreadyExistsException(Exception):
    """Exception raised when an entity already exist during a request to create a new entity."""

    pass


class UnavailableException(Exception):
    """Exception raised when a gRPC service is unavailable."""

    pass
