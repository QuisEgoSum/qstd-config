import os
import typing

from qstd_config.loader import ChainLoader, CustomLoaderABC, EnvLoader
from qstd_config.merge_strategy import DeepMergeStrategy
from tests.fixtures.config import AppConfig


def test_chain_loader():
    class CustomLoader(CustomLoaderABC):
        def load(self) -> typing.MutableMapping[str, typing.Any]:
            return {
                'debug': 'false',
                'string': 'test',
                'nested': {
                    'flag': True,
                },
            }

    merge_strategy = DeepMergeStrategy()

    chain_loader = ChainLoader(
        loaders=[
            CustomLoader(),
            EnvLoader(model=AppConfig, prefix=None),
        ],
        merge_strategy=merge_strategy,
    )

    os.environ['DEBUG_OVERRIDE'] = 'true'

    config = chain_loader.load()

    assert config == {
        'debug': 'true',
        'string': 'test',
        'nested': {
            'flag': True,
        },
    }
