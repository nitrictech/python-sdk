from typing import List
from nitric.proto import queue
from nitric.proto import queue_service
from nitric.sdk.v1._base_client import BaseClient
from google.protobuf.struct_pb2 import Struct
from nitric.sdk.v1.models import Event, FailedEvent
from google.protobuf.json_format import MessageToDict


class PushResponse(object):
    """Represents the result of a Queue Push."""

    def __init__(self, failed_events: List[FailedEvent]):
        """Construct a Push Response."""
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

    def evt_to_wire(self, event: Event) -> queue.NitricEvent:
        """
        Convert a Nitric Event to a Nitric Queue Event.

        :param event: to convert
        :return: converted event
        """
        payload_struct = Struct()
        payload_struct.update(event.payload)

        return queue.NitricEvent(
            requestId=event.request_id,
            payloadType=event.payload_type,
            payload=payload_struct,
        )

    def wire_to_failed_evt(self, event: queue.FailedMessage) -> FailedEvent:
        """
        Convert a queue event that failed to push into a Failed Event object.

        :param event: the failed event
        :return: the Failed Event with failure message
        """
        tmp_evt = event.event
        tmp_msg = event.message

        evt = Event(
            request_id=tmp_evt.request_id,
            payload_type=tmp_evt.payload_type,
            payload=MessageToDict(tmp_evt.payload),
        )

        return FailedEvent(event=evt, message=tmp_msg)

    def push(self, queue_name: str, events: List[Event] = None) -> PushResponse:
        """
        Publish an event/message to a topic, which can be subscribed to by other services.

        :param queue_name: the name of the queue to publish to
        :param events: The events to push to the queue
        :return: the request id on successful publish
        """
        if events is None:
            events = []
        wire_events = map(self.evt_to_wire, events)

        request = queue.PushRequest(queue=queue_name, events=wire_events)

        response: queue.PushResponse = self._exec("Push", request)

        failed_events = map(self.wire_to_failed_evt, response.failedMessages)

        return PushResponse(failed_events=list(failed_events))
