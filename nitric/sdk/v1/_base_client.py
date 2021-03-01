from abc import ABC
import grpc
from google.protobuf.struct_pb2 import Struct
from grpc._channel import _InactiveRpcError
from nitric.config import settings
from nitric.sdk.v1.exception import (
    UnimplementedException,
    AlreadyExistsException,
    UnavailableException,
)


class BaseClient(ABC):
    """Abstract base class for GRPC based Nitric client classes."""

    _stub = None

    def __init__(self):
        """Construct a base nitric gRPC client."""
        self._channel = grpc.insecure_channel(settings.SERVICE_BIND)

    def _get_method_function(self, method):
        return getattr(self._stub, method)

    def _exec(self, method: str, request: object = None):
        """
        Execute a gRPC request.

        :param method: gRPC method to execute.
        :param request: payload for the request.
        :return: gRPC reply class, based on method.
        """
        if request is None:
            request = Struct()
        grpc_method = self._get_method_function(method)
        try:
            response = grpc_method(request)
        except _InactiveRpcError as ire:
            method_name = str(grpc_method._method, "utf-8").replace("/", "", 1)
            ex_message = (
                "Failed to call {method}\n\tCode: {code}\n\tDetails: {details}".format(
                    method=method_name, code=ire.code(), details=ire.details()
                )
            )

            # handle specific status codes
            if ire.code() == grpc.StatusCode.UNIMPLEMENTED:
                raise UnimplementedException(ex_message) from None
            elif ire.code() == grpc.StatusCode.ALREADY_EXISTS:
                raise AlreadyExistsException(ex_message) from None
            elif ire.code() == grpc.StatusCode.UNAVAILABLE:
                raise UnavailableException(ex_message) from None

            raise Exception(ex_message) from None

        return response
