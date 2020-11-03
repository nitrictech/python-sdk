from abc import ABC
import grpc
from nitric.config import settings
from nitric.proto import api_service_v1


class BaseClient(ABC):

    def __init__(self):
        ambassador_bind = f"{settings.AMBASSADOR_ADDRESS}:{settings.AMBASSADOR_PORT}"
        # TODO: handle other channel types
        self._channel = grpc.insecure_channel(ambassador_bind)
