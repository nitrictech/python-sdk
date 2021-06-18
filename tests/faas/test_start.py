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
from unittest.mock import patch, Mock
import unittest
from nitric.faas import Response, ResponseContext, HttpResponseContext
from nitric.faas import start
from nitric.faas.faas import Handler
from nitric.proto.faas.v1.faas_pb2 import TriggerResponse
from google.protobuf import json_format


class StartCases(unittest.TestCase):
    def test_serve_called(self):
        mock_serve = Mock()
        mock_serve.return_value = None

        with patch("nitric.faas.faas.serve", mock_serve):
            start(func=lambda a: "test mock response")

        args, kwargs = mock_serve.call_args
        mock_serve.assert_called_once()
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 8080


class HandlerCases(unittest.TestCase):
    def test_full_response(self):
        mock_func = Mock()
        mock_response = Response(
            data="it works".encode(),
            context=ResponseContext(context=HttpResponseContext(headers={"a": "a header"}, status=200)),
        )
        mock_func.return_value = mock_response

        return_body = json_format.MessageToJson(mock_response.to_grpc_trigger_response_context())

        with patch("nitric.faas.faas.construct_request", Mock()):
            handler = Handler(mock_func)
            response = handler()

        # Ensure the response is returned in the tuple format for Flask
        assert response == (return_body, 200, {"Content-Type": "application/json"})

    def test_unhandled_exception(self):
        # always return and error to test how it's handled internally
        def error_func():
            raise Exception("mock error")

        with patch("nitric.faas.faas.construct_request", Mock()):
            handler = Handler(error_func)
            response = handler()

        # Ensure the 500 internal server error status is returned.
        # TODO: No body should be included outside of debug mode. Use this assert in future once that's implemented
        # assert response == ('', 500)
        # We'll return a 200 OK for errors, the actual response is encoded in the body
        assert response[1] == 200  # For now, just check that the error status is set

    def test_debug_unhandled_exception(self):
        # TODO: set the debug environment variable (or equivalent) once available
        # always return and error to test how it's handled internally
        def error_func():
            raise Exception("mock error")

        with patch("nitric.faas.faas.construct_request", Mock()):
            handler = Handler(error_func)
            response = handler()

        trigger_response = json_format.Parse(response[0], TriggerResponse())

        # Ensure the debug details are provided along with the error status
        assert trigger_response.data.decode().startswith(
            "<html><head><title>Error</title></head><body><h2>An Error Occurred:</h2>"
        )
        assert response[1] == 200  # Status code

    def test_str_response(self):
        mock_func = Mock()
        mock_func.return_value = "test"

        with patch("nitric.faas.faas.construct_request", Mock()):
            handler = Handler(mock_func)
            response = handler()

        trigger_response = json_format.Parse(response[0], TriggerResponse())

        # Ensure the response string was wrapped with http response values
        assert trigger_response.data.decode() == "test"
        assert response[1] == 200

    def test_no_response(self):
        def no_response(request):
            # do nothing
            mock = Mock()

        with patch("nitric.faas.faas.construct_request", Mock()):
            handler = Handler(no_response)
            response = handler()

        trigger_response = json_format.Parse(response[0], TriggerResponse())
        # Ensure an empty response with a success status
        assert trigger_response.data.decode() == ""
        assert response[1] == 200
