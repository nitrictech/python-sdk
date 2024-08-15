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

import logging
from dataclasses import dataclass
from typing import Callable, Concatenate, Dict, List, Optional, ParamSpec, TypeVar, Union

import betterproto
import grpclib
from grpclib import GRPCError

from nitric.application import Nitric
from nitric.bidi import AsyncNotifierList
from nitric.context import (
    FunctionServer,
    HttpContext,
    HttpHandler,
    HttpMethod,
    HttpMiddleware,
    HttpRequest,
    Record,
    compose_middleware,
)
from nitric.exception import exception_from_grpc_error
from nitric.proto.apis.v1 import (
    ApiDetailsRequest,
    ApiStub,
    ApiWorkerOptions,
    ApiWorkerScopes,
    ClientMessage,
    HeaderValue,
)
from nitric.proto.apis.v1 import HttpRequest as ProtoHttpRequest
from nitric.proto.apis.v1 import HttpResponse as ProtoHttpResponse
from nitric.proto.apis.v1 import RegistrationRequest
from nitric.proto.resources.v1 import (
    ApiOpenIdConnectionDefinition,
    ApiResource,
    ApiScopes,
    ApiSecurityDefinitionResource,
    ResourceDeclareRequest,
    ResourceIdentifier,
    ResourceType,
)
from nitric.resources.resource import Resource as BaseResource
from nitric.channel import ChannelManager


@dataclass
class ApiDetails:
    """
    Represents a deployed API's details.

    url (str): the url of the API
    """

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


@dataclass
class MethodOptions:
    """
    Represents options when defining a method handler.

    security (dict[str, List[str]])
    """

    security: Optional[List[ScopedOidcOptions]] = None


# SecurityDefinition = JwtSecurityDefinition


class ApiOptions:
    """Represents options when creating an API, such as middleware to be applied to all HTTP request to the API."""

    path: str
    middleware: Optional[Union[HttpMiddleware, List[HttpMiddleware]]]
    security: Optional[List[ScopedOidcOptions]]

    def __init__(
        self,
        path: str = "",
        middleware: Optional[Union[HttpMiddleware, List[HttpMiddleware]]] = None,
        security: Optional[List[ScopedOidcOptions]] = None,
    ):
        """Construct a new API options object."""
        if middleware is None:
            middleware = []
        if security is None:
            security = []
        self.middleware = middleware
        self.security = security
        self.path = path


class RouteOptions:
    """Represents options when creating a route, such as middleware to be applied to all HTTP Methods for the route."""

    middleware: Union[None, List[HttpMiddleware]]

    def __init__(self, middleware: Optional[List[HttpMiddleware]] = None):
        """Construct a new route options object."""
        if middleware is None:
            middleware = []
        self.middleware = middleware


def _to_resource_identifier(b: Api) -> ResourceIdentifier:
    return ResourceIdentifier(name=b.name, type=ResourceType.Api)


def _security_to_grpc_declaration(security: Optional[List[ScopedOidcOptions]] = None) -> dict[str, ApiScopes]:
    if security is None or len(security) == 0:
        return {}
    return {sec.name: ApiScopes(sec.scopes) for sec in security}


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
    security: Optional[List[ScopedOidcOptions]]
    _api_stub: ApiStub

    def __init__(self, name: str, opts: Optional[ApiOptions] = None):
        """Construct a new HTTP API."""
        super().__init__(name)
        self._api_stub = ApiStub(channel=self._channel)
        if opts is None:
            opts = ApiOptions()

        self.middleware = (
            opts.middleware
            if isinstance(opts.middleware, list)
            else [opts.middleware] if opts.middleware is not None else []
        )
        self.path = opts.path
        self.routes = []
        self.security = opts.security

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    id=_to_resource_identifier(self),
                    api=ApiResource(
                        security=_security_to_grpc_declaration(self.security),
                    ),
                )
            )

            # Attach security rules for this api
            for security_rule in self.security if self.security else []:
                _attach_oidc(api_name=self.name, options=security_rule)
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    def _route(self, match: str, opts: Optional[RouteOptions] = None) -> Route:
        """Define an HTTP route to be handled by this API."""
        if opts is None:
            opts = RouteOptions()

        if self.middleware is not None:
            opts.middleware = (self.middleware + opts.middleware) if opts.middleware is not None else self.middleware

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
                opts=opts if opts is not None else MethodOptions(security=None),
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
            res = await self._api_stub.api_details(
                api_details_request=ApiDetailsRequest(
                    api_name=self.name,
                )
            )
            return ApiDetails(res.url)
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

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

        # ensure route/api middlewares are added
        middleware = (
            *self.middleware,
            *middleware
        )

        Method(self, methods, *middleware, opts=opts if opts else MethodOptions())

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

    server: ApiRouteWorker
    route: Route
    methods: List[HttpMethod]
    opts: Optional[MethodOptions]

    def __init__(
        self,
        route: Route,
        methods: List[HttpMethod],
        *middleware: HttpMiddleware | HttpHandler,
        opts: MethodOptions,
    ):
        """Construct a method handler for the specified route."""
        self.route = route
        self.methods = methods

        handler = compose_middleware(*middleware)

        self.server = ApiRouteWorker(
            api_name=self.route.api.name, path=self.route.path, methods=self.methods, handler=handler, options=opts
        )


def _http_context_from_proto(msg: ProtoHttpRequest) -> HttpContext:
    """Construct a new HttpContext from a Http trigger from the Nitric Membrane."""
    headers: Record = {k: v.value for (k, v) in msg.headers.items()}
    query: Record = {k: v.value for (k, v) in msg.query_params.items()}

    return HttpContext(
        request=HttpRequest(
            data=msg.body,
            method=msg.method,
            query=query,
            path=msg.path,
            params=dict(msg.path_params.items()),
            headers=headers,
        )
    )


def _http_context_to_proto_response(ctx: HttpContext) -> ProtoHttpResponse:
    """Construct a HttpResponse for the Nitric Membrane from this context object."""
    body = ctx.res.body if ctx.res.body else bytes()
    headers: Dict[str, HeaderValue] = {}
    for k, v in ctx.res.headers.items():
        hv = HeaderValue()
        hv.value = HttpContext._ensure_value_is_list(v)  # pylint: disable=protected-access
        headers[k] = hv

    return ProtoHttpResponse(
        status=ctx.res.status,
        body=body,
        headers=headers,
    )


class ApiRouteWorker(FunctionServer):
    """A worker for handling HTTP requests for a specific API route."""

    _handler: HttpHandler
    _registration_request: RegistrationRequest
    _responses: AsyncNotifierList[ClientMessage]
    _options: MethodOptions

    def __init__(
        self,
        api_name: str,
        path: str,
        methods: List[HttpMethod],
        handler: HttpHandler,
        options: MethodOptions,
    ):
        """Construct a new ApiRouteWorker."""
        sec = {opt.name: ApiWorkerScopes(scopes=opt.scopes) for opt in options.security} if options.security else {}
        reg_options = ApiWorkerOptions(
            security=sec,
            security_disabled=True if options.security == [] else False,
        )

        self._handler = handler
        self._responses = AsyncNotifierList()
        self._options = options
        self._registration_request = RegistrationRequest(
            api=api_name,
            path=path,
            methods=[method.value for method in methods],
            options=reg_options,
        )

        Nitric._register_worker(self)

    async def _route_request_iterator(self):
        # Register with the server
        yield ClientMessage(registration_request=self._registration_request)
        # wait for any responses for the server and send them
        async for response in self._responses:
            yield response

    async def start(self) -> None:
        """Register this API route handler and handle http requests."""
        channel = ChannelManager.get_channel()
        server = ApiStub(channel=channel)

        # Attach security rules for this route
        for security_rule in self._options.security if self._options.security else []:
            _attach_oidc(api_name=self._registration_request.api, options=security_rule)

        try:
            async for server_msg in server.serve(self._route_request_iterator()):
                msg_type, _ = betterproto.which_one_of(server_msg, "content")

                if msg_type == "registration_response":
                    continue
                if msg_type == "http_request":
                    ctx = _http_context_from_proto(server_msg.http_request)
                    response: ClientMessage
                    try:
                        result = await self._handler(ctx)
                        ctx = result if result else ctx
                        response = ClientMessage(id=server_msg.id, http_response=_http_context_to_proto_response(ctx))
                    except Exception as e:  # pylint: disable=broad-except
                        logging.exception("An unhandled error occurred in an api route handler: %s", e)
                        failed_http_response = ProtoHttpResponse(
                            status=500,
                            body=b"Internal Server Error",
                        )
                        response = ClientMessage(id=server_msg.id, http_response=failed_http_response)
                    await self._responses.add_item(response)
        except grpclib.exceptions.GRPCError as e:
            print(f"Stream terminated: {e.message}")
        except grpclib.exceptions.StreamTerminatedError:
            print("Stream from membrane closed.")
        finally:
            print("Closing client stream")
            channel.close()


def api(name: str, opts: Optional[ApiOptions] = None) -> Api:
    """Create a new API resource."""
    return Nitric._create_resource(Api, name, opts=opts)  # type: ignore pylint: disable=protected-access


class OidcOptions:
    """An OIDC security definition for an API."""

    name: str
    issuer: str
    audiences: List[str]

    def __init__(self, name: str, issuer: str, audiences: List[str]):
        """Construct a new OIDC security definition."""
        self.name = name
        self.issuer = issuer
        self.audiences = audiences


class ScopedOidcOptions(OidcOptions):
    """An OIDC security definition for an API with scopes."""

    scopes: List[str]

    def __init__(self, name: str, issuer: str, audiences: List[str], scopes: List[str]):
        """Construct a new scoped OIDC security definition."""
        super().__init__(name=name, issuer=issuer, audiences=audiences)
        self.scopes = scopes


def _oidc_to_resource(b: OidcSecurityDefinition) -> ResourceIdentifier:
    """Generate a resource identifier for an OIDC security definition."""
    return ResourceIdentifier(name=b.name, type=ResourceType.ApiSecurityDefinition)


class OidcSecurityDefinition(BaseResource):
    """An OIDC security definition for an API."""

    api_name: str
    issuer: str
    rule_name: str
    audiences: List[str]

    def __init__(self, name: str, api_name: str, options: OidcOptions):
        """Construct a new OIDC security definition."""
        super().__init__(name)
        self.api_name = api_name
        self.issuer = options.issuer
        self.audiences = options.audiences
        self.rule_name = options.name

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(
                    id=_oidc_to_resource(self),
                    api_security_definition=ApiSecurityDefinitionResource(
                        api_name=self.api_name,
                        oidc=ApiOpenIdConnectionDefinition(
                            issuer=self.issuer,
                            audiences=self.audiences,
                        ),
                    ),
                )
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err


def _attach_oidc(api_name: str, options: OidcOptions) -> OidcSecurityDefinition:
    return Nitric._create_resource(  # pylint: disable=protected-access
        OidcSecurityDefinition, f"{options.name}-{api_name}", api_name, options
    )


def oidc_rule(name: str, issuer: str, audiences: List[str]) -> Callable[[List[str]], ScopedOidcOptions]:
    """Create a function that returns scoped OIDC security definitions."""
    return lambda scopes: ScopedOidcOptions(name, issuer, audiences, scopes)
