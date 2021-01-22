from typing import List
from nitric.proto import queue
from nitric.proto import queue_service
from nitric.sdk.v1._base_client import BaseClient
from google.protobuf.struct_pb2 import Struct
from nitric.sdk.v1.models import Event, FailedEvent

import uuid

class PushResponse(object):
    def __init__(self, failed_events: list[FailedEvent]):
        self.failed_events = failed_events

class QueueClient(BaseClient):
    """
    Nitric generic publish/subscribe eventing client.

    This client insulates application code from stack specific event/topic operations or SDKs.
    """

    def __init__(self):
        """Construct a Nitric Event Client."""
        super(self.__class__, self).__init__()
        self._stub = queue_service.QueueStub(self._channel)

    def evt_to_wire(
        self,
        event: Event
    ) -> queue.NitricEvent:
        payload_struct = Struct()
        payload_struct.update(event.payload)

        return queue.NitricEvent(requestId=event.request_id, payloadType=event.payload_type, payload=payload_struct)

    def wire_to_failed_evt(
      self,
      event: queue.FailedMessage
    ) -> FailedEvent:
        

    def push(
        self,
        queue_name: str,
        events: list[Event] = []
    ) -> PushResponse:
        """
        Publish an event/message to a topic, which can be subscribed to by other services.

        :param queue_name: the name of the queue to publish to
        :param events: The events to push to the queue
        :return: the request id on successful publish
        """
        wire_events = map(self.evt_to_wire, events)

        request = queue.PushRequest(queue=queue_name, events=wire_events)

        response: PushResponse = self._exec("Push", request)
        
        return PushResponse(failed_events)