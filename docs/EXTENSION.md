# Extension

---

## Adding a new FileLoader

A new `FileLoader` must implement the `SingleFileLoaderProtocol` protocol:

```python
from pathlib import Path
from qstd_config import SingleFileLoaderProtocol, file_loader_registry


class TomlLoader(SingleFileLoaderProtocol):
    def supported_extensions(self):
        return [".toml"]

    def is_supported(self, path: Path): ...

    def load(self, path: Path): ...


# Register with higher priority (default loaders use priority 0)
file_loader_registry.register_file_loader(TomlLoader(), priority=10)
```

You can also override an existing loader for a supported file format.

---

## File loader registry

The file loader registry provides methods to manage registered file loaders:
- `register_file_loader(new_loader: FileLoader, *, priority: int = 1, replace: bool = False) -> None` - registers a new loader.
- `unregister_file_loader(predicate: Callable) -> None` - removes loaders that match the provided predicate.
- `get_file_loaders() -> List[FileLoader]` - returns the list of currently registered loaders.

---

## Adding a custom loader

```python
import typing

from qstd_config import ConfigManager, CustomLoaderABC


class RedisLoader(CustomLoaderABC):
    def load(self) -> typing.MutableMapping[str, typing.Any]: ...


manager = ConfigManager(
    ...,
    custom_loaders=[RedisLoader()]
)
```

By default, custom loaders have the lowest priority - they are executed first, so their values can be overridden
by later loaders like `FileLoader` and `EnvLoader`.

---

## Changing the order of config source application

If you want to redefine the order in which config sources are applied - or remove some entirely - you can override
the `ChainLoader` factory function.

```python
import typing
from pathlib import Path
from pydantic import BaseModel
from qstd_config import (
    ConfigManager, ConfigMergeStrategyProtocol, CustomLoaderABC, ChainLoader, ChainLoaderABC,
    FileLoader, EnvLoader
)
from qstd_config.loader import file_loader_registry


def chain_loader_factory(
    model: typing.Type[BaseModel],
    paths: typing.List[Path],
    prefix: typing.Optional[str],
    merge_strategy: ConfigMergeStrategyProtocol,
    custom_loaders: typing.List[CustomLoaderABC],
) -> ChainLoaderABC:
    return ChainLoader(
        loaders=[
            FileLoader(
                paths=paths,
                file_loaders=file_loader_registry.get_file_loaders(),
                merge_strategy=merge_strategy,
            ),
            EnvLoader(model=model, prefix=prefix),
            *custom_loaders,  # last in list = highest priority
        ],
        merge_strategy=merge_strategy,
    )


manager = ConfigManager(
    ...,
    custom_loaders=[RedisLoader()],
    chain_loader_factory=chain_loader_factory,
)
```

---

### Custom merge strategy


You can define a custom strategy to merge configuration values from different sources by
implementing the `ConfigMergeStrategyProtocol` protocol:

```python
import typing
from qstd_config import ConfigMergeStrategyProtocol


class ListAppendStrategy(ConfigMergeStrategyProtocol):
    def merge(
        self,
        base: typing.MutableMapping[str, typing.Any],
        override: typing.Mapping[str, typing.Any]
    ) -> typing.MutableMapping[str, typing.Any]:
        # custom merge logic
        return result


manager = ConfigManager(AppConfig, ..., merge_strategy=ListAppendStrategy())
```
