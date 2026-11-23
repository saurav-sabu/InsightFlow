import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure global application logging.

    Args:
        log_level: Logging level as string ('DEBUG', 'INFO', 'WARNING', 'ERROR').
    """
    # Configure root logger. force=True replaces any existing default handlers
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Suppress verbose log messages from external libraries
    noisy_libraries = ["httpx", "httpcore", "qdrant_client", "urllib3", "openai"]
    for lib in noisy_libraries:
        logging.getLogger(lib).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Usage:
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Message here")
    """
    return logging.getLogger(name)
