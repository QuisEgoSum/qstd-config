# qstd-config

A lightweight and flexible configuration management library for Python applications, built on top of Pydantic.  
It allows you to load and validate settings from multiple sources
(YAML/JSON files, environment variables, or custom loaders), merge them via strategy,
and supports hot-reload as well as multiprocess-safe sharing.

---

## Key Features

- **Chain of loaders**: load configuration from multiple sources (files, environment variables, custom loaders).
- **Pydantic integration**: validate the final config using a `BaseModel`.
- **Flexible merge strategies**: deep merge by default, with support for custom strategies.
- **ProxyConfig**: proxy object with `reload()`, `setup()` methods and model attribute access.
- **Hot-reload support**: update configuration at runtime without restarting the process.
- **Multiprocessing storage**: share configuration between processes using `multiprocessing.Manager().dict()`.
- **Extensibility**: plug in custom loaders, merge strategies, and storages.

---

## Documentation

- [ConfigManager](https://github.com/QuisEgoSum/qstd-config/blob/release/v1.0/docs/CONFIG_MANAGER.md)
- [Config Proxy and Storage](https://github.com/QuisEgoSum/qstd-config/blob/release/v1.0/docs/PROXY_AND_STORAGE.md)
- [Extension](https://github.com/QuisEgoSum/qstd-config/blob/release/v1.0/docs/EXTENSION.md)

---

## Install

```bash
pip install qstd-config
```

---

## Quick start

```python
from pydantic import BaseModel
from qstd_config import ConfigManager


class AppConfig(BaseModel):
    class DB(BaseModel):
        host: str = "localhost"
        port: int = 5432

    debug: bool = False
    db: DB


manager = ConfigManager(
    AppConfig,
    project_name="My App",
    config_paths=["./config.yaml"],
    default_config_values={"debug": False},
)
config = manager.load_config_model()

print(config.db.host, config.db.port, config.debug)
```

---

## Environment variables

The list of supported environment variables is automatically generated based on the structure of the config model.
You can override variable names explicitly via `json_schema_extra` in Pydantic’s Field. For example:

```python
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    class DB(BaseModel):
        host: str = Field("localhost")
        port: int = Field(5432, json_schema_extra={'env': 'DATABASE_PORT'})

    debug: bool = False
    db: DB
```

Recognized environment variables:
- `DEBUG`
- `DB_HOST`
- `DATABASE_PORT`

If `project_name="My App"` is specified, variables will be prefixed:
- `MY_APP_DEBUG`
- `MY_APP_DB_HOST`
- `MY_APP_DATABASE_PORT`

---

## Configuration paths


You can provide configuration file paths from multiple sources.
The order below defines the **precedence** (higher overrides lower):
1. CLI argument: `--config=/path/to/config.yaml`
2. Environment variable: `MY_APP_CONFIG=/path1.yaml;/path2.yaml`
3. `config_paths` argument passed explicitly to the manager

---

## Tests

```shell
pytest --cov=qstd_config --cov-report=term-missing
```

## Compatibility

Tested on Python 3.9–3.12.

## License

MIT © QuisEgoSum

```text
Copyright (c) 2025 QuisEgoSum

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
