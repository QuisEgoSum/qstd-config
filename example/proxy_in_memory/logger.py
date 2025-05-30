import logging

logger = logging.getLogger('app')

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(processName)s] [%(levelname)s] %(name)s: %(message)s",
)
