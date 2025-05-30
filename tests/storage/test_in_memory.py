from qstd_config import InMemoryStorage
from tests.fixtures.config import AppConfig


def test_in_memory_storage():
    storage = InMemoryStorage(AppConfig())

    assert storage.is_initialized
    assert isinstance(storage.current(), AppConfig)

    assert storage.current().debug is False

    storage.update(AppConfig(debug=True))

    assert storage.current().debug is True
