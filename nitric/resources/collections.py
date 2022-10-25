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

from nitric.api.documents import CollectionRef, Documents
from nitric.api.exception import exception_from_grpc_error
from typing import List, Union
from enum import Enum
from grpclib import GRPCError

from nitric.application import Nitric
from nitric.utils import new_default_channel
from nitricapi.nitric.resource.v1 import (
    Resource,
    ResourceServiceStub,
    PolicyResource,
    ResourceType,
    Action, ResourceDeclareRequest,
)

from nitric.resources.base import BaseResource


class CollectionPermission(Enum):
    """Valid query expression operators."""

    reading = "reading"
    writing = "writing"
    deleting = "deleting"


def _perms_to_actions(permissions: List[Union[CollectionPermission, str]]) -> List[Action]:
    permission_actions_map = {
        CollectionPermission.reading: [Action.CollectionDocumentRead, Action.CollectionQuery, Action.CollectionList],
        CollectionPermission.writing: [Action.CollectionDocumentWrite, Action.CollectionList],
        CollectionPermission.deleting: [Action.CollectionDocumentDelete, Action.CollectionList],
    }
    # convert strings to the enum value where needed
    perms = [
        permission if isinstance(permission, CollectionPermission) else CollectionPermission[permission.lower()]
        for permission in permissions
    ]

    return [action for perm in perms for action in permission_actions_map[perm]]


def _to_resource(collection: Collection) -> Resource:
    return Resource(name=collection.name, type=ResourceType.Collection)


class Collection(BaseResource):
    """A document collection resource."""

    def __init__(self, name: str):
        """Construct a new document collection."""
        super().__init__()
        self.name = name
        self._channel = new_default_channel()
        self._resources_stub = ResourceServiceStub(channel=self._channel)

    async def _register(self):
        try:
            await self._resources_stub.declare(resource_declare_request=ResourceDeclareRequest(resource=_to_resource(self)))
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    async def allow(self, permissions: List[Union[CollectionPermission, str]]) -> CollectionRef:
        """Request the required permissions for this collection."""
        # Ensure registration of the resource is complete before requesting permissions.
        if self._reg is not None:
            await self._reg

        policy = PolicyResource(
            principals=[Resource(type=ResourceType.Function)],
            actions=_perms_to_actions(permissions),
            resources=[_to_resource(self)],
        )
        try:
            await self._resources_stub.declare(resource_declare_request=ResourceDeclareRequest(resource=Resource(type=ResourceType.Policy), policy=policy))
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

        return Documents().collection(self.name)


def collection(name: str) -> Collection:
    """
    Create and register a collection.

    If a collection has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Collection, name)
