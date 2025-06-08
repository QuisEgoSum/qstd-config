import typing

from pathlib import Path

from pydantic import BaseModel, ValidationError

from . import CustomLoaderABC
from .exceptions import ConfigValidationError
from .loader.base import ChainLoaderABC, EnvLoaderABC
from .loader.env_field import EnvironmentField
from .loader.factory import default_chain_loader_factory
from .merge_strategy import DeepMergeStrategy
from .merge_strategy.base import ConfigMergeStrategyProtocol
from .proxy import ProxyConfig
from .storage.base import ConfigStorageABC
from .utils import get_config_paths

T = typing.TypeVar('T', bound=BaseModel)


class ConfigManager(typing.Generic[T]):
    """
    High-level orchestrator that loads, validates, merges, and provides
    access to a Pydantic-based configuration.

    It builds a chain of loaders (environment, files, custom),
    merges their raw outputs according to a strategy, validates
    the result against the Pydantic model, and exposes both
    direct model access and proxy-based hot-reload/storage APIs.
    """

    _config_cls: typing.Type[T]
    _project_name: typing.Optional[str]
    _pre_validation_hook: typing.Optional[
        typing.Callable[
            [typing.MutableMapping[str, typing.Any]],
            typing.MutableMapping[str, typing.Any],
        ]
    ]
    _config_paths: typing.List[Path]
    _default_config_values: typing.Dict[str, typing.Any]
    _merge_strategy: ConfigMergeStrategyProtocol
    _chain_loader: ChainLoaderABC

    def __init__(
        self,
        config_cls: typing.Type[T],
        *,
        project_name: typing.Optional[str] = None,
        config_paths: typing.Optional[typing.List[str]] = None,
        root_config_path: typing.Optional[str] = None,
        pre_validation_hook: typing.Optional[
            typing.Callable[
                [typing.MutableMapping[str, typing.Any]],
                typing.MutableMapping[str, typing.Any],
            ]
        ] = None,
        parse_config_paths_from_args: bool = True,
        parse_config_paths_from_env: bool = True,
        default_config_values: typing.Optional[typing.Dict[str, typing.Any]] = None,
        custom_loaders: typing.Optional[typing.List[CustomLoaderABC]] = None,
        chain_loader_factory: typing.Callable[
            [
                typing.Type[T],
                typing.List[Path],
                typing.Optional[str],
                ConfigMergeStrategyProtocol,
                typing.List[CustomLoaderABC],
            ],
            ChainLoaderABC,
        ] = default_chain_loader_factory,
        merge_strategy: ConfigMergeStrategyProtocol = DeepMergeStrategy(),
    ) -> None:
        """
        Initialize the configuration manager.

        :param config_cls:        Pydantic BaseModel subclass defining the config schema.
        :param project_name:      Optional name used as prefix for env vars and for parsing ENV-based config paths.
        :param config_paths:      Explicit list of config file paths (strings) to load.
        :param root_config_path:  Base directory to resolve relative file paths.
        :param pre_validation_hook:
                                  Optional hook to transform the merged raw dict
                                  before Pydantic validation (e.g., inject secrets).
        :param parse_config_paths_from_args:
                                  If True, read additional file paths from CLI `--config`/`-c` arguments.
        :param parse_config_paths_from_env:
                                  If True, read additional file paths from ENV var `{PROJECT_NAME}_CONFIG`.
        :param default_config_values:
                                  Default raw values (dict) to seed the merge as the base.
        :param chain_loader_factory:
                                  Factory to construct the ChainLoader;
                                  receives (model, paths, project_name, strategy, custom_loaders).
        :param merge_strategy:    Strategy to merge raw dicts from each loader.
        :raise FileNotExistsError: If any file is missing.
        """

        self._config_cls = config_cls
        self._project_name = project_name
        self._pre_validation_hook = pre_validation_hook

        self._config_paths = get_config_paths(
            base_paths=config_paths,
            parse_config_paths_from_args=parse_config_paths_from_args,
            parse_config_paths_from_env=parse_config_paths_from_env,
            project_name=project_name,
            root_config_path=root_config_path,
        )
        self._default_config_values = default_config_values or {}
        self._merge_strategy = merge_strategy
        self._chain_loader = chain_loader_factory(
            config_cls,
            self._config_paths,
            self._project_name,
            merge_strategy,
            (custom_loaders or []),
        )

    @property
    def config_paths(self) -> typing.List[Path]:
        """
        Return the list of resolved configuration file paths.

        These paths are determined during initialization using the `config_paths` argument,
        environment variables, or CLI arguments — in that priority order.

        :return: A list of absolute file paths used to load configuration.
        """

        return list(self._config_paths)

    @property
    def used_env_list(self) -> typing.List[EnvironmentField]:
        """
        :return: EnvironmentFields that were actually applied (present in ENV)
                 during the last load() call.
        """

        loader = self._chain_loader.get_loader(EnvLoaderABC)
        return loader.used_env_list if loader else []

    @property
    def env_list(self) -> typing.List[EnvironmentField]:
        """
        :return: All possible EnvironmentField entries derived from the model,
                 regardless of whether they were set.
        """

        loader = self._chain_loader.get_loader(EnvLoaderABC)
        return loader.env_list if loader else []

    def load_config_dict(self) -> typing.Dict[str, typing.Any]:
        """
        Execute the loader chain to obtain a merged raw configuration `dict`,
        applying default values and an optional pre-validation hook.

        :return: Final raw configuration dict ready for Pydantic validation.
        :raises InvalidFileContentError: if the parsed file is not a dict.
        """

        raw_override = self._chain_loader.load()
        merged = self._merge_strategy.merge(
            dict(self._default_config_values),
            raw_override,
        )
        if self._pre_validation_hook:
            merged = self._pre_validation_hook(merged)
        return dict(merged)

    def load_config_model(self) -> T:
        """
        Validate and instantiate the Pydantic model from the merged raw `dict`.

        :return: A fully validated instance of the config model.
        :raises InvalidFileContentError: if the parsed file is not a dict.
        """

        raw = self.load_config_dict()
        try:
            return self._config_cls.model_validate(raw)
        except ValidationError as ex:
            raise ConfigValidationError(ex) from ex

    def get_proxy(
        self,
        storage_cls: typing.Type[ConfigStorageABC[T]],
    ) -> ProxyConfig[T]:
        """
        Create a ProxyConfig bound to the given storage backend.

        :param storage_cls: A subclass of ConfigStorageABC to wrap the model.
                            For hot-reload or multiprocess support, choose accordingly.
        :return: A ProxyConfig that delegates attribute access to the storage.
        :raises InvalidFileContentError: if the parsed file is not a dict.
        """

        model_instance = self.load_config_model()
        storage = storage_cls(model_instance)
        return ProxyConfig(self, storage)

    def render_env_help(self) -> typing.Optional[str]:
        """
        Generate a human-readable help text for environment variables,
        listing name, type, description, and defaults.

        :return: Multiline help string or None if no EnvLoader is present.
        """

        loader = self._chain_loader.get_loader(EnvLoaderABC)
        return loader.render_env_help() if loader else None
