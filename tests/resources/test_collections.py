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

from nitricapi.nitric.resource.v1 import Action, ResourceType, PolicyResource, ResourceDeclareRequest, Resource

from betterproto.lib.google.protobuf import Struct, Value


from nitricapi.nitric.document.v1 import Key, Collection as DocumentCollection, DocumentGetResponse, Document


class Object(object):
    pass


class CollectionTest(IsolatedAsyncioTestCase):
    def test_create_allow_writing(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            collection("test-collection").allow("writing")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(resource_declare_request=ResourceDeclareRequest(
            resource=Resource(type=ResourceType.Policy),
            policy=PolicyResource(
                principals=[Resource(type=ResourceType.Function)],
                actions=[
                    Action.CollectionDocumentWrite,
                    Action.CollectionList,
                ],
                resources=[Resource(type=ResourceType.Collection, name="test-collection")]
            )
        ))

    def test_create_allow_reading(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            collection("test-collection").allow("reading")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(resource_declare_request=ResourceDeclareRequest(
            resource=Resource(type=ResourceType.Policy),
            policy=PolicyResource(
                principals=[Resource(type=ResourceType.Function)],
                actions=[
                    Action.CollectionDocumentRead,
                    Action.CollectionQuery,
                    Action.CollectionList,
                ],
                resources=[Resource(type=ResourceType.Collection, name="test-collection")]
            )
        ))

    def test_create_allow_deleting(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            collection("test-collection").allow("deleting")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(resource_declare_request=ResourceDeclareRequest(
            resource=Resource(type=ResourceType.Policy),
            policy=PolicyResource(
                principals=[Resource(type=ResourceType.Function)],
                actions=[
                    Action.CollectionDocumentDelete,
                    Action.CollectionList,
                ],
                resources=[Resource(type=ResourceType.Collection, name="test-collection")]
            )
        ))

    def test_create_allow_all(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            collection("test-collection").allow("deleting", "reading", "writing")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(resource_declare_request=ResourceDeclareRequest(
            resource=Resource(type=ResourceType.Policy),
            policy=PolicyResource(
                principals=[Resource(type=ResourceType.Function)],
                actions=[
                    Action.CollectionDocumentDelete,
                    Action.CollectionList,
                    Action.CollectionDocumentRead,
                    Action.CollectionQuery,
                    Action.CollectionList,
                    Action.CollectionDocumentWrite,
                    Action.CollectionList,
                ],
                resources=[Resource(type=ResourceType.Collection, name="test-collection")]
            )
        ))

    def test_create_allow_all_reversed_policy(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            collection("test-collection").allow("writing", "reading", "deleting")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(resource_declare_request=ResourceDeclareRequest(
            resource=Resource(type=ResourceType.Policy),
            policy=PolicyResource(
                principals=[Resource(type=ResourceType.Function)],
                actions=[
                    Action.CollectionDocumentWrite,
                    Action.CollectionList,
                    Action.CollectionDocumentRead,
                    Action.CollectionQuery,
                    Action.CollectionList,
                    Action.CollectionDocumentDelete,
                    Action.CollectionList,
                ],
                resources=[Resource(type=ResourceType.Collection, name="test-collection")]
            )
        ))
