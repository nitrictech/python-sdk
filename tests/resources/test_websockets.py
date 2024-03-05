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

from nitric.proto.resources.v1 import Action, PolicyResource, ResourceDeclareRequest, ResourceIdentifier, ResourceType
from nitric.proto.websockets.v1 import WebsocketSendRequest
from nitric.resources import Websocket, websocket
from nitric.resources.websockets import WebsocketRef

# pylint: disable=protected-access,missing-function-docstring,missing-class-docstring


class Object(object):
    pass


class WebsocketClientTest(IsolatedAsyncioTestCase):
    async def test_send(self):
        mock_send = AsyncMock()
        mock_response = Object()
        mock_send.return_value = mock_response
        test_data = b"test-data"

        with patch("nitric.proto.websockets.v1.WebsocketStub.send_message", mock_send):
            await WebsocketRef().send("test-socket", "test-connection", test_data)

        # Check expected values were passed to Stub
        mock_send.assert_called_once_with(
            websocket_send_request=WebsocketSendRequest(
                socket_name="test-socket", connection_id="test-connection", data=test_data
            )
        )


class MockAsyncChannel:
    def __init__(self):
        self.send = AsyncMock()
        self.close = Mock()
        self.done = Mock()


class WebsocketTest(IsolatedAsyncioTestCase):
    def test_create(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            websocket("test-websocket")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[Action.WebsocketManage],
                    resources=[ResourceIdentifier(type=ResourceType.Websocket, name="test-websocket")],
                ),
            )
        )


class WebsocketClientTest(IsolatedAsyncioTestCase):
    async def test_send(self):
        mock_send = AsyncMock()
        mock_response = Object()
        mock_send.return_value = mock_response
        test_data = b"test-data"

        with patch("nitric.proto.websockets.v1.WebsocketStub.send_message", mock_send):
            await Websocket("testing").send("test-connection", test_data)

        # Check expected values were passed to Stub
        mock_send.assert_called_once_with(
            websocket_send_request=WebsocketSendRequest(
                socket_name="testing", connection_id="test-connection", data=test_data
            )
        )
