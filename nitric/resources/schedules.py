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
from nitric.application import Nitric
from nitric.faas import FunctionServer, EventMiddleware, RateWorkerOptions, Frequency


class Schedule:
    """A schedule for running functions on a cadence."""

    description: str
    server: FunctionServer

    def start(self):
        """Start the function server that executes the scheduled middleware."""
        return self.server.start()

    def __init__(self, description: str):
        """Construct a new schedule."""
        self.description = description

    def every(self, rate_description: str, *middleware: EventMiddleware):
        """
        Register middleware to be run at the specified rate.

        E.g. every("3 hours")
        """
        rate_description = rate_description.lower()

        if not any([frequency in rate_description for frequency in Frequency.as_str_list()]):
            # handle singular frequencies. e.g. every('day')
            rate_description = f"1 {rate_description}s"  # 'day' becomes '1 days'

        rate, freq_str = rate_description.split(" ")
        freq = Frequency.from_str(freq_str)

        if not rate.isdigit():
            raise Exception("invalid rate expression, expression must begin with a positive integer")

        if not freq:
            raise Exception(
                f"invalid rate expression, frequency must be one of ${Frequency.as_str_list()}, received ${freq_str}"
            )

        opts = RateWorkerOptions(self.description, int(rate), freq)

        self.server = FunctionServer(opts)
        self.server.event(*middleware)
        return Nitric._register_worker(self.server)


def schedule(description: str, every: str):
    """Return a schedule decorator."""

    def decorator(func: EventMiddleware):
        r = Schedule(description)
        r.every(every, func)
        return r

    return decorator