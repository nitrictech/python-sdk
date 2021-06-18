#
# Copyright (c) 2021 Nitric Technologies Pty Ltd.
#
# This file is part of Nitric Python 3 SDK.
# See https://github.com/nitrictech/python-sdk for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from nitric.proto import storage
from nitric.proto import storage_service
from nitric.api._base_client import BaseClient


class StorageClient(BaseClient):
    """
    Nitric generic blob storage client.

    This client insulates application code from stack specific blob store operations or SDKs.
    """

    def __init__(self):
        """Construct a new StorageClient."""
        super(self.__class__, self).__init__()
        self._stub = storage_service.StorageStub(self._channel)

    def write(self, bucket_name: str, key: str, body: bytes):
        """
        Store a file.

        :param bucket_name: name of the bucket to store the data in.
        :param key: key within the bucket, where the file should be stored.
        :param body: data to be stored.
        :return: storage result.
        """
        request = storage.StorageWriteRequest(bucket_name=bucket_name, key=key, body=body)
        response = self._exec("Write", request)
        return response

    def read(self, bucket_name: str, key: str) -> bytes:
        """
        Retrieve an existing file.

        :param bucket_name: name of the bucket where the file was stored.
        :param key: key for the file to retrieve.
        :return: the file as bytes.
        """
        request = storage.StorageReadRequest(bucket_name=bucket_name, key=key)
        response = self._exec("Read", request)
        return response.body
