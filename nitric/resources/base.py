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

from typing import TypeVar, Type, Union, List

from grpclib import GRPCError
from nitric.proto.nitric.resource.v1 import (
    Action,
    PolicyResource,
    Resource,
    ResourceType,
    ResourceDeclareRequest,
    ResourceServiceStub,
)

from nitric.api.exception import exception_from_grpc_error, NitricResourceException
from nitric.utils import new_default_channel

T = TypeVar("T", bound="BaseResource")


class BaseResource(ABC):
    """A base resource class with common functionality."""

    cache = {}

    def __init__(self):
        """Construct a new resource."""
        self._reg: Union[Task, None] = None
        self._channel = new_default_channel()
        self._resources_stub = ResourceServiceStub(channel=self._channel)

    @abstractmethod
    async def _register(self):
        pass

    @classmethod
    def make(cls: Type[T], name: str, *args, **kwargs) -> T:
        """
        Create and register the resource.

        The registration process for resources async, so this method should be used instead of __init__.
        """
        # Todo: store the resource reference in a cache to avoid duplicate registrations
        r = cls(name, *args, **kwargs)
        try:
            loop = asyncio.get_running_loop()
            r._reg = loop.create_task(r._register())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(r._register())

        return r


class SecureResource(BaseResource):
    """A secure base resource class."""

    @abstractmethod
    def _to_resource(self) -> Resource:
        pass

    @abstractmethod
    def _perms_to_actions(self, *args: str) -> List[Action]:
        pass

    async def _register_policy_async(self, *args: str):
        # if self._reg is not None:
        #     await asyncio.wait({self._reg})

        policy = PolicyResource(
            principals=[Resource(type=ResourceType.Function)],
            actions=self._perms_to_actions(*args),
            resources=[self._to_resource()],
        )
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    resource=Resource(type=ResourceType.Policy), policy=policy
                )
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    def _register_policy(self, *args: str):
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._register_policy_async(*args))
        except RuntimeError:
            # TODO: Check nitric runtime ENV variable
            raise NitricResourceException(
                "Nitric resources cannot be declared at runtime e.g. within the scope of a function. \
                    Move resource declarations to the top level of scripts so that they can be safely provisioned"
            )
