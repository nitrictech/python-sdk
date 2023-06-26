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

from nitric.exception import exception_from_grpc_error
from typing import List, Literal
from grpclib import GRPCError
from nitric.api.queues import QueueRef, Queues
from nitric.application import Nitric
from nitric.proto.nitric.resource.v1 import (
    Resource,
    ResourceType,
    Action,
    ResourceDeclareRequest,
)

from nitric.resources.resource import SecureResource

QueuePermission = Literal["sending", "receiving"]


class Queue(SecureResource):
    """A queue resource."""

    name: str
    actions: List[Action]

    def __init__(self, name: str):
        """Construct a new queue resource."""
        super().__init__()
        self.name = name

    def _to_resource(self) -> Resource:
        return Resource(name=self.name, type=ResourceType.Queue)  # type:ignore

    def _perms_to_actions(self, *args: QueuePermission) -> List[int]:
        permission_actions_map: dict[QueuePermission, List[int]] = {
            "sending": [Action.QueueSend, Action.QueueList, Action.QueueDetail],
            "receiving": [Action.QueueReceive, Action.QueueList, Action.QueueDetail],
        }

        return [action for perm in args for action in permission_actions_map[perm]]

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(resource=self._to_resource())
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    def allow(self, *args: QueuePermission) -> QueueRef:
        """Request the required permissions for this queue."""
        # Ensure registration of the resource is complete before requesting permissions.
        str_args = [str(permission) for permission in args]
        self._register_policy(*str_args)

        return Queues().queue(self.name)


def queue(name: str) -> Queue:
    """
    Create and register a queue.

    If a queue has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Queue, name)  # type: ignore
