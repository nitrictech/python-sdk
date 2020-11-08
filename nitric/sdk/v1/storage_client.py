from nitric.proto import storage
from nitric.proto import storage_service
from nitric.sdk.v1._base_client import BaseClient


class StorageClient(BaseClient):

    def __init__(self):
        super(self.__class__, self).__init__()
        self._stub = storage_service.StorageStub(self._channel)

    def put(self, bucket_name: str, key: str, body: bytes):
        request = storage.PutRequest(bucketName=bucket_name, key=key, body=body)
        response = self._exec("Put", request)
        return response

    def get(self, bucket_name: str, key: str):
        request = storage.GetRequest(bucketName=bucket_name, key=key)
        response = self._exec("Get", request)
        return response
