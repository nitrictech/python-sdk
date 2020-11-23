from nitric.sdk.v1.faas.request import _clean_header, Request
from unittest.mock import patch, MagicMock, Mock


def test_clean_header():
    test_headers = [
        # Input, Expected Output
        ("x-nitric-test-prop", "test_prop"),
        ("X-NITRIC-ALL-CAPS-PROP", "all_caps_prop"),
        ("x-not-nitric-prop", "x_not_nitric_prop"),
    ]

    for header in test_headers:
        cleaned = _clean_header(header[0])
        assert cleaned == header[1]


def test_headers_are_cleaned_in_request():
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
    with patch("nitric.sdk.v1.faas.request._clean_header", mock_clean_headers):
        request = Request(test_headers, b"test content")
    mock_clean_headers.assert_called_with("x-nitric-payload-type")


def test_unsupported_headers_ignored():
    test_headers = {
        "x-nitric-request-id": "abc123",
        "x-nitric-source": "some.source",
        "x-nitric-source-type": "REQUEST",
        "x-nitric-payload-type": "com.example.payload.type",
        "x-nitric-unknown-header": "should be ignored",
    }

    request = Request(test_headers, b"test content")
    # Make sure the unknown header didn't end up in the context and no errors are thrown.
    assert (
        len([key for key in request.context.__dict__.keys() if "unknown" in key]) == 0
    )
