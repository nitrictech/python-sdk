from unittest.mock import patch, Mock
from nitric.sdk.v1 import TopicClient
from google.protobuf.struct_pb2 import Struct


def test_get_topics():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_get_topics = Mock()
    mock_get_topics.return_value.topics = []

    with patch(
        "nitric.sdk.v1.TopicClient._get_method_function", mock_grpc_method_getter
    ):
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
