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

from typing import Any, Union

from grpclib import GRPCError

from nitric.exception import exception_from_grpc_error
from grpclib.client import Channel
from nitric.utils import new_default_channel, struct_from_dict
from nitric.proto.topics.v1 import TopicsStub, TopicPublishRequest, Message
from dataclasses import dataclass, field


@dataclass(frozen=True, order=True)
class Event(object):
    """Eventing client, providing access to Topic and Event references and operations on those entities."""

    payload: dict[str, Any] = field(default_factory=dict)


def _event_to_wire(event: Event) -> Message:
    return Message(struct_payload=struct_from_dict(event.payload))


@dataclass(frozen=True, order=True)
class TopicRef(object):
    """A reference to a topic on an event service, used to perform operations on that topic."""

    _events: Events
    name: str

    async def publish(
        self,
        event: Union[Event, dict[str, Any]],
    ) -> Event:
        """
        Publish an event/message to a topic, which can be subscribed to by other services.

        :param event: the event to publish
        :return: the published event, with the id added if one was auto-generated
        """
        if isinstance(event, dict):
            event = Event(payload=event)

        try:
            response = await self._events.topics_stub.publish(
                topic_publish_request=TopicPublishRequest(topic_name=self.name, message=_event_to_wire(event))
            )
            return Event(**{**event.__dict__.copy(), **{"id": response.id}})
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)


class Events(object):
    """
    Nitric generic publish/subscribe event client.

    This client insulates application code from stack specific event operations or SDKs.
    """

    def __init__(self):
        """Construct a Nitric Event Client."""
        self.channel: Union[Channel, None] = new_default_channel()
        self.topics_stub = TopicsStub(channel=self.channel)

    def __del__(self):
        # close the channel when this client is destroyed
        if self.channel is not None:
            self.channel.close()

    def topic(self, name: str) -> TopicRef:
        """Return a reference to a topic."""
        return TopicRef(_events=self, name=name)
