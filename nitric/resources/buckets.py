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
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Callable, List, Literal, Optional, Union, cast
from warnings import warn

import betterproto
import grpclib
from grpclib import GRPCError
from grpclib.client import Channel

from nitric.application import Nitric
from nitric.bidi import AsyncNotifierList
from nitric.context import FunctionServer, Handler, Middleware
from nitric.exception import InvalidArgumentException, exception_from_grpc_error
from nitric.proto.resources.v1 import Action, ResourceDeclareRequest, ResourceIdentifier, ResourceType
from nitric.proto.storage.v1 import (
    BlobEventRequest,
    BlobEventResponse,
    BlobEventType,
    ClientMessage,
    RegistrationRequest,
    StorageDeleteRequest,
    StorageExistsRequest,
    StorageListBlobsRequest,
    StorageListenerStub,
    StoragePreSignUrlRequest,
    StoragePreSignUrlRequestOperation,
    StorageReadRequest,
    StorageStub,
    StorageWriteRequest,
)
from nitric.resources.resource import SecureResource
from nitric.channel import ChannelManager


class BucketNotifyRequest:
    """Represents a translated Event, from a subscribed bucket notification, forwarded from the Nitric Membrane."""

    bucket_name: str
    key: str
    notification_type: BlobEventType
    bucket: BucketRef
    file: FileRef

    def __init__(self, bucket_name: str, key: str, notification_type: BlobEventType):
        """Construct a new BucketNotifyRequest."""
        self.bucket_name = bucket_name
        self.key = key
        self.notification_type = notification_type
        self.bucket = BucketRef(bucket_name)
        self.file = self.bucket.file(key)


class BucketNotifyResponse:
    """Represents the response to a trigger from a Bucket."""

    def __init__(self, success: bool = True):
        """Construct a new BucketNotificationResponse."""
        self.success = success


class BucketNotificationContext:
    """Represents the full request/response context for a bucket notification trigger."""

    def __init__(self, request: BucketNotifyRequest, response: Optional[BucketNotifyResponse] = None):
        """Construct a new BucketNotificationContext."""
        self.req = request
        self.res = response if response else BucketNotifyResponse()


class FileNotifyRequest(BucketNotifyRequest):
    """Represents a translated Event, from a subscribed bucket notification, forwarded from the Nitric Membrane."""

    def __init__(
        self,
        bucket_name: str,
        bucket_ref: BucketRef,
        key: str,
        notification_type: BlobEventType,
    ):
        """Construct a new FileNotificationRequest."""
        super().__init__(bucket_name=bucket_name, key=key, notification_type=notification_type)
        self.file = bucket_ref.file(key)


class FileNotificationContext(BucketNotificationContext):
    """Represents the full request/response context for a bucket notification trigger."""

    def __init__(self, request: FileNotifyRequest, response: Optional[BucketNotifyResponse] = None):
        """Construct a new FileNotificationContext."""
        super().__init__(request=request, response=response)
        self.req = request

    @staticmethod
    def _from_client_message_with_bucket(msg: BlobEventRequest, bucket_ref) -> FileNotificationContext:
        """Construct a new FileNotificationTrigger from a Bucket Notification trigger from the Nitric Membrane."""
        return FileNotificationContext(
            request=FileNotifyRequest(
                bucket_name=msg.bucket_name,
                key=msg.blob_event.key,
                bucket_ref=bucket_ref,
                notification_type=msg.blob_event.type,
            )
        )


BucketNotificationMiddleware = Middleware[BucketNotificationContext]
BucketNotificationHandler = Handler[BucketNotificationContext]

FileNotificationMiddleware = Middleware[FileNotificationContext]
FileNotificationHandler = Handler[FileNotificationContext]


class BucketRef(object):
    """A reference to a deployed storage bucket, used to interact with the bucket at runtime."""

    _channel: Channel
    _storage_stub: StorageStub
    name: str

    def __init__(self, name: str):
        """Construct a Nitric Storage Client."""
        self._channel: Union[Channel, None] = ChannelManager.get_channel()
        self._storage_stub = StorageStub(channel=self._channel)
        self.name = name

    def __del__(self):
        # close the channel when this client is destroyed
        if self._channel is not None:
            self._channel.close()

    def file(self, key: str):
        """Return a reference to a file in this bucket."""
        return FileRef(_bucket=self, key=key)

    async def files(self):
        """Return a list of files in this bucket."""
        resp = await self._storage_stub.list_blobs(
            storage_list_blobs_request=StorageListBlobsRequest(bucket_name=self.name)
        )
        return [self.file(f.key) for f in resp.files]

    async def exists(self, key: str) -> bool:
        """Return true if a file in the bucket exists."""
        resp = await self._storage_stub.exists(
            storage_exists_request=StorageExistsRequest(bucket_name=self.name, key=key)
        )
        return resp.exists

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


class FileMode(Enum):
    """Definition of available operation modes for file signed URLs."""

    READ = 0
    WRITE = 1

    def to_request_operation(self) -> StoragePreSignUrlRequestOperation:
        """Convert FileMode to a StoragePreSignUrlRequestOperation."""
        if self == FileMode.READ:
            return StoragePreSignUrlRequestOperation.READ
        elif self == FileMode.WRITE:
            return StoragePreSignUrlRequestOperation.WRITE
        else:
            raise InvalidArgumentException("Invalid FileMode")


@dataclass(frozen=True, order=True)
class FileRef(object):
    """A reference to a file in a bucket, used to perform operations on that file."""

    _bucket: BucketRef
    key: str

    async def write(self, body: bytes):
        """
        Write the bytes as the content of this file.

        Will create the file if it doesn't already exist.
        """
        try:
            await self._bucket._storage_stub.write(
                storage_write_request=StorageWriteRequest(bucket_name=self._bucket.name, key=self.key, body=body)
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    async def read(self) -> bytes:
        """Read this files contents from the bucket."""
        try:
            response = await self._bucket._storage_stub.read(
                storage_read_request=StorageReadRequest(bucket_name=self._bucket.name, key=self.key)
            )
            return response.body
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    async def delete(self):
        """Delete this file from the bucket."""
        try:
            await self._bucket._storage_stub.delete(
                storage_delete_request=StorageDeleteRequest(bucket_name=self._bucket.name, key=self.key)
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    async def upload_url(self, expiry: Optional[Union[timedelta, int]] = None):
        """
        Get a temporary writable URL to this file.

        Parameters
        ----------
        expiry : int, timedelta, optional
            The expiry time for the signed URL.
            If an integer is provided, it is treated as seconds. Default is 600 seconds.

        Returns
        -------
        str: The signed URL.

        """
        return await self._sign_url(mode=FileMode.WRITE, expiry=expiry)

    async def download_url(self, expiry: Optional[Union[timedelta, int]] = None):
        """
        Get a temporary readable URL to this file.

        Parameters
        ----------
        expiry : int, timedelta, optional
            The expiry time for the signed URL.
            If an integer is provided, it is treated as seconds. Default is 600 seconds.

        Returns
        -------
        str: The signed URL.

        """
        return await self._sign_url(mode=FileMode.READ, expiry=expiry)

    async def _sign_url(self, mode: FileMode = FileMode.READ, expiry: Optional[Union[timedelta, int]] = None):
        """Generate a signed URL for reading or writing to a file."""
        if expiry is None:
            expiry = timedelta(seconds=600)
        if not isinstance(expiry, timedelta):
            expiry = timedelta(seconds=expiry)

        try:
            response = await self._bucket._storage_stub.pre_sign_url(
                storage_pre_sign_url_request=StoragePreSignUrlRequest(
                    bucket_name=self._bucket.name, key=self.key, operation=mode.to_request_operation(), expiry=expiry
                )
            )
            return response.url
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err


LegacyBucketPermission = Literal["reading", "writing", "deleting"]
BucketPermission = Literal["read", "write", "delete"]

legacy_perms: List[LegacyBucketPermission] = ["reading", "writing", "deleting"]
new_perms: List[BucketPermission] = ["read", "write", "delete"]


def check_permission(permission: Union[LegacyBucketPermission, BucketPermission]) -> BucketPermission:
    """Check if the permission is valid and return the new permission if it is a legacy permission."""
    if permission in legacy_perms:
        new_perm = new_perms[legacy_perms.index(cast(LegacyBucketPermission, permission))]
        warn(
            f"The permission '{permission}' is deprecated. Use '{new_perm}' instead.", DeprecationWarning, stacklevel=2
        )
        return new_perm
    elif permission in new_perms:
        return cast(BucketPermission, permission)
    else:
        raise ValueError("Invalid permission value, must be one of 'read', 'write', or 'delete'.")


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

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(id=self._to_resource_id())
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    def _perms_to_actions(self, *args: BucketPermission) -> List[Action]:
        permission_actions_map: dict[BucketPermission, List[Action]] = {
            "read": [Action.BucketFileGet, Action.BucketFileList],
            "write": [Action.BucketFilePut],
            "delete": [Action.BucketFileDelete],
        }

        return [action for perm in args for action in permission_actions_map[perm]]

    def _to_resource_id(self) -> ResourceIdentifier:
        return ResourceIdentifier(name=self.name, type=ResourceType.Bucket)

    def allow(
        self,
        perm: Union[LegacyBucketPermission, BucketPermission],
        *args: Union[LegacyBucketPermission, BucketPermission],
    ) -> BucketRef:
        """Request the required permissions for this resource."""
        all_perms: List[BucketPermission] = [check_permission(perm)] + [check_permission(p) for p in args]

        str_args = [str(permission) for permission in all_perms]
        self._register_policy(*str_args)

        return BucketRef(self.name)

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
    """A bucket event listener."""

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
        """Construct a new bucket event listener."""
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

        # noinspection PyProtectedMember
        Nitric._register_worker(self)

    async def _listener_request_iterator(self):
        # Register with the server
        yield ClientMessage(registration_request=self._registration_request)
        # wait for any responses for the server and send them
        async for response in self._responses:
            yield response

    async def start(self) -> None:
        """Register this bucket listener and listen for events."""
        channel = ChannelManager.get_channel()
        server = StorageListenerStub(channel=channel)

        try:
            async for server_msg in server.listen(self._listener_request_iterator()):
                msg_type, _ = betterproto.which_one_of(server_msg, "content")

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
                    except Exception as e:  # pylint: disable=broad-except
                        logging.exception("An unhandled error occurred in a bucket event listener: %s", e)
                        be = BlobEventResponse(success=False)
                        response = ClientMessage(id=server_msg.id, blob_event_response=be)
                    await self._responses.add_item(response)
        except grpclib.exceptions.GRPCError as e:
            print(f"Stream terminated: {e.message}")
        except grpclib.exceptions.StreamTerminatedError:
            print("Stream from membrane closed.")
        except KeyboardInterrupt:
            print("Keyboard interrupt")
        finally:
            print("Closing client stream")
            channel.close()
        print("Listener stopped")


def bucket(name: str) -> Bucket:
    """
    Create and register a bucket.

    If a bucket has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Bucket, name)
