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

import logging
from typing import Callable, Literal

import betterproto
import grpclib
from grpclib import GRPCError
from grpclib.client import Channel

from nitric.application import Nitric
from nitric.bidi import AsyncNotifierList
from nitric.context import (
    FunctionServer,
    Record,
    WebsocketConnectionRequest,
    WebsocketConnectionResponse,
    WebsocketContext,
    WebsocketHandler,
    WebsocketMessageRequest,
    WebsocketRequest,
)
from nitric.exception import exception_from_grpc_error
from nitric.proto.resources.v1 import Action, PolicyResource, ResourceDeclareRequest, ResourceIdentifier, ResourceType
from nitric.proto.websockets.v1 import ClientMessage, RegistrationRequest
from nitric.proto.websockets.v1 import WebsocketConnectionResponse as ProtoWebsocketConnectionResponse
from nitric.proto.websockets.v1 import (
    WebsocketEventRequest,
    WebsocketEventResponse,
    WebsocketEventType,
    WebsocketHandlerStub,
    WebsocketSendRequest,
    WebsocketStub,
)
from nitric.resources.resource import Resource as BaseResource
from nitric.channel import ChannelManager


class WebsocketRef:
    """A reference to a deployed websocket, used to interact with the websocket at runtime."""

    def __init__(self) -> None:
        """Construct a Nitric Websocket Client."""
        self._channel: Channel = ChannelManager.get_channel()
        self._websocket_stub = WebsocketStub(channel=self._channel)

    async def send(self, socket: str, connection_id: str, data: bytes):
        """Send data to a connection on a socket."""
        try:
            await self._websocket_stub.send_message(
                websocket_send_request=WebsocketSendRequest(socket_name=socket, connection_id=connection_id, data=data)
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err


def _to_grpc_event_type(event_type: Literal["connect", "disconnect", "message"]) -> WebsocketEventType:
    if event_type == "connect":
        return WebsocketEventType.Connect
    elif event_type == "disconnect":
        return WebsocketEventType.Disconnect
    elif event_type == "message":
        return WebsocketEventType.Message
    else:
        raise ValueError(f"Event type {event_type} is unsupported")


def _to_resource(b: Websocket) -> ResourceIdentifier:
    return ResourceIdentifier(name=b.name, type=ResourceType.Websocket)


class Websocket(BaseResource):
    """A Websocket API."""

    app: Nitric
    _websocket: WebsocketRef
    name: str

    def __init__(self, name: str):
        """Construct a new Websocket API."""
        super().__init__(name)
        self._websocket = WebsocketRef()

    async def _register(self) -> None:
        try:
            resource = _to_resource(self)
            default_principle = ResourceIdentifier(type=ResourceType.Service)

            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    id=resource,
                )
            )

            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    id=ResourceIdentifier(type=ResourceType.Policy),
                    policy=PolicyResource(
                        actions=[Action.WebsocketManage], principals=[default_principle], resources=[resource]
                    ),
                )
            )

        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

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
            WebsocketWorker(
                socket_name=self.name,
                event_type=event_type,
                handler=func,
            )

        return decorator


def websocket(name: str) -> Websocket:
    """
    Create and registers a websocket.

    If a websocket has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Websocket, name)  # type: ignore pylint: disable=protected-access


def _websocket_context_from_proto(msg: WebsocketEventRequest) -> WebsocketContext:
    """Construct a new WebsocketContext from a websocket trigger from the Nitric Server."""
    query: Record = {k: v.value for (k, v) in msg.connection.query_params.items()}

    req = WebsocketRequest(
        connection_id=msg.connection_id,
    )
    evt_type, _ = betterproto.which_one_of(msg, "websocket_event")
    if evt_type == "connection":
        req = WebsocketConnectionRequest(
            connection_id=msg.connection_id,
            query=query,
        )
    if evt_type == "message":
        req = WebsocketMessageRequest(connection_id=msg.connection_id, data=msg.message.body)

    return WebsocketContext(request=req)


def _websocket_context_to_proto_response(ctx: WebsocketContext) -> WebsocketEventResponse:
    resp = WebsocketEventResponse()
    if isinstance(ctx.res, WebsocketConnectionResponse):
        resp.connection_response = ProtoWebsocketConnectionResponse(reject=ctx.res.reject)
    return resp


class WebsocketWorker(FunctionServer):
    """A handler for websocket events."""

    _handler: WebsocketHandler
    _registration_request: RegistrationRequest
    _responses: AsyncNotifierList[ClientMessage]

    def __init__(
        self, socket_name: str, event_type: Literal["connect", "disconnect", "message"], handler: WebsocketHandler
    ):
        """Construct a new WebsocketHandler."""
        self._handler = handler
        self._responses = AsyncNotifierList()
        self._registration_request = RegistrationRequest(
            socket_name=socket_name, event_type=_to_grpc_event_type(event_type)
        )

        Nitric._register_worker(self)

    async def _ws_request_iterator(self):
        # Register with the server
        yield ClientMessage(registration_request=self._registration_request)
        # wait for any responses for the server and send them
        async for response in self._responses:
            yield response

    async def start(self) -> None:
        """Register this websocket handler and listen for messages."""
        channel = ChannelManager.get_channel()
        server = WebsocketHandlerStub(channel=channel)

        try:
            async for server_msg in server.handle_events(self._ws_request_iterator()):
                msg_type, _ = betterproto.which_one_of(server_msg, "content")

                if msg_type == "registration_response":
                    continue
                if msg_type == "websocket_event_request":
                    ctx = _websocket_context_from_proto(server_msg.websocket_event_request)

                    response: ClientMessage
                    try:
                        result = await self._handler(ctx)
                        ctx = result if result else ctx
                        response = ClientMessage(id=server_msg.id, websocket_event_response=WebsocketEventResponse())
                        if isinstance(ctx.res, WebsocketConnectionResponse):
                            response.websocket_event_response.connection_response.reject = ctx.res.reject
                    except Exception as e:  # pylint: disable=broad-except
                        logging.exception("An unhandled error occurred in a websocket event handler: %s", e)
                        response = ClientMessage(id=server_msg.id, websocket_event_response=WebsocketEventResponse())
                        if isinstance(ctx.req, WebsocketConnectionRequest):
                            response.websocket_event_response.connection_response.reject = True
                    await self._responses.add_item(response)
        except grpclib.exceptions.GRPCError as e:
            print(f"Stream terminated: {e.message}")
        except grpclib.exceptions.StreamTerminatedError:
            print("Stream from membrane closed.")
        finally:
            print("Closing client stream")
            channel.close()
