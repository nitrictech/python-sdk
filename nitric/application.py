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
from os import getenv, environ

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient

from nitric.faas import FunctionServer
from nitric.api.exception import NitricUnavailableException

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
        try:
            resource_type = resource.__name__.lower()
            if cls._cache.get(resource_type).get(name) is None:
                cls._cache[resource_type][name] = resource.make(name, *args, **kwargs)

            return cls._cache[resource_type][name]
        except ConnectionRefusedError:
            raise NitricUnavailableException(
                'Unable to connect to a nitric server! If you\'re running locally make sure to run "nitric start"'
            )

    @classmethod
    def _create_tracer(cls, local: bool = True, sampler: int = 100) -> TracerProvider:
        local_run = local or "OTELCOL_BIN" not in environ
        samplePercent = int(getenv("NITRIC_TRACE_SAMPLE_PERCENT", sampler)) / 100.0

        # If its a local run use a console exporter, otherwise export using OTEL Protocol
        exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
        if local_run:
            exporter = ConsoleSpanExporter()

        provider = TracerProvider(
            active_span_processor=BatchSpanProcessor(exporter),
            sampler=sampling.TraceIdRatioBased(samplePercent),
        )
        trace.set_tracer_provider(provider)

        grpc_client_instrumentor = GrpcInstrumentorClient()
        grpc_client_instrumentor.instrument()

        return provider

    @classmethod
    def run(cls):
        """
        Start the nitric application.

        This will execute in an existing event loop if there is one, otherwise it will attempt to create its own.
        """
        provider = cls._create_tracer()
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
            )
        finally:
            if provider is not None:
                provider.force_flush()
