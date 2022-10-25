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

from nitric.api.exception import exception_from_grpc_error
from nitric.api.storage import BucketRef, Storage
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


class BucketPermission(Enum):
    """Valid query expression operators."""

    reading = "reading"
    writing = "writing"
    deleting = "deleting"


def _perms_to_actions(permissions: List[Union[BucketPermission, str]]) -> List[Action]:
    permission_actions_map = {
        BucketPermission.reading: [Action.BucketFileGet, Action.BucketFileList],
        BucketPermission.writing: [Action.BucketFilePut],
        BucketPermission.deleting: [Action.BucketFileDelete],
    }
    # convert strings to the enum value where needed
    perms = [
        permission if isinstance(permission, BucketPermission) else BucketPermission[permission.lower()]
        for permission in permissions
    ]
    return [action for perm in perms for action in permission_actions_map[perm]]


def _to_resource(b: Bucket) -> Resource:
    return Resource(name=b.name, type=ResourceType.Bucket)


class Bucket(BaseResource):
    """A bucket resource, used for storage and retrieval of blob/binary data."""

    name: str
    actions: List[Action]

    def __init__(self, name: str):
        """Create a bucket with the name provided or references it if it already exists."""
        super().__init__()
        self.name = name
        self._channel = new_default_channel()
        self._resources_stub = ResourceServiceStub(channel=self._channel)

    async def _register(self):
        try:
            await self._resources_stub.declare(resource_declare_request=ResourceDeclareRequest(resource=_to_resource(self)))
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    async def allow(self, permissions: List[str]) -> BucketRef:
        """Request the required permissions for this resource."""
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

        return Storage().bucket(self.name)


def bucket(name: str) -> Bucket:
    """
    Create and register a bucket.

    If a bucket has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Bucket, name)
