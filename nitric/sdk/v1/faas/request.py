from enum import Enum
import typing


class SourceType(Enum):
    """The type of the source of an event."""

    SUBSCRIPTION = "subscription"
    REQUEST = "request"


class Context(object):
    """Represents the contextual metadata for a Nitric function request."""

    def __init__(
        self,
        *,
        request_id: str = None,
        source: str = None,
        source_type: str = None,
        payload_type: str = None,
        **kwargs
    ):
        """Construct a Nitric Request Content object."""
        self.request_id = request_id
        self.source = source
        self.source_type = source_type
        self.payload_type = payload_type


def _clean_header(header_name: str):
    """Convert a Nitric HTTP request header name into the equivalent Context property name."""
    return header_name.lower().replace("x-nitric-", "").replace("-", "_")


class RequestParameters(object):
    """Represents parsed URL path and query parameters."""

    def __init__(self, path: dict = None, query: dict = None):
        """Construct a new request parameters object containing path and query param dicts."""
        if path is None:
            path = {}
        if query is None:
            query = {}
        self.path = path
        self.query = query


class Request(object):
    """
    Represents a standard Nitric function request.

    These requests are normalized from their original stack-specific structures.
    """

    def __init__(self, headers: typing.Dict[str, str], payload: bytes, path: str = ""):
        """Construct a Nitric Function Request."""
        # Map headers to context properties
        context_props = {
            _clean_header(k): v
            for k, v in headers.items()
            if k.lower().startswith("x-nitric")
        }
        self.context = Context(**context_props)
        self.payload = payload
        self.path = path

    def get_body(self) -> bytes:
        """Return the bytes of the body of the request."""
        return self.payload

    def get_object(self) -> dict:
        """
        Assume the payload is JSON and return the content deserialized into a dictionary.

        :raises JSONDecodeError: raised when the request payload (body) is not valid JSON.

        :return: the deserialized JSON request body as a dictionary
        """
        import json

        return json.loads(self.payload)

    # TODO: Implement path and query param parsing, which is consistent with other SDKs
    # def get_params(self) -> RequestParameters:
    #     self.path
