import logging
import time

from app.core.config import settings

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("clearsky.worker")


def main() -> None:
    logger.info("clearSKY worker started in %s mode", settings.app_env)
    while True:
        logger.info("Worker heartbeat. Job polling is implemented in Module 2.")
        time.sleep(60)


if __name__ == "__main__":
    main()

