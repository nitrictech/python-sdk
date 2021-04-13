from json.decoder import JSONDecodeError

from nitric.faas.request import _clean_header, Request
from unittest.mock import patch, Mock
import unittest


class RequestCases(unittest.TestCase):
    def test_clean_header(self):
        test_headers = [
            # Input, Expected Output
            ("x-nitric-test-prop", "test_prop"),
            ("X-NITRIC-ALL-CAPS-PROP", "all_caps_prop"),
            ("x-not-nitric-prop", "x_not_nitric_prop"),
        ]

        for header in test_headers:
            cleaned = _clean_header(header[0])
            assert cleaned == header[1]

    def test_headers_are_cleaned_in_request(self):
        test_headers = {
            "x-nitric-request-id": "abc123",
            "x-nitric-source": "some.source",
            "x-nitric-source-type": "REQUEST",
            "x-nitric-payload-type": "com.example.payload.type",
        }

        mock_clean_headers = Mock()
        mock_clean_headers.side_effect = [
            "request_id",
            "source",
            "source_type",
            "payload_type",
        ]
        with patch("nitric.faas.request._clean_header", mock_clean_headers):
            request = Request(test_headers, b"test content")
        mock_clean_headers.assert_called_with("x-nitric-payload-type")

    def test_mime_canon_headers_are_cleaned_in_request(self):
        test_headers = {
            "X-Nitric-Request-Id": "abc123",
            "X-Nitric-Source": "some.source",
            "X-Nitric-Source-Type": "REQUEST",
            "X-Nitric-Payload-Type": "com.example.payload.type",
        }

        mock_clean_headers = Mock()
        mock_clean_headers.side_effect = [
            "request_id",
            "source",
            "source_type",
            "payload_type",
        ]
        with patch("nitric.faas.request._clean_header", mock_clean_headers):
            request = Request(test_headers, b"test content")
        mock_clean_headers.assert_called_with("X-Nitric-Payload-Type")

    def test_unsupported_headers_ignored(self):
        test_headers = {
            "x-nitric-request-id": "abc123",
            "x-nitric-source": "some.source",
            "x-nitric-source-type": "REQUEST",
            "x-nitric-payload-type": "com.example.payload.type",
            "x-nitric-unknown-header": "should be ignored",
        }

        request = Request(test_headers, b"test content")
        # Make sure the unknown header didn't end up in the context and no errors are thrown.
        assert len([key for key in request.context.__dict__.keys() if "unknown" in key]) == 0

    def test_get_object(self):
        test_headers = {
            "x-nitric-request-id": "abc123",
            "x-nitric-source": "some.source",
            "x-nitric-source-type": "REQUEST",
            "x-nitric-payload-type": "com.example.payload.type",
            "x-nitric-unknown-header": "should be ignored",
        }
        request = Request(headers=test_headers, payload=b'{"name": "John"}')
        assert request.get_object()["name"] == "John"

    def test_get_object_with_invalid_payload_json(self):
        test_headers = {
            "x-nitric-request-id": "abc123",
            "x-nitric-source": "some.source",
            "x-nitric-source-type": "REQUEST",
            "x-nitric-payload-type": "com.example.payload.type",
            "x-nitric-unknown-header": "should be ignored",
        }
        # Missing beginning " before "name" property.
        request = Request(headers=test_headers, payload=b'{name": "John"}')
        self.assertRaises(JSONDecodeError, request.get_object)
