import os
import sys
import typing

from unittest.mock import mock_open, patch

from qstd_config import MultiprocessingStorage, ProjectMetadataType
from qstd_config.manager import ConfigManager

from fixtures.sample_config import AppConfig


def test_load_config_from_initial_data():
    manager = ConfigManager(
        AppConfig,
        project_metadata={'name': 'project', 'version': '1.0.0'},
    )
    config = manager.load_config_model({'debug': 'true', 'nested': {'flag': 'true'}})

    assert config.debug is True
    assert config.nested.flag is True


def test_load_config_from_yaml():
    manager = ConfigManager(
        AppConfig,
        project_metadata={'name': 'project', 'version': '1.0.0'},
        config_paths=['config.yaml']
    )

    config_yaml = '''
    debug: true
    string: test
    nested:
        flag: true
    '''

    with patch('qstd_config.manager.open', mock_open(read_data=config_yaml)):
        config = manager.load_config_model()

    assert config.debug is True
    assert config.string == 'test'
    assert config.nested.flag is True


def test_load_config_from_yaml_with_override():
    manager = ConfigManager(
        AppConfig,
        project_metadata={'name': 'project', 'version': '1.0.0'},
        config_paths=['config.yaml', 'config2.yaml']
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

    with patch('qstd_config.manager.open', side_effect=[mock1.return_value, mock2.return_value]):
        config = manager.load_config_model()

    assert config.debug is True
    assert config.string == 'test2'
    assert config.nested.flag is False


def test_load_config_from_all_sources_with_override():

    manager = ConfigManager(
        AppConfig,
        project_metadata={'name': 'project', 'version': '1.0.0'},
        config_paths=['config.yaml']
    )

    config_yaml = '''
    string: test
    nested:
        flag: false
    '''

    os.environ['PROJECT_NESTED_FLAG'] = 'true'

    with patch('qstd_config.manager.open', mock_open(read_data=config_yaml)):
        config = manager.load_config_model({'debug': True})

    assert config.debug is True
    assert config.string == 'test'
    assert config.nested.flag is True


def test_multiprocess_simulation():
    # main process
    manager_main = ConfigManager(
        AppConfig,
        project_metadata={'name': 'project', 'version': '1.0.0'},
        storage=MultiprocessingStorage
    )
    proxy_main = manager_main.load_config_model({'debug': 'true'})

    assert proxy_main.is_ready is True

    assert proxy_main.debug is True

    context = manager_main.get_multiprocessing_context()

    # simulated child process
    with patch('multiprocessing.current_process') as mock_proc:
        mock_proc.return_value.name = 'spawned'

        manager_child = ConfigManager(
            AppConfig,
            project_metadata={'name': 'project', 'version': '1.0.0'},
            storage=MultiprocessingStorage
        )
        proxy_child = manager_child.load_config_model()

        assert proxy_child.is_ready is False

        manager_child.set_multiprocessing_context(context)

        assert proxy_child.is_ready is True

        assert proxy_child.debug is True


def test_config_path_parsing_from_args():
    with patch.object(sys, 'argv', ['app.py', '--config=config.yaml']):
        manager = ConfigManager(
            AppConfig,
            project_metadata={'name': 'project', 'version': '1.0.0'}
        )
        assert manager._config_paths == ['config.yaml']  # type: ignore[reportPrivateUsage]

    with patch.object(sys, 'argv', ['app.py', '--config=./config.yaml']):
        manager = ConfigManager(
            AppConfig,
            project_metadata={'name': 'project', 'version': '1.0.0'}
        )
        assert manager._config_paths == ['./config.yaml']  # type: ignore[reportPrivateUsage]

    with patch.object(sys, 'argv', ['app.py', '--config=config.yaml;/etc/project/override/override.yaml']):
        manager = ConfigManager(
            AppConfig,
            project_metadata={'name': 'project', 'version': '1.0.0'},
            root_config_path='/etc/project'
        )
        assert manager._config_paths == [    # type: ignore[reportPrivateUsage]
            '/etc/project/config.yaml', '/etc/project/override/override.yaml'
        ]


def test_config_path_parsing_from_env():
    os.environ['PROJECT_CONFIG'] = 'config.yaml'
    manager = ConfigManager(
        AppConfig,
        project_metadata={'name': 'project', 'version': '1.0.0'}
    )
    assert manager._config_paths == ['config.yaml']  # type: ignore[reportPrivateUsage]

    os.environ['PROJECT_CONFIG'] = './config.yaml'
    manager = ConfigManager(
        AppConfig,
        project_metadata={'name': 'project', 'version': '1.0.0'}
    )
    assert manager._config_paths == ['./config.yaml']  # type: ignore[reportPrivateUsage]

    os.environ['PROJECT_CONFIG'] = './config.yaml;/etc/project/override/override.yaml'
    manager = ConfigManager(
        AppConfig,
        project_metadata={'name': 'project', 'version': '1.0.0'},
        root_config_path='/etc/project'
    )
    assert manager._config_paths == [  # type: ignore[reportPrivateUsage]
        '/etc/project/config.yaml', '/etc/project/override/override.yaml'
    ]


def test_used_env():
    os.environ['DEBUG_OVERRIDE'] = 'true'
    os.environ['PROJECT_NESTED_FLAG'] = 'true'
    manager = ConfigManager(
        AppConfig,
        project_metadata={'name': 'project', 'version': '1.0.0'}
    )
    manager.load_config_model()
    assert set(manager.used_env) == {'DEBUG_OVERRIDE', 'PROJECT_NESTED_FLAG'}


def test_without_project_name():
    class OverrideConfigManager(ConfigManager[AppConfig, ProjectMetadataType]):
        def get_project_name(self) -> typing.Optional[str]:
            return None

    manager = OverrideConfigManager(
        AppConfig,
        project_metadata={'name': 'project', 'version': '1.0.0'}
    )

    assert {env.name for env in manager.env_list} == {'DEBUG_OVERRIDE', 'NESTED_FLAG', 'STRING'}
