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
import copy

from nitric.utils import struct_from_dict, dict_from_struct


def test__dict_from_struct():
    dict_val = {
        "a": True,
        "b": False,
        "c": 1,
        "d": 4.123,
        "e": "this is a string",
        "f": None,
        "g": {"ga": 1, "gb": "testing inner dict"},
        "h": [1, 2, 3, "four"],
    }
    dict_copy = copy.deepcopy(dict_val)

    # Serialization and Deserialization shouldn't modify the object in most cases.
    assert dict_from_struct(struct_from_dict(dict_val)) == dict_copy
