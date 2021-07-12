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
from unittest.mock import patch, AsyncMock, Mock, call

from nitric.faas import faas
from nitric.proto.nitric.faas.v1 import (
    ServerMessage,
    InitResponse,
    ClientMessage,
    InitRequest,
    TriggerRequest,
    TopicTriggerContext,
    HttpTriggerContext,
)


class Object(object):
    pass


class MockAsyncChannel:
    def __init__(self):
        self.send = AsyncMock()
        self.close = Mock()
        self.done = Mock()


class EventClientTest(IsolatedAsyncioTestCase):
    def test_start_handler_is_passed_to_register(self):
        mock_register = AsyncMock()
        mock_handler = Mock()

        with patch("nitric.faas.faas._register_faas_worker", mock_register):
            faas.start(mock_handler)

        mock_register.assert_called_once_with(mock_handler)

    def test_start_starts_event_loop(self):
        mock_register, mock_registered, mock_asyncio_run = [Mock() for i in range(3)]
        mock_register.return_value = mock_registered
        mock_handler = Mock()

        with patch("nitric.faas.faas._register_faas_worker", mock_register):
            with patch("asyncio.run", mock_asyncio_run):
                faas.start(mock_handler)

        mock_asyncio_run.assert_called_once_with(mock_registered)
        mock_register.assert_called_once_with(mock_handler)

    async def test_init(self):
        mock_handler = Mock()
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [ServerMessage(init_response=InitResponse())]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitric.proto.nitric.faas.v1.FaasStub.trigger_stream", mock_stream
        ), patch("nitric.faas.faas.new_default_channel", mock_grpc_channel):
            await faas._register_faas_worker(mock_handler)

        # gRPC channel created
        mock_grpc_channel.assert_called_once()
        # Async request channel created
        mock_async_channel_init.assert_called_once_with(close=True)
        # Send the init request
        mock_async_chan.send.assert_called_once_with(ClientMessage(init_request=InitRequest()))
        # accept the init response from server
        assert 1 == stream_calls
        # mock handler not called
        mock_handler.assert_not_called()

    async def test_trigger_sync_handler(self):
        mock_handler = Mock()
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [
                ServerMessage(
                    trigger_request=TriggerRequest(
                        data=b"a byte string",
                        topic=TopicTriggerContext(),
                    )
                )
            ]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitric.proto.nitric.faas.v1.FaasStub.trigger_stream", mock_stream
        ), patch("nitric.faas.faas.new_default_channel", mock_grpc_channel):
            await faas._register_faas_worker(mock_handler)

        # accept the init response from server
        assert 1 == stream_calls
        # mock handler not called
        mock_handler.assert_called_once()

    async def test_trigger_async_handler(self):
        mock_handler = AsyncMock()
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [
                ServerMessage(
                    trigger_request=TriggerRequest(
                        data=b"a byte string",
                        topic=TopicTriggerContext(),
                    )
                )
            ]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitric.proto.nitric.faas.v1.FaasStub.trigger_stream", mock_stream
        ), patch("nitric.faas.faas.new_default_channel", mock_grpc_channel):
            await faas._register_faas_worker(mock_handler)

        # accept the init response from server
        assert 1 == stream_calls
        # mock handler not called
        mock_handler.assert_called_once()

    async def test_failing_topic_handler(self):
        mock_handler = Mock()
        mock_handler.side_effect = Exception("test exception")
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [
                ServerMessage(trigger_request=TriggerRequest(data=b"a byte string", topic=TopicTriggerContext()))
            ]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitric.proto.nitric.faas.v1.FaasStub.trigger_stream", mock_stream
        ), patch("nitric.faas.faas.new_default_channel", mock_grpc_channel):
            await faas._register_faas_worker(mock_handler)

        # accept the trigger response from server
        assert 1 == stream_calls
        # handler called
        mock_handler.assert_called_once()
        # init, trigger response, done, close
        self.assertEqual(2, len(mock_async_chan.send.mock_calls))
        args, kwargs = mock_async_chan.send.call_args_list[1]
        (message,) = args
        # Success status in response should be False
        self.assertFalse(message.trigger_response.topic.success)

    async def test_failing_http_handler(self):
        mock_handler = Mock()
        mock_handler.side_effect = Exception("test exception")
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [
                ServerMessage(
                    trigger_request=TriggerRequest(
                        data=b"a byte string", http=HttpTriggerContext(method="GET", path="/")
                    )
                )
            ]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitric.proto.nitric.faas.v1.FaasStub.trigger_stream", mock_stream
        ), patch("nitric.faas.faas.new_default_channel", mock_grpc_channel):
            await faas._register_faas_worker(mock_handler)

        # accept the trigger response from server
        assert 1 == stream_calls
        # handler called
        mock_handler.assert_called_once()
        # init, trigger response
        self.assertEqual(2, len(mock_async_chan.send.mock_calls))
        args, kwargs = mock_async_chan.send.call_args_list[1]
        (message,) = args
        # Success status in response should be False
        self.assertEqual(500, message.trigger_response.http.status)

    async def test_handler_bytes_response(self):
        mock_handler = Mock()
        mock_handler.return_value = b"some bytes"
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [
                ServerMessage(
                    trigger_request=TriggerRequest(
                        data=b"",
                        topic=TopicTriggerContext(),
                    )
                )
            ]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitric.proto.nitric.faas.v1.FaasStub.trigger_stream", mock_stream
        ), patch("nitric.faas.faas.new_default_channel", mock_grpc_channel):
            await faas._register_faas_worker(mock_handler)

            # accept the trigger response from server
            assert 1 == stream_calls
            # handler called
            mock_handler.assert_called_once()
            # init, trigger response
            self.assertEqual(2, len(mock_async_chan.send.mock_calls))
            args, kwargs = mock_async_chan.send.call_args_list[1]
            (message,) = args
            # Response bytes should be unmodified.
            self.assertEqual(b"some bytes", message.trigger_response.data)

    async def test_handler_dict_response(self):
        mock_handler = Mock()
        mock_handler.return_value = {"key": "value", "num": 123}
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [
                ServerMessage(
                    trigger_request=TriggerRequest(
                        data=b"",
                        http=HttpTriggerContext(),
                    )
                )
            ]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitric.proto.nitric.faas.v1.FaasStub.trigger_stream", mock_stream
        ), patch("nitric.faas.faas.new_default_channel", mock_grpc_channel):
            await faas._register_faas_worker(mock_handler)

            # accept the trigger response from server
            assert 1 == stream_calls
            # handler called
            mock_handler.assert_called_once()
            # init, trigger response
            self.assertEqual(2, len(mock_async_chan.send.mock_calls))
            args, kwargs = mock_async_chan.send.call_args_list[1]
            (message,) = args
            # Response should be returned as JSON
            self.assertEqual(b'{"key": "value", "num": 123}', message.trigger_response.data)
            self.assertEqual({"Content-Type": "application/json"}, message.trigger_response.http.headers)

    async def test_handler_string_response(self):
        mock_handler = Mock()
        mock_handler.return_value = "a test string"
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [
                ServerMessage(
                    trigger_request=TriggerRequest(
                        data=b"",
                        topic=TopicTriggerContext(),
                    )
                )
            ]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitric.proto.nitric.faas.v1.FaasStub.trigger_stream", mock_stream
        ), patch("nitric.faas.faas.new_default_channel", mock_grpc_channel):
            await faas._register_faas_worker(mock_handler)

            # accept the trigger response from server
            assert 1 == stream_calls
            # handler called
            mock_handler.assert_called_once()
            # init, trigger response
            self.assertEqual(2, len(mock_async_chan.send.mock_calls))
            args, kwargs = mock_async_chan.send.call_args_list[1]
            (message,) = args
            # Response string should be converted to bytes
            self.assertEqual(b"a test string", message.trigger_response.data)
