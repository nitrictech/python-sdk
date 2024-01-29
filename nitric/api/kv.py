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
from __future__ import annotations

from typing import Optional

from grpclib.client import Channel

from nitric.proto.KeyValue.v1 import (
    KeyValueStub,
    ValueRef,
    KeyValueGetRequest,
    KeyValueSetRequest,
    KeyValueDeleteRequest,
)

from nitric.utils import new_default_channel
from typing import TypeVar, Generic

T = TypeVar("T")


class KVStore(object, Generic[T]):
    """
    Nitric client for interacting with key value stores.

    This client insulates application code from stack specific event operations or SDKs.
    """

    _kv_stub: KeyValueStub

    def __init__(self, name: str):
        """Construct a Nitric Document Client."""
        self._channel: Optional[Channel] = new_default_channel()
        self._kv_stub = KeyValueStub(channel=self._channel)
        self.name = name

    def __del__(self):
        # close the channel when this client is destroyed
        if self._channel is not None:
            self._channel.close()

    async def get(self, key: str) -> T:
        """Return a value from the key value store."""
        ref = ValueRef(store=self.name, key=key)

        req = KeyValueGetRequest(ref=ref)

        resp = await self._kv_stub.get(key_value_get_request=req)

        return resp.value

    async def delete(self, key: str) -> None:
        """Delete a key from the key value store."""
        ref = ValueRef(store=self.name, key=key)

        req = KeyValueDeleteRequest(ref=ref)

        await self._kv_stub.delete(key_value_delete_request=req)

    async def set(self, key: str, value: T) -> None:
        """Set a key and value in the key value store."""
        ref = ValueRef(store=self.name, key=key)

        req = KeyValueSetRequest(ref=ref)

        await self._kv_stub.set(key_value_set_request=req)
