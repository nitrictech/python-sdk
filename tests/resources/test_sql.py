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
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

import pytest
from grpclib import GRPCError, Status

from nitric.exception import UnknownException
from nitric.proto.resources.v1 import (
    Action,
    PolicyResource,
    ResourceDeclareRequest,
    ResourceIdentifier,
    ResourceType,
    SqlDatabaseResource,
)
from nitric.proto.topics.v1 import TopicMessage, TopicPublishRequest
from nitric.resources import sql
from nitric.resources.topics import TopicRef
from nitric.utils import struct_from_dict

# pylint: disable=protected-access,missing-function-docstring,missing-class-docstring


class Object(object):
    pass


class MockAsyncChannel:
    def __init__(self):
        self.send = AsyncMock()
        self.close = Mock()
        self.done = Mock()


class SqlTest(IsolatedAsyncioTestCase):
    def test_declare_sql(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            sqldb = sql("test-sql")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(name="test-sql", type=ResourceType.SqlDatabase),
                sql_database=SqlDatabaseResource(),
            )
        )
