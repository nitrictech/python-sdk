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
from typing import Union

from grpclib import GRPCError

from nitric.api.exception import exception_from_grpc_error
from nitric.utils import new_default_channel
from nitricapi.nitric.secret.v1 import SecretServiceStub, Secret as SecretMessage, SecretVersion as VersionMessage


class Secrets(object):
    """
    Nitric secrets management client.

    This client insulates application code from stack specific secrets managements services.
    """

    def __init__(self):
        """Construct a Nitric Storage Client."""
        self._channel = new_default_channel()
        self._secrets_stub = SecretServiceStub(channel=self._channel)

    def __del__(self):
        # close the channel when this client is destroyed
        if self._channel is not None:
            self._channel.close()

    def secret(self, name: str):
        """Return a reference to a secret container from the connected secrets management service."""
        return SecretContainer(_secrets=self, name=name)


def _secret_to_wire(secret: SecretContainer) -> SecretMessage:
    return SecretMessage(name=secret.name)


@dataclass(frozen=True)
class SecretContainer(object):
    """A reference to a secret container, used to store and retrieve secret versions."""

    _secrets: Secrets
    name: str

    async def put(self, value: Union[str, bytes]) -> SecretVersion:
        """
        Create a new secret version, making it the latest and storing the provided value.

        :param value: the secret value to store
        """
        if isinstance(value, str):
            value = bytes(value, "utf-8")

        secret_message = _secret_to_wire(self)

        try:
            response = await self._secrets._secrets_stub.put(secret=secret_message, value=value)
            return self.version(version=response.secret_version.version)
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    def version(self, version: str):
        """
        Return a reference to a specific version of a secret.

        Can be used to retrieve the secret value associated with the version.
        """
        return SecretVersion(_secrets=self._secrets, secret=self, id=version)

    def latest(self):
        """
        Return a reference to the 'latest' secret version.

        Note: using 'access' on this reference may return different values between requests if a
        new version is created between access calls.
        """
        return self.version("latest")


def _secret_version_to_wire(version: SecretVersion) -> VersionMessage:
    return VersionMessage(_secret_to_wire(version.secret), version=version.id)


@dataclass(frozen=True)
class SecretVersion(object):
    """A reference to a version of a secret, used to access the value of the version."""

    _secrets: Secrets
    secret: SecretContainer
    id: str

    async def access(self) -> SecretValue:
        """Return the value stored against this version of the secret."""
        version_message = _secret_version_to_wire(self)
        try:
            response = await self._secrets._secrets_stub.access(secret_version=version_message)
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

        # Construct a new SecretVersion if the response version id doesn't match this reference.
        # This ensures calls to access from the 'latest' version return new version objects
        # with a fixed version id.
        static_version = (
            self
            if response.secret_version.version == self.id
            else SecretVersion(_secrets=self._secrets, secret=self.secret, id=response.secret_version.version)
        )

        return SecretValue(version=static_version, value=response.value)


@dataclass(frozen=True)
class SecretValue(object):
    """Represents the value of a secret, tied to a specific version."""

    # The version containing this value. Never 'latest', always a specific version.
    version: SecretVersion
    value: bytes

    def __str__(self) -> str:
        return self.value.decode("utf-8")

    def __bytes__(self) -> bytes:
        return self.value

    def as_string(self):
        """Return the content of this secret value as a string."""
        return str(self)

    def as_bytes(self):
        """Return the content of this secret value."""
        return bytes(self)
