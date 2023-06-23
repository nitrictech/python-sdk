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

from nitric.exception import InternalException
from nitric.faas import HttpMethod, MethodOptions, ApiWorkerOptions
from nitric.proto.nitric.resource.v1 import (
    ResourceDeclareRequest,
    ApiResource,
    Resource,
    ResourceType,
    ResourceDetailsResponse,
    ApiResourceDetails,
    ResourceDetailsRequest,
    ApiScopes,
    ApiSecurityDefinition,
    ApiSecurityDefinitionJwt,
    ResourceServiceStub,
)

from nitric.resources import api, ApiOptions, JwtSecurityDefinition
from nitric.resources.apis import Method, Route, RouteOptions, Api


class Object(object):
    pass


class ApiTest(IsolatedAsyncioTestCase):
    def test_create_default_api(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response
        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            api("test-api")

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                resource=Resource(type=ResourceType.Api, name="test-api"),
                api=ApiResource(security={}, security_definitions={}),
            )
        )

    def test_create_api_throws_error(self):
        mock_declare = AsyncMock()
        mock_declare.side_effect = GRPCError(Status.INTERNAL, "test-error")

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            with pytest.raises(InternalException) as e:
                api("test-api-error")

    def test_cached_api(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            api("test-api-cached")

            api("test-api-cached")

            # Check expected values were passed to Stub
        mock_declare.assert_called_once_with(
            resource_declare_request=ResourceDeclareRequest(
                resource=Resource(type=ResourceType.Api, name="test-api-cached"),
                api=ApiResource(security={}, security_definitions={}),
            )
        )

    def test_create_api_with_empty_options(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            api("test-api-empty-options", ApiOptions())

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                resource=Resource(type=ResourceType.Api, name="test-api-empty-options"),
                api=ApiResource(security={}, security_definitions={}),
            )
        )

    def test_create_api_with_base_path(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-base-path", ApiOptions(path="/api/v1"))

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                resource=Resource(type=ResourceType.Api, name="test-api-base-path"),
                api=ApiResource(security={}, security_definitions={}),
            )
        )

        assert test_api.path == "/api/v1"

    def test_create_api_with_security_definition(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            api(
                "test-api-security-definition",
                ApiOptions(
                    security_definitions={
                        "user": JwtSecurityDefinition(
                            issuer="https://example-issuer.com", audiences=["test-audience", "other-audience"]
                        )
                    },
                    security={"user": ["test:read", "test:write"]},
                ),
            )

        # Check expected values were passed to Stub
        mock_declare.assert_called_with(
            resource_declare_request=ResourceDeclareRequest(
                resource=Resource(type=ResourceType.Api, name="test-api-security-definition"),
                api=ApiResource(
                    security_definitions={
                        "user": ApiSecurityDefinition(
                            jwt=ApiSecurityDefinitionJwt(
                                issuer="https://example-issuer.com", audiences=["test-audience", "other-audience"]
                            )
                        )
                    },
                    security={"user": ApiScopes(scopes=["test:read", "test:write"])},
                ),
            )
        )

    @patch.object(Api, "_register", AsyncMock())
    async def test_get_api_url(self):
        test_api = api("test-api-get-url")

        assert test_api is not None

        # Test URL called
        mock_details = AsyncMock()
        mock_details.return_value = ResourceDetailsResponse(api=ApiResourceDetails(url="https://google-api.com/"))

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.details", mock_details):
            url = await test_api.url()

        assert url == "https://google-api.com/"

        # Check expected values were passed to Stub
        mock_details.assert_called_once_with(
            resource_details_request=ResourceDetailsRequest(
                resource=Resource(type=ResourceType.Api, name="test-api-get-url")
            )
        )

    async def test_get_api_url_throws_error(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-get-url")

        assert test_api is not None

        # Test URL called
        mock_details = AsyncMock()
        mock_details.side_effect = GRPCError(Status.INTERNAL, "test error")

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.details", mock_details):
            with pytest.raises(InternalException) as e:
                await test_api.url()

    def test_api_route(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-route", ApiOptions(path="/api/v2/"))

        test_route = test_api._route("/hello")

        assert test_route.path == "/api/v2/hello"
        assert test_route.middleware == []
        assert test_route.api.name == test_api.name

    def test_define_route(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-define-route", ApiOptions(path="/api/v2/"))

        test_route = Route(test_api, "/hello", opts=RouteOptions())

        assert test_route.path == "/api/v2/hello"
        assert test_route.middleware == []
        assert test_route.api.name == test_api.name

    def test_define_method(self):
        mock_declare = AsyncMock()
        mock_response = Object()
        mock_declare.return_value = mock_response

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-define-method", ApiOptions(path="/api/v2/"))

        test_route = Route(test_api, "/hello", opts=RouteOptions())

        test_method = Method(
            route=test_route,
            methods=[HttpMethod.GET, HttpMethod.POST],
            opts=MethodOptions(security={"user": ["test:delete"]}),
        )

        assert test_method.methods == [HttpMethod.GET, HttpMethod.POST]
        assert test_method.route == test_route
        assert test_method.server is not None

        assert isinstance(test_method.server._opts, ApiWorkerOptions)
        assert test_method.server._opts.methods == ["GET", "POST"]
        assert test_method.server._opts.api == "test-api-define-method"
        assert test_method.server._opts.opts.security == {"user": ["test:delete"]}

    def test_api_get(self):
        mock_declare = AsyncMock()

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-get", ApiOptions(path="/api/v2/"))

        test_api.get("/hello")(lambda ctx: ctx)

        assert len(test_api.routes) == 1
        assert test_api.routes[0].path == "/api/v2/hello"

    def test_api_post(self):
        mock_declare = AsyncMock()

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-post", ApiOptions(path="/api/v2/"))

        test_api.post("/hello")(lambda ctx: ctx)

        assert len(test_api.routes) == 1
        assert test_api.routes[0].path == "/api/v2/hello"

    def test_api_delete(self):
        mock_declare = AsyncMock()

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-delete", ApiOptions(path="/api/v2/"))

        test_api.delete("/hello")(lambda ctx: ctx)

        assert len(test_api.routes) == 1
        assert test_api.routes[0].path == "/api/v2/hello"

    def test_api_put(self):
        mock_declare = AsyncMock()

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-put", ApiOptions(path="/api/v2/"))

        test_api.put("/hello")(lambda ctx: ctx)

        assert len(test_api.routes) == 1
        assert test_api.routes[0].path == "/api/v2/hello"

    def test_api_patch(self):
        mock_declare = AsyncMock()

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-patch", ApiOptions(path="/api/v2/"))

        test_api.patch("/hello")(lambda ctx: ctx)

        assert len(test_api.routes) == 1
        assert test_api.routes[0].path == "/api/v2/hello"

    def test_api_all(self):
        mock_declare = AsyncMock()

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-all", ApiOptions(path="/api/v2/"))

        test_api.all("/hello")(lambda ctx: ctx)

        assert len(test_api.routes) == 1
        assert test_api.routes[0].path == "/api/v2/hello"

    def test_api_methods(self):
        mock_declare = AsyncMock()

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-methods", ApiOptions(path="/api/v2/"))

        test_api.methods([HttpMethod.GET], "/hello")(lambda ctx: ctx)

        assert len(test_api.routes) == 1
        assert test_api.routes[0].path == "/api/v2/hello"

    def test_api_options(self):
        mock_declare = AsyncMock()

        with patch("nitric.proto.nitric.resource.v1.ResourceServiceStub.declare", mock_declare):
            test_api = api("test-api-options", ApiOptions(path="/api/v2/"))

        test_api.options("/hello")(lambda ctx: ctx)

        assert len(test_api.routes) == 1
        assert test_api.routes[0].path == "/api/v2/hello"
