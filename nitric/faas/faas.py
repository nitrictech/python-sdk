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

from nitric.config import settings
from nitric.faas import TriggerRequest, Response
from grpc import aio

from nitric.faas.trigger import Trigger
from nitric.proto.faas.v1 import faas_pb2, faas_pb2_grpc

import asyncio


def get_stream(stub: faas_pb2_grpc.FaasStub) -> aio.StreamStreamCall[faas_pb2.ClientMessage, faas_pb2.ServerMessage]:
    return stub.TriggerStream()


async def loop(func: Union[Callable[[TriggerRequest], Union[Response, str]]]):
    """FaaS loop"""
    async with aio.insecure_channel(settings.SERVICE_BIND) as channel:
        stub = faas_pb2_grpc.FaasStub(channel)
        stream = get_stream(stub)

        # Let the server know we're ready to work
        await stream.write(faas_pb2.ClientMessage(init_request=faas_pb2.InitRequest()))

        # Infinite loop
        while 1:
            # Receive a message, will block until a message is available
            # This can be one of ServerMessage of EOFType
            # If its an EOFType we may terminate the stream
            # Otherwise we keep running
            msg = await stream.read()

            # EOF we can exit now
            if msg is None:
                # Break the loop
                break

            if msg.HasField("init_response"):
                # Handle the init response
                print("Function connected to Membrane")
                # We don't need to reply
                # Time to go to the next available message
                continue
            elif msg.HasField("trigger_request"):
                client_msg = faas_pb2.ClientMessage(
                    id=msg.id,
                )

                trigger = Trigger.from_trigger_request(trigger_request=msg.trigger_request)
                # Invoke the handler here
                try:
                    # FIXME: Await the function as an async function
                    # This will allow the user to define non-blocking I/O within the scope
                    # of their function allowing the runtime to queue up more requests
                    if asyncio.iscoroutinefunction(func):
                        print("call non-blocking")
                        response = await func(trigger)
                    else:
                        response = func(trigger)
                        print("call blocking")

                    if isinstance(response, Response):
                        client_msg.trigger_response.CopyFrom(response.to_grpc_trigger_response_context())
                    elif isinstance(response, str):
                        # Construct a default response from the data
                        default_response = trigger.default_response()
                        default_response.data = response.encode()
                        client_msg.trigger_response.CopyFrom(default_response.to_grpc_trigger_response_context())

                    # translate the response
                except Exception:
                    # Handle the exception here
                    # write an exception back to the server
                    default_response = trigger.default_response()
                    default_response.data = "Internal Error".encode()
                    if default_response.context.is_http():
                        http_context = default_response.context.as_http()
                        http_context.status = 500
                        http_context.headers = {"Content-Type": "text/plain"}
                    elif default_response.context.is_topic():
                        topic_context = default_response.context.as_topic()
                        topic_context.success = False

                    client_msg.trigger_response.CopyFrom(default_response.to_grpc_trigger_response_context())

                # Write it back to the server
                await stream.write(client_msg)
                # Continue the loop

        print("Function Exiting")


# TODO: We need to change this to an Awaitable or a Coroutine
def start(func: Union[Callable[[TriggerRequest], Union[Response, str]]]):
    """
    Register the provided function as the request handler and starts handling new requests.

    :param func: to use to handle new requests
    """

    # Begin the event loop
    asyncio.run(loop(func))
