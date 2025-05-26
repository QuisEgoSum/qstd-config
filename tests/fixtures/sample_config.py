from pydantic import Field
from qstd_config.base import BaseConfig


class NestedConfig(BaseConfig):
    flag: bool = Field(default=False, description='Nested flag')


class AppConfig(BaseConfig):
    debug: bool = Field(default=False, json_schema_extra={'env': 'DEBUG_OVERRIDE'})
    string: str = Field(default='string')
    nested: NestedConfig = NestedConfig()
