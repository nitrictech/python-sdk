import copy

from nitric.api._utils import _struct_from_dict, _dict_from_struct


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
    assert _dict_from_struct(_struct_from_dict(dict_val)) == dict_copy
