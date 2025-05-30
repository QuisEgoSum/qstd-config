import os
import typing

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from pydantic_core import PydanticUndefined

from qstd_config import ConfigManager, EnvironmentField, MultiprocessingDictStorage
from qstd_config.exceptions import ConfigValidationError
from tests.fixtures.config import AppConfig, ComplexConfiguration


def test_load_config_from_initial_data():
    manager = ConfigManager(
        AppConfig,
        default_config_values={'debug': 'true', 'nested': {'flag': 'true'}},
    )
    config = manager.load_config_model()

    assert config.debug is True
    assert config.nested.flag is True


def test_load_config_from_yaml():
    with patch.object(Path, "exists", return_value=True):
        manager = ConfigManager(
            AppConfig,
            config_paths=['config.yaml'],
        )

    config_yaml = '''
    debug: true
    string: test
    nested:
        flag: true
    '''

    with patch('qstd_config.loader.file_loader.open', mock_open(read_data=config_yaml)):
        config = manager.load_config_model()

    assert manager.config_paths == [Path('config.yaml')]

    assert config.debug is True
    assert config.string == 'test'
    assert config.nested.flag is True


def test_load_config_from_yaml_with_override():
    with patch.object(Path, "exists", return_value=True):
        manager = ConfigManager(
            AppConfig,
            config_paths=['config.yaml', 'config2.yaml'],
        )

    config_yaml = '''
    debug: true
    string: test
    nested:
        flag: true
    '''

    config2_yaml = '''
    debug: true
    string: test2
    nested:
        flag: false
    '''

    mock1 = mock_open(read_data=config_yaml)
    mock2 = mock_open(read_data=config2_yaml)

    with patch(
        'qstd_config.loader.file_loader.open',
        side_effect=[mock1.return_value, mock2.return_value],
    ):
        config = manager.load_config_model()

    assert config.debug is True
    assert config.string == 'test2'
    assert config.nested.flag is False


def test_load_config_from_all_sources_with_override():
    def pre_validation_hook(
        raw_config: typing.MutableMapping[str, typing.Any],
    ) -> typing.MutableMapping[str, typing.Any]:
        raw_config['string'] = 'from pre validation hook'
        return raw_config

    with patch.object(Path, "exists", return_value=True):
        manager = ConfigManager(
            AppConfig,
            project_name='project',
            config_paths=['config.yaml'],
            default_config_values={'debug': True},
            pre_validation_hook=pre_validation_hook,
        )

    config_yaml = '''
    string: test
    nested:
        flag: false
    '''

    os.environ['PROJECT_NESTED_FLAG'] = 'true'

    with patch('qstd_config.loader.file_loader.open', mock_open(read_data=config_yaml)):
        config = manager.load_config_model()

    assert config.debug is True
    assert config.string == 'from pre validation hook'
    assert config.nested.flag is True


def test_multiprocess_simulation():
    # main process
    manager_main = ConfigManager(
        AppConfig,
        project_name='project',
        default_config_values={'debug': 'true'},
    )
    proxy_main = manager_main.get_proxy(MultiprocessingDictStorage)

    ctx = MultiprocessingDictStorage.create_shared_context()

    proxy_main.setup(multiprocessing_dict=ctx)

    assert proxy_main.is_ready is True

    assert proxy_main.debug is True

    # simulated child process
    manager_child = ConfigManager(
        AppConfig,
        project_name='project',
        default_config_values={'debug': 'true'},
    )
    proxy_child = manager_child.get_proxy(MultiprocessingDictStorage)

    assert proxy_child.is_ready is False

    proxy_child.setup(multiprocessing_dict=ctx)

    assert proxy_child.is_ready is True

    assert proxy_child.debug is True


def test_env_fields_access():
    os.environ['DEBUG_OVERRIDE'] = 'true'
    os.environ['NESTED_FLAG'] = 'true'

    manager = ConfigManager(AppConfig)

    manager.load_config_model()

    assert manager.env_list == [
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
    ]
    assert {env.name for env in manager.used_env_list} == {
        'DEBUG_OVERRIDE',
        'NESTED_FLAG',
    }
    assert isinstance(manager.render_env_help(), str)


def test_raise_validation_error():
    with patch.object(Path, "exists", return_value=True):
        manager = ConfigManager(AppConfig, config_paths=['config.yaml'])

    config_yaml = '''
    debug: 123
    string:
        field: 1
    nested:
        flag:
            - 1
            - 2
    '''

    with (
        pytest.raises(ConfigValidationError),
        patch('qstd_config.loader.file_loader.open', mock_open(read_data=config_yaml)),
    ):
        manager.load_config_model()


def test_complex_config():
    manager = ConfigManager(ComplexConfiguration)

    assert manager.env_list == [
        EnvironmentField(
            title='value',
            name='NESTED_VALUE',
            field_path=['nested', 'value'],
            type=typing.Union[int, float],
            default=PydanticUndefined,
            description=None,
            examples=None,
        ),
        EnvironmentField(
            title='nested',
            name='NESTED',
            field_path=['nested'],
            type=typing.Union[str, int, typing.List[ComplexConfiguration.Nested]],
            default=PydanticUndefined,
            description=None,
            examples=None,
        ),
        EnvironmentField(
            title='value',
            name='OPTIONAL_VALUE',
            field_path=['optional', 'value'],
            type=typing.Union[float, int],
            default=PydanticUndefined,
            description=None,
            examples=None,
        ),
        EnvironmentField(
            title='value',
            name='ANNOTATED_VALUE',
            field_path=['annotated', 'value'],
            type=typing.Union[float, int],
            default=PydanticUndefined,
            description=None,
            examples=None,
        ),
    ]
