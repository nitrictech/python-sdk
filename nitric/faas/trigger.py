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
import typing
from dataclasses import dataclass, field

import betterproto

from nitric.proto.nitric.faas.v1 import TriggerRequest
from nitric.faas.response import Response, TopicResponseContext, HttpResponseContext, ResponseContext


@dataclass(order=True)
class HttpTriggerContext(object):
    """Represents Trigger metadata from a HTTP subscription."""

    method: str
    path: str
    headers: typing.Dict[str, str]
    query_params: typing.Dict[str, str]


class TopicTriggerContext(object):
    """Represents Trigger metadata from a topic subscription."""

    def __init__(self, topic: str):
        """Construct a new TopicTriggerContext, including the name of the source topic for this trigger."""
        self.topic = topic


@dataclass(order=True)
class TriggerContext(object):
    """Represents the contextual metadata for a Nitric function request."""

    context: typing.Union[TopicTriggerContext, HttpTriggerContext]

    def is_http(self) -> bool:
        """
        Indicate whether the trigger was from an HTTP request.

        This indicates the availability of additional HTTP specific context such as path, query parameters and headers.
        """
        return isinstance(self.context, HttpTriggerContext)

    def as_http(self) -> typing.Union[HttpTriggerContext, None]:
        """
        Return this context as an HTTP context type.

        If the trigger wasn't an HTTP request, this function returns None.
        is_http() should be used first to determine if this was an HTTP request trigger.
        """
        if not self.is_http():
            return None

        return self.context

    def is_topic(self) -> bool:
        """
        Indicate whether the trigger was from a topic (event).

        This indicates the availability of additional topic/event specific context such as the topic name.
        """
        return isinstance(self.context, TopicTriggerContext)

    def as_topic(self) -> typing.Union[TopicTriggerContext, None]:
        """
        Return this context as a topic context type.

        If the trigger wasn't an event from a topic, this function returns None.
        is_topic() should be used first to determine if this was a topic trigger.
        """
        if not self.is_topic():
            return None

        return self.context

    @staticmethod
    def from_trigger_request(trigger_request: TriggerRequest):
        """Return a TriggerContext from a TriggerRequest."""
        context_type, context = betterproto.which_one_of(trigger_request, "context")
        if context_type == "http":
            return TriggerContext(
                context=HttpTriggerContext(
                    headers=trigger_request.http.headers,
                    method=trigger_request.http.method,
                    query_params=trigger_request.http.query_params,
                    path=trigger_request.http.path,
                )
            )
        elif context_type == "topic":
            return TriggerContext(context=TopicTriggerContext(topic=trigger_request.topic.topic))
        else:
            print("Trigger with unknown context received, context type: {0}".format(context_type))
            raise Exception("Unknown trigger context, type: {0}".format(context_type))


def _clean_header(header_name: str):
    """Convert a Nitric HTTP request header name into the equivalent Context property name."""
    return header_name.lower().replace("x-nitric-", "").replace("-", "_")


@dataclass(order=True)
class Trigger(object):
    """
    Represents a standard Nitric function request.

    These requests are normalized from their original stack-specific structures.
    """

    context: TriggerContext
    data: bytes = field(default_factory=bytes)

    def get_body(self) -> bytes:
        """Return the bytes of the body of the request."""
        return self.data

    def get_object(self) -> dict:
        """
        Assume the payload is JSON and return the content deserialized into a dictionary.

        :raises JSONDecodeError: raised when the request payload (body) is not valid JSON.

        :return: the deserialized JSON request body as a dictionary
        """
        import json

        return json.loads(self.data)

    def default_response(self) -> Response:
        """
        Return the trigger response, based on the trigger context type.

        The returned response can be interrogated with its context to determine the appropriate
        response context e.g. response.context.is_http() or response.context.is_topic().
        """
        response_ctx = None

        if self.context.is_http():
            response_ctx = ResponseContext(context=HttpResponseContext())
        elif self.context.is_topic():
            response_ctx = ResponseContext(context=TopicResponseContext())

        return Response(context=response_ctx)

    @staticmethod
    def from_trigger_request(trigger_request: TriggerRequest):
        """Return the python SDK implementation of a Trigger from a protobuf representation."""
        context = TriggerContext.from_trigger_request(trigger_request)

        return Trigger(context=context, data=trigger_request.data)
