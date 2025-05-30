# Config Proxy and Storage

The main idea behind the proxy is to provide an easy way to replace the configuration object with a dynamic
proxy that supports reload and shared memory storage across processes.

---

## ProxyConfig

ProxyConfig is a proxy object wrapping a Pydantic model that allows hot-reloading the configuration
in memory without restarting the process.

It provides the following methods and properties:
- `config` - the current Pydantic model instance.
- `reload() -> None` - reloads the config by calling `ConfigManager.load_config_model()` and updates the storage
with the new model.
- `setup(**kwargs: Any)` - initializes the storage, required for some storage implementations.
- `is_ready` - returns whether the config is initialized and ready for use.
- `__getattr__` - delegates attribute access to the underlying model.

---

## Storage

A storage is responsible for holding and updating the configuration instance.

It must implement the `ConfigStorageABC` interface with the following methods and properties:
- `setup(**kwargs) -> None` - initializes the storage, if necessary.
- `update(config: BaseModel) -> None` - updates the stored configuration.
- `current() -> BaseModel` - returns the current Pydantic model from storage.
`is_initialized` - whether the storage is ready for use.

You can also implement your own custom storage by subclassing `ConfigStorageABC`.

---

## Hot-reload in single-process mode

The default usage of `ProxyConfig` works with `InMemoryStorage`, which stores the configuration model directly in memory.

```python
from pydantic import BaseModel
from qstd_config import ConfigManager, ProxyConfig, InMemoryStorage


class AppConfig(BaseModel):
    debug: bool = False


manager = ConfigManager(AppConfig)

# Get the proxy object
proxy: ProxyConfig[AppConfig] = manager.get_proxy(InMemoryStorage)

# Access fields like a normal model
print(proxy.debug)

# Reload config from files/ENV
proxy.reload()
print(proxy.debug)
```

---

## Multiprocessing and shared reload

`MultiprocessingDictStorage` uses a shared `multiprocessing.Manager().dict()` to synchronize the configuration object
between the main and worker processes.

When the config is updated in one process, changes are immediately reflected in all others.

This type of storage requires explicit initialization using `ProxyConfig.setup()` with a `multiprocessing_dict`.

The proxy can be declared globally, but access before setup will issue a warning and use a fallback local
config - which might result in inconsistent state across processes.

```python
import multiprocessing
from pydantic import BaseModel
from qstd_config import ConfigManager, MultiprocessingDictStorage, MultiprocessingContextType


class AppConfig(BaseModel):
    debug: bool = False


manager = ConfigManager(AppConfig)

proxy = manager.get_proxy(MultiprocessingDictStorage)


# Worker function
def worker(ctx: MultiprocessingContextType):
    proxy.setup(multiprocessing_dict=ctx)
    print(proxy.config)


# Entry point
def main():
    # Create shared context
    ctx = MultiprocessingDictStorage.create_shared_context()

    # Spawn worker processes
    procs = []
    for i in range(3):
        p = multiprocessing.get_context("spawn").Process(target=worker, args=(ctx,))
        p.start()
        procs.append(p)

    # Initialize in main process
    proxy.setup(multiprocessing_dict=ctx)
    
    # Main process can also reload
    print(proxy.config)
    proxy.reload()

    for p in procs:
        p.join()


if __name__ == "__main__":
    main()
```

---

## Warnings and Best Practices

`qstd-config` may emit runtime warnings when `MultiprocessingDictStorage` is misused. These are non-fatal,
but intended to inform about potentially unintended usage patterns.

### `MultiprocessingStorageReinitWarning`

Emitted when `setup()` is called more than once in the same process.

```python
warnings.warn(
    "MultiprocessingStorage reinitialized.",
    MultiprocessingStorageReinitWarning,
    stacklevel=2,
)
```

#### Recommendation

Call `setup()` only once per process. It's preferable to bind the shared context at the start of the process
rather than at the module level.

#### Suppress

```python
import warnings
from qstd_config.exceptions import MultiprocessingStorageReinitWarning

warnings.filterwarnings("ignore", category=MultiprocessingStorageReinitWarning)
```

### `MultiprocessingStorageNotInitializedWarning`

Emitted when the configuration is accessed before calling `setup()` — including calls to `current()`
or any attribute of the config.

```python
warnings.warn(
    "MultiprocessingStorage not initialized; returning local config.",
    MultiprocessingStorageNotInitializedWarning,
    stacklevel=2
)
```

#### Recommendation

Access the config only after calling `setup()`.

However, if you're intentionally configuring global modules (e.g. `logger`) before the configuration is fully
initialized, this behavior is allowed and will return a local config snapshot.

#### Suppress

```python
import warnings
from qstd_config.exceptions import MultiprocessingStorageNotInitializedWarning

warnings.filterwarnings("ignore", category=MultiprocessingStorageNotInitializedWarning)
```

---

## Typing and IDE support


One of the design goals for the proxy was seamless substitution of the original config object.
However, Python's type system doesn't allow precise typing of proxy classes that mimic both
the proxy API and the original model.

To make your IDE (e.g. PyCharm, VSCode) recognize both model fields and proxy methods like `reload`,
you can define a stub class:

```python
from qstd_config import ProxyConfig, InMemoryStorage


class AppConfigProxy(ProxyConfig[AppConfig], AppConfig):
    pass


# Then use:
config: AppConfigProxy = typing.cast(AppConfigProxy, manager.get_proxy(InMemoryStorage))
```
