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

from dataclasses import dataclass
from typing import List, Literal, Union

from grpclib import GRPCError
from grpclib.client import Channel

from nitric.application import Nitric
from nitric.exception import exception_from_grpc_error
from nitric.proto.resources.v1 import Action, ResourceDeclareRequest, ResourceIdentifier, ResourceType
from nitric.proto.secrets.v1 import Secret as SecretMessage
from nitric.proto.secrets.v1 import SecretAccessRequest, SecretManagerStub, SecretPutRequest
from nitric.proto.secrets.v1 import SecretVersion as VersionMessage
from nitric.resources.resource import SecureResource
from nitric.channel import ChannelManager


class SecretRef:
    """A reference to a deployed secret, used to interact with the secret at runtime."""

    _channel: Channel
    _secrets_stub: SecretManagerStub
    name: str

    def __init__(self, name: str) -> None:
        """Construct a Nitric Storage Client."""
        self._channel: Channel = ChannelManager.get_channel()
        self._secrets_stub = SecretManagerStub(channel=self._channel)
        self.name = name

    def __del__(self):
        # close the channel when this client is destroyed
        if self._channel is not None:
            self._channel.close()

    async def put(self, value: Union[str, bytes]) -> SecretVersionRef:
        """
        Create a new secret version, making it the latest and storing the provided value.

        :param value: the secret value to store
        """
        if isinstance(value, str):
            value = bytes(value, "utf-8")

        secret_message = SecretMessage(name=self.name)

        try:
            response = await self._secrets_stub.put(
                secret_put_request=SecretPutRequest(secret=secret_message, value=value)
            )
            return self.version(version=response.secret_version.version)
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    def version(self, version: str) -> SecretVersionRef:
        """
        Return a reference to a specific version of a secret.

        Can be used to retrieve the secret value associated with the version.
        """
        return SecretVersionRef(secret=self, id=version)

    def latest(self) -> SecretVersionRef:
        """
        Return a reference to the 'latest' secret version.

        Note: using 'access' on this reference may return different values between requests if a
        new version is created between access calls.
        """
        return self.version("latest")


def _secret_version_to_wire(version: SecretVersionRef) -> VersionMessage:
    return VersionMessage(SecretMessage(name=version.secret.name), version=version.id)


@dataclass(frozen=True)
class SecretVersionRef:
    """A reference to a version of a secret, used to access the value of the version."""

    secret: SecretRef
    id: str

    async def access(self) -> SecretValue:
        """Return the value stored in this version of the secret."""
        version_message = _secret_version_to_wire(self)
        try:
            response = await self.secret._secrets_stub.access(  # type: ignore pylint: disable=protected-access
                secret_access_request=SecretAccessRequest(secret_version=version_message)
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

        # Construct a new SecretVersion if the response version id doesn't match this reference.
        # This ensures calls to access from the 'latest' version return new version objects
        # with a fixed version id.
        static_version = (
            self
            if response.secret_version.version == self.id
            else SecretVersionRef(secret=self.secret, id=response.secret_version.version)
        )

        return SecretValue(version=static_version, value=response.value)


@dataclass(frozen=True)
class SecretValue:
    """Represents the value of a secret, tied to a specific version of the secret."""

    # The version containing this value. Never 'latest', always a specific version.
    version: SecretVersionRef
    value: bytes

    def __str__(self) -> str:
        return self.value.decode("utf-8")

    def __bytes__(self) -> bytes:
        return self.value

    def as_string(self) -> str:
        """Return the content of this secret value as a string."""
        return str(self)

    def as_bytes(self) -> bytes:
        """Return the content of this secret value."""
        return bytes(self)


SecretPermission = Literal["access", "put"]


class Secret(SecureResource):
    """A secret resource, used for storing sensitive information."""

    name: str
    actions: List[Action]

    def __init__(self, name: str):
        """Construct a new secret resource reference."""
        super().__init__(name)

    def _to_resource_id(self) -> ResourceIdentifier:
        return ResourceIdentifier(name=self.name, type=ResourceType.Secret)

    async def _register(self):
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(id=self._to_resource_id())
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    def _perms_to_actions(self, *args: SecretPermission) -> List[Action]:
        permissions_actions_map: dict[SecretPermission, List[Action]] = {
            "access": [Action.SecretAccess],
            "put": [Action.SecretPut],
        }

        return [action for perm in args for action in permissions_actions_map[perm]]

    def allow(self, perm: SecretPermission, *args: SecretPermission) -> SecretRef:
        """Request the specified permissions to this resource."""
        str_args = [str(perm)] + [str(permission) for permission in args]
        self._register_policy(*str_args)

        return SecretRef(self.name)


def secret(name: str) -> Secret:
    """
    Create and registers a secret.

    If a secret has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Secret, name)  # type: ignore pylint: disable=protected-access
