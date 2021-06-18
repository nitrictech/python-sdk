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
from unittest.mock import patch, Mock

from google.protobuf.struct_pb2 import Struct

from nitric.api import KeyValueClient
from nitric.proto.kv.v1.kv_pb2 import KeyValueGetResponse


# Put
def test_put_key_value():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_create = Mock()

    test_key_value = {"content": "some text content"}

    with patch("nitric.api.KeyValueClient._get_method_function", mock_grpc_method_getter):
        client = KeyValueClient()
        client.put("collection_name", "kv_key", test_key_value)

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Put")

    # Ensure the get topics method is called with the expected input
    mock_create.assert_called_once()  # No input data required to get topics
    assert mock_create.call_args[0][0].collection == "collection_name"
    assert mock_create.call_args[0][0].key == "kv_key"
    assert mock_create.call_args[0][0].value["content"] == "some text content"


# Get
def test_get_key_value():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_get = Mock()
    value_struct = Struct()
    value_struct.update({"kv_key": "doc_value"})
    reply = KeyValueGetResponse(value=value_struct)
    mock_get.return_value = reply

    with patch("nitric.api.KeyValueClient._get_method_function", mock_grpc_method_getter):
        client = KeyValueClient()
        response_value = client.get("collection_name", "kv_key")

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Get")
    assert response_value == {"kv_key": "doc_value"}


# Delete
def test_delete_key_value():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_create = Mock()

    with patch("nitric.api.KeyValueClient._get_method_function", mock_grpc_method_getter):
        client = KeyValueClient()
        client.delete("collection_name", "kv_key")

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Delete")

    # Ensure the get topics method is called with the expected input
    mock_create.assert_called_once()  # No input data required to get topics
    assert mock_create.call_args[0][0].collection == "collection_name"
    assert mock_create.call_args[0][0].key == "kv_key"


def test_grpc_methods():
    client = KeyValueClient()
    assert client._get_method_function("Put")._method == b"/nitric.kv.v1.KeyValue/Put"
    assert client._get_method_function("Get")._method == b"/nitric.kv.v1.KeyValue/Get"
    assert client._get_method_function("Delete")._method == b"/nitric.kv.v1.KeyValue/Delete"


def test_create_client():
    client = KeyValueClient()
