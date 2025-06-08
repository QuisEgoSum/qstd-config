import typing

from pydantic import BaseModel

from .storage.base import ConfigStorageABC

if typing.TYPE_CHECKING:  # pragma: no cover
    from .manager import ConfigManager

T = typing.TypeVar('T', bound=BaseModel)


class ProxyConfig(typing.Generic[T]):
    """
    Proxy for safe and lazy access to configuration.
    Delegates attribute access to the bound storage's current config instance.
    Provides methods to reload and setup the underlying storage.
    """

    _manager: "ConfigManager[T]"
    _storage: ConfigStorageABC[T]

    def __init__(
        self,
        manager: "ConfigManager[T]",
        storage: ConfigStorageABC[T],
    ) -> None:
        """
        Initialize the proxy with a ConfigManager and a storage backend.

        :param manager: The ConfigManager responsible for loading and validating config.
        :param storage: The storage backend implementing ConfigStorageABC.
        """

        self._manager = manager
        self._storage = storage

    def __getattr__(self, item: str):
        # Delegate attribute access to the underlying config model
        return getattr(self._storage.current(), item)

    def __repr__(self) -> str:
        # Represent as the underlying config model
        return self._storage.current().__repr__()

    def __str__(self) -> str:
        # Stringify as the underlying config model
        return self._storage.current().__str__()

    @property
    def config(self) -> T:
        """
        Return the current configuration model instance.

        :return: The latest Pydantic model returned by storage.current().
        """
        return self._storage.current()

    @property
    def is_ready(self) -> bool:
        """
        Check if the storage backend has been initialized.

        :return: True if storage.setup() has been called; False otherwise.
        """

        return self._storage.is_initialized

    def reload(self) -> None:
        """
        Reload the configuration from all sources and update the storage.

        :raises InvalidFileContentError: if the parsed file is not a dict.
        """

        config = self._manager.load_config_model()
        self._storage.update(config)

    def setup(self, **kwargs: typing.Any) -> None:
        """
        Initialize the storage backend with given parameters.

        :param kwargs: Parameters to pass to storage.setup(), e.g., multiprocessing_dict.
        """

        self._storage.setup(**kwargs)
