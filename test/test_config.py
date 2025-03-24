import collections
import sys
import typing
from decimal import Decimal

import pytest
from pydantic import Field

from qstd_config import InMemoryConfig, MultiprocessingConfig, ConfigManager


def get_test_configration_class(base_cls):
    class Config(base_cls):
        class NestedConfig(base_cls):
            nested_field: str

        class NestedConfig2(base_cls):
            nested_field2: int

        class NestedConfig3(base_cls):
            class NestedConfig4(base_cls):
                class NestedConfig5(base_cls):
                    nested_field: int
                nested_field5: NestedConfig5
            nested_field4: NestedConfig4

        string_field: str
        int_field: int
        float_field: float
        bool_field: bool
        none_field: typing.Optional[str] = None
        none_field2: typing.Optional[int] = None

        int_with_default_field: int = 42

        decimal_field: Decimal

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
        nested_field3: NestedConfig3

        union_field: typing.Union[str, NestedConfig, NestedConfig2]
        annotated_field: typing.Annotated[int, Field(gt=0)]

        string_with_annotation: typing.Annotated[str, Field(max_length=100)]

        optional_union_field: typing.Optional[typing.Union[str, NestedConfig, NestedConfig2]] = None

    return Config


def get_default_config_dict():
    return {
        'nested_field3': {
            'nested_field4': {
                'nested_field5': {
                    'nested_field': 5
                }
            }
        },
        'string_field': 'example string',
        'int_field': 42,
        'float_field': 3.14,
        'bool_field': True,
        'none_field': None,
        'none_field2': None,

        'decimal_field': 3.14,

        'literal_field': 'option1',

        'list_field': ['item1', 'item2', 'item3'],
        'tuple_field': (1, 2, 3),
        'dict_field': {'key1': 10, 'key2': 20},
        'set_field': {'item1', 'item2', 'item3'},
        'frozenset_field': ['item1', 'item2', 'item3'],
        'deque_field': ['item1', 'item2', 'item3'],

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


def get_default_env_list_names():
    return [
        'NESTED_FIELD3_NESTED_FIELD4_NESTED_FIELD5_NESTED_FIELD',
        'STRING_FIELD',
        'INT_FIELD',
        'INT_WITH_DEFAULT_FIELD',
        'FLOAT_FIELD',
        'BOOL_FIELD',
        'NONE_FIELD',
        'NONE_FIELD2',
        'DECIMAL_FIELD',
        'LITERAL_FIELD',
        'LIST_FIELD',
        'TUPLE_FIELD',
        'DICT_FIELD',
        'SET_FIELD',
        'FROZENSET_FIELD',
        'DEQUE_FIELD',
        'NESTED_CONFIG_NESTED_FIELD',
        'NESTED_CONFIG_LIST',
        'NESTED_CONFIG_DICT',
        'NESTED_CONFIG_OPTIONAL',
        'NESTED_CONFIG_OPTIONAL_NESTED_FIELD',
        'NESTED_CONFIG_TUPLE',
        'UNION_FIELD',
        'UNION_FIELD_NESTED_FIELD',
        'UNION_FIELD_NESTED_FIELD2',
        'ANNOTATED_FIELD',
        'STRING_WITH_ANNOTATION',
        'OPTIONAL_UNION_FIELD',
        'OPTIONAL_UNION_FIELD_NESTED_FIELD',
        'OPTIONAL_UNION_FIELD_NESTED_FIELD2'
    ]


def get_default_env_values():
    return {
        'NESTED_FIELD3_NESTED_FIELD4_NESTED_FIELD5_NESTED_FIELD': '5',
        'STRING_FIELD': 'example string',
        'INT_FIELD': '42',
        'FLOAT_FIELD': '3.14',
        'BOOL_FIELD': 'true',
        'DECIMAL_FIELD': '3.14',
        'LITERAL_FIELD': 'option1',
        'LIST_FIELD': '["item1", "item2", "item3"]',
        'TUPLE_FIELD': '[1, 2, 3]',
        'DICT_FIELD': '{"key1": 10, "key2": 20}',
        'SET_FIELD': '["item1", "item2", "item3"]',
        'FROZENSET_FIELD': '["item1", "item2", "item3"]',
        'DEQUE_FIELD': '["item1", "item2", "item3"]',
        'NESTED_CONFIG_NESTED_FIELD': 'nested value',
        'NESTED_CONFIG_LIST': '[{"nested_field": "nested value 1"},{"nested_field": "nested value 2"}]',
        'NESTED_CONFIG_DICT': '{"key1": {"nested_field": "nested value"}}',
        'NESTED_CONFIG_OPTIONAL_NESTED_FIELD': 'nested value',
        'NESTED_CONFIG_TUPLE': '[{"nested_field": "nested value"}, {"nested_field": "nested value"}, {"nested_field2": 1}]',
        'UNION_FIELD_NESTED_FIELD': 'nested value',
        'ANNOTATED_FIELD': '5',
        'STRING_WITH_ANNOTATION': 'test',
        'OPTIONAL_UNION_FIELD_NESTED_FIELD2': '42'
    }


def default_configuration_type_asserts(config, Config):
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
def test_load_configuration(Config):
    manager = ConfigManager(Config)
    config = manager.load_configuration(get_default_config_dict())
    default_configuration_type_asserts(config, Config)


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


@pytest.mark.parametrize(
    'Config',
    [
        get_test_configration_class(InMemoryConfig),
        get_test_configration_class(MultiprocessingConfig)
    ]
)
def test_env_list_without_application_name(Config):
    manager = ConfigManager(Config)
    env_properties = manager.get_env_list()
    expected_env = set(get_default_env_list_names())
    for env_property in env_properties:
        assert env_property.name in expected_env


@pytest.mark.parametrize(
    'Config',
    [
        get_test_configration_class(InMemoryConfig),
        get_test_configration_class(MultiprocessingConfig)
    ]
)
def test_env_list_with_application_name(Config):
    manager = ConfigManager(Config, project_metadata=dict(name='some name'))
    env_properties = manager.get_env_list()
    expected_env_list = set()
    for name in get_default_env_list_names():
        expected_env_list.add('SOME_NAME_' + name)
    for env_property in env_properties:
        assert env_property.name in expected_env_list


@pytest.mark.parametrize(
    'Config',
    [
        get_test_configration_class(InMemoryConfig),
        get_test_configration_class(MultiprocessingConfig)
    ]
)
def test_load_from_env(Config, monkeypatch):
    for key, value in get_default_env_values().items():
        monkeypatch.setenv(key, value)
    manager = ConfigManager(Config)
    config = manager.load_configuration()
    default_configuration_type_asserts(config, Config)


@pytest.mark.parametrize(
    'Config',
    [
        get_test_configration_class(InMemoryConfig),
        get_test_configration_class(MultiprocessingConfig)
    ]
)
def test_load_from_env2(Config, monkeypatch):
    env_dict = get_default_env_values()
    del env_dict['UNION_FIELD_NESTED_FIELD']
    del env_dict['OPTIONAL_UNION_FIELD_NESTED_FIELD2']
    del env_dict['NESTED_CONFIG_OPTIONAL_NESTED_FIELD']
    env_dict['UNION_FIELD'] = 'str'
    env_dict['OPTIONAL_UNION_FIELD'] = 'str'
    env_dict['NESTED_CONFIG_OPTIONAL'] = 'null'
    for key, value in env_dict.items():
        monkeypatch.setenv(key, value)
    manager = ConfigManager(Config)
    config = manager.load_configuration()
    assert isinstance(config.union_field, str)
    assert config.nested_config_optional is None
    assert isinstance(config.optional_union_field, str)


@pytest.mark.parametrize(
    'Config',
    [
        get_test_configration_class(InMemoryConfig),
        get_test_configration_class(MultiprocessingConfig)
    ]
)
def test_load_from_env3(Config, monkeypatch):
    env_dict = get_default_env_values()
    del env_dict['UNION_FIELD_NESTED_FIELD']
    del env_dict['OPTIONAL_UNION_FIELD_NESTED_FIELD2']
    env_dict['UNION_FIELD_NESTED_FIELD2'] = '42'
    env_dict['OPTIONAL_UNION_FIELD_NESTED_FIELD'] = 'str'
    for key, value in env_dict.items():
        monkeypatch.setenv(key, value)
    manager = ConfigManager(Config)
    config = manager.load_configuration()
    assert isinstance(config.union_field, Config.NestedConfig2)
    assert isinstance(config.optional_union_field, Config.NestedConfig)


def test_parse_config_files_paths(monkeypatch):
    monkeypatch.setenv('CONFIG', './some/file2.yaml;./some/file3.yaml')
    monkeypatch.setattr(sys, 'argv', ['program', '--config', './some/file4.yaml;./some/file5.yaml'])
    Config = get_test_configration_class(InMemoryConfig)
    manager = ConfigManager(Config, default_config_dir='/etc/project', config_paths=['./some/file1.yaml'])

    assert manager.config_paths[0] == '/etc/project/some/file1.yaml'
    assert manager.config_paths[1] == '/etc/project/some/file2.yaml'
    assert manager.config_paths[2] == '/etc/project/some/file3.yaml'
    assert manager.config_paths[3] == '/etc/project/some/file4.yaml'
    assert manager.config_paths[4] == '/etc/project/some/file5.yaml'


def test_parse_config_file_from_env_with_project_name(monkeypatch):
    monkeypatch.setenv('SOME_PROJECT_CONFIG', './some/file1.yaml')
    Config = get_test_configration_class(InMemoryConfig)
    manager = ConfigManager(Config, default_config_dir='/etc/project', project_metadata=dict(name='some project'))
    assert manager.config_paths[0] == '/etc/project/some/file1.yaml'


@pytest.mark.parametrize(
    'Config',
    [
        get_test_configration_class(InMemoryConfig),
        get_test_configration_class(MultiprocessingConfig)
    ]
)
def test_load_config_from_file(Config, monkeypatch):
    pass


@pytest.mark.parametrize(
    'Config',
    [
        get_test_configration_class(InMemoryConfig),
        get_test_configration_class(MultiprocessingConfig)
    ]
)
def test_override_config_from_multiple_files(Config, monkeypatch):
    pass


@pytest.mark.parametrize(
    'Config',
    [
        get_test_configration_class(InMemoryConfig),
        get_test_configration_class(MultiprocessingConfig)
    ]
)
def test_override_config_from_env(Config, monkeypatch):
    pass
