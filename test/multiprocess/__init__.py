"""
export PYTHONPATH=./
python3 ./test/multiprocess/__init__.py --config=config.yaml
"""
import asyncio
import os
from multiprocessing import current_process, get_context

from qstd_config import ConfigManager, BaseConfig


CONFIG_V1 = """
test: test 1
"""

CONFIG_V2 = """
test: test 2
"""


class Config(BaseConfig):
    test: str


manager = ConfigManager(
    Config,
    {
        'name': 'Test config',
        'version': '0.1.0'
    },
    root_config_dir=os.path.dirname(__file__),
    multiprocessing_mode=True
)

with open(os.path.join(manager.root_config_dir, 'config.yaml'), 'w') as file:
    file.write(CONFIG_V1)

config = manager.load_config()


def config_assert(i: int):
    if i == 1:
        assert config.test == 'test 1'
    elif i == 2:
        assert config.test == 'test 2'


async def child_process():
    i = 0
    while True:
        i += 1
        if i == 4:
            return
        print(current_process().name, config.test)
        config_assert(i)
        await asyncio.sleep(0.3)


def run_child_process(config_dict):
    manager.set_multiprocessing_config_dict(config_dict)
    asyncio.run(child_process())


async def parent_process():
    i = 0
    while True:
        i += 1
        if i == 3:
            with open(os.path.join(manager.root_config_dir, 'config.yaml'), 'w') as file:
                file.write(CONFIG_V1)
            return
        if i == 2:
            with open(os.path.join(manager.root_config_dir, 'config.yaml'), 'w') as file:
                file.write(CONFIG_V2)
            manager.load_config()
        print(current_process().name, config.test)
        config_assert(i)
        await asyncio.sleep(0.3)


def main():
    child_process_names = ['Child Process 1', 'Child Process 2']
    for child_process_name in child_process_names:
        get_context('spawn').Process(
            target=run_child_process,
            daemon=True,
            name=child_process_name,
            args=(manager.get_multiprocessing_config_dict(),)
        ).start()

    asyncio.run(parent_process())


if __name__ == '__main__':
    main()

