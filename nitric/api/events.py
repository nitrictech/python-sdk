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
from typing import List, Union
from nitric.api._utils import new_default_channel
from nitric.proto.nitric.event.v1 import EventStub, NitricEvent, TopicStub
from betterproto.lib.google.protobuf import Struct
from dataclasses import dataclass, field


@dataclass(frozen=True, order=True)
class Topic(object):
    """Represents event topic metadata."""

    name: str


@dataclass(frozen=True, order=True)
class Event(object):
    """Represents a NitricEvent."""

    payload: dict = field(default_factory=dict)
    id: str = ""
    payload_type: str = ""


def _event_to_wire(event: Event) -> NitricEvent:
    return NitricEvent(
        id=event.id,
        payload=Struct().from_dict(event.payload),
        payload_type=event.payload_type,
    )


class EventClient(object):
    """
    Nitric generic publish/subscribe event client.

    This client insulates application code from stack specific event operations or SDKs.
    """

    def __init__(self, topic: str):
        """Construct a Nitric Event Client."""
        self.topic = topic
        self._stub = EventStub(channel=new_default_channel())

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
            event = Event(**event)

        response = await self._stub.publish(topic=self.topic, event=_event_to_wire(event))
        return Event(**{**event.__dict__.copy(), **{"id": response.id}})


class TopicClient(object):
    """
    Nitric generic event topic client.

    This client insulates application code from stack specific topic operations or SDKs.
    """

    def __init__(self):
        """Construct a Nitric Topic Client."""
        self._stub = TopicStub(channel=new_default_channel())

    async def get_topics(self) -> List[Topic]:
        """Get a list of topics available for publishing or subscription."""
        response = await self._stub.list()
        return [Topic(name=topic.name) for topic in response.topics]
