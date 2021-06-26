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
from nitric.api._utils import new_default_channel
from nitric.proto.nitric.storage.v1 import StorageStub


class StorageClient(object):
    """
    Nitric generic blob storage client.

    This client insulates application code from stack specific blob store operations or SDKs.
    """

    def __init__(self, bucket: str):
        """
        Construct a Nitric Event Client.

        :param bucket: name of the bucket to perform operations on.
        """
        self.bucket = bucket
        self._stub = StorageStub(channel=new_default_channel())

    async def write(self, key: str, body: bytes):
        """
        Write a file to the bucket under the given key.

        :param key: key within the bucket, where the file should be stored.
        :param body: data to be stored.
        """
        await self._stub.write(bucket_name=self.bucket, key=key, body=body)

    async def read(self, key: str) -> bytes:
        """
        Retrieve an existing file.

        :param key: key for the file to retrieve.
        :return: the file as bytes.
        """
        response = await self._stub.read(bucket_name=self.bucket, key=key)
        return response.body

    async def delete(self, key: str):
        """
        Delete an existing file.

        :param key: key of the file to delete.
        """
        await self._stub.delete(bucket_name=self.bucket, key=key)
