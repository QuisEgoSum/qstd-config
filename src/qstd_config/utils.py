import argparse
import os
import typing

from pathlib import Path

from qstd_config.exceptions import FileNotExistsError
from qstd_config.loader.utils import to_env_name


def resolve_config_path(path: str, base_path: typing.Optional[str]) -> Path:
    """
    Resolves a config path relative to a base directory, unless it is already absolute.
    """

    if base_path is not None and not path.startswith('/'):
        return Path(base_path) / path
    return Path(path)


def validate_files_exist(file_paths: typing.List[Path]) -> None:
    """
    Raise FileNotExistsError if any file in the list does not exist.

    :param file_paths: Iterable of Path instances to check.
    :raises FileNotExistsError: If any file is missing.
    """

    missing = [path for path in file_paths if not path.exists()]
    if missing:
        raise FileNotExistsError(missing)


def get_config_paths_from_env(
    project_name: typing.Optional[str],
    root_path: typing.Optional[str],
) -> typing.List[Path]:
    """
    Retrieve configuration file paths from environment variables.

    If `project_name` is provided, looks for `{PROJECT_NAME}_CONFIG`.
    Otherwise, defaults to `CONFIG`.

    Multiple paths can be separated by a semicolon (`;`).
    Each path is resolved via `resolve_config_path()`.

    :param project_name: Optional project name to prefix the env var.
    :param root_path: Optional base path to resolve relative paths.
    :return: List of resolved config file paths.
    """

    paths: typing.List[Path] = []

    env_name = (
        'CONFIG' if project_name is None else f'{to_env_name(project_name)}_CONFIG'
    )
    env_paths = os.environ.get(env_name)

    if env_paths:
        for env_path in env_paths.split(';'):
            paths.append(resolve_config_path(env_path, root_path))

    return paths


def get_config_paths_from_args(root_path: typing.Optional[str]) -> typing.List[Path]:
    """
    Retrieve configuration file paths from CLI arguments.

    Expects `--config` or `-c` argument. Multiple paths may be separated by `;`.
    Parses only known arguments (`argparse.parse_known_args()`), making it safe
    to use alongside other CLI parsers.

    Each path is resolved via `resolve_config_path()`.

    :param root_path: Optional base path to resolve relative paths.
    :return: List of resolved config file paths.
    """

    paths: typing.List[Path] = []

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config',
        '-c',
        type=str,
        help='The path to the application configuration file',
    )

    argument_paths = parser.parse_known_args()[0].config

    if argument_paths:
        for argument_path in argument_paths.split(';'):
            paths.append(resolve_config_path(argument_path, root_path))

    return paths


def get_config_paths(
    base_paths: typing.Optional[typing.List[str]],
    parse_config_paths_from_env: bool,
    parse_config_paths_from_args: bool,
    project_name: typing.Optional[str],
    root_config_path: typing.Optional[str],
) -> typing.List[Path]:
    """
    Compose and validate configuration file paths from multiple sources.

    Sources (in order of precedence):
      - `base_paths` (user-provided list)
      - environment variables (`{PROJECT_NAME}_CONFIG` or `CONFIG`)
      - command-line arguments (`--config`, `-c`)

    All paths are resolved relative to `root_config_path`, if provided.
    After resolution, each file path is checked for existence.

    :param base_paths: List of direct paths (or None).
    :param parse_config_paths_from_env: Whether to include env-defined paths.
    :param parse_config_paths_from_args: Whether to include CLI-provided paths.
    :param project_name: Used to form env var name.
    :param root_config_path: Optional root for resolving relative paths.
    :return: List of existing config file paths.
    :raises FileNotExistsError: If any resolved path does not exist.
    """

    config_paths: typing.List[Path] = []

    if base_paths is not None:
        config_paths.extend(
            resolve_config_path(config_path, root_config_path)
            for config_path in base_paths
        )

    if parse_config_paths_from_env:
        config_paths.extend(get_config_paths_from_env(project_name, root_config_path))

    if parse_config_paths_from_args:
        config_paths.extend(get_config_paths_from_args(root_config_path))

    validate_files_exist(config_paths)

    return config_paths
