import copy
import typing

from .base import ConfigMergeStrategyProtocol


class DeepMergeStrategy(ConfigMergeStrategyProtocol):
    """
    Deeply (recursively) merge two mappings.

    For each key:
      - if key only in base: keep base[key]
      - if key only in override: take override[key]
      - if key in both and both values are mappings: recursively merge
      - otherwise: take override[key]
    """

    def merge(
        self,
        base: typing.MutableMapping[str, typing.Any],
        override: typing.Mapping[str, typing.Any],
    ) -> typing.MutableMapping[str, typing.Any]:
        """
        :param base: Original mapping to serve as the starting point.
        :param override: Mapping with overriding values.
        :return: A new dict containing the merged result.
        """

        result = copy.deepcopy(base)
        return self._merge(result, override)

    def _merge(
        self,
        result: typing.MutableMapping[str, typing.Any],
        override: typing.Mapping[str, typing.Any],
    ) -> typing.MutableMapping[str, typing.Any]:
        """
        :param result: Original mapping to serve as the starting point.
        :param override: Mapping with overriding values.
        :return: A new dict containing the merged result.
        """

        for key, value in override.items():
            if key not in result:
                result[key] = value
            elif isinstance(value, dict) and isinstance(result[key], dict):
                value = typing.cast(typing.Dict[str, typing.Any], value)
                result[key] = self._merge(
                    typing.cast(typing.MutableMapping[str, typing.Any], result[key]),
                    typing.cast(typing.Mapping[str, typing.Any], value),
                )
            else:
                result[key] = value
        return result
