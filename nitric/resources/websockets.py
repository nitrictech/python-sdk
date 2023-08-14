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
from __future__ import annotations
from typing import Literal, Callable
from nitric.faas import (
    FunctionServer,
    WebsocketWorkerOptions,
    WebsocketHandler,
)
from nitric.api.websocket import Websocket as WebsocketClient
from nitric.application import Nitric
from nitric.resources.resource import Resource as BaseResource
from nitric.proto.nitric.resource.v1 import Resource, Action, ResourceType, ResourceDeclareRequest, PolicyResource
from grpclib import GRPCError
from nitric.exception import exception_from_grpc_error

WebsocketEventType = Literal["connect", "disconnect", "message"]


def _to_resource(b: Websocket) -> Resource:
    return Resource(name=b.name, type=ResourceType.Websocket)


class Websocket(BaseResource):
    """A Websocket API."""

    app: Nitric
    _websocket: WebsocketClient
    name: str

    def __init__(self, name: str):
        """Construct a new Websocket API."""
        super().__init__()

        self._websocket = WebsocketClient()
        self.name = name

    async def _register(self) -> None:
        try:
            resource = _to_resource(self)
            default_principle = Resource(type=ResourceType.Function)

            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    resource=resource,
                )
            )

            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    resource=Resource(type=ResourceType.Policy),
                    policy=PolicyResource(
                        actions=[Action.WebsocketManage], principals=[default_principle], resources=[resource]
                    ),
                )
            )

        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    async def send(
        self,
        connection_id: str,
        data: bytes,
    ) -> None:
        """Send a message to a connection on this socket."""
        await self._websocket.send(socket=self.name, connection_id=connection_id, data=data)

    def on(self, event_type: WebsocketEventType) -> Callable[[WebsocketHandler], None]:
        """Create and return a worker decorator for this socket."""

        def decorator(func: WebsocketHandler) -> None:
            self._server = FunctionServer(
                WebsocketWorkerOptions(
                    socket_name=self.name,
                    event_type=event_type,
                )
            )
            self._server.websocket(func)
            return Nitric._register_worker(self._server)  # type: ignore

        return decorator


def websocket(name: str) -> Websocket:
    """
    Create and registers a websocket.

    If a websocket has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Websocket, name)  # type: ignore
