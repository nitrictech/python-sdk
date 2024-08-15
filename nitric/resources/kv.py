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

from typing import Any, List, Literal, AsyncIterator, Optional

from grpclib import GRPCError
from grpclib.client import Channel

from nitric.application import Nitric
from nitric.exception import exception_from_grpc_error
from nitric.proto.kvstore.v1 import (
    Store,
    KvStoreScanKeysRequest,
    KvStoreDeleteKeyRequest,
    KvStoreGetValueRequest,
    KvStoreSetValueRequest,
    KvStoreStub,
    ValueRef,
)
from nitric.proto.resources.v1 import (
    Action,
    KeyValueStoreResource,
    ResourceDeclareRequest,
    ResourceIdentifier,
    ResourceType,
)
from nitric.resources.resource import SecureResource
from nitric.utils import dict_from_struct, struct_from_dict
from nitric.channel import ChannelManager


class KeyValueStoreRef:
    """A reference to a deployed key value store, used to interact with the key value store at runtime."""

    _kv_stub: KvStoreStub
    _channel: Channel
    name: str

    def __init__(self, name: str):
        """Construct a reference to a deployed key value store."""
        self._channel: Channel = ChannelManager.get_channel()
        self._kv_stub = KvStoreStub(channel=self._channel)
        self.name = name

    def __del__(self):
        # close the channel when this client is destroyed
        if self._channel is not None:
            self._channel.close()

    async def set(self, key: str, value: dict[str, Any]) -> None:
        """Set a key and value in the key value store."""
        ref = ValueRef(store=self.name, key=key)

        req = KvStoreSetValueRequest(ref=ref, content=struct_from_dict(value))

        try:
            await self._kv_stub.set_value(kv_store_set_value_request=req)
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    async def get(self, key: str) -> dict[str, Any]:
        """Return a value from the key value store."""
        ref = ValueRef(store=self.name, key=key)

        req = KvStoreGetValueRequest(ref=ref)

        try:
            resp = await self._kv_stub.get_value(kv_store_get_value_request=req)

            return dict_from_struct(resp.value.content)
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    async def keys(self, prefix: Optional[str] = "") -> AsyncIterator[str]:
        """Return a list of keys from the key value store."""
        if prefix is None:
            prefix = ""

        req = KvStoreScanKeysRequest(
            store=Store(name=self.name),
            prefix=prefix,
        )

        try:
            response_iterator = self._kv_stub.scan_keys(kv_store_scan_keys_request=req)
            async for item in response_iterator:
                yield item.key
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

        return

    async def delete(self, key: str) -> None:
        """Delete a key from the key value store."""
        ref = ValueRef(store=self.name, key=key)

        req = KvStoreDeleteKeyRequest(ref=ref)

        try:
            await self._kv_stub.delete_key(kv_store_delete_key_request=req)
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err


KVPermission = Literal["get", "set", "delete"]


class KeyValueStore(SecureResource):
    """A key value store resource."""

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    id=self._to_resource_id(), key_value_store=KeyValueStoreResource()
                )
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    def _to_resource_id(self) -> ResourceIdentifier:
        return ResourceIdentifier(name=self.name, type=ResourceType.KeyValueStore)

    def _perms_to_actions(self, *args: KVPermission) -> List[Action]:
        permission_actions_map: dict[KVPermission, List[Action]] = {
            "get": [Action.KeyValueStoreRead],
            "set": [Action.KeyValueStoreWrite],
            "delete": [Action.KeyValueStoreDelete],
        }

        return [action for perm in args for action in permission_actions_map[perm]]

    def allow(self, perm: KVPermission, *args: KVPermission) -> KeyValueStoreRef:
        """Request the required permissions for this collection."""
        # Ensure registration of the resource is complete before requesting permissions.
        str_args = [str(perm)] + [str(permission) for permission in args]
        self._register_policy(*str_args)

        return KeyValueStoreRef(self.name)


def kv(name: str) -> KeyValueStore:
    """
    Create and register a key value store.

    If a key value store has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(KeyValueStore, name)  # type: ignore pylint: disable=protected-access
