import typing

from pydantic import BaseModel

from qstd_config.logger import logger

from .base import ConfigStorageABC

T = typing.TypeVar('T', bound=BaseModel)


class InMemoryStorage(ConfigStorageABC[T], typing.Generic[T]):
    """
    In-memory storage backend for configuration.
    Does not require any setup and always remains ready.
    """

    @property
    def is_initialized(self) -> bool:
        """
        :return: Always True for in-memory storage.
        """
        return True

    def setup(self, **kwargs: typing.Any) -> None:
        """
        No initialization needed for in-memory storage.
        """
        pass

    def update(self, config: T) -> None:
        """
        Replace the stored config with a new Pydantic model.

        :param config: New configuration instance to store.
        """

        logger.debug('InMemoryStorage received config update')

        self._config = config

    def current(self) -> T:
        """
        Return the currently stored configuration.

        :return: The last value.
        """
        return self._config
