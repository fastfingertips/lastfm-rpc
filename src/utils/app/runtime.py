import sys
import traceback

from loguru import logger


def setup_global_exception_handler():
    """Sets up a global sys.excepthook to catch and log uncaught exceptions."""

    def _handler(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.opt(exception=True).critical(f"FATAL CRASH:\n{tb_str}")

    sys.excepthook = _handler
