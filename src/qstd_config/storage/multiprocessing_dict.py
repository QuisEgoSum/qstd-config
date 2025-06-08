import multiprocessing
import os
import typing
import warnings

from multiprocessing.managers import SyncManager

from pydantic import BaseModel

from qstd_config.exceptions import (
    MultiprocessingStorageNotInitializedWarning,
    MultiprocessingStorageReinitWarning,
    StorageNotInitializedError,
)
from qstd_config.logger import logger
from qstd_config.storage.types import MultiprocessingContextType

from .base import ConfigStorageABC

T = typing.TypeVar('T', bound=BaseModel)


class MultiprocessingDictStorage(ConfigStorageABC[T], typing.Generic[T]):
    """
    Storage that shares configuration across processes using a multiprocessing.Manager dict.

    In the main process:
      ctx = MultiprocessingDictStorage.create_shared_context()
      config = manager.get_proxy(MultiprocessingDictStorage)
      config.setup(multiprocessing_dict=ctx)

    In worker processes:
      config = manager.get_proxy(MultiprocessingDictStorage)
      config.setup(multiprocessing_dict=ctx)
    """

    _multiprocessing_dict: typing.Optional[MultiprocessingContextType]
    _model_cls: typing.Type[T]
    _current_revision: typing.Optional[str]

    def __init__(self, config: T) -> None:
        super().__init__(config)

        self._model_cls = config.__class__
        self._multiprocessing_dict = None
        self._current_revision = None

    @property
    def is_initialized(self) -> bool:
        """
        :return: True once setup() has been called successfully.
        """
        return self._multiprocessing_dict is not None

    def setup(
        self,
        *,
        multiprocessing_dict: MultiprocessingContextType,
        **_: typing.Any,
    ) -> None:
        """
        Bind a shared context dict to this storage instance.

        :param multiprocessing_dict: Shared dict created by create_shared_context().
        """

        if multiprocessing_dict['initialized'] is False:
            revision = os.urandom(16).hex()

            logger.debug(
                'Initializing shared config in multiprocessing dict. Revision: %s',
                revision,
            )

            multiprocessing_dict['initialized'] = True
            multiprocessing_dict['config'] = self._config.model_dump(mode='json')
            multiprocessing_dict['revision'] = revision

        if self._multiprocessing_dict is not None:
            # It is recommended to call `setup()` only once per process.
            # (Prefer initializing the storage inside the process entry point,
            # rather than at the global module level.)
            # To disable this warning:
            #     warnings.filterwarnings("ignore", category=MultiprocessingStorageReinitWarning)
            warnings.warn(
                'MultiprocessingStorage reinitialized.',
                MultiprocessingStorageReinitWarning,
                stacklevel=2,
            )

        revision = multiprocessing_dict.get('revision')

        logger.debug(
            'Binding shared multiprocessing dict to local storage instance. Revision: %s',
            revision,
        )

        self._multiprocessing_dict = multiprocessing_dict

    def update(self, config: T) -> None:
        """
        Push a new configuration to all processes via the shared dict.

        :param config: New Pydantic model instance to broadcast.
        :raises ConfigError: If setup() has not been called yet.
        """

        if self._multiprocessing_dict is None:
            raise StorageNotInitializedError(
                'MultiprocessingStorage not initialized yet',
            )

        revision = os.urandom(16).hex()

        logger.debug(
            "Broadcasting new config to multiprocessing dict. Revision: %s",
            revision,
        )

        self._multiprocessing_dict['config'] = config.model_dump(mode='json')
        self._multiprocessing_dict['revision'] = revision

    def current(self) -> T:
        """
        Retrieve the current config. Lazily reloads if revision has changed.

        :return: Latest Pydantic model instance.
        :raises Warning: If called before setup(), returns local copy.
        """

        if self._multiprocessing_dict is None:
            # It is recommended not to access the configuration before `setup()` has been called.
            # However, doing so is allowed if you intentionally use config values
            # during the initialization of global modules — for example,
            # configuring a logger that relies on config settings before full initialization.
            # To disable this warning:
            #     warnings.filterwarnings("ignore", category=MultiprocessingStorageNotInitializedWarning)
            warnings.warn(
                'MultiprocessingStorage not initialized; returning local config.',
                MultiprocessingStorageNotInitializedWarning,
                stacklevel=2,
            )
            return self._config

        rev = self._multiprocessing_dict.get('revision')

        if rev != self._current_revision:

            logger.debug(
                "Detected revision change, reloading config from shared memory. Revision: %s",
                rev,
            )

            self._config = self._model_cls.model_validate(
                self._multiprocessing_dict['config'],
            )
            self._current_revision = rev

        return self._config

    @staticmethod
    def create_shared_context(
        *,
        manager: typing.Optional[SyncManager] = None,
    ) -> MultiprocessingContextType:
        """
        Create a shared dict for use by all processes.

        :param manager: Optional custom multiprocessing.Manager instance.
                        If None, a new Manager() is created.
        :return: A MultiprocessingContextType dict with initial fields.
        """

        multiprocessing_dict: MultiprocessingContextType = typing.cast(
            MultiprocessingContextType,
            (manager or multiprocessing.Manager()).dict(),
        )

        multiprocessing_dict['initialized'] = False
        multiprocessing_dict['config'] = {}
        multiprocessing_dict['revision'] = os.urandom(16).hex()

        return multiprocessing_dict
