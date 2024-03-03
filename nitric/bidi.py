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
import asyncio
from typing import Generic, List, TypeVar

T = TypeVar("T")


class AsyncNotifierList(Generic[T]):
    """An async iterable that notifies when new items are added."""

    def __init__(self):
        """Create a new AsyncNotifierList."""
        self.items: List[T] = []  # type: ignore
        self.new_item_event: asyncio.Event = asyncio.Event()  # type: ignore

    async def add_item(self, item: T) -> None:
        """Add a new item to the list."""
        self.items.append(item)
        self.new_item_event.set()

    def __aiter__(self):
        return self

    async def __anext__(self):
        while not self.items:
            await self.new_item_event.wait()  # Wait for an item to be added
        item = self.items.pop(0)
        if not self.items:
            self.new_item_event.clear()  # Reset the event if there are no more items
        return item
