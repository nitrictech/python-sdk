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
from unittest import TestCase

import pytest
from grpclib import GRPCError, Status

from nitric.api.exception import (
    CancelledException,
    exception_from_grpc_error,
    _exception_code_map,
    UnknownException,
    InvalidArgumentException,
    DeadlineExceededException,
    NotFoundException,
    AlreadyExistsException,
    PermissionDeniedException,
    ResourceExhaustedException,
    FailedPreconditionException,
    AbortedException,
    OutOfRangeException,
    UnimplementedException,
    InternalException,
    UnavailableException,
    DataLossException,
    UnauthenticatedException,
    exception_from_grpc_code,
)


expectedMapping = [
    (0, Exception),
    (1, CancelledException),
    (2, UnknownException),
    (3, InvalidArgumentException),
    (4, DeadlineExceededException),
    (5, NotFoundException),
    (6, AlreadyExistsException),
    (7, PermissionDeniedException),
    (8, ResourceExhaustedException),
    (9, FailedPreconditionException),
    (10, AbortedException),
    (11, OutOfRangeException),
    (12, UnimplementedException),
    (13, InternalException),
    (14, UnavailableException),
    (15, DataLossException),
    (16, UnauthenticatedException),
]


class TestException:
    @pytest.fixture(autouse=True)
    def init_exceptions(self):
        # Status codes that can be automatically converted to exceptions
        self.accepted_status_codes = set(_exception_code_map.keys())

        # Ensure none of the status are missing from the test cases
        assert set(k for k, v in expectedMapping) == self.accepted_status_codes

    def test_all_codes_handled(self):
        # Status codes defined by betterproto
        all_grpc_status_codes = set(status.value for status in Status)

        assert all_grpc_status_codes == self.accepted_status_codes

    @pytest.mark.parametrize("test_value", expectedMapping)
    def test_grpc_code_to_exception(self, test_value):
        status, expected_class = test_value
        exception = exception_from_grpc_error(GRPCError(Status(status), "some error"))

        assert isinstance(exception, expected_class)

    def test_unexpected_status_code(self):
        assert isinstance(exception_from_grpc_code(100), UnknownException)
