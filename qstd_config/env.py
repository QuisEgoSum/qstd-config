import copy
import os
import typing
from dataclasses import dataclass

import jsonref
from pydantic import BaseModel

from .utils import unify_name


@dataclass(frozen=True)
class EnvOption:
    parts: typing.List[str]
    type: str
    name: str


def _fill_env_list(schema: dict, result: typing.List[EnvOption], parts: typing.List[str], project_name: str) -> None:
    if 'allOf' in schema:
        for next_schema in schema['allOf']:
            _fill_env_list(next_schema, result, parts, project_name)
    elif schema['type'] == 'object' or 'object' in schema['type']:
        for name, next_schema in schema['properties'].items():
            current_parts = list(parts)
            current_parts.append(name)
            _fill_env_list(next_schema, result, current_parts, project_name)
    else:
        current_paths = list(parts)
        name_parts = [unify_name(env_name) for env_name in current_paths]
        name_parts.insert(0, project_name)
        result.append(EnvOption(current_paths, schema['type'], '_'.join(name_parts)))


def create_env_list_from_schema(config_cls: typing.Type[BaseModel], project_name: str) -> typing.List[EnvOption]:
    result: typing.List[EnvOption] = []
    _fill_env_list(
        copy.deepcopy(jsonref.loads(config_cls.schema_json(), jsonschema=True)),
        result,
        [],
        project_name
    )
    return result


def assign_env_to_dict(
    config: dict,
    env_list: typing.List[EnvOption],
) -> typing.List[str]:
    assigned_env_list: typing.List[str] = []
    for env in env_list:
        value = os.environ.get(env.name, None)
        if value is None:
            continue
        assigned_env_list.append(env.name)
        current_config_dict = config
        last_part_index = len(env.parts) - 1
        for index, key in enumerate(env.parts):
            if index == last_part_index:
                current_config_dict[key] = value
            else:
                if key not in current_config_dict:
                    current_config_dict[key] = dict()
                current_config_dict = current_config_dict[key]
    return assigned_env_list
