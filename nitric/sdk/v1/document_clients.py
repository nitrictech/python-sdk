from nitric.proto import documents
from nitric.proto import documents_service
from nitric.sdk.v1._base_client import BaseClient
from google.protobuf.struct_pb2 import Struct
from google.protobuf.json_format import MessageToDict
from nitric.proto.v1.documents_pb2 import GetDocumentReply


class DocumentsClient(BaseClient):
    """
    Nitric generic document store/db client.

    This client insulates application code from stack specific document CRUD operations or SDKs.
    """

    def __init__(self):
        """Construct a new DocumentClient."""
        super(self.__class__, self).__init__()
        self._stub = documents_service.DocumentsStub(self._channel)

    def create_document(self, collection: str, key: str, document: dict):
        """Create a new document with the specified key in the specified collection."""
        doc_struct = Struct()
        doc_struct.update(document)
        request = documents.CreateDocumentRequest(
            collection=collection, key=key, document=doc_struct
        )
        return self._exec("CreateDocument", request)

    def get_document(self, collection: str, key: str) -> dict:
        """Retrieve a document from the specified collection by its key."""
        request = documents.GetDocumentRequest(collection=collection, key=key)
        reply: GetDocumentReply = self._exec("GetDocument", request)
        document = MessageToDict(reply)
        return document

    def update_document(self, collection: str, key: str, document: dict):
        """Update the contents of an existing document."""
        doc_struct = Struct()
        doc_struct.update(document)
        request = documents.UpdateDocumentRequest(
            collection=collection, key=key, document=doc_struct
        )
        return self._exec("UpdateDocument", request)

    def delete_document(self, collection: str, key: str):
        """Delete the specified document from the collection."""
        request = documents.DeleteDocumentRequest(collection=collection, key=key)
        return self._exec("DeleteDocument", request)
