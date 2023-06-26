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

import inspect
from enum import Enum

import functools
import json
import traceback
from typing import Dict, Generic, Protocol, Union, List, TypeVar, Any, Optional, Sequence
from opentelemetry import context, propagate

import betterproto
from betterproto.grpc.util.async_channel import AsyncChannel
from nitric.api.storage import BucketRef
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
    BucketNotificationWorker,
    BucketNotificationConfig,
    BucketNotificationType,
    NotificationResponseContext,
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

    def __init__(self, data: bytes, trace_context: Dict[str, str]):
        """Construct a new Request."""
        self.data = data
        self.trace_context = trace_context


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

    def bucket_notification(self) -> Union[BucketNotificationContext, None]:
        """Return this context as a BucketNotificationContext if it is one, otherwise returns None."""
        return None


def _ctx_from_grpc_trigger_request(trigger_request: TriggerRequest, options: Optional[FaasClientOptions] = None):
    """Return a TriggerContext from a TriggerRequest."""
    context_type, _ = betterproto.which_one_of(trigger_request, "context")
    if context_type == "http":
        return HttpContext.from_grpc_trigger_request(trigger_request)
    elif context_type == "topic":
        return EventContext.from_grpc_trigger_request(trigger_request)
    elif context_type == "notification":
        if isinstance(options, FileNotificationWorkerOptions):
            return FileNotificationContext.from_grpc_trigger_request_and_options(trigger_request, options)
        else:
            return BucketNotificationContext.from_grpc_trigger_request(trigger_request)
    else:
        print(f"Trigger with unknown context received, context type: {context_type}")
        raise Exception(f"Unknown trigger context, type: {context_type}")


def _ensure_header_is_list(value: Union[str, Sequence[str]]) -> List[str]:
    if isinstance(value, str):
        return [value]
    return list(value)


def _grpc_response_from_ctx(ctx: TriggerContext) -> TriggerResponse:
    """
    Create a GRPC TriggerResponse from a TriggerContext.

    The ctx is used to determine the appropriate TriggerResponse content,
    the ctx.res is then used to construct the response.
    """
    http_context = ctx.http()
    if http_context is not None:
        headers = {k: HeaderValue(value=_ensure_header_is_list(v)) for (k, v) in http_context.res.headers.items()}
        data = http_context.res.body if http_context.res.body else bytes()

        return TriggerResponse(
            data=data,
            http=HttpResponseContext(status=http_context.res.status, headers=headers),
        )

    event_context = ctx.event()
    if event_context is not None:
        return TriggerResponse(
            topic=TopicResponseContext(
                success=event_context.res.success,
            ),
        )

    bucket_context = ctx.bucket_notification()
    if bucket_context is not None:
        return TriggerResponse(notification=NotificationResponseContext(success=bucket_context.res.success))

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
        super().__init__(data, trace_context)
        self.method = method
        self.path = path
        self.params = params
        self.query = query
        self.headers = headers

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

    def __init__(self, status: int = 200, headers: Optional[Record] = None, body: Optional[bytes] = None):
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

    def __init__(self, request: HttpRequest, response: Optional[HttpResponse] = None):
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
        headers: Record = {k: v.value for (k, v) in trigger_request.http.headers.items()}
        query: Record = {k: v.value for (k, v) in trigger_request.http.query_params.items()}

        return HttpContext(
            request=HttpRequest(
                data=trigger_request.data,
                method=trigger_request.http.method,
                query=query,
                path=trigger_request.http.path,
                params={k: v for (k, v) in trigger_request.http.path_params.items()},
                headers=headers,
                trace_context=trigger_request.trace_context.values,
            )
        )


class EventRequest(Request):
    """Represents a translated Event, from a Subscribed Topic, forwarded from the Nitric Membrane."""

    def __init__(self, data: bytes, topic: str, trace_context: Dict[str, str]):
        """Construct a new EventRequest."""
        super().__init__(data, trace_context)
        self.topic = topic

    @property
    def payload(self) -> Any:
        """Return the payload of this event, usually a dictionary."""
        event_envelope = json.loads(self.data.decode("utf-8"))
        return event_envelope["payload"] if isinstance(event_envelope, dict) else event_envelope


class EventResponse(Response):
    """Represents the response to a trigger from an Event as a result of a Topic subscription."""

    def __init__(self, success: bool = True):
        """Construct a new EventResponse."""
        self.success = success


class EventContext(TriggerContext):
    """Represents the full request/response context for an Event based trigger."""

    def __init__(self, request: EventRequest, response: Optional[EventResponse] = None):
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
                trace_context=trigger_request.trace_context.values,
            )
        )


class BucketNotificationRequest(Request):
    """Represents a translated Event, from a subscribed bucket notification, forwarded from the Nitric Membrane."""

    def __init__(self, data: bytes, key: str, notification_type: BucketNotificationType, trace_context: Dict[str, str]):
        """Construct a new EventRequest."""
        super().__init__(data, trace_context)

        self.key = key
        self.notification_type = notification_type


class BucketNotificationResponse(Response):
    """Represents the response to a trigger from a Bucket."""

    def __init__(self, success: bool = True):
        """Construct a new BucketNotificationResponse."""
        self.success = success


class BucketNotificationContext(TriggerContext):
    """Represents the full request/response context for a bucket notification trigger."""

    def __init__(self, request: BucketNotificationRequest, response: Optional[BucketNotificationResponse] = None):
        """Construct a new BucketNotificationContext."""
        super().__init__()
        self.req = request
        self.res = response if response else BucketNotificationResponse()

    def bucket_notification(self) -> BucketNotificationContext:
        """Return this BucketNotificationContext, used when determining the context type of a trigger."""
        return self

    @staticmethod
    def from_grpc_trigger_request(trigger_request: TriggerRequest) -> BucketNotificationContext:
        """Construct a new BucketNotificationContext from a Bucket Notification trigger from the Nitric Membrane."""
        return BucketNotificationContext(
            request=BucketNotificationRequest(
                data=trigger_request.data,
                key=trigger_request.notification.bucket.key,
                notification_type=trigger_request.notification.bucket.type,
                trace_context=trigger_request.trace_context.values,
            )
        )


class FileNotificationRequest(BucketNotificationRequest):
    """Represents a translated Event, from a subscribed bucket notification, forwarded from the Nitric Membrane."""

    def __init__(
        self,
        data: bytes,
        bucket_ref: Any,  # can't import BucketRef due to circular dependency problems
        key: str,
        notification_type: BucketNotificationType,
        trace_context: Dict[str, str],
    ):
        """Construct a new FileNotificationRequest."""
        super().__init__(data=data, key=key, notification_type=notification_type, trace_context=trace_context)
        self.file = bucket_ref.file(key)


class FileNotificationContext(BucketNotificationContext):
    """Represents the full request/response context for a bucket notification trigger."""

    def __init__(self, request: FileNotificationRequest, response: Optional[BucketNotificationResponse] = None):
        """Construct a new FileNotificationContext."""
        super().__init__(request=request, response=response)
        self.req = request

    def bucket_notification(self) -> BucketNotificationContext:
        """Return this FileNotificationContext, used when determining the context type of a trigger."""
        return self

    @staticmethod
    def from_grpc_trigger_request_and_options(
        trigger_request: TriggerRequest, options: FileNotificationWorkerOptions
    ) -> FileNotificationContext:
        """Construct a new FileNotificationTrigger from a Bucket Notification trigger from the Nitric Membrane."""
        return FileNotificationContext(
            request=FileNotificationRequest(
                data=trigger_request.data,
                key=trigger_request.notification.bucket.key,
                bucket_ref=options.bucket_ref,
                notification_type=trigger_request.notification.bucket.type,
                trace_context=trigger_request.trace_context.values,
            )
        )


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


class BucketNotificationWorkerOptions:
    """Options for bucket notification workers."""

    def __init__(self, bucket_name: str, notification_type: str, notification_prefix_filter: str):
        """Construct a new options object."""
        self.bucket_name = bucket_name
        self.notification_type = BucketNotificationWorkerOptions._to_grpc_event_type(notification_type.lower())
        self.notification_prefix_filter = notification_prefix_filter

    @staticmethod
    def _to_grpc_event_type(event_type: str) -> BucketNotificationType:
        if event_type == "write":
            return BucketNotificationType.Created
        elif event_type == "delete":
            return BucketNotificationType.Deleted
        else:
            raise ValueError(f"Event type {event_type} is unsupported")


class FileNotificationWorkerOptions(BucketNotificationWorkerOptions):
    """Options for bucket notification workers with file references."""

    def __init__(self, bucket: BucketRef, notification_type: str, notification_prefix_filter: str):
        """Construct a new FileNotificationWorkerOptions."""
        super().__init__(bucket.name, notification_type, notification_prefix_filter)

        self.bucket_ref = bucket


class ApiWorkerOptions:
    """Options for API workers."""

    def __init__(
        self, api: str, route: str, methods: Sequence[Union[str, HttpMethod]], opts: Optional[MethodOptions] = None
    ):
        """Construct a new options object."""
        self.api = api
        self.route = route
        self.methods = [str(method) for method in methods]
        self.opts = opts


class MethodOptions:
    """Represents options when defining a method handler."""

    security: Optional[dict[str, List[str]]]

    def __init__(self, security: Optional[dict[str, List[str]]] = None):
        """Construct a new HTTP method options object."""
        self.security = security


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
        try:
            return Frequency[value.strip().lower()]
        except Exception:
            raise ValueError(f"{value} is not valid frequency")

    @staticmethod
    def as_str_list() -> List[str]:
        """Return all frequency values as a list of strings."""
        return [str(frequency.value) for frequency in Frequency]


class FaasWorkerOptions:
    """Empty worker options for generic function handlers."""

    pass


FaasClientOptions = Union[
    ApiWorkerOptions,
    RateWorkerOptions,
    SubscriptionWorkerOptions,
    BucketNotificationWorkerOptions,
    FileNotificationWorkerOptions,
    FaasWorkerOptions,
]

# class Context(Protocol):
#     ...

C = TypeVar("C", TriggerContext, HttpContext, EventContext, FileNotificationContext, BucketNotificationContext)


class Middleware(Protocol, Generic[C]):
    """A middleware function."""

    async def __call__(self, ctx: C, nxt: Optional[Middleware[C]]) -> C:
        """Process trigger context."""
        ...


class Handler(Protocol, Generic[C]):
    """A handler function."""

    async def __call__(self, ctx: C) -> C | None:
        """Process trigger context."""
        ...


HttpMiddleware = Middleware[HttpContext]
EventMiddleware = Middleware[EventContext]
BucketNotificationMiddleware = Middleware[BucketNotificationContext]
FileNotificationMiddleware = Middleware[FileNotificationContext]

HttpHandler = Handler[HttpContext]
EventHandler = Handler[EventContext]
BucketNotificationHandler = Handler[BucketNotificationContext]
FileNotificationHandler = Handler[FileNotificationContext]


def _convert_to_middleware(handler: Handler[C] | Middleware[C]) -> Middleware[C]:
    """Convert a handler to a middleware, if it's already a middleware it's returned unchanged."""
    if not _is_handler(handler):
        # it's not a middleware, don't convert it.
        return handler  # type: ignore

    async def middleware(ctx: C, nxt: Middleware[C]) -> C:
        context = await handler(ctx)  # type: ignore
        return await nxt(context) if nxt else context  # type: ignore

    return middleware  # type: ignore


def _is_handler(unknown: Middleware[C] | Handler[C]) -> bool:
    """Return True if the provided function is a handler (1 positional arg)."""
    signature = inspect.signature(unknown)
    params = signature.parameters
    positional = [name for name, param in params.items() if param.default == inspect.Parameter.empty]
    return len(positional) == 1


def compose_middleware(*middlewares: Middleware[C] | Handler[C]) -> Middleware[C]:
    """
    Compose multiple middleware functions into a single middleware function.

    The resulting middleware will effectively be a chain of the provided middleware,
    where each calls the next in the chain when they're successful.
    """
    middlewares = [_convert_to_middleware(middleware) for middleware in middlewares]  # type: ignore

    async def composed(ctx: C, nxt: Optional[Middleware[C]] = None) -> C:
        last_middleware = nxt

        def reduce_chain(acc_next: Middleware[C], cur: Middleware[C]) -> Middleware[C]:
            async def chained_middleware(ctx: C, nxt: Optional[Middleware[C]] = None) -> C:
                result = (await nxt(ctx)) if nxt is not None else ctx  # type: ignore
                # type ignored because mypy appears to misidentify the correct return type
                output_context = await cur(result, acc_next)  # type: ignore
                if not output_context:
                    return result  # type: ignore
                if not isinstance(output_context, TriggerContext):
                    raise Exception(
                        f"middleware {cur} returned unexpected response type, expected a context object, "
                        f"got {output_context}"
                    )
                return output_context  # type: ignore

            return chained_middleware

        middleware_chain = functools.reduce(reduce_chain, reversed(middlewares))  # type: ignore
        # type ignored because mypy appears to misidentify the correct return type
        return await middleware_chain(ctx, last_middleware)  # type: ignore

    return composed


# ====== Function Server ======


def _create_internal_error_response(req: TriggerRequest) -> TriggerResponse:
    """Create a general error response based on the trigger request type."""
    context_type, _ = betterproto.which_one_of(req, "context")
    if context_type == "http":
        return TriggerResponse(data=bytes(), http=HttpResponseContext(status=500))
    elif context_type == "topic":
        return TriggerResponse(data=bytes(), topic=TopicResponseContext(success=False))
    else:
        raise Exception(f"Unknown trigger type: {context_type}, unable to generate expected response")


class FunctionServer:
    """A Function as a Service server, which acts as a faas handler for the Nitric Membrane."""

    def __init__(self, opts: FaasClientOptions):
        """Construct a new function server."""
        self.__http_handler: Optional[HttpMiddleware] = None
        self.__event_handler: Optional[EventMiddleware] = None
        self.__bucket_notification_handler: Optional[
            Union[BucketNotificationMiddleware, FileNotificationMiddleware]
        ] = None
        self._opts = opts

    def http(self, *handlers: HttpMiddleware | HttpHandler) -> FunctionServer:
        """
        Register one or more HTTP Trigger Handlers or Middleware.

        When multiple handlers are provided, they will be called in order.
        """
        self.__http_handler = compose_middleware(*handlers)
        return self

    def event(self, *handlers: EventMiddleware | EventHandler) -> FunctionServer:
        """
        Register one or more Event Trigger Handlers or Middleware.

        When multiple handlers are provided, they will be called in order.
        """
        self.__event_handler = compose_middleware(*handlers)
        return self

    def bucket_notification(
        self, *handlers: BucketNotificationMiddleware | BucketNotificationHandler
    ) -> FunctionServer:
        """
        Register one or more Bucket Notification Trigger Handlers or Middleware.

        When multiple handlers are provided, they will be called in order.
        """
        self.__bucket_notification_handler = compose_middleware(*handlers)
        return self

    async def start(self):
        """Start the function server using the previously provided middleware."""
        if not self._http_handler and not self._event_handler and not self.__bucket_notification_handler:
            raise Exception("At least one handler function must be provided.")

        await self._run()

    @property
    def _http_handler(self):
        return self.__http_handler

    @property
    def _event_handler(self):
        return self.__event_handler

    @property
    def _bucket_notification_handler(self):
        return self.__bucket_notification_handler

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
            elif isinstance(self._opts, BucketNotificationWorkerOptions) or isinstance(
                self._opts, FileNotificationWorkerOptions
            ):
                config = BucketNotificationConfig(
                    notification_type=self._opts.notification_type,
                    notification_prefix_filter=self._opts.notification_prefix_filter,
                )
                init_request = InitRequest(
                    bucket_notification=BucketNotificationWorker(bucket=self._opts.bucket_name, config=config)
                )

            # let the membrane server know we're ready to start
            await request_channel.send(ClientMessage(init_request=init_request))
            async for srv_msg in client.trigger_stream(request_channel):
                # The response iterator will remain active until the connection is closed
                msg_type, _ = betterproto.which_one_of(srv_msg, "content")

                if msg_type == "init_response":
                    print("function connected to Membrane")
                    # We don't need to reply
                    # proceed to the next available message
                    continue
                if msg_type == "trigger_request":
                    ctx: Any = _ctx_from_grpc_trigger_request(srv_msg.trigger_request, self._opts)  # type: ignore

                    try:
                        if len(ctx.req.trace_context) > 0:
                            context.attach(PROPAGATOR.extract(ctx.req.trace_context))

                        if ctx.http():
                            func = self._http_handler
                        elif ctx.event():
                            func = self._event_handler
                        elif ctx.bucket_notification():
                            func = self._bucket_notification_handler

                        assert func is not None

                        response_ctx: TriggerContext = await func(ctx)  # type: ignore

                        # TODO: should we allow middleware/handlers that return None still?
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
