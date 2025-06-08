import json
import typing

from pathlib import Path

import yaml

from qstd_config.exceptions import InvalidFileContentError, UnsupportedFileTypeError
from qstd_config.logger import logger

from .base import FileLoaderABC, SingleFileLoaderProtocol
from .file_loader_registry import DEFAULT_INTERNAL_LOADER_PRIORITY, register_file_loader


class YamlFileLoader(SingleFileLoaderProtocol):
    """
    Loads a single YAML configuration file and returns its contents as a dict.
    """

    def supported_extensions(self) -> typing.Sequence[str]:
        """
        Return supported extensions: ['.yaml', '.yml'].

        :return: List of supported extensions including leading dot.
        """

        return ['.yaml', '.yml']

    def is_supported(self, path: Path) -> bool:
        """
        Check if this loader can handle the given file based on its extension.

        :param path: Path to the configuration file to check.
        :return: True if the file has a supported YAML extension.
        """

        return path.suffix.lower() in self.supported_extensions()

    def load(self, path: Path) -> typing.MutableMapping[str, typing.Any]:
        """
        Read the YAML file at `path`, parse with safe_load,
        and return a dict (empty if file is blank).

        :param path: Path to the YAML file to load.
        :return: Parsed contents as a raw dict.
        :raises InvalidFileContentError: if the parsed value is not a dict.
        """

        logger.debug('Reading config file: %s', path)

        with open(path) as f:
            data: typing.Optional[typing.Dict[str, typing.Any]] = (
                yaml.safe_load(f) or {}
            )
            if not isinstance(data, dict):
                raise InvalidFileContentError(path, type(data))
            return data


class JsonFileLoader(SingleFileLoaderProtocol):
    """
    Loader for JSON files (.json).
    Parses with `json.load` and returns a dict.
    """

    def supported_extensions(self) -> typing.Sequence[str]:
        """
        :return: List of supported extensions: ['.json'].
        """

        return ['.json']

    def is_supported(self, path: Path) -> bool:
        """
        Check if this loader can handle the given file based on its extension.

        :param path: Path to the configuration file to check.
        :return: True if the file has a supported JSON extension.
        """

        return path.suffix.lower() in self.supported_extensions()

    def load(self, path: Path) -> typing.MutableMapping[str, typing.Any]:
        """
        Read the JSON file at `path`, parse with `json.load`, and return a dict.

        :param path: Path to the JSON file to load.
        :return: Parsed contents as a raw dict.
        :raises InvalidFileContentError: if the parsed value is not a dict.
        """

        logger.debug('Reading config file: %s', path)

        with open(path) as f:
            data: typing.Optional[typing.Dict[str, typing.Any]] = json.load(f)
            if not isinstance(data, dict):
                raise InvalidFileContentError(path, type(data))
            return data


class FileLoader(FileLoaderABC):
    """
    Aggregates multiple SingleFileLoaderProtocol instances to
    load configuration from a list of file paths and merge them.
    """

    def load(self) -> typing.MutableMapping[str, typing.Any]:
        """
        Sequentially load each file via the first supporting loader,
        merge the resulting dicts, and return the combined config.

        :raises RuntimeError: if no loader supports a given file extension.
        :return: Merged configuration dict from all files.
        """

        base: typing.MutableMapping[str, typing.Any] = {}
        for path in self._paths:
            for loader in self._file_loaders:
                if loader.is_supported(path):
                    override = loader.load(path)
                    base = self._merge_strategy.merge(base, override)
                    break
            else:
                raise UnsupportedFileTypeError(path)
        return base


register_file_loader(YamlFileLoader(), priority=DEFAULT_INTERNAL_LOADER_PRIORITY)
register_file_loader(JsonFileLoader(), priority=DEFAULT_INTERNAL_LOADER_PRIORITY)
