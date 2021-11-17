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

from nitric.api import Storage
from nitric.api.exception import UnknownException


class Object(object):
    pass


class StorageClientTest(IsolatedAsyncioTestCase):
    async def test_write(self):
        mock_write = AsyncMock()
        mock_response = Object()
        mock_write.return_value = mock_response

        contents = b"some text as bytes"

        with patch("nitricapi.nitric.storage.v1.StorageServiceStub.write", mock_write):
            bucket = Storage().bucket("test-bucket")
            file = bucket.file("test-file")
            await file.write(contents)

        # Check expected values were passed to Stub
        mock_write.assert_called_once()
        assert mock_write.call_args.kwargs["bucket_name"] == "test-bucket"
        assert mock_write.call_args.kwargs["key"] == "test-file"
        assert mock_write.call_args.kwargs["body"] == contents

    async def test_read(self):
        contents = b"some text as bytes"

        mock_read = AsyncMock()
        mock_response = Object()
        mock_response.body = contents
        mock_read.return_value = mock_response

        with patch("nitricapi.nitric.storage.v1.StorageServiceStub.read", mock_read):
            bucket = Storage().bucket("test-bucket")
            file = bucket.file("test-file")
            response = await file.read()

        assert response == contents

        # Check expected values were passed to Stub
        mock_read.assert_called_once()
        assert mock_read.call_args.kwargs["bucket_name"] == "test-bucket"
        assert mock_read.call_args.kwargs["key"] == "test-file"

    async def test_delete(self):
        mock_read = AsyncMock()
        mock_read.return_value = Object()

        with patch("nitricapi.nitric.storage.v1.StorageServiceStub.delete", mock_read):
            bucket = Storage().bucket("test-bucket")
            file = bucket.file("test-file")
            await file.delete()

        # Check expected values were passed to Stub
        mock_read.assert_called_once()
        assert mock_read.call_args.kwargs["bucket_name"] == "test-bucket"
        assert mock_read.call_args.kwargs["key"] == "test-file"

    async def test_sign_url(self):
        mock_pre_sign_url = AsyncMock()
        mock_pre_sign_url.return_value = Object()

        with patch("nitricapi.nitric.storage.v1.StorageServiceStub.pre_sign_url", mock_pre_sign_url):
            bucket = Storage().bucket("test-bucket")
            file = bucket.file("test-file")
            await file.sign_url()

        # Check expected values were passed to Stub
        mock_pre_sign_url.assert_called_once()
        assert mock_pre_sign_url.call_args.kwargs["bucket_name"] == "test-bucket"
        assert mock_pre_sign_url.call_args.kwargs["key"] == "test-file"
        assert mock_pre_sign_url.call_args.kwargs["operation"] == 0
        assert mock_pre_sign_url.call_args.kwargs["expiry"] == 3600

    async def test_write_error(self):
        mock_write = AsyncMock()
        mock_write.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitricapi.nitric.storage.v1.StorageServiceStub.write", mock_write):
            with pytest.raises(UnknownException) as e:
                await Storage().bucket("test-bucket").file("test-file").write(b"some text as bytes")

    async def test_read_error(self):
        mock_read = AsyncMock()
        mock_read.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitricapi.nitric.storage.v1.StorageServiceStub.read", mock_read):
            with pytest.raises(UnknownException) as e:
                await Storage().bucket("test-bucket").file("test-file").read()

    async def test_delete_error(self):
        mock_delete = AsyncMock()
        mock_delete.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitricapi.nitric.storage.v1.StorageServiceStub.delete", mock_delete):
            with pytest.raises(UnknownException) as e:
                await Storage().bucket("test-bucket").file("test-file").delete()

    async def test_sign_url_error(self):
        mock_pre_sign_url = AsyncMock()
        mock_pre_sign_url.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitricapi.nitric.storage.v1.StorageServiceStub.pre_sign_url", mock_pre_sign_url):
            with pytest.raises(UnknownException) as e:
                await Storage().bucket("test-bucket").file("test-file").sign_url()
