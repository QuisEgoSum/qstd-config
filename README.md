# QSTD Config

`qstd_config` is a Python library for loading, validating, and safely accessing configuration.  
It supports hierarchical configuration loading from multiple YAML files, overrides via environment variables,
and the ability to reload the configuration at runtime without restarting the process. It also supports
synchronization between processes using `multiprocessing.Manager().dict()`.

---

## Features

- Load configuration from multiple YAML files
- Override values via environment variables
- Pydantic-based validation and typing
- Support for nested models
- Runtime-safe proxy access to configuration
- Reload configuration in-place via `load_config_model()`
- Config path resolution via CLI (`--config`) or environment variable
- Built-in environment variable metadata with rendering support
- Multiprocessing support with shared configuration

---

## Installation

```bash
pip install qstd-config
```

---

## Basic example

```python
from pydantic import BaseModel
from qstd_config import ConfigManager

class DatabaseConfig(BaseModel):
    host: str
    port: int

class AppConfig(BaseModel):
    debug: bool
    db: DatabaseConfig

manager = ConfigManager(
    AppConfig,
    project_metadata={"name": "my_app", "version": "1.0.0"}
)

config = manager.load_config_model()
print(config.db.host)
```

---

## Configuration sources and priority

1. Environment variables
2. Paths from CLI arguments (`--config` / `-c`)
3. Paths from the `MY_APP_CONFIG` environment variable
4. Paths explicitly passed via `config_paths` argument

Multiple paths can be passed using `;` as separator — they will be applied top to bottom as overrides.

---

## Environment variable naming

Variable names follow the format:

```
{PROJECT_NAME}_{PATH_TO_FIELD}
```

Where:
- `PROJECT_NAME` is returned by `ConfigManager.get_project_name()` (can be overridden)
- `PATH_TO_FIELD` reflects field nesting, joined by `_`
- All segments are uppercased and sanitized (non-alphanumeric replaced by `_`)

You can explicitly override the env name:

```python
Field(..., json_schema_extra={"env": "CUSTOM_ENV_NAME"})
```

---

## CLI and environment integration

### CLI usage

```bash
python app.py --config=./base.yaml;./override.yaml
```

### ENV usage

```bash
export MY_APP_CONFIG=./base.yaml;./override.yaml
```

---

## Multiprocessing support

When using `MultiprocessingStorage`, configuration is synchronized between processes
using `multiprocessing.Manager().dict()`.

### Behavior

- In the main process, you may call `load_config_model()` before forking — this will load config from all sources.
- In a child process, `set_multiprocessing_context(context)` must be called before access.
- Accessing configuration before `set_multiprocessing_context()` does not raise an error, but emits a warning and
returns the uninitialized config state.

### Example

```python
from multiprocessing import get_context
from qstd_config import ConfigManager, MultiprocessingStorage

manager = ConfigManager(..., storage=MultiprocessingStorage)
config = manager.load_config_model()

def worker(context):
    manager.set_multiprocessing_context(context)
    manager.load_config_model()
    print(config.debug)

ctx = manager.get_multiprocessing_context()
get_context("spawn").Process(target=worker, args=(ctx,), daemon=True).start()
```

---

## ConfigManager

| Parameter                      | Type                                               | Description                                                                                                                                                |
|--------------------------------|----------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `config_cls`                   | `Type[BaseModel]`                                  | Root Pydantic model that defines and validates the configuration structure                                                                                 |
| `project_metadata`             | `dict` (typically `{"name": str, "version": str}`) | Project metadata used in environment prefix and optionally injected into the config                                                                        |
| `project_metadata_as`          | `Optional[str]`                                    | Key under which `project_metadata` will be included in the config. If `None`, metadata is not injected.                                                    |
| `storage`                      | `Type[StorageABC]`                                 | Storage implementation used for maintaining current config. Defaults to `InMemoryStorage`. Can be set to `MultiprocessingStorage` for multiprocess sharing |
| `config_paths`                 | `List[str]`                                        | List of configuration file paths to load                                                                                                                   |
| `root_config_path`             | `Optional[str]`                                    | Root directory used to resolve relative config paths                                                                                                       |
| `pre_validation_hook`          | `Callable[[dict], dict]`                           | Optional hook to modify raw configuration dict before validation (e.g., expand paths, inject secrets)                                                      |
| `parse_config_paths_from_args` | `bool`                                             | If `True`, reads config file paths from CLI arguments `--config/-c`                                                                                        |
| `parse_config_paths_from_env`  | `bool`                                             | If `True`, reads config file paths from the environment variable `{PROJECT_NAME}_CONFIG`                                                                   |
| `multiprocessing_manager`      | `multiprocessing.Manager`                          | Optional custom multiprocessing manager. Used only with `MultiprocessingStorage`                                                                           |


| Method                                 | Description                                                             |
|----------------------------------------|-------------------------------------------------------------------------|
| `load_config_model()`                  | Validates and updates configuration model and proxy                     |
| `get_multiprocessing_context()`        | Returns a shared dict for child processes                               |
| `set_multiprocessing_context(context)` | Sets the shared dict inside a subprocess                                |
| `render_env_help()`                    | Returns a human-readable help string for environment variables          |
| `used_env`                             | List of environment variables that were applied                         |
| `env_list`                             | Full list of environment-bound fields and metadata (`EnvironmentField`) |


> A single `ConfigManager` instance manages one `ProxyConfig`. Repeated calls to `load_config_model()` update the internal state, and all references to the proxy remain valid and reflect the new configuration.

---

## ProxyConfig object

Provides typed, transparent access to current configuration.  
Acts as a proxy to the latest state in the underlying `Storage`. Automatically updated when calling `load_config_model()`.

Supports:

- Attribute access to fields (e.g. `config.some_field`)
- `is_ready` property to check initialization status (useful for multiprocessing startup)

---

## Render environment variable documentation

```python
from qstd_config.manager import ConfigManager

manager = ConfigManager(...)
print(manager.render_env_help())
```

This can be used in your CLI:

```python
if "--env-help" in sys.argv:
    print(manager.render_env_help())
    sys.exit(0)
```

---

## License

MIT
