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

import asyncio
from abc import ABC, abstractmethod
from asyncio import Task
from typing import Any, List, Optional, Sequence, Type, TypeVar

from grpclib import GRPCError

from nitric.exception import NitricResourceException, exception_from_grpc_error
from nitric.proto.resources.v1 import (
    Action,
    PolicyResource,
    ResourceDeclareRequest,
    ResourceIdentifier,
    ResourcesStub,
    ResourceType,
)
from nitric.channel import ChannelManager

T = TypeVar("T", bound="Resource")


class Resource(ABC):
    """A base resource class with common functionality."""

    name: str

    def __init__(self, name: str):
        """Construct a new resource."""
        self.name = name
        self._reg: Optional[Task[Any]] = None  # type: ignore
        self._channel = ChannelManager.get_channel()
        self._resources_stub = ResourcesStub(channel=self._channel)

    @abstractmethod
    async def _register(self) -> None:
        pass

    @classmethod
    def make(cls: Type[T], name: str, *args: Sequence[Any], **kwargs: dict[str, Any]) -> T:
        """
        Create and register the resource.

        The registration process for resources async, so this method should be used instead of __init__.
        """
        r = cls(name, *args, **kwargs)  # type: ignore
        try:
            loop = asyncio.get_running_loop()
            r._reg = loop.create_task(r._register())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(r._register())

        return r


class SecureResource(Resource):
    """A secure base resource class."""

    @abstractmethod
    def _to_resource_id(self) -> ResourceIdentifier:
        pass

    @abstractmethod
    def _perms_to_actions(self, *args: Any) -> List[Action]:
        pass

    async def _register_policy_async(self, *args: str) -> None:
        policy = PolicyResource(
            principals=[ResourceIdentifier(type=ResourceType.Service)],
            actions=self._perms_to_actions(*args),
            resources=[self._to_resource_id()],
        )
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    id=ResourceIdentifier(type=ResourceType.Policy), policy=policy
                )
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    def _register_policy(self, *args: str) -> None:
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._register_policy_async(*args))
        except RuntimeError:
            raise NitricResourceException(
                "Nitric resources cannot be declared at runtime e.g. within the scope of a runtime function. \
                    Move resource declarations to the top level of scripts so that they can be safely provisioned"
            ) from None
