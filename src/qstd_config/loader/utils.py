import re
import typing

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from qstd_config.loader.env_field import EnvironmentField


def to_env_name(name: str):
    """
    Converts a string into an environment variable name format: upper-cases all letters and replaces any
    non-alphanumeric characters with underscores.

    :param name:
    :return:
    """

    return re.sub(
        pattern=r'[^A-Z0-9]+',
        repl='_',
        flags=re.DOTALL,
        string=name.upper(),
    ).strip('_')


def deep_set(
    mapping: typing.MutableMapping[str, typing.Any],
    keys: typing.List[str],
    value: typing.Any,
) -> None:
    """
    Set a value in a nested mapping given a sequence of keys,
    creating intermediate dicts as needed.

    :param mapping: The root mapping to modify.
    :param keys: Ordered sequence of keys representing the nested path.
    :param value: The value to assign at the deepest key.
    :raises TypeError: If an intermediate value is not a MutableMapping.
    """
    m = mapping
    for key in keys[:-1]:
        if key not in m or not isinstance(m[key], typing.MutableMapping):
            m[key] = {}
        m = m[key]
    m[keys[-1]] = value


def unwrap_types(annotation: typing.Any) -> typing.Set[typing.Any]:
    """
    Recursively unwraps Union, Optional, and Annotated types to extract base types.
    Container types (like List, Dict, Tuple) are not unwrapped.

    :param annotation: The annotation to process.
    :return: A set of base or container types.
    """

    origin = typing.get_origin(annotation)

    # Special case: Annotated — unwrap only first arg
    if origin is typing.Annotated:
        return unwrap_types(typing.get_args(annotation)[0])

    # Special case: Union — recurse into its args
    if origin is typing.Union:
        result: typing.Set[typing.Any] = set()
        for arg in typing.get_args(annotation):
            result.update(unwrap_types(arg))
        return result

    # Not a supported wrapper — return as-is
    return {annotation}


def is_model_type(annotation: typing.Any) -> bool:
    """
    Check whether the given annotation is a subclass of Pydantic `BaseModel`.

    :param annotation: The object or annotation to test.
    :return: True if annotation is a `BaseModel` subclass, False otherwise.
    """

    if annotation is None:
        return False
    try:
        return issubclass(annotation, BaseModel)
    except TypeError:
        return False


def safe_get_type_name(obj: typing.Any) -> str:
    """
    Return the `__name__` of a class or type, or fallback
    to its `str()` representation if no __name__ exists.

    :param obj: The object or type to inspect.
    :return: A string name.
    """

    return getattr(obj, "__name__", None) or str(obj)


def _add_env(
    alias: str,
    field: FieldInfo,
    field_type: typing.Any,
    result: typing.List[EnvironmentField],
    env_name_path: typing.List[str],
    field_path: typing.List[str],
):
    """
    Append a new EnvironmentField to `result` for a single field.

    :param alias: Field name or alias in the model.
    :param field: Pydantic FieldInfo metadata.
    :param field_type: Python type or BaseModel subclass for this field.
    :param result: List accumulating EnvironmentField instances.
    :param env_name_path: Components used to build the env var name.
    :param field_path: Components indicating where to set this value in the nested dict.
    """

    jse = field.json_schema_extra
    if isinstance(jse, dict) and isinstance(jse.get('env'), str):  # type: ignore[reportUnknownMemberType]
        jse = typing.cast(typing.Dict[str, str], jse)
        env_name: str = typing.cast(str, jse.get('env'))
    else:
        env_name: str = '_'.join(map(to_env_name, env_name_path))
    result.append(
        EnvironmentField(
            title=field.title or alias,
            name=env_name,
            field_path=field_path,
            type=field_type,
            default=field.default,
            description=field.description,
            examples=field.examples,
        ),
    )


def _fill_env_list(
    config_model: typing.Type[BaseModel],
    result: typing.List[EnvironmentField],
    field_path: typing.List[str],
    env_name_path: typing.List[str],
) -> None:
    """
    Recursively traverse a BaseModel class to collect EnvironmentField entries
    for each field, handling nested BaseModel types and Optionals.

    :param config_model: Pydantic BaseModel class to inspect.
    :param result: List to accumulate EnvironmentField instances.
    :param field_path: Accumulated path segments for nested keys.
    :param env_name_path: Accumulated segments for constructing env var names.
    """

    for name, field in config_model.model_fields.items():
        alias = field.alias or name

        current_field_path = field_path + [alias]
        current_env_name_path = env_name_path + [alias]

        type_list = unwrap_types(field.annotation)
        non_model_types: typing.List[typing.Any] = []

        for field_type in type_list:
            if is_model_type(field_type):
                _fill_env_list(
                    config_model=field_type,
                    result=result,
                    field_path=current_field_path,
                    env_name_path=current_env_name_path,
                )
            else:
                non_model_types.append(field_type)

        if non_model_types and not (
            len(non_model_types) == 1 and non_model_types[0] is type(None)
        ):
            _add_env(
                alias,
                field,
                typing.Union[tuple(non_model_types)],
                result,
                current_env_name_path,
                current_field_path,
            )


def build_env_list(
    model: typing.Type[BaseModel],
    prefix: typing.Optional[str],
) -> typing.List[EnvironmentField]:
    """
    Generate the complete list of EnvironmentField for a Pydantic model.

    :param model: Pydantic BaseModel class.
    :param prefix: Optional environment variable name prefix
    :return: List of all EnvironmentField entries for every model field.
    """

    result: typing.List[EnvironmentField] = []

    env_name_path: typing.List[str] = []
    if prefix is not None:
        env_name_path.append(prefix)

    _fill_env_list(
        config_model=model,
        result=result,
        field_path=[],
        env_name_path=env_name_path,
    )
    return result
