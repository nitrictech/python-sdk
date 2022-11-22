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

from nitric.api.exception import exception_from_grpc_error
from typing import List, Union
from enum import Enum
from grpclib import GRPCError

from nitric.application import Nitric
from nitric.api.secrets import Secrets, SecretContainerRef
from nitric.proto.nitric.resource.v1 import (
    Resource,
    ResourceType,
    Action,
    ResourceDeclareRequest,
)

from nitric.resources.base import SecureResource


class SecretPermission(Enum):
    """Available permissions that can be requested for secret resources."""

    accessing = "accessing"
    putting = "putting"


class Secret(SecureResource):
    """A secret resource, used for storing and retrieving secret versions and values."""

    name: str
    actions: List[Action]

    def __init__(self, name: str):
        """Construct a new secret resource reference."""
        super().__init__()
        self.name = name

    def _to_resource(self) -> Resource:
        return Resource(name=self.name, type=ResourceType.Secret)

    async def _register(self):
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(resource=self._to_resource())
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    def _perms_to_actions(self, *args: Union[SecretPermission, str]) -> List[Action]:
        permissions_actions_map = {
            SecretPermission.accessing: [Action.SecretAccess],
            SecretPermission.putting: [Action.SecretPut],
        }
        # convert strings to the enum value where needed
        perms = [
            permission if isinstance(permission, SecretPermission) else SecretPermission[permission.lower()]
            for permission in args
        ]

        return [action for perm in perms for action in permissions_actions_map[perm]]

    def allow(self, *args: Union[SecretPermission, str]) -> SecretContainerRef:
        """Request the specified permissions to this resource."""
        self._register_policy(*args)

        return Secrets().secret(self.name)


#
def secret(name: str) -> Secret:
    """
    Create and registers a secret.

    If a secret has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Secret, name)
