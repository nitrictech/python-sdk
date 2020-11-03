from nitric.proto import storage
from nitric.proto import storage_service
from nitric.sdk.v1._base_client import BaseClient


class StorageClient(BaseClient):

    def __init__(self):
        super(self.__class__, self).__init__()
        self._stub = storage_service.StorageStub(self._channel)

    def put(self, bucket_name: str, key: str, body: bytes):
        response = self._stub.Put(storage.PutRequest(bucket_name, key, body))
        return response

    def get(self, bucket_name: str, key: str):
        response: storage.GetReply = self._stub.Get(storage.GetRequest(bucket_name, key))
        return response