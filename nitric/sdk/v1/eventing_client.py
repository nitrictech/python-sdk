from nitric.proto import eventing
from nitric.proto import eventing_service
from nitric.sdk.v1._base_client import BaseClient


class EventingClient(BaseClient):

    def __init__(self):
        super(self.__class__, self).__init__()
        self._stub = eventing_service.EventingStub(self._channel)

    def get_topics(self):
        response = self._stub.GetTopics()
        return response

    def publish(self, topic_name: str, message: str):
        # FIXME: Think about a smarter way to define the params
        # api_v1._PUBLISHREQUEST.fields
        response = self._stub.Publish(eventing.PublishRequest(topic_name, message))
        return response
