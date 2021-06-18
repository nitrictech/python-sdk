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
from nitric.api import QueueClient, Task


def test_push():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_push = Mock()
    mock_push.return_value.failedMessages = []

    test_tasks = [Task(task_id="1234", payload_type="test-payload", payload={"test": "test"})]

    with patch("nitric.api.QueueClient._get_method_function", mock_grpc_method_getter):
        client = QueueClient()
        client.send_batch("test-queue", test_tasks)

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("SendBatch")

    # Ensure the queue push method is called with the expected input
    mock_push.assert_called_once()
    assert mock_push.call_args[0][0].queue == "test-queue"
    assert mock_push.call_args[0][0].tasks[0].id == "1234"
    assert mock_push.call_args[0][0].tasks[0].payload_type == "test-payload"
    assert mock_push.call_args[0][0].tasks[0].payload["test"] == "test"


def test_receive():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_receive = Mock()
    mock_receive.return_value.items = []

    with patch("nitric.api.QueueClient._get_method_function", mock_grpc_method_getter):
        client = QueueClient()
        client.receive("test-queue", 1)

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Receive")

    # Ensure the queue receive method is called with the expected input
    mock_receive.assert_called_once()
    assert mock_receive.call_args[0][0].queue == "test-queue"
    assert mock_receive.call_args[0][0].depth == 1


def test_receive_no_depth():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_receive = Mock()
    mock_receive.return_value.items = []

    with patch("nitric.api.QueueClient._get_method_function", mock_grpc_method_getter):
        client = QueueClient()
        client.receive("test-queue")  # call receive without the optional depth parameter.

    # Ensure the default value 1 is used.
    assert mock_receive.call_args[0][0].depth == 1


def test_receive_none_depth():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_receive = Mock()
    mock_receive.return_value.items = []

    with patch("nitric.api.QueueClient._get_method_function", mock_grpc_method_getter):
        client = QueueClient()
        client.receive("test-queue", None)  # call receive with depth = None.

    # Ensure the default value 1 is used.
    assert mock_receive.call_args[0][0].depth == 1


def test_receive_negative_depth():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_receive = Mock()
    mock_receive.return_value.items = []

    with patch("nitric.api.QueueClient._get_method_function", mock_grpc_method_getter):
        client = QueueClient()
        client.receive("test-queue", -2)  # call receive with a negative integer for depth.

    # Ensure the default value 1 is used.
    assert mock_receive.call_args[0][0].depth == 1


def test_grpc_methods():
    client = QueueClient()
    assert client._get_method_function("SendBatch")._method == b"/nitric.queue.v1.Queue/SendBatch"
    assert client._get_method_function("Receive")._method == b"/nitric.queue.v1.Queue/Receive"
