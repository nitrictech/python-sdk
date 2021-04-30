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
from abc import ABC
import grpc
from google.protobuf.struct_pb2 import Struct
from grpc._channel import _InactiveRpcError
from nitric.config import settings
from nitric.api.exception import (
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
            ex_message = "Failed to call {method}\n\tCode: {code}\n\tDetails: {details}".format(
                method=method_name, code=ire.code(), details=ire.details()
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
