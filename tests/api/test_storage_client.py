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
from nitric.api import StorageClient


# Write to bucket
def test_write():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_create = Mock()

    content = b"test content"

    with patch("nitric.api.StorageClient._get_method_function", mock_grpc_method_getter):
        client = StorageClient()
        client.write("bucket_name", "key_name", content)

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Write")

    # Ensure the 'Put' method is called with the expected input
    mock_create.assert_called_once()  # No input data required to get topics
    assert mock_create.call_args[0][0].bucket_name == "bucket_name"
    assert mock_create.call_args[0][0].key == "key_name"
    assert mock_create.call_args[0][0].body == content


# Read from bucket
def test_read():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_create = Mock()

    with patch("nitric.api.StorageClient._get_method_function", mock_grpc_method_getter):
        client = StorageClient()
        client.read("bucket_name", "key_name")

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Read")

    # Ensure the 'Get' method is called with the expected input
    mock_create.assert_called_once()  # No input data required to get topics
    assert mock_create.call_args[0][0].bucket_name == "bucket_name"
    assert mock_create.call_args[0][0].key == "key_name"


def test_grpc_methods():
    client = StorageClient()
    assert client._get_method_function("Read")._method == b"/nitric.storage.v1.Storage/Read"
    assert client._get_method_function("Write")._method == b"/nitric.storage.v1.Storage/Write"
