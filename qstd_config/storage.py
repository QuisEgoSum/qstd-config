import abc
import os
import typing
import warnings

from qstd_config.base import BaseConfig
from qstd_config.types import MultiprocessingContextType
from qstd_config.utils import is_main_process

T = typing.TypeVar('T', bound=BaseConfig)


class StorageABC(abc.ABC, typing.Generic[T]):
    """
    Abstract base class for configuration storage implementations.
    Provides the interface for updating and retrieving the current config.
    """

    _value: T

    def __init__(self, value: T) -> None:
        self._value = value

    @abc.abstractmethod
    def update(self, value: T) -> None: ...

    @abc.abstractmethod
    def current(self) -> T: ...

    @property
    @abc.abstractmethod
    def is_initialized(self) -> bool: ...


class InMemoryStorage(StorageABC[T]):
    """
    Simple in-memory storage for configuration.
    Always initialized.
    """

    def update(self, value: T) -> None:
        self._value = value

    def current(self) -> T:
        return self._value

    @property
    def is_initialized(self) -> bool:
        return True


class MultiprocessingStorage(StorageABC[T]):
    """
    Multiprocessing-safe storage backed by a shared dictionary.
    Synchronizes configuration across processes using a revision-based mechanism.
    Needs to be initialized via `init_storage()` in spawned processes.
    """

    _value: T
    _multiprocessing_dict: typing.Optional[MultiprocessingContextType]
    _current_revision: typing.Optional[str]

    model_cls: typing.Type[T]

    def __init__(self, value: T) -> None:
        self._multiprocessing_dict = None
        self._current_revision = None
        self.model_cls = value.__class__
        super().__init__(value)

    @property
    def is_initialized(self) -> bool:
        return self._multiprocessing_dict is not None

    def init_storage(self, multiprocessing_dict: MultiprocessingContextType) -> None:
        """
        Binds the shared multiprocessing dictionary to the storage instance.
        Must be called explicitly in spawned processes.
        """

        self._multiprocessing_dict = multiprocessing_dict
        if is_main_process():
            self._multiprocessing_dict['config'] = self._value.model_dump(mode='json')
            self._multiprocessing_dict['revision'] = os.urandom(16).hex()

    def update(self, value: T) -> None:
        if self._multiprocessing_dict is None:
            raise RuntimeError('MultiprocessingStorage not initialized yet')
        self._multiprocessing_dict['config'] = value.model_dump(mode='json')
        self._multiprocessing_dict['revision'] = os.urandom(16).hex()

    def current(self) -> T:
        """
        Returns the current configuration instance.
        If shared dict is updated (revision mismatch), re-parses from JSON.
        """

        if self._multiprocessing_dict is None:
            warnings.warn(
                "MultiprocessingStorage used before initialization. "
                "Configuration will not be shared across processes until "
                "set_multiprocessing_context() is called.",
                RuntimeWarning,
                stacklevel=2
            )
            return self._value
        rev = self._multiprocessing_dict.get('revision')
        if rev != self._current_revision:
            self._value = self.model_cls.model_validate(self._multiprocessing_dict['config'])
            self._current_revision = rev
        return self._value
