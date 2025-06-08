import typing

from pydantic import BaseModel

from qstd_config.loader.env_field import EnvironmentField
from qstd_config.loader.utils import (
    build_env_list,
    deep_set,
    is_model_type,
    safe_get_type_name,
    to_env_name,
    unwrap_types,
)
from tests.fixtures.config import AppConfig


def test_to_env_name():
    assert to_env_name('hello world') == 'HELLO_WORLD'
    assert to_env_name('hello_world') == 'HELLO_WORLD'
    assert to_env_name('hello-world') == 'HELLO_WORLD'
    assert to_env_name('hello world 123') == 'HELLO_WORLD_123'
    assert to_env_name('hello%&*(@!#world') == 'HELLO_WORLD'
    assert to_env_name('%;hello%&*(@!#world:?') == 'HELLO_WORLD'


def test_deep_set():
    base: typing.MutableMapping[str, typing.Any] = {}

    deep_set(base, ['a', 'b', 'c'], 1)

    assert base['a']['b']['c'] == 1

    deep_set(base, ['a', 'b', 'c'], 2)

    assert base['a']['b']['c'] == 2

    deep_set(base, ['a', 'b', 'd'], 3)

    assert base['a']['b']['c'] == 2
    assert base['a']['b']['d'] == 3


def test_unwrap_types():
    class NamedTuple(typing.NamedTuple):
        field: AppConfig

    class TypedDict(typing.TypedDict):
        field: AppConfig

    CustomType = typing.NewType('CustomType', int)
    ref = typing.ForwardRef("SomeType")

    assert unwrap_types(int) == {int}
    assert unwrap_types(typing.Annotated[str, 'meta']) == {str}
    assert unwrap_types(typing.Union[int, str]) == {int, str}
    assert unwrap_types(typing.Optional[str]) == {str, type(None)}
    assert unwrap_types(typing.Annotated[typing.Union[int, str], "meta"]) == {int, str}
    assert unwrap_types(typing.Annotated[typing.Optional[int], "meta"]) == {
        int,
        type(None),
    }
    assert unwrap_types(ref) == {ref}

    assert unwrap_types(typing.Tuple[int, str]) == {typing.Tuple[int, str]}
    assert unwrap_types(typing.List[int]) == {typing.List[int]}
    assert unwrap_types(typing.Dict[str, int]) == {typing.Dict[str, int]}
    assert unwrap_types(NamedTuple) == {NamedTuple}
    assert unwrap_types(TypedDict) == {TypedDict}
    assert unwrap_types(typing.Literal['a', 'b', 1]) == {typing.Literal['a', 'b', 1]}
    assert unwrap_types(typing.Final[int]) == {typing.Final[int]}
    assert unwrap_types(CustomType) == {CustomType}

    assert unwrap_types(
        typing.Union[
            int,
            typing.Union[str, float],
            typing.List[str],
            typing.Tuple[int, str, float],
            typing.Annotated[str, 'hello'],
        ],
    ) == {
        int,
        str,
        float,
        typing.List[str],
        typing.Tuple[int, str, float],
    }


def test_is_model_type():
    assert is_model_type(BaseModel)
    assert is_model_type(AppConfig)
    assert not is_model_type(typing.Union[BaseModel, int])
    assert not is_model_type(None)


def test_safe_get_type_name():
    assert safe_get_type_name(str) == 'str'
    assert 'List' in safe_get_type_name(typing.List[str])
    assert 'Union' in safe_get_type_name(typing.Union[str, int])
    assert safe_get_type_name(int) == 'int'
    assert safe_get_type_name(None) == 'None'


def test_build_env_list():
    class BuildEnvListConfig(AppConfig):
        optional_type: typing.Optional[int] = None

    env_list = build_env_list(BuildEnvListConfig, None)

    assert env_list == [
        EnvironmentField(
            title='debug',
            name='DEBUG_OVERRIDE',
            field_path=['debug'],
            type=bool,
            default=False,
            description=None,
            examples=None,
        ),
        EnvironmentField(
            title='string',
            name='STRING',
            field_path=['string'],
            type=str,
            default='string',
            description=None,
            examples=None,
        ),
        EnvironmentField(
            title='flag',
            name='NESTED_FLAG',
            field_path=['nested', 'flag'],
            type=bool,
            default=False,
            description='Nested flag',
            examples=None,
        ),
        EnvironmentField(
            title='optional_type',
            name='OPTIONAL_TYPE',
            field_path=['optional_type'],
            type=typing.Optional[int],
            default=None,
            description=None,
            examples=None,
        ),
    ]

    env_list = build_env_list(AppConfig, 'Test project')

    assert {env.name for env in env_list} == {
        'DEBUG_OVERRIDE',
        'TEST_PROJECT_STRING',
        'TEST_PROJECT_NESTED_FLAG',
    }
