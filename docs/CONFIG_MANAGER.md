# ConfigManager

`ConfigManager` is the core class of the library, responsible for collecting and validating configuration
from multiple sources.

It supports loading configuration from YAML/JSON files, environment variables, and custom loaders,
merging them using a defined strategy.

---

## Usage example

```python
from pydantic import BaseModel
from qstd_config import ConfigManager, DeepMergeStrategy


class AppConfig(BaseModel):
    debug: bool = False


manager = ConfigManager(
    AppConfig,
    project_name="My App",
    config_paths=["./config.yaml"],
    root_config_path='/etc/project',
    pre_validation_hook=pre_validation_hook,
    parse_config_paths_from_env=True,
    parse_config_paths_from_args=True,
    default_config_values={"debug": False},
    custom_loaders=[MyLoader()],
    chain_loader_factory=custom_chain_loader_factory,
    merge_strategy=DeepMergeStrategy,
)

config = manager.load_config_model()
```

---

## Class parameters:
- `config_cls` - the Pydantic model class
- `project_name` - optional name used to prefix environment variables
- `config_paths` – optional list of default configuration file paths. The files are loaded in the given order
- `root_config_path` – optional root directory for resolving relative paths in configuration files
- `pre_validation_hook` – optional function called after merging all sources but before validation.
Useful for injecting secrets, loading keys from disk, etc.
- `parse_config_paths_from_args` – whether to extract config file paths from CLI arguments (`--config` / `-c`),
defaults to `True`
- `parse_config_paths_from_env` – whether to extract config file paths from env variable
(`{PROJECT_NAME}_CONFIG` or `CONFIG`), defaults to `True`
- `default_config_values` – optional raw dict with default values, primarily for use in test environments
- `custom_loaders` – optional list of custom loaders implementing `CustomLoaderABC`.
By default, they have lower priority than `EnvLoader` and `FileLoader`
- `chain_loader_factory` – optional factory function to construct a custom `ChainLoader`
- `merge_strategy` – merge strategy for raw config dicts, defaults to DeepMergeStrategy

---

## Default loader priority

| Loader                | Priority | Description                                           |
|-----------------------|----------|-------------------------------------------------------|
| default_config_values | 1        | Default values                                        |
| custom_loaders        | 2        | Custom loaders                                        |
| FileLoader            | 3        | Config values from files (YAML, JSON, custom formats) |
| EnvLoader             | 4        | Environment variables                                 |

---

## Class methods:
- `load_config_dict() -> dict[str, Any]` – loads and merges raw config from all sources,
then applies `pre_validation_hook`
- `load_config_model() -> AppConfig` – loads config and returns a validated Pydantic model
- `get_proxy(storage_cls: Type[StorageABC]) -> ProxyConfig` – returns a proxy config object that supports hot reload
and storage-backed sync (e.g., `InMemoryStorage`, `MultiprocessingDictStorage`)
- `render_env_help() -> Optional[str]` – returns a formatted help string for environment variables,
available only if `EnvLoaderABC` is used (enabled by default)

---

## Class attributes:
- `config_paths` – list of resolved `Path` objects used during configuration loading,
includes paths from direct arguments, environment variables, and CLI args (in order of priority)
- `env_list` – list of `EnvironmentField` generated from the Pydantic model,
available if EnvLoaderABC is used (which it is by default)
- `used_env_list` – list of `EnvironmentField` that were actually used during the last config load,
also depends on `EnvLoaderABC` being active
