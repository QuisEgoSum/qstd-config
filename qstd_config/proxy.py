import typing

from .base import BaseConfig
from .storage import StorageABC

T = typing.TypeVar('T', bound=BaseConfig)


class ProxyConfig(typing.Generic[T]):
    """
    A proxy object for safe and lazy access to the configuration.
    Defers all attribute access to the bound storage's current config instance.
    """

    _storage: typing.Optional[StorageABC[T]]

    def __init__(self) -> None:
        self._storage = None

    def bind(self, storage: StorageABC[T]) -> None:
        """
        Binds a storage instance to the proxy.
        Can only be called once.
        """

        if self._storage is not None:
            raise RuntimeError('Config storage is already bound')
        self._storage = storage

    @property
    def is_ready(self) -> bool:
        """
        Returns whether the proxy has been successfully bound and initialized.
        """

        return self._storage is not None and self._storage.is_initialized

    def __getattr__(self, item: str):
        if self._storage is None:
            raise RuntimeError('Config not initialized yet')
        return getattr(self._storage.current(), item)

    def __repr__(self) -> str:
        return self._storage.current().__repr__() if self._storage is not None else 'Config not initialized yet'

    def __str__(self) -> str:
        return self._storage.current().__str__() if self._storage is not None else 'Config not initialized yet'
