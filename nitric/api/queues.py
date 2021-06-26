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
from typing import List, Union

from betterproto.lib.google.protobuf import Struct

from nitric.api._utils import new_default_channel
from nitric.proto.nitric.queue.v1 import QueueStub, NitricTask, FailedTask as WireFailedTask
from dataclasses import dataclass, field


@dataclass(frozen=True, order=True)
class Task(object):
    """Represents a NitricTask."""

    id: str = field(default=None)
    payload_type: str = field(default=None)
    payload: dict = field(default_factory=dict)
    lease_id: str = field(default=None)


@dataclass(frozen=True, order=True)
class FailedTask(Task):
    """Represents a failed queue publish for an event."""

    message: str = field(default="")


def _task_to_wire(task: Task) -> NitricTask:
    """
    Convert a Nitric Task to a Nitric Queue Task.

    :param task: to convert
    :return: converted task
    """
    return NitricTask(
        id=task.id,
        payload_type=task.payload_type,
        payload=Struct().from_dict(task.payload),
    )


def _wire_to_task(task: NitricTask) -> Task:
    """
    Convert a Nitric Queue Task (protobuf) to a Nitric Task (python SDK).

    :param task: to convert
    :return: converted task
    """
    return Task(
        id=task.id,
        payload_type=task.payload_type,
        payload=task.payload.to_dict(),
        lease_id=task.lease_id,
    )


def _wire_to_failed_task(failed_task: WireFailedTask) -> FailedTask:
    """
    Convert a queue task that failed to push into a Failed Task object.

    :param failed_task: the failed task
    :return: the Failed Task with failure message
    """
    task = _wire_to_task(failed_task.task)

    return FailedTask(
        id=task.id,
        payload_type=task.payload_type,
        payload=task.payload,
        lease_id=task.lease_id,
        message=failed_task.message,
    )


class QueueClient(object):
    """
    Nitric generic publish/subscribe tasking client.

    This client insulates application code from stack specific task/topic operations or SDKs.
    """

    def __init__(self, queue: str):
        """Construct a Nitric Queue Client."""
        self.queue = queue
        self._stub = QueueStub(channel=new_default_channel())

    async def send_batch(
        self, tasks: List[Union[Task, dict]] = None, raise_on_failure: bool = True
    ) -> List[FailedTask]:
        """
        Push a collection of tasks to a queue, which can be retrieved by other services.

        :param tasks: The tasks to push to the queue
        :param raise_on_failure: Whether to raise an exception when one or more tasks fails to send
        :return: PushResponse containing a list containing details of any messages that failed to publish.
        """
        if tasks is None:
            tasks = []

        wire_tasks = [_task_to_wire(Task(**task) if isinstance(task, dict) else task) for task in tasks]

        response = await self._stub.send_batch(queue=self.queue, tasks=wire_tasks)

        return [_wire_to_failed_task(failed_task) for failed_task in response.failed_tasks]

    def receive(self, depth: int = None) -> List[Task]:
        """
        Pop 1 or more items from the specified queue up to the depth limit.

        Queue items are Nitric Tasks that are leased for a limited period of time, where they may be worked on.
        Once complete or failed they must be acknowledged using the request specific leaseId.

        If the lease on a queue item expires before it is acknowledged or the lease is extended the task will be
        returned to the queue for reprocessing.

        identifier.
        :param depth: The maximum number of queue items to return. Default: 1, Min: 1.
        :return: Queue items popped from the specified queue.
        """
        # Set the default and minimum depth to 1.
        if depth is None or depth < 1:
            depth = 1

        response = await self._stub.receive(queue=self.queue, depth=depth)

        # Map the response protobuf response items to Python SDK Nitric Queue Items
        return [_wire_to_task(item) for item in response.items]
