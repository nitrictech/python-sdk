from typing import List
from nitric.proto import queue
from nitric.proto import queue_service
from nitric.proto import common
from nitric.sdk.v1._base_client import BaseClient
from google.protobuf.struct_pb2 import Struct
from nitric.sdk.v1.models import Event, FailedEvent, QueueItem
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

    def _evt_to_wire(self, event: Event) -> common.NitricEvent:
        """
        Convert a Nitric Event to a Nitric Queue Event.

        :param event: to convert
        :return: converted event
        """
        payload_struct = Struct()
        payload_struct.update(event.payload)

        return common.NitricEvent(
            requestId=event.request_id,
            payloadType=event.payload_type,
            payload=payload_struct,
        )

    def _wire_to_event(self, event: common.NitricEvent) -> Event:
        """
        Convert a Nitric Queue Event (protobuf) to a Nitric Event (python SDK).

        :param event: to convert
        :return: converted event
        """
        return Event(
            request_id=event.requestId,
            payload_type=event.payloadType,
            payload=MessageToDict(event.payload),
        )

    def _wire_to_queue_item(self, item: queue.NitricQueueItem) -> QueueItem:
        """
        Convert a NitricQueueItem to the Python SDK model equivalent QueueItem.

        :param item: to be converted
        :return: the converted queue item, containing the associated event
        """
        evt = self._wire_to_event(item.event)

        return QueueItem(event=evt, lease_id=item.leaseId)

    def _wire_to_failed_evt(self, failed_message: queue.FailedMessage) -> FailedEvent:
        """
        Convert a queue event that failed to push into a Failed Event object.

        :param failed_message: the failed event
        :return: the Failed Event with failure message
        """
        evt = self._wire_to_event(failed_message.event)

        return FailedEvent(event=evt, message=failed_message.message)

    def push(self, queue_name: str, events: List[Event] = None) -> PushResponse:
        """
        Publish an event/message to a topic, which can be subscribed to by other services.

        :param queue_name: the name of the queue to publish to
        :param events: The events to push to the queue
        :return: the request id on successful publish
        """
        if events is None:
            events = []
        wire_events = map(self._evt_to_wire, events)

        request = queue.PushRequest(queue=queue_name, events=wire_events)

        response: queue.PushResponse = self._exec("Push", request)

        failed_events = map(self._wire_to_failed_evt, response.failedMessages)

        return PushResponse(failed_events=list(failed_events))

    def pop(self, queue_name: str, depth: int = None) -> List[QueueItem]:
        """
        Pops 1 or more items from the specified queue up to the depth limit.

        :param queue_name: Nitric name for the queue. This will be automatically resolved to the provider specific
        identifier.
        :param depth: The maximum number of queue items to return. Default: 1, Min: 1.
        :return: Queue items popped from the specified queue.
        """
        # Set the default and minimum depth to 1.
        if depth is None or depth < 1:
            depth = 1

        request = queue.PopRequest(queue=queue_name, depth=depth)

        response: queue.PopResponse = self._exec("Pop", request)

        # Map the response protobuf response items to Python SDK Nitric Queue Items
        return [self._wire_to_queue_item(item) for item in response.items]
