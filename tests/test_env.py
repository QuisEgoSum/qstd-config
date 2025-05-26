import os
import typing

from qstd_config.env import assign_env_to_dict, create_env_list_from_cls, render_env_help

from fixtures.sample_config import AppConfig


def test_env_mapping_and_assignment():
    os.environ['DEBUG_OVERRIDE'] = 'false'

    envs = create_env_list_from_cls(AppConfig, 'APP')

    assert len(envs) == 3

    config_dict: typing.Dict[typing.Any, typing.Any] = {}
    assigned = assign_env_to_dict(config_dict, envs)

    assert 'DEBUG_OVERRIDE' in assigned
    assert config_dict['debug'] == 'false'


def test_render_env_help():
    envs = create_env_list_from_cls(AppConfig, 'APP')

    env_help = render_env_help(envs)

    assert env_help == (
        "DEBUG_OVERRIDE (bool) [default: False]\n"
        "APP_STRING (str) [default: 'string']\n"
        "APP_NESTED_FLAG (bool) — Nested flag [default: False]"
    )
