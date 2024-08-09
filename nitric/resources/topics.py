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

import logging
from typing import Any, Callable, List, Literal

import betterproto
import grpclib
from grpclib import GRPCError
from grpclib.client import Channel

from nitric.application import Nitric
from nitric.bidi import AsyncNotifierList
from nitric.context import EventHandler, FunctionServer, MessageContext, MessageRequest
from nitric.exception import exception_from_grpc_error
from nitric.proto.resources.v1 import Action, ResourceDeclareRequest, ResourceIdentifier, ResourceType
from nitric.proto.topics.v1 import ClientMessage, TopicMessage
from nitric.proto.topics.v1 import MessageRequest as ProtoMessageRequest
from nitric.proto.topics.v1 import MessageResponse as ProtoMessageResponse
from nitric.proto.topics.v1 import RegistrationRequest, SubscriberStub
from nitric.proto.topics.v1 import TopicPublishRequest, TopicsStub
from nitric.resources.resource import SecureResource
from nitric.utils import dict_from_struct, struct_from_dict
from nitric.channel import ChannelManager

TopicPermission = Literal["publish"]


class TopicRef:
    """A reference to a deployed topic, used to interact with the topic at runtime."""

    _channel: Channel
    _topics_stub: TopicsStub
    name: str

    def __init__(self, name: str) -> None:
        """Construct a reference to a deployed Topic."""
        self._channel: Channel = ChannelManager.get_channel()
        self._topics_stub = TopicsStub(channel=self._channel)
        self.name = name

    def __del__(self) -> None:
        # close the channel when this client is destroyed
        if self._channel is not None:
            self._channel.close()

    async def publish(
        self,
        message: dict[str, Any],
    ) -> None:
        """
        Publish a message to a topic, which can be subscribed to by other services.

        :param message: the event to publish
        :return: the published event, with the id added if one was auto-generated
        """
        if not isinstance(message, dict):
            raise ValueError("Message must be a dictionary")

        try:
            proto_message = TopicMessage(struct_payload=struct_from_dict(message))
            await self._topics_stub.publish(
                topic_publish_request=TopicPublishRequest(topic_name=self.name, message=proto_message)
            )
            return None
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err


class Topic(SecureResource):
    """A topic resource, used for asynchronous messaging between functions."""

    name: str
    actions: List[Action]

    def __init__(self, name: str) -> None:
        """Declare a new topic resourced."""
        super().__init__(name)

    async def _register(self) -> None:
        try:
            await self._resources_stub.declare(
                resource_declare_request=ResourceDeclareRequest(id=self._to_resource_id())
            )
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err) from grpc_err

    def _to_resource_id(self) -> ResourceIdentifier:
        return ResourceIdentifier(name=self.name, type=ResourceType.Topic)

    def _perms_to_actions(self, *args: TopicPermission) -> List[Action]:
        _permMap: dict[TopicPermission, List[Action]] = {"publish": [Action.TopicPublish]}

        return [action for perm in args for action in _permMap[perm]]

    def allow(self, perm: TopicPermission, *args: TopicPermission) -> TopicRef:
        """Request the specified permissions to this resource."""
        str_args = [perm] + [str(permission) for permission in args]
        self._register_policy(*str_args)

        return TopicRef(self.name)

    def subscribe(self) -> Callable[[EventHandler], None]:
        """Create and return a subscription decorator for this topic."""

        def decorator(func: EventHandler) -> None:
            Subscriber(
                topic_name=self.name,
                handler=func,
            )

        return decorator


def _message_context_from_proto(msg: ProtoMessageRequest) -> MessageContext:
    return MessageContext(
        request=MessageRequest(
            data=dict_from_struct(msg.message.struct_payload),
            topic=msg.topic_name,
        )
    )


class Subscriber(FunctionServer):
    """A handler for topic messages."""

    _handler: EventHandler
    _registration_request: RegistrationRequest
    _responses: AsyncNotifierList[ClientMessage]

    def __init__(self, topic_name: str, handler: EventHandler):
        """Construct a new WebsocketHandler."""
        self._handler = handler
        self._responses = AsyncNotifierList()
        self._registration_request = RegistrationRequest(topic_name=topic_name)

        Nitric._register_worker(self)

    async def _message_request_iterator(self):
        # Register with the server
        yield ClientMessage(registration_request=self._registration_request)
        # wait for any responses for the server and send them
        async for response in self._responses:
            yield response

    async def start(self) -> None:
        """Register this subscriber and listen for messages."""
        channel = ChannelManager.get_channel()
        server = SubscriberStub(channel=channel)

        try:
            async for server_msg in server.subscribe(self._message_request_iterator()):
                msg_type, _ = betterproto.which_one_of(server_msg, "content")

                if msg_type == "registration_response":
                    continue
                if msg_type == "message_request":
                    ctx = _message_context_from_proto(server_msg.message_request)

                    response: ClientMessage
                    try:
                        result = await self._handler(ctx)
                        ctx = result if result else ctx
                        response = ClientMessage(
                            id=server_msg.id, message_response=ProtoMessageResponse(success=ctx.res.success)
                        )
                    except Exception as e:  # pylint: disable=broad-except
                        logging.exception("An unhandled error occurred in a subscription event handler: %s", e)
                        response = ClientMessage(id=server_msg.id, message_response=ProtoMessageResponse(success=False))
                    await self._responses.add_item(response)
        except grpclib.exceptions.GRPCError as e:
            print(f"Stream terminated: {e.message}")
        except grpclib.exceptions.StreamTerminatedError:
            print("Stream from membrane closed.")
        finally:
            print("Closing client stream")
            channel.close()


def topic(name: str) -> Topic:
    """
    Create and register a topic.

    If a topic has already been registered with the same name, the original reference will be reused.
    """
    # type ignored because the create call are treated as protected.
    return Nitric._create_resource(Topic, name)  # type: ignore pylint: disable=protected-access
