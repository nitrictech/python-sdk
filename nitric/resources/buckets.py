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

import logging

import betterproto
import grpclib

from nitric.bidi import AsyncNotifierList
from nitric.exception import exception_from_grpc_error
from nitric.api.storage import BucketRef, Storage
from typing import List, Callable, Literal
from grpclib import GRPCError

from nitric.application import Nitric
from nitric.context import FunctionServer, BucketNotificationHandler, BucketNotificationContext, BucketNotifyRequest
from nitric.proto.resources.v1 import (
    ResourceIdentifier,
    ResourceType,
    Action,
    ResourceDeclareRequest,
)
from nitric.proto.storage.v1 import (
    BlobEventType,
    StorageListenerStub,
    ClientMessage,
    RegistrationRequest,
    BlobEventResponse,
)

from nitric.resources.resource import SecureResource
from nitric.utils import new_default_channel

BucketPermission = Literal["reading", "writing", "deleting"]


class BucketNotificationWorkerOptions:
    """Options for bucket notification workers."""

    def __init__(self, bucket_name: str, notification_type: str, notification_prefix_filter: str):
        """Construct a new options object."""
        self.bucket_name = bucket_name
        self.notification_type = BucketNotificationWorkerOptions._to_grpc_event_type(notification_type.lower())
        self.notification_prefix_filter = notification_prefix_filter

    @staticmethod
    def _to_grpc_event_type(event_type: str) -> BlobEventType:
        if event_type == "write":
            return BlobEventType.Created
        elif event_type == "delete":
            return BlobEventType.Deleted
        else:
            raise ValueError(f"Event type {event_type} is unsupported")


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
            await self._resources_stub.declare(resource_declare_request=ResourceDeclareRequest(id=self._to_resource()))
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    def _perms_to_actions(self, *args: BucketPermission) -> List[Action]:
        permission_actions_map: dict[BucketPermission, List[Action]] = {
            "reading": [Action.BucketFileGet, Action.BucketFileList],
            "writing": [Action.BucketFilePut],
            "deleting": [Action.BucketFileDelete],
        }

        return [action for perm in args for action in permission_actions_map[perm]]

    def _to_resource(self) -> ResourceIdentifier:
        return Resource(name=self.name, type=ResourceType.Bucket)  # type:ignore

    def allow(self, perm: BucketPermission, *args: BucketPermission) -> BucketRef:
        """Request the required permissions for this resource."""
        str_args = [str(perm)] + [str(permission) for permission in args]
        self._register_policy(*str_args)

        return Storage().bucket(self.name)

    def on(
        self, notification_type: str, notification_prefix_filter: str
    ) -> Callable[[BucketNotificationHandler], None]:
        """Create and return a bucket notification decorator for this bucket."""

        def decorator(func: BucketNotificationHandler) -> None:
            Listener(
                bucket_name=self.name,
                notification_type=notification_type,
                notification_prefix_filter=notification_prefix_filter,
                handler=func,
            )

        return decorator


class Listener(FunctionServer):
    _handler: BucketNotificationHandler
    _registration_request: RegistrationRequest
    _responses: AsyncNotifierList[ClientMessage]

    def __init__(
        self,
        bucket_name: str,
        notification_type: str,
        notification_prefix_filter: str,
        handler: BucketNotificationHandler,
    ):
        self._handler = handler
        self._responses = AsyncNotifierList()

        event_type = BlobEventType.Created
        if "del" in notification_type:
            event_type = BlobEventType.Deleted

        self._registration_request = RegistrationRequest(
            bucket_name=bucket_name,
            blob_event_type=event_type,
            key_prefix_filter=notification_prefix_filter,
        )

        Nitric._register_worker(self)

    async def _listener_request_iterator(self):
        # Register with the server
        yield ClientMessage(registration_request=self._registration_request)
        # wait for any responses for the server and send them
        async for response in self._responses:
            yield response

    async def start(self) -> None:
        """Register this bucket listener and listen for events."""
        channel = new_default_channel()
        server = StorageListenerStub(channel=channel)

        try:
            async for server_msg in server.listen(self._listener_request_iterator()):
                msg_type = betterproto.which_one_of(server_msg, "content")

                if msg_type == "registration_response":
                    continue
                if msg_type == "blob_event_request":
                    ctx = BucketNotificationContext(
                        request=BucketNotifyRequest(
                            bucket_name=server_msg.blob_event_request.bucket_name,
                            key=server_msg.blob_event_request.blob_event.key,
                            notification_type=server_msg.blob_event_request.blob_event.type,
                        )
                    )
                    response: ClientMessage
                    try:
                        result = await self._handler(ctx)
                        ctx = result if result else ctx
                        be = BlobEventResponse(success=ctx.res.success)
                        response = ClientMessage(id=server_msg.id, blob_event_response=be)
                    except Exception as e:
                        logging.exception(f"An unhandled error occurred in a bucket event listener: {e}")
                        be = BlobEventResponse(success=False)
                        response = ClientMessage(id=server_msg.id, blob_event_response=be)
                    await self._responses.add_item(response)
        except grpclib.exceptions.GRPCError as e:
            print(f"Stream terminated: {e.message}")
        except grpclib.exceptions.StreamTerminatedError:
            print("Stream from membrane closed.")
        finally:
            print("Closing client stream")
            channel.close()


def bucket(name: str) -> Bucket:
    """
    Create and register a bucket.

    If a bucket has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Bucket, name)  # type: ignore
