# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: proto/schedules/v1/schedules.proto
# plugin: python-betterproto
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    AsyncIterable,
    AsyncIterator,
    Dict,
    Iterable,
    Optional,
    Union,
)

import betterproto
import grpclib
from betterproto.grpc.grpclib_server import ServiceBase


if TYPE_CHECKING:
    import grpclib.server
    from betterproto.grpc.grpclib_client import MetadataLike
    from grpclib.metadata import Deadline


@dataclass(eq=False, repr=False)
class ClientMessage(betterproto.Message):
    id: str = betterproto.string_field(1)
    """globally unique ID of the request/response pair"""

    registration_request: "RegistrationRequest" = betterproto.message_field(
        2, group="content"
    )
    """Register a subscription to a schedule"""

    interval_response: "IntervalResponse" = betterproto.message_field(
        3, group="content"
    )
    """Response to a schedule interval"""


@dataclass(eq=False, repr=False)
class IntervalRequest(betterproto.Message):
    schedule_name: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class MessageResponse(betterproto.Message):
    success: bool = betterproto.bool_field(1)


@dataclass(eq=False, repr=False)
class ServerMessage(betterproto.Message):
    id: str = betterproto.string_field(1)
    """globally unique ID of the request/response pair"""

    registration_response: "RegistrationResponse" = betterproto.message_field(
        2, group="content"
    )
    """Response to a schedule subscription request"""

    interval_request: "IntervalRequest" = betterproto.message_field(3, group="content")
    """A schedule interval trigger request"""


@dataclass(eq=False, repr=False)
class RegistrationRequest(betterproto.Message):
    schedule_name: str = betterproto.string_field(1)
    every: "ScheduleEvery" = betterproto.message_field(10, group="cadence")
    cron: "ScheduleCron" = betterproto.message_field(11, group="cadence")


@dataclass(eq=False, repr=False)
class ScheduleEvery(betterproto.Message):
    rate: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class ScheduleCron(betterproto.Message):
    expression: str = betterproto.string_field(1)


@dataclass(eq=False, repr=False)
class RegistrationResponse(betterproto.Message):
    pass


@dataclass(eq=False, repr=False)
class IntervalResponse(betterproto.Message):
    pass


class SchedulesStub(betterproto.ServiceStub):
    async def schedule(
        self,
        client_message_iterator: Union[
            AsyncIterable["ClientMessage"], Iterable["ClientMessage"]
        ],
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> AsyncIterator["ServerMessage"]:
        async for response in self._stream_stream(
            "/nitric.proto.schedules.v1.Schedules/Schedule",
            client_message_iterator,
            ClientMessage,
            ServerMessage,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        ):
            yield response


class SchedulesBase(ServiceBase):
    async def schedule(
        self, client_message_iterator: AsyncIterator["ClientMessage"]
    ) -> AsyncIterator["ServerMessage"]:
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def __rpc_schedule(
        self, stream: "grpclib.server.Stream[ClientMessage, ServerMessage]"
    ) -> None:
        request = stream.__aiter__()
        await self._call_rpc_handler_server_stream(
            self.schedule,
            stream,
            request,
        )

    def __mapping__(self) -> Dict[str, grpclib.const.Handler]:
        return {
            "/nitric.proto.schedules.v1.Schedules/Schedule": grpclib.const.Handler(
                self.__rpc_schedule,
                grpclib.const.Cardinality.STREAM_STREAM,
                ClientMessage,
                ServerMessage,
            ),
        }
