import os

from pathlib import Path
from unittest.mock import mock_open, patch

from qstd_config.loader.factory import default_chain_loader_factory
from qstd_config.merge_strategy import DeepMergeStrategy
from tests.fixtures.config import AppConfig


def test_chain_loader():
    merge_strategy = DeepMergeStrategy()

    chain_loader = default_chain_loader_factory(
        model=AppConfig,
        paths=[Path('test.yaml')],
        prefix=None,
        merge_strategy=merge_strategy,
        custom_loaders=[],
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
