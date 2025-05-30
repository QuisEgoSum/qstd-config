import pytest

from qstd_config import ConfigManager, InMemoryStorage, ProxyConfig
from tests.fixtures.config import AppConfig


def test_proxy():
    manager = ConfigManager(AppConfig)
    proxy = manager.get_proxy(InMemoryStorage)

    assert isinstance(proxy, ProxyConfig)
    assert isinstance(proxy.config, AppConfig)
    assert isinstance(proxy.debug, bool)
    proxy.reload()
    assert proxy.is_ready is True
    proxy.setup()
    proxy.__repr__()
    proxy.__str__()

    with pytest.raises(AttributeError):
        proxy.unknown_field  # noqa: B018
