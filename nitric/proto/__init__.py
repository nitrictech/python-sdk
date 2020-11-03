from nitric.proto.v1 import eventing_pb2 as eventing
from nitric.proto.v1 import eventing_pb2_grpc as eventing_service
from nitric.proto.v1 import storage_pb2 as storage
from nitric.proto.v1 import storage_pb2_grpc as storage_service

__all__ = [
    'eventing',
    'eventing_service',
    'storage',
    'storage_service'
]