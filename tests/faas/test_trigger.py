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
from unittest.mock import patch, AsyncMock, Mock, call

from nitric.faas import ResponseContext, HttpResponseContext, TopicResponseContext, Trigger, TriggerContext
from nitricapi.nitric.faas.v1 import TriggerRequest, TopicTriggerContext, HttpTriggerContext


class ResponseContextTest(IsolatedAsyncioTestCase):

    # def default_response_no_trigger_context(self):
    #     trigger = Trigger(context=TriggerContext(), data=b'')

    def test_from_wire_http_trigger(self):
        wire_trigger = TriggerRequest(data=b"a byte string", http=HttpTriggerContext())
        trigger = Trigger.from_trigger_request(wire_trigger)
        self.assertTrue(trigger.context.is_http())
        self.assertFalse(trigger.context.is_topic())

    def test_from_wire_topic_trigger(self):
        wire_trigger = TriggerRequest(data=b"a byte string", topic=TopicTriggerContext())
        trigger = Trigger.from_trigger_request(wire_trigger)
        self.assertTrue(trigger.context.is_topic())
        self.assertFalse(trigger.context.is_http())
