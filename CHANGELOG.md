# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


---

## [1.0.1] - 2025-06-15

### Added

- Add `py.typed` for proper type hint discovery by third-party tools.


---

## [1.0.0] - 2025-06-08

### Added

- New `ConfigManager` class with flexible configuration loading pipeline.
- Built-in support for file loaders (`YAML`, `JSON`) and environment variables.
- Environment variable resolution strategy in `EnvLoader`, based on the nested field path and
optional `project_name` prefix.
- Proxy-based access to validated config with hot-reload support and shared storage compatibility.
- Multiprocessing-compatible storage via `MultiprocessingDictStorage`.
- Extension system for:
  - custom config loaders (`CustomLoaderABC`)
  - file format loaders (`SingleFileLoaderProtocol`)
  - custom merge strategies (`ConfigMergeStrategyProtocol`)
  - loader chain customization (`ChainLoaderABC`)
- Utilities for parsing `--config` CLI arguments and environment variables.
- ENV variable documentation generator: `render_env_help()`.
- Full Pydantic `BaseModel` validation pipeline.
- Built-in deep merge strategy.

### Changed

- Complete rewrite of the public API. No compatibility with 0.x versions.
- Internal APIs and entrypoints have been restructured for improved extensibility and maintainability.
- Stronger typing guarantees and simplified configuration model.

### Removed

- All legacy `0.x` code and transitional interfaces.

---

> Note: versions before `1.0.0` are considered deprecated and undocumented.
