#
# Copyright (c) 2021 Nitric Technologies Pty Ltd.
#
# This file is part of Nitric Python 3 SDK.
# See https://github.com/nitrictech/python-sdk for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
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
        return "http://{0}".format(url)
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
    if struct is None:
        return {}
    gpb_struct = WorkingStruct()
    gpb_struct.ParseFromString(bytes(struct))
    return MessageToDict(gpb_struct)


def _struct_from_dict(dictionary: dict) -> Struct:
    """Construct a Struct from a dict."""
    # Convert to dict into a Struct class from the protobuf library
    #   since protobuf Structs are able to be created from a dict
    #   unlike the Struct class from betterproto.
    if dictionary is None:
        return Struct()
    gpb_struct = WorkingStruct()
    gpb_struct.update(dictionary)
    # Convert the bytes representation of the protobuf Struct into the betterproto Struct
    #   so that the returned Struct is compatible with other betterproto generated classes
    struct = Struct().parse(gpb_struct.SerializeToString())
    return struct
