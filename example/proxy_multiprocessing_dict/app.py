import multiprocessing
import os
import sys
import typing

from multiprocessing.context import Process, SpawnProcess

from qstd_config import MultiprocessingContextType, MultiprocessingDictStorage

from .config import config, manager
from .logger import logger


def app():
    logger.info('Config is ready: %s', config.is_ready)
    logger.info('Config: %s', config.config)

    os.environ['EXAMPLE_DEBUG'] = 'false'

    config.reload()

    logger.info('Config after reload: %s', config.config)


def worker(ctx: MultiprocessingContextType):
    config.setup(multiprocessing_dict=ctx)

    app()


def main():
    processes: typing.List[typing.Union[SpawnProcess, Process]] = []
    ctx = MultiprocessingDictStorage.create_shared_context()

    for i in range(2):
        process = multiprocessing.Process(
            target=worker,
            args=(ctx,),
            name=f'Worker-{i}',
        )
        processes.append(process)
        process.start()

    for i in range(2):
        process = multiprocessing.get_context('spawn').Process(
            target=worker,
            args=(ctx,),
            name=f'WorkerSpawn-{i}',
        )
        processes.append(process)
        process.start()

    config.setup(multiprocessing_dict=ctx)

    app()

    for process in processes:
        process.join()


if __name__ == '__main__':
    if "--env-help" in sys.argv:
        print(manager.render_env_help())  # noqa: T201
        sys.exit(0)

    main()
