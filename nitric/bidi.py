import asyncio
from typing import Generic, TypeVar, List


T = TypeVar("T")


class AsyncNotifierList(Generic[T]):
    def __init__(self):
        self.items: List[T] = []  # type: ignore
        self.new_item_event: asyncio.Event = asyncio.Event()  # type: ignore

    async def add_item(self, item: T) -> None:
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
