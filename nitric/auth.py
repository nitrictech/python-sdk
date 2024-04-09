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
from abc import ABC, abstractmethod
from typing import Optional
import jwt

from nitric.context import HttpContext, HttpMiddleware
from nitric.resources.apis import ApiOptions


class AuthMiddleware(ABC):
    """Abstract base class for authentication middleware."""

    @abstractmethod
    async def __call__(self, ctx: HttpContext, nxt: HttpMiddleware) -> HttpContext:
        """Process the request and response."""
        pass

    @abstractmethod
    def get_auth_token(self, ctx: HttpContext) -> Optional[str]:
        """Retrieve the authentication token from the request."""
        pass

    @abstractmethod
    def authenticate(self, token: str) -> Optional[dict]:
        """Authenticate the provided token and return the user info."""
        pass

    async def authenticate_request(self, ctx: HttpContext) -> None:
        """Process the request, authenticate the user and set the user info."""
        token = self.get_auth_token(ctx)
        ctx.req.user = None  # Set user to None by default

        if token:
            user_info = self.authenticate(token)
            if user_info:
                ctx.req.user = user_info
            else:
                ctx.res.status = 401
                ctx.res.body = {"error": "Invalid token"}
        else:
            ctx.res.status = 401
            ctx.res.body = {"error": "Missing token"}


class JWTAuthMiddleware(AuthMiddleware):
    """JWT authentication middleware."""

    def __init__(self, api_options: ApiOptions):
        """Initialize the middleware with the provided secret and algorithm."""
        self.secret = api_options.jwt_secret
        self.algorithm = api_options.jwt_algorithm

    async def __call__(self, ctx: HttpContext, nxt: HttpMiddleware) -> HttpContext:
        """Process the request and response."""
        await self.authenticate_request(ctx)
        if ctx.res.status != 401:
            ctx = await nxt(ctx)
        return ctx

    def get_auth_token(self, ctx: HttpContext) -> Optional[str]:
        """Retrieve the JWT token from the Authorization header."""
        auth_header = ctx.req.headers.get("Authorization")
        if auth_header:
            if isinstance(auth_header, list):
                auth_header = auth_header[0]
            if auth_header.startswith("Bearer "):
                return auth_header[7:]
        return None

    def authenticate(self, token: str) -> Optional[dict]:
        """Decode the JWT token and return the payload."""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.InvalidTokenError:
            return None
