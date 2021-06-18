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
from nitric.api import EventClient
from google.protobuf.struct_pb2 import Struct
from uuid import UUID


def test_publish():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_publish = Mock()
    mock_publish.return_value.topics = []

    payload = {"content": "of event"}

    with patch("nitric.api.EventClient._get_method_function", mock_grpc_method_getter):
        client = EventClient()
        request_id = client.publish("topic_name", payload, "payload.type", event_id="abc-123")

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Publish")
    payload_struct = Struct()
    payload_struct.update(payload)

    # Ensure the publish method is called with the expected input
    mock_publish.assert_called_once()
    assert mock_publish.call_args[0][0].topic == "topic_name"
    assert mock_publish.call_args[0][0].event.id == "abc-123"
    assert mock_publish.call_args[0][0].event.payload_type == "payload.type"
    assert mock_publish.call_args[0][0].event.payload["content"] == "of event"


def test_empty_payload():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_publish = Mock()
    mock_publish.return_value.topics = []

    with patch("nitric.api.EventClient._get_method_function", mock_grpc_method_getter):
        client = EventClient()
        client.publish(topic_name="topic_name", payload_type="payload.type")

    # Ensure the gRPC method is called, with an empty Struct as the payload.
    mock_publish.assert_called_once()
    assert mock_publish.call_args[0][0].event.payload == Struct()


def test_grpc_methods():
    client = EventClient()
    assert client._get_method_function("Publish")._method == b"/nitric.event.v1.Event/Publish"


def test_create_client():
    client = EventClient()
