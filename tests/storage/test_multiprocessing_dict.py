import pytest

from qstd_config import MultiprocessingDictStorage
from qstd_config.exceptions import (
    MultiprocessingStorageNotInitializedWarning,
    MultiprocessingStorageReinitWarning,
    StorageNotInitializedError,
)
from qstd_config.storage.types import MultiprocessingContextType
from tests.fixtures.config import AppConfig


def test_multiprocessing_storage_main_process():
    config = AppConfig(debug=False)

    storage = MultiprocessingDictStorage(config)

    assert storage.is_initialized is False

    ctx: MultiprocessingContextType = {
        'initialized': False,
        'config': {},
        'revision': 'xxx',
    }

    with pytest.raises(StorageNotInitializedError):
        storage.update(AppConfig(debug=True))

    with pytest.warns(MultiprocessingStorageNotInitializedWarning):
        storage.current()

    storage.setup(multiprocessing_dict=ctx)

    assert ctx['initialized'] is True

    assert storage.is_initialized is True

    assert storage.current().debug is False

    storage.update(AppConfig(debug=True))

    assert storage.current().debug is True

    with pytest.warns(MultiprocessingStorageReinitWarning):
        storage.setup(multiprocessing_dict=ctx)


def test_multiprocessing_storage_child_process():
    config = AppConfig(debug=False)

    storage = MultiprocessingDictStorage(config)

    ctx: MultiprocessingContextType = {
        'initialized': True,
        'config': config.model_dump(mode='json'),
        'revision': 'xxx',
    }

    assert storage.is_initialized is False

    storage.setup(multiprocessing_dict=ctx)

    assert ctx['initialized'] is True
    assert ctx['config'] == config.model_dump(mode='json')
    assert ctx['revision'] == 'xxx'

    assert storage.is_initialized is True

    assert storage.current().debug is False

    storage.update(AppConfig(debug=True))

    assert storage.current().debug is True
    assert ctx['revision'] != 'xxx'
