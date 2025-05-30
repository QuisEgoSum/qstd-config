import typing

from pathlib import Path

from pydantic import BaseModel

from qstd_config.merge_strategy.base import ConfigMergeStrategyProtocol

from .base import ChainLoaderABC, CustomLoaderABC
from .chain_loader import ChainLoader
from .env_loader import EnvLoader
from .file_loader import FileLoader
from .file_loader_registry import get_file_loaders


def default_chain_loader_factory(
    model: typing.Type[BaseModel],
    paths: typing.List[Path],
    prefix: typing.Optional[str],
    merge_strategy: ConfigMergeStrategyProtocol,
    custom_loaders: typing.List[CustomLoaderABC],
) -> ChainLoaderABC:
    """
    Default implementation of ChainLoader factory.

    Constructs a ChainLoader instance by combining the provided custom loaders (if any),
    followed by a FileLoader (for YAML/JSON/etc), and finally an EnvLoader (for environment variables).

    The resulting order of application is:
        1. Custom loaders (lowest priority, override everything)
        2. FileLoader
        3. EnvLoader (highest priority)

    All loaders are merged via the provided ConfigMergeStrategy.

    Note:
        Because the loaders are applied sequentially and merged cumulatively, later loaders
        override the keys of earlier ones. If you want your custom loaders to take precedence
        over file or environment sources, include them first in the list.

    :param model: Pydantic model class for env variable resolution.
    :param paths: List of config file paths to be passed to FileLoader.
    :param prefix: Optional prefix for environment variable names.
    :param merge_strategy: Strategy to merge raw config dicts.
    :param custom_loaders: Optional list of user-defined loaders.
    :return: ChainLoaderABC instance.
    """

    return ChainLoader(
        loaders=[
            *custom_loaders,
            FileLoader(
                paths=paths,
                file_loaders=get_file_loaders(),
                merge_strategy=merge_strategy,
            ),
            EnvLoader(model=model, prefix=prefix),
        ],
        merge_strategy=merge_strategy,
    )
