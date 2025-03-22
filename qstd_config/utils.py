import copy
import inspect
import re
import sys
import typing

if sys.version_info >= (3, 10):
    def get_annotations(obj: typing.Any) -> typing.Mapping[str, typing.Any]:
        return inspect.get_annotations(obj)
else:
    def get_annotations(obj: typing.Any) -> typing.Mapping[str, typing.Any]:
        # https://docs.python.org/3/howto/annotations.html#annotations-howto
        if isinstance(obj, type):
            ann = obj.__dict__.get("__annotations__", None)
        else:
            ann = obj.__annotations__
        if ann is None:
            return dict()
        else:
            return typing.cast("Mapping[str, Any]", ann)


def unify_name(name: str):
    return re.sub(pattern='[^a-zA-Z0-9]', repl='_', flags=re.DOTALL, string=name.upper())


def cross_merge_dicts(dict_a: dict, dict_b: dict):
    result = copy.deepcopy(dict_a)
    for key, value in dict_b.items():
        if key not in result:
            result[key] = value
        elif isinstance(value, dict) and isinstance(result[key], dict):
            result[key] = cross_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
