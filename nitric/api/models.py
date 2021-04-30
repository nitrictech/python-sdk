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


class Topic(object):
    """Represents event topic metadata."""

    def __init__(self, name: str):
        """Construct a new topic instance."""
        self.name = name


class Event(object):
    """Represents a NitricEvent."""

    def __init__(self, event_id: str, payload_type: str, payload: dict):
        """Construct a new Event."""
        self.event_id = event_id
        self.payload_type = payload_type
        self.payload = payload


class Task(object):
    """Represents a NitricTask."""

    def __init__(self, task_id: str, payload_type: str, payload: dict, lease_id: str = None):
        """Construct a new Task."""
        self.task_id = task_id
        self.payload_type = payload_type
        self.payload = payload
        self.lease_id = lease_id


class FailedTask(Task):
    """Represents a failed queue publish for an event."""

    def __init__(self, task: Task, message: str):
        """Construct a new Failed Event."""
        super().__init__(task.task_id, task.payload_type, task.payload, task.lease_id)
        self.message = message
