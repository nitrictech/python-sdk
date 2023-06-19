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
from typing import Optional
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock, Mock, call, MagicMock

import pytest

from nitric.faas import (
    FunctionServer,
    HttpContext,
    compose_middleware,
    HttpResponse,
    FaasWorkerOptions,
    BucketNotificationWorkerOptions,
    FileNotificationWorkerOptions,
    EventContext,
    EventMiddleware,
    EventRequest,
    EventResponse,
    HttpRequest,
)

from nitric.proto.nitric.faas.v1 import (
    ServerMessage,
    InitResponse,
    ClientMessage,
    InitRequest,
    TriggerRequest,
    TopicTriggerContext,
    HttpTriggerContext,
    BucketNotificationType,
)


class Object(object):
    pass


class MockAsyncChannel:
    def __init__(self):
        self.send = AsyncMock()
        self.close = Mock()
        self.done = Mock()


class FaasClientTest(IsolatedAsyncioTestCase):
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
            "nitric.proto.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
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

    #
    # async def test_trigger_sync_event_handler(self):
    #     mock_http_handler = Mock()
    #     mock_event_handler = Mock()
    #     mock_bucket_notification_handler = Mock()
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
    #                 # Simulate Event Trigger
    #                 trigger_request=TriggerRequest(
    #                     data=b"a byte string",
    #                     topic=TopicTriggerContext(),
    #                 )
    #             )
    #         ]
    #         for message in mock_stream:
    #             stream_calls += 1
    #             yield message
    #
    #     with patch("nitric.faas.AsyncChannel", mock_async_channel_init), patch(
    #         "nitric.proto.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
    #     ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
    #         await (
    #             FunctionServer(opts=FaasWorkerOptions())
    #             .http(mock_http_handler)
    #             .event(mock_event_handler)
    #             .bucket_notification(mock_bucket_notification_handler)
    #             ._run()
    #         )
    #
    #     # accept the init response from server
    #     assert 1 == stream_calls
    #     mock_event_handler.assert_called_once()
    #     mock_http_handler.assert_not_called()
    #     mock_bucket_notification_handler.assert_not_called()
    #
    # async def test_trigger_sync_http_handler(self):
    #     mock_http_handler = Mock()
    #     mock_event_handler = Mock()
    #     mock_bucket_notification_handler = Mock()
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
    #                 # Simulate Http Trigger
    #                 trigger_request=TriggerRequest(
    #                     data=b"a byte string",
    #                     http=HttpTriggerContext(),
    #                 )
    #             )
    #         ]
    #         for message in mock_stream:
    #             stream_calls += 1
    #             yield message
    #
    #     with patch("nitric.faas.AsyncChannel", mock_async_channel_init), patch(
    #         "nitric.proto.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
    #     ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
    #         await (
    #             FunctionServer(opts=FaasWorkerOptions())
    #             .http(mock_http_handler)
    #             .event(mock_event_handler)
    #             .bucket_notification(mock_bucket_notification_handler)
    #             ._run()
    #         )
    #
    #     # accept the init response from server
    #     assert 1 == stream_calls
    #     mock_http_handler.assert_called_once()
    #     mock_event_handler.assert_not_called()
    #     mock_bucket_notification_handler.assert_not_called()

    async def test_trigger_async_event_handler(self):
        mock_http_handler = AsyncMock()
        mock_event_handler = AsyncMock()
        mock_bucket_notification_handler = AsyncMock()
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        stream_calls = 0

        mock_event_handler.return_value = EventContext(request=EventRequest({}, "test", None), response=EventResponse())

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
            "nitric.proto.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
        ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
            await FunctionServer(opts=FaasWorkerOptions()).http(mock_http_handler).event(
                mock_event_handler
            ).bucket_notification(mock_bucket_notification_handler)._run()

        # accept the init response from server
        assert 1 == stream_calls
        mock_event_handler.assert_called_once()
        mock_http_handler.assert_not_called()
        mock_bucket_notification_handler.assert_not_called()

    async def test_trigger_async_http_handler(self):
        mock_http_handler = AsyncMock()
        mock_event_handler = AsyncMock()
        mock_bucket_notification_handler = AsyncMock()
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        mock_http_handler.return_value = HttpContext(
            request=HttpRequest(b"", "GET", "/", {}, {}, {}, None), response=HttpResponse()
        )

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
            "nitric.proto.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
        ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
            await FunctionServer(opts=FaasWorkerOptions()).http(mock_http_handler).event(
                mock_event_handler
            ).bucket_notification(mock_bucket_notification_handler)._run()

        # accept the init response from server
        assert 1 == stream_calls
        mock_http_handler.assert_called_once()
        mock_event_handler.assert_not_called()
        mock_bucket_notification_handler.assert_not_called()

    async def test_failing_async_http_handler(self):
        mock_http_handler = AsyncMock()
        mock_event_handler = AsyncMock()
        mock_bucket_notification_handler = AsyncMock()
        mock_grpc_channel = Mock()
        mock_async_channel_init = Mock()
        mock_async_chan = MockAsyncChannel()
        mock_async_channel_init.return_value = mock_async_chan

        mock_http_handler.return_value = {"test": 123}

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
            "nitric.proto.nitric.faas.v1.FaasServiceStub.trigger_stream", mock_stream
        ), patch("nitric.faas.new_default_channel", mock_grpc_channel):
            await FunctionServer(opts=FaasWorkerOptions()).http(mock_http_handler, mock_http_handler).event(
                mock_event_handler
            ).bucket_notification(mock_bucket_notification_handler)._run()

        # accept the init response from server
        assert 1 == stream_calls
        mock_http_handler.assert_called_once()
        mock_event_handler.assert_not_called()
        mock_bucket_notification_handler.assert_not_called()
