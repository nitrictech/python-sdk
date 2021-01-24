from unittest.mock import patch, Mock
from nitric.sdk.v1 import QueueClient, Event

def test_push():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_create = Mock()
    mock_create.return_value.failedMessages = []

    content = b"test content"

    test_events = [Event(request_id="1234", payload_type="test-payload", payload={'test': 'test'})]

    with patch(
        "nitric.sdk.v1.QueueClient._get_method_function", mock_grpc_method_getter
    ):
        client = QueueClient()
        client.push("test-queue", test_events)

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Push")

    # Ensure the get topics method is called with the expected input
    mock_create.assert_called_once()  # No input data required to get topics
    assert mock_create.call_args.args[0].queue == "test-queue"
    assert mock_create.call_args.args[0].events[0].requestId == "1234"
    assert mock_create.call_args.args[0].events[0].payloadType == "test-payload"
    assert mock_create.call_args.args[0].events[0].payload["test"] == "test"