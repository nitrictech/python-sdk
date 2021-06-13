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
from typing import Union, Dict
from nitric.proto.faas.v1.faas_pb2 import TriggerResponse, HttpResponseContext, TopicResponseContext


class TopicResponseContext(object):
    def __init__(self, success: bool = True):
        self.success = success

    def to_grpc_topic_response_context(self) -> TopicResponseContext:
        return TopicResponseContext(success=self.success)


class HttpResponseContext(object):
    def __init__(self, headers: Dict[str, str] = {}, status: int = 200):
        self.headers = headers
        self.status = status

    def to_grpc_http_response_context(self) -> HttpResponseContext:
        return HttpResponseContext(headers=self.headers, status=self.status)


class ResponseContext(object):
    def __init__(self, context: Union[TopicResponseContext, HttpResponseContext]):
        self.context = context

    def is_http(self):
        return isinstance(self.context, HttpResponseContext)

    def is_topic(self):
        return isinstance(self.context, TopicResponseContext)

    def as_http(self) -> Union[HttpResponseContext, None]:
        if not self.is_http():
            return None

        return self.context

    def as_topic(self) -> Union[TopicResponseContext, None]:
        """Determine is ResponseContext is for a topic"""
        if not self.is_topic():
            return None

        return self.context


class Response(object):
    """Nitric Function as a Service (FaaS) response class."""

    def __init__(
        self,
        context: ResponseContext,
        data: Union[bytes] = None,
    ):
        """Construct a new Nitric Response."""
        # FIXME: Fix typing of the status parameter, add tests
        self.context = context
        self.data = data

    def to_grpc_trigger_response_context(self) -> TriggerResponse:
        """Translate a response object ready for on the wire transport"""

        response = TriggerResponse(data=self.data)

        if self.context.is_http():
            ctx = self.context.as_http()
            response.http = ctx.to_grpc_http_response_context()
        elif self.context.is_topic():
            ctx = self.context.as_topic()
            response.topic = ctx.to_grpc_topic_response_context()

        return response
