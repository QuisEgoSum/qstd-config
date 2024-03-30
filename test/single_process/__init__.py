"""
export PYTHONPATH=./
export TEST_CONFIG_CONFIG='config1.yaml;config2.yaml'
python3 ./test/single_process/__init__.py --config='config3.yaml;config4.yaml'
"""

import os

from pydantic import BaseModel

from qstd_config import ConfigManager, BaseConfig


CONFIG4_V1 = """
test:
  test_field4: 'test_field4'
"""

CONFIG4_V2 = """
test:
  test_field: 'test_field4'
  test_field2: 'test_field4'
  test_field3: 'test_field4'
  test_field4: 'test_field4'
"""


class Config(BaseConfig):
    class Test(BaseModel):
        test_field: str
        test_field2: str
        test_field3: str
        test_field4: str

    test: Test


manager = ConfigManager(
    Config,
    {
        'name': 'Test config',
        'version': '0.1.0'
    },
    root_config_dir=os.path.dirname(__file__)
)


with open(os.path.join(manager.root_config_dir, 'config4.yaml'), 'w') as file:
    file.write(CONFIG4_V1)

config = manager.load_config()

assert config.project.name == 'Test config'
assert config.project.version == '0.1.0'
assert config.is_production is True
assert config.mode == 'production'
assert config.test.test_field == 'test_field'
assert config.test.test_field2 == 'test_field2'
assert config.test.test_field3 == 'test_field3'
assert config.test.test_field4 == 'test_field4'


with open(os.path.join(manager.root_config_dir, 'config4.yaml'), 'w') as file:
    file.write(CONFIG4_V2)

manager.load_config()

assert config.test.test_field == 'test_field4'
assert config.test.test_field2 == 'test_field4'
assert config.test.test_field3 == 'test_field4'
assert config.test.test_field4 == 'test_field4'

with open(os.path.join(manager.root_config_dir, 'config4.yaml'), 'w') as file:
    file.write(CONFIG4_V1)
