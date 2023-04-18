# simple logging for chatgse
from datetime import datetime
import os
import pydoc
import logging


def get_logger(name: str = "chatgse") -> logging.Logger:
    """
    Access the module logger, create a new one if does not exist yet.

    The file handler creates a log file named after the current date and
    time. Levels to output to file and console can be set here.

    Args:
        name:
            Name of the logger instance.

    Returns:
        An instance of the Python :py:mod:`logging.Logger`.
    """

    if not logging.getLogger(name).hasHandlers():
        # create logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        # formatting
        file_formatter = logging.Formatter(
            "%(asctime)s\t%(levelname)s\tmodule:%(module)s\n%(message)s",
        )
        stdout_formatter = logging.Formatter("%(levelname)s -- %(message)s")

        # file name and creation
        now = datetime.now()
        date_time = now.strftime("%Y%m%d-%H%M%S")

        logdir = "chatgse-log"
        os.makedirs(logdir, exist_ok=True)
        logfile = os.path.join(logdir, f"chatgse-{date_time}.log")

        # handlers
        # stream handler
        stdout_handler = logging.StreamHandler()
        stdout_handler.setLevel(logging.INFO)
        stdout_handler.setFormatter(stdout_formatter)

        # file handler
        file_handler = logging.FileHandler(logfile)

        file_handler.setLevel(logging.DEBUG)

        file_handler.setFormatter(file_formatter)

        # add handlers
        logger.addHandler(file_handler)
        logger.addHandler(stdout_handler)

        # startup message
        logger.info(f"Logging into `{logfile}`.")

    return logging.getLogger(name)


def logfile() -> str:
    """
    Path to the log file.
    """

    return get_logger().handlers[0].baseFilename


def log():
    """
    Browse the log file.
    """

    with open(logfile()) as fp:
        pydoc.pager(fp.read())


logger = get_logger()
