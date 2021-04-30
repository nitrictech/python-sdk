#
# Copyright (c) 2021 Nitric Technologies Pty Ltd.
#
# This file is part of Nitric Python 3 SDK.
# See https://github.com/nitrictech/python-sdk for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from nitric.proto.event.v1 import event_pb2 as event
from nitric.proto.event.v1 import event_pb2_grpc as event_service
from nitric.proto.storage.v1 import storage_pb2 as storage
from nitric.proto.storage.v1 import storage_pb2_grpc as storage_service
from nitric.proto.kv.v1 import kv_pb2 as key_value
from nitric.proto.kv.v1 import kv_pb2_grpc as key_value_service
from nitric.proto.queue.v1 import queue_pb2 as queue
from nitric.proto.queue.v1 import queue_pb2_grpc as queue_service

__all__ = [
    "event",
    "event_service",
    "storage",
    "storage_service",
    "key_value",
    "key_value_service",
    "queue",
    "queue_service",
]
