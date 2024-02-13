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

from nitric.api.kv import KVStore
from nitric.exception import exception_from_grpc_error
from typing import List, Literal
from grpclib import GRPCError
from nitric.application import Nitric
from nitric.proto.resources.v1 import (
    KeyValueStoreResource,
    ResourceIdentifier,
    ResourceType,
    Action,
    ResourceDeclareRequest,
)
from nitric.resources.resource import SecureResource


KVPermission = Literal["getting", "setting", "deleting"]


class KVStoreResource(SecureResource):
    """A key value store resource."""

    def __init__(self, name: str):
        """Construct a new key value store."""
        super().__init__()
        self.name = name

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    id=self._to_resource(), key_value_store=KeyValueStoreResource()
                )
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    def _to_resource(self) -> ResourceIdentifier:
        return ResourceIdentifier(name=self.name, type=ResourceType.KeyValueStore)

    def _perms_to_actions(self, *args: KVPermission) -> List[Action]:
        permission_actions_map: dict[KVPermission, List[Action]] = {
            "getting": [Action.KeyValueStoreRead],
            "setting": [Action.KeyValueStoreWrite],
            "deleting": [Action.KeyValueStoreDelete],
        }

        return [action for perm in args for action in permission_actions_map[perm]]

    def allow(self, perm: KVPermission, *args: KVPermission) -> KVStore:
        """Request the required permissions for this collection."""
        # Ensure registration of the resource is complete before requesting permissions.
        str_args = [str(perm)] + [str(permission) for permission in args]
        self._register_policy(*str_args)

        return KVStore(self.name)


def kv(name: str) -> KVStoreResource:
    """
    Create and register a key value store.

    If a key value store has already been registered with the same name, the original reference will be reused.
    """
    # type ignored because the register call is treated as protected.
    return Nitric._create_resource(KVStore, name)  # type: ignore
