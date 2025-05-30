import typing


class ConfigMergeStrategyProtocol(typing.Protocol):
    """
    Defines how two configuration mappings are merged.
    """

    def merge(
        self,
        base: typing.MutableMapping[str, typing.Any],
        override: typing.Mapping[str, typing.Any],
    ) -> typing.MutableMapping[str, typing.Any]:
        """
        Merges two configuration dictionaries-`base` and `override`-returning a new dictionary where values from
        override overwrite or augment those in base according to the strategy’s implementation.

        :param base:
        :param override:
        :return: A new merged dictionary. The input mappings must not be mutated.
        """
        ...  # pragma: no cover
