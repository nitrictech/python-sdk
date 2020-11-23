from http import HTTPStatus


class Response(object):
    """Nitric Function as a Service (FaaS) response class."""

    def __init__(self, status: int = HTTPStatus.OK, headers=None, body: bytes = None):
        # FIXME: Fix typing of the status parameter
        """Construct a new Nitric Response."""
        if headers is None:
            headers = {}
        if body is None:
            body = bytes()
        self.status = status
        self.headers = headers
        self.body = body
