from grpc._channel import _InactiveRpcError, _UnaryUnaryMultiCallable

from nitric.proto import eventing
from nitric.proto import eventing_service
from nitric.sdk.v1._base_client import BaseClient
from google.protobuf.struct_pb2 import Struct


class EventingClient(BaseClient):

    def __init__(self):
        super(self.__class__, self).__init__()
        self._stub = eventing_service.EventingStub(self._channel)

    def get_topics(self):
        return self._exec('GetTopics')

    def publish(self, topic_name: str, message: dict):
        # FIXME: Think about a smarter way to define the params
        # api_v1._PUBLISHREQUEST.fields
        message_struct = Struct()
        message_struct.update(message)
        request = eventing.PublishRequest(topicName=topic_name, message=message_struct)
        return self._exec('Publish', request)
