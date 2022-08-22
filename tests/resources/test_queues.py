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
from nitric.resources import queue

from nitricapi.nitric.resource.v1 import Action
from nitric.utils import _struct_from_dict


class Object(object):
    pass


class QueueTest(IsolatedAsyncioTestCase):
    async def test_create_allow_sending(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await queue("test-queue").allow(["sending"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()
        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-queue")
        self.assertListEqual(
            mock_declare.call_args.kwargs["policy"].actions,
            [
                Action.QueueSend,
                Action.QueueList,
                Action.QueueDetail,
            ],
        )

    async def test_create_allow_receiving(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await queue("test-queue").allow(["receiving"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()

        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-queue")
        self.assertListEqual(
            mock_declare.call_args.kwargs["policy"].actions,
            [
                Action.QueueReceive,
                Action.QueueList,
                Action.QueueDetail,
            ],
        )

    async def test_create_allow_all(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await queue("test-queue").allow(["sending", "receiving"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()
        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-queue")
        self.assertListEqual(
            mock_declare.call_args.kwargs["policy"].actions,
            [
                Action.QueueSend,
                Action.QueueList,
                Action.QueueDetail,
                Action.QueueReceive,
                Action.QueueList,
                Action.QueueDetail,
            ],
        )

    async def test_send_dict(self):
        mock_send = AsyncMock()
        mock_declare = AsyncMock()

        mock_response = Object()
        mock_send.return_value = mock_response

        payload = {"content": "of task"}

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            with patch("nitricapi.nitric.queue.v1.QueueServiceStub.send", mock_send):
                q = await queue("test-queue").allow(["sending"])
                await q.send({"id": "123", "payload": payload})

        # Check expected values were passed to Stub
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.kwargs["queue"], "test-queue")
        self.assertEqual(mock_send.call_args.kwargs["task"].id, "123")
        self.assertIsNone(mock_send.call_args.kwargs["task"].payload_type)
        self.assertEqual(len(mock_send.call_args.kwargs["task"].payload.fields), 1)
        self.assertEqual(mock_send.call_args.kwargs["task"].payload, _struct_from_dict(payload))
