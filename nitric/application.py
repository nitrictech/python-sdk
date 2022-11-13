import asyncio
from nitric.faas import FunctionServer

# from nitric.resources.base import BaseResource
from typing import Dict, List, Type, Any, TypeVar


BT = TypeVar("BT")


class Nitric:
    """Represents a nitric app."""

    _workers: List[FunctionServer] = []
    _cache: Dict[str, Dict[str, Any]] = {
        "api": {},
        "bucket": {},
        "topic": {},
        "secret": {},
        "queue": {},
        "collection": {},
    }

    @classmethod
    def _register_worker(cls, srv: FunctionServer):
        """Register a worker for this application."""
        cls._workers.append(srv)

    @classmethod
    def _create_resource(cls, resource: Type[BT], name: str, *args, **kwargs) -> BT:
        resource_type = resource.__name__.lower()
        if cls._cache.get(resource_type).get(name) is None:
            cls._cache[resource_type][name] = resource.make(name, *args, **kwargs)

        return cls._cache[resource_type][name]

    @classmethod
    def run(cls):
        """
        Start the nitric application.

        This will execute in an existing event loop if there is one, otherwise it will attempt to create its own.
        """
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()

            loop.run_until_complete(asyncio.gather(*[wkr.start() for wkr in cls._workers]))
        except KeyboardInterrupt:
            print("\nexiting")
