import copy
import typing

import yaml

from multiprocessing import Manager, current_process

from .types import ProjectMetadata
from .proxy import ProxyConfig, ProxyConfigDictContener
from .utils import (
    abs_path,
    cross_merge_dicts,
    unify_name,
    get_override_config_paths_from_env,
    get_override_config_paths_from_args
)
from .env import assign_env_to_dict, create_env_list_from_schema


T = typing.TypeVar('T')


class ConfigManager(typing.Generic[T]):
    def __init__(
        self,
        config_cls: typing.Type[T],
        project_metadata: typing.Union[ProjectMetadata, typing.Dict],
        *,
        config_paths: typing.List[str] = None,
        project_metadata_as: typing.Optional[str] = 'project',
        root_config_dir: typing.Optional[str] = None,
        pre_validation_hook: typing.Callable[[dict], dict] = lambda _config: _config,
        parse_config_paths_from_args: bool = True,
        parse_config_paths_from_env: bool = True,
        multiprocessing_mode: bool = False
    ):
        self.config_cls = config_cls
        self.config_paths = config_paths or []
        if parse_config_paths_from_env:
            self.config_paths.extend(get_override_config_paths_from_env(project_metadata['name'], root_config_dir))
        if parse_config_paths_from_args:
            self.config_paths.extend(get_override_config_paths_from_args(root_config_dir))
        self.project_metadata = project_metadata
        self.project_metadata_as = project_metadata_as
        self.root_config_dir = root_config_dir
        self.pre_validation_hook = pre_validation_hook
        self.multiprocessing_mode = multiprocessing_mode
        self._config_dict = ProxyConfigDictContener(None)
        if multiprocessing_mode:
            if current_process().name == 'MainProcess':
                manager = Manager()
                self._config_dict.config_dict = manager.dict()
            else:
                self._config_dict.config_dict = dict()
        else:
            self._config_dict.config_dict = dict()
        self.env_list = create_env_list_from_schema(config_cls, unify_name(self.project_metadata['name']))
        self.used_env = []

    def set_multiprocessing_config_dict(self, config_dict):
        if self.multiprocessing_mode is False:
            raise Exception('Multiprocessing mode disabled')
        self._config_dict.config_dict = config_dict

    def get_multiprocessing_config_dict(self):
        if self.multiprocessing_mode is False:
            raise Exception('Multiprocessing mode disabled')
        if current_process().name != 'MainProcess':
            raise Exception('Get multiprocessing config allowed only on MainProcess')
        return self._config_dict.config_dict

    def get_config(self):
        return ProxyConfig(self._config_dict)

    def load_config(self) -> typing.Union[T]:
        config_dict = dict()

        if self.project_metadata_as:
            config_dict[self.project_metadata_as] = copy.deepcopy(self.project_metadata)

        for config_path in self.config_paths:
            with open(abs_path(config_path, self.root_config_dir), 'r') as file:
                override_config_dict = yaml.safe_load(file) or dict()
                config_dict = cross_merge_dicts(config_dict, override_config_dict)

        self.used_env = assign_env_to_dict(config_dict, self.env_list)

        config_dict = self.pre_validation_hook(config_dict)

        config_dict = self.config_cls.parse_obj(config_dict).dict()

        self._config_dict.config_dict.clear()
        self._config_dict.config_dict.update(**config_dict)
        return typing.cast(T, ProxyConfig(self._config_dict))
