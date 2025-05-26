import copy
import multiprocessing
import os
import re
import typing

from pydantic import BaseModel


def unify_name(name: str):
    """
    Converts a string to a normalized uppercase environment variable format.
    Replaces non-alphanumeric characters with underscores.
    """

    return re.sub(pattern='[^a-zA-Z0-9]', repl='_', flags=re.DOTALL, string=name.upper())


def resolve_config_path(path: str, base_path: typing.Optional[str]):
    """
    Resolves a config path relative to a base directory, unless it is already absolute.
    """

    if base_path is not None and not path.startswith('/'):
        return os.path.abspath(os.path.join(base_path, path))
    return path


def cross_merge_dicts(
    dict_a: typing.Dict[str, typing.Any],
    dict_b: typing.Dict[str, typing.Any]
) -> typing.Dict[str, typing.Any]:
    result = copy.deepcopy(dict_a)
    for key, value in dict_b.items():
        if key not in result:
            result[key] = value
        elif isinstance(value, dict) and isinstance(result[key], dict):
            value = typing.cast(typing.Dict[str, typing.Any], value)
            result[key] = cross_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def get_override_config_paths_from_env(
    project_name: typing.Optional[str],
    root_path: typing.Optional[str],
) -> typing.List[str]:
    paths: typing.List[str] = []
    env_name = 'CONFIG' if project_name is None else f'{unify_name(project_name)}_CONFIG'
    env_paths = os.environ.get(env_name)
    if env_paths:
        for env_path in env_paths.split(';'):
            paths.append(resolve_config_path(env_path, root_path))
    return paths


def get_override_config_paths_from_args(root_path: typing.Optional[str]) -> typing.List[str]:
    import argparse
    paths: typing.List[str] = []
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config',
        '-c',
        type=str,
        help='The path to the application configuration file'
    )
    argument_paths = parser.parse_known_args()[0].config
    if argument_paths:
        for argument_path in argument_paths.split(';'):
            paths.append(resolve_config_path(argument_path, root_path))
    return paths


def is_main_process() -> bool:
    return multiprocessing.current_process().name == 'MainProcess'


def is_optional_type(value: typing.Any) -> bool:
    origin = typing.get_origin(value)
    if origin is typing.Union:
        args = typing.get_args(value)
        if len(args) == 2 and type(None) in args:
            return True
    return False


def unwrap_types(annotation: typing.Any) -> typing.List[typing.Any]:
    if typing.get_origin(annotation) is None:
        return [annotation]
    args = typing.get_args(annotation)
    type_list: typing.List[typing.Any] = []
    for arg in args:
        type_list.extend(unwrap_types(arg))
    return type_list


def is_model_type(_type: typing.Any) -> bool:
    if _type is None:
        return False
    try:
        return issubclass(_type, BaseModel)
    except TypeError:
        return False
