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
from __future__ import annotations
from typing import List, Union, Optional, ParamSpec, TypeVar, Callable, Concatenate
from dataclasses import dataclass
from nitric.faas import ApiWorkerOptions, FunctionServer, MethodOptions, HttpMethod, HttpMiddleware, HttpHandler
from nitric.application import Nitric
from nitric.resources.resource import Resource as BaseResource
from nitric.proto.nitric.resource.v1 import (
    Resource,
    ResourceType,
    ApiResource,
    ApiScopes,
    ApiSecurityDefinition,
    ApiSecurityDefinitionJwt,
    ResourceDeclareRequest,
    ResourceDetailsRequest,
)
from grpclib import GRPCError
from nitric.exception import exception_from_grpc_error


@dataclass
class ApiDetails:
    """Represents the APIs deployment details."""

    # the identifier of the resource
    id: str
    # The provider this resource is deployed with (e.g. aws)
    provider: str
    # The service this resource is deployed on (e.g. ApiGateway)
    service: str
    # The url of the API
    url: str


@dataclass
class JwtSecurityDefinition:
    """
    Represents the JWT security definition for an API.

    issuer (str): the JWT issuer
    audiences (List[str]): a list of the allowed audiences for the API
    """

    issuer: str
    audiences: List[str]


# TODO: Union type for multiple security definition mappings
# type SecurityDefinition = JwtSecurityDefinition;

SecurityDefinition = JwtSecurityDefinition


class ApiOptions:
    """Represents options when creating an API, such as middleware to be applied to all HTTP request to the API."""

    path: str
    middleware: Optional[Union[HttpMiddleware, List[HttpMiddleware]]]
    security_definitions: dict[str, SecurityDefinition]
    security: dict[str, List[str]]

    def __init__(
        self,
        path: str = "",
        middleware: Optional[Union[HttpMiddleware, List[HttpMiddleware]]] = [],
        security_definitions: dict[str, SecurityDefinition] = {},
        security: dict[str, List[str]] = {},
    ):
        """Construct a new API options object."""
        self.middleware = middleware
        self.security_definitions = security_definitions
        self.security = security
        self.path = path


class RouteOptions:
    """Represents options when creating a route, such as middleware to be applied to all HTTP Methods for the route."""

    middleware: Union[None, List[HttpMiddleware]]

    def __init__(self, middleware: List[HttpMiddleware] = []):
        """Construct a new route options object."""
        self.middleware = middleware


def _to_resource(b: Api) -> Resource:
    return Resource(name=b.name, type=ResourceType.Api)


def _security_definition_to_grpc_declaration(
    security_definitions: Optional[dict[str, SecurityDefinition]] = None
) -> dict[str, ApiSecurityDefinition]:
    if security_definitions is None or len(security_definitions) == 0:
        return {}
    return {
        k: ApiSecurityDefinition(jwt=ApiSecurityDefinitionJwt(issuer=v.issuer, audiences=v.audiences))
        for k, v in security_definitions.items()
    }


def _security_to_grpc_declaration(security: Optional[dict[str, List[str]]] = None) -> dict[str, ApiScopes]:
    if security is None or len(security) == 0:
        return {}
    return {k: ApiScopes(v) for k, v in security.items()}


Param = ParamSpec("Param")
RetType = TypeVar("RetType")
OriginalFunc = Callable[Param, RetType]
DecoratedFunc = Callable[Concatenate[str, Param], RetType]


class Api(BaseResource):
    """An HTTP API."""

    app: Nitric
    name: str
    path: str
    middleware: List[HttpMiddleware]
    routes: List[Route]
    security_definitions: dict[str, SecurityDefinition]
    security: dict[str, List[str]]

    def __init__(self, name: str, opts: Optional[ApiOptions] = None):
        """Construct a new HTTP API."""
        super().__init__()
        if opts is None:
            opts = ApiOptions()

        self.name = name
        self.middleware = (
            opts.middleware
            if isinstance(opts.middleware, list)
            else [opts.middleware]
            if opts.middleware is not None
            else []
        )
        self.path = opts.path
        self.routes = []
        self.security_definitions = opts.security_definitions
        self.security = opts.security

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    resource=_to_resource(self),
                    api=ApiResource(
                        security_definitions=_security_definition_to_grpc_declaration(self.security_definitions),
                        security=_security_to_grpc_declaration(self.security),
                    ),
                )
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    def _route(self, match: str, opts: Optional[RouteOptions] = None) -> Route:
        """Define an HTTP route to be handled by this API."""
        if opts is None:
            opts = RouteOptions()

        r = Route(self, match, opts)
        self.routes.append(r)
        return r

    def all(self, match: str, opts: Optional[MethodOptions] = None) -> Callable[[HttpHandler], None]:
        """Define an HTTP route which will respond to HTTP GET requests."""

        def decorator(function: HttpHandler) -> None:
            r = self._route(match)
            r.method(
                [
                    HttpMethod.GET,
                    HttpMethod.POST,
                    HttpMethod.PATCH,
                    HttpMethod.PUT,
                    HttpMethod.DELETE,
                    HttpMethod.OPTIONS,
                ],
                function,
                opts=opts if opts is not None else MethodOptions(),
            )

        return decorator

    def methods(
        self, methods: List[HttpMethod], match: str, opts: Optional[MethodOptions] = None
    ) -> Callable[[HttpHandler], None]:
        """Define an HTTP route which will respond to specific HTTP requests defined by a list of verbs."""
        if opts is None:
            opts = MethodOptions()

        def decorator(function: HttpHandler) -> None:
            r = self._route(match)
            r.method(methods, function, opts=opts)

        return decorator

    def get(self, match: str, opts: Optional[MethodOptions] = None) -> Callable[[HttpHandler], None]:
        """Define an HTTP route which will respond to HTTP GET requests."""
        if opts is None:
            opts = MethodOptions()

        def decorator(function: HttpHandler) -> None:
            r = self._route(match)
            r.get(function, opts=opts)

        return decorator

    def post(self, match: str, opts: Optional[MethodOptions] = None) -> Callable[[HttpHandler], None]:
        """Define an HTTP route which will respond to HTTP POST requests."""
        if opts is None:
            opts = MethodOptions()

        def decorator(function: HttpHandler) -> None:
            r = self._route(match)
            r.post(function, opts=opts)

        return decorator

    def delete(self, match: str, opts: Optional[MethodOptions] = None) -> Callable[[HttpHandler], None]:
        """Define an HTTP route which will respond to HTTP DELETE requests."""
        if opts is None:
            opts = MethodOptions()

        def decorator(function: HttpHandler) -> None:
            r = self._route(match)
            r.delete(function, opts=opts)

        return decorator

    def options(self, match: str, opts: Optional[MethodOptions] = None) -> Callable[[HttpHandler], None]:
        """Define an HTTP route which will respond to HTTP OPTIONS requests."""
        if opts is None:
            opts = MethodOptions()

        def decorator(function: HttpHandler) -> None:
            r = self._route(match)
            r.options(function, opts=opts)

        return decorator

    def patch(self, match: str, opts: Optional[MethodOptions] = None) -> Callable[[HttpHandler], None]:
        """Define an HTTP route which will respond to HTTP PATCH requests."""
        if opts is None:
            opts = MethodOptions()

        def decorator(function: HttpHandler) -> None:
            r = self._route(match)
            r.patch(function, opts=opts)

        return decorator

    def put(self, match: str, opts: Optional[MethodOptions] = None) -> Callable[[HttpHandler], None]:
        """Define an HTTP route which will respond to HTTP PUT requests."""
        if opts is None:
            opts = MethodOptions()

        def decorator(function: HttpHandler) -> None:
            r = self._route(match)
            r.put(function, opts=opts)

        return decorator

    async def _details(self) -> ApiDetails:
        """Get the API deployment details."""
        try:
            res = await self._resources_stub.details(
                resource_details_request=ResourceDetailsRequest(
                    resource=_to_resource(self),
                )
            )
            return ApiDetails(res.id, res.provider, res.service, res.api.url)
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    async def url(self) -> str:
        """Get the APIs live URL."""
        details = await self._details()
        return details.url


class Route:
    """An HTTP route."""

    api: Api
    path: str
    middleware: List[HttpMiddleware]

    def __init__(self, api: Api, path: str, opts: RouteOptions):
        """Define a route to be handled by the provided API."""
        self.api = api
        self.path = (api.path + path).replace("//", "/")
        self.middleware = opts.middleware if opts.middleware is not None else []

    def method(
        self, methods: List[HttpMethod], *middleware: HttpMiddleware | HttpHandler, opts: Optional[MethodOptions] = None
    ) -> None:
        """Register middleware for multiple HTTP Methods."""
        return Method(self, methods, *middleware, opts=opts).start()

    def get(self, *middleware: HttpMiddleware | HttpHandler, opts: Optional[MethodOptions] = None) -> None:
        """Register middleware for HTTP GET requests."""
        return self.method([HttpMethod.GET], *middleware, opts=opts)

    def post(self, *middleware: HttpMiddleware | HttpHandler, opts: Optional[MethodOptions] = None) -> None:
        """Register middleware for HTTP POST requests."""
        return self.method([HttpMethod.POST], *middleware, opts=opts)

    def put(self, *middleware: HttpMiddleware | HttpHandler, opts: Optional[MethodOptions] = None) -> None:
        """Register middleware for HTTP PUT requests."""
        return self.method([HttpMethod.PUT], *middleware, opts=opts)

    def patch(self, *middleware: HttpMiddleware | HttpHandler, opts: Optional[MethodOptions] = None) -> None:
        """Register middleware for HTTP PATCH requests."""
        return self.method([HttpMethod.PATCH], *middleware, opts=opts)

    def delete(self, *middleware: HttpMiddleware | HttpHandler, opts: Optional[MethodOptions] = None) -> None:
        """Register middleware for HTTP DELETE requests."""
        return self.method([HttpMethod.DELETE], *middleware, opts=opts)

    def options(self, *middleware: HttpMiddleware | HttpHandler, opts: Optional[MethodOptions] = None) -> None:
        """Register middleware for HTTP OPTIONS requests."""
        return self.method([HttpMethod.OPTIONS], *middleware, opts=opts)


class Method:
    """A method handler."""

    server: FunctionServer
    route: Route
    methods: List[HttpMethod]
    opts: Optional[MethodOptions]

    def __init__(
        self,
        route: Route,
        methods: List[HttpMethod],
        *middleware: HttpMiddleware | HttpHandler,
        opts: Optional[MethodOptions] = None,
    ):
        """Construct a method handler for the specified route."""
        self.route = route
        self.methods = methods
        self.server = FunctionServer(ApiWorkerOptions(route.api.name, route.path, methods, opts))
        self.server.http(*route.api.middleware, *route.middleware, *middleware)

    def start(self) -> None:
        """Start the server which will respond to incoming requests."""
        Nitric._register_worker(self.server)  # type: ignore


def api(name: str, opts: Optional[ApiOptions] = None) -> Api:
    """Create a new API resource."""
    return Nitric._create_resource(Api, name, opts=opts)  # type: ignore
