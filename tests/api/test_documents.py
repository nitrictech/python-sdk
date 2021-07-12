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

import pytest
from betterproto.lib.google.protobuf import Struct, Value

from nitric.api import Events, Event
from nitric.api.documents import QueryBuilder, Operator, Documents
from nitric.proto.nitric.document.v1 import (
    Key,
    Collection,
    DocumentGetResponse,
    Document,
    DocumentQueryResponse,
    Expression,
    ExpressionValue,
    DocumentQueryStreamResponse,
)
from nitric.proto.nitric.event.v1 import TopicListResponse, NitricTopic
from nitric.utils import _struct_from_dict


class Object(object):
    pass


class DocumentsClientTest(IsolatedAsyncioTestCase):
    async def test_set_document(self):
        mock_set = AsyncMock()

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.set", mock_set):
            await Documents().collection("a").doc("b").set({"a": 1})

        mock_set.assert_called_once_with(
            key=Key(
                collection=Collection(name="a"),
                id="b",
            ),
            content=Struct(
                fields={
                    "a": Value(number_value=1.0),
                },
            ),
        )

    async def test_set_subcollection_document(self):
        mock_set = AsyncMock()

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.set", mock_set):
            await Documents().collection("a").doc("b").collection("c").doc("d").set({"a": 1})

        mock_set.assert_called_once_with(
            key=Key(
                collection=Collection(
                    name="c",
                    parent=Key(
                        collection=Collection(name="a"),
                        id="b",
                    ),
                ),
                id="d",
            ),
            content=Struct(
                fields={
                    "a": Value(number_value=1.0),
                },
            ),
        )

    async def test_get_document(self):
        mock_get = AsyncMock()
        mock_get.return_value = DocumentGetResponse(
            document=Document(
                content=Struct(
                    fields={
                        "a": Value(number_value=1.0),
                    },
                ),
            ),
        )

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.get", mock_get):
            response = await Documents().collection("a").doc("b").get()

        mock_get.assert_called_once_with(
            key=Key(
                collection=Collection(name="a"),
                id="b",
            )
        )
        self.assertEqual(1.0, response["a"])

    async def test_get_subcollection_document(self):
        mock_get = AsyncMock()
        mock_get.return_value = DocumentGetResponse(
            document=Document(
                content=Struct(
                    fields={
                        "a": Value(number_value=1.0),
                    },
                ),
            ),
        )

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.get", mock_get):
            response = await Documents().collection("a").doc("b").collection("c").doc("d").get()

        mock_get.assert_called_once_with(
            key=Key(
                collection=Collection(
                    name="c",
                    parent=Key(
                        collection=Collection(name="a"),
                        id="b",
                    ),
                ),
                id="d",
            )
        )
        self.assertEqual(1.0, response["a"])

    async def test_delete_document(self):
        mock_delete = AsyncMock()

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.delete", mock_delete):
            await Documents().collection("a").doc("b").delete()

        mock_delete.assert_called_once_with(
            key=Key(
                collection=Collection(name="a"),
                id="b",
            )
        )

    async def test_delete_subcollection_document(self):
        mock_delete = AsyncMock()

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.delete", mock_delete):
            await Documents().collection("a").doc("b").collection("c").doc("d").delete()

        mock_delete.assert_called_once_with(
            key=Key(
                collection=Collection(
                    name="c",
                    parent=Key(
                        collection=Collection(name="a"),
                        id="b",
                    ),
                ),
                id="d",
            )
        )

    async def test_nested_subcollections_fail(self):
        with pytest.raises(Exception) as e:
            Documents().collection("a").doc("b").collection("c").doc("d").collection("should-fail")

        self.assertIn("sub-collections may only be nested 1 deep", str(e.value))

    async def test_collection_query_fetch(self):
        mock_query = AsyncMock()
        mock_query.return_value = DocumentQueryResponse(
            documents=[Document(content=Struct(fields={"a": Value(number_value=i)})) for i in range(3)],
            paging_token={"b": "c"},
        )

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.query", mock_query):
            results = (
                await Documents()
                .collection("a")
                .query()
                .where("name", "startsWith", "test")
                .where("age", ">", 3)
                .where("dollar", "<", 2.0)
                .where("true", "=", True)
                .limit(3)
                .fetch()
            )

        mock_query.assert_called_once_with(
            collection=Collection(name="a"),
            expressions=[
                Expression(operand="name", operator="startsWith", value=ExpressionValue(string_value="test")),
                Expression(operand="age", operator=">", value=ExpressionValue(int_value=3)),
                Expression(operand="dollar", operator="<", value=ExpressionValue(double_value=2.0)),
                Expression(operand="true", operator="=", value=ExpressionValue(bool_value=True)),
            ],
            limit=3,
            paging_token=None,
        )

        self.assertEqual({"b": "c"}, results.paging_token)
        self.assertEqual([{"a": i} for i in range(3)], [doc.content for doc in results.documents])

    async def test_collection_query_stream(self):
        stream_calls = 0
        call_args = {}

        async def mock_stream(self, **kwargs):
            nonlocal call_args
            nonlocal stream_calls
            call_args = kwargs
            for i in range(3):
                stream_calls += 1
                yield DocumentQueryStreamResponse(
                    document=Document(content=Struct(fields={"a": Value(number_value=i)}))
                )

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.query_stream", mock_stream):
            results = []
            async for result in Documents().collection("a").query().where("name", "startsWith", "test").stream():
                results.append(result)

        self.assertEqual(3, stream_calls)
        self.assertEqual(
            {
                "collection": Collection(name="a"),
                "expressions": [
                    Expression(operand="name", operator="startsWith", value=ExpressionValue(string_value="test"))
                ],
                "limit": 0,
            },
            call_args,
        )
        self.assertEqual([{"a": i} for i in range(3)], [doc.content for doc in results])


class QueryTest(IsolatedAsyncioTestCase):
    def test_query_repr(self):
        self.assertEqual(
            "Documents.collection(None).query().page_from(a).where(name starts_with test).limit(3)",
            QueryBuilder(documents=None, collection=None)
            .page_from("a")
            .where("name", Operator.starts_with, "test")
            .limit(3)
            .__repr__(),
        )

    def test_query_str(self):
        self.assertEqual(
            "Query(from None, paging token a, where name starts_with test, limit to 3 results)",
            QueryBuilder(documents=None, collection=None)
            .page_from("a")
            .where("name", Operator.starts_with, "test")
            .limit(3)
            .__str__(),
        )
