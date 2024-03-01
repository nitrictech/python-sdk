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
from datetime import timedelta
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

import pytest
from grpclib import GRPCError, Status

from nitric.exception import UnknownException
from nitric.proto.resources.v1 import Action, PolicyResource, ResourceDeclareRequest, ResourceIdentifier, ResourceType
from nitric.proto.storage.v1 import (
    StorageDeleteRequest,
    StoragePreSignUrlRequest,
    StoragePreSignUrlRequestOperation,
    StoragePreSignUrlResponse,
    StorageReadRequest,
    StorageWriteRequest,
)

# from nitric.proto.storage.v1 import StorageWriteRequest
from nitric.resources import bucket
from nitric.resources.buckets import BucketRef


class Object(object):
    pass


class BucketRefTest(IsolatedAsyncioTestCase):
    async def test_write(self):
        mock_write = AsyncMock()
        mock_response = Object()
        mock_write.return_value = mock_response

        contents = b"some text as bytes"

        with patch("nitric.proto.storage.v1.StorageStub.write", mock_write):
            bucket = BucketRef("test-bucket")
            file = bucket.file("test-file")
            await file.write(contents)

        # Check expected values were passed to Stub
        mock_write.assert_called_once_with(
            storage_write_request=StorageWriteRequest(bucket_name="test-bucket", key="test-file", body=contents)
        )

    async def test_read(self):
        contents = b"some text as bytes"

        mock_read = AsyncMock()
        mock_response = Object()
        mock_response.body = contents
        mock_read.return_value = mock_response

        with patch("nitric.proto.storage.v1.StorageStub.read", mock_read):
            bucket = BucketRef("test-bucket")
            file = bucket.file("test-file")
            response = await file.read()

        assert response == contents

        # Check expected values were passed to Stub
        mock_read.assert_called_once_with(
            storage_read_request=StorageReadRequest(
                bucket_name="test-bucket",
                key="test-file",
            )
        )

    async def test_delete(self):
        mock_delete = AsyncMock()
        mock_delete.return_value = Object()

        with patch("nitric.proto.storage.v1.StorageStub.delete", mock_delete):
            bucket = BucketRef("test-bucket")
            file = bucket.file("test-file")
            await file.delete()

        # Check expected values were passed to Stub
        mock_delete.assert_called_once_with(
            storage_delete_request=StorageDeleteRequest(
                bucket_name="test-bucket",
                key="test-file",
            )
        )

    async def test_download_url_with_default_expiry(self):
        mock_pre_sign_url = AsyncMock()
        mock_pre_sign_url.return_value = StoragePreSignUrlResponse(url="www.example.com")

        with patch("nitric.proto.storage.v1.StorageStub.pre_sign_url", mock_pre_sign_url):
            bucket = BucketRef("test-bucket")
            file = bucket.file("test-file")
            url = await file.download_url()

        # Check expected values were passed to Stub
        mock_pre_sign_url.assert_called_once_with(
            storage_pre_sign_url_request=StoragePreSignUrlRequest(
                bucket_name="test-bucket",
                key="test-file",
                operation=StoragePreSignUrlRequestOperation.READ,
                expiry=timedelta(seconds=600),
            )
        )

        # check the URL is returned
        assert url == "www.example.com"

    async def test_download_url_with_provided_expiry(self):
        mock_pre_sign_url = AsyncMock()
        mock_pre_sign_url.return_value = StoragePreSignUrlResponse(url="www.example.com")

        with patch("nitric.proto.storage.v1.StorageStub.pre_sign_url", mock_pre_sign_url):
            bucket = BucketRef("test-bucket")
            file = bucket.file("test-file")
            url = await file.download_url(timedelta(seconds=60))

        # Check expected values were passed to Stub
        mock_pre_sign_url.assert_called_once_with(
            storage_pre_sign_url_request=StoragePreSignUrlRequest(
                bucket_name="test-bucket",
                key="test-file",
                operation=StoragePreSignUrlRequestOperation.READ,
                expiry=timedelta(seconds=60),
            )
        )

        # check the URL is returned
        assert url == "www.example.com"

    async def test_upload_url_with_default_expiry(self):
        mock_pre_sign_url = AsyncMock()
        mock_pre_sign_url.return_value = StoragePreSignUrlResponse(url="www.example.com")

        with patch("nitric.proto.storage.v1.StorageStub.pre_sign_url", mock_pre_sign_url):
            bucket = BucketRef("test-bucket")
            file = bucket.file("test-file")
            url = await file.upload_url()

        # Check expected values were passed to Stub
        mock_pre_sign_url.assert_called_once_with(
            storage_pre_sign_url_request=StoragePreSignUrlRequest(
                bucket_name="test-bucket",
                key="test-file",
                operation=StoragePreSignUrlRequestOperation.WRITE,
                expiry=timedelta(seconds=600),
            )
        )

        # check the URL is returned
        assert url == "www.example.com"

    async def test_upload_url_with_provided_expiry(self):
        mock_pre_sign_url = AsyncMock()
        mock_pre_sign_url.return_value = StoragePreSignUrlResponse(url="www.example.com")

        with patch("nitric.proto.storage.v1.StorageStub.pre_sign_url", mock_pre_sign_url):
            bucket = BucketRef("test-bucket")
            file = bucket.file("test-file")
            url = await file.upload_url(timedelta(seconds=60))

        # Check expected values were passed to Stub
        mock_pre_sign_url.assert_called_once_with(
            storage_pre_sign_url_request=StoragePreSignUrlRequest(
                bucket_name="test-bucket",
                key="test-file",
                operation=StoragePreSignUrlRequestOperation.WRITE,
                expiry=timedelta(seconds=60),
            )
        )

        # check the URL is returned
        assert url == "www.example.com"

    async def test_write_error(self):
        mock_write = AsyncMock()
        mock_write.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitric.proto.storage.v1.StorageStub.write", mock_write):
            with pytest.raises(UnknownException) as e:
                await BucketRef("test-bucket").file("test-file").write(b"some text as bytes")

    async def test_read_error(self):
        mock_read = AsyncMock()
        mock_read.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitric.proto.storage.v1.StorageStub.read", mock_read):
            with pytest.raises(UnknownException) as e:
                await BucketRef("test-bucket").file("test-file").read()

    async def test_delete_error(self):
        mock_delete = AsyncMock()
        mock_delete.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitric.proto.storage.v1.StorageStub.delete", mock_delete):
            with pytest.raises(UnknownException) as e:
                await BucketRef("test-bucket").file("test-file").delete()

    async def test_sign_url_error(self):
        mock_pre_sign_url = AsyncMock()
        mock_pre_sign_url.side_effect = GRPCError(Status.UNKNOWN, "test error")

        with patch("nitric.proto.storage.v1.StorageStub.pre_sign_url", mock_pre_sign_url):
            with pytest.raises(UnknownException) as e:
                await BucketRef("test-bucket").file("test-file").upload_url()


class BucketTest(IsolatedAsyncioTestCase):
    def test_create_allow_writing(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            bucket("test-bucket").allow("writing")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[Action.BucketFilePut],
                    resources=[ResourceIdentifier(type=ResourceType.Bucket, name="test-bucket")],
                ),
            )
        )

    def test_create_allow_reading(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            bucket("test-bucket").allow("reading")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[Action.BucketFileGet, Action.BucketFileList],
                    resources=[ResourceIdentifier(type=ResourceType.Bucket, name="test-bucket")],
                ),
            )
        )

    def test_create_allow_deleting(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            bucket("test-bucket").allow("deleting")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[Action.BucketFileDelete],
                    resources=[ResourceIdentifier(type=ResourceType.Bucket, name="test-bucket")],
                ),
            )
        )

    def test_create_allow_all(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            bucket("test-bucket").allow("deleting", "reading", "writing")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[
                        Action.BucketFileDelete,
                        Action.BucketFileGet,
                        Action.BucketFileList,
                        Action.BucketFilePut,
                    ],
                    resources=[ResourceIdentifier(type=ResourceType.Bucket, name="test-bucket")],
                ),
            )
        )

    def test_create_allow_all_reversed_policy(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.resources.v1.ResourcesStub.declare", mock_declare):
            bucket("test-bucket").allow("writing", "reading", "deleting")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                id=ResourceIdentifier(type=ResourceType.Policy),
                policy=PolicyResource(
                    principals=[ResourceIdentifier(type=ResourceType.Service)],
                    actions=[
                        Action.BucketFilePut,
                        Action.BucketFileGet,
                        Action.BucketFileList,
                        Action.BucketFileDelete,
                    ],
                    resources=[ResourceIdentifier(type=ResourceType.Bucket, name="test-bucket")],
                ),
            )
        )
