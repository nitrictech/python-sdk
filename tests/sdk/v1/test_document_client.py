from unittest.mock import patch, Mock

from google.protobuf.struct_pb2 import Struct

from nitric.sdk.v1 import DocumentsClient
from nitric.proto.v1.documents_pb2 import GetDocumentReply


# Create
def test_create_document():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_create = Mock()
    # mock_create.return_value.topics = []

    test_document = {"content": "some text content"}

    with patch(
        "nitric.sdk.v1.DocumentsClient._get_method_function", mock_grpc_method_getter
    ):
        client = DocumentsClient()
        client.create_document("collection_name", "doc_key", test_document)

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("CreateDocument")

    # Ensure the get topics method is called with the expected input
    mock_create.assert_called_once()  # No input data required to get topics
    assert mock_create.call_args.args[0].collection == "collection_name"
    assert mock_create.call_args.args[0].key == "doc_key"
    assert mock_create.call_args.args[0].document["content"] == "some text content"


# Get
def test_get_document():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_get = Mock()
    document = Struct()
    document.update({"doc_key": "doc_value"})
    reply = GetDocumentReply(document=document)
    mock_get.return_value = reply

    with patch(
        "nitric.sdk.v1.DocumentsClient._get_method_function", mock_grpc_method_getter
    ):
        client = DocumentsClient()
        document = client.get_document("collection_name", "doc_key")

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("GetDocument")
    # TODO: Should this just return the doc, rather than the full dict?
    assert document == {"document": {"doc_key": "doc_value"}}


# Update
def test_update_document():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_create = Mock()
    # mock_create.return_value.topics = []

    test_document = {"content": "some text content"}

    with patch(
        "nitric.sdk.v1.DocumentsClient._get_method_function", mock_grpc_method_getter
    ):
        client = DocumentsClient()
        client.update_document("collection_name", "doc_key", test_document)

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("UpdateDocument")

    # Ensure the get topics method is called with the expected input
    mock_create.assert_called_once()  # No input data required to get topics
    assert mock_create.call_args.args[0].collection == "collection_name"
    assert mock_create.call_args.args[0].key == "doc_key"
    assert mock_create.call_args.args[0].document["content"] == "some text content"


# TODO: test update non-existent document


# Delete
def test_delete_document():
    mock_grpc_method_getter = Mock()
    mock_grpc_method_getter.return_value = mock_create = Mock()
    # mock_create.return_value.topics = []

    test_document = {"content": "some text content"}

    with patch(
        "nitric.sdk.v1.DocumentsClient._get_method_function", mock_grpc_method_getter
    ):
        client = DocumentsClient()
        client.delete_document("collection_name", "doc_key")

    # Ensure the correct gRPC method is retrieved
    mock_grpc_method_getter.assert_called_with("DeleteDocument")

    # Ensure the get topics method is called with the expected input
    mock_create.assert_called_once()  # No input data required to get topics
    assert mock_create.call_args.args[0].collection == "collection_name"
    assert mock_create.call_args.args[0].key == "doc_key"


def test_grpc_methods():
    client = DocumentsClient()
    assert (
        client._get_method_function("CreateDocument")._method
        == b"/nitric.v1.documents.Documents/CreateDocument"
    )
    assert (
        client._get_method_function("GetDocument")._method
        == b"/nitric.v1.documents.Documents/GetDocument"
    )
    assert (
        client._get_method_function("UpdateDocument")._method
        == b"/nitric.v1.documents.Documents/UpdateDocument"
    )
    assert (
        client._get_method_function("DeleteDocument")._method
        == b"/nitric.v1.documents.Documents/DeleteDocument"
    )


def test_create_client():
    client = DocumentsClient()
