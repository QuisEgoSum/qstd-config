import typing

from .base import ChainLoaderABC, ConfigLoaderABC

T = typing.TypeVar('T', bound=ConfigLoaderABC)


class ChainLoader(ChainLoaderABC):
    """
    Orchestrates a sequence of configuration loaders,
    applying each loader in order and merging their
    outputs into a single raw configuration dict.
    """

    def load(self) -> typing.MutableMapping[str, typing.Any]:
        """
        Sequentially invokes each loader's `load()` and merges
        the partial dicts into a single result.

        :return: Combined raw configuration dict.
        """

        base: typing.MutableMapping[str, typing.Any] = {}
        for loader in self._loaders:
            override = loader.load()
            base = self._merge_strategy.merge(base, override)
        return base

    def get_loader(self, loader_cls: typing.Type[T]) -> typing.Optional[T]:
        """
        Finds the first loader in the chain that is an instance of `loader_cls`.

        :param loader_cls: Loader class to search for.
        :return: Instance of that loader, or None if not present.
        """

        for loader in self._loaders:
            if isinstance(loader, loader_cls):
                return loader
        return None
