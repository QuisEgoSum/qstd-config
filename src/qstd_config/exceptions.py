import typing

from pathlib import Path

from pydantic import ValidationError


class ConfigError(Exception):
    """
    Base exception for all configuration-related errors.
    """

    pass


class ConfigValidationError(ConfigError):
    """
    Raised when configuration validation via Pydantic fails.

    Wraps the original `pydantic.ValidationError`, providing a more concise,
    line-based summary of all validation issues, and preserving the original
    exception in `self.original`.

    Example error message:
        Config validation errors:
        database.port (type_error.integer): value is not a valid integer
        api.host (value_error.missing): field required
    """

    def __init__(self, original_exception: ValidationError):
        msg_parts = ['Config validation errors: ']
        for error in original_exception.errors():
            loc: str = ".".join(map(str, error["loc"]))
            msg_parts.append(
                f'{loc} ({error["type"]}): {error["msg"]}',
            )

        super().__init__('\n'.join(msg_parts))

        self.original = original_exception


class InvalidFileContentError(ConfigError):
    """
    Raised when a configuration file is parsed successfully,
    but the top-level content is not a dict.
    """

    def __init__(self, path: Path, received_type: type) -> None:
        message = (
            f'Config file {path!r} returning {received_type.__name__}, expected dict.'
        )

        super().__init__(message)

        self.path = path
        self.received_type = received_type


class UnsupportedFileTypeError(ConfigError):
    """
    Raised when no registered file loader supports the given file extension.
    """

    def __init__(self, path: Path) -> None:
        message = f'No loader found for extension {path.suffix} (file: {path!r}).'

        super().__init__(message)

        self.path = path


class StorageNotInitializedError(ConfigError):
    """
    Raised when attempting to update configuration
    from a storage backend that has not been initialized.
    """

    pass


class FileNotExistsError(ConfigError):
    """
    Raised when one or more configuration file paths do not exist.

    Used during config path resolution to enforce file presence before loading.

    :param paths: List of missing file paths.
    """

    def __init__(self, paths: typing.List[Path]) -> None:
        message = f'The following files do not exist: {",".join(map(str, paths))}.'
        super().__init__(message)


class QstdConfigWarning(RuntimeWarning):
    """Base warning class for qstd-config related warnings."""

    pass


class MultiprocessingStorageReinitWarning(QstdConfigWarning):
    """Warns when MultiprocessingDictStorage is re-initialized after setup."""

    pass


class MultiprocessingStorageNotInitializedWarning(QstdConfigWarning):
    """Warns when storage is used before being initialized (returns local config)."""

    pass
