import abc
import typing

from pathlib import Path

from pydantic import BaseModel

from qstd_config.merge_strategy.base import ConfigMergeStrategyProtocol

from .env_field import EnvironmentField

T = typing.TypeVar('T', bound='ConfigLoaderABC')


class ConfigLoaderABC(abc.ABC):
    """
    Abstract base class defining the interface for configuration loaders.

    Responsible only for reading raw data, without validation or type conversion.
    """

    @abc.abstractmethod
    def load(self) -> typing.MutableMapping[str, typing.Any]:
        """
        Loads raw configuration data from the specified source.

        :return:
        """
        ...  # pragma: no cover


class EnvLoaderABC(ConfigLoaderABC, abc.ABC):
    """
    Abstract base class for configuration loaders that read from environment variables.
    """

    _model: typing.Type[BaseModel]
    _prefix: typing.Optional[str]

    def __init__(
        self,
        *,
        model: typing.Type[BaseModel],
        prefix: typing.Optional[str],
    ) -> None:
        """

        :param model: The Pydantic model class defining the configuration schema.
        :param prefix: Optional prefix for environment variable names (without trailing "_");
                       automatically normalized, e.g. "app" -> "APP_"
        """
        self._model = model
        self._prefix = prefix

    @property
    @abc.abstractmethod
    def env_list(self) -> typing.List[EnvironmentField]:
        """
        :return: Returns the list of all environment variables (`EnvironmentField`) derived from the model fields.
        """
        ...  # pragma: no cover

    @property
    @abc.abstractmethod
    def used_env_list(self) -> typing.List[EnvironmentField]:
        """
        :return: Returns the list of `EnvironmentField` objects that were actually applied during the last load call.
        """
        ...  # pragma: no cover

    @abc.abstractmethod
    def render_env_help(self) -> str:
        """
        Generates a human-readable --help-like block for environment variables.

        Example output:
            APP_DB_HOST (str) - Database host. Default: "localhost"
            APP_DEBUG (bool) - Enables debug mode.

        :return:
        """
        ...  # pragma: no cover


class SingleFileLoaderProtocol(typing.Protocol):
    """
    Protocol for loaders of a single configuration file.
    """

    def supported_extensions(self) -> typing.Sequence[str]:
        """
        :return: Returns the list of supported file extensions (including the leading dot), e.g. ‘.json’, ‘.yaml’.
        """
        ...  # pragma: no cover

    def is_supported(self, path: Path) -> bool:
        """
        Checks whether this loader supports the given file path.

        :param path:
        :return:
        """
        ...  # pragma: no cover

    def load(self, path: Path) -> typing.MutableMapping[str, typing.Any]:
        """
        Reads the specified file and returns its contents as a raw data dict.

        :param path:
        :return:
        """
        ...  # pragma: no cover


class FileLoaderABC(ConfigLoaderABC, abc.ABC):
    """
    Abstract base class for loading and merging configuration from multiple files.
    """

    _paths: typing.List[Path]
    _file_loaders: typing.List[SingleFileLoaderProtocol]
    _merge_strategy: ConfigMergeStrategyProtocol

    def __init__(
        self,
        *,
        paths: typing.List[Path],
        file_loaders: typing.List[SingleFileLoaderProtocol],
        merge_strategy: ConfigMergeStrategyProtocol,
    ):
        """

        :param paths: List of file paths to load.
        :param file_loaders: List of `SingleFileLoader` instances in priority order.
        :param merge_strategy: Strategy for merging the results of individual file loads.
        """

        self._paths = paths
        self._file_loaders = file_loaders
        self._merge_strategy = merge_strategy

    @abc.abstractmethod
    def load(self) -> typing.MutableMapping[str, typing.Any]:
        """
        Loads and merges configuration from all specified file paths: for each path, selects the first supporting
        SingleFileLoader, invokes its load(), and then merges the results using the configured merge strategy.

        :return:
        """
        ...  # pragma: no cover


class CustomLoaderABC(ConfigLoaderABC, abc.ABC):
    """
    Abstract base class for custom loaders from arbitrary sources (Redis, HTTP, etc.).
    """

    @abc.abstractmethod
    def load(self) -> typing.MutableMapping[str, typing.Any]:
        """
        Loads the configuration from the custom source and returns it as a raw data dict.

        :return:
        """
        ...  # pragma: no cover


class ChainLoaderABC(ConfigLoaderABC, abc.ABC):
    """
    Abstract base class for composing multiple configuration loaders into a single pipeline.

    This loader delegates to a sequence of sub-loaders (e.g. `EnvLoader`, `FileLoader`, `CustomLoader`),
    invokes each one's `load()` method in order, and merges their outputs using the specified
    `ConfigMergeStrategy`.
    """

    _loaders: typing.List[ConfigLoaderABC]
    _merge_strategy: ConfigMergeStrategyProtocol

    def __init__(
        self,
        *,
        loaders: typing.List[ConfigLoaderABC],
        merge_strategy: ConfigMergeStrategyProtocol,
    ):
        """
        :param loaders: A list of ConfigLoaderABC instances to be executed in sequence.
        :param merge_strategy: Strategy used to merge the dict results of individual loaders.
        """

        self._loaders = loaders
        self._merge_strategy = merge_strategy

    @abc.abstractmethod
    def load(self) -> typing.MutableMapping[str, typing.Any]:
        """
        Executes each loader in the configured sequence and merges their outputs.

        :return: Combined configuration dict from all loaders.
        """
        ...  # pragma: no cover

    @abc.abstractmethod
    def get_loader(self, loader_cls: typing.Type[T]) -> typing.Optional[T]:
        """
        Retrieves the first loader in the chain that is an instance of the specified class.

        :param loader_cls: The loader class to look for (e.g. EnvLoaderABC).
        :return: The first matching loader instance, or None if not found.
        """
        ...  # pragma: no cover
