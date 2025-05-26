import typing


class ProjectMetadataType(typing.TypedDict):
    name: str
    version: str


class MultiprocessingContextType(typing.TypedDict):
    revision: str
    config: typing.Dict[str, typing.Any]
