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
        client.send_batch("test-queue", test_events)

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("SendBatch")

    # Ensure the queue push method is called with the expected input
    mock_push.assert_called_once()
    assert mock_push.call_args.args[0].queue == "test-queue"
    assert mock_push.call_args.args[0].events[0].requestId == "1234"
    assert mock_push.call_args.args[0].events[0].payloadType == "test-payload"
    assert mock_push.call_args.args[0].events[0].payload["test"] == "test"


def test_receive():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_receive = Mock()
    mock_receive.return_value.items = []

    with patch(
        "nitric.sdk.v1.QueueClient._get_method_function", mock_grpc_method_getter
    ):
        client = QueueClient()
        client.receive("test-queue", 1)

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Receive")

    # Ensure the queue receive method is called with the expected input
    mock_receive.assert_called_once()
    assert mock_receive.call_args.args[0].queue == "test-queue"
    assert mock_receive.call_args.args[0].depth == 1


def test_receive_no_depth():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_receive = Mock()
    mock_receive.return_value.items = []

    with patch(
        "nitric.sdk.v1.QueueClient._get_method_function", mock_grpc_method_getter
    ):
        client = QueueClient()
        client.receive(
            "test-queue"
        )  # call receive without the optional depth parameter.

    # Ensure the default value 1 is used.
    assert mock_receive.call_args.args[0].depth == 1


def test_receive_none_depth():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_receive = Mock()
    mock_receive.return_value.items = []

    with patch(
        "nitric.sdk.v1.QueueClient._get_method_function", mock_grpc_method_getter
    ):
        client = QueueClient()
        client.receive("test-queue", None)  # call receive with depth = None.

    # Ensure the default value 1 is used.
    assert mock_receive.call_args.args[0].depth == 1


def test_receive_negative_depth():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_receive = Mock()
    mock_receive.return_value.items = []

    with patch(
        "nitric.sdk.v1.QueueClient._get_method_function", mock_grpc_method_getter
    ):
        client = QueueClient()
        client.receive(
            "test-queue", -2
        )  # call receive with a negative integer for depth.

    # Ensure the default value 1 is used.
    assert mock_receive.call_args.args[0].depth == 1


def test_grpc_methods():
    client = QueueClient()
    assert (
        client._get_method_function("SendBatch")._method
        == b"/nitric.queue.v1.Queue/SendBatch"
    )
    assert (
        client._get_method_function("Receive")._method
        == b"/nitric.queue.v1.Queue/Receive"
    )
