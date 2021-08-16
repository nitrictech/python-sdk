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
