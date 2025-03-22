
# Project Configuration Manager

Supports configuration from yaml files and env.

The order of configuration overload(from highest priority to lowest):
- Parameters set in environment variables;
- Files specified via the environment variable `{PROJECT_NAME}_CONFIG`;
- Files specified in the process startup parameter `--config`(`-c`);
- Files specified by the `config_paths` parameter in the initialization of the `ConfigManager` class.
