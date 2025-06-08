import os

from pathlib import Path
from unittest.mock import mock_open, patch

from qstd_config.loader import ChainLoader, EnvLoader, FileLoader
from qstd_config.loader.base import CustomLoaderABC, EnvLoaderABC
from qstd_config.loader.file_loader_registry import get_file_loaders
from qstd_config.merge_strategy import DeepMergeStrategy
from tests.fixtures.config import AppConfig


def test_chain_loader():
    merge_strategy = DeepMergeStrategy()

    chain_loader = ChainLoader(
        loaders=[
            FileLoader(
                paths=[Path('test.yaml')],
                file_loaders=get_file_loaders(),
                merge_strategy=merge_strategy,
            ),
            EnvLoader(model=AppConfig, prefix=None),
        ],
        merge_strategy=merge_strategy,
    )

    os.environ['DEBUG_OVERRIDE'] = 'true'

    config_yaml = '''
    debug: false
    string: string
    nested:
        flag: false
    '''

    with patch('qstd_config.loader.file_loader.open', mock_open(read_data=config_yaml)):
        config = chain_loader.load()

    assert config == {
        'debug': 'true',
        'string': 'string',
        'nested': {
            'flag': False,
        },
    }

    assert isinstance(chain_loader.get_loader(EnvLoaderABC), EnvLoaderABC)
    assert chain_loader.get_loader(CustomLoaderABC) is None
