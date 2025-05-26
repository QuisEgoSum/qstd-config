import pytest

from qstd_config.proxy import ProxyConfig
from qstd_config.storage import InMemoryStorage

from fixtures.sample_config import AppConfig


def test_proxy_access():
    proxy: ProxyConfig[AppConfig] = ProxyConfig()
    with pytest.raises(RuntimeError):
        proxy.debug  # noqa: B018

    assert proxy.is_ready is False

    proxy.bind(InMemoryStorage(AppConfig(debug=True)))

    assert proxy.is_ready is True
    assert proxy.debug is True

    proxy.__repr__()
    proxy.__str__()
