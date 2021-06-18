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
from typing import List

from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct

from nitric.api._base_client import BaseClient
from nitric.api.models import FailedTask, Task
from nitric.proto import queue
from nitric.proto import queue_service


class PushResponse(object):
    """Represents the result of a Queue Push."""

    def __init__(self, failed_tasks: List[FailedTask]):
        """Construct a Push Response."""
        self.failed_tasks = failed_tasks


class QueueClient(BaseClient):
    """
    Nitric generic publish/subscribe tasking client.

    This client insulates application code from stack specific task/topic operations or SDKs.
    """

    def __init__(self):
        """Construct a Nitric Queue Client."""
        super(self.__class__, self).__init__()
        self._stub = queue_service.QueueStub(self._channel)

    def _task_to_wire(self, task: Task) -> queue.NitricTask:
        """
        Convert a Nitric Task to a Nitric Queue Task.

        :param task: to convert
        :return: converted task
        """
        payload_struct = Struct()
        payload_struct.update(task.payload)

        return queue.NitricTask(
            id=task.task_id,
            payload_type=task.payload_type,
            payload=payload_struct,
        )

    def _wire_to_task(self, task: queue.NitricTask) -> Task:
        """
        Convert a Nitric Queue Task (protobuf) to a Nitric Task (python SDK).

        :param task: to convert
        :return: converted task
        """
        return Task(
            task_id=task.id,
            payload_type=task.payload_type,
            payload=MessageToDict(task.payload),
            lease_id=task.lease_id,
        )

    def _wire_to_failed_task(self, failed_task: queue.FailedTask) -> FailedTask:
        """
        Convert a queue task that failed to push into a Failed Task object.

        :param failed_task: the failed task
        :return: the Failed Task with failure message
        """
        task = self._wire_to_task(failed_task.task)

        return FailedTask(
            task_id=task.task_id,
            payload_type=task.payload_type,
            payload=task.payload,
            lease_id=task.lease_id,
            message=failed_task.message,
        )

    def send_batch(self, queue_name: str, tasks: List[Task] = None) -> PushResponse:
        """
        Push a collection of tasks to a queue, which can be retrieved by other services.

        :param queue_name: the name of the queue to publish to
        :param tasks: The tasks to push to the queue
        :return: PushResponse containing a list containing details of any messages that failed to publish.
        """
        if tasks is None:
            tasks = []
        wire_tasks = map(self._task_to_wire, tasks)

        request = queue.QueueSendBatchRequest(queue=queue_name, tasks=wire_tasks)

        response: queue.QueueSendBatchResponse = self._exec("SendBatch", request)

        failed_tasks = map(self._wire_to_failed_task, response.failedMessages)

        return PushResponse(failed_tasks=list(failed_tasks))

    def receive(self, queue_name: str, depth: int = None) -> List[Task]:
        """
        Pop 1 or more items from the specified queue up to the depth limit.

        Queue items are Nitric Tasks that are leased for a limited period of time, where they may be worked on.
        Once complete or failed they must be acknowledged using the request specific leaseId.

        If the lease on a queue item expires before it is acknowledged or the lease is extended the task will be
        returned to the queue for reprocessing.

        :param queue_name: Nitric name for the queue. This will be automatically resolved to the provider specific
        identifier.
        :param depth: The maximum number of queue items to return. Default: 1, Min: 1.
        :return: Queue items popped from the specified queue.
        """
        # Set the default and minimum depth to 1.
        if depth is None or depth < 1:
            depth = 1

        request = queue.QueueReceiveRequest(queue=queue_name, depth=depth)

        response: queue.QueueReceiveResponse = self._exec("Receive", request)

        # Map the response protobuf response items to Python SDK Nitric Queue Items
        return [self._wire_to_task(item) for item in response.items]
