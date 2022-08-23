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
from nitric.resources import bucket

from nitricapi.nitric.resource.v1 import Action


class Object(object):
    pass


class BucketTest(IsolatedAsyncioTestCase):
    async def test_create_allow_writing(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await bucket("test-bucket").allow(["writing"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()
        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-bucket")
        self.assertEqual(mock_declare.call_args.kwargs["policy"].actions, [Action.BucketFilePut])

    async def test_create_allow_reading(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await bucket("test-bucket").allow(["reading"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()

        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-bucket")
        self.assertEqual(mock_declare.call_args.kwargs["policy"].actions, [Action.BucketFileGet, Action.BucketFileList])

    async def test_create_allow_deleting(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await bucket("test-bucket").allow(["deleting"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()
        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-bucket")
        self.assertEqual(mock_declare.call_args.kwargs["policy"].actions, [Action.BucketFileDelete])

    async def test_create_allow_all(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await bucket("test-bucket").allow(["deleting", "reading", "writing"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()
        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-bucket")
        self.assertEqual(
            mock_declare.call_args.kwargs["policy"].actions,
            [
                Action.BucketFileDelete,
                Action.BucketFileGet,
                Action.BucketFileList,
                Action.BucketFilePut,
            ],
        )

    async def test_create_allow_all_reversed_policy(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            await bucket("test-bucket").allow(["writing", "reading", "deleting"])

        # Check expected values were passed to Stub
        mock_declare.assert_called()
        self.assertEqual(mock_declare.call_args.kwargs["policy"].resources[0].name, "test-bucket")
        self.assertLessEqual(
            mock_declare.call_args.kwargs["policy"].actions,
            [
                Action.BucketFilePut,
                Action.BucketFileGet,
                Action.BucketFileList,
                Action.BucketFileDelete,
            ],
        )

    async def test_write(self):
        mock_declare = AsyncMock()
        mock_write = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        contents = b"some text as bytes"

        with patch("nitricapi.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            with patch("nitricapi.nitric.storage.v1.StorageServiceStub.write", mock_write):
                b = await bucket("test-bucket").allow(["writing"])
                file = b.file("test-file")
                await file.write(contents)

        # Check expected values were passed to Stub
        print(f"num calls: {len(mock_declare.mock_calls)}")
        self.assertEqual(mock_write.call_args.kwargs["bucket_name"], "test-bucket")
        self.assertEqual(mock_write.call_args.kwargs["key"], "test-file")
        self.assertEqual(mock_write.call_args.kwargs["body"], contents)
