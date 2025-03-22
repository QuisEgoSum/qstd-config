import collections
import typing

import pytest
from pydantic import Field

from qstd_config import InMemoryConfig, MultiprocessingConfig, ConfigManager


def get_test_configration_class(base_cls):
    class Config(base_cls):
        class NestedConfig(base_cls):
            nested_field: str

        class NestedConfig2(base_cls):
            nested_field2: int

        string_field: str
        int_field: int
        float_field: float
        bool_field: bool
        none_field: typing.Optional[str] = None

        literal_field: typing.Literal['option1', 'option2', 'option3']

        list_field: typing.List[str]
        tuple_field: typing.Tuple[int, int, int]
        dict_field: typing.Dict[str, int]
        set_field: typing.Set[str]
        frozenset_field: typing.FrozenSet[str]
        deque_field: collections.deque

        nested_config: NestedConfig
        nested_config_list: typing.List[NestedConfig]
        nested_config_dict: typing.Dict[str, NestedConfig]
        nested_config_optional: typing.Optional[NestedConfig]
        nested_config_tuple: typing.Tuple[NestedConfig, NestedConfig, NestedConfig2]

        union_field: typing.Union[str, NestedConfig, NestedConfig2]
        annotated_field: typing.Annotated[int, Field(gt=0)]

        string_with_annotation: typing.Annotated[str, Field(max_length=100)]

        optional_union_field: typing.Optional[typing.Union[str, NestedConfig, NestedConfig2]] = None

    return Config


def get_default_config_dict():
    return {
        'string_field': 'example string',
        'int_field': 42,
        'float_field': 3.14,
        'bool_field': True,
        'none_field': None,
        'literal_field': 'option1',
        'list_field': ['item1', 'item2', 'item3'],
        'tuple_field': (1, 2, 3),
        'dict_field': {'key1': 10, 'key2': 20},
        'set_field': {'item1', 'item2', 'item3'},
        'frozenset_field': frozenset({'item1', 'item2', 'item3'}),
        'deque_field': collections.deque(['item1', 'item2', 'item3']),

        'nested_config': {
            'nested_field': 'nested value'
        },
        'nested_config_list': [
            {'nested_field': 'nested value 1'},
            {'nested_field': 'nested value 2'}
        ],
        'nested_config_dict': {
            'key1': {'nested_field': 'nested value 1'},
            'key2': {'nested_field': 'nested value 2'}
        },
        'nested_config_optional': {
            'nested_field': 'nested value optional'
        },
        'nested_config_tuple': [
            {'nested_field': 'nested value 1'},
            {'nested_field': 'nested value 2'},
            {'nested_field2': 3}
        ],

        'union_field': {'nested_field': 'union nested value'},
        'annotated_field': 5,

        'string_with_annotation': 'some long string',

        'optional_union_field': {'nested_field2': 1}
    }


@pytest.mark.parametrize(
    'Config',
    [
        get_test_configration_class(InMemoryConfig),
        get_test_configration_class(MultiprocessingConfig)
    ]
)
def test_load_configuration(Config):
    manager = ConfigManager(Config)
    config = manager.load_configuration(get_default_config_dict())

    assert isinstance(config, Config)
    assert isinstance(config.string_field, str)
    assert isinstance(config.int_field, int)
    assert isinstance(config.float_field, float)
    assert isinstance(config.bool_field, bool)
    assert config.none_field is None

    assert isinstance(config.literal_field, str)

    assert isinstance(config.list_field, list)
    assert all(isinstance(item, str) for item in config.list_field)
    assert isinstance(config.tuple_field, tuple)
    assert all(isinstance(item, int) for item in config.tuple_field)
    assert isinstance(config.dict_field, dict)
    assert all(isinstance(key, str) for key in config.dict_field)
    assert all(isinstance(value, int) for value in config.dict_field.values())
    assert isinstance(config.set_field, set)
    assert all(isinstance(item, str) for item in config.set_field)
    assert isinstance(config.frozenset_field, frozenset)
    assert all(isinstance(item, str) for item in config.frozenset_field)
    assert isinstance(config.deque_field, collections.deque)

    assert isinstance(config.nested_config, Config.NestedConfig)
    assert isinstance(config.nested_config.nested_field, str)
    assert isinstance(config.nested_config_list, list)
    assert all(isinstance(item, Config.NestedConfig) for item in config.nested_config_list)
    assert isinstance(config.nested_config_optional, Config.NestedConfig)
    assert isinstance(config.nested_config_optional.nested_field, str)
    assert isinstance(config.nested_config_tuple, tuple)
    assert isinstance(config.nested_config_tuple[0], Config.NestedConfig)
    assert isinstance(config.nested_config_tuple[1], Config.NestedConfig)
    assert isinstance(config.nested_config_tuple[2], Config.NestedConfig2)
    assert isinstance(config.nested_config_tuple[2].nested_field2, int)

    assert isinstance(config.union_field, Config.NestedConfig)
    assert isinstance(config.annotated_field, int)
    assert isinstance(config.string_with_annotation, str)
    assert isinstance(config.optional_union_field, Config.NestedConfig2)


@pytest.mark.parametrize(
    'Config',
    [
        get_test_configration_class(InMemoryConfig),
        get_test_configration_class(MultiprocessingConfig)
    ]
)
def test_update_configuration(Config):
    manager = ConfigManager(Config)
    config = manager.load_configuration(get_default_config_dict())
    config_dict = get_default_config_dict()
    config_dict['optional_union_field'] = None
    config_dict['union_field'] = 'str'
    config_dict['nested_config_optional'] = None
    config_dict['frozenset_field'] = frozenset({'item1', 'item2'})
    config_dict['tuple_field'] = (11, 22, 11)
    config_dict['dict_field'] = {'key3': 10}
    manager.load_configuration(config_dict)
    assert config.optional_union_field is None
    assert isinstance(config.union_field, str)
    assert config.nested_config_optional is None
    assert isinstance(config.frozenset_field, frozenset)
    assert config.frozenset_field == frozenset({'item1', 'item2'})
    assert config.tuple_field == (11, 22, 11)
    assert config.dict_field == {'key3': 10}
