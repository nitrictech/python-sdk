from unittest.mock import patch, MagicMock, Mock
from nitric.sdk.v1 import EventingClient
from google.protobuf.struct_pb2 import Struct
from uuid import UUID


def test_get_topics():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_get_topics = Mock()
    mock_get_topics.return_value.topics = []

    with patch(
        "nitric.sdk.v1.EventingClient._get_method_function", mock_grpc_method_getter
    ):
        client = EventingClient()
        topics = client.get_topics()

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("GetTopics")
    # Ensure the get topics method is called
    mock_get_topics.assert_called_with(Struct())  # No input data required to get topics


def test_publish():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_publish = Mock()
    mock_publish.return_value.topics = []

    payload = {"content": "of event"}

    with patch(
        "nitric.sdk.v1.EventingClient._get_method_function", mock_grpc_method_getter
    ):
        client = EventingClient()
        request_id = client.publish(
            "topic_name", payload, "payload.type", request_id="abc-123"
        )

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Publish")
    payload_struct = Struct()
    payload_struct.update(payload)

    # Ensure the get topics method is called with the expected input
    mock_publish.assert_called_once()  # No input data required to get topics
    assert mock_publish.call_args.args[0].topicName == "topic_name"
    assert mock_publish.call_args.args[0].event.requestId == "abc-123"
    assert mock_publish.call_args.args[0].event.payloadType == "payload.type"
    assert mock_publish.call_args.args[0].event.payload["content"] == "of event"


def test_automatic_request_id():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_publish = Mock()
    mock_publish.return_value.topics = []

    payload = {"content": "of event"}

    with patch(
        "nitric.sdk.v1.EventingClient._get_method_function", mock_grpc_method_getter
    ):
        client = EventingClient()
        request_id = client.publish("topic_name", payload, "payload.type")

    # Ensure a request id was automatically generated
    assert len(request_id) > 0
    assert type(request_id) == str

    # Currently default request ids are UUIDs
    try:
        uuid4 = UUID(request_id, version=4)
    except Exception:
        raise Exception(
            "Auto-generated Request ID was not a valid version 4 UUID value."
        ) from None


def test_create_client():
    client = EventingClient()
