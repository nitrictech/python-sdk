from enum import Enum
import typing


class SourceType(Enum):
    """The type of the source of an event"""
    SUBSCRIPTION = 'subscription'
    REQUEST = 'request'


class NitricContext(object):
    """Represents the contextual metadata for a Nitric function request"""

    def __init__(self, request_id: str, source: str, source_type: SourceType | str, content_type: str,
                 payload_type: str, payload: bytes):
        self.request_id = request_id
        self.type = type
        self.source = source
        self.source_type = source_type
        self.content_type = content_type
        self.payload_type = payload_type
        self.payload = payload


def _clean_header(header_name: str):
    """Converts the standard Nitric HTTP request headers into the equivalent NitricContext property name"""
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
        self.context = NitricContext(**context_props)
        self.payload = payload
