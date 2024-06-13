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
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
from nitric.auth import JWTAuthMiddleware
from nitric.resources.apis import ApiOptions
from nitric.context import HttpContext, HttpRequest, HttpResponse


class TestJWTAuthMiddleware(IsolatedAsyncioTestCase):
    async def test_valid_token(self):
        secret = "secret"
        algorithm = "HS256"
        api_options = ApiOptions(jwt_secret=secret, jwt_algorithm=algorithm)
        middleware = JWTAuthMiddleware(api_options=api_options)

        token = jwt.encode({"sub": "user123"}, secret, algorithm=algorithm)

        request = HttpRequest(
            data=b"", method="GET", path="/", params={}, query={}, headers={"Authorization": f"Bearer {token}"}
        )
        context = HttpContext(request=request)

        mock_next = AsyncMock(return_value=context)

        result = await middleware(context, mock_next)

        mock_next.assert_awaited_once_with(context)
        self.assertEqual(result.req.user, {"sub": "user123"})

    async def test_missing_token(self):
        api_options = ApiOptions(jwt_secret="secret", jwt_algorithm="HS256")
        middleware = JWTAuthMiddleware(api_options=api_options)

        request = HttpRequest(data=b"", method="GET", path="/", params={}, query={}, headers={})
        context = HttpContext(request=request)

        mock_next = AsyncMock()

        result = await middleware(context, mock_next)

        mock_next.assert_not_awaited()
        self.assertEqual(result.res.status, 401)
        self.assertEqual(result.res.body, b'{"error": "Missing token"}')

    async def test_invalid_token(self):
        api_options = ApiOptions(jwt_secret="secret", jwt_algorithm="HS256")
        middleware = JWTAuthMiddleware(api_options=api_options)

        request = HttpRequest(
            data=b"", method="GET", path="/", params={}, query={}, headers={"Authorization": "Bearer invalid_token"}
        )
        context = HttpContext(request=request)

        mock_next = AsyncMock()

        result = await middleware(context, mock_next)

        mock_next.assert_not_awaited()
        self.assertEqual(result.res.status, 401)
        self.assertEqual(result.res.body, b'{"error": "Invalid token"}')
