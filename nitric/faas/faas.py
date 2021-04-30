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

from flask import Flask, request, jsonify
from waitress import serve

from nitric.config import settings
from nitric.faas import Request, Response


def construct_request() -> Request:
    """Construct a Nitric Request object from the Flask HTTP Request."""
    # full_path used to better match behavior in other SDKs
    return Request(dict(request.headers), request.get_data(), path=request.full_path)


def format_status(response: Response) -> int:
    """Return a HTTP status code int from the status of a Nitric Response object."""
    if response.status is None:
        return 200
    try:
        return int(response.status)
    except Exception:
        raise Exception("Invalid response status [{0}], status must an int.".format(response.status))


def format_body(response: Response):
    """
    Return a response for Flask which is a str or bytes, based on the contents of the Nitric Response body.

    str and bytes objects are unchanged
    dicts will be converted to a json string
    all other objects are cast to str type
    """
    if response.body is None:
        return ""
    if type(response.body) == dict:
        return jsonify(response.body)
    if type(response.body) == bytes or type(response.body) == str:
        return response.body

    return str(response.body)


def http_response(response: Union[Response, str]):
    """
    Return a full HTTP response tuple based on the Nitric Response contents.

    The response includes a body, status and headers as appropriate.
    """
    if response is None:
        return "", 200
    if isinstance(response, str):
        # Convert to Nitric Response for consistent handling
        response = Response(response)

    return format_body(response), format_status(response), response.headers


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

    def __init__(self, func: Callable[[Request], Union[Response, str]]):
        """Construct a new handler using the provided function to handle new requests."""
        self.func = func

    def __call__(self, path="", *args):
        """Construct Nitric Request from HTTP Request."""
        nitric_request = construct_request()
        try:
            # Execute the handler function
            response: Union[Response, str] = self.func(nitric_request)
        except Exception:
            # TODO: Only return error detail in debug mode.
            return exception_to_html(), 500

        return http_response(response)


def start(func: Callable[[Request], Union[Response, str]]):
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
