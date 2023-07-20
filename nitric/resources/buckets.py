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
from nitric.api.storage import BucketRef, Storage
from typing import List, Callable, Literal
from grpclib import GRPCError

from nitric.application import Nitric
from nitric.faas import FunctionServer, BucketNotificationWorkerOptions, BucketNotificationHandler
from nitric.proto.nitric.resource.v1 import (
    Resource,
    ResourceType,
    Action,
    ResourceDeclareRequest,
)

from nitric.resources.resource import SecureResource

BucketPermission = Literal["reading", "writing", "deleting"]


class Bucket(SecureResource):
    """A bucket resource, used for storage and retrieval of blob/binary data."""

    name: str
    actions: List[Action]
    _server: FunctionServer

    def __init__(self, name: str):
        """Create a bucket with the name provided or references it if it already exists."""
        super().__init__()
        self.name = name

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(resource=self._to_resource())
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    def _perms_to_actions(self, *args: BucketPermission) -> List[int]:
        permission_actions_map: dict[BucketPermission, List[int]] = {
            "reading": [Action.BucketFileGet, Action.BucketFileList],
            "writing": [Action.BucketFilePut],
            "deleting": [Action.BucketFileDelete],
        }

        return [action for perm in args for action in permission_actions_map[perm]]

    def _to_resource(self) -> Resource:
        return Resource(name=self.name, type=ResourceType.Bucket)  # type:ignore

    def allow(self, *args: BucketPermission) -> BucketRef:
        """Request the required permissions for this resource."""
        str_args = [str(permission) for permission in args]
        self._register_policy(*str_args)

        return Storage().bucket(self.name)

    def on(
        self, notification_type: str, notification_prefix_filter: str
    ) -> Callable[[BucketNotificationHandler], None]:
        """Create and return a bucket notification decorator for this bucket."""

        def decorator(func: BucketNotificationHandler) -> None:
            self._server = FunctionServer(
                BucketNotificationWorkerOptions(
                    bucket_name=self.name,
                    notification_type=notification_type,
                    notification_prefix_filter=notification_prefix_filter,
                )
            )
            self._server.bucket_notification(func)
            return Nitric._register_worker(self._server)  # type: ignore

        return decorator


def bucket(name: str) -> Bucket:
    """
    Create and register a bucket.

    If a bucket has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Bucket, name)  # type: ignore
