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
from examples.storage.read import storage_read
from examples.storage.delete import storage_delete
from examples.storage.write import storage_write

from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock


class StorageExamplesTest(IsolatedAsyncioTestCase):
    async def test_read_storage(self):
        mock_read = AsyncMock()

        with patch("nitric.proto.nitric.storage.v1.StorageServiceStub.read", mock_read):
            await storage_read()

        mock_read.assert_called_once()

    async def test_write_storage(self):
        mock_write = AsyncMock()

        with patch("nitric.proto.nitric.storage.v1.StorageServiceStub.write", mock_write):
            await storage_write()

        mock_write.assert_called_once()

    async def test_delete_storage(self):
        mock_delete = AsyncMock()

        with patch("nitric.proto.nitric.storage.v1.StorageServiceStub.delete", mock_delete):
            await storage_delete()

        mock_delete.assert_called_once()
