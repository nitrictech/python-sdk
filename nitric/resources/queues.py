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

from dataclasses import dataclass, field
from typing import Any, List, Literal, Optional, Union

from grpclib import GRPCError
from grpclib.client import Channel

from nitric.application import Nitric
from nitric.exception import exception_from_grpc_error
from nitric.proto.queues.v1 import DequeuedMessage as ProtoDequeuedMessage
from nitric.proto.queues.v1 import QueueCompleteRequest, QueueDequeueRequest, QueueEnqueueRequest, QueueMessage
from nitric.proto.queues.v1 import QueuesStub as QueueServiceStub
from nitric.proto.resources.v1 import Action, ResourceDeclareRequest, ResourceIdentifier, ResourceType
from nitric.resources.resource import SecureResource
from nitric.utils import dict_from_struct, struct_from_dict
from nitric.channel import ChannelManager


@dataclass(frozen=True, order=True)
class DequeuedMessage(object):
    """A reference to a message received from a Queue, with a lease."""

    lease_id: str = field()
    _queue: QueueRef = field()
    payload: dict[str, Any] = field(default_factory=dict)

    async def complete(self):
        """
        Mark this message as complete and remove it from the queue.

        Only callable for messages that have been dequeued.
        """
        try:
            await self._queue._queue_stub.complete(
                queue_complete_request=QueueCompleteRequest(queue_name=self._queue.name, lease_id=self.lease_id)
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err


class EnqueueFailedException(Exception):
    """An exception raised when a message fails to be enqueued."""


@dataclass(frozen=True, order=True)
class FailedMessage:
    """Represents a failed queue publish."""

    message: dict[str, Any] = field(default_factory=dict)
    details: str = field(default="")


def _proto_to_dequeued(message: ProtoDequeuedMessage, queue: QueueRef) -> DequeuedMessage:
    """
    Convert a DequeuedMessage (protocol buffers) to a DequeuedMessage (python SDK).

    :param message: to convert
    :return: converted message
    """
    return DequeuedMessage(
        payload=dict_from_struct(message.message.struct_payload),
        lease_id=message.lease_id,
        _queue=queue,
    )


class QueueRef(object):
    """A reference to a queue from a queue service, used to perform operations on that queue."""

    _channel: Channel
    _queue_stub: QueueServiceStub
    name: str

    def __init__(self, name: str) -> None:
        """Construct a Nitric Queue Client."""
        self._channel: Channel = ChannelManager.get_channel()
        self._queue_stub = QueueServiceStub(channel=self._channel)
        self.name = name

    def __del__(self) -> None:
        # close the channel when this client is destroyed
        if self._channel is not None:
            self._channel.close()

    async def enqueue(self, messages: Union[dict[str, Any], List[dict[str, Any]]]) -> Union[None, List[FailedMessage]]:
        """
        Send one or more messages to this queue.

        If a list of messages is provided this function will return a list containing any messages that failed
        to be sent to the queue.

        :param messages: A message or list of messages to send to the queue.
        """
        if not isinstance(messages, list):
            messages = [messages]

        try:
            resp = await self._queue_stub.enqueue(
                queue_enqueue_request=QueueEnqueueRequest(
                    queue_name=self.name,
                    messages=[QueueMessage(struct_payload=struct_from_dict(message)) for message in messages],
                )
            )

            if len(resp.failed_messages) > 0:
                if len(messages) == 1:
                    raise EnqueueFailedException(resp.failed_messages[0].details)

                return [
                    FailedMessage(
                        message=dict_from_struct(failed_message.message.struct_payload), details=failed_message.details
                    )
                    for failed_message in resp.failed_messages
                ]

        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

        return None

    async def dequeue(self, limit: Optional[int] = None) -> List[DequeuedMessage]:
        """
        Pop 1 or more message from the queue, up to the depth limit.

        DequeuedMessages are messages that are leased for a limited period of time, where they may be worked on.
        Once complete or failed they must be acknowledged using the request specific leaseId.

        If the lease on a queue item expires before it is acknowledged the task will be
        returned to the queue for reprocessing.

        :param limit: The maximum number of messages to dequeue. Default: 1, Min: 1.
        :return: Messages popped from the queue.
        """
        # Set the default and minimum depth to 1.
        if limit is None or limit < 1:
            limit = 1

        try:
            response = await self._queue_stub.dequeue(
                queue_dequeue_request=QueueDequeueRequest(queue_name=self.name, depth=limit)
            )
            # Map the response protobuf response items to Python SDK objects
            return [_proto_to_dequeued(message=message, queue=self) for message in response.messages]
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err


QueuePermission = Literal["enqueue", "dequeue"]


class Queue(SecureResource):
    """A queue resource."""

    name: str
    actions: List[Action]

    def __init__(self, name: str):
        """Construct a new queue resource."""
        super().__init__(name)

    def _to_resource_id(self) -> ResourceIdentifier:
        return ResourceIdentifier(name=self.name, type=ResourceType.Queue)

    def _perms_to_actions(self, *args: QueuePermission) -> List[Action]:
        permission_actions_map: dict[QueuePermission, List[Action]] = {
            "enqueue": [Action.QueueEnqueue],
            "dequeue": [Action.QueueDequeue],
        }

        return [action for perm in args for action in permission_actions_map[perm]]

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(id=self._to_resource_id())
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    def allow(self, perm: QueuePermission, *args: QueuePermission) -> QueueRef:
        """Request the required permissions for this queue."""
        # Ensure registration of the resource is complete before requesting permissions.
        str_args = [str(perm)] + [str(permission) for permission in args]
        self._register_policy(*str_args)

        return QueueRef(self.name)


def queue(name: str) -> Queue:
    """
    Create and register a queue.

    If a queue has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Queue, name)  # type: ignore pylint: disable=protected-access
