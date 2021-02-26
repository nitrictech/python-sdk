from nitric.proto import events
from nitric.proto import event_service
from nitric.sdk.v1._base_client import BaseClient
from google.protobuf.struct_pb2 import Struct
from nitric.proto.v1.common_pb2 import NitricEvent
import uuid


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
        payload_type: str = "none",
        request_id: str = None,
    ) -> str:
        """
        Publish an event/message to a topic, which can be subscribed to by other services.

        :param topic_name: the name of the topic to publish to
        :param payload: content of the message to send
        :param payload_type: fully qualified name of the event payload type, e.g. io.nitric.example.customer.created
        :param request_id: a unique id, used to ensure idempotent processing of events. Defaults to a version 4 UUID.
        :return: the request id on successful publish
        """
        # FIXME: Think about a smarter way to define the params
        # api_v1._PUBLISHREQUEST.fields
        if payload is None:
            payload = {}
        if request_id is None:
            request_id = str(uuid.uuid4())
        payload_struct = Struct()
        payload_struct.update(payload)
        event = NitricEvent(
            requestId=request_id, payloadType=payload_type, payload=payload_struct
        )
        request = events.EventPublishRequest(topic=topic_name, event=event)
        self._exec("Publish", request)
        return request_id
