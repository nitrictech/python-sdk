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
from typing import Any, Dict, List, Type, TypeVar

from nitric.context import FunctionServer
from nitric.exception import NitricUnavailableException

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
        "websocket": {},
        "keyvaluestore": {},
        "oidcsecuritydefinition": {},
    }

    @classmethod
    def _register_worker(cls, srv: FunctionServer):
        """Register a worker for this application."""
        cls._workers.append(srv)

    @classmethod
    def _create_resource(cls, resource: Type[BT], name: str, *args: Any, **kwargs: Any) -> BT:
        try:
            resource_type = resource.__name__.lower()
            cached_resources = cls._cache.get(resource_type)
            if cached_resources is None or cached_resources.get(name) is None:
                cls._cache[resource_type][name] = resource.make(name, *args, **kwargs)  # type: ignore

            return cls._cache[resource_type][name]
        except ConnectionRefusedError:
            raise NitricUnavailableException(
                'Unable to connect to a nitric server! If you\'re running locally make sure to run "nitric start"'
            ) from None

    @classmethod
    def run(cls) -> None:
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
        except ConnectionRefusedError:
            raise NitricUnavailableException(
                'Unable to connect to a nitric server! If you\'re running locally make sure to run "nitric start"'
            ) from None
