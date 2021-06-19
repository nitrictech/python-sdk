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

from nitric.proto.faas.v1.faas_pb2 import TriggerRequest

from nitric.faas.response import Response, TopicResponseContext, HttpResponseContext, ResponseContext


class HttpTriggerContext(object):
    """Represents Trigger metadata from a HTTP subscription."""

    def __init__(
        self,
        method: str,
        path: str,
        headers: typing.Dict[str, str],
        query_params: typing.Dict[str, str],
    ):
        """Create a Http trigger context."""
        self.method = method
        self.path = path
        self.headers = headers
        self.query_params = query_params


class TopicTriggerContext(object):
    """Represents Trigger metadata from a topic subscription."""

    def __init__(self, topic: str):
        """Create a Topic trigger context."""
        self.topic = topic


class TriggerContext(object):
    """Represents the contextual metadata for a Nitric function request."""

    def __init__(self, context: typing.Union[TopicTriggerContext, HttpTriggerContext]):
        """Construct a Nitric Trigger Context."""
        self.context = context

    def is_http(self) -> bool:
        """
        Determine if trigger was raised by a http request.

        :return true if trigger was raised by a HTTP request
        """
        return isinstance(self.context, HttpTriggerContext)

    def as_http(self) -> typing.Union[HttpTriggerContext, None]:
        """
        Unwrap HttpTriggerContext.

        :return HttpTriggerContext if is_http is true otherwise None
        """
        if not self.is_http():
            return None

        return self.context

    def is_topic(self) -> bool:
        """
        Determine if trigger was raised by a topic event.

        :return true if trigger is for a topic event
        """
        return isinstance(self.context, TriggerContext)

    def as_topic(self) -> typing.Union[TopicTriggerContext, None]:
        """
        Unwrap TopicTriggerContext.

        :return TopicTriggerContext if is_topic is true otherwise None
        """
        if not self.is_topic():
            return None

        return self.context

    @staticmethod
    def from_trigger_request(trigger_request: TriggerRequest):
        """
        Create a TriggerContext from a gRPC TriggerRequest.

        :return Created TriggerContext
        """
        if trigger_request.http is not None:
            return TriggerContext(
                context=HttpTriggerContext(
                    headers=dict(trigger_request.http.headers),
                    path=trigger_request.http.path,
                    method=trigger_request.http.method,
                    query_params=dict(trigger_request.http.query_params),
                )
            )
        elif trigger_request.topic is not None:
            return TriggerContext(context=TopicTriggerContext(topic=trigger_request.topic.topic))
        else:
            # We have an error
            # should probably raise an exception
            return None


class Trigger(object):
    """
    Represents a standard Nitric function request.

    These requests are normalized from their original stack-specific structures.
    """

    def __init__(self, context: TriggerContext, data: bytes):
        """Construct a Nitric Function Request."""
        self.context = context
        self.data = data

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
        Create a relevant default response.

        The returned response can be interrogated with its context to determine the appropriate
        response context e.g. response.context.is_http() or response.context.is_topic().

        :returns Default response for this Trigger
        """
        response_ctx = None

        if self.context.is_http():
            response_ctx = ResponseContext(context=HttpResponseContext())
        elif self.context.is_topic():
            response_ctx = ResponseContext(context=TopicResponseContext())

        return Response(data=None, context=response_ctx)

    @staticmethod
    def from_trigger_request(trigger_request: TriggerRequest):
        """
        Create a Trigger from a gRPC TriggerRequest.

        :returns Created Trigger
        """
        context = TriggerContext.from_trigger_request(trigger_request)

        return Trigger(context=context, data=trigger_request.data)
