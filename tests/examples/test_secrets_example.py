from nitricapi.nitric.secret.v1 import Secret, SecretVersion, SecretAccessResponse, SecretPutResponse
from examples.secrets.access import secret_access
from examples.secrets.put import secret_put
from examples.secrets.latest import secret_latest

from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock


class SecretsExamplesTest(IsolatedAsyncioTestCase):
    async def test_latest_secret(self):
        mock_latest = AsyncMock()
        mock_response = SecretAccessResponse(
            secret_version=SecretVersion(secret=Secret(name="test-secret"), version="response-version"),
            value=b"super secret value",
        )
        mock_latest.return_value = mock_response

        with patch("nitricapi.nitric.secret.v1.SecretServiceStub.access", mock_latest):
            await secret_latest()

        mock_latest.assert_called_once()

    async def test_put_secret(self):
        mock_put = AsyncMock()
        mock_response = SecretPutResponse(
            secret_version=SecretVersion(secret=Secret(name="test-secret"), version="test-version")
        )
        mock_put.return_value = mock_response

        mock_access = AsyncMock()
        mock_response = SecretAccessResponse(
            secret_version=SecretVersion(secret=Secret(name="test-secret"), version="response-version"),
            value=b"super secret value",
        )
        mock_access.return_value = mock_response

        with patch("nitricapi.nitric.secret.v1.SecretServiceStub.put", mock_put):
            with patch("nitricapi.nitric.secret.v1.SecretServiceStub.access", mock_access):
                await secret_put()

        mock_put.assert_called_once()
        mock_access.assert_called_once()

    async def test_access_secret(self):
        mock_access = AsyncMock()
        mock_response = SecretAccessResponse(
            secret_version=SecretVersion(secret=Secret(name="test-secret"), version="response-version"),
            value=b"super secret value",
        )
        mock_access.return_value = mock_response
        with patch("nitricapi.nitric.secret.v1.SecretServiceStub.access", mock_access):
            await secret_access()

        mock_access.assert_called_once()
