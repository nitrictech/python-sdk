import re
from betterproto.lib.google.protobuf import Struct
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct as WorkingStruct
from nitric.config import settings
from urllib.parse import urlparse
from grpclib.client import Channel


def format_url(url: str):
    """Add the default http scheme prefix to urls without one."""
    if not re.match("^((?:http|ftp|https):)?//", url.lower()):
        return "http://{}".format(url)
    return url


def new_default_channel():
    """Create new gRPC channel from settings."""
    channel_url = urlparse(format_url(settings.SERVICE_BIND))
    return Channel(host=channel_url.hostname, port=channel_url.port)


# These functions convert to/from python dict <-> betterproto.lib.google.protobuf.Struct
# the existing Struct().from_dict() method doesn't work for Structs,
#   it relies on Message meta information, that isn't available for dynamic structs.
def _dict_from_struct(struct: Struct) -> dict:
    """Construct a dict from a Struct."""
    # Convert the bytes representation of the betterproto Struct into a protobuf Struct
    # in order to use the MessageToDict function to safely create a dict.
    gpb_struct = WorkingStruct()
    gpb_struct.ParseFromString(bytes(struct))
    return MessageToDict(gpb_struct)


def _struct_from_dict(dictionary: dict) -> Struct:
    """Construct a Struct from a dict."""
    # Convert to dict into a Struct class from the protobuf library
    #   since protobuf Structs are able to be created from a dict
    #   unlike the Struct class from betterproto.
    gpb_struct = WorkingStruct()
    gpb_struct.update(dictionary)
    # Convert the bytes representation of the protobuf Struct into the betterproto Struct
    #   so that the returned Struct is compatible with other betterproto generated classes
    struct = Struct().parse(gpb_struct.SerializeToString())
    return struct
