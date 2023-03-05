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
from nitric.resources import secret

from nitric.proto.nitric.resource.v1 import Action, ResourceDeclareRequest, Resource, ResourceType, PolicyResource
from nitric.proto.nitric.secret.v1 import SecretPutResponse, SecretVersion, Secret


class Object(object):
    pass


class SecretTest(IsolatedAsyncioTestCase):
    def test_allow_put(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            secret("test-secret").allow("putting")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                resource=Resource(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[Resource(type=ResourceType.Function)],
                    actions=[Action.SecretPut],
                    resources=[Resource(type=ResourceType.Secret, name="test-secret")],
                ),
            )
        )

    def test_allow_access(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            secret("test-secret").allow("accessing")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                resource=Resource(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[Resource(type=ResourceType.Function)],
                    actions=[Action.SecretAccess],
                    resources=[Resource(type=ResourceType.Secret, name="test-secret")],
                ),
            )
        )
