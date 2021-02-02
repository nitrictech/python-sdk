from unittest.mock import patch, Mock
from nitric.sdk.v1 import QueueClient, Event


def test_push():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_push = Mock()
    mock_push.return_value.failedMessages = []

    test_events = [
        Event(request_id="1234", payload_type="test-payload", payload={"test": "test"})
    ]

    with patch(
        "nitric.sdk.v1.QueueClient._get_method_function", mock_grpc_method_getter
    ):
        client = QueueClient()
        client.push("test-queue", test_events)

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Push")

    # Ensure the queue push method is called with the expected input
    mock_push.assert_called_once()
    assert mock_push.call_args.args[0].queue == "test-queue"
    assert mock_push.call_args.args[0].events[0].requestId == "1234"
    assert mock_push.call_args.args[0].events[0].payloadType == "test-payload"
    assert mock_push.call_args.args[0].events[0].payload["test"] == "test"


def test_pop():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_pop = Mock()
    mock_pop.return_value.items = []

    with patch(
        "nitric.sdk.v1.QueueClient._get_method_function", mock_grpc_method_getter
    ):
        client = QueueClient()
        client.pop("test-queue", 1)

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Pop")

    # Ensure the queue pop method is called with the expected input
    mock_pop.assert_called_once()
    assert mock_pop.call_args.args[0].queue == "test-queue"
    assert mock_pop.call_args.args[0].depth == 1


def test_pop_no_depth():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_pop = Mock()
    mock_pop.return_value.items = []

    with patch(
        "nitric.sdk.v1.QueueClient._get_method_function", mock_grpc_method_getter
    ):
        client = QueueClient()
        client.pop("test-queue")  # call pop without the optional depth parameter.

    # Ensure the default value 1 is used.
    assert mock_pop.call_args.args[0].depth == 1


def test_pop_none_depth():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_pop = Mock()
    mock_pop.return_value.items = []

    with patch(
        "nitric.sdk.v1.QueueClient._get_method_function", mock_grpc_method_getter
    ):
        client = QueueClient()
        client.pop("test-queue", None)  # call pop with depth = None.

    # Ensure the default value 1 is used.
    assert mock_pop.call_args.args[0].depth == 1


def test_pop_negative_depth():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_pop = Mock()
    mock_pop.return_value.items = []

    with patch(
        "nitric.sdk.v1.QueueClient._get_method_function", mock_grpc_method_getter
    ):
        client = QueueClient()
        client.pop("test-queue", -2)  # call pop with a negative integer for depth.

    # Ensure the default value 1 is used.
    assert mock_pop.call_args.args[0].depth == 1
