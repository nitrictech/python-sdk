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
from grpclib import GRPCError, Status

from nitric.api import Secrets
from nitric.exception import UnknownException
from nitric.api.secrets import SecretValue
from nitric.proto.nitric.secret.v1 import (
    SecretPutResponse,
    SecretVersion,
    Secret,
    SecretAccessResponse,
    SecretPutRequest,
    SecretAccessRequest,
)


class Object(object):
    pass


class SecretsClientTest(IsolatedAsyncioTestCase):
    async def test_put(self):
        mock_put = AsyncMock()
        mock_response = SecretPutResponse(
            secret_version=SecretVersion(secret=Secret(name="test-secret"), version="test-version")
        )
        mock_put.return_value = mock_response

        with patch("nitric.proto.nitric.secret.v1.SecretServiceStub.put", mock_put):
            secret = Secrets().secret("test-secret")
            result = await secret.put(b"a test secret value")

        # Check expected values were passed to Stub
        mock_put.assert_called_once_with(
            secret_put_request=SecretPutRequest(secret=Secret(name="test-secret"), value=b"a test secret value")
        )

        # Check the returned value
        assert result.id == "test-version"
        assert result.secret.name == "test-secret"

    async def test_put_string(self):
        mock_put = AsyncMock()
        mock_response = SecretPutResponse(
            secret_version=SecretVersion(secret=Secret(name="test-secret"), version="test-version")
        )
        mock_put.return_value = mock_response

        with patch("nitric.proto.nitric.secret.v1.SecretServiceStub.put", mock_put):
            secret = Secrets().secret("test-secret")
            await secret.put("a test secret value")  # string, not bytes

        # Check expected values were passed to Stub
        mock_put.assert_called_once_with(
            secret_put_request=SecretPutRequest(secret=Secret(name="test-secret"), value=b"a test secret value")
        )

    async def test_latest(self):
        version = Secrets().secret("test-secret").latest()

        assert version.secret.name == "test-secret"
        assert version.id == "latest"

    async def test_access(self):
        mock_access = AsyncMock()
        mock_response = SecretAccessResponse(
            secret_version=SecretVersion(secret=Secret(name="test-secret"), version="response-version"),
            value=b"super secret value",
        )
        mock_access.return_value = mock_response

        with patch("nitric.proto.nitric.secret.v1.SecretServiceStub.access", mock_access):
            version = Secrets().secret("test-secret").latest()
            result = await version.access()

            # Check expected values were passed to Stub
            mock_access.assert_called_once_with(
                secret_access_request=SecretAccessRequest(
                    secret_version=SecretVersion(secret=Secret(name="test-secret"), version="latest")
                )
            )

            # Check the returned value
            assert result.version.id == "response-version"
            assert result.value == b"super secret value"

    async def test_value_to_string(self):
        value = SecretValue(version=None, value=b"secret value")

        assert value.as_string() == "secret value"
        assert str(value) == "secret value"

    async def test_value_to_bytes(self):
        value = SecretValue(version=None, value=b"secret value")

        assert value.as_bytes() == b"secret value"
        assert bytes(value) == b"secret value"

    async def test_put_error(self):
        mock_put = AsyncMock()
        mock_put.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitric.proto.nitric.secret.v1.SecretServiceStub.put", mock_put):
            with pytest.raises(UnknownException) as e:
                secret = Secrets().secret("test-secret")
                await secret.put(b"a test secret value")

    async def test_access_error(self):
        mock_access = AsyncMock()
        mock_access.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitric.proto.nitric.secret.v1.SecretServiceStub.access", mock_access):
            with pytest.raises(UnknownException) as e:
                await Secrets().secret("test-secret").latest().access()
