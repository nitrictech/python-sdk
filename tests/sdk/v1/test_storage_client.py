from unittest.mock import patch, Mock
from nitric.sdk.v1 import StorageClient


# Put to bucket
def test_put():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_create = Mock()

    content = b"test content"

    with patch(
        "nitric.sdk.v1.StorageClient._get_method_function", mock_grpc_method_getter
    ):
        client = StorageClient()
        client.put("bucket_name", "key_name", content)

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Put")

    # Ensure the get topics method is called with the expected input
    mock_create.assert_called_once()  # No input data required to get topics
    assert mock_create.call_args.args[0].bucketName == "bucket_name"
    assert mock_create.call_args.args[0].key == "key_name"
    assert mock_create.call_args.args[0].body == content


# Get from bucket
def test_get():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_create = Mock()

    with patch(
        "nitric.sdk.v1.StorageClient._get_method_function", mock_grpc_method_getter
    ):
        client = StorageClient()
        client.get("bucket_name", "key_name")

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("Get")

    # Ensure the get topics method is called with the expected input
    mock_create.assert_called_once()  # No input data required to get topics
    assert mock_create.call_args.args[0].bucketName == "bucket_name"
    assert mock_create.call_args.args[0].key == "key_name"


def test_grpc_methods():
    client = StorageClient()
    assert (
        client._get_method_function("Get")._method == b"/nitric.v1.storage.Storage/Get"
    )
    assert (
        client._get_method_function("Put")._method == b"/nitric.v1.storage.Storage/Put"
    )
