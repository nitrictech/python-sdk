from nitric.proto import documents
from nitric.proto import documents_service
from nitric.sdk.v1._base_client import BaseClient
from google.protobuf.struct_pb2 import Struct
from google.protobuf.json_format import MessageToDict
from nitric.proto.v1.documents_pb2 import DocumentGetResponse


class DocumentsClient(BaseClient):
    """
    Nitric generic document store/db client.

    This client insulates application code from stack specific document CRUD operations or SDKs.
    """

    def __init__(self):
        """Construct a new DocumentClient."""
        super(self.__class__, self).__init__()
        self._stub = documents_service.DocumentStub(self._channel)

    def create_document(self, collection: str, key: str, document: dict):
        """Create a new document with the specified key in the specified collection."""
        doc_struct = Struct()
        doc_struct.update(document)
        request = documents.DocumentCreateRequest(
            collection=collection, key=key, document=doc_struct
        )
        return self._exec("Create", request)

    def get_document(self, collection: str, key: str) -> dict:
        """Retrieve a document from the specified collection by its key."""
        request = documents.DocumentGetRequest(collection=collection, key=key)
        reply: DocumentGetResponse = self._exec("Get", request)
        document = MessageToDict(reply)["document"]
        return document

    def update_document(self, collection: str, key: str, document: dict):
        """Update the contents of an existing document."""
        doc_struct = Struct()
        doc_struct.update(document)
        request = documents.DocumentUpdateRequest(
            collection=collection, key=key, document=doc_struct
        )
        return self._exec("Update", request)

    def delete_document(self, collection: str, key: str):
        """Delete the specified document from the collection."""
        request = documents.DocumentDeleteRequest(collection=collection, key=key)
        return self._exec("Delete", request)
