# Generated by the protocol buffer compiler.  DO NOT EDIT!
# sources: nitric/proto/secrets/v1/secrets.proto
# plugin: python-betterproto
# This file has been @generated

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Dict,
    Optional,
)

import betterproto
import grpclib
from betterproto.grpc.grpclib_server import ServiceBase


if TYPE_CHECKING:
    import grpclib.server
    from betterproto.grpc.grpclib_client import MetadataLike
    from grpclib.metadata import Deadline


@dataclass(eq=False, repr=False)
class SecretPutRequest(betterproto.Message):
    """Request to put a secret to a Secret Store"""

    secret: "Secret" = betterproto.message_field(1)
    """The Secret to put to the Secret store"""

    value: bytes = betterproto.bytes_field(2)
    """The value to assign to that secret"""


@dataclass(eq=False, repr=False)
class SecretPutResponse(betterproto.Message):
    """Result from putting the secret to a Secret Store"""

    secret_version: "SecretVersion" = betterproto.message_field(1)
    """The id of the secret"""


@dataclass(eq=False, repr=False)
class SecretAccessRequest(betterproto.Message):
    """Request to get a secret from a Secret Store"""

    secret_version: "SecretVersion" = betterproto.message_field(1)
    """The id of the secret"""


@dataclass(eq=False, repr=False)
class SecretAccessResponse(betterproto.Message):
    """The secret response"""

    secret_version: "SecretVersion" = betterproto.message_field(1)
    """The version of the secret that was requested"""

    value: bytes = betterproto.bytes_field(2)
    """The value of the secret"""


@dataclass(eq=False, repr=False)
class Secret(betterproto.Message):
    """The secret container"""

    name: str = betterproto.string_field(1)
    """The secret name"""


@dataclass(eq=False, repr=False)
class SecretVersion(betterproto.Message):
    """A version of a secret"""

    secret: "Secret" = betterproto.message_field(1)
    """Reference to the secret container"""

    version: str = betterproto.string_field(2)
    """The secret version"""


class SecretManagerStub(betterproto.ServiceStub):
    async def put(
        self,
        secret_put_request: "SecretPutRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "SecretPutResponse":
        return await self._unary_unary(
            "/nitric.proto.secrets.v1.SecretManager/Put",
            secret_put_request,
            SecretPutResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )

    async def access(
        self,
        secret_access_request: "SecretAccessRequest",
        *,
        timeout: Optional[float] = None,
        deadline: Optional["Deadline"] = None,
        metadata: Optional["MetadataLike"] = None
    ) -> "SecretAccessResponse":
        return await self._unary_unary(
            "/nitric.proto.secrets.v1.SecretManager/Access",
            secret_access_request,
            SecretAccessResponse,
            timeout=timeout,
            deadline=deadline,
            metadata=metadata,
        )


class SecretManagerBase(ServiceBase):
    async def put(self, secret_put_request: "SecretPutRequest") -> "SecretPutResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def access(
        self, secret_access_request: "SecretAccessRequest"
    ) -> "SecretAccessResponse":
        raise grpclib.GRPCError(grpclib.const.Status.UNIMPLEMENTED)

    async def __rpc_put(
        self, stream: "grpclib.server.Stream[SecretPutRequest, SecretPutResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.put(request)
        await stream.send_message(response)

    async def __rpc_access(
        self, stream: "grpclib.server.Stream[SecretAccessRequest, SecretAccessResponse]"
    ) -> None:
        request = await stream.recv_message()
        response = await self.access(request)
        await stream.send_message(response)

    def __mapping__(self) -> Dict[str, grpclib.const.Handler]:
        return {
            "/nitric.proto.secrets.v1.SecretManager/Put": grpclib.const.Handler(
                self.__rpc_put,
                grpclib.const.Cardinality.UNARY_UNARY,
                SecretPutRequest,
                SecretPutResponse,
            ),
            "/nitric.proto.secrets.v1.SecretManager/Access": grpclib.const.Handler(
                self.__rpc_access,
                grpclib.const.Cardinality.UNARY_UNARY,
                SecretAccessRequest,
                SecretAccessResponse,
            ),
        }