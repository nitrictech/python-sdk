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

from nitricapi.nitric.storage.v1 import StorageWriteRequest

from nitric.resources import bucket

from nitricapi.nitric.resource.v1 import Action, ResourceDeclareRequest, Resource, ResourceType, PolicyResource


class Object(object):
    pass


class BucketTest(IsolatedAsyncioTestCase):
    def test_create_allow_writing(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            bucket("test-bucket").allow(["writing"])

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(resource_declare_request=ResourceDeclareRequest(
            resource=Resource(type=ResourceType.Policy),
            policy=PolicyResource(
                principals=[Resource(type=ResourceType.Function)],
                actions=[Action.BucketFilePut],
                resources=[Resource(type=ResourceType.Bucket, name="test-bucket")]
            )
        ))

    def test_create_allow_reading(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            bucket("test-bucket").allow(["reading"])

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(resource_declare_request=ResourceDeclareRequest(
            resource=Resource(type=ResourceType.Policy),
            policy=PolicyResource(
                principals=[Resource(type=ResourceType.Function)],
                actions=[Action.BucketFileGet, Action.BucketFileList],
                resources=[Resource(type=ResourceType.Bucket, name="test-bucket")]
            )
        ))

    def test_create_allow_deleting(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            bucket("test-bucket").allow(["deleting"])

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(resource_declare_request=ResourceDeclareRequest(
            resource=Resource(type=ResourceType.Policy),
            policy=PolicyResource(
                principals=[Resource(type=ResourceType.Function)],
                actions=[Action.BucketFileDelete],
                resources=[Resource(type=ResourceType.Bucket, name="test-bucket")]
            )
        ))

    def test_create_allow_all(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            bucket("test-bucket").allow(["deleting", "reading", "writing"])

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(resource_declare_request=ResourceDeclareRequest(
            resource=Resource(type=ResourceType.Policy),
            policy=PolicyResource(
                principals=[Resource(type=ResourceType.Function)],
                actions=[
                    Action.BucketFileDelete,
                    Action.BucketFileGet,
                    Action.BucketFileList,
                    Action.BucketFilePut
                ],
                resources=[Resource(type=ResourceType.Bucket, name="test-bucket")]
            )
        ))

    def test_create_allow_all_reversed_policy(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            bucket("test-bucket").allow(["writing", "reading", "deleting"])

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(resource_declare_request=ResourceDeclareRequest(
            resource=Resource(type=ResourceType.Policy),
            policy=PolicyResource(
                principals=[Resource(type=ResourceType.Function)],
                actions=[
                    Action.BucketFilePut,
                    Action.BucketFileGet,
                    Action.BucketFileList,
                    Action.BucketFileDelete,
                ],
                resources=[Resource(type=ResourceType.Bucket, name="test-bucket")]
            )
        ))

