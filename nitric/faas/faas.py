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
import json
import traceback
from typing import Callable, Union, Coroutine, Any

import betterproto
from betterproto.grpc.util.async_channel import AsyncChannel

from nitric.utils import new_default_channel
from nitric.faas import Trigger, Response
from nitric.proto.nitric.faas.v1 import FaasServiceStub, InitRequest, ClientMessage
import asyncio


async def _register_faas_worker(
    func: Callable[
        [Trigger],
        Union[
            Coroutine[Any, Any, Union[Response, None, dict, list, set, bytes]],
            Union[Response, None, dict, list, set, bytes],
        ],
    ]
):
    """
    Register a new FaaS worker with the Membrane, using the provided function as the handler.

    :param func: handler function for incoming triggers. Can be sync or async, async is preferred.
    """
    channel = new_default_channel()
    client = FaasServiceStub(channel)
    request_channel = AsyncChannel(close=True)
    # We can start be sending all the requests we already have
    try:
        await request_channel.send(ClientMessage(init_request=InitRequest()))
        async for srv_msg in client.trigger_stream(request_channel):
            # The response iterator will remain active until the connection is closed
            msg_type, val = betterproto.which_one_of(srv_msg, "content")

            if msg_type == "init_response":
                print("function connected to Membrane")
                # We don't need to reply
                # proceed to the next available message
                continue
            if msg_type == "trigger_request":
                trigger = Trigger.from_trigger_request(srv_msg.trigger_request)
                try:
                    response = (await func(trigger)) if asyncio.iscoroutinefunction(func) else func(trigger)
                except Exception:
                    print("Error calling handler function")
                    traceback.print_exc()
                    response = trigger.default_response()
                    if response.context.is_http():
                        response.context.as_http().status = 500
                    else:
                        response.context.as_topic().success = False

                # Handle lite responses with just data, assume a success in these cases
                if not isinstance(response, Response):
                    full_response = trigger.default_response()
                    # don't modify bytes responses
                    if isinstance(response, bytes):
                        full_response.data = response
                    # convert dict responses to JSON
                    elif isinstance(response, (dict, list, set)):
                        full_response.data = bytes(json.dumps(response), "utf-8")
                        if full_response.context.is_http():
                            full_response.context.as_http().headers["Content-Type"] = "application/json"
                    # convert anything else to a string
                    # TODO: this might not always be safe. investigate alternatives
                    else:
                        full_response.data = bytes(str(response), "utf-8")
                    response = full_response

                # Send function response back to server
                await request_channel.send(
                    ClientMessage(id=srv_msg.id, trigger_response=response.to_grpc_trigger_response_context())
                )
            else:
                print("unhandled message type {0}, skipping".format(msg_type))
                continue
            if request_channel.done():
                break
    except ConnectionRefusedError as cre:
        traceback.print_exc()
        raise ConnectionRefusedError("Failed to register function with Membrane") from cre
    except Exception as e:
        traceback.print_exc()
        raise Exception("An unexpected error occurred.") from e
    finally:
        print("stream from Membrane closed, closing client stream")
        # The channel must be closed to complete the gRPC connection
        request_channel.close()
        channel.close()


def start(handler: Callable[[Trigger], Coroutine[Any, Any, Union[Response, None, dict, list, set, bytes]]]):
    """
    Register the provided function as the trigger handler and starts handling new trigger requests.

    :param handler: handler function for incoming triggers. Can be sync or async, async is preferred.
    """
    asyncio.run(_register_faas_worker(handler))
