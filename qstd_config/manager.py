import multiprocessing
import typing

from multiprocessing.managers import SyncManager

import yaml

from .base import BaseConfig
from .env import EnvironmentField, assign_env_to_dict, create_env_list_from_cls, render_env_help
from .proxy import ProxyConfig
from .storage import InMemoryStorage, MultiprocessingStorage, StorageABC
from .types import MultiprocessingContextType, ProjectMetadataType
from .utils import (
    cross_merge_dicts,
    get_override_config_paths_from_args,
    get_override_config_paths_from_env,
    is_main_process,
    resolve_config_path,
)

ConfigCLS = typing.TypeVar('ConfigCLS', bound=BaseConfig)
ProjectMetadata = typing.TypeVar('ProjectMetadata', bound=ProjectMetadataType)


class ConfigManager(typing.Generic[ConfigCLS, ProjectMetadata]):
    """
    High-level orchestrator for loading and managing configuration.
    Supports multiple sources (YAML, env), and optionally multiprocess-safe storage.
    """

    _config_cls: typing.Type[ConfigCLS]
    _storage_cls: typing.Type[StorageABC[ConfigCLS]]
    _project_metadata: ProjectMetadata
    _project_metadata_as: typing.Optional[str]
    _root_config_path: typing.Optional[str]
    _pre_validation_hook: typing.Optional[typing.Callable[[typing.Dict[str, typing.Any]], typing.Dict[str, typing.Any]]]
    _config_paths: typing.List[str]
    _multiprocessing_manager: typing.Optional[SyncManager]
    _multiprocessing_dict: typing.Optional[MultiprocessingContextType]
    _env_list: typing.List[EnvironmentField]
    _used_env: typing.List[str]

    _config: ProxyConfig[ConfigCLS]
    _storage: typing.Optional[StorageABC[ConfigCLS]]

    def __init__(
        self,
        config_cls: typing.Type[ConfigCLS],
        project_metadata: ProjectMetadata,
        *,
        project_metadata_as: typing.Optional[str] = None,
        storage: typing.Type[StorageABC[ConfigCLS]] = InMemoryStorage,
        config_paths: typing.Optional[typing.List[str]] = None,
        root_config_path: typing.Optional[str] = None,
        pre_validation_hook: typing.Optional[
            typing.Callable[[typing.Dict[str, typing.Any]], typing.Dict[str, typing.Any]]
        ] = None,
        parse_config_paths_from_args: bool = True,
        parse_config_paths_from_env: bool = True,
        multiprocessing_manager: typing.Optional[SyncManager] = None,
    ) -> None:
        """
        :param config_cls: Root Pydantic model that defines and validates the configuration structure
        :param project_metadata: Project metadata used in environment prefix and optionally injected into the config
        :param project_metadata_as: Key under which `project_metadata` will be included in the config. If `None`,
            metadata is not injected.
        :param storage: Storage implementation used for maintaining current config. Defaults to `InMemoryStorage`.
            Can be set to `MultiprocessingStorage` for multiprocess sharing
        :param config_paths: List of configuration file paths to load
        :param root_config_path: Root directory used to resolve relative config paths
        :param pre_validation_hook: Optional hook to modify raw configuration dict before
            validation (e.g., expand paths, inject secrets)
        :param parse_config_paths_from_args: If `True`, reads config file paths from CLI arguments `--config/-c`
        :param parse_config_paths_from_env: If `True`, reads config file paths from the environment variable
            `{PROJECT_NAME}_CONFIG`
        :param multiprocessing_manager: Optional custom multiprocessing manager. Used only with `MultiprocessingStorage`
        """

        self._config_cls = config_cls
        self._storage_cls = storage
        self._project_metadata = project_metadata
        self._project_metadata_as = project_metadata_as

        self._root_config_path = root_config_path
        self._pre_validation_hook = pre_validation_hook

        self._config_paths = self._load_config_paths(
            config_paths or [],
            parse_config_paths_from_args,
            parse_config_paths_from_env
        )

        if issubclass(storage, MultiprocessingStorage) and is_main_process():
            self._multiprocessing_manager = multiprocessing_manager or multiprocessing.Manager()
            self._multiprocessing_dict = self._create_multiprocessing_dict()
        else:
            self._multiprocessing_manager = None
            self._multiprocessing_dict = None

        self._env_list = create_env_list_from_cls(config_cls, self.get_project_name())

        self._config = ProxyConfig()
        self._storage = None
        self._used_env = []

    def get_project_name(self) -> typing.Optional[str]:
        return self._project_metadata['name']

    @property
    def used_env(self) -> typing.List[str]:
        return self._used_env

    @property
    def env_list(self) -> typing.List[EnvironmentField]:
        return list(self._env_list)

    def get_multiprocessing_context(self) -> MultiprocessingContextType:
        if not issubclass(self._storage_cls, MultiprocessingStorage):
            raise RuntimeError(
                "get_multiprocessing_context() is only available when using MultiprocessingStorage. "
                f"Current storage class: {self._storage_cls.__name__}"
            )
        return typing.cast(MultiprocessingContextType, self._multiprocessing_dict)

    def render_env_help(self) -> str:
        return render_env_help(self._env_list)

    def set_multiprocessing_context(self, context: MultiprocessingContextType) -> None:
        self._multiprocessing_dict = context
        if self._storage is not None and isinstance(self._storage, MultiprocessingStorage):
            self._storage.init_storage(self._multiprocessing_dict)

    def load_config_dict(
        self,
        config_dict: typing.Optional[typing.Dict[str, typing.Any]] = None
    ) -> typing.Dict[str, typing.Any]:
        """
        Loads raw config data from YAML files, env vars and project metadata.
        Returns a nested dict ready for Pydantic validation.
        """

        if config_dict is None:
            config_dict = {}

        if self._project_metadata_as is not None:
            config_dict[self._project_metadata_as] = self._project_metadata

        for config_path in self._config_paths:
            with open(resolve_config_path(config_path, self._root_config_path)) as file:
                override_config_dict: typing.Dict[str, typing.Any] = yaml.safe_load(file) or {}
                config_dict = cross_merge_dicts(config_dict, override_config_dict)

        self._used_env = assign_env_to_dict(config_dict, self._env_list)

        if self._pre_validation_hook is not None:
            config_dict = self._pre_validation_hook(config_dict)

        return config_dict

    def load_config_model(
        self,
        initial_data: typing.Optional[typing.Dict[str, typing.Any]] = None,
    ) -> ConfigCLS:
        """
        Loads and validates the configuration model, binds it to storage,
        and returns the proxy object for runtime access.

        :param initial_data:
        :return: Real type `ProxyConfig[ConfigCLS]`
        """

        config_dict = self.load_config_dict(initial_data)

        config = self._config_cls.model_validate(config_dict)

        self._update_storage(config)

        return typing.cast(ConfigCLS, self._config)

    def _create_multiprocessing_dict(self) -> MultiprocessingContextType:
        if self._multiprocessing_manager is None:
            raise RuntimeError('Multiprocessing manager is not initialized.')

        multiprocessing_dict = self._multiprocessing_manager.dict()

        # Initialize required keys to satisfy TypedDict; actual content will be set during storage initialization
        multiprocessing_dict['revision'] = 'xxx'
        multiprocessing_dict['config'] = {}

        return typing.cast(MultiprocessingContextType, multiprocessing_dict)

    def _load_config_paths(
        self,
        config_paths: typing.List[str],
        parse_config_paths_from_args: bool,
        parse_config_paths_from_env: bool,
    ) -> typing.List[str]:
        if parse_config_paths_from_env:
            config_paths.extend(get_override_config_paths_from_env(self.get_project_name(), self._root_config_path))

        if parse_config_paths_from_args:
            config_paths.extend(get_override_config_paths_from_args(self._root_config_path))

        return config_paths

    def _init_storage(self, config: ConfigCLS) -> None:
        self._storage = self._storage_cls(config)
        self._config.bind(self._storage)

        if (
            isinstance(self._storage, MultiprocessingStorage)
            and self._multiprocessing_dict is not None
        ):
            self._storage.init_storage(self._multiprocessing_dict)

    def _update_storage(self, config: ConfigCLS) -> None:
        if self._storage is None:
            self._init_storage(config)
        else:
            self._storage.update(config)
