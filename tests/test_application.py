# #
# # Copyright (c) 2021 Nitric Technologies Pty Ltd.
# #
# # This file is part of Nitric Python 3 SDK.
# # See https://github.com/nitrictech/python-sdk for further info.
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# #
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock, Mock

from grpclib import GRPCError, Status
from opentelemetry.sdk.trace import TracerProvider, sampling


from nitric.api.exception import NitricUnavailableException
from nitric.resources import Bucket
from nitric.application import Nitric


class Object(object):
    pass


class MockAsyncChannel:
    def __init__(self):
        self.send = AsyncMock()
        self.close = Mock()
        self.done = Mock()


class ApplicationTest(IsolatedAsyncioTestCase):
    def test_create_resource(self):
        application = Nitric()
        mock_make = Mock()
        mock_make.side_effect = ConnectionRefusedError("test error")

        with patch("nitric.resources.base.BaseResource.make", mock_make):
            try:
                application._create_resource(Bucket, "test-bucket")
            except NitricUnavailableException as e:
                assert str(e).startswith("Unable to connect")

    def test_create_tracer(self):
        application = Nitric()

        tracer = application._create_tracer(local=True, sampler=80)

        assert tracer is not None
        assert isinstance(tracer.sampler, sampling.TraceIdRatioBased)
        assert tracer.sampler.rate == 0.8

    def test_run(self):
        application = Nitric()

        mock_running_loop = Mock()
        mock_event_loop = Mock()

        with patch("asyncio.get_event_loop", mock_event_loop):
            with patch("asyncio.get_running_loop", mock_running_loop):
                application.run()

                mock_running_loop.assert_called_once()
                mock_event_loop.assert_not_called()

    def test_run_with_no_active_event_loop(self):
        application = Nitric()

        mock_running_loop = Mock()
        mock_running_loop.side_effect = RuntimeError("loop is not running")

        mock_event_loop = Mock()

        with patch("asyncio.get_event_loop", mock_event_loop):
            with patch("asyncio.get_running_loop", mock_running_loop):
                application.run()

                mock_running_loop.assert_called_once()
                mock_event_loop.assert_called_once()

    def test_run_with_keyboard_interrupt(self):
        application = Nitric()

        mock_running_loop = Mock()
        mock_running_loop.side_effect = KeyboardInterrupt("cancel")

        mock_event_loop = Mock()

        with patch("asyncio.get_event_loop", mock_event_loop):
            with patch("asyncio.get_running_loop", mock_running_loop):
                application.run()

                mock_running_loop.assert_called_once()
                mock_event_loop.assert_not_called()

    def test_run_with_connection_refused(self):
        application = Nitric()

        mock_running_loop = Mock()
        mock_running_loop.side_effect = ConnectionRefusedError("refusing connection")

        mock_event_loop = Mock()

        with patch("asyncio.get_event_loop", mock_event_loop):
            with patch("asyncio.get_running_loop", mock_running_loop):
                try:
                    application.run()
                    pytest.fail()
                except NitricUnavailableException as e:
                    assert str(e).startswith("Unable to connect to a nitric server!")

                mock_running_loop.assert_called_once()
                mock_event_loop.assert_not_called()
