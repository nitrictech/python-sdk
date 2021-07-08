from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock, Mock, call

from nitric.faas import ResponseContext, HttpResponseContext, TopicResponseContext, Trigger, TriggerContext
from nitric.proto.nitric.faas.v1 import TriggerRequest, TopicTriggerContext, HttpTriggerContext


class ResponseContextTest(IsolatedAsyncioTestCase):

    # def default_response_no_trigger_context(self):
    #     trigger = Trigger(context=TriggerContext(), data=b'')

    def test_from_wire_http_trigger(self):
        wire_trigger = TriggerRequest(data=b"a byte string", http=HttpTriggerContext())
        trigger = Trigger.from_trigger_request(wire_trigger)
        self.assertTrue(trigger.context.is_http())
        self.assertFalse(trigger.context.is_topic())

    def test_from_wire_topic_trigger(self):
        wire_trigger = TriggerRequest(data=b"a byte string", topic=TopicTriggerContext())
        trigger = Trigger.from_trigger_request(wire_trigger)
        self.assertTrue(trigger.context.is_topic())
        self.assertFalse(trigger.context.is_http())
