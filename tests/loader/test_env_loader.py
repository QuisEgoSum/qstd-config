import os

from pydantic import Field

from qstd_config import EnvironmentField
from qstd_config.loader import EnvLoader
from tests.fixtures.config import AppConfig


def test_env_loader():
    loader = EnvLoader(AppConfig)

    assert loader.env_list == [
        EnvironmentField(
            title='debug',
            name='DEBUG_OVERRIDE',
            field_path=['debug'],
            type=bool,
            default=False,
            description=None,
            examples=None,
        ),
        EnvironmentField(
            title='string',
            name='STRING',
            field_path=['string'],
            type=str,
            default='string',
            description=None,
            examples=None,
        ),
        EnvironmentField(
            title='flag',
            name='NESTED_FLAG',
            field_path=['nested', 'flag'],
            type=bool,
            default=False,
            description='Nested flag',
            examples=None,
        ),
    ]

    assert loader.used_env_list == []

    config = loader.load()

    assert config == {}
    assert loader.used_env_list == []

    os.environ['DEBUG_OVERRIDE'] = 'true'
    os.environ['STRING'] = 'string'
    os.environ['NESTED_FLAG'] = 'false'

    config = loader.load()

    assert config == {'string': 'string', 'debug': 'true', 'nested': {'flag': 'false'}}
    assert {env.name for env in loader.used_env_list} == {
        'DEBUG_OVERRIDE',
        'STRING',
        'NESTED_FLAG',
    }


def test_env_loader_with_project_name():
    loader = EnvLoader(AppConfig, prefix='project name')

    assert loader.env_list == [
        EnvironmentField(
            title='debug',
            name='DEBUG_OVERRIDE',
            field_path=['debug'],
            type=bool,
            default=False,
            description=None,
            examples=None,
        ),
        EnvironmentField(
            title='string',
            name='PROJECT_NAME_STRING',
            field_path=['string'],
            type=str,
            default='string',
            description=None,
            examples=None,
        ),
        EnvironmentField(
            title='flag',
            name='PROJECT_NAME_NESTED_FLAG',
            field_path=['nested', 'flag'],
            type=bool,
            default=False,
            description='Nested flag',
            examples=None,
        ),
    ]


def test_env_loader_render_env_help():
    class EnvHelpConfig(AppConfig):
        without_default: str
        with_description: str = Field(..., description='description')

    loader = EnvLoader(EnvHelpConfig)

    env_help = (
        "DEBUG_OVERRIDE (bool) [default: False]\n"
        "STRING (str) [default: 'string']\n"
        "NESTED_FLAG (bool) - Nested flag [default: False]\n"
        "WITHOUT_DEFAULT (str)\n"
        "WITH_DESCRIPTION (str) - description"
    )

    assert loader.render_env_help() == env_help
    assert loader.render_env_help() == env_help  # from cache
