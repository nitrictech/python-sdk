from http import HTTPStatus
from typing import Union


class Response(object):
    """Nitric Function as a Service (FaaS) response class."""

    def __init__(self, status: Union[int, HTTPStatus] = HTTPStatus.OK, headers: dict = None, body=None):
        """Construct a new Nitric Response."""
        # FIXME: Fix typing of the status parameter, add tests
        if headers is None:
            headers = {}
        if body is None:
            body = ""
        self.status = status
        self.headers = headers
        self.body = body
