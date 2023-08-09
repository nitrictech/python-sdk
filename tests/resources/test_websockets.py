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

from nitric.faas import WebsocketContext
from nitric.proto.nitric.resource.v1 import Action, ResourceDeclareRequest, Resource, ResourceType, PolicyResource

from nitric.resources import websocket


class Object(object):
    pass


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

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            websocket("test-websocket")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                resource=Resource(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[Resource(type=ResourceType.Function)],
                    actions=[Action.WebsocketManage],
                    resources=[Resource(type=ResourceType.Websocket, name="test-websocket")],
                ),
            )
        )
