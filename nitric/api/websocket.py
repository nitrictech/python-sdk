from typing import Union
from grpclib.client import Channel
from grpclib import GRPCError
from nitric.exception import exception_from_grpc_error
from nitric.utils import new_default_channel
from nitric.proto.websockets.v1 import (
    WebsocketStub,
    WebsocketSendRequest,
)


class Websocket(object):
    """Nitric generic Websocket client."""

    def __init__(self):
        """Construct a Nitric Websocket Client."""
        self._channel: Union[Channel, None] = new_default_channel()
        self.websocket_stub = WebsocketStub(channel=self._channel)

    async def send(self, socket: str, connection_id: str, data: bytes):
        """Send data to a connection on a socket."""
        try:
            await self.websocket_stub.send(
                websocket_send_request=WebsocketSendRequest(socket_name=socket, connection_id=connection_id, data=data)
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)
