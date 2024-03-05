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
from unittest import IsolatedAsyncioTestCase

from nitric.resources import schedule, ScheduleServer


# pylint: disable=protected-access,missing-function-docstring,missing-class-docstring


class Object(object):
    pass


class ApiTest(IsolatedAsyncioTestCase):
    def test_create_schedule(self):
        test_schedule = ScheduleServer("test-schedule")

        assert test_schedule is not None
        assert test_schedule.description == "test-schedule"

    def test_create_schedule_decorator_every(self):
        # test_schedule = schedule("test-schedule", "3 hours")(lambda ctx: ctx)
        test_schedule = schedule("test-schedule-every")
        schedule_server = test_schedule.every("3 hours")(lambda ctx: ctx)

        assert test_schedule is not None
        assert test_schedule.description == "test-schedule-every"
        assert (
            schedule_server._registration_request.schedule_name == "test-schedule-every"
        )  # pylint: disable=protected-access
        assert schedule_server._registration_request.every.rate == "3 hours"  # pylint: disable=protected-access

    def test_create_schedule_decorator_cron(self):
        # test_schedule = schedule("test-schedule", "3 hours")(lambda ctx: ctx)
        test_schedule = schedule("test-schedule-cron")
        schedule_server = test_schedule.cron("* * * * *")(lambda ctx: ctx)

        assert test_schedule is not None
        assert test_schedule.description == "test-schedule-cron"
        assert (
            schedule_server._registration_request.schedule_name == "test-schedule-cron"
        )  # pylint: disable=protected-access
        assert schedule_server._registration_request.cron.expression == "* * * * *"  # pylint: disable=protected-access

    # TODO: Re-implement schedule validation
    # def test_every_with_invalid_rate_description_frequency(self):
    #     test_schedule = Schedule("test-schedule")

    #     try:
    #         test_schedule.every("3 months", lambda ctx: ctx)
    #         pytest.fail()
    #     except Exception as e:
    #         assert str(e).startswith("invalid rate expression, frequency") is True

    # TODO: Re-implement schedule validation
    # def test_every_with_missing_rate_description_frequency(self):
    #     test_schedule = Schedule("test-schedule")

    #     try:
    #         test_schedule.every("3", lambda ctx: ctx)
    #         pytest.fail()
    #     except Exception as e:
    #         assert str(e).startswith("invalid rate expression, frequency") is True

    # TODO: Re-implement schedule validation
    # def test_every_with_invalid_rate_description_rate(self):
    #     test_schedule = Schedule("test-schedule")

    #     try:
    #         test_schedule.every("three days", lambda ctx: ctx)
    #         pytest.fail()
    #     except Exception as e:
    #         assert str(e).startswith("invalid rate expression, expression") is True

    # TODO: Re-implement schedule validation
    # def test_every_with_invalid_rate_description_frequency_and_rate(self):
    #     test_schedule = Schedule("test-schedule")

    #     try:
    #         test_schedule.every("three days", lambda ctx: ctx)
    #         pytest.fail()
    #     except Exception as e:
    #         assert str(e).startswith("invalid rate expression, expression") is True

    # TODO: Re-implement schedule validation
    # def test_every_with_missing_rate_description_rate(self):
    #     test_schedule = Schedule("test-schedule")

    #     try:
    #         test_schedule.every("months", lambda ctx: ctx)
    #         pytest.fail()
    #     except Exception as e:
    #         assert str(e).startswith("invalid rate expression, frequency") is True
