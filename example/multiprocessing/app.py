import multiprocessing
import sys

from .config import config, manager


def app():
    print(f'Process {multiprocessing.current_process().name}. Config is ready: {config.is_ready}')
    print(f'Process {multiprocessing.current_process().name}', config)


def worker(ctx: dict):
    manager.set_multiprocessing_context(ctx)

    app()


def main():
    processes = []
    ctx = manager.get_multiprocessing_context()

    for i in range(3):
        process = multiprocessing.get_context('spawn').Process(
            target=worker,
            args=(ctx,),
            daemon=True,
            name=f'Worker {i}',
        )
        processes.append(process)
        process.start()

    app()

    for process in processes:
        process.join()


if __name__ == '__main__':
    if "--env-help" in sys.argv:
        print(manager.render_env_help())
        sys.exit(0)

    main()
