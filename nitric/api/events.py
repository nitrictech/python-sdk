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

from typing import List, Union

from grpclib import GRPCError

from nitric.api.exception import exception_from_grpc_error
from nitric.utils import new_default_channel, _struct_from_dict
from nitricapi.nitric.event.v1 import EventServiceStub, NitricEvent, TopicServiceStub
from dataclasses import dataclass, field


@dataclass(frozen=True, order=True)
class Event(object):
    """Eventing client, providing access to Topic and Event references and operations on those entities."""

    payload: dict = field(default_factory=dict)
    id: str = field(default=None)
    payload_type: str = field(default=None)


def _event_to_wire(event: Event) -> NitricEvent:
    return NitricEvent(
        id=event.id,
        payload=_struct_from_dict(event.payload),
        payload_type=event.payload_type,
    )


@dataclass(frozen=True, order=True)
class Topic(object):
    """A reference to a topic on an event service, used to perform operations on that topic."""

    _events: Events
    name: str

    async def publish(
        self,
        event: Union[Event, dict] = None,
    ) -> Event:
        """
        Publish an event/message to a topic, which can be subscribed to by other services.

        :param event: the event to publish
        :return: the published event, with the id added if one was auto-generated
        """
        if event is None:
            event = Event()

        if isinstance(event, dict):
            # TODO: handle events that are just a payload
            event = Event(**event)

        try:
            response = await self._events._stub.publish(topic=self.name, event=_event_to_wire(event))
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
        self.channel = new_default_channel()
        self._stub = EventServiceStub(channel=self.channel)
        self._topic_stub = TopicServiceStub(channel=self.channel)

    def __del__(self):
        # close the channel when this client is destroyed
        if self.channel is not None:
            self.channel.close()

    async def topics(self) -> List[Topic]:
        """Get a list of topics available for publishing or subscription."""
        try:
            response = await self._topic_stub.list()
            return [self.topic(topic.name) for topic in response.topics]
        except GRPCError as grpc_err:
            raise exception_from_grpc_error(grpc_err)

    def topic(self, name: str) -> Topic:
        """Return a reference to a topic."""
        return Topic(_events=self, name=name)
