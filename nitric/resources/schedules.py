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

from datetime import timedelta
from enum import Enum
from typing import Callable, List

import betterproto
import grpclib.client
from nitric.application import Nitric
from nitric.faas import IntervalHandler, IntervalContext
from nitric.proto.schedules.v1 import (
    ScheduleRate,
    SchedulesStub,
    ClientMessage,
    RegistrationRequest,
)
from nitric.utils import new_default_channel
from nitric.faas import FunctionServer


class Schedule(FunctionServer):
    """A schedule for running functions on a cadence."""

    description: str

    handler: IntervalHandler
    registration_request: RegistrationRequest
    server: SchedulesStub

    def __init__(self, description: str):
        """Create a schedule for running functions on a cadence."""
        self.description = description

    def every(self, rate_description: str, handler: IntervalHandler) -> None:
        """
        Register middleware to be run at the specified rate.

        E.g. every("3 hours")
        """
        rate_description = rate_description.lower()

        rate, raw_freq = rate_description.split(" ")
        freq = Frequency.from_str(raw_freq)

        minutes = freq.as_time(int(rate))

        self.registration_request = RegistrationRequest(
            schedule_name=self.description,
            rate=ScheduleRate(minutes),
        )

        self.handler = handler

        Nitric._register_worker(self)

    async def start(self) -> None:
        """Register this schedule and start listening for requests."""
        channel = new_default_channel()
        server = SchedulesStub(channel=channel)

        try:
            async for server_message in server.schedule(
                [ClientMessage(registration_request=self.registration_request)]
            ):
                msg_type = betterproto.which_one_of(server_message, "content")

                if msg_type == "registration_response":
                    print("Schedule connected with membrane")
                    continue
                if msg_type == "interval_request":
                    ctx = IntervalContext.from_request(server_message)
                    await self.handler(ctx)
                    await self.server.schedule([ctx.to_response()])
        except grpclib.exceptions.GRPCError as e:
            print(f"Stream terminated: {e.message}")
        except grpclib.exceptions.StreamTerminatedError:
            print("Stream from membrane closed.")
        finally:
            print("Closing client stream")
            channel.close()


class Frequency(Enum):
    """Valid schedule frequencies."""

    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"

    @staticmethod
    def from_str(value: str) -> Frequency:
        """Convert a string frequency value to Frequency."""
        try:
            return Frequency[value.strip().upper()]
        except Exception:
            raise ValueError(f"{value} is not a valid frequency")

    @staticmethod
    def as_str_list() -> List[str]:
        """Return all frequency values as a list of strings."""
        return [str(frequency.value) for frequency in Frequency]

    def as_time(self, rate: int) -> timedelta:
        """Convert the rate to minutes based on the frequency."""
        if self == Frequency.MINUTES:
            return timedelta(minutes=rate)
        elif self == Frequency.HOURS:
            return timedelta(hours=rate)
        elif self == Frequency.DAYS:
            return timedelta(days=rate)
        else:
            raise ValueError(f"{self} is not a valid frequency")


def schedule(description: str, every: str) -> Callable[[IntervalHandler], Schedule]:
    """Return a schedule decorator."""

    def decorator(func: IntervalHandler) -> Schedule:
        r = Schedule(description)
        r.every(every, func)
        return r

    return decorator
