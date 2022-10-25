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
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from asyncio import Task

from typing import TypeVar, Type, Coroutine, Union

T = TypeVar("T", bound="BaseResource")


class BaseResource(ABC):
    """A base resource class with common functionality."""

    cache = {}

    def __init__(self):
        """Construct a new resource."""
        self._reg: Union[Task, None] = None

    @abstractmethod
    async def _register(self):
        pass

    @classmethod
    def make(cls: Type[T], name: str) -> T:
        """
        Create and register the resource.

        The registration process for resources async, so this method should be used instead of __init__.
        """
        # Todo: store the resource reference in a cache to avoid duplicate registrations
        r = cls(name)
        try:
            loop = asyncio.get_running_loop()
            r._reg = loop.create_task(r._register())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(r._register())

        return r
