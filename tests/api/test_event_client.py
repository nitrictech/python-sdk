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
        request_id = client.publish(
            "topic_name", payload, "payload.type", event_id="abc-123"
        )

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Publish")
    payload_struct = Struct()
    payload_struct.update(payload)

    # Ensure the publish method is called with the expected input
    mock_publish.assert_called_once()
    assert mock_publish.call_args.args[0].topic == "topic_name"
    assert mock_publish.call_args.args[0].event.id == "abc-123"
    assert mock_publish.call_args.args[0].event.payloadType == "payload.type"
    assert mock_publish.call_args.args[0].event.payload["content"] == "of event"


def test_automatic_request_id():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_publish = Mock()
    mock_publish.return_value.topics = []

    payload = {"content": "of event"}

    with patch("nitric.api.EventClient._get_method_function", mock_grpc_method_getter):
        client = EventClient()
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


def test_empty_payload():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_publish = Mock()
    mock_publish.return_value.topics = []

    with patch("nitric.api.EventClient._get_method_function", mock_grpc_method_getter):
        client = EventClient()
        client.publish(topic_name="topic_name", payload_type="payload.type")

    # Ensure the gRPC method is called, with an empty Struct as the payload.
    mock_publish.assert_called_once()
    assert mock_publish.call_args.args[0].event.payload == Struct()


def test_grpc_methods():
    client = EventClient()
    assert (
        client._get_method_function("Publish")._method
        == b"/nitric.event.v1.Event/Publish"
    )


def test_create_client():
    client = EventClient()
