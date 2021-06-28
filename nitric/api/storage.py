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
from dataclasses import dataclass

from nitric.api._utils import new_default_channel
from nitric.proto.nitric.storage.v1 import StorageStub


class StorageClient(object):
    """
    Nitric generic blob storage client.

    This client insulates application code from stack specific blob store operations or SDKs.
    """

    def __init__(self):
        """Construct a Nitric Storage Client."""
        self._storage_stub = StorageStub(channel=new_default_channel())

    def bucket(self, name: str):
        return Bucket(_storage_stub=self._storage_stub, name=name)


@dataclass(frozen=True, order=True)
class Bucket(object):
    _storage_stub: StorageStub
    name: str

    def file(self, key: str):
        return File(_storage_stub=self._storage_stub, _bucket=self.name, key=key)


@dataclass(frozen=True, order=True)
class File(object):
    _storage_stub: StorageStub
    _bucket: str
    key: str

    async def write(self, body: bytes):
        """
        Write the bytes as the content of this file.

        Will create the file if it doesn't already exist.
        """
        await self._storage_stub.write(bucket_name=self._bucket, key=self.key, body=body)

    async def read(self) -> bytes:
        """Read this files contents from the bucket."""
        response = await self._storage_stub.read(bucket_name=self._bucket, key=self.key)
        return response.body

    async def delete(self):
        """Delete this file from the bucket."""
        await self._storage_stub.delete(bucket_name=self._bucket, key=self.key)
