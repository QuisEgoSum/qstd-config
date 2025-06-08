import os
import sys

from pathlib import Path
from unittest.mock import patch

import pytest

from qstd_config.exceptions import FileNotExistsError
from qstd_config.utils import (
    get_config_paths,
    get_config_paths_from_args,
    get_config_paths_from_env,
    resolve_config_path,
)


def test_resolve_config_path():
    assert resolve_config_path('config.yaml', None) == Path('config.yaml')
    assert resolve_config_path('./config.yaml', None) == Path('config.yaml')
    assert resolve_config_path('./config.yaml', '/etc/project') == Path(
        '/etc/project/config.yaml',
    )
    assert resolve_config_path(
        '/etc/project/config.yaml',
        '/etc/project/base',
    ) == Path('/etc/project/config.yaml')


def test_config_path_parsing_from_args():
    with patch.object(sys, 'argv', ['app.py', '--config=config.yaml']):
        assert get_config_paths_from_args(None) == [Path('config.yaml')]

    with patch.object(sys, 'argv', ['app.py', '--config=./config.yaml']):
        assert get_config_paths_from_args(None) == [Path('./config.yaml')]

    with patch.object(
        sys,
        'argv',
        ['app.py', '--config=config.yaml;/etc/project/override/override.yaml'],
    ):
        assert get_config_paths_from_args('/etc/project') == [
            Path('/etc/project/config.yaml'),
            Path('/etc/project/override/override.yaml'),
        ]


def test_config_path_parsing_from_env():
    os.environ['PROJECT_CONFIG'] = 'config.yaml'
    assert get_config_paths_from_env('project', None) == [Path('config.yaml')]

    os.environ['CONFIG'] = 'config.yaml'
    assert get_config_paths_from_env(None, None) == [Path('config.yaml')]

    os.environ['PROJECT_CONFIG'] = './config.yaml'
    assert get_config_paths_from_env('project', None) == [Path('./config.yaml')]

    os.environ['PROJECT_CONFIG'] = './config.yaml;/etc/project/override/override.yaml'
    assert get_config_paths_from_env('project', '/etc/project') == [
        Path('/etc/project/config.yaml'),
        Path('/etc/project/override/override.yaml'),
    ]


def test_get_config_paths():
    os.environ['CONFIG'] = 'env_config.yaml'
    os.environ['PROJECT_CONFIG'] = 'env_project_config.yaml'

    with (
        patch.object(sys, 'argv', ['app.py', '--config=argv_config.yaml']),
        patch.object(Path, "exists", return_value=True),
    ):
        assert get_config_paths(
            ['./base.yaml'],
            parse_config_paths_from_env=True,
            parse_config_paths_from_args=True,
            project_name=None,
            root_config_path=None,
        ) == [
            Path('base.yaml'),
            Path('env_config.yaml'),
            Path('argv_config.yaml'),
        ]

    with (
        patch.object(sys, 'argv', ['app.py', '--config=argv_config.yaml']),
        patch.object(Path, "exists", return_value=True),
    ):
        assert get_config_paths(
            ['./base.yaml'],
            parse_config_paths_from_env=True,
            parse_config_paths_from_args=True,
            project_name='project',
            root_config_path='/etc/project',
        ) == [
            Path('/etc/project/base.yaml'),
            Path('/etc/project/env_project_config.yaml'),
            Path('/etc/project/argv_config.yaml'),
        ]

    with (
        patch.object(sys, 'argv', ['app.py', '--config=argv_config.yaml']),
        patch.object(Path, "exists", return_value=True),
    ):
        assert get_config_paths(
            ['./base.yaml'],
            parse_config_paths_from_env=False,
            parse_config_paths_from_args=False,
            project_name=None,
            root_config_path=None,
        ) == [Path('base.yaml')]

    with pytest.raises(FileNotExistsError):
        get_config_paths(
            ['./base.yaml'],
            parse_config_paths_from_env=False,
            parse_config_paths_from_args=False,
            project_name=None,
            root_config_path=None,
        )
