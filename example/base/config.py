import os

from pydantic import BaseModel

from qstd_config import ConfigManager


class AppConfig(BaseModel):
    debug: bool = False


manager: ConfigManager[AppConfig] = ConfigManager(
    AppConfig,
    project_name='example',
    config_paths=['./config.yaml'],
    default_config_values={
        'debug': False,
    },
    root_config_path=os.path.dirname(os.path.abspath(__file__)),
)

config: AppConfig = manager.load_config_model()
