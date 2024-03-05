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
from nitric.resources import queue

from nitric.proto.resources.v1 import Action, ResourceDeclareRequest, ResourceIdentifier, ResourceType, PolicyResource

# pylint: disable=protected-access,missing-function-docstring,missing-class-docstring


class Object(object):
    pass


class QueueTest(IsolatedAsyncioTestCase):
    def test_create_allow_sending(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            queue("test-queue").allow("enqueue")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[
                        Action.QueueEnqueue,
                    ],
                    resources=[ResourceIdentifier(type=ResourceType.Queue, name="test-queue")],
                ),
            )
        )

    def test_create_allow_receiving(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            queue("test-queue").allow("dequeue")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[
                        Action.QueueDequeue,
                    ],
                    resources=[ResourceIdentifier(type=ResourceType.Queue, name="test-queue")],
                ),
            )
        )

    def test_create_allow_all(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            queue("test-queue").allow("enqueue", "dequeue")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[
                        Action.QueueEnqueue,
                        Action.QueueDequeue,
                    ],
                    resources=[ResourceIdentifier(type=ResourceType.Queue, name="test-queue")],
                ),
            )
        )
