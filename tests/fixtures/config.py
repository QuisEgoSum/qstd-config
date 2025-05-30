import typing

from pydantic import BaseModel, Field


class NestedConfig(BaseModel):
    flag: bool = Field(default=False, description='Nested flag')


class AppConfig(BaseModel):
    debug: bool = Field(default=False, json_schema_extra={'env': 'DEBUG_OVERRIDE'})
    string: str = Field(default='string')
    nested: NestedConfig = NestedConfig()


class ComplexConfiguration(BaseModel):
    class Nested(BaseModel):
        value: typing.Union[int, float]

    nested: typing.Union[int, str, Nested, typing.List[Nested]]
    optional: typing.Optional[Nested]
    annotated: typing.Annotated[Nested, int]
