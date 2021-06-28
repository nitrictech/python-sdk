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

from betterproto.lib.google.protobuf import Struct

from nitric.api import QueueClient, Task
from nitric.api._utils import _struct_from_dict


class Object(object):
    pass


class QueueClientTest(IsolatedAsyncioTestCase):
    async def test_send(self):
        mock_send = AsyncMock()
        mock_response = Object()
        mock_send.return_value = mock_response

        payload = {"content": "of task"}

        with patch("nitric.proto.nitric.queue.v1.QueueStub.send", mock_send):
            queue = QueueClient().queue("test-queue")
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
            queue = QueueClient().queue("test-queue")
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
            queue = QueueClient().queue("test-queue")
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
            queue = QueueClient().queue("test-queue")
            await queue.send()

        # Check expected values were passed to Stub
        mock_send.assert_called_once()
        assert mock_send.call_args.kwargs["queue"] == "test-queue"
        assert mock_send.call_args.kwargs["task"].id is None
        assert mock_send.call_args.kwargs["task"].payload_type is None
        assert mock_send.call_args.kwargs["task"].payload == Struct()
