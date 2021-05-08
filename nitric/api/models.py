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
from dataclasses import dataclass, field


@dataclass(frozen=True, order=True)
class Topic(object):
    """Represents event topic metadata."""

    name: str


@dataclass(frozen=True, order=True)
class Event(object):
    """Represents a NitricEvent."""

    event_id: str
    payload_type: str
    payload: dict


@dataclass(frozen=True, order=True)
class Task(object):
    """Represents a NitricTask."""

    task_id: str
    payload_type: str
    payload: dict
    lease_id: str = field(default=None)


@dataclass(frozen=True, order=True)
class FailedTask(Task):
    """Represents a failed queue publish for an event."""

    message: str = field(default="")
