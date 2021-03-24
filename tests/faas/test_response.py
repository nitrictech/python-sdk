from nitric.faas import Response
from http import HTTPStatus


def test_create_response():
    response = Response(
        status=HTTPStatus.ACCEPTED,
        headers={"x-test-header": "test value"},
        body=b"test body content",
    )


def test_body_only_response():
    response = Response(body=b"test body content")
    assert response.status == HTTPStatus.OK


def test_status_only_response():
    response = Response(status=HTTPStatus.BAD_REQUEST)
    assert response.status == HTTPStatus.BAD_REQUEST
