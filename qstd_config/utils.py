import copy
import os
import re

import typing


def unify_name(name: str):
    return re.sub(pattern='[^a-zA-Z0-9]', repl='_', flags=re.DOTALL, string=name.upper())


def abs_path(path: str, base_path: typing.Optional[str]):
    if base_path is not None and not path.startswith('/'):
        return os.path.abspath(os.path.join(base_path, path))
    return path


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


def get_override_config_paths_from_env(project_name: str, root_path: str) -> typing.List[str]:
    paths = []
    env_paths = os.environ.get(f'{unify_name(project_name)}_CONFIG')
    if env_paths:
        for env_path in env_paths.split(';'):
            paths.append(abs_path(env_path, root_path))
    return paths


def get_override_config_paths_from_args(root_path: str) -> typing.List[str]:
    import argparse
    paths = []
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
            paths.append(abs_path(argument_path, root_path))
    return paths
