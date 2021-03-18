from nitric.proto.event.v1 import event_pb2 as event
from nitric.proto.event.v1 import event_pb2_grpc as event_service
from nitric.proto.storage.v1 import storage_pb2 as storage
from nitric.proto.storage.v1 import storage_pb2_grpc as storage_service
from nitric.proto.kv.v1 import kv_pb2 as key_value
from nitric.proto.kv.v1 import kv_pb2_grpc as key_value_service
from nitric.proto.queue.v1 import queue_pb2 as queue
from nitric.proto.queue.v1 import queue_pb2_grpc as queue_service
from nitric.proto.common.v1 import common_pb2 as common

__all__ = [
    "event",
    "event_service",
    "storage",
    "storage_service",
    "key_value",
    "key_value_service",
    "queue",
    "queue_service",
    "common",
]
