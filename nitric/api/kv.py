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
from nitric.proto.nitric.kv.v1 import KeyValueStub
from betterproto.lib.google.protobuf import Struct


class KeyValueClient(object):
    """
    Nitric generic document store/db client.

    This client insulates application code from stack specific document CRUD operations or SDKs.
    """

    def __init__(self, collection: str):
        """
        Construct a new DocumentClient.

        :param collection: name of the key/value collection
        """
        self.collection = collection
        self._stub = KeyValueStub(channel=new_default_channel())

    async def put(self, key: str, value: dict):
        """Create a new document with the specified key."""
        await self._stub.put(collection=self.collection, key=key, value=Struct().from_dict(value))

    async def get(self, key: str) -> dict:
        """Retrieve a document from the specified key."""
        response = await self._stub.get(collection=self.collection, key=key)
        return response.value.to_dict()

    async def delete(self, key: str):
        """Delete the specified document from the collection."""
        await self._stub.delete(collection=self.collection, key=key)
