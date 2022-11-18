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
from examples.documents.sub_col_query import documents_sub_col_query
from nitric.proto.nitric.document.v1 import (
    Collection,
    DocumentGetResponse,
    DocumentQueryStreamResponse,
    Document,
    Key,
    DocumentGetRequest,
)
from examples.documents.set import documents_set
from examples.documents.get import documents_get
from examples.documents.delete import documents_delete
from examples.documents.paged_results import documents_paged_results
from examples.documents.query import documents_query
from examples.documents.query_filter import documents_query_filter
from examples.documents.query_limits import documents_query_limits
from examples.documents.refs import documents_refs
from examples.documents.streamed import documents_streamed
from examples.documents.sub_doc_query import documents_sub_doc_query

import pytest
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock
from betterproto.lib.google.protobuf import Struct, Value


class DocumentsExamplesTest(IsolatedAsyncioTestCase):
    async def test_set_document(self):
        mock_set = AsyncMock()

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.set", mock_set):
            await documents_set()

        mock_set.assert_called_once()

    async def test_get_document(self):
        mock_get = AsyncMock()
        mock_get.return_value = DocumentGetResponse(
            document=Document(
                key=Key(id="nitric", collection=Collection(name="products")),
                content=Struct(
                    fields={
                        "nitric": Value(number_value=1.0),
                    },
                ),
            ),
        )

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.get", mock_get):
            await documents_get()

        mock_get.assert_called_once_with(
            document_get_request=DocumentGetRequest(
                key=Key(
                    collection=Collection(name="products"),
                    id="nitric",
                )
            )
        )

    async def test_delete_document(self):
        mock_delete = AsyncMock()

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.delete", mock_delete):
            await documents_delete()

        mock_delete.assert_called_once()

    async def test_query_document(self):
        mock_query = AsyncMock()

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.query", mock_query):
            await documents_query()

        mock_query.assert_called_once()

    async def test_paged_results_document(self):
        mock_query = AsyncMock()

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.query", mock_query):
            await documents_paged_results()

        mock_query.assert_called()

    async def test_query_filter_document(self):
        mock_query = AsyncMock()

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.query", mock_query):
            await documents_query_filter()

        mock_query.assert_called_once()

    async def test_query_limits_document(self):
        mock_query = AsyncMock()

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.query", mock_query):
            await documents_query_limits()

        mock_query.assert_called_once()

    async def test_sub_doc_query_document(self):
        mock_query = AsyncMock()

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.query", mock_query):
            await documents_sub_doc_query()

        mock_query.assert_called_once()

    async def test_sub_col_query_document(self):
        mock_query = AsyncMock()

        with patch("nitric.proto.nitric.document.v1.DocumentServiceStub.query", mock_query):
            await documents_sub_col_query()

        mock_query.assert_called_once()

    async def test_streamed_document(self):
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
            await documents_streamed()

        self.assertEqual(3, stream_calls)

    def test_refs_document(self):
        try:
            documents_refs()
        except:
            pytest.fail()
