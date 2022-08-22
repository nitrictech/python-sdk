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
from examples.events.publish import events_publish
from examples.events.event_ids import events_event_ids

from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock


class EventsExamplesTest(IsolatedAsyncioTestCase):
    async def test_publish_topic(self):
        mock_publish = AsyncMock()

        with patch("nitricapi.nitric.event.v1.EventServiceStub.publish", mock_publish):
            await events_publish()

        mock_publish.assert_called_once()

    async def test_event_id_publish(self):
        mock_publish = AsyncMock()

        with patch("nitricapi.nitric.event.v1.EventServiceStub.publish", mock_publish):
            await events_event_ids()

        mock_publish.assert_called_once()
