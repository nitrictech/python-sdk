from grpc._channel import _InactiveRpcError, _UnaryUnaryMultiCallable

from nitric.proto import documents
from nitric.proto import documents_service
from nitric.sdk.v1._base_client import BaseClient
from google.protobuf.struct_pb2 import Struct

class DocumentsClient(BaseClient):

    def __init__(self):
        super(self.__class__, self).__init__()
        self._stub = documents_service.DocumentsStub(self._channel)

    def create_document(self, collection: str, key: str, document: dict):
        doc_struct = Struct()
        doc_struct.update(document)
        request = documents.CreateDocumentRequest(collection=collection, key=key, document=doc_struct)
        return self._exec('CreateDocument', request)

    def get_document(self, collection: str, key: str):
        request = documents.GetDocumentRequest(collection=collection, key=key)
        return self._exec('GetDocument', request)

    def update_document(self, collection: str, key: str, document: dict):
        doc_struct = Struct()
        doc_struct.update(document)
        request = documents.UpdateDocumentRequest(collection=collection, key=key, document=doc_struct)
        return self._exec('UpdateDocument', request)

    def delete_document(self, collection: str, key: str):
        request = documents.DeleteDocumentRequest(collection=collection, key=key)
        return self._exec('DeleteDocument', request)
