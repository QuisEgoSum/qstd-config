import typing


class MultiprocessingContextType(typing.TypedDict):
    """
    Shared state for MultiprocessingDictStorage, kept in a
    multiprocessing.Manager().dict() and synchronized across processes.

    Attributes:
        initialized (bool):
            Whether the main process has populated this context
            with the initial config and revision.
        revision (str):
            A unique identifier (e.g. random hex) that changes on every update,
            used to detect when workers need to reload.
        config (dict[str, Any]):
            The JSON-serializable representation of the last validated config,
            as produced by `config.model_dump(mode="json")`.
    """

    initialized: bool
    revision: str
    config: typing.Dict[str, typing.Any]
