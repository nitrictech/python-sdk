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

from nitric.proto.nitric.queue.v1 import NitricTask, QueueSendBatchResponse, QueueSendResponse, FailedTask

from examples.queues.failed import queues_failed
from examples.queues.receive import queues_receive
from examples.queues.send import queues_send

from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock


class QueuesExamplesTest(IsolatedAsyncioTestCase):
    async def test_receive_queue(self):
        mock_receive = AsyncMock()

        with patch("nitric.proto.nitric.queue.v1.QueueServiceStub.receive", mock_receive):
            await queues_receive()

        mock_receive.assert_called_once()

    async def test_send_queue(self):
        mock_send = AsyncMock()

        with patch("nitric.proto.nitric.queue.v1.QueueServiceStub.send", mock_send):
            await queues_send()

        mock_send.assert_called_once()

    async def test_failed_queue(self):
        mock_failed = AsyncMock()
        mock_failed.return_value = QueueSendBatchResponse(
            failed_tasks=[
                FailedTask(
                    task=NitricTask(
                        id="1",
                    ),
                    message="failed to send in this test",
                )
            ]
        )

        with patch("nitric.proto.nitric.queue.v1.QueueServiceStub.send_batch", mock_failed):
            await queues_failed()

        mock_failed.assert_called_once()
