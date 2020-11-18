from abc import ABC, abstractmethod
import grpc
from google.protobuf.struct_pb2 import Struct
from grpc._channel import _InactiveRpcError

from nitric.config import settings
from nitric.sdk.v1.exception import *

class BaseClient(ABC):

    _stub = None

    def __init__(self):
        ambassador_bind = f"{settings.AMBASSADOR_ADDRESS}:{settings.AMBASSADOR_PORT}"
        # TODO: handle other channel types
        self._channel = grpc.insecure_channel(ambassador_bind)

    def _exec(self, method: str, request: object = Struct()):
        grpc_method = getattr(self._stub, method)
        try:
            response = grpc_method(request)
        except _InactiveRpcError as ire:
            method_name = str(grpc_method._method, 'utf-8').replace("/", "", 1)
            ex_message = "Failed to call {}\n\tCode: {}\n\tDetails: {}".format(method_name, ire.code(), ire.details())

            # handle specific status codes
            if ire.code() == grpc.StatusCode.UNIMPLEMENTED:
                raise UnimplementedException(ex_message) from None
            elif ire.code() == grpc.StatusCode.ALREADY_EXISTS:
                raise AlreadyExistsException(ex_message) from None

            raise Exception(ex_message) from None

        return response
