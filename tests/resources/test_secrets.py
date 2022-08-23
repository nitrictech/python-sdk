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

from nitricapi.nitric.resource.v1 import Action
from nitricapi.nitric.secret.v1 import SecretPutResponse, SecretVersion, Secret


class Object(object):
    pass


class SecretTest(IsolatedAsyncioTestCase):
    async def test_allow_put(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await secret("test-secret").allow(["putting"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()
        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-secret")
        self.assertListEqual(mock_declare.call_args.kwargs["policy"].actions, [Action.SecretPut])

    async def test_allow_access(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await secret("test-secret").allow(["accessing"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()
        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-secret")
        self.assertListEqual(mock_declare.call_args.kwargs["policy"].actions, [Action.SecretAccess])

    async def test_put_string(self):
        mock_put = AsyncMock()
        mock_declare = AsyncMock()

        mock_response = SecretPutResponse(
            secret_version=SecretVersion(secret=Secret(name="test-secret"), version="test-version")
        )
        mock_put.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            with patch("nitricapi.nitric.secret.v1.SecretServiceStub.put", mock_put):
                s = await secret("test-secret").allow(["accessing"])
                await s.put("a test secret value")  # string, not bytes

        # Check expected values were passed to Stub
        mock_put.assert_called_once()
        assert mock_put.call_args.kwargs["value"] == b"a test secret value"  # value should still be bytes when sent.
