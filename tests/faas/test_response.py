from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock, Mock, call

from nitric.faas import ResponseContext, HttpResponseContext, TopicResponseContext


class ResponseContextTest(IsolatedAsyncioTestCase):
    def test_is_http(self):
        context = ResponseContext(context=HttpResponseContext())
        self.assertTrue(context.is_http())
        self.assertFalse(context.is_topic())

    def test_is_topic(self):
        context = ResponseContext(context=TopicResponseContext())
        self.assertTrue(context.is_topic())
        self.assertFalse(context.is_http())
