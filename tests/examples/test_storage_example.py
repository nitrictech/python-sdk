from examples.storage.read import storage_read
from examples.storage.delete import storage_delete
from examples.storage.write import storage_write

from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock


class StorageExamplesTest(IsolatedAsyncioTestCase):
    async def test_read_storage(self):
        mock_read = AsyncMock()

        with patch("nitricapi.nitric.storage.v1.StorageServiceStub.read", mock_read):
            await storage_read()

        mock_read.assert_called_once()

    async def test_write_storage(self):
        mock_write = AsyncMock()

        with patch("nitricapi.nitric.storage.v1.StorageServiceStub.write", mock_write):
            await storage_write()

        mock_write.assert_called_once()

    async def test_delete_storage(self):
        mock_delete = AsyncMock()

        with patch("nitricapi.nitric.storage.v1.StorageServiceStub.delete", mock_delete):
            await storage_delete()

        mock_delete.assert_called_once()
