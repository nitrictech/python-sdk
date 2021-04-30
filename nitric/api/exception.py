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


class UnimplementedException(Exception):
    """Exception raised when the requested operation isn't supported by the server."""

    pass


class AlreadyExistsException(Exception):
    """Exception raised when an entity already exist during a request to create a new entity."""

    pass


class UnavailableException(Exception):
    """Exception raised when a gRPC service is unavailable."""

    pass
