import os
import sys

from .config import config, manager
from .logger import logger


def app():
    logger.info('Config: %s', config)

    os.environ['EXAMPLE_DEBUG'] = 'false'

    config.reload()

    logger.info('Config: %s', config)


if __name__ == '__main__':
    if "--env-help" in sys.argv:
        print(manager.render_env_help())  # noqa: T201
        sys.exit(0)

    app()
