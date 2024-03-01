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
from unittest.mock import AsyncMock, Mock, patch

import pytest
from grpclib import GRPCError, Status

from nitric.exception import UnknownException
from nitric.proto.resources.v1 import Action, PolicyResource, ResourceDeclareRequest, ResourceIdentifier, ResourceType
from nitric.proto.topics.v1 import TopicMessage, TopicPublishRequest
from nitric.resources import topic
from nitric.resources.topics import TopicRef
from nitric.utils import struct_from_dict

# pylint: disable=protected-access,missing-function-docstring,missing-class-docstring


class Object(object):
    pass


class EventClientTest(IsolatedAsyncioTestCase):
    async def test_publish(self):
        mock_publish = AsyncMock()
        mock_response = Object()
        mock_publish.return_value = mock_response

        payload = {"content": "of event"}

        with patch("nitric.proto.topics.v1.TopicsStub.publish", mock_publish):
            topic = TopicRef("test-topic")
            await topic.publish(payload)

        # Check expected values were passed to Stub
        # mock_publish.assert_called_once()
        mock_publish.assert_called_once_with(
            topic_publish_request=TopicPublishRequest(
                topic_name="test-topic", message=TopicMessage(struct_payload=struct_from_dict(payload))
            )
        )

    async def test_publish_invalid_type(self):
        mock_publish = AsyncMock()
        mock_response = Object()
        mock_publish.return_value = mock_response

        with patch("nitric.proto.topics.v1.TopicsStub.publish", mock_publish):
            topic = TopicRef("test-topic")
            with pytest.raises(ValueError):
                await topic.publish((1, 2, 3))

    async def test_publish_error(self):
        mock_publish = AsyncMock()
        mock_publish.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitric.proto.topics.v1.TopicsStub.publish", mock_publish):
            with pytest.raises(UnknownException):
                await TopicRef("test-topic").publish({})


class Object(object):
    pass


class MockAsyncChannel:
    def __init__(self):
        self.send = AsyncMock()
        self.close = Mock()
        self.done = Mock()


class TopicTest(IsolatedAsyncioTestCase):
    def test_create_allow_publishing(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            topic("test-topic").allow("publish")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[Action.TopicPublish],
                    resources=[ResourceIdentifier(type=ResourceType.Topic, name="test-topic")],
                ),
            )
        )
