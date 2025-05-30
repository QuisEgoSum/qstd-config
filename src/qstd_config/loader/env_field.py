import typing

from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentField:
    """
    Metadata for one environment-bound field in the configuration.
    Used for documentation, env parsing and diagnostics.
    """

    title: str
    name: str
    field_path: typing.List[str]
    type: typing.Any
    default: typing.Any
    description: typing.Optional[str]
    examples: typing.Optional[typing.List[typing.Any]]
