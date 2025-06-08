import os
import typing

from pydantic import BaseModel

from qstd_config import ConfigManager, InMemoryStorage, ProxyConfig


class AppConfig(BaseModel):
    debug: bool = False


class TypedProxyStub(ProxyConfig[AppConfig], AppConfig):
    """
    Optional typing stub for IDEs and static analyzers.

    Combines the ProxyConfig API (reload, setup, is_ready) with
    the AppConfig model fields, allowing you to treat the proxy
    as if it were a direct AppConfig instance in your code.

    This is purely for type‐checking and editor autocompletion;
    at runtime it still returns a regular ProxyConfig.
    """

    pass


manager: ConfigManager[AppConfig] = ConfigManager(
    AppConfig,
    project_name='example',
    config_paths=['./config.yaml'],
    default_config_values={
        'debug': False,
    },
    root_config_path=os.path.dirname(os.path.abspath(__file__)),
)

config: TypedProxyStub = typing.cast(TypedProxyStub, manager.get_proxy(InMemoryStorage))
