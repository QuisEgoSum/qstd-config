import os
import typing

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from qstd_config.logger import logger

from .base import EnvLoaderABC
from .env_field import EnvironmentField
from .utils import build_env_list, deep_set, safe_get_type_name


class EnvLoader(EnvLoaderABC):
    """
    Loads raw environment variables into a nested dict structure
    according to a Pydantic BaseModel schema.

    Does NOT perform validation or type conversion: it simply
    maps string values from `os.environ` into the dict for later
    Pydantic parsing.
    """

    _env_list: typing.List[EnvironmentField]
    _used_env_list: typing.List[EnvironmentField]
    _env_help: typing.Optional[str]

    def __init__(
        self,
        model: typing.Type[BaseModel],
        prefix: typing.Optional[str] = None,
    ) -> None:
        """
        :param model: The Pydantic BaseModel class defining the config schema.
        :param prefix: Optional environment variable name prefix (without trailing underscore).
                       If provided, it is prepended (with an underscore) to all variable names,
                       e.g. prefix="app" -> env vars "APP_FOO", "APP_BAR_BAZ", etc.
        """

        super().__init__(model=model, prefix=prefix)

        self._env_list = build_env_list(self._model, self._prefix)
        self._used_env_list = []
        self._env_help = None

    @property
    def env_list(self) -> typing.List[EnvironmentField]:
        """
        :return: A list of `EnvironmentField` describing every possible variable name and its target field path
                 in the config.
        """

        return list(self._env_list)

    @property
    def used_env_list(self) -> typing.List[EnvironmentField]:
        """
        :return: Subset of env_list that were actually present in `os.environ` during the last load() call.
        """

        return list(self._used_env_list)

    def render_env_help(self) -> str:
        """
        Returns a help text listing all possible environment variables:
        name, type, description, and default if any.

        :return: Multiline help string.
        """

        if self._env_help is not None:
            return self._env_help

        lines: typing.List[str] = []

        for field in self._env_list:
            line = f"{field.name} ({safe_get_type_name(field.type)})"

            if field.description:
                line += f" - {field.description.strip()}"

            if field.default is not PydanticUndefined:
                line += f" [default: {repr(field.default)}]"

            lines.append(line)

        self._env_help = "\n".join(lines)
        return self._env_help

    def load(self) -> typing.Dict[str, typing.Any]:
        """
        Reads all environment variables defined in `env_list`, builds a nested `dict` of raw string values,
        and tracks which variables were used.

        :return: A `dict` of raw config values, structured for Pydantic validation.
        """

        self._used_env_list = []

        result: typing.Dict[str, typing.Any] = {}

        for env in self._env_list:
            value = os.environ.get(env.name, None)

            if value is None:
                logger.debug('Env %s is not present in os.environ', env.name)
                continue

            logger.debug('Env %s is present in os.environ', env.name)

            self._used_env_list.append(env)

            deep_set(result, env.field_path, value)

        return result
