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
from unittest.mock import AsyncMock, patch

import pytest
from betterproto.lib.google.protobuf import Struct
from betterproto.lib.google.protobuf import Value as ProtoValue
from grpclib import GRPCError, Status

from nitric.exception import UnknownException
from nitric.proto.kvstore.v1 import (
    KvStoreDeleteKeyRequest,
    KvStoreGetValueRequest,
    KvStoreGetValueResponse,
    KvStoreSetValueRequest,
    Value,
    ValueRef,
)
from nitric.proto.resources.v1 import Action, PolicyResource, ResourceDeclareRequest, ResourceIdentifier, ResourceType
from nitric.resources import kv
from nitric.resources.kv import KeyValueStoreRef

# pylint: disable=protected-access,missing-function-docstring,missing-class-docstring


class Object(object):
    pass


class CollectionTest(IsolatedAsyncioTestCase):
    def test_create_allow_writing(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            kv("test-collection").allow("set")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[
                        Action.KeyValueStoreWrite,
                    ],
                    resources=[ResourceIdentifier(type=ResourceType.KeyValueStore, name="test-collection")],
                ),
            )
        )

    def test_create_allow_reading(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            kv("test-collection").allow("get")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[
                        Action.KeyValueStoreRead,
                    ],
                    resources=[ResourceIdentifier(type=ResourceType.KeyValueStore, name="test-collection")],
                ),
            )
        )

    def test_create_allow_deleting(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            kv("test-collection").allow("delete")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[
                        Action.KeyValueStoreDelete,
                    ],
                    resources=[ResourceIdentifier(type=ResourceType.KeyValueStore, name="test-collection")],
                ),
            )
        )

    def test_create_allow_all(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            kv("test-collection").allow("delete", "get", "set")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[
                        Action.KeyValueStoreDelete,
                        Action.KeyValueStoreRead,
                        Action.KeyValueStoreWrite,
                    ],
                    resources=[ResourceIdentifier(type=ResourceType.KeyValueStore, name="test-collection")],
                ),
            )
        )

    def test_create_allow_all_reversed_policy(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            kv("test-collection").allow("set", "get", "delete")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[
                        Action.KeyValueStoreWrite,
                        Action.KeyValueStoreRead,
                        Action.KeyValueStoreDelete,
                    ],
                    resources=[ResourceIdentifier(type=ResourceType.KeyValueStore, name="test-collection")],
                ),
            )
        )


class DocumentsClientTest(IsolatedAsyncioTestCase):
    async def test_set_value(self):
        mock_set = AsyncMock()

        with patch("nitric.proto.kvstore.v1.KvStoreStub.set_value", mock_set):
            await KeyValueStoreRef("a").set("b", {"a": 1})

        mock_set.assert_called_once_with(
            kv_store_set_value_request=KvStoreSetValueRequest(
                ref=ValueRef(store="a", key="b"),
                content=Struct(
                    fields={
                        "a": ProtoValue(number_value=1.0),
                    },
                ),
            )
        )

    async def test_get_value(self):
        mock_get = AsyncMock()
        mock_get.return_value = KvStoreGetValueResponse(
            value=Value(
                ref=ValueRef(store="a", key="b"),
                content=Struct(
                    fields={
                        "a": ProtoValue(number_value=1.0),
                    },
                ),
            ),
        )

        with patch("nitric.proto.kvstore.v1.KvStoreStub.get_value", mock_get):
            response = await KeyValueStoreRef("a").get("b")

        mock_get.assert_called_once_with(
            kv_store_get_value_request=KvStoreGetValueRequest(
                ref=ValueRef(
                    store="a",
                    key="b",
                ),
            )
        )
        self.assertEqual(1.0, response["a"])

    async def test_delete_document(self):
        mock_delete = AsyncMock()

        with patch("nitric.proto.kvstore.v1.KvStoreStub.delete_key", mock_delete):
            await KeyValueStoreRef("a").delete("b")

        mock_delete.assert_called_once_with(
            kv_store_delete_key_request=KvStoreDeleteKeyRequest(
                ref=ValueRef(
                    store="a",
                    key="b",
                )
            )
        )

    async def test_set_document_error(self):
        mock_set = AsyncMock()
        mock_set.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitric.proto.kvstore.v1.KvStoreStub.set_value", mock_set):
            with pytest.raises(UnknownException):
                await KeyValueStoreRef("a").set("b", {"a": 1})

    async def test_get_document_error(self):
        mock_get = AsyncMock()
        mock_get.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitric.proto.kvstore.v1.KvStoreStub.get_value", mock_get):
            with pytest.raises(UnknownException):
                await KeyValueStoreRef("a").get("b")

    async def test_delete_document_error(self):
        mock_delete = AsyncMock()
        mock_delete.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitric.proto.kvstore.v1.KvStoreStub.delete_key", mock_delete):
            with pytest.raises(UnknownException):
                await KeyValueStoreRef("a").delete("b")
