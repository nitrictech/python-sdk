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
from typing import Callable, Union

from flask import Flask, request
from waitress import serve

from nitric.proto.faas.v1.faas_pb2 import TriggerRequest, TriggerResponse
from nitric.config import settings
from nitric.faas import Trigger, Response
from google.protobuf import json_format


def construct_request() -> TriggerRequest:
    """Construct a Nitric Request object from the Flask HTTP Request."""
    # full_path used to better match behavior in other SDKs
    # return TriggerRequest(dict(request.headers), request.get_data(), path=request.full_path)
    message = json_format.Parse(request.get_data(), TriggerRequest(), ignore_unknown_fields=False)
    return message


def http_response(response: TriggerResponse):
    """
    Return a full HTTP response tuple based on the Nitric Response contents.

    The response includes a body, status and headers as appropriate.
    """
    headers = {"Content-Type": "application/json"}

    return json_format.MessageToJson(response), 200, headers


def exception_to_html():
    """Return a traceback as HTML."""
    import traceback
    import sys
    import html

    limit = None
    exception_type, value, tb = sys.exc_info()
    trace_list = traceback.format_tb(tb, limit) + traceback.format_exception_only(exception_type, value)
    body = "Traceback:\n" + "%-20s %s" % ("".join(trace_list[:-1]), trace_list[-1])
    return (
        "<html><head><title>Error</title></head><body><h2>An Error Occurred:</h2>\n<pre>"
        + html.escape(body)
        + "</pre></body></html>\n"
    )


class Handler(object):
    """Nitric Function handler."""

    def __init__(self, func: Callable[[Trigger], Union[Response, str]]):
        """Construct a new handler using the provided function to handle new requests."""
        self.func = func

    def __call__(self, path="", *args):
        """Construct Nitric Request from HTTP Request."""
        trigger_request = construct_request()

        grpc_trigger_response: TriggerResponse

        # convert it to a trigger
        trigger = Trigger.from_trigger_request(trigger_request)

        try:
            # Execute the handler function
            response: Union[Response, str] = self.func(trigger)

            final_response: Response
            if isinstance(response, str):
                final_response = trigger.default_response()
                final_response.data = response.encode()
            elif isinstance(response, Response):
                final_response = response
            else:
                # assume None
                final_response = trigger.default_response()
                final_response.data = "".encode()

            grpc_trigger_response = final_response.to_grpc_trigger_response_context()

        except Exception:
            trigger_response = trigger.default_response()
            if trigger_response.context.is_http():
                trigger_response.context.as_http().status = 500
                trigger_response.context.as_http().headers = {"Content-Type": "text/html"}
                trigger_response.data = exception_to_html().encode()
            elif trigger_response.context.is_topic():
                trigger_response.data = "Error processing message"
                trigger_response.context.as_topic().success = False

            grpc_trigger_response = trigger_response.to_grpc_trigger_response_context()

        return http_response(grpc_trigger_response)


def start(func: Callable[[Trigger], Union[Response, str]]):
    """
    Register the provided function as the request handler and starts handling new requests.

    :param func: to use to handle new requests
    """
    app = Flask(__name__)
    app.add_url_rule("/", "index", Handler(func), methods=["GET", "PUT", "POST", "PATCH", "DELETE"])
    app.add_url_rule(
        "/<path:path>",
        "path",
        Handler(func),
        methods=["GET", "PUT", "POST", "PATCH", "DELETE"],
    )

    host, port = f"{settings.CHILD_ADDRESS}".split(":")
    # Start the function HTTP server
    serve(app, host=host, port=int(port))
