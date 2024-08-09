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

import logging
from datetime import timedelta
from enum import Enum
from typing import Callable, List

import betterproto
import grpclib.exceptions

from nitric.application import Nitric
from nitric.bidi import AsyncNotifierList
from nitric.context import FunctionServer, IntervalContext, IntervalHandler
from nitric.proto.schedules.v1 import (
    ClientMessage,
    IntervalResponse,
    RegistrationRequest,
    ScheduleCron,
    ScheduleEvery,
    SchedulesStub,
)
from nitric.channel import ChannelManager


class ScheduleServer(FunctionServer):
    """A schedule for running functions on a cadence."""

    description: str

    handler: IntervalHandler
    _registration_request: RegistrationRequest
    _responses: AsyncNotifierList[ClientMessage]

    def __init__(self, description: str):
        """Create a schedule for running functions on a cadence."""
        self.description = description
        self._responses = AsyncNotifierList()

    def every(self, rate_description: str, handler: IntervalHandler) -> None:
        """
        Register a function to be run at the specified rate.

        E.g. every("3 hours")
        """
        self._registration_request = RegistrationRequest(
            schedule_name=self.description,
            every=ScheduleEvery(rate=rate_description.lower()),
        )

        self.handler = handler

        Nitric._register_worker(self)  # type: ignore pylint: disable=protected-access

    def cron(self, cron_expression: str, handler: IntervalHandler) -> None:
        """
        Register a function to be run at the specified cron schedule.

        E.g. cron("3 * * * *")
        """
        self._registration_request = RegistrationRequest(
            schedule_name=self.description,
            cron=ScheduleCron(expression=cron_expression),
        )

        self.handler = handler

        Nitric._register_worker(self)  # type: ignore pylint: disable=protected-access

    async def _schedule_request_iterator(self):
        # Register with the server
        yield ClientMessage(registration_request=self._registration_request)
        # wait for any responses for the server and send them
        async for response in self._responses:
            yield response

    async def start(self) -> None:
        """Register this schedule and start listening for requests."""
        channel = ChannelManager.get_channel()
        schedules_stub = SchedulesStub(channel=channel)

        try:
            async for server_msg in schedules_stub.schedule(self._schedule_request_iterator()):
                msg_type, _ = betterproto.which_one_of(server_msg, "content")

                if msg_type == "registration_response":
                    continue
                if msg_type == "interval_request":
                    ctx = IntervalContext(server_msg)
                    try:
                        await self.handler(ctx)
                    except Exception as e:  # pylint: disable=broad-except
                        logging.exception("An unhandled error occurred in a scheduled function: %s", e)
                    resp = IntervalResponse()
                    await self._responses.add_item(ClientMessage(id=server_msg.id, interval_response=resp))
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


class Schedule:
    """A raw schedule to be deployed and assigned a rate or cron interval."""

    def __init__(self, description: str):
        """Create a new schedule resource."""
        self.description = description

    def every(self, every: str) -> Callable[[IntervalHandler], ScheduleServer]:
        """
        Set the schedule interval.

        e.g. every('3 days').
        """

        def decorator(func: IntervalHandler) -> ScheduleServer:
            r = ScheduleServer(self.description)
            r.every(every, func)
            return r

        return decorator

    def cron(self, cron: str) -> Callable[[IntervalHandler], ScheduleServer]:
        """
        Set the schedule interval.

        e.g. cron('3 * * * *').
        """

        def decorator(func: IntervalHandler) -> ScheduleServer:
            r = ScheduleServer(self.description)
            r.cron(cron, func)
            return r

        return decorator


def schedule(description: str) -> Schedule:
    """Return a schedule."""
    return Schedule(description=description)
