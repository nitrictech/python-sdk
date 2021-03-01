from unittest.mock import patch, Mock
import unittest
from nitric.sdk.v1.faas import Response
from nitric.sdk.v1.faas import start
from nitric.sdk.v1.faas.faas import Handler


class StartCases(unittest.TestCase):
    def test_serve_called(self):
        mock_serve = Mock()
        mock_serve.return_value = None

        with patch("nitric.sdk.v1.faas.faas.serve", mock_serve):
            start(func=lambda a: Response("test mock response"))

        args, kwargs = mock_serve.call_args
        mock_serve.assert_called_once()
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 8080


class HandlerCases(unittest.TestCase):
    def test_full_response(self):
        mock_func = Mock()
        mock_func.return_value = Response(
            status=200, body="it works", headers={"a": "a header", "b": "b header"}
        )

        with patch("nitric.sdk.v1.faas.faas.construct_request", Mock()):
            handler = Handler(mock_func)
            response = handler()

        # Ensure the response is returned in the tuple format for Flask
        assert response == ("it works", 200, {"a": "a header", "b": "b header"})

    def test_custom_status(self):
        mock_func = Mock()
        mock_func.return_value = Response(
            status=404
        )  # Simulate a non 200 status, such as an error

        with patch("nitric.sdk.v1.faas.faas.construct_request", Mock()):
            handler = Handler(mock_func)
            response = handler()

        # Ensure the response is returned in the tuple format for Flask
        assert response == ("", 404, {})

    def test_unhandled_exception(self):
        # always return and error to test how it's handled internally
        def error_func():
            raise Exception("mock error")

        with patch("nitric.sdk.v1.faas.faas.construct_request", Mock()):
            handler = Handler(error_func)
            response = handler()

        # Ensure the 500 internal server error status is returned.
        # TODO: No body should be included outside of debug mode. Use this assert in future once that's implemented
        # assert response == ('', 500)
        assert response[1] == 500  # For now, just check that the error status is set

    def test_debug_unhandled_exception(self):
        # TODO: set the debug environment variable (or equivalent) once available
        # always return and error to test how it's handled internally
        def error_func():
            raise Exception("mock error")

        with patch("nitric.sdk.v1.faas.faas.construct_request", Mock()):
            handler = Handler(error_func)
            response = handler()

        # Ensure the debug details are provided along with the error status
        assert response[0].startswith(
            "<html><head><title>Error</title></head><body><h2>An Error Occurred:</h2>"
        )
        assert response[1] == 500  # Status code

    def test_str_response(self):
        mock_func = Mock()
        mock_func.return_value = "test"

        with patch("nitric.sdk.v1.faas.faas.construct_request", Mock()):
            handler = Handler(mock_func)
            response = handler()

        # Ensure the response string was wrapped with http response values
        assert response == ("test", 200, {})

    def test_no_response(self):
        def no_response(request):
            # do nothing
            mock = Mock()

        with patch("nitric.sdk.v1.faas.faas.construct_request", Mock()):
            handler = Handler(no_response)
            response = handler()

        # Ensure an empty response with a success status
        assert response == ("", 200)
