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
from unittest.mock import patch, AsyncMock

from betterproto.lib.google.protobuf import Struct

from nitric.api import Events, Event
from nitric.api.documents import QueryBuilder, Operator
from nitric.proto.nitric.event.v1 import TopicListResponse, NitricTopic
from nitric.utils import _struct_from_dict


class Object(object):
    pass


class DocumentsClientTest(IsolatedAsyncioTestCase):
    async def test_query_repr(self):
        self.assertEqual(
            "Documents.collection(None).query().page_from(a).where(name starts_with test).limit(3)",
            QueryBuilder(documents=None, collection=None)
            .page_from("a")
            .where("name", Operator.starts_with, "test")
            .limit(3)
            .__repr__(),
        )

    async def test_query_str(self):
        self.assertEqual(
            "Query(from None, paging token a, where name starts_with test, limit to 3 results)",
            QueryBuilder(documents=None, collection=None)
            .page_from("a")
            .where("name", Operator.starts_with, "test")
            .limit(3)
            .__str__(),
        )
