
# Project Configuration Manager

Supports configuration from yaml files and env.

The order of configuration overload(from highest priority to lowest):
- Parameters set in environment variables;
- Files specified via the environment variable `{PROJECT_NAME}_CONFIG`;
- Files specified in the process startup parameter `--config`(`-c`);
- Files specified by the `config_paths` parameter in the initialization of the `ConfigManager` class.

---

Manager Parameters:
- `config_cls`(`pydantic.BaseModel`) - class, used for validating and typing config fields;
- `project_metadata`(`dict`) - Basic information about the project (name, version).
`name` is used to generate environment variables;
- `config_paths`(`List[str]`) - Paths to the application configuration files;
- `project_metadata_as`: (`Optional[str]`) - This key will be assigned to `project_metadata` in the configuration object.
By default `project`. If `None` is set, `project_metadata` will not be added to the config;
- `root_config_dir`(`Optional[str]`) - Base path to the directory with configuration files to set relative paths;
- `pre_validation_hook`(`Callable[[dict], dict]`) - The method called after loading the configuration before validation.
If it is necessary to perform any transformations (downloading key files from the file system, etc.);
- `parse_config_paths_from_args`(`bool`) - Specifies whether it is necessary to automatically search for configuration
files in the command line options or not;
- `parse_config_paths_from_env`(`bool`) - Specifies whether it is necessary to automatically search for configuration
files in an environment variable(`{PROJECT_NAME}_CONFIG`) or not;
- `multiprocessing_mode`(`bool`) - Specifies whether it is necessary to use `multiprocessing.Manager().dict()` to store
the configuration.


---

Manager Methods:
- `load_config` - Loads the configuration from configuration files and environment variables.
It can be called repeatedly to update the configuration object. Returns the proxy configuration object;
- `get_config` - Returns a new proxy object to the configuration without loading the configuration;
- `get_multiprocessing_config_dict` - Returns `multiprocessing.Manager().dict()` for passing to child processes.
This option is available only with `multiprocessing_mode=True`;
- `set_multiprocessing_config_dict` - Accepts `multiprocessing.Manager().dict()`. Sets as the configuration source.
It must be installed in child processes during initialization. Available only with `multiprocessing_mode=True`.

---

Creation of environment variable names:


A transformation is used for each element of the name:
```python
import re
re.sub(pattern='[^a-zA-Z0-9]', repl='_', flags=re.DOTALL, string=name.upper())
```

For example, the project name `Test project` is converted to `TEST_PROJECT`.

The variable name is formed from `{PROJECT_NAME}_` + `'_'.join(path_to_variable)`.

```python
from pydantic import BaseModel
from qstd_config import BaseConfig, ConfigManager

class Config(BaseConfig):
    class Example(BaseModel):
        class Child(BaseModel):
            value: str
        
        child: Child
        value: int
        
    example: Example

manager = ConfigManager(Config, {'name': 'Test project', 'version': 'version'})
```

Generates the following environment variables:
- `TEST_PROJECT_EXAMPLE_VALUE`;
- `TEST_PROJECT_EXAMPLE_CHILD_VALUE`.

---

Basic example

```python
from pydantic import BaseModel

from qstd_config import ConfigManager, BaseConfig

class Config(BaseConfig):
    class Example(BaseModel):
        example: str
    
    example: Example
        
        
manager = ConfigManager(
    Config,
    {'name': 'Project name', 'version': 'project version'}
)

config = manager.load_config()
```

---

Basic multiprocessing example

```python
from multiprocessing import get_context
from pydantic import BaseModel

from qstd_config import ConfigManager, BaseConfig

class Config(BaseConfig):
    class Example(BaseModel):
        example: str
    
    example: Example
        
        
manager = ConfigManager(
    Config,
    {'name': 'Project name', 'version': 'project version'}
)

config = manager.load_config()

def run_child_process(config_dict):
    manager.set_multiprocessing_config_dict(config_dict)
    ...


get_context('spawn').Process(
    target=run_child_process,
    daemon=True,
    args=(manager.get_multiprocessing_config_dict(),)
).start()
```

