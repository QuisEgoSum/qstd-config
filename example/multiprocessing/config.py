from qstd_config import ConfigManager, MultiprocessingStorage, ProjectMetadataType, BaseConfig


class AppConfig(BaseConfig):
    class Project(BaseConfig):
        name: str
        version: str

    debug: bool = False
    project: Project


manager: ConfigManager[AppConfig, ProjectMetadataType] = ConfigManager(
    AppConfig,
    {'name': 'qstd_config', 'version': '1.0.0'},
    project_metadata_as='project',
    config_paths=['./config.yaml'],
    storage=MultiprocessingStorage,
)

config = manager.load_config_model()
