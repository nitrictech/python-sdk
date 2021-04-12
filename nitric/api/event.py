from typing import List

from nitric.proto import event as event_model, event
from nitric.proto import event_service
from nitric.proto.event.v1.event_pb2 import NitricEvent
from nitric.api._base_client import BaseClient
from google.protobuf.struct_pb2 import Struct

from nitric.api.models import Topic


class EventClient(BaseClient):
    """
    Nitric generic publish/subscribe event client.

    This client insulates application code from stack specific event operations or SDKs.
    """

    def __init__(self):
        """Construct a Nitric Event Client."""
        super(self.__class__, self).__init__()
        self._stub = event_service.EventStub(self._channel)

    def publish(
        self,
        topic_name: str,
        payload: dict = None,
        payload_type: str = "",
        event_id: str = None,
    ) -> str:
        """
        Publish an event/message to a topic, which can be subscribed to by other services.

        :param topic_name: the name of the topic to publish to
        :param payload: content of the message to send
        :param payload_type: fully qualified name of the event payload type, e.g. io.nitric.example.customer.created
        :param event_id: a unique id, used to ensure idempotent processing of events. Defaults to a version 4 UUID.
        :return: the request id on successful publish
        """
        if payload is None:
            payload = {}
        payload_struct = Struct()
        payload_struct.update(payload)
        nitric_event = NitricEvent(id=event_id, payloadType=payload_type, payload=payload_struct)
        request = event_model.EventPublishRequest(topic=topic_name, event=nitric_event)
        self._exec("Publish", request)
        return event_id


class TopicClient(BaseClient):
    """
    Nitric generic event topic client.

    This client insulates application code from stack specific topic operations or SDKs.
    """

    def __init__(self):
        """Construct a Nitric Topic Client."""
        super(self.__class__, self).__init__()
        self._stub = event_service.TopicStub(self._channel)

    def get_topics(self) -> List[Topic]:
        """Get a list of topics available for publishing or subscription."""
        response: event.TopicListResponse = self._exec("List")
        topics = [Topic(name=topic.name) for topic in response.topics]
        return topics
