from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

from typing import TypeVar, Type, Coroutine, Union

T = TypeVar("T", bound="BaseResource")


class BaseResource(ABC):
    """A base resource class with common functionality."""

    cache = {}

    def __init__(self):
        """Construct a new resource."""
        self._reg: Union[Coroutine, None] = None

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
        r._reg = r._register()
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(r._reg)
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(r._reg)

        return r
