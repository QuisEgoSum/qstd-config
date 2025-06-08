from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from qstd_config.exceptions import InvalidFileContentError, UnsupportedFileTypeError
from qstd_config.loader import FileLoader, JsonFileLoader, YamlFileLoader
from qstd_config.merge_strategy import DeepMergeStrategy


def test_yaml_loader():
    loader = YamlFileLoader()

    assert loader.supported_extensions() == ['.yaml', '.yml']
    assert loader.is_supported(Path('/etc/config.yaml'))
    assert loader.is_supported(Path('/etc/config.yml'))

    config_yaml = '''
    debug: true
    string: test
    nested:
        flag: true
    '''

    with patch('qstd_config.loader.file_loader.open', mock_open(read_data=config_yaml)):
        config = loader.load(Path('/etc/config.yaml'))

    assert config == {'debug': True, 'string': 'test', 'nested': {'flag': True}}

    config_yaml = '''
    - a
    - b
    '''

    with (
        pytest.raises(InvalidFileContentError),
        patch('qstd_config.loader.file_loader.open', mock_open(read_data=config_yaml)),
    ):
        loader.load(Path('/etc/config.yaml'))


def test_json_loader():
    loader = JsonFileLoader()

    assert loader.supported_extensions() == ['.json']
    assert loader.is_supported(Path('/etc/config.json'))

    config_json = '''
    {
        "debug": true,
        "string": "test",
        "nested": {
            "flag": true
        }
    }
    '''

    with patch('qstd_config.loader.file_loader.open', mock_open(read_data=config_json)):
        config = loader.load(Path('/etc/config.json'))

    assert config == {'debug': True, 'string': 'test', 'nested': {'flag': True}}

    config_json = '''
    [1, 2]
    '''

    with (
        pytest.raises(InvalidFileContentError),
        patch('qstd_config.loader.file_loader.open', mock_open(read_data=config_json)),
    ):
        loader.load(Path('/etc/config.json'))


def test_file_loader():
    loader = FileLoader(
        paths=[Path('/etc/config.yaml'), Path('/etc/config.json')],
        file_loaders=[
            YamlFileLoader(),
            JsonFileLoader(),
        ],
        merge_strategy=DeepMergeStrategy(),
    )

    config_yaml = '''
    debug: false
    string: string
    nested:
        flag: false
    '''
    config_json = '''
    {
        "debug": true,
        "string": "test",
        "nested": {
            "flag": true
        }
    }
    '''

    mock_yaml = mock_open(read_data=config_yaml)
    mock_json = mock_open(read_data=config_json)

    with patch(
        'qstd_config.loader.file_loader.open',
        side_effect=[mock_yaml.return_value, mock_json.return_value],
    ):
        config = loader.load()

    assert config == {'debug': True, 'string': 'test', 'nested': {'flag': True}}


def test_file_loader_unsupported_extension():
    loader = FileLoader(
        paths=[Path('/etc/config.xml')],
        file_loaders=[
            YamlFileLoader(),
            JsonFileLoader(),
        ],
        merge_strategy=DeepMergeStrategy(),
    )

    with pytest.raises(UnsupportedFileTypeError):
        loader.load()
