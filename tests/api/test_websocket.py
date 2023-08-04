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
from nitric.proto.nitric.websocket.v1 import (
    WebsocketSendRequest,
)
from nitric.api import Websocket


class Object(object):
    pass


class WebsocketClientTest(IsolatedAsyncioTestCase):
    async def test_send(self):
        mock_send = AsyncMock()
        mock_response = Object()
        mock_send.return_value = mock_response
        test_data = b"test-data"

        contents = b"some text as bytes"

        with patch("nitric.proto.nitric.websocket.v1.WebsocketServiceStub.send", mock_send):
            await Websocket().send("test-socket", "test-connection", test_data)

        # Check expected values were passed to Stub
        mock_send.assert_called_once_with(
            websocket_send_request=WebsocketSendRequest(
                socket="test-socket", connection_id="test-connection", data=test_data
            )
        )
