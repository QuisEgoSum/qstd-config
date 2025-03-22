import multiprocessing
import os
import typing
from pathlib import Path

import yaml
from pydantic import BaseModel

from . import utils
from .config import BaseConfig, InMemoryConfig, MultiprocessingConfig


T = typing.TypeVar('T', bound=BaseConfig)


class ProjectMetadata(typing.TypedDict):
    name: str


class ConfigManager:
    """
    Manages the loading and merging of configuration data from multiple sources.

    The `ConfigManager` class is responsible for loading configuration data from various
    paths, including files, environment variables, and arguments. It also handles the
    merging of configuration data and supports pre-validation hooks to modify the
    configuration before validation.

    The configuration is then validated using Pydantic models, and the final configuration
    object is created, which can include nested configuration structures.

    Attributes:
        config_cls (Type[T]): The configuration class that defines the structure and validation rules.
        project_metadata (Optional[ProjectMetadata]): Metadata about the project, such as the project name.
        project_metadata_as_config_property (Optional[str]): The name of the config property for project metadata.
        config_paths (List[str]): A list of paths to configuration files.
        default_config_dir (str): The default directory for configuration files.
        pre_validation_hook (Optional[Callable[[dict], dict]]): A hook to modify the configuration before validation.
        used_env (List[str]): A list of environment variables used to populate the configuration.
    """

    def __init__(
        self,
        config_cls: typing.Type[T],
        *,
        project_metadata: typing.Optional[typing.Union[ProjectMetadata, typing.Dict]] = None,
        project_metadata_as: typing.Optional[str] = None,

        default_config_dir: typing.Optional[str] = None,
        config_paths: typing.List[str] = None,
        pre_validation_hook: typing.Optional[typing.Callable[[dict], dict]] = None,
        parse_config_paths_from_args: bool = True,
        parse_config_paths_from_env: bool = True,

        multiprocessing_manager: typing.Optional[multiprocessing.Manager] = None
    ):
        self.config_cls = config_cls

        self.project_metadata = project_metadata
        self.project_metadata_as_config_property = project_metadata_as

        self.default_config_dir = default_config_dir or Path.cwd().__str__()
        self.config_paths = config_paths or []
        self.pre_validation_hook = pre_validation_hook
        self.used_env = []
        if config_paths:
            self.config_paths.extend([self.abs_config_path(path) for path in config_paths])
        if parse_config_paths_from_env:
            self.config_paths.extend(self.get_override_config_paths_from_env())
        if parse_config_paths_from_args:
            self.config_paths.extend(self.get_override_config_paths_from_args())
        project_name = self.get_project_name()
        env_parts = []
        if project_name:
            env_parts.append(project_name)

        self._multiprocessing_manager = multiprocessing_manager
        self._multiprocessing_dict = None

        self._config = None

    def config_factory(self, valid_configuration: BaseModel):
        if issubclass(self.config_cls, InMemoryConfig):
            return self.config_cls(valid_configuration)
        elif issubclass(self.config_cls, MultiprocessingConfig):
            self._multiprocessing_dict = (self._multiprocessing_manager or multiprocessing.Manager()).dict()
            return self.config_cls(valid_configuration, multiprocessing_dict=self._multiprocessing_dict)
        else:
            raise Exception('Unsupported config class')

    def load_configuration(self, configuration: typing.Optional[dict] = None) -> T:
        """
        Loads the configuration by merging values from multiple sources: configuration
        files, environment variables, and project metadata. It also validates and maps the
        data to the provided configuration class.

        The configuration application order (from lowest to highest):
        - Default data passed to the method
        - Configuration files passed to the class constructor
        - Configuration files passed via environment variable
        - Configuration files passed via argument
        - Parameters defined through environment variables.

        Args:
            configuration (dict, optional): A dictionary of configuration data to override
                                             the default (empty by default).

        Returns:
            T: The loaded and validated configuration object.
        """
        if configuration is None:
            configuration = dict()
        if self.project_metadata and self.project_metadata_as_config_property:
            configuration[self.project_metadata_as_config_property] = self.project_metadata
        for config_path in self.config_paths:
            with open(config_path, 'r') as file:
                override_config_dict = yaml.safe_load(file) or dict()
                configuration = utils.cross_merge_dicts(configuration, override_config_dict)
        self.used_env = self.assign_env_to_dict(configuration)
        if self.pre_validation_hook is not None:
            configuration = self.pre_validation_hook(configuration)
        valid_configuration = self.config_cls.__qstd_pydantic_cls__.model_validate(configuration)
        if self._config is None:
            self._config = self.config_factory(valid_configuration)
        else:
            self._config.__update_configuration__(valid_configuration)
        return self._config

    def assign_env_to_dict(self, configuration: dict):
        """
        Maps environment variables to the configuration dictionary.

        Args:
            configuration (dict): The current configuration dictionary to be updated.

        Returns:
            list: A list of environment variables that were used to populate the configuration.
        """
        used_env = []
        project_name = self.get_project_name()
        if project_name is not None:
            project_name = utils.unify_name(project_name)
        for config_property in self.config_cls.__qstd_configuration_properties__:
            env = config_property.env
            if project_name:
                env = '_'.join([project_name, env])
            value = os.environ.get(env, None)
            if value is None:
                continue
            current_value = configuration
            last_index = len(config_property.path)
            for index, key in enumerate(config_property.path):
                if index == last_index:
                    current_value[key] = value
                else:
                    if key not in current_value:
                        current_value[key] = dict()
                    current_value = current_value[key]
            used_env.append(config_property.env)
        return used_env

    def get_project_name(self) -> typing.Optional[str]:
        """
        Retrieves the project name from the project metadata.

        The project name is used for:
        - Forming the environment variable {PROJECT_NAME}_CONFIG
        - Adding a prefix to environment variables to prevent name conflicts.

        Returns:
            str or None: The project name if present, otherwise None.
        """
        if self.project_metadata is not None:
            return self.project_metadata['name']

    def abs_config_path(self, path: str):
        """
        Converts a relative configuration path to an absolute path.

        Args:
            path (str): The relative configuration path.

        Returns:
            str: The absolute configuration path.
        """
        if not path.startswith('/'):
            return os.path.abspath(os.path.join(self.default_config_dir, path))
        return path

    def get_override_config_paths_from_env(self) -> typing.List[str]:
        """
        Retrieves additional configuration file paths from environment variables.

        Multiple configuration paths are separated by the `;` delimiter.

        Returns:
            list: A list of configuration paths obtained from environment variables.
        """
        paths = []
        project_name = self.get_project_name()
        if project_name:
            config_env = utils.unify_name(self.get_project_name()) + '_CONFIG'
        else:
            config_env = 'CONFIG'
        env_paths = os.environ.get(config_env)
        if env_paths:
            paths.extend(self.abs_config_path(path) for path in env_paths.split(';'))
        return paths

    def get_override_config_paths_from_args(self) -> typing.List[str]:
        """
        Retrieves configuration file paths passed as command-line arguments.

        Multiple configuration paths are separated by the `;` delimiter.

        Returns:
            list: A list of configuration paths passed via command-line arguments.
        """
        import argparse
        paths = []
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--config',
            '-c',
            type=str,
            help='The path to the application configuration file'
        )
        argument_paths = parser.parse_known_args()[0].config
        if argument_paths:
            paths.extend(self.abs_config_path(path) for path in argument_paths.split(';'))
        return paths
