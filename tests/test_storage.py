from unittest.mock import patch

from qstd_config.storage import InMemoryStorage, MultiprocessingStorage


def test_in_memory_storage():
    from fixtures.sample_config import AppConfig

    config = AppConfig(debug=False)
    storage = InMemoryStorage(config)

    assert storage.is_initialized is True
    assert storage.current().debug is False

    storage.update(AppConfig(debug=True))

    assert storage.current().debug is True


def test_multiprocessing_storage_main_process():
    from fixtures.sample_config import AppConfig

    config = AppConfig(debug=False)
    storage = MultiprocessingStorage(config)

    assert storage.is_initialized is False

    storage.init_storage({'config': config.model_dump(mode='json'), 'revision': 'xxx'})

    assert storage.is_initialized is True

    assert storage.current().debug is False

    storage.update(AppConfig(debug=True))

    assert storage.current().debug is True


def test_multiprocessing_storage_child_process():
    from fixtures.sample_config import AppConfig

    config = AppConfig(debug=False)
    storage = MultiprocessingStorage(config)

    assert storage.is_initialized is False

    with patch('qstd_config.utils.is_main_process', return_value=False):
        storage.init_storage({'config': config.model_dump(mode='json'), 'revision': 'xxx'})

    assert storage.is_initialized is True

    assert storage.current().debug is False

    storage.update(AppConfig(debug=True))

    assert storage.current().debug is True
