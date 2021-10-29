#
# Copyright (c) 2021 Nitric Technologies Pty Ltd.
#
# This file is part of Nitric Python 3 SDK.
# See https://github.com/nitrictech/python-sdk for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from grpclib import GRPCError


class NitricServiceException(Exception):
    """Base exception for all errors returned by Nitric API methods."""

    pass


class AbortedException(NitricServiceException):
    """The operation was aborted, typically due to a concurrency issue such as a transaction abort."""

    pass


class AlreadyExistsException(NitricServiceException):
    """The entity that a client attempted to create (e.g., file or directory) already exists."""

    pass


class CancelledException(NitricServiceException):
    """The operation was cancelled, typically by the caller."""

    pass


class DataLossException(NitricServiceException):
    """Unrecoverable data loss or corruption."""

    pass


class DeadlineExceededException(NitricServiceException):
    """The deadline expired before the operation could complete."""

    pass


class FailedPreconditionException(NitricServiceException):
    """
    The operation was rejected because the system is not in a state required for the operation's execution.

    For example, the document collection to be deleted is not empty.
    """

    pass


class InternalException(NitricServiceException):
    """Internal errors."""

    pass


class InvalidArgumentException(NitricServiceException):
    """
    The client specified an invalid argument.

    Note that this differs from FAILED_PRECONDITION. INVALID_ARGUMENT indicates arguments that are problematic
    regardless of the state of the system (e.g., a malformed file name).
    """

    pass


class OutOfRangeException(NitricServiceException):
    """
    The operation was attempted past the valid range.

    E.g. reading past the end of a file.
    """

    pass


class NotFoundException(NitricServiceException):
    """Some requested entity was not found."""

    pass


class PermissionDeniedException(NitricServiceException):
    """The caller does not have permission to execute the specified operation."""

    pass


class ResourceExhaustedException(NitricServiceException):
    """Some resource has been exhausted, perhaps a per-user quota, or perhaps the entire file system is out of space."""

    pass


class UnauthenticatedException(NitricServiceException):
    """The request does not have valid authentication credentials for the operation."""

    pass


class UnavailableException(NitricServiceException):
    """
    The service is currently unavailable.

    This is most likely a transient condition, which can be corrected by retrying with a backoff.
    """

    pass


class UnimplementedException(NitricServiceException):
    """
    The operation is not implemented or is not supported/enabled in this service.

    May appear when using an older version of the Membrane with a newer SDK.
    """

    pass


class UnknownException(NitricServiceException):
    """Unknown error."""

    pass


def exception_from_grpc_error(error: GRPCError):
    """Translate a gRPC error to a nitric api exception."""
    return exception_from_grpc_code(error.status.value, error.message)


def exception_from_grpc_code(code: int, message: str = None):
    """
    Return a new instance of the appropriate exception for the given status code.

    If an unknown or unexpected status code value is provided an UnknownException will be returned.
    """
    if code not in _exception_code_map:
        return UnknownException()

    return _exception_code_map[code](message)


# Map of gRPC status codes to the appropriate exception class.
_exception_code_map = {
    0: lambda message: Exception("Error returned with status 0, which is a success status"),
    1: CancelledException,
    2: UnknownException,
    3: InvalidArgumentException,
    4: DeadlineExceededException,
    5: NotFoundException,
    6: AlreadyExistsException,
    7: PermissionDeniedException,
    8: ResourceExhaustedException,
    9: FailedPreconditionException,
    10: AbortedException,
    11: OutOfRangeException,
    12: UnimplementedException,
    13: InternalException,
    14: UnavailableException,
    15: DataLossException,
    16: UnauthenticatedException,
}
