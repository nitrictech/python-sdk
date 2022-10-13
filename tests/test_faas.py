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

import pytest

from nitric.faas import start, FunctionServer, HttpContext, compose_middleware, HttpResponse, FaasWorkerOptions

from nitricapi.nitric.faas.v1 import (
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
    async def test_compose_middleware(self):
        async def middleware(ctx: HttpContext, next) -> HttpContext:
            ctx.res.status = 401
            return await next(ctx)

        async def handler(ctx: HttpContext) -> HttpContext:
            ctx.res.body = "some text"
            return ctx

        composed = compose_middleware(middleware, handler)

        ctx = HttpContext(response=HttpResponse(), request=None)
        result = await composed(ctx)
        assert result.res.status == 401

    def test_start_with_one_handler(self):
        mock_server_constructor = Mock()
        mock_server = Object()
        mock_server.start = Mock()
        mock_server_constructor.return_value = mock_server

        mock_handler = Mock()
        with patch("nitric.faas.FunctionServer", mock_server_constructor):
            start(mock_handler)

        # It should construct the function server
        mock_server_constructor.assert_called_once()
        # It should start the server, with the handler
        mock_server.start.assert_called_once_with(mock_handler)

    def test_start_without_handlers(self):
        mock_server_constructor = Mock()

        with patch("nitric.faas.FunctionServer", mock_server_constructor):
            with pytest.raises(Exception):
                start()

        # It should not construct the function server
        mock_server_constructor.assert_not_called()

    def test_start_with_multiple_handler(self):
        mock_server_constructor = Mock()
        mock_server = Object()
        mock_server.start = Mock()
        mock_server_constructor.return_value = mock_server

        mock_handler = Mock()
        with patch("nitric.faas.FunctionServer", mock_server_constructor):
            start(mock_handler, mock_handler)

        # It should construct the function server
        mock_server_constructor.assert_called_once()
        # It should start the server, with the handler
        mock_server.start.assert_called_once_with(mock_handler, mock_handler)

    async def test_start_starts_event_loop(self):
        mock_compose, mock_middleware, mock_handler = [Mock() for i in range(3)]
        mock_run_coroutine, mock_run = [AsyncMock() for i in range(2)]
        mock_compose.return_value = mock_middleware
        mock_run.return_value = mock_run_coroutine

        with patch("nitric.faas.compose_middleware", mock_compose):
            with patch("nitric.faas.FunctionServer._run", mock_run):
                await FunctionServer(opts=FaasWorkerOptions()).start(mock_handler)

        # It should compose the handler(s) into a single handler function
        mock_compose.assert_called_once_with(mock_handler)
        # It should call run to create the coroutine
        mock_run.assert_called_once()

    async def test_init(self):
        mock_handler = AsyncMock()
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

        with patch("nitric.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitricapi.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
        ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
            await FunctionServer(opts=FaasWorkerOptions()).http(mock_handler)._run()

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

    async def test_trigger_sync_event_handler(self):
        mock_http_handler = Mock()
        mock_event_handler = Mock()
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [
                ServerMessage(
                    # Simulate Event Trigger
                    trigger_request=TriggerRequest(
                        data=b"a byte string",
                        topic=TopicTriggerContext(),
                    )
                )
            ]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitricapi.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
        ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
            await FunctionServer(opts=FaasWorkerOptions()).http(mock_http_handler).event(mock_event_handler)._run()

        # accept the init response from server
        assert 1 == stream_calls
        mock_event_handler.assert_called_once()
        mock_http_handler.assert_not_called()

    async def test_trigger_sync_http_handler(self):
        mock_http_handler = Mock()
        mock_event_handler = Mock()
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [
                ServerMessage(
                    # Simulate Http Trigger
                    trigger_request=TriggerRequest(
                        data=b"a byte string",
                        http=HttpTriggerContext(),
                    )
                )
            ]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitricapi.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
        ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
            await FunctionServer(opts=FaasWorkerOptions()).http(mock_http_handler).event(mock_event_handler)._run()

        # accept the init response from server
        assert 1 == stream_calls
        mock_http_handler.assert_called_once()
        mock_event_handler.assert_not_called()

    async def test_trigger_async_event_handler(self):
        mock_http_handler = AsyncMock()
        mock_event_handler = AsyncMock()
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [
                ServerMessage(
                    # Simulate Event Trigger
                    trigger_request=TriggerRequest(
                        data=b"a byte string",
                        topic=TopicTriggerContext(),
                    )
                )
            ]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitricapi.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
        ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
            await FunctionServer(opts=FaasWorkerOptions()).http(mock_http_handler).event(mock_event_handler)._run()

        # accept the init response from server
        assert 1 == stream_calls
        mock_event_handler.assert_called_once()
        mock_http_handler.assert_not_called()

    async def test_trigger_async_http_handler(self):
        mock_http_handler = AsyncMock()
        mock_event_handler = AsyncMock()
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [
                ServerMessage(
                    # Simulate Http Trigger
                    trigger_request=TriggerRequest(
                        data=b"a byte string",
                        http=HttpTriggerContext(),
                    )
                )
            ]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitricapi.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
        ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
            await FunctionServer(opts=FaasWorkerOptions()).http(mock_http_handler).event(mock_event_handler)._run()

        # accept the init response from server
        assert 1 == stream_calls
        mock_http_handler.assert_called_once()
        mock_event_handler.assert_not_called()

    async def test_failing_async_http_handler(self):
        mock_http_handler = AsyncMock()
        mock_event_handler = AsyncMock()
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [
                ServerMessage(
                    # Simulate Http Trigger
                    trigger_request=TriggerRequest(
                        data=b"a byte string",
                        http=HttpTriggerContext(),
                    )
                )
            ]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitricapi.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
        ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
            await FunctionServer(opts=FaasWorkerOptions()).http(mock_http_handler).event(mock_event_handler)._run()

        # accept the init response from server
        assert 1 == stream_calls
        mock_http_handler.assert_called_once()
        mock_event_handler.assert_not_called()

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

        with patch("nitric.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitricapi.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
        ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
            await FunctionServer(opts=FaasWorkerOptions()).event(mock_handler)._run()

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

        with patch("nitric.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitricapi.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
        ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
            await FunctionServer(opts=FaasWorkerOptions()).http(mock_handler)._run()

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
        trigger_request = TriggerRequest(
            data=b"",
            http=HttpTriggerContext(),
        )

        response_context = HttpContext.from_grpc_trigger_request(trigger_request)
        response_context.res.body = b"some bytes"

        mock_handler = Mock()
        mock_handler.return_value = response_context
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        async def mock_stream(self, request_iterator):
            nonlocal stream_calls
            mock_stream = [ServerMessage(trigger_request=trigger_request)]
            for message in mock_stream:
                stream_calls += 1
                yield message

        with patch("nitric.faas.AsyncChannel", mock_async_channel_init), patch(
            "nitricapi.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
        ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
            await FunctionServer(opts=FaasWorkerOptions()).http(mock_handler)._run()

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

    # async def test_handler_dict_response(self):
    #     mock_handler = Mock()
    #     mock_handler.return_value = {"key": "value", "num": 123}
    #     mock_grpc_channel = Mock()
    #     mock_async_channel_init = Mock()
    #     mock_async_chan = MockAsyncChannel()
    #     mock_async_channel_init.return_value = mock_async_chan
    #
    #     stream_calls = 0
    #
    #     async def mock_stream(self, request_iterator):
    #         nonlocal stream_calls
    #         mock_stream = [
    #             ServerMessage(
    #                 trigger_request=TriggerRequest(
    #                     data=b"",
    #                     http=HttpTriggerContext(),
    #                 )
    #             )
    #         ]
    #         for message in mock_stream:
    #             stream_calls += 1
    #             yield message
    #
    #     with patch("nitric.faas.faas.AsyncChannel", mock_async_channel_init), patch(
    #         "nitricapi.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
    #     ), patch("nitric.faas.faas.new_default_channel", mock_grpc_channel):
    #         await faas._register_function_handler(mock_handler)
    #
    #         # accept the trigger response from server
    #         assert 1 == stream_calls
    #         # handler called
    #         mock_handler.assert_called_once()
    #         # init, trigger response
    #         self.assertEqual(2, len(mock_async_chan.send.mock_calls))
    #         args, kwargs = mock_async_chan.send.call_args_list[1]
    #         (message,) = args
    #         # Response should be returned as JSON
    #         self.assertEqual(b'{"key": "value", "num": 123}', message.trigger_response.data)
    #         self.assertEqual({"Content-Type": "application/json"}, message.trigger_response.http.headers)
    #
    # async def test_handler_string_response(self):
    #     mock_handler = Mock()
    #     mock_handler.return_value = "a test string"
    #     mock_grpc_channel = Mock()
    #     mock_async_channel_init = Mock()
    #     mock_async_chan = MockAsyncChannel()
    #     mock_async_channel_init.return_value = mock_async_chan
    #
    #     stream_calls = 0
    #
    #     async def mock_stream(self, request_iterator):
    #         nonlocal stream_calls
    #         mock_stream = [
    #             ServerMessage(
    #                 trigger_request=TriggerRequest(
    #                     data=b"",
    #                     topic=TopicTriggerContext(),
    #                 )
    #             )
    #         ]
    #         for message in mock_stream:
    #             stream_calls += 1
    #             yield message
    #
    #     with patch("nitric.faas.faas.AsyncChannel", mock_async_channel_init), patch(
    #         "nitricapi.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
    #     ), patch("nitric.faas.faas.new_default_channel", mock_grpc_channel):
    #         await faas._register_function_handler(mock_handler)
    #
    #         # accept the trigger response from server
    #         assert 1 == stream_calls
    #         # handler called
    #         mock_handler.assert_called_once()
    #         # init, trigger response
    #         self.assertEqual(2, len(mock_async_chan.send.mock_calls))
    #         args, kwargs = mock_async_chan.send.call_args_list[1]
    #         (message,) = args
    #         # Response string should be converted to bytes
    #         self.assertEqual(b"a test string", message.trigger_response.data)
    #
    # async def test_unserializable_response(self):
    #     class NoJsonForYou:
    #         name: str
    #
    #         def __init__(self):
    #             self.name = "Can't be serialized"
    #
    #     mock_handler = Mock()
    #     mock_handler.return_value = Response(
    #         data=NoJsonForYou(),
    #         context=ResponseContext(context=TopicResponseContext(success=True)),
    #     )
    #     mock_grpc_channel = Mock()
    #     mock_async_channel_init = Mock()
    #     mock_async_chan = MockAsyncChannel()
    #     mock_async_channel_init.return_value = mock_async_chan
    #
    #     stream_calls = 0
    #
    #     async def mock_stream(self, request_iterator):
    #         nonlocal stream_calls
    #         mock_stream = [
    #             ServerMessage(
    #                 trigger_request=TriggerRequest(
    #                     data=b"",
    #                     topic=TopicTriggerContext(),
    #                 )
    #             )
    #         ]
    #         for message in mock_stream:
    #             stream_calls += 1
    #             yield message
    #
    #     with patch("nitric.faas.faas.AsyncChannel", mock_async_channel_init), patch(
    #         "nitricapi.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
    #     ), patch("nitric.faas.faas.new_default_channel", mock_grpc_channel):
    #         # An exception shouldn't be thrown, even though the serialization fails
    #         await faas._register_function_handler(mock_handler)
    #
    #         # accept the trigger response from server
    #         assert 1 == stream_calls
    #         # handler called
    #         mock_handler.assert_called_once()
    #         # init, trigger response
    #         self.assertEqual(2, len(mock_async_chan.send.mock_calls))
    #         args, kwargs = mock_async_chan.send.call_args_list[1]
    #         (message,) = args
    #         # Response return a success status of false and no data.
    #         self.assertEqual(bytes(), message.trigger_response.data)
    #         self.assertFalse(message.trigger_response.topic.success)
