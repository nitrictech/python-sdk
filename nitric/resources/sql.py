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

from typing import Union

from grpclib import GRPCError
from grpclib.client import Channel

from nitric.exception import exception_from_grpc_error
from nitric.proto.resources.v1 import (
    SqlDatabaseResource,
    SqlDatabaseMigrations,
    ResourceDeclareRequest,
    ResourceIdentifier,
    ResourceType,
)
from nitric.resources.resource import Resource as BaseResource
from nitric.channel import ChannelManager
from nitric.application import Nitric

from nitric.proto.sql.v1 import SqlStub, SqlConnectionStringRequest


class Sql(BaseResource):
    """A SQL Database."""

    _channel: Channel
    _sql_stub: SqlStub
    name: str
    migrations: Union[str, None]

    def __init__(self, name: str, migrations: Union[str, None] = None):
        """Construct a new SQL Database."""
        super().__init__(name)

        self._channel: Union[Channel, None] = ChannelManager.get_channel()
        self._sql_stub = SqlStub(channel=self._channel)
        self.name = name
        self.migrations = migrations

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    id=ResourceIdentifier(name=self.name, type=ResourceType.SqlDatabase),
                    sql_database=SqlDatabaseResource(
                        migrations=SqlDatabaseMigrations(migrations_path=self.migrations if self.migrations else "")
                    ),
                ),
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    async def connection_string(self) -> str:
        """Return the connection string for this SQL Database."""
        response = await self._sql_stub.connection_string(SqlConnectionStringRequest(database_name=self.name))

        return response.connection_string


def sql(name: str, migrations: Union[str, None] = None) -> Sql:
    """
    Create and register a sql database.

    If a sql databse has already been registered with the same name, the original reference will be reused.
    """
    return Nitric._create_resource(Sql, name, migrations)
