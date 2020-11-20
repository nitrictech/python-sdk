from nitric.proto import storage
from nitric.proto import storage_service
from nitric.sdk.v1._base_client import BaseClient


class StorageClient(BaseClient):
    """
    Nitric generic blob storage client.

    This client insulates application code from stack specific blob store operations or SDKs.
    """

    def __init__(self):
        """Construct a new StorageClient."""
        super(self.__class__, self).__init__()
        self._stub = storage_service.StorageStub(self._channel)

    def put(self, bucket_name: str, key: str, body: bytes):
        """
        Store a file.

        :param bucket_name: name of the bucket to store the data in.
        :param key: key within the bucket, where the file should be stored.
        :param body: data to be stored.
        :return: storage result.
        """
        request = storage.PutRequest(bucketName=bucket_name, key=key, body=body)
        response = self._exec("Put", request)
        return response

    def get(self, bucket_name: str, key: str) -> bytes:
        """
        Retrieve an existing file.

        :param bucket_name: name of the bucket where the file was stored.
        :param key: key for the file to retrieve.
        :return: the file as bytes.
        """
        request = storage.GetRequest(bucketName=bucket_name, key=key)
        response = self._exec("Get", request)
        # TODO: just return the bytes
        return response
