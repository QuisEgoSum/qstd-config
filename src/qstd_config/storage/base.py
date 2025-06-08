import abc
import typing

from pydantic import BaseModel

T = typing.TypeVar('T', bound=BaseModel)


class ConfigStorageABC(abc.ABC, typing.Generic[T]):
    """
    Abstract base class for configuration storage implementations.
    Provides the interface for updating and retrieving the current config.
    """

    _config: T

    def __init__(self, config: T) -> None:
        self._config = config

    @property
    @abc.abstractmethod
    def is_initialized(self) -> bool:
        """
        :return: True if setup() has been called (if required),
                 False if the storage is not yet ready to serve updates.
        """
        ...  # pragma: no cover

    @abc.abstractmethod
    def setup(self, **kwargs: typing.Any) -> None:
        """
        Perform any initialization required by this storage.

        :param kwargs: Named parameters required by this storage implementation.
        """
        ...  # pragma: no cover

    @abc.abstractmethod
    def update(self, config: T) -> None:
        """
        Store or broadcast a new configuration value.

        :param config: New Pydantic model instance to persist or share.
        """
        ...  # pragma: no cover

    @abc.abstractmethod
    def current(self) -> T:
        """
        Retrieve the current configuration instance.

        :return: The most recently stored Pydantic model.
        """
        ...  # pragma: no cover
