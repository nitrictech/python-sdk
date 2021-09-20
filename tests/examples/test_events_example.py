from examples.events.publish import events_publish
from examples.events.event_ids import events_event_ids

from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock


class EventsExamplesTest(IsolatedAsyncioTestCase):
    async def test_publish_topic(self):
        mock_publish = AsyncMock()

        with patch("nitricapi.nitric.event.v1.EventServiceStub.publish", mock_publish):
            await events_publish()

        mock_publish.assert_called_once()

    async def test_event_id_publish(self):
        mock_publish = AsyncMock()

        with patch("nitricapi.nitric.event.v1.EventServiceStub.publish", mock_publish):
            await events_event_ids()

        mock_publish.assert_called_once()
