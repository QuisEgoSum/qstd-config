import sys

from .config import config, manager


def app():
    print('Config is ready: ', config.is_ready)
    print(config)


if __name__ == '__main__':
    if "--env-help" in sys.argv:
        print(manager.render_env_help())
        sys.exit(0)

    app()
