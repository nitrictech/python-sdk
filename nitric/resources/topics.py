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

from nitric.api.events import Events, TopicRef
from nitric.exception import exception_from_grpc_error
from typing import List, Callable, Literal
from grpclib import GRPCError
from nitric.application import Nitric
from nitric.faas import FunctionServer, SubscriptionWorkerOptions, EventHandler
from nitric.proto.nitric.resource.v1 import (
    Resource,
    ResourceType,
    Action,
    ResourceDeclareRequest,
)

from nitric.resources.resource import SecureResource

TopicPermission = Literal["publishing"]


class Topic(SecureResource):
    """A topic resource, used for asynchronous messaging between functions."""

    name: str
    actions: List[Action]

    def __init__(self, name: str):
        """Construct a new topic."""
        super().__init__()
        self.name = name

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(resource=self._to_resource())
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    def _to_resource(self) -> Resource:
        return Resource(name=self.name, type=ResourceType.Topic)  # type:ignore

    def _perms_to_actions(self, *args: TopicPermission) -> List[int]:
        _permMap: dict[TopicPermission, List[int]] = {"publishing": [Action.TopicEventPublish]}

        return [action for perm in args for action in _permMap[perm]]

    def allow(self, *args: TopicPermission) -> TopicRef:
        """Request the specified permissions to this resource."""
        str_args = [str(permission) for permission in args]
        self._register_policy(*str_args)

        return Events().topic(self.name)

    def subscribe(self) -> Callable[[EventHandler], None]:
        """Create and return a subscription decorator for this topic."""

        def decorator(func: EventHandler) -> None:
            server = FunctionServer(SubscriptionWorkerOptions(topic=self.name))
            server.event(func)
            # type ignored because the register call is treated as protected.
            Nitric._register_worker(server)  # type: ignore

        return decorator


def topic(name: str) -> Topic:
    """
    Create and register a topic.

    If a topic has already been registered with the same name, the original reference will be reused.
    """
    # type ignored because the create call are treated as protected.
    return Nitric._create_resource(Topic, name)  # type: ignore
