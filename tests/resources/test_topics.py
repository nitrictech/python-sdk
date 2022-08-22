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
from unittest.mock import patch, AsyncMock, Mock
from nitric.resources import topic

from nitricapi.nitric.resource.v1 import Action
from nitric.utils import _struct_from_dict


class Object(object):
    pass


class MockAsyncChannel:
    def __init__(self):
        self.send = AsyncMock()
        self.close = Mock()
        self.done = Mock()


class TopicTest(IsolatedAsyncioTestCase):
    async def test_create_allow_publishing(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await topic("test-topic").allow(["publishing"])

        # Check expected values were passed to Stub
        self.assertEqual(len(mock_declare.mock_calls), 2)

        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-topic")
        self.assertListEqual(mock_declare.call_args.kwargs["policy"].actions, [Action.TopicEventPublish])

    async def test_publish_dict(self):
        mock_publish = AsyncMock()
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_response.id = "123"
        mock_publish.return_value = mock_response

        payload = {"content": "of event"}

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            with patch("nitricapi.nitric.event.v1.EventServiceStub.publish", mock_publish):
                t = await topic("test-topic").allow(["publishing"])
                await t.publish({"id": "123", "payload": payload})

        # Check expected values were passed to Stub
        mock_publish.assert_called_once()
        assert mock_publish.call_args.kwargs["topic"] == "test-topic"
        assert mock_publish.call_args.kwargs["event"].id == "123"
        assert mock_publish.call_args.kwargs["event"].payload_type is None
        assert len(mock_publish.call_args.kwargs["event"].payload.fields) == 1
        assert mock_publish.call_args.kwargs["event"].payload == _struct_from_dict(payload)
