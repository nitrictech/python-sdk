from nitric.proto import key_value
from nitric.proto import key_value_service
from nitric.api._base_client import BaseClient
from google.protobuf.struct_pb2 import Struct
from google.protobuf.json_format import MessageToDict
from nitric.proto.kv.v1.kv_pb2 import KeyValueGetResponse


class KeyValueClient(BaseClient):
    """
    Nitric generic document store/db client.

    This client insulates application code from stack specific document CRUD operations or SDKs.
    """

    def __init__(self):
        """Construct a new DocumentClient."""
        super(self.__class__, self).__init__()
        self._stub = key_value_service.KeyValueStub(self._channel)

    def put(self, collection: str, key: str, value: dict):
        """Create a new document with the specified key in the specified collection."""
        value_struct = Struct()
        value_struct.update(value)
        request = key_value.KeyValuePutRequest(collection=collection, key=key, value=value_struct)
        return self._exec("Put", request)

    def get(self, collection: str, key: str) -> dict:
        """Retrieve a document from the specified collection by its key."""
        request = key_value.KeyValueGetRequest(collection=collection, key=key)
        reply: KeyValueGetResponse = self._exec("Get", request)
        document = MessageToDict(reply)["value"]
        return document

    def delete(self, collection: str, key: str):
        """Delete the specified document from the collection."""
        request = key_value.KeyValueDeleteRequest(collection=collection, key=key)
        return self._exec("Delete", request)
