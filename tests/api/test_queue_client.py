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
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock

import pytest
from betterproto.lib.google.protobuf import Struct

from nitric.api import Queueing, Task
from nitric.proto.nitric.queue.v1 import QueueReceiveResponse, NitricTask, QueueCompleteResponse
from nitric.utils import _struct_from_dict


class Object(object):
    pass


class QueueClientTest(IsolatedAsyncioTestCase):
    async def test_send(self):
        mock_send = AsyncMock()
        mock_response = Object()
        mock_send.return_value = mock_response

        payload = {"content": "of task"}

        with patch("nitric.proto.nitric.queue.v1.QueueStub.send", mock_send):
            queue = Queueing().queue("test-queue")
            await queue.send(Task(payload=payload))

        # Check expected values were passed to Stub
        mock_send.assert_called_once()
        assert mock_send.call_args.kwargs["queue"] == "test-queue"
        assert mock_send.call_args.kwargs["task"].id is None
        assert mock_send.call_args.kwargs["task"].payload_type is None
        assert len(mock_send.call_args.kwargs["task"].payload.fields) == 1
        assert mock_send.call_args.kwargs["task"].payload == _struct_from_dict(payload)

    async def test_send_dict(self):
        mock_send = AsyncMock()
        mock_response = Object()
        mock_send.return_value = mock_response

        payload = {"content": "of task"}

        with patch("nitric.proto.nitric.queue.v1.QueueStub.send", mock_send):
            queue = Queueing().queue("test-queue")
            await queue.send({"id": "123", "payload": payload})

        # Check expected values were passed to Stub
        mock_send.assert_called_once()
        assert mock_send.call_args.kwargs["queue"] == "test-queue"
        assert mock_send.call_args.kwargs["task"].id == "123"
        assert mock_send.call_args.kwargs["task"].payload_type is None
        assert len(mock_send.call_args.kwargs["task"].payload.fields) == 1
        assert mock_send.call_args.kwargs["task"].payload == _struct_from_dict(payload)

    async def test_publish_invalid_type(self):
        mock_send = AsyncMock()
        mock_response = Object()
        mock_send.return_value = mock_response

        payload = {"content": "of task"}

        with patch("nitric.proto.nitric.queue.v1.QueueStub.send", mock_send):
            queue = Queueing().queue("test-queue")
            try:
                await queue.send((1, 2, 3))
                assert False
            except AttributeError:
                # Exception raised if expected duck type attributes are missing
                assert True

    async def test_send_none(self):
        mock_send = AsyncMock()
        mock_response = Object()
        mock_send.return_value = mock_response

        payload = {"content": "of task"}

        with patch("nitric.proto.nitric.queue.v1.QueueStub.send", mock_send):
            queue = Queueing().queue("test-queue")
            await queue.send()

        # Check expected values were passed to Stub
        mock_send.assert_called_once()
        assert mock_send.call_args.kwargs["queue"] == "test-queue"
        assert mock_send.call_args.kwargs["task"].id is None
        assert mock_send.call_args.kwargs["task"].payload_type is None
        assert mock_send.call_args.kwargs["task"].payload == Struct()

    async def test_receive(self):
        payload = {"content": "of task"}

        mock_receive = AsyncMock()
        mock_receive.return_value = QueueReceiveResponse(
            tasks=[
                NitricTask(
                    id="test-task", lease_id="test-lease", payload_type="test-type", payload=_struct_from_dict(payload)
                )
            ]
        )

        with patch("nitric.proto.nitric.queue.v1.QueueStub.receive", mock_receive):
            queueing = Queueing()
            queue = queueing.queue("test-queue")
            (task,) = await queue.receive()

        # Check expected values were passed to Stub
        mock_receive.assert_called_once()
        self.assertEqual("test-queue", mock_receive.call_args.kwargs["queue"])
        self.assertEqual(1, mock_receive.call_args.kwargs["depth"])

        self.assertEqual("test-task", task.id)
        self.assertEqual("test-lease", task.lease_id)
        self.assertEqual("test-type", task.payload_type)
        self.assertEqual(payload, task.payload)
        self.assertEqual(queueing, task._queueing)
        self.assertEqual(queue, task._queue)

    async def test_receive_custom_limit(self):
        mock_receive = AsyncMock()
        mock_receive.return_value = QueueReceiveResponse(
            tasks=[
                NitricTask(
                    id="test-task",
                    lease_id="test-lease",
                    payload_type="test-type",
                    payload=_struct_from_dict({"content": "of task"}),
                )
            ]
        )

        with patch("nitric.proto.nitric.queue.v1.QueueStub.receive", mock_receive):
            await Queueing().queue("test-queue").receive(limit=3)  # explicitly set a limit

        # Check expected values were passed to Stub
        mock_receive.assert_called_once()
        self.assertEqual(3, mock_receive.call_args.kwargs["depth"])

    async def test_receive_below_minimum_limit(self):
        mock_receive = AsyncMock()
        mock_receive.return_value = QueueReceiveResponse(
            tasks=[
                NitricTask(
                    id="test-task",
                    lease_id="test-lease",
                    payload_type="test-type",
                    payload=_struct_from_dict({"content": "of task"}),
                )
            ]
        )

        with patch("nitric.proto.nitric.queue.v1.QueueStub.receive", mock_receive):
            await Queueing().queue("test-queue").receive(limit=0)  # explicitly set a limit

        # Check expected values were passed to Stub
        mock_receive.assert_called_once()
        self.assertEqual(1, mock_receive.call_args.kwargs["depth"])

    async def test_receive_task_without_payload(self):
        mock_receive = AsyncMock()
        mock_receive.return_value = QueueReceiveResponse(tasks=[NitricTask(id="test-task", lease_id="test-lease")])

        with patch("nitric.proto.nitric.queue.v1.QueueStub.receive", mock_receive):
            (task,) = await Queueing().queue("test-queue").receive(limit=0)  # explicitly set a limit

        # Verify that an empty dict is returned for payload and no payload type.
        mock_receive.assert_called_once()
        self.assertEquals("", task.payload_type)
        self.assertEquals({}, task.payload)

    async def test_complete(self):
        mock_complete = AsyncMock()
        mock_complete.return_value = QueueCompleteResponse()

        queueing = Queueing()
        task = Task(lease_id="test-lease", _queueing=queueing, _queue=queueing.queue("test-queue"))

        with patch("nitric.proto.nitric.queue.v1.QueueStub.complete", mock_complete):
            await task.complete()

        # Check expected values were passed to Stub
        mock_complete.assert_called_once()
        self.assertEqual("test-queue", mock_complete.call_args.kwargs["queue"])
        self.assertEqual("test-lease", mock_complete.call_args.kwargs["lease_id"])

    async def test_complete_unleased_task(self):
        mock_complete = AsyncMock()
        mock_complete.return_value = QueueCompleteResponse()

        queueing = Queueing()
        # lease_id omitted.
        task = Task(_queueing=queueing, _queue=queueing.queue("test-queue"))

        with patch("nitric.proto.nitric.queue.v1.QueueStub.complete", mock_complete):
            with pytest.raises(Exception) as e:
                await task.complete()
            self.assertIn("Tasks must be received", str(e.value))
