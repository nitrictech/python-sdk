from nitric.proto.v1 import auth_pb2 as auth
from nitric.proto.v1 import auth_pb2_grpc as auth_service
from nitric.proto.v1 import events_pb2 as events
from nitric.proto.v1 import events_pb2_grpc as event_service
from nitric.proto.v1 import storage_pb2 as storage
from nitric.proto.v1 import storage_pb2_grpc as storage_service
from nitric.proto.v1 import documents_pb2 as documents
from nitric.proto.v1 import documents_pb2_grpc as documents_service
from nitric.proto.v1 import queues_pb2 as queue
from nitric.proto.v1 import queues_pb2_grpc as queue_service
from nitric.proto.v1 import common_pb2 as common

__all__ = [
    "auth",
    "auth_service",
    "events",
    "event_service",
    "storage",
    "storage_service",
    "documents",
    "documents_service",
    "queue",
    "queue_service",
    "common",
]
