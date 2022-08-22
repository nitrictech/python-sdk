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

from nitric.resources import collection

from nitricapi.nitric.resource.v1 import Action

from betterproto.lib.google.protobuf import Struct, Value


from nitricapi.nitric.document.v1 import Key, Collection as DocumentCollection, DocumentGetResponse, Document


class Object(object):
    pass


class CollectionTest(IsolatedAsyncioTestCase):
    async def test_create_allow_writing(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await collection("test-collection").allow(["writing"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()
        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-collection")
        self.assertListEqual(
            mock_declare.call_args.kwargs["policy"].actions,
            [
                Action.CollectionDocumentWrite,
                Action.CollectionList,
            ],
        )

    async def test_create_allow_reading(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await collection("test-collection").allow(["reading"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()

        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-collection")
        self.assertListEqual(
            mock_declare.call_args.kwargs["policy"].actions,
            [
                Action.CollectionDocumentRead,
                Action.CollectionQuery,
                Action.CollectionList,
            ],
        )

    async def test_create_allow_deleting(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await collection("test-collection").allow(["deleting"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()
        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-collection")
        self.assertListEqual(
            mock_declare.call_args.kwargs["policy"].actions,
            [
                Action.CollectionDocumentDelete,
                Action.CollectionList,
            ],
        )

    async def test_create_allow_all(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await collection("test-collection").allow(["deleting", "reading", "writing"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()
        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-collection")
        self.assertListEqual(
            mock_declare.call_args.kwargs["policy"].actions,
            [
                Action.CollectionDocumentDelete,
                Action.CollectionList,
                Action.CollectionDocumentRead,
                Action.CollectionQuery,
                Action.CollectionList,
                Action.CollectionDocumentWrite,
                Action.CollectionList,
            ],
        )

    async def test_create_allow_all_reversed_policy(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await collection("test-collection").allow(["writing", "reading", "deleting"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()
        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-collection")
        self.assertListEqual(
            mock_declare.call_args.kwargs["policy"].actions,
            [
                Action.CollectionDocumentWrite,
                Action.CollectionList,
                Action.CollectionDocumentRead,
                Action.CollectionQuery,
                Action.CollectionList,
                Action.CollectionDocumentDelete,
                Action.CollectionList,
            ],
        )

    async def test_set_document(self):
        mock_set = AsyncMock()
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            with patch("nitricapi.nitric.document.v1.DocumentServiceStub.set", mock_set):
                collection_a = await collection("a").allow(["writing"])
                await collection_a.doc("b").set({"a": 1})

        mock_set.assert_called_once_with(
            key=Key(
                collection=DocumentCollection(name="a"),
                id="b",
            ),
            content=Struct(
                fields={
                    "a": Value(number_value=1.0),
                },
            ),
        )
        self.assertListEqual(
            mock_declare.call_args.kwargs["policy"].actions,
            [
                Action.CollectionDocumentWrite,
                Action.CollectionList,
            ],
        )

    async def test_get_document(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        mock_get = AsyncMock()
        mock_get.return_value = DocumentGetResponse(
            document=Document(
                key=Key(id="b", collection=DocumentCollection(name="a")),
                content=Struct(
                    fields={
                        "a": Value(number_value=1.0),
                    },
                ),
            ),
        )

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            with patch("nitricapi.nitric.document.v1.DocumentServiceStub.get", mock_get):
                collection_a = await collection("a").allow(["reading"])
                response = await collection_a.doc("b").get()

        mock_get.assert_called_once_with(
            key=Key(
                collection=DocumentCollection(name="a"),
                id="b",
            )
        )
        self.assertEqual(1.0, response.content["a"])
