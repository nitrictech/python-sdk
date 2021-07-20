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
from dataclasses import dataclass, field
from typing import Union
from nitric.proto.nitric.faas import v1
from nitric.proto.nitric.faas.v1 import TriggerResponse


@dataclass(order=True)
class TopicResponseContext(object):
    """Represents a topic/event specific response context data such as whether the event was processed successfully."""

    success: bool = True

    def to_grpc_topic_response_context(self) -> v1.TopicResponseContext:
        """Reformat this topic response context for on the wire transfer."""
        return v1.TopicResponseContext(success=self.success)


@dataclass(order=True)
class HttpResponseContext(object):
    """Represents HTTP specific response context data such as an HTTP status and headers."""

    headers: dict = field(default_factory=lambda: {})
    status: int = 200

    def to_grpc_http_response_context(self) -> v1.HttpResponseContext:
        """Reformat this http response context for on the wire transfer."""
        return v1.HttpResponseContext(headers=self.headers, status=self.status)


@dataclass(order=True)
class ResponseContext(object):
    """Additional context data for a trigger response, specific to the original trigger type."""

    context: Union[TopicResponseContext, HttpResponseContext]

    def is_http(self):
        """Indicate whether the trigger was from an HTTP request."""
        return isinstance(self.context, HttpResponseContext)

    def is_topic(self):
        """Indicate whether the trigger was from a topic (event)."""
        return isinstance(self.context, TopicResponseContext)

    def as_http(self) -> Union[HttpResponseContext, None]:
        """
        Return this context as an HTTP context type.

        If the trigger wasn't an HTTP request, this function returns None.
        is_http() should be used first to determine if this was an HTTP request trigger.
        """
        if not self.is_http():
            return None

        return self.context

    def as_topic(self) -> Union[TopicResponseContext, None]:
        """
        Return this context as a topic context type.

        If the trigger wasn't an event from a topic, this function returns None.
        is_topic() should be used first to determine if this was a topic trigger.
        """
        if not self.is_topic():
            return None

        return self.context


@dataclass(order=True)
class Response(object):
    """Nitric Function as a Service (FaaS) response class."""

    context: ResponseContext
    data: bytes = field(default_factory=bytes)

    def to_grpc_trigger_response_context(self) -> TriggerResponse:
        """Translate a response object ready for on the wire transport."""
        response = TriggerResponse(data=self.data)

        if self.context.is_http():
            ctx = self.context.as_http()
            response.http = ctx.to_grpc_http_response_context()
        elif self.context.is_topic():
            ctx = self.context.as_topic()
            response.topic = ctx.to_grpc_topic_response_context()

        return response
