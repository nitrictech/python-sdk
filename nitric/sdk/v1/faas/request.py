from enum import Enum
import typing


class SourceType(Enum):
    """The type of the source of an event"""
    SUBSCRIPTION = 'subscription'
    REQUEST = 'request'


class Context(object):
    """Represents the contextual metadata for a Nitric function request"""

    def __init__(self, request_id: str, source: str, source_type: str, payload_type: str):
        self.request_id = request_id
        self.source = source
        self.source_type = source_type
        self.payload_type = payload_type


def _clean_header(header_name: str):
    """Converts a Nitric HTTP request header name into the equivalent Context property name"""
    return header_name \
        .replace("x-nitric-", "") \
        .replace("-", "_") \
        .lower()


class Request(object):
    """Represents a standard Nitric function request.
    These requests are normalized from their original stack-specific structures"""

    def __init__(self, headers: typing.Dict[str, str], payload: bytes):
        # Map headers to context properties
        context_props = {_clean_header(k): v for k, v in headers.items() if k.startswith("x-nitric")}
        self.context = Context(**context_props)
        self.payload = payload
