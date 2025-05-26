import os
import typing

from dataclasses import dataclass

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from .utils import is_model_type, is_optional_type, unify_name, unwrap_types


@dataclass(frozen=True)
class EnvironmentField:
    """
    Metadata for one environment-bound field in the configuration.
    Used for documentation, env parsing and diagnostics.
    """

    title: str
    name: str
    field_path: typing.List[str]
    type: typing.Any
    default: typing.Any
    description: typing.Optional[str]
    examples: typing.Optional[typing.List[typing.Any]]


def _add_env(
    name: str,
    field: FieldInfo,
    _type: typing.Any,
    result: typing.List[EnvironmentField],
    current_env_name_path: typing.List[str],
    current_field_path: typing.List[str],
):
    jse = field.json_schema_extra
    if isinstance(jse, dict) and isinstance(jse.get('env'), str):  # type: ignore[reportUnknownMemberType]
        jse = typing.cast(typing.Dict[str, str], jse)
        env_name: str = typing.cast(str, jse.get('env'))
    else:
        env_name: str = '_'.join(map(unify_name, current_env_name_path))
    result.append(
        EnvironmentField(
            title=field.title or field.alias or name,
            name=env_name,
            field_path=current_field_path,
            type=_type,
            default=field.default,
            description=field.description,
            examples=field.examples,
        )
    )


def _fill_env_list(
    config_cls: typing.Type[BaseModel],
    result: typing.List[EnvironmentField],
    field_path: typing.List[str],
    env_name_path: typing.List[str],
) -> None:
    for name, field in config_cls.model_fields.items():
        current_field_path = field_path + [field.alias or name]
        current_env_name_path = env_name_path + [field.alias or name]
        if is_optional_type(field.annotation):
            _add_env(
                name,
                field,
                field.annotation,
                result,
                current_env_name_path,
                current_field_path,
            )
            continue
        types = unwrap_types(field.annotation)
        for _type in types:
            if is_model_type(_type):
                _fill_env_list(
                    config_cls=_type,
                    result=result,
                    field_path=current_field_path,
                    env_name_path=current_env_name_path,
                )
            else:
                _add_env(
                    name,
                    field,
                    _type,
                    result,
                    current_env_name_path,
                    current_field_path,
                )


def create_env_list_from_cls(
    config_cls: typing.Type[BaseModel],
    project_name: typing.Optional[str]
) -> typing.List[EnvironmentField]:
    """
    Traverses the given Pydantic model and collects environment binding metadata.
    Supports nested models and custom env names via json_schema_extra['env'].
    """

    result: typing.List[EnvironmentField] = []
    _fill_env_list(
        config_cls=config_cls,
        result=result,
        field_path=[],
        env_name_path=[project_name] if project_name else []
    )
    return result


def assign_env_to_dict(
    config: typing.Dict[typing.Any, typing.Any],
    env_list: typing.List[EnvironmentField],
) -> typing.List[str]:
    """
    Reads values from `os.environ` and assigns them into the nested config dict.
    Returns the list of successfully applied environment variable names.
    """

    assigned_env_list: typing.List[str] = []
    for env in env_list:
        value = os.environ.get(env.name, None)
        if value is None:
            continue
        assigned_env_list.append(env.name)
        current_config_dict = config
        last_part_index = len(env.field_path) - 1
        for index, key in enumerate(env.field_path):
            if index == last_part_index:
                current_config_dict[key] = value
            else:
                if key not in current_config_dict:
                    current_config_dict[key] = {}
                current_config_dict = current_config_dict[key]
    return assigned_env_list


def _safe_get_type_name(_type: typing.Any):
    if hasattr(_type, '__name__'):
        return _type.__name__
    else:
        return str(_type)


def render_env_help(env_fields: typing.List[EnvironmentField]) -> str:
    """
    Generates a human-readable --help-like block for environment variables.

    Example output:
        APP_DB_HOST (str) — Database host. Default: "localhost"
        APP_DEBUG (bool) — Enables debug mode.
    """
    lines: typing.List[str] = []
    for field in env_fields:
        line = f"{field.name} ({_safe_get_type_name(field.type)})"
        if field.description:
            line += f" — {field.description.strip()}"
        if field.default not in (None, ..., PydanticUndefined):
            line += f" [default: {repr(field.default)}]"
        lines.append(line)
    return "\n".join(lines)
