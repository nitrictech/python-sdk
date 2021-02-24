from typing import List

from nitric.proto import event_service
from nitric.proto.v1.events_pb2 import TopicListResponse
from nitric.sdk.v1._base_client import BaseClient
from nitric.sdk.v1.models import Topic


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
        response: TopicListResponse = self._exec("List")
        topics = [Topic(name=topic.name) for topic in response.topics]
        return topics
