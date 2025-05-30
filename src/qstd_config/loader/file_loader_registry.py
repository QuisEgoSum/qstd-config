import threading
import typing

from qstd_config.logger import logger

from .base import SingleFileLoaderProtocol

_file_loaders: typing.List[typing.Tuple[SingleFileLoaderProtocol, int]] = []
_lock = threading.Lock()

DEFAULT_CUSTOM_LOADER_PRIORITY: typing.Final[int] = 1
DEFAULT_INTERNAL_LOADER_PRIORITY: typing.Final[int] = 0


def register_file_loader(
    new_loader: SingleFileLoaderProtocol,
    *,
    priority: int = DEFAULT_CUSTOM_LOADER_PRIORITY,
    replace: bool = False,
) -> None:
    """
    Register a new single-file loader.

    :param new_loader: Instance supporting SingleFileLoaderProtocol.
    :param priority: Higher priority loaders are tried first.
    :param replace: If True, remove existing loaders for the same
                    extensions before registering this one.
    """

    global _file_loaders

    with _lock:
        if replace:
            new_loaders: typing.List[typing.Tuple[SingleFileLoaderProtocol, int]] = []

            for loader, priority in _file_loaders:
                if type(loader) is type(new_loader) or any(
                    ext in loader.supported_extensions()
                    for ext in new_loader.supported_extensions()
                ):
                    logger.debug(
                        'Unregister loader(replace): %s with priority=%s',
                        type(loader).__name__,
                        priority,
                    )
                else:
                    new_loaders.append((loader, priority))

            _file_loaders = new_loaders

        _file_loaders.append((new_loader, priority))

        logger.debug(
            'Registering loader: %s with priority=%s',
            type(new_loader).__name__,
            priority,
        )


def unregister_file_loader(
    predicate: typing.Callable[[SingleFileLoaderProtocol], bool],
) -> None:
    """
    Unregister file loaders matching the given predicate.

    :param predicate: Function receiving a loader and returning True
                      to remove it from the registry.
    """

    global _file_loaders

    with _lock:
        new_loaders: typing.List[typing.Tuple[SingleFileLoaderProtocol, int]] = []

        for loader, priority in _file_loaders:
            if not predicate(loader):
                new_loaders.append((loader, priority))
            else:
                logger.debug(
                    'Unregister loader(predicate): %s with priority=%s',
                    type(loader).__name__,
                    priority,
                )
        _file_loaders = new_loaders


def get_file_loaders() -> typing.List[SingleFileLoaderProtocol]:
    """
    Return all registered single-file loaders, sorted by descending priority.

    :return: List of loader instances.
    """

    with _lock:
        return [loader for (loader, _) in sorted(_file_loaders, key=lambda t: -t[1])]
