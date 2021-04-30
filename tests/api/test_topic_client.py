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
from nitric.api import TopicClient
from google.protobuf.struct_pb2 import Struct


def test_get_topics():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_get_topics = Mock()
    mock_get_topics.return_value.topics = []

    with patch("nitric.api.TopicClient._get_method_function", mock_grpc_method_getter):
        client = TopicClient()
        topics = client.get_topics()

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("List")
    # Ensure the get topics method is called
    mock_get_topics.assert_called_with(Struct())  # No input data required to get topics


def test_grpc_methods():
    client = TopicClient()
    assert client._get_method_function("List")._method == b"/nitric.event.v1.Topic/List"


def test_create_client():
    client = TopicClient()
