from typing import List

from nitricapi.nitric.queue.v1 import NitricTask, QueueSendBatchResponse, QueueSendResponse, FailedTask

from examples.queues.failed import queues_failed
from examples.queues.receive import queues_receive
from examples.queues.send import queues_send

from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock


class QueuesExamplesTest(IsolatedAsyncioTestCase):
    async def test_receive_queue(self):
        mock_receive = AsyncMock()

        with patch("nitricapi.nitric.queue.v1.QueueServiceStub.receive", mock_receive):
            await queues_receive()

        mock_receive.assert_called_once()

    async def test_send_queue(self):
        mock_send = AsyncMock()

        with patch("nitricapi.nitric.queue.v1.QueueServiceStub.send", mock_send):
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

        with patch("nitricapi.nitric.queue.v1.QueueServiceStub.send_batch", mock_failed):
            await queues_failed()

        mock_failed.assert_called_once()
