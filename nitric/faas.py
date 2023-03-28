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
from enum import Enum

import functools
import json
import traceback
from typing import Dict, Union, List, TypeVar, Callable, Coroutine, Any, Optional
from opentelemetry import context, propagate

import betterproto
from betterproto.grpc.util.async_channel import AsyncChannel
from nitric.utils import new_default_channel
from nitric.proto.nitric.faas.v1 import (
    FaasServiceStub,
    InitRequest,
    ClientMessage,
    TriggerRequest,
    TriggerResponse,
    HeaderValue,
    HttpResponseContext,
    TopicResponseContext,
    ScheduleWorker,
    ApiWorker,
    SubscriptionWorker,
    ScheduleRate,
)
import grpclib
import asyncio
from abc import ABC

Record = Dict[str, Union[str, List[str]]]
PROPAGATOR = propagate.get_global_textmap()


class HttpMethod(Enum):
    """Valid query expression operators."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"

    def __str__(self):
        return str(self.value)


class Request(ABC):
    """Represents an abstract trigger request."""

    def __init__(self, data: bytes):
        """Construct a new Request."""
        self.data = data


class Response(ABC):
    """Represents an abstract trigger response."""

    pass


class TriggerContext(ABC):
    """Represents an abstract request/response context for any trigger."""

    def http(self) -> Union[HttpContext, None]:
        """Return this context as an HttpContext if it is one, otherwise returns None."""
        return None

    def event(self) -> Union[EventContext, None]:
        """Return this context as an EventContext if it is one, otherwise returns None."""
        return None


def _ctx_from_grpc_trigger_request(trigger_request: TriggerRequest):
    """Return a TriggerContext from a TriggerRequest."""
    context_type, context = betterproto.which_one_of(trigger_request, "context")
    if context_type == "http":
        return HttpContext.from_grpc_trigger_request(trigger_request)
    elif context_type == "topic":
        return EventContext.from_grpc_trigger_request(trigger_request)
    else:
        print(f"Trigger with unknown context received, context type: {context_type}")
        raise Exception(f"Unknown trigger context, type: {context_type}")


def _grpc_response_from_ctx(ctx: TriggerContext) -> TriggerResponse:
    """
    Create a GRPC TriggerResponse from a TriggerContext.

    The ctx is used to determine the appropriate TriggerResponse content,
    the ctx.res is then used to construct the response.
    """
    if ctx.http():
        ctx = ctx.http()
        headers = {k: HeaderValue(value=v) for (k, v) in ctx.res.headers.items()}
        headers_old = {k: v[0] for (k, v) in ctx.res.headers.items()}
        data = ctx.res.body if ctx.res.body else bytes()

        return TriggerResponse(
            data=data,
            http=HttpResponseContext(status=ctx.res.status, headers=headers, headers_old=headers_old),
        )
    elif ctx.event():
        ctx = ctx.event()
        return TriggerResponse(
            topic=TopicResponseContext(
                success=ctx.res.success,
            ),
        )
    else:
        raise Exception("Unknown Trigger Context type, unable to return valid response")


# ====== HTTP ======


class HttpRequest(Request):
    """Represents a translated Http Request forwarded from the Nitric Membrane."""

    def __init__(
        self,
        data: bytes,
        method: str,
        path: str,
        params: Dict[str, str],
        query: Record,
        headers: Record,
        trace_context: Dict[str, str],
    ):
        """Construct a new HttpRequest."""
        super().__init__(data)
        self.method = method
        self.path = path
        self.params = params
        self.query = query
        self.headers = headers
        self.trace_context = trace_context

    @property
    def json(self) -> Optional[Any]:
        """Get the body of the request as JSON, returns None if request body is not JSON."""
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:
            return None
        except TypeError:
            return None

    @property
    def body(self):
        """Get the body of the request as text."""
        return self.data.decode("utf-8")


class HttpResponse(Response):
    """Represents an HTTP Response to be generated by the Nitric Membrane in response to an HTTP Request Trigger."""

    def __init__(self, status: int = 200, headers: Record = None, body: bytes = None):
        """Construct a new HttpResponse."""
        self.status = status
        self.headers = headers if headers else {}
        self._body = body if body else bytes()

    @property
    def body(self):
        """Return the HTTP response body."""
        return self._body

    @body.setter
    def body(self, value: Union[str, bytes, Any]):
        if isinstance(value, str):
            self._body = value.encode("utf-8")
        elif isinstance(value, bytes):
            self._body = value
        else:
            self._body = json.dumps(value).encode("utf-8")
            self.headers["Content-Type"] = ["application/json"]


class HttpContext(TriggerContext):
    """Represents the full request/response context for an Http based trigger."""

    def __init__(self, request: HttpRequest, response: HttpResponse = None):
        """Construct a new HttpContext."""
        super().__init__()
        self.req = request
        self.res = response if response else HttpResponse()

    def http(self) -> HttpContext:
        """Return this HttpContext, used when determining the context type of a trigger."""
        return self

    @staticmethod
    def from_grpc_trigger_request(trigger_request: TriggerRequest) -> HttpContext:
        """Construct a new HttpContext from an Http trigger from the Nitric Membrane."""
        if len(trigger_request.http.headers.keys()) > 0:
            headers = {k: v.value for (k, v) in trigger_request.http.headers.items()}
        else:
            headers = trigger_request.http.headers_old

        if len(trigger_request.http.query_params.keys()) > 0:
            query = {k: v.value for (k, v) in trigger_request.http.query_params.items()}
        else:
            query = trigger_request.http.query_params_old

        return HttpContext(
            request=HttpRequest(
                data=trigger_request.data,
                method=trigger_request.http.method,
                query=query,
                path=trigger_request.http.path,
                params={k: v for (k, v) in trigger_request.http.path_params.items()},
                headers=headers,
                trace_context=trigger_request.trace_context,
            )
        )


class EventRequest(Request):
    """Represents a translated Event, from a Subscribed Topic, forwarded from the Nitric Membrane."""

    def __init__(self, data: bytes, topic: str, trace_context: Dict[str, str]):
        """Construct a new EventRequest."""
        super().__init__(data)
        self.topic = topic
        self.trace_context = trace_context

    @property
    def payload(self) -> bytes:
        """Return the payload of this request as text."""
        return json.loads(self.data.decode("utf-8"))


class EventResponse(Response):
    """Represents the response to a trigger from an Event as a result of a Topic subscription."""

    def __init__(self, success: bool = True):
        """Construct a new EventResponse."""
        self.success = success


class EventContext(TriggerContext):
    """Represents the full request/response context for an Event based trigger."""

    def __init__(self, request: EventRequest, response: EventResponse = None):
        """Construct a new EventContext."""
        super().__init__()
        self.req = request
        self.res = response if response else EventResponse()

    def event(self) -> EventContext:
        """Return this EventContext, used when determining the context type of a trigger."""
        return self

    @staticmethod
    def from_grpc_trigger_request(trigger_request: TriggerRequest):
        """Construct a new EventContext from an Event trigger from the Nitric Membrane."""
        return EventContext(
            request=EventRequest(
                data=trigger_request.data,
                topic=trigger_request.topic.topic,
                trace_context=trigger_request.trace_context,
            )
        )


# async def face(inpp: int) -> str:
#     return "thing"


# ====== Function Handlers ======

C = TypeVar("C", TriggerContext, HttpContext, EventContext)
Middleware = Callable
Handler = Coroutine[Any, Any, C]
HttpHandler = Coroutine[Any, Any, Optional[HttpContext]]
EventHandler = Coroutine[Any, Any, Optional[EventContext]]
Middleware = Callable[[C, Middleware], Handler]
HttpMiddleware = Callable[[HttpContext, HttpHandler], HttpHandler]
EventMiddleware = Callable[[EventContext, EventHandler], EventHandler]


def compose_middleware(*middlewares: Union[Middleware, List[Middleware]]) -> Middleware:
    """
    Compose multiple middleware functions into a single middleware function.

    The resulting middleware will effectively be a chain of the provided middleware,
    where each calls the next in the chain when they're successful.
    """
    middlewares = list(middlewares)
    if len(middlewares) == 1 and not isinstance(middlewares[0], list):
        return middlewares[0]

    middlewares = [compose_middleware(m) if isinstance(m, list) else m for m in middlewares]

    async def handler(ctx, next_middleware=lambda ctx: ctx):
        def reduce_chain(acc_next, cur):
            async def chained_middleware(context):
                # Count the positional arguments to determine if the function is a handler or middleware.
                all_args = cur.__code__.co_argcount
                kwargs = len(cur.__defaults__) if cur.__defaults__ is not None else 0
                pos_args = all_args - kwargs
                if pos_args == 2:
                    # Call the middleware with next and return the result
                    return (
                        (await cur(context, acc_next)) if asyncio.iscoroutinefunction(cur) else cur(context, acc_next)
                    )
                else:
                    # Call the handler with ctx only, then call the remainder of the middleware chain
                    result = (await cur(context)) if asyncio.iscoroutinefunction(cur) else cur(context)
                    return (await acc_next(result)) if asyncio.iscoroutinefunction(acc_next) else acc_next(result)

            return chained_middleware

        middleware_chain = functools.reduce(reduce_chain, reversed(middlewares + [next_middleware]))
        return await middleware_chain(ctx)

    return handler


# ====== Function Server ======


def _create_internal_error_response(req: TriggerRequest) -> TriggerResponse:
    """Create a general error response based on the trigger request type."""
    context_type, context = betterproto.which_one_of(req, "context")
    if context_type == "http":
        return TriggerResponse(data=bytes(), http=HttpResponseContext(status=500))
    elif context_type == "topic":
        return TriggerResponse(data=bytes(), topic=TopicResponseContext(success=False))
    else:
        raise Exception(f"Unknown trigger type: {context_type}, unable to generate expected response")


class ApiWorkerOptions:
    """Options for API workers."""

    def __init__(self, api: str, route: str, methods: List[Union[str, HttpMethod]], opts: MethodOptions):
        """Construct a new options object."""
        self.api = api
        self.route = route
        self.methods = [str(method) for method in methods]
        self.opts = opts


class RateWorkerOptions:
    """Options for rate workers."""

    description: str
    rate: int
    frequency: Frequency

    def __init__(self, description: str, rate: int, frequency: Frequency):
        """Construct a new options object."""
        self.description = description
        self.rate = rate
        self.frequency = frequency


class SubscriptionWorkerOptions:
    """Options for subscription workers."""

    def __init__(self, topic: str):
        """Construct a new options object."""
        self.topic = topic


class Frequency(Enum):
    """Valid schedule frequencies."""

    seconds = "seconds"
    minutes = "minutes"
    hours = "hours"
    days = "days"

    @staticmethod
    def from_str(value: str) -> Frequency:
        """Convert a string frequency value to a Frequency."""
        return Frequency[value.strip().lower()]

    @staticmethod
    def as_str_list() -> List[str]:
        """Return all frequency values as a list of strings."""
        return [str(frequency.value) for frequency in Frequency]


class MethodOptions:
    """Represents options when defining a method handler."""

    security: dict[str, List[str]]

    def __init__(self, security: dict[str, List[str]] = None):
        """Construct a new HTTP method options object."""
        self.security = security


class FaasWorkerOptions:
    """Empty worker options for generic function handlers."""

    pass


FaasClientOptions = Union[ApiWorkerOptions, RateWorkerOptions, SubscriptionWorkerOptions, FaasWorkerOptions]


class FunctionServer:
    """A Function as a Service server, which acts as a faas handler for the Nitric Membrane."""

    def __init__(self, opts: FaasClientOptions):
        """Construct a new function server."""
        self.__http_handler = None
        self.__event_handler = None
        self._any_handler = None
        self._opts = opts

    def http(self, *handlers: Union[Middleware, List[Middleware]]) -> FunctionServer:
        """
        Register one or more HTTP Trigger Handlers or Middleware.

        When multiple handlers are provided, they will be called in order.
        """
        self.__http_handler = compose_middleware(*handlers)
        return self

    def event(self, *handlers: Union[Middleware, List[Middleware]]) -> FunctionServer:
        """
        Register one or more Event Trigger Handlers or Middleware.

        When multiple handlers are provided, they will be called in order.
        """
        self.__event_handler = compose_middleware(*handlers)
        return self

    async def start(self, *handlers: Union[Middleware, List[Middleware]]):
        """Start the function server using the provided trigger handlers."""
        self._any_handler = compose_middleware(*handlers) if len(handlers) > 0 else None
        if not self._any_handler and not self._http_handler and not self._event_handler:
            raise Exception("At least one handler function must be provided.")

        await self._run()

    @property
    def _http_handler(self):
        return self.__http_handler if self.__http_handler else self._any_handler

    @property
    def _event_handler(self):
        return self.__event_handler if self.__event_handler else self._any_handler

    async def _run(self):
        """Register a new FaaS worker with the Membrane, using the provided function as the handler."""
        channel = new_default_channel()
        client = FaasServiceStub(channel)
        request_channel = AsyncChannel(close=True)
        # We can start be sending all the requests we already have
        try:
            init_request = InitRequest()
            # Construct init request based on API worker options
            if isinstance(self._opts, ApiWorkerOptions):
                init_request = InitRequest(
                    api=ApiWorker(api=self._opts.api, path=self._opts.route, methods=self._opts.methods)
                )
            elif isinstance(self._opts, RateWorkerOptions):
                # TODO: Populate rate
                init_request = InitRequest(
                    schedule=ScheduleWorker(
                        key=self._opts.description, rate=ScheduleRate(rate=f"{self._opts.rate} {self._opts.frequency}")
                    )
                )
            elif isinstance(self._opts, SubscriptionWorkerOptions):
                init_request = InitRequest(subscription=SubscriptionWorker(topic=self._opts.topic))

            # let the membrane server know we're ready to start
            await request_channel.send(ClientMessage(init_request=init_request))
            async for srv_msg in client.trigger_stream(request_channel):
                # The response iterator will remain active until the connection is closed
                msg_type, val = betterproto.which_one_of(srv_msg, "content")

                if msg_type == "init_response":
                    print("function connected to Membrane")
                    # We don't need to reply
                    # proceed to the next available message
                    continue
                if msg_type == "trigger_request":
                    ctx = _ctx_from_grpc_trigger_request(srv_msg.trigger_request)

                    try:
                        if len(ctx.req.trace_context) > 0:
                            context.attach(PROPAGATOR().extract(ctx.req.trace_context))

                        if ctx.http():
                            func = self._http_handler
                        elif ctx.event():
                            func = self._event_handler
                        else:
                            func = self._any_handler

                        response_ctx = (await func(ctx)) if asyncio.iscoroutinefunction(func) else func(ctx)

                        if response_ctx is None:
                            response_ctx = ctx

                        # Send function response back to server
                        await request_channel.send(
                            ClientMessage(
                                id=srv_msg.id,
                                trigger_response=_grpc_response_from_ctx(response_ctx),
                            )
                        )
                    except Exception:
                        # Any unhandled exceptions in the above code will end the loop
                        # and stop processing future triggers, we catch them here as a last resort.
                        print("An unexpected error occurred processing trigger or response")
                        traceback.print_exc()
                        response = _create_internal_error_response(srv_msg.trigger_request)
                        await request_channel.send(ClientMessage(id=srv_msg.id, trigger_response=response))
                else:
                    print(f"unhandled message type {msg_type}, skipping")
                    continue
                if request_channel.done():
                    break
        except grpclib.exceptions.StreamTerminatedError:
            print("stream from Membrane closed, closing client stream")
        except asyncio.CancelledError:
            # Membrane has closed stream after init
            print("stream from Membrane closed, closing client stream")
        except ConnectionRefusedError as cre:
            traceback.print_exc()
            raise ConnectionRefusedError("Failed to register function with Membrane") from cre
        except Exception as e:
            traceback.print_exc()
            raise Exception("An unexpected error occurred.") from e
        finally:
            # The channel must be closed to complete the gRPC connection
            request_channel.close()
            channel.close()


# Convenience functions to create function servers


def http(*handlers: Union[Middleware, List[Middleware]]) -> FunctionServer:
    """
    Create a new Function Server and Register one or more HTTP Trigger Handlers or Middleware.

    When multiple handlers are provided, they will be called in order.
    """
    return FunctionServer(opts=[]).http(*handlers)


def event(*handlers: Union[Middleware, List[Middleware]]) -> FunctionServer:
    """
    Create a new Function Server and Register one or more Event Trigger Handlers or Middleware.

    When multiple handlers are provided, they will be called in order.
    """
    return FunctionServer(opts=[]).event(*handlers)


def start(*handlers: Union[Middleware, List[Middleware]]):
    """Create a new Function Server and start it using the provided trigger handlers."""
    if len(handlers) < 1:
        raise Exception("At least one handler must be provided.")
    return FunctionServer(opts=[]).start(*handlers)
