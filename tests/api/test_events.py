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
from grpclib import GRPCError, Status

from nitric.api import Events, Event
from nitric.exception import UnknownException
from nitric.proto.nitric.event.v1 import TopicListResponse, NitricTopic, EventPublishRequest, NitricEvent
from nitric.utils import struct_from_dict


class Object(object):
    pass


class EventClientTest(IsolatedAsyncioTestCase):
    async def test_publish(self):
        mock_publish = AsyncMock()
        mock_response = Object()
        mock_response.id = "test-id"
        mock_publish.return_value = mock_response

        payload = {"content": "of event"}

        with patch("nitric.proto.nitric.event.v1.EventServiceStub.publish", mock_publish):
            topic = Events().topic("test-topic")
            event = await topic.publish(Event(payload=payload))

        # Check the returned ID was set on the event
        assert event.id == "test-id"

        # Check expected values were passed to Stub
        # mock_publish.assert_called_once()
        mock_publish.assert_called_once_with(
            event_publish_request=EventPublishRequest(
                topic="test-topic", event=NitricEvent(id=None, payload_type=None, payload=struct_from_dict(payload))
            )
        )

    async def test_publish_dict(self):
        mock_publish = AsyncMock()
        mock_response = Object()
        mock_response.id = "123"
        mock_publish.return_value = mock_response

        payload = {"content": "of event"}

        with patch("nitric.proto.nitric.event.v1.EventServiceStub.publish", mock_publish):
            topic = Events().topic("test-topic")
            await topic.publish(Event(id="123", payload=payload))

        mock_publish.assert_called_once_with(
            event_publish_request=EventPublishRequest(
                topic="test-topic", event=NitricEvent(id="123", payload=struct_from_dict(payload), payload_type=None)
            )
        )

    async def test_publish_invalid_type(self):
        mock_publish = AsyncMock()
        mock_response = Object()
        mock_response.id = "test-id"
        mock_publish.return_value = mock_response

        payload = {"content": "of event"}

        with patch("nitric.proto.nitric.event.v1.EventServiceStub.publish", mock_publish):
            topic = Events().topic("test-topic")
            with pytest.raises(Exception):
                await topic.publish((1, 2, 3))

    async def test_publish_none(self):
        mock_publish = AsyncMock()
        mock_response = Object()
        mock_response.id = "123"
        mock_publish.return_value = mock_response

        payload = {"content": "of event"}

        with patch("nitric.proto.nitric.event.v1.EventServiceStub.publish", mock_publish):
            topic = Events().topic("test-topic")
            await topic.publish()

        # Check expected values were passed to Stub
        mock_publish.assert_called_once_with(
            event_publish_request=EventPublishRequest(
                topic="test-topic", event=NitricEvent(id=None, payload=Struct(), payload_type=None)
            )
        )

    async def test_get_topics(self):
        mock_list_topics = AsyncMock()
        mock_response = TopicListResponse(
            topics=[
                NitricTopic(name="test-topic1"),
                NitricTopic(name="test-topic2"),
            ]
        )
        mock_list_topics.return_value = mock_response

        payload = {"content": "of event"}

        with patch("nitric.proto.nitric.event.v1.TopicServiceStub.list", mock_list_topics):
            topics = await Events().topics()

        # Check expected values were passed to Stub
        mock_list_topics.assert_called_once()
        self.assertEqual(2, len(topics))
        self.assertEqual(topics[0].name, "test-topic1")
        self.assertEqual(topics[1].name, "test-topic2")

    async def test_publish_error(self):
        mock_publish = AsyncMock()
        mock_publish.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitric.proto.nitric.event.v1.EventServiceStub.publish", mock_publish):
            with pytest.raises(UnknownException) as e:
                await Events().topic("test-topic").publish(Event(payload={}))

    async def test_get_topics_error(self):
        mock_get_topics = AsyncMock()
        mock_get_topics.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitric.proto.nitric.event.v1.TopicServiceStub.list", mock_get_topics):
            with pytest.raises(UnknownException) as e:
                await Events().topics()
