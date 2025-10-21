import logging
import logging.config
from pathlib import Path


def setup_logging():
    """
    Configures logging for the application using Python's standard logging module.
    """
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Define the logging configuration dictionary
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "default",
                "filename": "logs/error.log",
                "maxBytes": 1024 * 1024,  # 1 MB
                "backupCount": 10,
                "encoding": "utf8",
            },
        },
        "root": {"level": "INFO", "handlers": ["console", "error_file"]},
    }

    # Apply the configuration
    logging.config.dictConfig(LOGGING_CONFIG)
    logging.getLogger(__name__).info("Logging configured.")
