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

from nitric.api.events import Events, TopicRef
from nitric.api.exception import exception_from_grpc_error
from typing import List, Union
from enum import Enum
from grpclib import GRPCError
from nitric.application import Nitric
from nitric.faas import EventMiddleware, FunctionServer, SubscriptionWorkerOptions
from nitric.utils import new_default_channel
from nitricapi.nitric.resource.v1 import (
    Resource,
    ResourceServiceStub,
    PolicyResource,
    ResourceType,
    Action, ResourceDeclareRequest,
)

from nitric.resources.base import BaseResource


class TopicPermission(Enum):
    """Valid query expression operators."""

    publishing = "publishing"


def _perms_to_actions(permissions: List[Union[TopicPermission, str]]) -> List[Action]:
    _permMap = {TopicPermission.publishing: [Action.TopicEventPublish]}
    # convert strings to the enum value where needed
    perms = [
        permission if isinstance(permission, TopicPermission) else TopicPermission[permission.lower()]
        for permission in permissions
    ]

    return [action for perm in perms for action in _permMap[perm]]


def _to_resource(topic: Topic) -> Resource:
    return Resource(name=topic.name, type=ResourceType.Topic)


class Topic(BaseResource):
    """A topic resource, used for asynchronous messaging between functions."""

    name: str
    actions: List[Action]
    server: FunctionServer

    def __init__(self, name: str):
        """Construct a new topic."""
        super().__init__()
        self.name = name
        self._channel = new_default_channel()
        self._resources_stub = ResourceServiceStub(channel=self._channel)

    async def _register(self):
        try:
            await self._resources_stub.declare(resource_declare_request=ResourceDeclareRequest(resource=_to_resource(self)))
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    async def allow(self, permissions: List[str]) -> TopicRef:
        """Request the permissions required for this topic."""
        # Ensure registration of the resource is complete before requesting permissions.
        if self._reg is not None:
            await asyncio.wait({self._reg})

        policy = PolicyResource(
            principals=[Resource(type=ResourceType.Function)],
            actions=_perms_to_actions(permissions),
            resources=[_to_resource(self)],
        )
        try:
            await self._resources_stub.declare(resource_declare_request=ResourceDeclareRequest(resource=Resource(type=ResourceType.Policy), policy=policy))
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

        return Events().topic(self.name)

    def subscribe(self, func: EventMiddleware):
        """Create and return a subscription decorator for this topic."""

        self.server = FunctionServer(SubscriptionWorkerOptions(topic=self.name))
        self.server.event(func)
        Nitric._register_worker(self.server)


def topic(name: str) -> Topic:
    """
    Create and register a topic.

    If a topic has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Topic, name)
